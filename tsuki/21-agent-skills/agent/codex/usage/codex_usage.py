#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Read local Codex usage and estimate equivalent current API base costs.

Python 3.10+, standard library only. Databases and rollouts are read-only.
No prompts, credentials, or usage records are sent over the network.
"""

import argparse
import calendar
from collections import Counter
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import json
import os
from pathlib import Path
import re
import sqlite3
import shutil
import sys
import tempfile
import threading
import textwrap
import time
import traceback
from typing import Any, TextIO
import urllib.request
from zoneinfo import ZoneInfo


class CLIStyle:
    """Apply semantic colors only to interactive terminal output."""

    COLORS = {"TITLE": 36, "CONTENT": 0, "MUTED": 90, "WARNING": 33, "ERROR": 31}

    @staticmethod
    def color(text: str, role: str = "CONTENT", stream: TextIO | None = None) -> str:
        """Respect redirection and NO_COLOR."""
        if not (stream or sys.stdout).isatty() or "NO_COLOR" in os.environ:
            return text
        return f"\033[{CLIStyle.COLORS[role]}m{text}\033[0m"

    @staticmethod
    def emit(text: str, role: str = "CONTENT") -> None:
        """Write one styled output line."""
        print(CLIStyle.color(text, role))


class Progress:
    """Report live stages on stderr, including during blocking network reads."""

    def __init__(self, enabled: bool = True) -> None:
        self.enabled = enabled
        self.started = time.monotonic()
        self.description = "Starting"
        self.stopped = threading.Event()
        self.lock = threading.Lock()
        self.worker: threading.Thread | None = None

    def start(self) -> None:
        """Start a heartbeat without altering stdout report data."""
        if self.enabled:
            self.render()
            self.worker = threading.Thread(target=self.heartbeat, daemon=True)
            self.worker.start()

    def update(self, description: str, announce: bool = False) -> None:
        """Replace the current stage safely from the processing thread."""
        with self.lock:
            self.description = description
        if announce and self.enabled:
            self.render()

    def render(self) -> None:
        """Refresh a terminal line or append a timestamped log entry."""
        with self.lock:
            text = f"[{time.monotonic() - self.started:6.1f}s] {self.description}"
        interactive = sys.stderr.isatty()
        prefix, suffix = ("\r\033[2K", "") if interactive else ("", "\n")
        sys.stderr.write(prefix + CLIStyle.color(text, "TITLE", sys.stderr) + suffix)
        sys.stderr.flush()

    def heartbeat(self) -> None:
        """Keep elapsed time moving even while one large file is processed."""
        interval = 1.0 if sys.stderr.isatty() else 5.0
        while not self.stopped.wait(interval):
            self.render()

    def finish(self, description: str) -> None:
        """Stop the heartbeat before the final report or error is printed."""
        self.stopped.set()
        if self.worker:
            self.worker.join()
        if self.enabled:
            self.update(description)
            self.render()
            if sys.stderr.isatty():
                sys.stderr.write("\n")
                sys.stderr.flush()


class ColoredArgumentParser(argparse.ArgumentParser):
    """Color help without introducing escape codes into redirected output."""

    def format_help(self) -> str:
        """Render sections and options with semantic colors."""
        text = super().format_help()
        return (
            "\n".join(
                CLIStyle.color(line, "TITLE" if not line.startswith(" ") else "CONTENT")
                for line in text.splitlines()
            )
            + "\n"
        )


def parser() -> argparse.ArgumentParser:
    """Define time selection and output options."""
    result = ColoredArgumentParser(
        description="Codex local usage and current API-equivalent base cost (USD).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Examples:
  python codex_usage.py --period 7d
  python codex_usage.py --period 24h
  python codex_usage.py --period 1m
  python codex_usage.py --period all
  python codex_usage.py --since 2026-09-01 --until 2026-09-09
  python codex_usage.py --since 2026-09-01T12:00 --timezone Asia/Singapore
  python codex_usage.py --period all --json > usage.json
  python codex_usage.py --offline --prices-file prices.json

Notes:
  Default: rolling 7 days. 1m means one calendar month, clamped at month end.
  Date-only --until includes the whole date; datetime --until is exclusive.
  Input includes cached/cache-write tokens; output includes reasoning tokens.
  Costs exclude long-context, Fast mode, regional and tool surcharges.
  Unknown models are unpriced, never silently treated as free.
  Price cache is refreshed each online run; offline/fallback age is displayed.
  --prices-file JSON: {"models": {"my-model":
    {"input": 1, "cached": 0.1, "write": null, "output": 5}}}
  All custom rates are USD per million tokens; model names match exactly.
""",
    )
    result.add_argument("--period", choices=["24h", "7d", "1m", "all"])
    result.add_argument("--since", metavar="ISO_DATE", help="Inclusive start date/time")
    result.add_argument("--until", metavar="ISO_DATE", help="End date/time")
    result.add_argument(
        "--timezone",
        default=None,
        metavar="IANA_ZONE",
        help="Default: system local timezone",
    )
    result.add_argument(
        "--codex-home",
        type=Path,
        default=Path(os.environ.get("CODEX_HOME", "~/.codex")).expanduser(),
    )
    result.add_argument("--db", type=Path, help="Explicit state_N.sqlite database")
    result.add_argument("--json", action="store_true", help="Machine-readable report")
    result.add_argument("--offline", action="store_true", help="Do not fetch prices")
    result.add_argument(
        "--prices-file",
        type=Path,
        help="Use a custom price JSON instead of official prices",
    )
    result.add_argument(
        "--price-cache",
        type=Path,
        default=Path(__file__).resolve().with_name("prices-cache.json"),
    )
    result.add_argument("--log", action="store_true", help="Show traceback on failure")
    result.add_argument(
        "--no-progress", action="store_true", help="Disable progress on stderr"
    )
    result.add_argument(
        "--details",
        action="store_true",
        help="Show price table, metadata and full counting notes",
    )
    return result


def parse_date(value: str, zone: Any) -> datetime:
    """Interpret naive dates in the chosen timezone."""
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    return parsed.replace(tzinfo=zone) if parsed.tzinfo is None else parsed


def time_window(
    args: argparse.Namespace, now: datetime
) -> tuple[datetime | None, datetime]:
    """Return a half-open time window."""
    if args.period and (args.since or args.until):
        raise ValueError("--period cannot be combined with --since/--until")
    end = parse_date(args.until, now.tzinfo) if args.until else now
    if args.until and re.fullmatch(r"\d{4}-\d{2}-\d{2}", args.until):
        end += timedelta(days=1)
    if args.since or args.until:
        start = parse_date(args.since, now.tzinfo) if args.since else None
    else:
        start = preset_start(args.period or "7d", now)
    if start is not None and start >= end:
        raise ValueError("Start must precede end")
    return start, end


def preset_start(period: str, now: datetime) -> datetime | None:
    """Handle rolling durations and calendar month arithmetic."""
    if period == "all":
        return None
    if period == "1m":
        year, month = (now.year, now.month - 1) if now.month > 1 else (now.year - 1, 12)
        return now.replace(
            year=year,
            month=month,
            day=min(now.day, calendar.monthrange(year, month)[1]),
        )
    hours = 24 if period == "24h" else 168
    return (now.astimezone(timezone.utc) - timedelta(hours=hours)).astimezone(
        now.tzinfo
    )


def local_zone() -> Any:
    """Preserve local daylight-saving rules when the OS exposes zoneinfo."""
    configured = os.environ.get("TZ", "").lstrip(":")
    if configured and not configured.startswith("/"):
        return ZoneInfo(configured)
    try:
        with Path(configured or "/etc/localtime").open("rb") as stream:
            return ZoneInfo.from_file(stream)
    except (OSError, ValueError):
        return datetime.now().astimezone().tzinfo


def read_threads(
    home: Path, explicit: Path | None
) -> tuple[Path, list[dict[str, Any]]]:
    """Discover the newest schema version and read only required metadata."""
    candidates = list(home.glob("state_[0-9]*.sqlite"))
    db = explicit or max(
        candidates, key=lambda p: int(p.stem.split("_")[-1]), default=None
    )
    if db is None:
        raise FileNotFoundError(f"No state_N.sqlite database in {home}")
    connection = sqlite3.connect(
        db.resolve().as_uri() + "?mode=ro", uri=True, timeout=10
    )
    try:
        connection.row_factory = sqlite3.Row
        columns = {row[1] for row in connection.execute("PRAGMA table_info(threads)")}
        required = {"id", "rollout_path", "tokens_used"}
        if not required <= columns:
            raise ValueError("Unsupported database: threads metadata is missing")
        selected = sorted(
            required | ({"model", "archived", "created_at", "updated_at"} & columns)
        )
        rows = [
            dict(row)
            for row in connection.execute(
                "SELECT " + ",".join(selected) + " FROM threads"
            )
        ]
    finally:
        connection.close()
    return db, rows


def usage_values(raw: dict[str, Any]) -> dict[str, int]:
    """Validate counters and normalize optional fields."""
    keys = (
        "input_tokens",
        "cached_input_tokens",
        "cache_write_input_tokens",
        "output_tokens",
        "reasoning_output_tokens",
    )
    result = {key: int(raw.get(key, 0)) for key in keys}
    result["total_tokens"] = int(
        raw.get("total_tokens", result["input_tokens"] + result["output_tokens"])
    )
    if min(result.values()) < 0:
        raise ValueError("Negative usage counter")
    return result


class RolloutReader:
    """Prefer per-response records, using cumulative deltas for legacy turns."""

    def __init__(self, thread_id: str, issues: Counter) -> None:
        self.thread_id = thread_id
        self.issues = issues
        self.model = "unknown"
        self.owner = thread_id
        self.previous: dict[str, int] = {}
        self.responses: set[str] = set()
        self.turn_id = ""
        self.modern_turns: set[str] = set()
        self.turn_models: dict[str, str] = {}
        self.history_start: int | None = None

    def consume(self, event: dict[str, Any]) -> tuple[str, str, dict[str, int]] | None:
        """Extract one incremental usage record, suppressing mirror events."""
        kind, payload = event.get("type"), event.get("payload") or {}
        if kind == "session_meta":
            self.owner = payload.get("id", self.owner)
            self.history_start = payload.get("subagent_history_start_ordinal")
        if kind == "turn_context":
            self.model = payload.get("model") or "unknown"
            self.turn_id = payload.get("turn_id") or ""
        if kind == "token_usage_record":
            return self.modern(event, payload)
        info = (
            payload.get("info")
            if kind == "event_msg" and payload.get("type") == "token_count"
            else None
        )
        if not info or not info.get("total_token_usage"):
            return None
        total = usage_values(info["total_token_usage"])
        if self.turn_id in self.modern_turns:
            self.previous = total
            return None
        delta = self.advance(total, info.get("last_token_usage"))
        inherited = (
            self.history_start is not None
            and event.get("ordinal", self.history_start) < self.history_start
        )
        if self.owner != self.thread_id or inherited or not delta:
            return None
        return event["timestamp"], self.model, delta

    def advance(
        self, total: dict[str, int], last: dict[str, Any] | None
    ) -> dict[str, int] | None:
        """Use cumulative differences; handle counter resets explicitly."""
        if total == self.previous:
            return None
        delta = {key: value - self.previous.get(key, 0) for key, value in total.items()}
        self.previous = total
        if min(delta.values()) < 0:
            self.issues["counter_resets_using_last_usage"] += 1
            return usage_values(last) if last else None
        return delta if delta["total_tokens"] else None

    def modern(
        self, event: dict[str, Any], payload: dict[str, Any]
    ) -> tuple[str, str, dict[str, int]] | None:
        """Count response IDs once; cumulative mirrors can diverge on compaction."""
        response_id = payload.get("response_id")
        if payload.get("thread_id", self.thread_id) != self.thread_id:
            return None
        self.modern_turns.add(payload.get("turn_id") or self.turn_id)
        if response_id and response_id in self.responses:
            return None
        if response_id:
            self.responses.add(response_id)
        if not payload.get("usage"):
            self.issues["modern_records_missing_usage"] += 1
            return None
        usage = usage_values(payload["usage"])
        model = (
            payload.get("model")
            or self.turn_models.get(payload.get("turn_id"))
            or self.model
        )
        return event["timestamp"], model, usage


def scan_rollout(
    path: Path, thread_id: str, issues: Counter
) -> list[tuple[str, str, dict[str, int]]]:
    """Read usage-only lines; tolerate incomplete final writes in active files."""
    reader = RolloutReader(thread_id, issues)
    result = []
    events = []
    with path.open("rb") as stream:
        for line in stream:
            if not any(
                marker in line
                for marker in (
                    b'"token_count"',
                    b'"token_usage_record"',
                    b'"turn_context"',
                    b'"session_meta"',
                )
            ):
                continue
            try:
                event = json.loads(line)
            except (ValueError, UnicodeDecodeError):
                issues["malformed_usage_records"] += 1
                continue
            if event.get("type") in {
                "session_meta",
                "turn_context",
                "token_usage_record",
            } or (
                event.get("type") == "event_msg"
                and event.get("payload", {}).get("type") == "token_count"
            ):
                events.append(event)
    reader.modern_turns = modern_turns(events, thread_id)
    reader.turn_models = {
        event["payload"]["turn_id"]: event["payload"]["model"]
        for event in events
        if event.get("type") == "turn_context"
        and event.get("payload", {}).get("turn_id")
        and event["payload"].get("model")
    }
    for event in events:
        item = decode_usage(event, reader, issues)
        if item:
            result.append(item)
    return result


def modern_turns(events: list[dict], thread_id: str) -> set[str]:
    """Prefer response records for whole turns, including earlier legacy mirrors."""
    result = set()
    turn_id = ""
    for event in events:
        payload = event.get("payload") or {}
        if event.get("type") == "turn_context":
            turn_id = payload.get("turn_id") or ""
        if (
            event.get("type") == "token_usage_record"
            and payload.get("thread_id", thread_id) == thread_id
        ):
            result.add(payload.get("turn_id") or turn_id)
    return result


def decode_usage(
    event: dict, reader: RolloutReader, issues: Counter
) -> tuple[str, str, dict[str, int]] | None:
    """Count malformed usage records instead of concealing missing data."""
    try:
        return reader.consume(event)
    except (ValueError, KeyError, TypeError, AttributeError):
        issues["malformed_usage_records"] += 1
        return None


def parse_prices(markdown: str) -> dict[str, dict[str, float | None]]:
    """Parse explicitly Standard text tables, never Batch/Flex/Fast tables."""
    prices: dict[str, dict[str, float | None]] = {}
    mode = ""
    headers: list[str] = []
    for line in markdown.splitlines():
        stripped = line.strip()
        if stripped in {"Standard", "Batch", "Flex", "Fast mode"}:
            mode = stripped
        if not stripped.startswith("|"):
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if "Model" in cells:
            headers = cells
            continue
        if mode == "Standard" and "Model" in headers and "Modality" not in headers:
            add_price_row(prices, headers, cells)
    if not prices:
        raise ValueError("Official pricing table format not recognized")
    return prices


def add_price_row(prices: dict, headers: list[str], cells: list[str]) -> None:
    """Accept numeric text-token prices from recognized column schemas."""
    if len(cells) != len(headers):
        return
    row = dict(zip(headers, cells))
    prefix = "Short context " if "Short context input" in row else ""
    names = [
        prefix + "input",
        prefix + "cached input",
        prefix + "cache writes",
        prefix + "output",
    ]
    lower = {key.lower(): value for key, value in row.items()}
    if not lower.get(names[0].lower(), "").startswith("$") or not lower.get(
        names[3].lower(), ""
    ).startswith("$"):
        return
    values = [lower.get(name.lower(), "-") for name in names]
    if any(value != "-" and not re.fullmatch(r"\$[\d.]+", value) for value in values):
        return
    model = row["Model"].split(" (")[0].strip("`")
    prices.setdefault(
        model,
        dict(
            zip(
                ("input", "cached", "write", "output"),
                [float(v[1:]) if v != "-" else None for v in values],
            )
        ),
    )


def validate_prices(data: dict[str, Any]) -> dict[str, Any]:
    """Reject malformed or negative custom/cache rates."""
    models = data["models"]
    if not isinstance(models, dict):
        raise ValueError("Price models must be an object")
    for rates in models.values():
        for key in ("input", "cached", "write", "output"):
            value = rates.get(key)
            if value is not None and (
                not Decimal(str(value)).is_finite() or Decimal(str(value)) < 0
            ):
                raise ValueError("Prices must be finite and non-negative")
    return data


def load_prices(args: argparse.Namespace, warnings: list[str]) -> dict[str, Any]:
    """Fetch a public documentation endpoint, with transparent cache fallback."""
    url = "https://developers.openai.com/api/docs/pricing.md"
    if args.prices_file:
        data = validate_prices(json.loads(args.prices_file.read_text()))
        return {**data, "source": str(args.prices_file), "status": "custom"}
    if not args.offline:
        try:
            request = urllib.request.Request(
                url, headers={"User-Agent": "codex-local-usage/1.0"}
            )
            with urllib.request.urlopen(request, timeout=20) as response:
                models = parse_prices(response.read(4_000_000).decode("utf-8"))
            data = {
                "models": models,
                "source": url,
                "fetched_at": datetime.now(timezone.utc).isoformat(),
                "status": "live",
            }
            save_cache(args.price_cache, data, warnings)
            return data
        except (OSError, ValueError) as error:
            warnings.append(
                f"Price refresh failed ({type(error).__name__}); trying cache."
            )
    if args.price_cache.exists():
        data = validate_prices(json.loads(args.price_cache.read_text()))
        return {**data, "status": "cached; not verified current"}
    warnings.append("No price data available; all models remain unpriced.")
    return {"models": {}, "source": url, "status": "unavailable"}


def save_cache(path: Path, data: dict, warnings: list[str]) -> None:
    """Atomically replace the price cache without risking partial JSON."""
    temporary = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w", dir=path.parent, delete=False
        ) as stream:
            temporary = Path(stream.name)
            json.dump(data, stream, indent=2)
        temporary.replace(path)
    except OSError:
        warnings.append("Could not save price cache; live prices are still usable.")
    finally:
        if temporary and temporary.exists():
            temporary.unlink()


def estimate(usage: dict[str, int], rates: dict | None) -> Decimal | None:
    """Partition input into disjoint uncached, cached, and cache-write tokens."""
    if rates is None:
        return None
    cached, written = usage["cached_input_tokens"], usage["cache_write_input_tokens"]
    uncached = usage["input_tokens"] - cached - written
    counts = {
        "input": uncached,
        "cached": cached,
        "write": written,
        "output": usage["output_tokens"],
    }
    if uncached < 0 or any(
        count and rates.get(key) is None for key, count in counts.items()
    ):
        return None
    return (
        sum(
            (
                Decimal(count) * Decimal(str(rates.get(key) or 0))
                for key, count in counts.items()
            ),
            Decimal(0),
        )
        / 1_000_000
    )


def aggregate(
    threads: list[dict],
    home: Path,
    start: datetime | None,
    end: datetime,
    issues: Counter,
    progress: Progress | None = None,
) -> tuple[list[dict], set[str]]:
    """Count per-model usage within the requested event-time range."""
    groups: dict[str, dict] = {}
    sessions: set[str] = set()
    for index, thread in enumerate(threads):
        if progress:
            progress.update(
                f"Scanning sessions: {index:,}/{len(threads):,} "
                f"({index / len(threads):.1%}) completed | "
                f"matched: {len(sessions):,} | unreadable: {issues['unreadable_rollouts']:,}"
            )
        path = Path(thread["rollout_path"])
        if not path.is_absolute():
            path = home / path
        try:
            events = scan_rollout(path, thread["id"], issues)
        except OSError:
            issues["unreadable_rollouts"] += 1
            continue
        collect_events(events, thread["id"], start, end, groups, sessions, issues)
    rows = [
        {"model": model, "sessions": len(value["sessions"]), **value["usage"]}
        for model, value in groups.items()
    ]
    return sorted(rows, key=lambda row: row["total_tokens"], reverse=True), sessions


def collect_events(
    events: list,
    thread_id: str,
    start: datetime | None,
    end: datetime,
    groups: dict,
    sessions: set,
    issues: Counter,
) -> None:
    """Filter after reconstructing counters so pre-window usage is excluded."""
    for stamp, model, usage in events:
        try:
            when = parse_date(stamp, timezone.utc)
        except ValueError:
            issues["invalid_timestamps"] += 1
            continue
        if when >= end or (start and when < start):
            continue
        group = groups.setdefault(model, {"sessions": set(), "usage": Counter()})
        group["sessions"].add(thread_id)
        group["usage"].update(usage)
        sessions.add(thread_id)


def friendly_time(value: str | None) -> str:
    """Format timestamps for humans while preserving the UTC offset."""
    if not value:
        return "beginning"
    try:
        return datetime.fromisoformat(value).isoformat(sep=" ", timespec="minutes")
    except ValueError:
        return value


def wrapped(text: str, role: str = "MUTED") -> None:
    """Keep explanatory text within the terminal width."""
    width = max(40, shutil.get_terminal_size((120, 24)).columns - 4)
    for line in textwrap.wrap(text, width=width, subsequent_indent="  "):
        CLIStyle.emit("  " + line, role)


def display(report: dict[str, Any], details: bool = False) -> None:
    """Separate the summary, usage table, and supporting details visually."""
    CLIStyle.emit("")
    CLIStyle.emit("  CODEX USAGE", "TITLE")
    wrapped(
        f"{friendly_time(report['start'])}  ->  {friendly_time(report['end'])} (end exclusive)"
    )
    CLIStyle.emit("")
    wrapped(
        f"Sessions  {report['sessions']:,}     Tokens  {report['total_tokens']:,}",
        "CONTENT",
    )
    wrapped(
        f"Priced subtotal  ${float(report['priced_subtotal_usd']):,.2f} USD", "TITLE"
    )
    if report["unpriced_models"]:
        wrapped(
            f"Unpriced: {report['unpriced_models']} model(s), {report['unpriced_tokens']:,} tokens (excluded from subtotal)"
        )
    CLIStyle.emit("")
    narrow = shutil.get_terminal_size((120, 24)).columns < 115
    keys = (
        ["total_tokens"]
        if narrow
        else ["total_tokens", "input_tokens", "cached_input_tokens", "output_tokens"]
    )
    headers = (
        ["Model", "Sessions", "Total tokens"]
        if narrow
        else ["Model", "Sessions", "Total tokens", "Input", "Cached input", "Output"]
    )
    if not narrow and any(row["cache_write_input_tokens"] for row in report["models"]):
        keys.append("cache_write_input_tokens")
        headers.append("Cache writes")
    headers.append("USD est.")
    rows = [
        [
            row["model"],
            str(row["sessions"]),
            *[f"{row[key]:,}" for key in keys],
            f"${float(row['cost_usd']):,.2f}"
            if row["cost_usd"] is not None
            else "unpriced",
        ]
        for row in report["models"]
    ]
    table(headers, rows)
    CLIStyle.emit("")
    price = report["pricing"]
    wrapped(
        f"Prices: {price['status']} | fetched {friendly_time(price.get('fetched_at'))}"
    )
    wrapped(
        "Current Standard base-price estimate, not an actual bill; excludes surcharges and tool fees."
    )
    if not narrow:
        wrapped(
            "Cached tokens are included in Input. Output includes reasoning tokens."
        )
    if report["warnings"]:
        CLIStyle.emit("")
        CLIStyle.emit("  DATA NOTICES", "WARNING")
        for warning in report["warnings"]:
            wrapped(
                warning.replace(
                    "counter_resets_using_last_usage:",
                    "Legacy counter resets (last usage used):",
                ).replace("unreadable_rollouts:", "Unreadable session files:"),
                "WARNING",
            )
    if details:
        display_details(report, narrow)
    else:
        wrapped(
            "Use --details for token breakdowns, unit prices, metadata and counting notes."
        )
    CLIStyle.emit("")


def display_details(report: dict[str, Any], narrow: bool) -> None:
    """Expand supporting information only when requested."""
    if narrow:
        CLIStyle.emit("")
        CLIStyle.emit("  TOKEN BREAKDOWN", "TITLE")
        for row in report["models"]:
            wrapped(row["model"], "TITLE")
            wrapped(
                f"Input {row['input_tokens']:,} | Cached {row['cached_input_tokens']:,} | Writes {row['cache_write_input_tokens']:,} | Output {row['output_tokens']:,}",
                "CONTENT",
            )
    CLIStyle.emit("")
    CLIStyle.emit("  API PRICES / 1M TOKENS (USD)", "TITLE")
    CLIStyle.emit("")
    rows = [
        [
            row["model"],
            *[
                str(row["rates_usd_per_million"].get(key))
                if row["rates_usd_per_million"].get(key) is not None
                else "-"
                for key in ("input", "cached", "write", "output")
            ],
        ]
        for row in report["models"]
        if row["rates_usd_per_million"]
    ]
    table(["Model", "Input", "Cached", "Write", "Output"], rows)
    CLIStyle.emit("")
    wrapped(f"Database: {report['database']}")
    wrapped(f"Indexed sessions: {report['indexed_sessions']:,}")
    wrapped(f"Price source: {report['pricing']['source']}")
    CLIStyle.emit("")
    for note in report["notes"]:
        wrapped("- " + note)


def table(headers: list[str], rows: list[list[str]]) -> None:
    """Align column headings with values and keep separators subdued."""
    widths = [
        max(len(row[index]) for row in [headers] + rows)
        for index in range(len(headers))
    ]
    for index, row in enumerate([headers] + rows):
        line = "  " + "  ".join(
            value.ljust(width) if column == 0 else value.rjust(width)
            for column, (value, width) in enumerate(zip(row, widths))
        )
        CLIStyle.emit(line, "TITLE" if index == 0 else "CONTENT")
        if index == 0:
            CLIStyle.emit("  " + "  ".join("-" * width for width in widths), "MUTED")


def run(args: argparse.Namespace, progress: Progress | None = None) -> dict[str, Any]:
    """Build a reproducible report with source and coverage metadata."""
    zone = ZoneInfo(args.timezone) if args.timezone else local_zone()
    start, end = time_window(args, datetime.now(zone))
    if progress:
        progress.update("Reading database metadata", announce=True)
    db, threads = read_threads(args.codex_home, args.db)
    warnings: list[str] = []
    if progress:
        action = (
            "Reading local prices"
            if args.offline or args.prices_file
            else "Fetching official prices (network timeout: 20s)"
        )
        progress.update(f"Indexed {len(threads):,} sessions | {action}", announce=True)
    prices = load_prices(args, warnings)
    issues: Counter = Counter()
    if progress:
        progress.update("Scanning usage records", announce=True)
    rows, sessions = aggregate(threads, args.codex_home, start, end, issues, progress)
    if progress:
        progress.update(
            f"Scanned {len(threads):,}/{len(threads):,} sessions (100%) | Calculating model totals and costs",
            announce=True,
        )
    if any(row["model"] == "unknown" for row in rows):
        warnings.append(
            "Some events lack a historical model label; reported as unknown, not assigned the thread's latest model."
        )
    subtotal = Decimal(0)
    for row in rows:
        row["unclassified_tokens"] = (
            row["total_tokens"] - row["input_tokens"] - row["output_tokens"]
        )
        if row["unclassified_tokens"]:
            warnings.append(
                f"{row['model']}: reported total differs from input + output by {row['unclassified_tokens']:,}; cost covers known input/output only."
            )
        rates = prices["models"].get(row["model"])
        cost = estimate(row, rates)
        row.update(
            cost_usd=str(cost) if cost is not None else None,
            rates_usd_per_million=rates,
        )
        subtotal += cost or Decimal(0)
    warnings.extend(f"{key}: {value}" for key, value in sorted(issues.items()))
    return {
        "start": start.isoformat() if start else None,
        "end": end.isoformat(),
        "database": str(db),
        "indexed_sessions": len(threads),
        "database_lifetime_tokens": sum(
            thread["tokens_used"] or 0 for thread in threads
        ),
        "sessions": len(sessions),
        "total_tokens": sum(row["total_tokens"] for row in rows),
        "priced_subtotal_usd": str(subtotal),
        "unpriced_models": sum(row["cost_usd"] is None for row in rows),
        "unpriced_tokens": sum(
            row["total_tokens"] for row in rows if row["cost_usd"] is None
        ),
        "models": rows,
        "pricing": {key: value for key, value in prices.items() if key != "models"},
        "warnings": warnings,
        "issues": dict(issues),
        "notes": [
            "Current Standard short-context API-equivalent estimate; not a Codex/ChatGPT bill or historical price calculation.",
            "Excludes long-context, Fast mode, regional and tool surcharges.",
            "Input includes cached/write tokens; output includes reasoning. Neither is added twice.",
            "Sessions count threads with usage in this interval, including subagents and archived threads. Model session counts can overlap.",
            "Coverage: database-indexed local rollouts only; deleted, missing or unsynced history cannot be reconstructed.",
        ],
    }


def main() -> int:
    """Execute the CLI and surface actionable errors."""
    args = parser().parse_args()
    progress = Progress(enabled=not args.no_progress)
    progress.start()
    try:
        report = run(args, progress)
        progress.finish("Complete")
        if args.json:
            sys.stdout.write(json.dumps(report, indent=2) + "\n")
        else:
            display(report, details=args.details)
        return 0
    except BrokenPipeError:
        progress.finish("Output pipe closed")
        return 0
    except KeyboardInterrupt:
        progress.finish("Interrupted")
        return 130
    except Exception as error:
        progress.finish("Failed")
        if args.log:
            traceback.print_exc()
        sys.stderr.write(CLIStyle.color(f"Error: {error}", "ERROR") + "\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
