#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import re
import sys
import traceback
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

DEBUG_MODE = False
DEFAULT_TIMEZONE_HOURS = 8
DEFAULT_CONTENT_HEADING_OFFSET = 2
MAX_MARKDOWN_HEADING_LEVEL = 6
NOISE_PATTERN = re.compile(
    r"The output of this plugin|Original custom instructions|system1_search_query|"
    r"source_analysis_msg_id|reasoning_recap|cite|writing\{variant="
)
CHATGPT_CITATION_PATTERN = re.compile(r"cite[^]+")
MARKDOWN_HEADING_PATTERN = re.compile(r"^(#{1,6})([ \t]+.+)$")
MARKDOWN_DIRECTIVE_PATTERN = re.compile(r"^:{3,}([A-Za-z][\w-]*)?(\{.*\})?\s*$")


class CLIStyle:
    """CLI tool unified style config."""

    COLORS = {
        "TITLE": 7,
        "SUB_TITLE": 2,
        "CONTENT": 3,
        "EXAMPLE": 7,
        "WARNING": 4,
        "ERROR": 2,
    }

    @staticmethod
    def color(text: str = "", color: int = COLORS["CONTENT"]) -> str:
        """Apply ANSI color to terminal text."""
        color_table = {
            0: "{}",
            1: "\033[1;30m{}\033[0m",
            2: "\033[1;31m{}\033[0m",
            3: "\033[1;32m{}\033[0m",
            4: "\033[1;33m{}\033[0m",
            5: "\033[1;34m{}\033[0m",
            6: "\033[1;35m{}\033[0m",
            7: "\033[1;36m{}\033[0m",
            8: "\033[1;37m{}\033[0m",
        }
        return color_table[color].format(text)


class ColoredArgumentParser(argparse.ArgumentParser):
    """ArgumentParser with colored help output."""

    def _format_action_invocation(self, action: argparse.Action) -> str:
        if not action.option_strings:
            metavar_formatter = self._metavar_formatter(action, action.dest)
            metavar = metavar_formatter(1)[0]
            return str(metavar)

        parts = []
        if action.nargs == 0:
            parts.extend(
                CLIStyle.color(option, CLIStyle.COLORS["SUB_TITLE"])
                for option in action.option_strings
            )
        else:
            args_string = self._format_args(action, action.dest.upper())
            for option_string in action.option_strings:
                parts.append(
                    CLIStyle.color(
                        f"{option_string} {args_string}",
                        CLIStyle.COLORS["SUB_TITLE"],
                    )
                )
        return ", ".join(parts)

    def format_help(self) -> str:
        formatter = self._get_formatter()
        if self.description:
            formatter.add_text(
                CLIStyle.color(self.description, CLIStyle.COLORS["TITLE"])
            )
        formatter.add_usage(self.usage, self._actions, self._mutually_exclusive_groups)
        formatter.add_text(
            CLIStyle.color("\nOptional Arguments:", CLIStyle.COLORS["TITLE"])
        )
        for action_group in self._action_groups:
            formatter.start_section(action_group.title)
            formatter.add_arguments(action_group._group_actions)
            formatter.end_section()
        if self.epilog:
            formatter.add_text(self.epilog)
        return formatter.format_help()


@dataclass
class Message:
    """Visible conversation message."""

    role: str
    text: str
    created_at: str


@dataclass
class Turn:
    """Visible QA turn."""

    index: int
    user: Message
    assistant: Message | None


@dataclass
class TurnPlan:
    """Curated turn table row."""

    index: int
    export: str
    heading: str
    q: str
    a: str
    note: str


def debug(message: str) -> None:
    """Print debug output when enabled."""
    if DEBUG_MODE:
        print(
            CLIStyle.color(f"DEBUG: {message}", CLIStyle.COLORS["WARNING"]),
            file=sys.stderr,
        )


def create_example_text(script_name: str) -> str:
    """Create colored help examples."""
    examples = [
        (
            "Export a public share URL",
            f"{script_name} https://chatgpt.com/share/<id> -o /tmp/share.md",
        ),
        (
            "Export a saved HTML file",
            f"{script_name} /tmp/share.html -o /tmp/share.md --source-url https://chatgpt.com/share/<id>",
        ),
        (
            "Use a curated plan",
            f"{script_name} /tmp/share.html -o /tmp/share.md --plan /tmp/plan.json",
        ),
    ]
    text = f"\n{CLIStyle.color('Examples:', CLIStyle.COLORS['SUB_TITLE'])}"
    for description, command in examples:
        text += f"\n  {CLIStyle.color(f'# {description}', CLIStyle.COLORS['EXAMPLE'])}"
        text += f"\n  {CLIStyle.color(command, CLIStyle.COLORS['CONTENT'])}\n"
    return text


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments."""
    parser = ColoredArgumentParser(
        description="Export a ChatGPT shared conversation page to readable Markdown.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=create_example_text("chatgpt-share-to-md.py"),
    )
    parser.add_argument(
        "source",
        help=CLIStyle.color(
            "ChatGPT share URL or saved HTML path", CLIStyle.COLORS["CONTENT"]
        ),
    )
    parser.add_argument(
        "-o",
        "--output",
        help=CLIStyle.color(
            "Markdown output path. Defaults to stdout.", CLIStyle.COLORS["CONTENT"]
        ),
    )
    parser.add_argument(
        "--source-url",
        help=CLIStyle.color(
            "Original share URL when source is a local HTML file",
            CLIStyle.COLORS["CONTENT"],
        ),
    )
    parser.add_argument(
        "--title",
        help=CLIStyle.color("Manual Markdown H1 title", CLIStyle.COLORS["CONTENT"]),
    )
    parser.add_argument(
        "--plan",
        help=CLIStyle.color("Curated export plan JSON", CLIStyle.COLORS["CONTENT"]),
    )
    parser.add_argument(
        "--plan-template",
        help=CLIStyle.color(
            "Write a starter export plan JSON for agent curation",
            CLIStyle.COLORS["CONTENT"],
        ),
    )
    parser.add_argument(
        "--messages-json",
        help=CLIStyle.color(
            "Optional visible message JSON output path", CLIStyle.COLORS["CONTENT"]
        ),
    )
    parser.add_argument(
        "--timezone-hours",
        type=int,
        default=DEFAULT_TIMEZONE_HOURS,
        help=CLIStyle.color("Local timezone offset hours", CLIStyle.COLORS["CONTENT"]),
    )
    parser.add_argument(
        "--content-heading-offset",
        type=int,
        default=DEFAULT_CONTENT_HEADING_OFFSET,
        help=CLIStyle.color(
            "Demote Markdown headings inside message bodies by N levels. Use 0 to preserve.",
            CLIStyle.COLORS["CONTENT"],
        ),
    )
    parser.add_argument(
        "--keep-chatgpt-cites",
        action="store_true",
        help=CLIStyle.color(
            "Keep ChatGPT internal citation tokens", CLIStyle.COLORS["CONTENT"]
        ),
    )
    parser.add_argument(
        "--log",
        action="store_true",
        help=CLIStyle.color("Enable debug logging", CLIStyle.COLORS["CONTENT"]),
    )
    return parser.parse_args()


def fetch_or_read_source(source: str) -> tuple[str, str]:
    """Read local HTML or fetch URL content."""
    path = Path(source).expanduser()
    if path.exists():
        return path.read_text(encoding="utf-8", errors="replace"), str(path)

    if not source.startswith(("http://", "https://")):
        raise FileNotFoundError(source)

    request = urllib.request.Request(
        source,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/125.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        },
    )
    with urllib.request.urlopen(request, timeout=30) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace"), source


def extract_rsc_table(html: str) -> list[Any]:
    """Extract the first JSON table from React Router stream chunks."""
    pattern = re.compile(r"streamController\.enqueue\((\".*?\")\);", re.S)
    for match in pattern.finditer(html):
        stream_text = json.loads(match.group(1))
        stripped = stream_text.strip()
        if not stripped.startswith("["):
            continue
        value = json.loads(stripped)
        if isinstance(value, list):
            debug(f"RSC table entries: {len(value)}")
            return value
    raise ValueError("No React Router JSON reference table found")


def resolve_rsc_table(table: list[Any]) -> Any:
    """Resolve React Server Component reference table values."""
    memo: dict[int, Any] = {}

    def resolve_ref(value: Any) -> Any:
        if isinstance(value, int):
            if value < 0:
                return None
            if value >= len(table):
                return value
            return resolve_value(value)
        return value

    def resolve_key(key: str) -> Any:
        if key.startswith("_") and key[1:].lstrip("-").isdigit():
            return resolve_ref(int(key[1:]))
        return key

    def resolve_value(index: int) -> Any:
        if index in memo:
            return memo[index]
        value = table[index]
        if isinstance(value, dict):
            resolved: dict[Any, Any] = {}
            memo[index] = resolved
            for key, item in value.items():
                resolved[resolve_key(key)] = resolve_ref(item)
            return resolved
        if isinstance(value, list):
            resolved_list: list[Any] = []
            memo[index] = resolved_list
            resolved_list.extend(resolve_ref(item) for item in value)
            return resolved_list
        memo[index] = value
        return value

    return resolve_value(0)


def get_share_data(root: Any) -> dict[str, Any]:
    """Return the decoded share data object."""
    loader_data = root.get("loaderData", {}) if isinstance(root, dict) else {}
    for route_value in loader_data.values():
        if not isinstance(route_value, dict):
            continue
        server_response = route_value.get("serverResponse")
        if isinstance(server_response, dict) and isinstance(
            server_response.get("data"), dict
        ):
            return server_response["data"]
    raise ValueError("No serverResponse.data object found")


def format_time(timestamp: Any, timezone_hours: int) -> str:
    """Format a UNIX timestamp with the requested timezone offset."""
    if not isinstance(timestamp, (int, float)):
        return ""
    local_tz = timezone(timedelta(hours=timezone_hours))
    offset = f"{timezone_hours:+03d}:00"
    return datetime.fromtimestamp(timestamp, local_tz).strftime(
        f"%Y-%m-%d %H:%M:%S (UTC{offset})"
    )


def text_from_content(content: Any) -> str:
    """Extract visible text from a ChatGPT message content object."""
    if not isinstance(content, dict):
        return ""
    if content.get("content_type") not in {"text", "multimodal_text"}:
        return ""
    parts = content.get("parts") or []
    text_parts = []
    for part in parts:
        if isinstance(part, str):
            text_parts.append(part)
        elif isinstance(part, dict):
            text = part.get("text") or part.get("name")
            if isinstance(text, str):
                text_parts.append(text)
    return "\n".join(text_parts).strip()


def is_runtime_json(text: str) -> bool:
    """Detect assistant runtime events serialized as visible-looking JSON."""
    stripped = text.strip()
    if not stripped.startswith(("{", "[")):
        return False
    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        return False
    if isinstance(parsed, dict):
        keys = set(parsed.keys())
        runtime_keys = {
            "content_type",
            "system1_search_query",
            "search_query",
            "open",
            "find",
            "click",
            "image_query",
            "weather",
            "finance",
        }
        return bool(keys & runtime_keys)
    return isinstance(parsed, list)


def should_keep_message(role: str, text: str) -> bool:
    """Return whether a visible message should be part of the readable export."""
    if not text.strip():
        return False
    if text.strip() == "Original custom instructions no longer available":
        return False
    if text.strip() == "The output of this plugin was redacted.":
        return False
    if role == "assistant" and is_runtime_json(text):
        return False
    return True


def clean_visible_text(text: str, keep_chatgpt_cites: bool) -> str:
    """Clean visible text artifacts that are not useful outside ChatGPT."""
    if keep_chatgpt_cites:
        cleaned = text
    else:
        cleaned = CHATGPT_CITATION_PATTERN.sub("", text)
    return strip_markdown_directive_containers(cleaned)


def strip_markdown_directive_containers(text: str) -> str:
    """Remove ChatGPT-renderer directive container lines outside code fences."""
    lines = []
    in_fence = False
    for line in text.splitlines():
        if is_fence_line(line):
            in_fence = not in_fence
            lines.append(line)
            continue
        if not in_fence and MARKDOWN_DIRECTIVE_PATTERN.match(line.strip()):
            continue
        lines.append(line)
    return "\n".join(lines).strip()


def extract_messages(
    data: dict[str, Any], timezone_hours: int, keep_chatgpt_cites: bool
) -> list[Message]:
    """Extract filtered visible user and assistant messages."""
    messages = []
    for node in data.get("linear_conversation") or []:
        if not isinstance(node, dict):
            continue
        message = node.get("message")
        if not isinstance(message, dict):
            continue
        author = message.get("author") or {}
        role = author.get("role")
        if role not in {"user", "assistant"}:
            continue
        text = text_from_content(message.get("content"))
        if not should_keep_message(role, text):
            continue
        text = clean_visible_text(text, keep_chatgpt_cites)
        messages.append(
            Message(
                role=role,
                text=text,
                created_at=format_time(message.get("create_time"), timezone_hours),
            )
        )
    debug(f"visible messages: {len(messages)}")
    return messages


def build_turns(messages: list[Message]) -> list[Turn]:
    """Build QA turns by attaching assistant candidates to each user message."""
    turns: list[Turn] = []
    current_user: Message | None = None
    assistant_candidates: list[Message] = []

    def finish_turn() -> None:
        nonlocal current_user, assistant_candidates
        if current_user is None:
            return
        substantial = [item for item in assistant_candidates if len(item.text) >= 300]
        assistant = (
            substantial[-1]
            if substantial
            else (assistant_candidates[-1] if assistant_candidates else None)
        )
        turns.append(Turn(index=len(turns) + 1, user=current_user, assistant=assistant))
        current_user = None
        assistant_candidates = []

    for message in messages:
        if message.role == "user":
            finish_turn()
            current_user = message
            assistant_candidates = []
        elif current_user is not None:
            assistant_candidates.append(message)
    finish_turn()
    debug(f"turns: {len(turns)}")
    return turns


def first_line_summary(text: str, max_chars: int = 90) -> str:
    """Create a deterministic short summary from text."""
    compact = " ".join(text.split())
    if len(compact) <= max_chars:
        return compact
    return compact[: max_chars - 1].rstrip() + "..."


def load_plan(path: str | None) -> tuple[str | None, dict[int, TurnPlan]]:
    """Load optional curated export plan."""
    if not path:
        return None, {}
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    title = data.get("title") if isinstance(data.get("title"), str) else None
    rows: dict[int, TurnPlan] = {}
    for item in data.get("turns") or []:
        if not isinstance(item, dict):
            continue
        index = int(item.get("index", 0))
        if index <= 0:
            continue
        rows[index] = TurnPlan(
            index=index,
            export=str(item.get("export") or "keep"),
            heading=str(item.get("heading") or first_line_summary(item.get("q") or "")),
            q=str(item.get("q") or ""),
            a=str(item.get("a") or ""),
            note=str(item.get("note") or ""),
        )
    return title, rows


def escape_table(text: str) -> str:
    """Escape Markdown table cell content."""
    return text.replace("|", "\\|").replace("\n", "<br>")


def is_fence_line(line: str) -> bool:
    """Return whether a line opens or closes a Markdown fence."""
    stripped = line.lstrip()
    return stripped.startswith("```") or stripped.startswith("~~~")


def demote_markdown_headings(text: str, offset: int) -> str:
    """Demote Markdown headings outside fenced code blocks."""
    if offset <= 0:
        return text

    lines = []
    in_fence = False
    for line in text.splitlines():
        if is_fence_line(line):
            in_fence = not in_fence
            lines.append(line)
            continue
        if in_fence:
            lines.append(line)
            continue
        match = MARKDOWN_HEADING_PATTERN.match(line)
        if not match:
            lines.append(line)
            continue
        level = min(MAX_MARKDOWN_HEADING_LEVEL, len(match.group(1)) + offset)
        lines.append(f"{'#' * level}{match.group(2)}")
    return "\n".join(lines)


def render_markdown(
    data: dict[str, Any],
    turns: list[Turn],
    source_label: str,
    source_url: str | None,
    title_override: str | None,
    plan_title: str | None,
    plan_rows: dict[int, TurnPlan],
    timezone_hours: int,
    content_heading_offset: int,
) -> str:
    """Render a readable Markdown transcript."""
    title = (
        title_override or plan_title or str(data.get("title") or "ChatGPT Share Export")
    )
    source = source_url or source_label
    lines = [
        f"# {title}",
        "",
        "## Metadata",
        "",
        f"- Source: {source}",
        "- Source type: ChatGPT shared conversation",
        "- Title source: manual override"
        if title_override
        else (
            "- Title source: export plan"
            if plan_title
            else "- Title source: ChatGPT share page metadata"
        ),
        f"- Conversation created: {format_time(data.get('create_time'), timezone_hours)}",
        f"- Conversation updated: {format_time(data.get('update_time'), timezone_hours)}",
        "- Export mode: base readable QA transcript",
        "- Curation: kept user turns and final assistant answers; omitted hidden runtime events",
        f"- Content heading offset: {content_heading_offset}",
        "",
        "## Turn Index",
        "",
        "| # | Export | Q | A | Note |",
        "| --- | --- | --- | --- | --- |",
    ]

    for turn in turns:
        row = plan_rows.get(turn.index)
        export = row.export if row else "keep"
        q_summary = row.q if row and row.q else first_line_summary(turn.user.text)
        assistant_text = turn.assistant.text if turn.assistant else ""
        a_summary = row.a if row and row.a else first_line_summary(assistant_text)
        note = row.note if row else ""
        lines.append(
            f"| {turn.index} | {escape_table(export)} | {escape_table(q_summary)} | "
            f"{escape_table(a_summary)} | {escape_table(note)} |"
        )
    lines.append("")

    for turn in turns:
        row = plan_rows.get(turn.index)
        if row and row.export == "exclude":
            continue
        heading = (
            row.heading
            if row and row.heading
            else first_line_summary(turn.user.text, 72)
        )
        lines.extend(
            [
                f"## {turn.index}. {heading}",
                "",
                '<h3 align="center"><strong>USER</strong></h3>',
            ]
        )
        if turn.user.created_at:
            lines.append(
                f'<p align="right"><strong>{turn.user.created_at}</strong></p>'
            )
        user_text = demote_markdown_headings(turn.user.text, content_heading_offset)
        assistant_text = (
            turn.assistant.text if turn.assistant else "_No assistant answer found._"
        )
        assistant_text = demote_markdown_headings(
            assistant_text, content_heading_offset
        )
        lines.extend(
            ["", user_text, "", '<h3 align="center"><strong>ASSISTANT</strong></h3>']
        )
        if turn.assistant and turn.assistant.created_at:
            lines.append(
                f'<p align="right"><strong>{turn.assistant.created_at}</strong></p>'
            )
        lines.extend(["", assistant_text, ""])

    return "\n".join(lines).rstrip() + "\n"


def write_messages_json(path: str, messages: list[Message], turns: list[Turn]) -> None:
    """Write extracted visible message data for inspection."""
    payload = {
        "messages": [message.__dict__ for message in messages],
        "turns": [
            {
                "index": turn.index,
                "user": turn.user.__dict__,
                "assistant": turn.assistant.__dict__ if turn.assistant else None,
            }
            for turn in turns
        ],
    }
    Path(path).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def write_plan_template(path: str, data: dict[str, Any], turns: list[Turn]) -> None:
    """Write a starter export plan for agent curation."""
    payload = {
        "title": str(data.get("title") or "ChatGPT Share Export"),
        "turns": [
            {
                "index": turn.index,
                "export": "keep",
                "heading": first_line_summary(turn.user.text, 72),
                "q": first_line_summary(turn.user.text),
                "a": first_line_summary(turn.assistant.text if turn.assistant else ""),
                "note": "",
            }
            for turn in turns
        ],
    }
    Path(path).write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def main() -> int:
    """Run the CLI."""
    global DEBUG_MODE
    args = parse_args()
    DEBUG_MODE = bool(args.log)

    try:
        html, source_label = fetch_or_read_source(args.source)
        table = extract_rsc_table(html)
        root = resolve_rsc_table(table)
        data = get_share_data(root)
        messages = extract_messages(data, args.timezone_hours, args.keep_chatgpt_cites)
        turns = build_turns(messages)
        plan_title, plan_rows = load_plan(args.plan)
        if args.plan_template:
            write_plan_template(args.plan_template, data, turns)
        markdown = render_markdown(
            data=data,
            turns=turns,
            source_label=source_label,
            source_url=args.source_url,
            title_override=args.title,
            plan_title=plan_title,
            plan_rows=plan_rows,
            timezone_hours=args.timezone_hours,
            content_heading_offset=args.content_heading_offset,
        )
        if args.messages_json:
            write_messages_json(args.messages_json, messages, turns)
        if args.output:
            Path(args.output).write_text(markdown, encoding="utf-8")
            print(CLIStyle.color(f"Wrote {args.output}", CLIStyle.COLORS["CONTENT"]))
        else:
            print(markdown, end="")
        if NOISE_PATTERN.search(markdown):
            print(
                CLIStyle.color(
                    "Warning: common noise markers remain in output",
                    CLIStyle.COLORS["WARNING"],
                ),
                file=sys.stderr,
            )
        return 0
    except FileNotFoundError:
        print(
            CLIStyle.color(
                f"Error: source not found: {args.source}", CLIStyle.COLORS["ERROR"]
            ),
            file=sys.stderr,
        )
        return 1
    except (urllib.error.URLError, TimeoutError) as error:
        print(
            CLIStyle.color(
                f"Error: failed to fetch URL: {error}", CLIStyle.COLORS["ERROR"]
            ),
            file=sys.stderr,
        )
        return 1
    except Exception as error:
        if DEBUG_MODE:
            traceback.print_exc()
        print(
            CLIStyle.color(f"Error: {error}", CLIStyle.COLORS["ERROR"]), file=sys.stderr
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
