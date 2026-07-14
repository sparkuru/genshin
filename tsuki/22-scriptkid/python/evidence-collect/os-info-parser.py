#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# Requires the sshpass command.

import argparse
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEBUG_MODE = False
DEFAULT_PORT = 22
DEFAULT_OUTPUT_PREFIX = "info"


class CLIStyle:
    """CLI tool unified style config."""

    COLORS = {
        "TITLE": 7,
        "SUB_TITLE": 2,
        "CONTENT": 3,
        "EXAMPLE": 7,
        "WARNING": 4,
        "ERROR": 2,
        "OK": 3,
        "INFO": 5,
    }

    @staticmethod
    def color(text: str = "", color: int = COLORS["CONTENT"]) -> str:
        """Unified color processing function."""
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

    @staticmethod
    def write(
        text: str = "",
        color: int = COLORS["CONTENT"],
        error: bool = False,
        end: str = "\n",
    ) -> None:
        """Write styled output to the selected stream."""
        stream = sys.stderr if error else sys.stdout
        stream.write(f"{CLIStyle.color(text, color)}{end}")
        stream.flush()


class ColoredArgumentParser(argparse.ArgumentParser):
    """Argument parser with colored help output."""

    def _format_action_invocation(self, action: argparse.Action) -> str:
        """Format option names with semantic terminal colors."""
        if not action.option_strings:
            (metavar,) = self._metavar_formatter(action, action.dest)(1)
            return metavar

        parts: list[str] = []
        if action.nargs == 0:
            parts.extend(
                CLIStyle.color(option, CLIStyle.COLORS["SUB_TITLE"])
                for option in action.option_strings
            )
            return ", ".join(parts)

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
        """Return colored help text."""
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


@dataclass(frozen=True)
class ConnectionConfig:
    """SSH connection configuration."""

    ip: str
    user: str
    password: str
    port: int


@dataclass(frozen=True)
class CommandSpec:
    """One displayed command and its real shell command."""

    display: str
    command: str
    sudo: bool


@dataclass(frozen=True)
class CollectJob:
    """One output file and its command list."""

    filename: str
    commands: list[CommandSpec]


def debug(
    *args: Any, file: str | None = None, append: bool = True, **kwargs: Any
) -> None:
    """
    Print debug details with caller location.
    ```python
    debug("message", key="value")

    return = None
    ```
    """
    if not DEBUG_MODE:
        return

    output = " ".join(str(arg) for arg in args)
    if kwargs:
        output += " " + " ".join(f"{key}={value}" for key, value in kwargs.items())
    output += "\n"

    if file is not None:
        file_mode = "a" if append else "w"
        with open(file, file_mode, encoding="utf-8") as file_handle:
            file_handle.write(output)
        return

    CLIStyle.write(output.rstrip(), CLIStyle.COLORS["WARNING"])


def create_example_text(
    script_name: str,
    examples: list[tuple[str, str]],
    notes: list[str] | None = None,
) -> str:
    """Create colored example help text."""
    text = f"\n{CLIStyle.color('Examples:', CLIStyle.COLORS['SUB_TITLE'])}"
    for desc, cmd in examples:
        text += f"\n  {CLIStyle.color(f'# {desc}', CLIStyle.COLORS['EXAMPLE'])}"
        text += f"\n  {CLIStyle.color(f'{script_name} {cmd}', CLIStyle.COLORS['CONTENT'])}\n"

    if notes:
        text += f"\n{CLIStyle.color('Notes:', CLIStyle.COLORS['SUB_TITLE'])}"
        for note in notes:
            text += f"\n  {CLIStyle.color(f'- {note}', CLIStyle.COLORS['CONTENT'])}"
    return text


def make_command(
    display: str,
    command: str | None = None,
    sudo: bool = True,
) -> CommandSpec:
    """Create a command specification."""
    return CommandSpec(display=display, command=command or display, sudo=sudo)


def default_collect_jobs() -> list[CollectJob]:
    """Return default Linux information collection jobs."""
    return [
        CollectJob(
            "base.txt",
            [
                make_command("date -Is"),
                make_command("hostname"),
                make_command("hostnamectl"),
                make_command("cat /etc/os-release"),
                make_command("id", sudo=False),
                make_command("whoami", sudo=False),
                make_command("uname -a"),
                make_command("cat /proc/cmdline"),
                make_command("uptime"),
                make_command("lscpu"),
                make_command("free -h"),
                make_command("ls -alh /"),
                make_command("cat /etc/passwd"),
                make_command("cat /etc/group"),
                make_command("printenv", sudo=False),
            ],
        ),
        CollectJob(
            "hardware.txt",
            [
                make_command("lsusb"),
                make_command("command -v lspci >/dev/null && lspci -nn || true"),
                make_command("command -v nvidia-smi >/dev/null && nvidia-smi || true"),
                make_command(
                    "cat /etc/nv_tegra_release",
                    "cat /etc/nv_tegra_release 2>/dev/null || true",
                ),
                make_command("command -v sensors >/dev/null && sensors || true"),
            ],
        ),
        CollectJob(
            "process.txt",
            [
                make_command("ps auxww"),
                make_command("top -b -n 1"),
                make_command("command -v pstree >/dev/null && pstree -alp || true"),
            ],
        ),
        CollectJob(
            "network.txt",
            [
                make_command("ip -br addr"),
                make_command("ip route"),
                make_command("ip neigh"),
                make_command("ss -plantu"),
                make_command("cat /etc/resolv.conf"),
                make_command("cat /etc/hosts"),
                make_command("iptables -S"),
                make_command("nft list ruleset"),
            ],
        ),
        CollectJob(
            "storage.txt",
            [
                make_command("df -hT"),
                make_command("lsblk -f"),
                make_command("mount"),
                make_command("cat /proc/mounts"),
                make_command("du -sh /home /var /tmp 2>/dev/null"),
            ],
        ),
        CollectJob(
            "service.txt",
            [
                make_command("systemctl --no-pager --type=service --state=running"),
                make_command("systemctl --no-pager --failed"),
                make_command("crontab -l"),
                make_command("ls -alh /etc/systemd/system"),
                make_command("ls -alh /etc/init.d"),
            ],
        ),
        CollectJob(
            "package.txt",
            [
                make_command("command -v dpkg >/dev/null && dpkg -l || true"),
                make_command("command -v rpm >/dev/null && rpm -qa || true"),
                make_command("command -v snap >/dev/null && snap list || true"),
                make_command("command -v pip3 >/dev/null && pip3 list || true"),
            ],
        ),
        CollectJob(
            "container.txt",
            [
                make_command("command -v docker >/dev/null && docker ps -a || true"),
                make_command("command -v docker >/dev/null && docker images || true"),
                make_command("command -v crictl >/dev/null && crictl ps -a || true"),
                make_command("command -v podman >/dev/null && podman ps -a || true"),
            ],
        ),
        CollectJob(
            "log.txt",
            [
                make_command("dmesg -T | tail -n 300"),
                make_command("journalctl -p 3 -xb -n 200 --no-pager"),
            ],
        ),
        CollectJob(
            "history.txt",
            [
                make_command(
                    "format current user history files",
                    'for file in "$HOME"/.bash_history "$HOME"/.zsh_history '
                    '"$HOME"/.ash_history "$HOME"/.sh_history; do '
                    '[ -f "$file" ] || continue; '
                    "printf '\\n==> %s <==\\n' \"$file\"; "
                    "awk '"
                    "function fmt_epoch(epoch) { "
                    'return epoch == "" ? "-" : strftime("%Y-%m-%d %H:%M:%S", epoch) '
                    "} "
                    'BEGIN { line_no = 0; pending_time = "-" } '
                    "/^#[0-9]+$/ { pending_time = fmt_epoch(substr($0, 2)); next } "
                    "/^: [0-9]+:[0-9]+;/ { "
                    "line = $0; "
                    'sub(/^: /, "", line); '
                    "meta = line; "
                    'sub(/;.*/, "", meta); '
                    "command = line; "
                    'sub(/^[^;]*;/, "", command); '
                    'split(meta, fields, ":"); '
                    "line_no++; "
                    'printf "%6d  %s  %s\\n", line_no, fmt_epoch(fields[1]), command; '
                    "next "
                    "} "
                    "{ "
                    "line_no++; "
                    'printf "%6d  %s  %s\\n", line_no, pending_time, $0; '
                    'pending_time = "-" '
                    '}\' "$file"; '
                    "done",
                    sudo=False,
                ),
                make_command(
                    "format current user history files",
                    'for file in "$HOME"/.bash_history "$HOME"/.zsh_history '
                    '"$HOME"/.ash_history "$HOME"/.sh_history; do '
                    '[ -f "$file" ] || continue; '
                    "printf '\\n==> %s <==\\n' \"$file\"; "
                    "awk '"
                    "function fmt_epoch(epoch) { "
                    'return epoch == "" ? "-" : strftime("%Y-%m-%d %H:%M:%S", epoch) '
                    "} "
                    'BEGIN { line_no = 0; pending_time = "-" } '
                    "/^#[0-9]+$/ { pending_time = fmt_epoch(substr($0, 2)); next } "
                    "/^: [0-9]+:[0-9]+;/ { "
                    "line = $0; "
                    'sub(/^: /, "", line); '
                    "meta = line; "
                    'sub(/;.*/, "", meta); '
                    "command = line; "
                    'sub(/^[^;]*;/, "", command); '
                    'split(meta, fields, ":"); '
                    "line_no++; "
                    'printf "%6d  %s  %s\\n", line_no, fmt_epoch(fields[1]), command; '
                    "next "
                    "} "
                    "{ "
                    "line_no++; "
                    'printf "%6d  %s  %s\\n", line_no, pending_time, $0; '
                    'pending_time = "-" '
                    '}\' "$file"; '
                    "done",
                ),
            ],
        ),
    ]


def command_with_prompt(
    command_spec: CommandSpec, leading_newline: bool = False
) -> str:
    """Build one shell command section with a CLI-style prompt."""
    prompt = "\\n$" if leading_newline else "$"
    display_text = (
        f"sudo {command_spec.display}" if command_spec.sudo else command_spec.display
    )
    display = shlex.quote(display_text)
    command = command_spec.command
    if command_spec.sudo:
        command = (
            "printf '%s\\n' \"$OS_INFO_SUDO_PASSWORD\" "
            f"| sudo -S -p '' \"$OS_INFO_REMOTE_SHELL\" -c {shlex.quote(command)}"
        )
    return f"printf '{prompt} %s\\n' {display}; {command}"


def command_group(commands: list[CommandSpec]) -> str:
    """Build a shell script that prints prompts before command output."""
    script = "; ".join(
        command_with_prompt(command_spec, index > 0)
        for index, command_spec in enumerate(commands)
    )
    return f"{script}; true"


def read_json_file(path: Path) -> dict[str, Any]:
    """Read a JSON object from disk."""
    with open(path, "r", encoding="utf-8") as file_handle:
        data = json.load(file_handle)

    if not isinstance(data, dict):
        raise ValueError(f"JSON file must contain an object: {path}")
    return data


def parse_config_file(path: Path) -> dict[str, Any]:
    """Read the target JSON config file."""
    return read_json_file(path)


def parse_config_command(value: Any) -> CommandSpec:
    """Parse one command item from JSON."""
    if isinstance(value, str):
        return make_command(value)

    if not isinstance(value, dict):
        raise ValueError("Command item must be a string or object")

    display = value.get("display")
    command = value.get("command", value.get("run"))
    if not isinstance(display, str) and not isinstance(command, str):
        raise ValueError("Command object needs display or command")

    if not isinstance(display, str):
        display = command
    if not isinstance(command, str):
        command = display

    sudo = value.get("sudo", True)
    as_user = value.get("as_user", False)
    if not isinstance(sudo, bool):
        raise ValueError("Command sudo field must be a boolean")
    if not isinstance(as_user, bool):
        raise ValueError("Command as_user field must be a boolean")
    return make_command(display, command, sudo=sudo and not as_user)


def parse_config_jobs(data: dict[str, Any]) -> list[CollectJob]:
    """Read additional collection jobs from target config data."""
    files = data.get("files", {})
    if not isinstance(files, dict):
        raise ValueError("Config files must be an object")

    jobs: list[CollectJob] = []
    for filename, value in files.items():
        if not isinstance(filename, str):
            raise ValueError("Output filename must be a string")

        if isinstance(value, dict) and "commands" in value:
            commands_value = value["commands"]
        else:
            commands_value = value
        if isinstance(commands_value, (str, dict)):
            commands_value = [commands_value]
        if not isinstance(commands_value, list):
            raise ValueError(f"Commands must be a list: {filename}")

        commands = [parse_config_command(command) for command in commands_value]
        jobs.append(CollectJob(normalize_output_filename(filename), commands))
    return jobs


def normalize_output_filename(filename: str) -> str:
    """Validate and normalize one output filename."""
    path = Path(filename)
    if path.is_absolute() or ".." in path.parts:
        raise ValueError(f"Unsafe output filename: {filename}")
    if path.name != filename:
        raise ValueError(f"Output filename must not contain directories: {filename}")
    if not filename:
        raise ValueError("Output filename must not be empty")
    return filename


def merge_jobs(
    base_jobs: list[CollectJob], config_jobs: list[CollectJob]
) -> list[CollectJob]:
    """Merge config jobs into the default job list."""
    merged: dict[str, list[CommandSpec]] = {
        job.filename: list(job.commands) for job in base_jobs
    }
    for job in config_jobs:
        merged.setdefault(job.filename, []).extend(job.commands)
    return [CollectJob(filename, commands) for filename, commands in merged.items()]


def sanitize_output_name(value: str) -> str:
    """Convert a target name to a safe directory suffix."""
    safe_value = re.sub(r"[^A-Za-z0-9._-]+", "_", value)
    return safe_value.strip("._-") or "target"


def resolve_output_dir(ip: str, output_dir: str | None) -> Path:
    """Resolve the output directory path."""
    if output_dir:
        return Path(output_dir).expanduser().resolve()

    dirname = f"{DEFAULT_OUTPUT_PREFIX}-{sanitize_output_name(ip)}"
    return (Path.cwd() / dirname).resolve()


def build_connection_config(
    args: argparse.Namespace,
    config_data: dict[str, Any],
) -> ConnectionConfig:
    """Build SSH connection configuration from CLI and optional config."""
    ip = args.ip or config_data.get("ip")
    user = args.user or config_data.get("user") or config_data.get("username")
    password = args.password or config_data.get("password")
    port = args.port or config_data.get("port") or DEFAULT_PORT

    missing_fields = [
        field
        for field, value in (("ip", ip), ("user", user), ("password", password))
        if not value
    ]
    if missing_fields:
        joined_fields = ", ".join(missing_fields)
        raise ValueError(
            f"Missing connection field(s): {joined_fields}. Try -h or --example."
        )

    return ConnectionConfig(
        ip=str(ip),
        user=str(user),
        password=str(password),
        port=int(port),
    )


def build_ssh_args(config: ConnectionConfig, command_script: str) -> list[str]:
    """Build sshpass and ssh argument list."""
    remote_shell_selector = (
        f"OS_INFO_SSH_USER={shlex.quote(config.user)}; "
        'OS_INFO_REMOTE_SHELL=$(awk -F: -v target_user="$OS_INFO_SSH_USER" '
        "'$1 == target_user && $7 ~ /^\\// && $7 !~ /(false|nologin)$/ "
        "{ print $7; exit }' /etc/passwd); "
        'if [ -z "$OS_INFO_REMOTE_SHELL" ] || [ ! -x "$OS_INFO_REMOTE_SHELL" ]; then '
        "OS_INFO_REMOTE_SHELL=''; "
        "for shell_name in zsh bash sh; do "
        'OS_INFO_REMOTE_SHELL=$(awk -F: -v shell_name="$shell_name" '
        '\'$7 ~ ("/" shell_name "$") && $7 !~ /(false|nologin)$/ '
        "{ print $7; exit }' /etc/passwd); "
        '[ -n "$OS_INFO_REMOTE_SHELL" ] && [ -x "$OS_INFO_REMOTE_SHELL" ] && break; '
        "done; "
        "fi; "
        'if [ -z "$OS_INFO_REMOTE_SHELL" ]; then OS_INFO_REMOTE_SHELL=/bin/sh; fi; '
        'if [ ! -x "$OS_INFO_REMOTE_SHELL" ]; then OS_INFO_REMOTE_SHELL=sh; fi'
    )
    remote_script = (
        f"{remote_shell_selector}; "
        f"OS_INFO_SUDO_PASSWORD={shlex.quote(config.password)}; "
        "export OS_INFO_REMOTE_SHELL OS_INFO_SUDO_PASSWORD; "
        f'"$OS_INFO_REMOTE_SHELL" -c {shlex.quote(command_script)}'
    )
    remote_cmd = f"{remote_script} 2>&1"
    return [
        "sshpass",
        "-p",
        config.password,
        "ssh",
        "-p",
        str(config.port),
        f"{config.user}@{config.ip}",
        remote_cmd,
    ]


def collect_job(config: ConnectionConfig, job: CollectJob, output_dir: Path) -> bool:
    """Run one collection job and write its output file."""
    output_path = output_dir / job.filename
    command_script = command_group(job.commands)
    ssh_args = build_ssh_args(config, command_script)

    CLIStyle.write(
        f"Collecting {job.filename:<14}",
        CLIStyle.COLORS["INFO"],
        end="",
    )
    try:
        with open(output_path, "w", encoding="utf-8") as output_file:
            result = subprocess.run(
                ssh_args,
                stdout=output_file,
                stderr=subprocess.PIPE,
                text=True,
            )
    except OSError as exc:
        CLIStyle.write(" failed", CLIStyle.COLORS["ERROR"])
        CLIStyle.write(f"  {exc}", CLIStyle.COLORS["ERROR"], error=True)
        return False

    if result.returncode != 0:
        CLIStyle.write(" failed", CLIStyle.COLORS["ERROR"])
        if result.stderr:
            CLIStyle.write(f"  {result.stderr.strip()}", CLIStyle.COLORS["ERROR"])
        return False

    CLIStyle.write(" done", CLIStyle.COLORS["OK"])
    return True


def example_config() -> dict[str, Any]:
    """Return an example target configuration object."""
    return {
        "ip": "192.168.1.1",
        "username": "user",
        "password": "admin@123",
        "port": DEFAULT_PORT,
        "files": {
            "base.txt": [
                "ls -alh /opt",
                {
                    "display": "id",
                    "sudo": False,
                },
                {
                    "display": "cat /proc/device-tree/model",
                    "command": "tr -d '\\000' < /proc/device-tree/model 2>/dev/null; echo",
                },
            ],
            "gpu.txt": [
                "nvidia-smi",
                "ls -alh /dev/nvidia* 2>/dev/null || true",
            ],
        },
    }


def write_example_config(path: Path) -> int:
    """Write an example target JSON file."""
    if path.exists():
        CLIStyle.write(
            f"Error: {path} already exists.",
            CLIStyle.COLORS["ERROR"],
            error=True,
        )
        return 1

    with open(path, "w", encoding="utf-8") as file_handle:
        json.dump(example_config(), file_handle, indent=2, ensure_ascii=False)
        file_handle.write("\n")

    CLIStyle.write(f"Created example config: {path}", CLIStyle.COLORS["OK"])
    return 0


def create_parser() -> ColoredArgumentParser:
    """Create the command line parser."""
    examples = [
        (
            "Collect with command line connection fields",
            "-i 192.168.1.1 -u user -p 'admin@123'",
        ),
        (
            "Collect with a JSON config file",
            "-c target.json",
        ),
        (
            "Create an example target config",
            "--example",
        ),
    ]
    notes = [
        'Config JSON: {"ip": "192.168.1.1", "username": "user", "password": "admin@123", "port": 22}',
        "Command objects support sudo: false or as_user: true.",
        "Default output directory: ./info-<ip>",
    ]
    parser = ColoredArgumentParser(
        description="Collect Linux OS information over SSH.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=create_example_text(os.path.basename(sys.argv[0]), examples, notes),
    )
    parser.add_argument(
        "-i",
        "--ip",
        metavar="IP",
        help=CLIStyle.color("Target host IP address.", CLIStyle.COLORS["CONTENT"]),
    )
    parser.add_argument(
        "-u",
        "--user",
        metavar="USER",
        help=CLIStyle.color("SSH username.", CLIStyle.COLORS["CONTENT"]),
    )
    parser.add_argument(
        "-p",
        "--password",
        metavar="PASSWORD",
        help=CLIStyle.color(
            "SSH password and sudo password.", CLIStyle.COLORS["CONTENT"]
        ),
    )
    parser.add_argument(
        "--port",
        metavar="PORT",
        type=int,
        help=CLIStyle.color("SSH port. Defaults to 22.", CLIStyle.COLORS["CONTENT"]),
    )
    parser.add_argument(
        "-c",
        "--config",
        metavar="FILE",
        help=CLIStyle.color("JSON target config file.", CLIStyle.COLORS["CONTENT"]),
    )
    parser.add_argument(
        "--example",
        metavar="FILE",
        nargs="?",
        const="target.json",
        help=CLIStyle.color(
            "Create an example target JSON file. Defaults to target.json.",
            CLIStyle.COLORS["CONTENT"],
        ),
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        metavar="DIR",
        dest="output_dir",
        help=CLIStyle.color(
            "Output directory. Defaults to ./info-<ip>.", CLIStyle.COLORS["CONTENT"]
        ),
    )
    parser.add_argument(
        "--log",
        action="store_true",
        help=CLIStyle.color("Enable debug logging.", CLIStyle.COLORS["CONTENT"]),
    )
    return parser


def run_collection(args: argparse.Namespace) -> int:
    """Run all configured collection jobs."""
    global DEBUG_MODE
    DEBUG_MODE = args.log

    config_data = {}
    if args.config:
        config_data = parse_config_file(Path(args.config).expanduser())

    config = build_connection_config(args, config_data)
    if shutil.which("sshpass") is None:
        raise RuntimeError("sshpass is required but was not found in PATH")

    output_dir = resolve_output_dir(config.ip, args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    config_jobs = parse_config_jobs(config_data)
    jobs = merge_jobs(default_collect_jobs(), config_jobs)

    CLIStyle.write("OS Info Collector", CLIStyle.COLORS["TITLE"])
    CLIStyle.write(
        f"Target : {config.user}@{config.ip}:{config.port}", CLIStyle.COLORS["CONTENT"]
    )
    CLIStyle.write(f"Output : {output_dir}", CLIStyle.COLORS["CONTENT"])
    CLIStyle.write(f"Jobs   : {len(jobs)}", CLIStyle.COLORS["CONTENT"])
    CLIStyle.write()

    success_count = 0
    for job in jobs:
        if collect_job(config, job, output_dir):
            success_count += 1

    CLIStyle.write()
    if success_count == len(jobs):
        CLIStyle.write(f"Done. Wrote {success_count} file(s).", CLIStyle.COLORS["OK"])
        return 0

    failed_count = len(jobs) - success_count
    CLIStyle.write(
        f"Finished with {failed_count} failed job(s).",
        CLIStyle.COLORS["WARNING"],
    )
    return 1


def main() -> int:
    """Main program entry point."""
    parser = create_parser()
    args = parser.parse_args()

    try:
        if args.example:
            return write_example_config(Path(args.example).expanduser())
        return run_collection(args)
    except FileNotFoundError as exc:
        CLIStyle.write(
            f"Error: file not found: {exc.filename}",
            CLIStyle.COLORS["ERROR"],
            error=True,
        )
        return 1
    except Exception as exc:
        if DEBUG_MODE:
            traceback.print_exc()
        CLIStyle.write(f"Error: {str(exc)}", CLIStyle.COLORS["ERROR"], error=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
