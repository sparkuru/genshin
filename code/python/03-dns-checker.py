# -*- coding: utf-8 -*-
"""Inspect DNS configuration sources and optionally test name resolution."""

import argparse
import ipaddress
import os
import platform
import re
import shlex
import shutil
import subprocess
import sys
import traceback
from dataclasses import dataclass, field
from pathlib import Path
from typing import TextIO


DEBUG_MODE = False


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
        """Apply semantic colors when stdout is an interactive terminal."""
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
        if not sys.stdout.isatty() or "NO_COLOR" in os.environ:
            return text
        return color_table[color].format(text)

    @staticmethod
    def emit(text: str, role: str = "CONTENT", file: TextIO | None = None) -> None:
        """Print text through the shared style layer."""
        print(CLIStyle.color(text, CLIStyle.COLORS[role]), file=file, flush=True)


class ColoredHelpFormatter(argparse.RawDescriptionHelpFormatter):
    """Format CLI actions using semantic option and metavar colors."""

    def _format_action(self, action: argparse.Action) -> str:
        """Color actions after argparse measures and wraps their plain text."""
        rendered = super()._format_action(action)
        invocation = super()._format_action_invocation(action)
        lines = []
        for line in rendered.splitlines(keepends=True):
            content = line.removesuffix("\n")
            if not content.strip():
                lines.append(line)
                continue
            if invocation in content:
                prefix, _, suffix = content.partition(invocation)
                colored = (
                    prefix
                    + CLIStyle.color(invocation, CLIStyle.COLORS["SUB_TITLE"])
                    + CLIStyle.color(suffix, CLIStyle.COLORS["CONTENT"])
                )
            else:
                colored = CLIStyle.color(content, CLIStyle.COLORS["CONTENT"])
            lines.append(colored + ("\n" if line.endswith("\n") else ""))
        return "".join(lines)

    def _format_usage(
        self,
        usage: str | None,
        actions: list[argparse.Action],
        groups: list[argparse._MutuallyExclusiveGroup],
        prefix: str | None,
    ) -> str:
        """Color usage tokens only after their line wrapping is complete."""
        rendered = super()._format_usage(usage, actions, groups, prefix)
        tokens = {option for action in actions for option in action.option_strings}
        tokens.update(
            action.metavar for action in actions if isinstance(action.metavar, str)
        )
        if not tokens:
            return rendered
        pattern = (
            r"(?<![\w-])(?:"
            + "|".join(
                re.escape(token) for token in sorted(tokens, key=len, reverse=True)
            )
            + r")(?![\w-])"
        )
        return re.sub(
            pattern,
            lambda match: CLIStyle.color(match[0], CLIStyle.COLORS["SUB_TITLE"]),
            rendered,
        )


class ColoredArgumentParser(argparse.ArgumentParser):
    """Provide styled help and errors while retaining argparse validation."""

    def format_help(self) -> str:
        """Build help with semantic headings and structured examples."""
        formatter = self._get_formatter()
        if self.description:
            formatter.add_text(
                CLIStyle.color(self.description, CLIStyle.COLORS["TITLE"])
            )
        formatter.add_usage(self.usage, self._actions, self._mutually_exclusive_groups)
        for action_group in self._action_groups:
            formatter.start_section(
                CLIStyle.color(action_group.title, CLIStyle.COLORS["TITLE"])
            )
            formatter.add_arguments(action_group._group_actions)
            formatter.end_section()
        if self.epilog:
            formatter.add_text(self.epilog)
        return formatter.format_help()

    def error(self, message: str) -> None:
        """Display parser errors through the shared terminal style."""
        self.print_usage(sys.stderr)
        self.exit(2, CLIStyle.color(f"Error: {message}\n", CLIStyle.COLORS["ERROR"]))


def create_example_text(
    script_name: str, examples: list[tuple[str, str]], notes: list[str] | None = None
) -> str:
    """Create a styled examples and notes block for CLI help."""
    text = f"\n{CLIStyle.color('Examples:', CLIStyle.COLORS['SUB_TITLE'])}"
    for description, command in examples:
        text += f"\n  {CLIStyle.color(f'# {description}', CLIStyle.COLORS['EXAMPLE'])}"
        text += f"\n  {CLIStyle.color(f'{script_name} {command}'.rstrip(), CLIStyle.COLORS['CONTENT'])}\n"
    if notes:
        text += f"\n{CLIStyle.color('Notes:', CLIStyle.COLORS['SUB_TITLE'])}"
        for note in notes:
            text += f"\n  {CLIStyle.color(f'- {note}', CLIStyle.COLORS['CONTENT'])}"
    return text


def positive_timeout(value: str) -> float:
    """Accept a finite positive subprocess timeout."""
    try:
        timeout = float(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("Expected a number of seconds.") from error
    if not 0 < timeout < float("inf"):
        raise argparse.ArgumentTypeError(
            "Timeout must be finite and greater than zero."
        )
    return timeout


def validate_domain(value: str) -> str:
    """Accept a DNS query name without option-like or shell syntax."""
    if len(value) > 253 or not re.fullmatch(r"[A-Za-z0-9_][A-Za-z0-9_.-]*", value):
        raise argparse.ArgumentTypeError(
            "Expected a hostname; use punycode for international names."
        )
    return value


def parse_nameservers(resolver_text: str) -> list[str]:
    """Extract unique numeric nameserver addresses, including scoped IPv6."""
    nameservers = []
    for line in resolver_text.splitlines():
        fields = line.split()
        if len(fields) < 2 or fields[0] != "nameserver":
            continue
        try:
            ipaddress.ip_address(fields[1])
        except ValueError:
            continue
        if fields[1] not in nameservers:
            nameservers.append(fields[1])
    return nameservers


def filter_runtime_dns(output: str) -> str:
    """Retain NetworkManager interface headings only when they have DNS data."""
    blocks = re.split(r"(?=^GENERAL\.DEVICE:)", output, flags=re.MULTILINE)
    lines = []
    for block in blocks:
        if not re.search(r"^IP[46]\.(DNS|DOMAIN)", block, flags=re.MULTILINE):
            continue
        lines.extend(
            line
            for line in block.splitlines()
            if re.match(r"^(GENERAL\.(DEVICE|CONNECTION):|IP[46]\.(DNS|DOMAIN))", line)
        )
    return "\n".join(lines)


@dataclass
class NetworkDns:
    """DNS currently reported for one NetworkManager interface."""

    device: str
    connection: str = ""
    uuid: str = ""
    ipv4: list[str] = field(default_factory=list)
    ipv6: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class QueryResult:
    """Separate a successful answer from failures and incomplete tests."""

    state: str
    addresses: tuple[str, ...] = ()
    detail: str = ""


@dataclass(frozen=True)
class RouteResult:
    """Record route availability without assuming server reachability."""

    state: str
    device: str = ""
    detail: str = ""
    is_tun: bool = False


def parse_fields(output: str) -> dict[str, str]:
    """Parse multiline key/value output while preserving colons in IPv6."""
    fields = {}
    for line in output.splitlines():
        key, separator, value = line.partition(":")
        if separator:
            fields[key.strip()] = value.strip()
    return fields


def parse_runtime_devices(output: str) -> list[NetworkDns]:
    """Capture per-interface runtime DNS with UUIDs for profile comparison."""
    devices = []
    for block in re.split(r"(?=^GENERAL\.DEVICE:)", output, flags=re.MULTILINE):
        fields = parse_fields(block)
        if "GENERAL.DEVICE" not in fields:
            continue
        device = NetworkDns(
            fields["GENERAL.DEVICE"],
            fields.get("GENERAL.CONNECTION", ""),
            fields.get("GENERAL.CON-UUID", ""),
        )
        device.ipv4 = [
            value for key, value in fields.items() if key.startswith("IP4.DNS")
        ]
        device.ipv6 = [
            value for key, value in fields.items() if key.startswith("IP6.DNS")
        ]
        devices.append(device)
    return devices


def parse_dns_answers(result: subprocess.CompletedProcess[str] | None) -> QueryResult:
    """Require positive A answers rather than treating dig exit zero as success."""
    if result is None:
        return QueryResult("unknown", detail="command unavailable or timed out")
    if result.returncode:
        return QueryResult(
            "failed",
            detail="no answer; command exited with status " + str(result.returncode),
        )
    match = re.search(r"status:\s*(\w+)", result.stdout)
    if not match:
        return QueryResult("unknown", detail="DNS response status was not reported")
    if match[1] != "NOERROR":
        return QueryResult("failed", detail=match[1])
    addresses = []
    for line in result.stdout.splitlines():
        fields = line.split()
        if len(fields) >= 5 and fields[-2] == "A":
            addresses.extend(parse_nameservers("nameserver " + fields[-1]))
    if not addresses:
        return QueryResult("no_answer", detail="NOERROR, but no A records")
    return QueryResult("success", tuple(dict.fromkeys(addresses)), "NOERROR")


class DnsChecker:
    """Collect DNS evidence without changing resolver or network configuration."""

    def __init__(
        self, timeout: float, use_sudo: bool = False, verbose: bool = False
    ) -> None:
        """Store command limits and optional noninteractive elevation."""
        self.timeout = timeout
        self.use_sudo = use_sudo
        self.os_name = platform.system()
        self.verbose = verbose
        self.resolver_target = ""
        self.service_states: dict[str, str] = {}
        self.runtime_devices: list[NetworkDns] = []
        self.saved_profiles: list[dict[str, str]] = []
        self.record_sources: dict[str, list[str]] = {}
        self.fixed_sources: dict[str, list[str]] = {}
        self.routes: dict[str, RouteResult] = {}
        self.system_query: QueryResult | None = None
        self.default_query: QueryResult | None = None
        self.server_queries: dict[str, QueryResult] = {}
        self.inspection_warnings: list[str] = []

    @staticmethod
    def title(text: str) -> None:
        """Print a report section heading."""
        CLIStyle.emit(f"\n{text}", "TITLE")

    def warn(self, text: str) -> None:
        """Print a recoverable diagnostic failure."""
        CLIStyle.emit(f"Warning: {text}", "WARNING", sys.stderr)
        self.inspection_warnings.append(text)

    @staticmethod
    def find_command(name: str) -> str | None:
        """Find a tool, including common administrative command directories."""
        command_path = shutil.which(name)
        if command_path:
            return command_path
        for directory in ("/usr/sbin", "/sbin"):
            candidate = Path(directory) / name
            if candidate.is_file() and os.access(candidate, os.X_OK):
                return str(candidate)
        return None

    def run_command(
        self,
        arguments: list[str],
        show: bool = False,
        privileged: bool = True,
        report_errors: bool = True,
    ) -> subprocess.CompletedProcess[str] | None:
        """Run a bounded command without a shell and report recoverable failures."""
        executable = self.find_command(arguments[0])
        if executable is None:
            if report_errors:
                self.warn(f"Command is unavailable: {arguments[0]}")
            return None
        command = [executable, *arguments[1:]]
        if self.use_sudo and privileged:
            command = ["sudo", "-n", *command]
        environment = dict(os.environ, LC_ALL="C", LANG="C")
        if DEBUG_MODE:
            CLIStyle.emit(f"Command: {shlex.join(command)}", "EXAMPLE", sys.stderr)
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=self.timeout,
                env=environment,
                check=False,
            )
        except subprocess.TimeoutExpired:
            if report_errors:
                self.warn(
                    f"Timed out after {self.timeout:g}s: {shlex.join(arguments)}; retry with --timeout 30."
                )
            return None
        except OSError as error:
            if report_errors:
                self.warn(f"Cannot execute {arguments[0]}: {error}")
            return None
        if (show or self.verbose) and result.stdout.strip():
            CLIStyle.emit(result.stdout.rstrip())
        if (self.verbose or report_errors) and result.stderr.strip():
            CLIStyle.emit(result.stderr.rstrip(), "WARNING", sys.stderr)
        if result.returncode and report_errors:
            self.warn(
                f"Command exited with status {result.returncode}: {shlex.join(arguments)}"
            )
        return result

    def read_file(self, file_path: Path, show: bool = False) -> str | None:
        """Read an available DNS source, optionally using sudo after a denial."""
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except FileNotFoundError:
            return None
        except PermissionError as error:
            if not self.use_sudo:
                self.warn(f"Cannot read {file_path}: {error}")
                return None
            result = self.run_command(["cat", str(file_path)], show=False)
            if result is None or result.returncode:
                return None
            content = result.stdout
        except OSError as error:
            self.warn(f"Cannot read {file_path}: {error}")
            return None
        if show or self.verbose:
            CLIStyle.emit(f"\n--- {file_path} ---", "EXAMPLE")
            CLIStyle.emit(content.rstrip())
        return content

    def report_resolver(self) -> list[str]:
        """Show resolver indirection and NSS lookup order and return its servers."""
        self.title("Resolver file and lookup order")
        resolver_path = Path("/etc/resolv.conf")
        try:
            if resolver_path.is_symlink():
                CLIStyle.emit(f"{resolver_path} -> {resolver_path.readlink()}")
            self.resolver_target = str(resolver_path.resolve(strict=True))
            CLIStyle.emit(f"Resolved target: {self.resolver_target}")
        except (OSError, RuntimeError) as error:
            self.warn(f"Resolver path is missing, broken, or inaccessible: {error}")
        content = self.read_file(resolver_path)
        nsswitch_text = self.read_file(Path("/etc/nsswitch.conf"), show=False)
        if nsswitch_text:
            lines = [
                line
                for line in nsswitch_text.splitlines()
                if re.match(r"\s*hosts\s*:", line)
            ]
            CLIStyle.emit("\n".join(lines))
        nameservers = parse_nameservers(content or "")
        CLIStyle.emit("Listed DNS (in order): " + (", ".join(nameservers) or "none"))
        return nameservers

    def report_managers(self) -> None:
        """Show applicable manager states and OS-specific runtime DNS."""
        if self.os_name == "Darwin":
            self.title("macOS effective resolver configuration")
            self.run_command(["scutil", "--dns"], show=True)
            CLIStyle.emit(
                "macOS uses scoped resolvers; resolv.conf is not the full configuration."
            )
            return
        if self.os_name != "Linux":
            return
        if self.find_command("systemctl") and Path("/run/systemd/system").is_dir():
            self.title("Manager service states")
            result = self.run_command(
                [
                    "systemctl",
                    "--no-pager",
                    "show",
                    "-p",
                    "Id",
                    "-p",
                    "ActiveState",
                    "-p",
                    "SubState",
                    "NetworkManager.service",
                    "systemd-resolved.service",
                    "systemd-networkd.service",
                    "resolvconf.service",
                    "dhcpcd.service",
                ]
            )
            if result is not None and result.returncode == 0:
                for block in result.stdout.split("\n\n"):
                    fields = dict(
                        line.split("=", 1) for line in block.splitlines() if "=" in line
                    )
                    if "Id" in fields:
                        self.service_states[fields["Id"]] = fields.get(
                            "ActiveState", "unknown"
                        )
                if not self.verbose:
                    active = [
                        name.removesuffix(".service")
                        for name, state in self.service_states.items()
                        if state == "active"
                    ]
                    other = [
                        f"{name.removesuffix('.service')}={state}"
                        for name, state in self.service_states.items()
                        if state != "active"
                    ]
                    CLIStyle.emit("Active: " + (", ".join(active) or "none"))
                    CLIStyle.emit("Other: " + ", ".join(other))
        resolved_active = (
            self.service_states.get("systemd-resolved.service") != "inactive"
        )
        if resolved_active and self.find_command("resolvectl"):
            self.title("systemd-resolved runtime DNS")
            self.run_command(["resolvectl", "status"], show=True)
        elif resolved_active and self.find_command("systemd-resolve"):
            self.title("systemd-resolved runtime DNS (legacy)")
            self.run_command(["systemd-resolve", "--status"], show=True)
        if self.find_command("nmcli"):
            self.report_networkmanager()

    def report_networkmanager(self) -> None:
        """Separate applied interface DNS from saved active-connection settings."""
        self.title("NetworkManager runtime DNS")
        result = self.run_command(
            [
                "nmcli",
                "-f",
                "GENERAL.DEVICE,GENERAL.CONNECTION,GENERAL.CON-UUID,IP4.DNS,IP4.DOMAIN,IP6.DNS,IP6.DOMAIN",
                "device",
                "show",
            ],
            show=False,
        )
        if result is not None and result.returncode == 0:
            self.runtime_devices = parse_runtime_devices(result.stdout)
            for device in self.runtime_devices:
                if device.ipv4 or device.ipv6:
                    CLIStyle.emit(
                        f"{device.device} ({device.connection}): IPv4={', '.join(device.ipv4) or 'none'}; IPv6={', '.join(device.ipv6) or 'none'}"
                    )
        self.title("NetworkManager saved settings for active connections")
        profiles = self.run_command(
            [
                "nmcli",
                "-t",
                "-f",
                "UUID,TYPE",
                "connection",
                "show",
                "--active",
            ],
            show=False,
        )
        if profiles is None or profiles.returncode:
            return
        fields = (
            "connection.id,ipv4.method,ipv4.dns,ipv4.ignore-auto-dns,ipv4.dns-priority,"
            "ipv6.method,ipv6.dns,ipv6.ignore-auto-dns,ipv6.dns-priority"
        )
        for line in profiles.stdout.splitlines():
            profile_id, separator, connection_type = line.partition(":")
            if not separator or connection_type in {"bridge", "loopback", "tun"}:
                continue
            result = self.run_command(
                ["nmcli", "-f", fields, "connection", "show", profile_id]
            )
            if result is None or result.returncode:
                continue
            settings = parse_fields(result.stdout)
            settings["uuid"] = profile_id
            self.saved_profiles.append(settings)
            if not self.verbose:
                CLIStyle.emit(
                    f"{settings.get('connection.id', profile_id)}: saved IPv4={settings.get('ipv4.dns', '--')}; IPv6={settings.get('ipv6.dns', '--')}; ignore-auto-dns(v4/v6)={settings.get('ipv4.ignore-auto-dns', '?')}/{settings.get('ipv6.ignore-auto-dns', '?')}"
                )

    def report_resolvconf(self) -> None:
        """Read submitted records directly before falling back to resolvconf -l."""
        for directory in (
            Path("/run/resolvconf/interface"),
            Path("/run/resolvconf/interfaces"),
        ):
            if not directory.is_dir():
                continue
            if self.verbose:
                self.title("resolvconf submitted records")
            try:
                records = sorted(directory.iterdir())
            except OSError as error:
                self.warn(f"Cannot list {directory}: {error}")
                continue
            for record in records:
                if record.is_file():
                    content = self.read_file(record)
                    if content is not None:
                        self.record_sources[record.name] = parse_nameservers(content)
            return
        if self.find_command("resolvconf"):
            self.title("resolvconf submitted records")
            self.run_command(["resolvconf", "-l"], show=True)

    def report_sources(self) -> None:
        """Display available generated files and fixed resolver inputs."""
        self.title(
            "Available generated and fixed DNS sources"
            if self.verbose
            else "DNS sources"
        )
        paths = (
            "/run/NetworkManager/resolv.conf",
            "/run/systemd/resolve/resolv.conf",
            "/run/systemd/resolve/stub-resolv.conf",
            "/run/resolvconf/resolv.conf",
            "/etc/resolvconf/resolv.conf.d/head",
            "/etc/resolvconf/resolv.conf.d/base",
            "/etc/resolvconf/resolv.conf.d/tail",
            "/etc/resolvconf.conf",
        )
        for file_path in paths:
            content = self.read_file(Path(file_path))
            if content is None or file_path.startswith("/run/"):
                continue
            nameservers = parse_nameservers(content)
            self.fixed_sources[file_path] = nameservers
            if nameservers and not self.verbose:
                CLIStyle.emit(f"{file_path}: {', '.join(nameservers)}")
        if self.record_sources and not self.verbose:
            CLIStyle.emit(
                "resolvconf input providers: " + ", ".join(self.record_sources)
            )

    def report_routes(self, nameservers: list[str]) -> None:
        """Inspect UDP DNS routes as the calling user, including policy routing."""
        if self.os_name != "Linux" or not self.find_command("ip"):
            return
        self.title("Routes to configured DNS servers (UDP port 53)")
        if not nameservers:
            CLIStyle.emit("No numeric nameservers were found in /etc/resolv.conf.")
        for nameserver in nameservers:
            if self.verbose:
                CLIStyle.emit(f"\n--- {nameserver} ---", "EXAMPLE")
            family = "-6" if ":" in nameserver else "-4"
            result = self.run_command(
                [
                    "ip",
                    family,
                    "route",
                    "get",
                    nameserver,
                    "ipproto",
                    "udp",
                    "dport",
                    "53",
                ],
                privileged=False,
                report_errors=False,
            )
            if result is None:
                route = RouteResult(
                    "unknown", detail="command unavailable or timed out"
                )
            elif result.returncode == 0:
                match = re.search(r"\bdev\s+(\S+)", result.stdout)
                device = match[1] if match else ""
                route = RouteResult(
                    "routed",
                    device,
                    result.stdout.strip(),
                    bool(device)
                    and (Path("/sys/class/net") / device / "tun_flags").exists(),
                )
            elif re.search(
                r"network is unreachable|no route to host|unreachable",
                result.stderr,
                re.IGNORECASE,
            ):
                route = RouteResult("unreachable", detail="no route")
            else:
                route = RouteResult(
                    "unknown",
                    detail=result.stderr.strip() or f"exit {result.returncode}",
                )
            self.routes[nameserver] = route
            if not self.verbose:
                detail = (
                    route.detail
                    if route.state != "routed"
                    else f"via {route.device or 'unknown interface'}"
                    + (" (TUN)" if route.is_tun else "")
                )
                CLIStyle.emit(
                    f"{nameserver}: {detail}",
                    "WARNING" if route.state != "routed" else "CONTENT",
                )

    def report_queries(self, domain: str, nameservers: list[str]) -> None:
        """Test the system resolver and explicit servers without elevating queries."""
        self.title(f"Resolution test: {domain}")
        result = None
        if self.find_command("getent"):
            result = self.run_command(
                ["getent", "ahosts", domain], privileged=False, report_errors=False
            )
        elif self.os_name == "Darwin" and self.find_command("dscacheutil"):
            result = self.run_command(
                ["dscacheutil", "-q", "host", "-a", "name", domain],
                privileged=False,
                report_errors=False,
            )
        else:
            CLIStyle.emit("System resolver: test tool unavailable", "WARNING")
        addresses = []
        if result is not None and result.returncode == 0:
            for line in result.stdout.splitlines():
                token = (
                    line.partition(":")[2].strip()
                    if line.startswith("ip_address:")
                    else (line.split() or [""])[0]
                )
                addresses.extend(parse_nameservers("nameserver " + token))
        if addresses:
            self.system_query = QueryResult("success", tuple(dict.fromkeys(addresses)))
        elif result is not None and result.returncode:
            self.system_query = QueryResult(
                "failed", detail=f"exit {result.returncode}"
            )
        else:
            self.system_query = QueryResult(
                "unknown", detail="no addresses reported or test unavailable"
            )
        self.show_query("System resolver", self.system_query)
        if not self.find_command("dig"):
            self.warn("dig is unavailable; direct DNS tests were skipped.")
            return
        self.default_query = self.query_dig(domain)
        self.show_query("Resolver-file query", self.default_query)
        for nameserver in nameservers:
            if self.verbose:
                CLIStyle.emit(
                    f"\n--- Query via {nameserver} (may be intercepted by VPN/TUN) ---",
                    "EXAMPLE",
                )
            query = self.query_dig(domain, nameserver)
            self.server_queries[nameserver] = query
            self.show_query(f"Via {nameserver}", query)

    def query_dig(self, domain: str, nameserver: str | None = None) -> QueryResult:
        """Run one bounded A query and flag unsuccessful DNS response codes."""
        arguments = ["dig"]
        if nameserver:
            arguments.append(f"@{nameserver}")
        arguments.extend(
            [domain, "A", "+time=2", "+tries=1", "+noall", "+answer", "+comments"]
        )
        result = self.run_command(arguments, privileged=False, report_errors=False)
        return parse_dns_answers(result)

    @staticmethod
    def show_query(label: str, query: QueryResult) -> None:
        """Display one query result without raw protocol output."""
        detail = (
            ", ".join(query.addresses) if query.state == "success" else query.detail
        )
        CLIStyle.emit(
            f"{label}: {query.state.upper()} ({detail})",
            "CONTENT" if query.state == "success" else "WARNING",
        )

    def saved_dns_differences(self) -> list[str]:
        """Find saved DNS missing from the matching connection's runtime data."""
        differences = []
        for profile in self.saved_profiles:
            matches = [
                device
                for device in self.runtime_devices
                if device.uuid == profile.get("uuid")
            ]
            if len(matches) != 1:
                continue
            for family in ("ipv4", "ipv6"):
                values = re.split(r"[\s,]+", profile.get(f"{family}.dns", ""))
                saved = parse_nameservers(
                    "\n".join("nameserver " + value for value in values)
                )
                runtime = getattr(matches[0], family)
                missing = [address for address in saved if address not in runtime]
                if missing:
                    differences.append(
                        f"Connection '{profile.get('connection.id', profile['uuid'])}': saved {family.replace('ipv', 'IPv')} DNS {', '.join(missing)} is absent from reported runtime DNS."
                    )
        return differences

    def report_findings(self, nameservers: list[str], domain: str | None) -> None:
        """Summarize observed facts while keeping missing evidence explicit."""
        self.title("Findings")
        if self.resolver_target.startswith("/run/resolvconf/"):
            CLIStyle.emit("resolvconf generates the resolver file.")
            if "NetworkManager" in self.record_sources:
                CLIStyle.emit(
                    "NetworkManager supplies dynamic DNS; fixed head/base/tail inputs can supplement it."
                )
        elif self.resolver_target.startswith("/run/systemd/resolve/"):
            CLIStyle.emit(
                "systemd-resolved provides the resolver file; review its global and per-link DNS settings."
            )
        if domain and self.system_query:
            self.show_query(f"System resolution for {domain}", self.system_query)
        else:
            CLIStyle.emit("Resolution: NOT TESTED (use --test DOMAIN).")
        if self.os_name == "Linux" and nameservers and not self.routes:
            CLIStyle.emit(
                "DNS routes: NOT CHECKED (route inspection tool unavailable).",
                "WARNING",
            )
        if (
            nameservers
            and self.routes.get(nameservers[0], RouteResult("unknown")).state
            == "unreachable"
        ):
            CLIStyle.emit(
                f"First listed DNS {nameservers[0]} has no route; the resolver may fall back to later entries.",
                "WARNING",
            )
        for server, route in self.routes.items():
            if route.is_tun:
                CLIStyle.emit(
                    f"DNS for {server} is routed through TUN '{route.device}'; query success does not verify the final upstream."
                )
            elif route.state == "unknown":
                CLIStyle.emit(
                    f"Route for {server}: UNKNOWN ({route.detail}).", "WARNING"
                )
            elif route.state == "unreachable" and server != nameservers[0]:
                CLIStyle.emit(f"Listed DNS {server} has no route.", "WARNING")
        differences = self.saved_dns_differences()
        for difference in differences:
            CLIStyle.emit(difference, "WARNING")
        if differences:
            CLIStyle.emit(
                "Review NetworkManager's saved and active connection settings; the cause of the difference is not established."
            )
        if self.inspection_warnings:
            CLIStyle.emit(
                "Some inspection checks were unavailable; conclusions are limited to the collected evidence.",
                "WARNING",
            )
        CLIStyle.emit(
            "Edit source configuration, not generated resolv.conf. Use --verbose for full evidence."
        )

    def report(self, domain: str | None = None) -> None:
        """Collect the report and send queries only when explicitly requested."""
        self.title(f"DNS report ({self.os_name})")
        CLIStyle.emit(
            "Scope: this process/network namespace; applications may use their own DNS."
        )
        nameservers = self.report_resolver()
        self.report_managers()
        self.report_resolvconf()
        self.report_sources()
        self.report_routes(nameservers)
        if domain:
            self.report_queries(domain, nameservers)
        self.report_findings(nameservers, domain)


def create_parser() -> ColoredArgumentParser:
    """Create the styled CLI with read-only defaults and explicit query tests."""
    script_name = f"python3 {Path(sys.argv[0]).name}"
    parser = ColoredArgumentParser(
        description="Inspect DNS managers, configuration sources, resolver routes, and optional queries.",
        formatter_class=ColoredHelpFormatter,
        add_help=False,
        epilog=create_example_text(
            script_name,
            [
                ("Inspect local DNS configuration", ""),
                ("Test name resolution", "--test example.com"),
                ("Show complete command and configuration output", "--verbose"),
                (
                    "Inspect with noninteractive sudo and a longer timeout",
                    "--sudo --timeout 30",
                ),
                ("Show diagnostic command details", "--log"),
            ],
            [
                "Python 3.10+; standard library only. External tools are detected as available.",
                "No configuration is changed. No queries are sent without --test.",
                "--sudo uses sudo -n for inspection only and never prompts for a password.",
                "Exit 0 means the report completed; individual failures appear as warnings.",
                "Routes do not prove reachability. VPN/TUN and application DNS can change the upstream.",
            ],
        ),
    )
    parser.add_argument("-h", "--help", action="help", help="Show this help and exit.")
    parser.add_argument(
        "--sudo",
        action="store_true",
        help="Use noninteractive sudo for local inspection.",
    )
    parser.add_argument(
        "--test",
        type=validate_domain,
        metavar="DOMAIN",
        help="Test the system resolver and each configured server.",
    )
    parser.add_argument(
        "--timeout",
        type=positive_timeout,
        default=10.0,
        metavar="SECONDS",
        help="Maximum time per external command (default: 10 seconds).",
    )
    parser.add_argument(
        "--log",
        action="store_true",
        help="Print commands and unexpected-error tracebacks.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Show full command output and DNS configuration files.",
    )
    return parser


def main() -> int:
    """Run the CLI and distinguish fatal failures from report warnings."""
    global DEBUG_MODE
    parser = create_parser()
    arguments = parser.parse_args()
    DEBUG_MODE = arguments.log
    if arguments.sudo and not DnsChecker.find_command("sudo"):
        parser.error("sudo is unavailable.")
    try:
        DnsChecker(arguments.timeout, arguments.sudo, arguments.verbose).report(
            arguments.test
        )
        return 0
    except FileNotFoundError as error:
        CLIStyle.emit(f"Error: File not found: {error}", "ERROR", sys.stderr)
        return 1
    except KeyboardInterrupt:
        CLIStyle.emit("Interrupted.", "WARNING", sys.stderr)
        return 130
    except BrokenPipeError:
        return 0
    except Exception as error:
        if DEBUG_MODE:
            traceback.print_exc()
        CLIStyle.emit(f"Error: {error}", "ERROR", sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
