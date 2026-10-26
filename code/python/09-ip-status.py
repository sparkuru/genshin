# -*- coding: utf-8 -*-
# pip install colorama requests
# Thanks to https://freeipapi.com/ for providing the API
# Route tracing uses the system traceroute (Unix/macOS) or tracert (Windows).

import argparse
import csv
import io
import ipaddress
import json
import logging
import math
import os
import re
import shutil
import socket
import subprocess
import sys
import time
from collections.abc import Iterator
from dataclasses import asdict, dataclass, field
from queue import Empty, Queue
from threading import Thread
from urllib.parse import urlsplit

import requests

if sys.platform == "win32":
    from colorama import init as colorama_init

    colorama_init(autoreset=True)


# CLI Style Template
class CLIStyle:
    """CLI Tool Style Configuration"""

    COLORS = {
        "TITLE": 7,  # Cyan - Main Title
        "SUB_TITLE": 2,  # Red - Subtitle
        "CONTENT": 3,  # Green - Content
        "EXAMPLE": 7,  # Cyan - Examples
        "WARNING": 4,  # Yellow - Warnings
        "ERROR": 2,  # Red - Errors
    }

    @staticmethod
    def color(text: str = "", color: int = COLORS["CONTENT"]) -> str:
        """Unified color function"""
        color_table = {
            0: "{}",  # No color
            1: "\033[1;30m{}\033[0m",  # Black bold
            2: "\033[1;31m{}\033[0m",  # Red bold
            3: "\033[1;32m{}\033[0m",  # Green bold
            4: "\033[1;33m{}\033[0m",  # Yellow bold
            5: "\033[1;34m{}\033[0m",  # Blue bold
            6: "\033[1;35m{}\033[0m",  # Purple bold
            7: "\033[1;36m{}\033[0m",  # Cyan bold
            8: "\033[1;37m{}\033[0m",  # White bold
        }
        return color_table[color].format(text)


class ColoredHelpFormatter(argparse.RawDescriptionHelpFormatter):
    """Apply option colors while preserving structured examples."""

    def _format_action_invocation(self, action: argparse.Action) -> str:
        """Color each option spelling in the generated invocation."""
        invocation = super()._format_action_invocation(action)
        for option in action.option_strings:
            invocation = invocation.replace(
                option, CLIStyle.color(option, CLIStyle.COLORS["SUB_TITLE"]), 1
            )
        return invocation


class ColoredArgumentParser(argparse.ArgumentParser):
    """Unified command line argument parser"""

    def format_help(self) -> str:
        """Render colored descriptions, argument sections, and examples."""
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
            formatter.start_section(
                CLIStyle.color(action_group.title, CLIStyle.COLORS["TITLE"])
            )
            formatter.add_arguments(action_group._group_actions)
            formatter.end_section()

        if self.epilog:
            formatter.add_text(self.epilog)

        return formatter.format_help()


def create_example_text(script_name: str, examples: list, notes: list = None) -> str:
    """Create unified example text"""
    text = f"\n{CLIStyle.color('Examples:', CLIStyle.COLORS['SUB_TITLE'])}"

    for desc, cmd in examples:
        text += f"\n  {CLIStyle.color(f'# {desc}', CLIStyle.COLORS['EXAMPLE'])}"
        text += (
            f"\n  {CLIStyle.color(f'{script_name} {cmd}', CLIStyle.COLORS['CONTENT'])}"
        )
        text += "\n"

    if notes:
        text += f"\n{CLIStyle.color('Notes:', CLIStyle.COLORS['SUB_TITLE'])}"
        for note in notes:
            text += f"\n  {CLIStyle.color(f'- {note}', CLIStyle.COLORS['CONTENT'])}"

    return text


class Config:
    BASE_URL = "https://freeipapi.com/api/json"


@dataclass
class TraceHop:
    """A hop's observed addresses, probe responses, and ICMP annotations."""

    number: int
    addresses: list[str]
    samples_ms: list[float | None]
    annotations: list[str]
    approximate_rtt: bool = False

    def reached(self, target: str) -> bool:
        """Require a timed reply from the target without an error annotation."""
        return (
            any(
                value.split("%", 1)[0] == target.split("%", 1)[0]
                for value in self.addresses
            )
            and any(value is not None for value in self.samples_ms)
            and not self.annotations
        )

    def statistics(self) -> dict:
        """Summarize probe responses without calling missing replies traffic loss."""
        values = [value for value in self.samples_ms if value is not None]
        missing = self.samples_ms.count(None)
        return {
            "sent": len(self.samples_ms),
            "no_reply": missing,
            "no_reply_percent": round(missing / len(self.samples_ms) * 100, 1),
            "min_ms": min(values) if values else None,
            "avg_ms": round(sum(values) / len(values), 3) if values else None,
            "max_ms": max(values) if values else None,
        }


@dataclass
class TraceCapture:
    """Keep partial observations when a probe budget or silence limit is reached."""

    hops: list[TraceHop] = field(default_factory=list)
    diagnostics: list[str] = field(default_factory=list)
    stop_reason: str = "completed"
    error: str | None = None


@dataclass
class TraceDisplay:
    """Group consecutive silent hops while retaining every hop in the report."""

    target: str
    silent: list[TraceHop] = field(default_factory=list)

    def add(self, hop: TraceHop) -> None:
        """Print responding hops and summarize runs of silent hops."""
        if not hop_has_reply(hop):
            if self.silent and hop.number != self.silent[-1].number + 1:
                self.flush()
            self.silent.append(hop)
            if len(self.silent) == 1:
                print(
                    CLIStyle.color(
                        f"{hop.number:>3}  *  No reply; grouping further silent hops...",
                        CLIStyle.COLORS["WARNING"],
                    ),
                    flush=True,
                )
            return
        self.flush()
        print_trace_hop(hop, self.target)

    def flush(self) -> None:
        """Describe the complete silent range once, without diagnosing an outage."""
        if len(self.silent) > 1:
            first, last = self.silent[0].number, self.silent[-1].number
            probes = sum(len(hop.samples_ms) for hop in self.silent)
            print(
                CLIStyle.color(
                    f"     Hops {first}-{last}: no replies to {probes} probes; "
                    "this does not prove an outage.",
                    CLIStyle.COLORS["WARNING"],
                ),
                flush=True,
            )
        self.silent.clear()


def hop_has_reply(hop: TraceHop) -> bool:
    """Count timed responses or explicit ICMP errors as observed replies."""
    return bool(hop.annotations) or any(value is not None for value in hop.samples_ms)


def resolve_trace_target(value: str, version: int | None) -> str:
    """Resolve one numeric destination, preferring IPv4 unless explicitly selected."""
    value = value.strip()
    if not value or any(character.isspace() for character in value):
        raise ValueError("Trace target must be a single IP address or domain")
    try:
        address = ipaddress.ip_address(value.strip("[]"))
    except ValueError:
        parsed = urlsplit(value if "://" in value else f"//{value}")
        host = parsed.hostname
        if not host or host.startswith("-"):
            raise ValueError("Trace target must be an IP address or domain")
        family = {4: socket.AF_INET, 6: socket.AF_INET6}.get(version, socket.AF_UNSPEC)
        try:
            results = socket.getaddrinfo(host, None, family, socket.SOCK_DGRAM)
        except socket.gaierror as error:
            raise ValueError(f"Cannot resolve trace target: {host}: {error}") from error
        results.sort(key=lambda result: result[0] != socket.AF_INET)
        return str(ipaddress.ip_address(results[0][4][0]))
    if version is not None and address.version != version:
        raise ValueError(f"Target address does not match IPv{version}")
    return str(address)


def classify_address(value: str) -> str:
    """Distinguish common address scopes without external lookup services."""
    address = ipaddress.ip_address(value)
    checks = (
        (address.is_loopback, "loopback"),
        (address.is_link_local, "link-local"),
        (address.is_multicast, "multicast"),
        (address.is_unspecified, "unspecified"),
        (
            address.version == 4 and address in ipaddress.ip_network("100.64.0.0/10"),
            "shared address space (often CGNAT)",
        ),
        (address.is_reserved, "reserved"),
        (address.is_private, "private/special-use"),
    )
    return next((label for matches, label in checks if matches), "public")


def parse_trace_hop(line: str) -> TraceHop | None:
    """Parse numeric traceroute/tracert rows, including multiple responding addresses."""
    match = re.match(r"^\s*(\d+)\s+(.+)$", line)
    if not match:
        return None
    body = match.group(2)
    probes = re.findall(r"\*|<?\s*\d+(?:[.,]\d+)?\s*ms\b", body)
    if not probes:
        return None
    addresses = []
    for token in body.split():
        try:
            address = str(ipaddress.ip_address(token.strip("()[],")))
        except ValueError:
            continue
        if address not in addresses:
            addresses.append(address)
    samples = [
        None
        if probe == "*"
        else float(re.sub(r"[<\s]|ms", "", probe).replace(",", "."))
        for probe in probes
    ]
    annotations = re.findall(r"![\w<>-]*", body)
    if re.search(r"\b(unreachable|prohibited)\b", body, re.IGNORECASE):
        annotations.append("!unreachable")
    return TraceHop(
        number=int(match.group(1)),
        addresses=addresses,
        samples_ms=samples,
        annotations=annotations,
        approximate_rtt=any("<" in probe for probe in probes),
    )


def describe_trace_hop(hop: TraceHop, target: str) -> str:
    """Explain observations without assigning a fault to a router."""
    if hop.annotations:
        meanings = {
            "!H": "host unreachable",
            "!N": "network unreachable",
            "!P": "protocol unreachable",
            "!F": "fragmentation needed",
            "!X": "administratively prohibited",
        }
        return "; ".join(
            meanings.get(code, f"ICMP annotation {code}") for code in hop.annotations
        )
    if not any(value is not None for value in hop.samples_ms):
        return "No reply; this alone does not prove an outage"
    if hop.reached(target):
        return "Target replied; service availability is not tested"
    scopes = list(dict.fromkeys(classify_address(value) for value in hop.addresses))
    description = ", ".join(scopes) or "Reply without a parsed address"
    if len(hop.addresses) > 1:
        description += "; multiple responders at this hop"
    return description


def build_trace_command(args: argparse.Namespace, target: str) -> tuple[list[str], str]:
    """Choose a native backend and reject unsupported options explicitly."""
    version = ipaddress.ip_address(target).version
    method = args.method or ("icmp" if sys.platform == "win32" else "udp")
    if args.port is not None and method != "tcp":
        raise ValueError("--port requires --method tcp")
    if sys.platform == "win32":
        executable = shutil.which("tracert")
        if not executable:
            raise FileNotFoundError("tracert was not found in PATH")
        if method != "icmp" or args.queries != 3:
            raise ValueError(
                "Windows tracert supports ICMP and exactly 3 probes per hop"
            )
        return [
            executable,
            "-d",
            f"-{version}",
            "-h",
            str(args.max_hops),
            "-w",
            str(math.ceil(args.probe_timeout * 1000)),
            target,
        ], method
    backend = (
        "traceroute6" if sys.platform == "darwin" and version == 6 else "traceroute"
    )
    executable = shutil.which(backend)
    if not executable:
        raise FileNotFoundError(
            f"{backend} was not found in PATH. Install your system's traceroute package."
        )
    if method == "tcp" and not sys.platform.startswith("linux"):
        raise ValueError("TCP tracing is supported only with Linux traceroute")
    command = [executable, "-n", "-m", str(args.max_hops), "-q", str(args.queries)]
    command.extend(["-w", str(args.probe_timeout)])
    if sys.platform.startswith("linux"):
        command.extend([f"-{version}", "-N", "1"])
    if method == "icmp":
        command.append("-I")
    if method == "tcp":
        command.extend(["-T", "-p", str(args.port or 443)])
    command.append(target)
    return command, method


def read_trace_lines(process: subprocess.Popen[str], lines: Queue[str | None]) -> None:
    """Forward backend output so the main thread can enforce a deadline."""
    try:
        if process.stdout is not None:
            for line in process.stdout:
                lines.put(line)
    finally:
        lines.put(None)


def iter_trace_lines(lines: Queue[str | None], deadline: float) -> Iterator[str]:
    """Yield backend lines until EOF, enforcing the overall trace deadline."""
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("Trace backend exceeded its runtime limit")
        try:
            line = lines.get(timeout=min(remaining, 0.2))
        except Empty:
            continue
        if line is None:
            return
        yield line


def process_trace_lines(
    lines: Queue[str | None],
    deadline: float,
    args: argparse.Namespace,
    target: str,
    capture: TraceCapture,
) -> None:
    """Stream observations and stop an automatic attempt after initial silence."""
    display = TraceDisplay(target) if args.format == "text" else None
    silence_limit = getattr(args, "silence_limit", 0)
    try:
        for line in iter_trace_lines(lines, deadline):
            logging.debug("Backend: %s", line.rstrip())
            hop = parse_trace_hop(line)
            if hop is None:
                capture.diagnostics.append(line.strip())
                continue
            capture.hops.append(hop)
            if display is not None:
                display.add(hop)
            if (
                silence_limit
                and len(capture.hops) >= silence_limit
                and not any(hop_has_reply(observed) for observed in capture.hops)
            ):
                capture.stop_reason = "initial_silence"
                return
    finally:
        if display is not None:
            display.flush()


def print_trace_hop(hop: TraceHop, target: str) -> None:
    """Display hop timings, missing replies, and a short explanation."""
    statistics = hop.statistics()
    timings = "-"
    if statistics["avg_ms"] is not None:
        timings = "/".join(
            f"{statistics[key]:.2f}" for key in ("min_ms", "avg_ms", "max_ms")
        )
    addresses = ", ".join(hop.addresses) or "*"
    missing = f"{statistics['no_reply']}/{statistics['sent']}"
    color = (
        CLIStyle.COLORS["WARNING"]
        if statistics["no_reply"] or hop.annotations
        else CLIStyle.COLORS["CONTENT"]
    )
    print(
        CLIStyle.color(
            f"{hop.number:>3}  {addresses:<39} {timings:<26} {missing}", color
        ),
        flush=True,
    )
    print(CLIStyle.color(f"     {describe_trace_hop(hop, target)}", color), flush=True)


def collect_trace_hops(
    command: list[str], args: argparse.Namespace, target: str
) -> TraceCapture:
    """Bound native probes, preserving observations and cleaning up child processes."""
    lines: Queue[str | None] = Queue()
    capture = TraceCapture()
    native_budget = args.max_hops * args.queries * args.probe_timeout + 10
    deadline = time.monotonic() + min(
        native_budget, getattr(args, "attempt_budget", native_budget)
    )
    environment = dict(os.environ, LC_ALL="C", LANG="C")
    with subprocess.Popen(
        command,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=environment,
    ) as process:
        reader = Thread(target=read_trace_lines, args=(process, lines), daemon=True)
        reader.start()
        try:
            process_trace_lines(lines, deadline, args, target, capture)
            if capture.stop_reason != "completed":
                return capture
            return_code = process.wait(
                timeout=max(0.01, min(2, deadline - time.monotonic()))
            )
            if return_code != 0 or not capture.hops:
                details = (
                    " ".join(capture.diagnostics[-5:]) or "no hop rows were recognized"
                )
                capture.stop_reason = "backend_error"
                capture.error = f"Trace backend failed (exit {return_code}): {details}. Use --log for raw output."
        except (TimeoutError, subprocess.TimeoutExpired):
            capture.stop_reason = "time_budget"
        finally:
            if process.poll() is None:
                process.kill()
            process.wait()
            reader.join(timeout=1)
    return capture


def create_trace_report(target: str, method: str, hops: list[TraceHop]) -> dict:
    """Build a serializable report with cautious interpretations of missing replies."""
    reached_hops = [hop.number for hop in hops if hop.reached(target)]
    notes = [
        "RTT is a round trip from this computer, not the delay between adjacent hops.",
        "No-reply counts describe these probes, not application packet loss.",
        "A slow or silent intermediate hop alone does not identify a faulty link.",
        "Reaching the target does not confirm that its application service works.",
    ]
    if any(hop.samples_ms.count(None) for hop in hops[:-1]) and reached_hops:
        notes.append(
            "The target replied despite missing intermediate replies; those gaps do not prove an outage."
        )
    if any(hop.approximate_rtt for hop in hops):
        notes.append(
            "Values reported as <1 ms use 1 ms as an upper bound in timing statistics."
        )
    if not reached_hops:
        notes.append(
            "Target arrival is unconfirmed; filtering, probe type, or the hop limit may explain this."
        )
    return {
        "target_ip": target,
        "ip_version": ipaddress.ip_address(target).version,
        "method": method,
        "reached": bool(reached_hops),
        "target_hop": reached_hops[0] if reached_hops else None,
        "responding_hops": sum(hop_has_reply(hop) for hop in hops),
        "hops": [
            {
                **asdict(hop),
                **hop.statistics(),
                "description": describe_trace_hop(hop, target),
            }
            for hop in hops
        ],
        "notes": notes,
    }


def plan_trace_methods(args: argparse.Namespace) -> list[str]:
    """Choose supported fallbacks, respecting an explicitly requested TCP port."""
    if args.method not in (None, "auto"):
        if args.port is not None and args.method != "tcp":
            raise ValueError("--port requires --method tcp or auto")
        return [args.method]
    if sys.platform == "win32":
        if args.port is not None:
            raise ValueError("Windows tracert cannot trace a TCP port")
        return ["icmp"]
    if sys.platform.startswith("linux"):
        return (
            ["tcp", "udp", "icmp"] if args.port is not None else ["udp", "tcp", "icmp"]
        )
    if args.port is not None:
        raise ValueError("TCP tracing is supported only with Linux traceroute")
    return ["udp", "icmp"]


def run_trace_attempt(args: argparse.Namespace, target: str) -> dict:
    """Run one protocol independently and retain partial results or backend errors."""
    command, method = build_trace_command(args, target)
    logging.debug("Trace command: %r", command)
    if args.format == "text":
        port = f" port {args.port or 443}" if method == "tcp" else ""
        print(
            CLIStyle.color(
                f"\nAttempt {args.attempt_number}: {method.upper()}{port} | "
                f"up to {args.attempt_budget:.1f}s",
                CLIStyle.COLORS["TITLE"],
            ),
            flush=True,
        )
        print(
            CLIStyle.color(
                "Hop  Responding address                      RTT min/avg/max (ms)       No reply",
                CLIStyle.COLORS["SUB_TITLE"],
            ),
            flush=True,
        )
    started = time.monotonic()
    try:
        capture = collect_trace_hops(command, args, target)
    except OSError as error:
        capture = TraceCapture(stop_reason="backend_error", error=str(error))
    report = create_trace_report(target, method, capture.hops)
    report.update(
        backend=os.path.basename(command[0]),
        stop_reason=capture.stop_reason,
        error=capture.error,
        elapsed_seconds=round(time.monotonic() - started, 3),
        settings={
            "max_hops": args.max_hops,
            "queries": args.queries,
            "probe_timeout": args.probe_timeout,
            "tcp_port": (args.port or 443) if method == "tcp" else None,
            "silence_limit": args.silence_limit,
            "time_budget": args.attempt_budget,
        },
    )
    report["status"] = trace_status([report])
    if capture.error:
        logging.warning("%s probe failed: %s", method.upper(), capture.error)
    if args.format == "text":
        print_trace_attempt_result(report)
    return report


def trace_status(attempts: list[dict]) -> str:
    """Distinguish target replies, intermediate replies, silence, and tool errors."""
    if any(attempt["reached"] for attempt in attempts):
        return "reached"
    if all(attempt["error"] for attempt in attempts):
        return "error"
    if any(attempt["responding_hops"] for attempt in attempts):
        return "partial"
    return "no_reply"


def print_trace_attempt_result(attempt: dict) -> None:
    """Explain why an attempt ended without calling silence a network failure."""
    reasons = {
        "completed": "backend finished",
        "initial_silence": "stopped after initial silent hops to try another method",
        "time_budget": "probe time budget reached; later replies may be hidden",
        "backend_error": "backend error; this method could not complete",
    }
    message = (
        f"{attempt['method'].upper()}: {attempt['status'].replace('_', ' ')}; "
        f"{attempt['responding_hops']} responding hops; {reasons[attempt['stop_reason']]}"
    )
    print(
        CLIStyle.color(
            message,
            CLIStyle.COLORS["CONTENT"]
            if attempt["reached"]
            else CLIStyle.COLORS["WARNING"],
        ),
        flush=True,
    )


def combine_trace_attempts(attempts: list[dict], args: argparse.Namespace) -> dict:
    """Select one observed path for compatibility, keeping every attempt separate."""
    best_index = max(
        range(len(attempts)),
        key=lambda index: (
            attempts[index]["reached"],
            attempts[index]["responding_hops"],
            attempts[index]["error"] is None,
            len(attempts[index]["hops"]),
        ),
    )
    report = dict(attempts[best_index])
    report.update(
        status=trace_status(attempts),
        attempts=attempts,
        selected_attempt=best_index + 1,
        requested_method=args.method or "auto",
        target_input=args.trace,
    )
    report["notes"] = list(report["notes"])
    report["next_steps"] = []
    if report["reached"] and any(
        attempt["status"] == "no_reply" for attempt in attempts
    ):
        report["notes"].append(
            "Probe methods behaved differently in the observed ranges. Filtering or response policy "
            "may explain this; the earlier silence does not prove an outage."
        )
    if any(
        attempt["stop_reason"] in ("initial_silence", "time_budget")
        for attempt in attempts
    ):
        report["notes"].append(
            "Some attempts ended early. Silent initial hops do not exclude later replies; "
            "increase --trace-budget or select a single --method for a longer trace."
        )
    if not report["reached"]:
        report["next_steps"] = [
            "Test the actual destination service normally; route-probe silence does not prove it is down.",
            "For SSH on Linux, use --method tcp --port 22; for HTTPS, use --method tcp --port 443.",
            "Compare from another network; this trace cannot locate where silent probes were filtered.",
        ]
    if report["status"] == "error":
        report["next_steps"] = [
            "Inspect backend errors with --log and choose a supported probe method; "
            "some methods require system permissions."
        ]
    return report


def output_trace_report(report: dict, output_format: str) -> None:
    """Render a summary or emit clean machine-readable JSON/CSV."""
    if output_format == "json":
        print(CLIStyle.color(json.dumps(report, indent=2), 0))
        return
    if output_format == "csv":
        buffer = io.StringIO()
        fields = [
            "target_ip",
            "attempt",
            "method",
            "tcp_port",
            "reached",
            "status",
            "stop_reason",
            "error",
            "hop",
            "addresses",
            "sent",
            "no_reply",
            "no_reply_percent",
            "min_ms",
            "avg_ms",
            "max_ms",
            "approximate_rtt",
            "annotations",
            "description",
        ]
        writer = csv.DictWriter(buffer, fieldnames=fields, lineterminator="\n")
        writer.writeheader()
        for index, attempt in enumerate(report.get("attempts", [report]), 1):
            for hop in attempt["hops"] or [{}]:
                row = {key: hop[key] for key in fields if key in hop}
                row.update(
                    target_ip=report["target_ip"],
                    attempt=index,
                    method=attempt["method"],
                    tcp_port=attempt["settings"]["tcp_port"],
                    reached=attempt["reached"],
                    status=attempt["status"],
                    stop_reason=attempt["stop_reason"],
                    error=attempt["error"],
                    hop=hop.get("number", ""),
                    addresses=";".join(hop.get("addresses", [])),
                    annotations=";".join(hop.get("annotations", [])),
                )
                writer.writerow(row)
        print(CLIStyle.color(buffer.getvalue(), 0), end="")
        return
    summaries = {
        "reached": f"Target replied at hop {report['target_hop']} using {report['method'].upper()}.",
        "partial": "Intermediate nodes replied, but target arrival was not confirmed.",
        "no_reply": "No route-probe replies observed; target availability remains unknown.",
        "error": "Probe tools could not complete; target availability remains unknown.",
    }
    summary = summaries[report["status"]]
    print(CLIStyle.color(f"\nResult: {summary}", CLIStyle.COLORS["TITLE"]))
    for note in report["notes"]:
        print(CLIStyle.color(f"  - {note}", CLIStyle.COLORS["WARNING"]))
    for step in report.get("next_steps", []):
        print(CLIStyle.color(f"  Next: {step}", CLIStyle.COLORS["CONTENT"]))


def run_trace(args: argparse.Namespace) -> int:
    """Run bounded automatic fallbacks, or one explicitly selected probe method."""
    target = resolve_trace_target(args.trace, args.ip_version)
    methods = plan_trace_methods(args)
    budget = getattr(args, "trace_budget", 45.0)
    silence_limit = getattr(args, "silent_hops", 5)
    automatic = args.method in (None, "auto")
    started = time.monotonic()
    deadline = started + budget
    if args.format == "text":
        print(
            CLIStyle.color(
                f"Route trace: {args.trace} -> {target}", CLIStyle.COLORS["TITLE"]
            ),
            flush=True,
        )
        print(
            CLIStyle.color(
                f"IPv{ipaddress.ip_address(target).version} | "
                f"{'AUTO: ' if automatic else ''}{' -> '.join(method.upper() for method in methods)} | "
                f"max {args.max_hops} hops | {args.queries} probes/hop | "
                f"{args.probe_timeout:g}s probe timeout | {budget:g}s total probe budget | "
                "no third-party API lookups",
                CLIStyle.COLORS["CONTENT"],
            ),
            flush=True,
        )
    attempts = []
    for index, method in enumerate(methods):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            break
        attempt_args = argparse.Namespace(**vars(args))
        attempt_args.method = method
        attempt_args.port = args.port if method == "tcp" else None
        attempt_args.attempt_number = index + 1
        attempt_args.attempt_budget = remaining / (len(methods) - index)
        attempt_args.silence_limit = (
            silence_limit if automatic and index + 1 < len(methods) else 0
        )
        attempts.append(run_trace_attempt(attempt_args, target))
        if attempts[-1]["reached"]:
            break
        if args.format == "text" and index + 1 < len(methods):
            print(
                CLIStyle.color(
                    f"Trying {methods[index + 1].upper()} independently; paths will not be combined.",
                    CLIStyle.COLORS["WARNING"],
                ),
                flush=True,
            )
    if not attempts:
        raise TimeoutError("No probe time remained to start a trace attempt")
    report = combine_trace_attempts(attempts, args)
    report["elapsed_seconds"] = round(time.monotonic() - started, 3)
    report["trace_budget"] = budget
    report["unattempted_methods"] = methods[len(attempts) :]
    if report["unattempted_methods"] and not report["reached"]:
        report["notes"].append(
            "The total probe budget expired before all planned methods could run."
        )
    output_trace_report(report, args.format)
    return 0 if report["reached"] else (1 if report["status"] == "error" else 2)


def execute_request(url: str, timeout: int = 5) -> str:
    """Execute HTTP request and return response text"""
    try:
        response = requests.get(
            url,
            allow_redirects=True,
            timeout=(min(timeout, 5), max(timeout, 10)),
            headers={
                "Accept": "application/json",
                "User-Agent": "ip-status.py/1.0 (+requests)",
            },
        )
        response.raise_for_status()
        return response.text.strip()
    except requests.Timeout:
        print(CLIStyle.color("\nError: Request timed out", CLIStyle.COLORS["ERROR"]))
        print(
            CLIStyle.color(
                "Please check your network connection or try again later",
                CLIStyle.COLORS["WARNING"],
            )
        )
        exit(1)
    except requests.RequestException as e:
        print(
            CLIStyle.color(
                f"\nError requesting API: {str(e)}", CLIStyle.COLORS["ERROR"]
            )
        )
        print(
            CLIStyle.color(
                "Please make sure requests is installed and network is accessible",
                CLIStyle.COLORS["WARNING"],
            )
        )
        exit(1)


class IPRSSClient:
    def __init__(self, args: dict) -> None:
        self.ip = ""
        self.args = args

    def get_ip_with_location(self) -> None:
        """Get public IP address with location details"""
        if self.args["ip"] != "":
            self.ip = self.args["ip"]
            url = f"{Config.BASE_URL}/{self.ip}"
        else:
            url = Config.BASE_URL
        response = execute_request(url, timeout=self.args["timeout"])
        response_json = json.loads(response)

        if response_json.get("ipAddress"):
            print(CLIStyle.color("IP with Location:", CLIStyle.COLORS["TITLE"]))
        else:
            print(CLIStyle.color("IP Query Result:", CLIStyle.COLORS["TITLE"]))

        self.ip = response_json.get("ipAddress", self.ip)
        format_dict(response_json, indent=2, exclude_keys=[])


def format_dict(data: dict, indent=0, exclude_keys=None):
    """Format dictionary output"""
    if exclude_keys is None:
        exclude_keys = []

    for key, value in data.items():
        if key in exclude_keys:
            continue
        if isinstance(value, dict):
            print(
                " " * indent + f"{CLIStyle.color(key, CLIStyle.COLORS['SUB_TITLE'])}:"
            )
            format_dict(value, indent + 4, exclude_keys)
        else:
            if isinstance(value, bool):
                value_color = CLIStyle.COLORS["WARNING"]
            elif isinstance(value, (int, float)):
                value_color = CLIStyle.COLORS["EXAMPLE"]
            else:
                value_color = CLIStyle.COLORS["CONTENT"]

            print(
                " " * indent
                + f"{CLIStyle.color(key, CLIStyle.COLORS['SUB_TITLE'])}: {CLIStyle.color(str(value), value_color)}"
            )


def check_ip_and_return_str(ip: str) -> str:
    """Check if IP address is valid and extract it, or resolve domain

    Args:
        ip (str): Input IP address string or domain name

    Returns:
        str: Extracted valid IP address

    Raises:
        AssertionError: When no valid IP address is found
    """
    ip_match = re.search(r"\d+\.\d+\.\d+\.\d+", ip)
    if ip_match:
        return ip_match.group()

    domain = re.sub(r"^(https?://)?", "", ip)
    domain = re.sub(r"[:/].*$", "", domain)

    try:
        resolved_ip = socket.gethostbyname(domain)
        print(
            CLIStyle.color(
                f"Resolved {domain} -> {resolved_ip}", CLIStyle.COLORS["WARNING"]
            )
        )
        return resolved_ip
    except socket.gaierror:
        raise AssertionError(f"Cannot resolve domain or find valid IP: {domain}")


def main() -> int:
    """Dispatch IP information lookups or the optional route trace."""
    script_name = os.path.basename(sys.argv[0])

    examples = [
        ("Check your own IP", ""),
        ("Check specific IP", "8.8.8.8"),
        ("Show request URL", "-c"),
        ("Output as JSON", "-f json"),
        ("Trace a domain without third-party API lookups", "--trace example.com"),
        ("Start automatic tracing with the SSH port", "--trace example.com --port 22"),
        (
            "Use only UDP with a longer budget",
            "--trace example.com --method udp --trace-budget 120",
        ),
        ("Trace an IPv6 address", "--trace ::1 -6"),
        (
            "Trace using TCP port 443 on Linux",
            "--trace example.com --method tcp --port 443",
        ),
        ("Save trace results as JSON", "--trace 1.1.1.1 -f json"),
    ]

    notes = [
        "Shows IP address information",
        "Includes country/region, city, ISP",
        "Shows geographical location (lat/long)",
        "Displays timezone information",
        "Use position argument for specific IP lookup",
        "Trace mode requires traceroute on Unix/macOS or tracert on Windows",
        "Windows tracing uses ICMP with 3 probes per hop; TCP tracing requires Linux",
        "Trace mode does not query IP location APIs or reverse DNS",
        "Default auto mode tries supported UDP/TCP/ICMP methods independently and stops when the target replies",
        "Auto mode reserves time for fallbacks and can stop after initial silence; later replies may be hidden",
        "JSON keeps every attempt separately; top-level hops belong only to the selected attempt",
        "Trace exit codes: 0 = target replied, 2 = arrival unconfirmed, 1 = error",
        "JSON/CSV output in trace mode contains no ANSI colors",
    ]

    ap = ColoredArgumentParser(
        description="IP Address Lookup and Explained Route Trace",
        formatter_class=ColoredHelpFormatter,
        epilog=create_example_text(script_name, examples, notes),
    )

    ap.add_argument(
        "ip",
        nargs="?",
        type=str,
        metavar=CLIStyle.color("IP", CLIStyle.COLORS["CONTENT"]),
        help=CLIStyle.color("Specify IP address to lookup", CLIStyle.COLORS["CONTENT"]),
    )
    ap.add_argument(
        "-c",
        "--cmd",
        action="store_true",
        help=CLIStyle.color(
            "Show corresponding request URL", CLIStyle.COLORS["CONTENT"]
        ),
    )
    ap.add_argument(
        "-f",
        "--format",
        choices=["text", "json", "csv"],
        default="text",
        help=CLIStyle.color(
            "Specify output format (default: text)", CLIStyle.COLORS["CONTENT"]
        ),
    )
    ap.add_argument(
        "-t",
        "--timeout",
        type=int,
        default=5,
        metavar=CLIStyle.color("SECONDS", CLIStyle.COLORS["CONTENT"]),
        help=CLIStyle.color(
            "Set request timeout (default: 5s)", CLIStyle.COLORS["CONTENT"]
        ),
    )

    trace_group = ap.add_argument_group("Route Trace Options")
    options = [
        (
            ("--trace",),
            {
                "metavar": "TARGET",
                "help": "Trace an IP address or domain instead of querying IP information",
            },
        ),
        (
            ("--max-hops",),
            {
                "type": int,
                "metavar": "N",
                "help": "Maximum hops, 1-255 (default: 30)",
            },
        ),
        (
            ("--queries",),
            {
                "type": int,
                "metavar": "N",
                "help": "Probes per hop, 1-10 (default: 3; Windows: 3 only)",
            },
        ),
        (
            ("--probe-timeout",),
            {
                "type": float,
                "metavar": "SECONDS",
                "help": "Wait per probe, 0.01-60 seconds (default: 1); separate from API timeout",
            },
        ),
        (
            ("--method",),
            {
                "choices": ["auto", "udp", "icmp", "tcp"],
                "help": "Probe method (default: auto); explicit methods disable fallback; TCP requires Linux",
            },
        ),
        (
            ("--port",),
            {
                "type": int,
                "metavar": "PORT",
                "help": "TCP destination port, 1-65535 (default: 443); auto mode tries TCP first when specified",
            },
        ),
        (
            ("--trace-budget",),
            {
                "type": float,
                "metavar": "SECONDS",
                "help": "Total probe time budget, 1-3600 seconds (default: 45); auto mode shares it across methods",
            },
        ),
        (
            ("--silent-hops",),
            {
                "type": int,
                "metavar": "N",
                "help": "Auto mode: switch methods after N initial silent hops, 0-255 (default: 5; 0 disables)",
            },
        ),
    ]
    for names, settings in options:
        settings["help"] = CLIStyle.color(settings["help"], CLIStyle.COLORS["CONTENT"])
        if "metavar" in settings:
            settings["metavar"] = CLIStyle.color(
                settings["metavar"], CLIStyle.COLORS["CONTENT"]
            )
        trace_group.add_argument(*names, **settings)
    family_group = trace_group.add_mutually_exclusive_group()
    family_group.add_argument(
        "-4",
        dest="ip_version",
        action="store_const",
        const=4,
        help=CLIStyle.color("Use IPv4 in trace mode", CLIStyle.COLORS["CONTENT"]),
    )
    family_group.add_argument(
        "-6",
        dest="ip_version",
        action="store_const",
        const=6,
        help=CLIStyle.color("Use IPv6 in trace mode", CLIStyle.COLORS["CONTENT"]),
    )
    ap.add_argument(
        "--log",
        action="store_true",
        help=CLIStyle.color(
            "Write debug details and raw trace output to stderr",
            CLIStyle.COLORS["CONTENT"],
        ),
    )
    namespace = ap.parse_args()
    logging.basicConfig(
        level=logging.DEBUG if namespace.log else logging.WARNING,
        format="%(levelname)s: %(message)s",
    )
    trace_settings = (
        namespace.max_hops,
        namespace.queries,
        namespace.probe_timeout,
        namespace.method,
        namespace.port,
        namespace.ip_version,
        namespace.trace_budget,
        namespace.silent_hops,
    )
    if namespace.trace is None and any(value is not None for value in trace_settings):
        ap.error("Route trace options require --trace TARGET")
    if namespace.trace is not None:
        namespace.max_hops = 30 if namespace.max_hops is None else namespace.max_hops
        namespace.queries = 3 if namespace.queries is None else namespace.queries
        namespace.probe_timeout = (
            1.0 if namespace.probe_timeout is None else namespace.probe_timeout
        )
        namespace.trace_budget = (
            45.0 if namespace.trace_budget is None else namespace.trace_budget
        )
        namespace.silent_hops = (
            5 if namespace.silent_hops is None else namespace.silent_hops
        )
        if namespace.ip or namespace.cmd:
            ap.error("--trace cannot be combined with a positional IP or --cmd")
        if not 1 <= namespace.max_hops <= 255 or not 1 <= namespace.queries <= 10:
            ap.error("--max-hops must be 1-255 and --queries must be 1-10")
        if not 0.01 <= namespace.probe_timeout <= 60:
            ap.error("--probe-timeout must be between 0.01 and 60 seconds")
        if namespace.port is not None and not 1 <= namespace.port <= 65535:
            ap.error("--port must be between 1 and 65535")
        if not 1 <= namespace.trace_budget <= 3600:
            ap.error("--trace-budget must be between 1 and 3600 seconds")
        if not 0 <= namespace.silent_hops <= 255:
            ap.error("--silent-hops must be between 0 and 255")
        return run_trace(namespace)
    args = vars(namespace)

    if args["ip"]:
        args["ip"] = check_ip_and_return_str(args["ip"])
    else:
        args["ip"] = ""

    if args["cmd"]:
        print(CLIStyle.color("Request URL:", CLIStyle.COLORS["TITLE"]))
        if args["ip"]:
            print(
                CLIStyle.color(
                    f"{' ' * 2}{Config.BASE_URL}/{args['ip']}",
                    CLIStyle.COLORS["CONTENT"],
                )
            )
        else:
            print(
                CLIStyle.color(
                    f"{' ' * 2}{Config.BASE_URL}", CLIStyle.COLORS["CONTENT"]
                )
            )
        return 0

    client = IPRSSClient(args)
    client.get_ip_with_location()
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(
            CLIStyle.color("\nOperation cancelled by user", CLIStyle.COLORS["ERROR"]),
            file=sys.stderr,
        )
        sys.exit(130)
    except FileNotFoundError as e:
        print(
            CLIStyle.color(f"\nError: {e}", CLIStyle.COLORS["ERROR"]), file=sys.stderr
        )
        sys.exit(1)
    except Exception as e:
        logging.debug("Operation failed", exc_info=True)
        print(
            CLIStyle.color(f"\nError: {str(e)}", CLIStyle.COLORS["ERROR"]),
            file=sys.stderr,
        )
        sys.exit(1)
