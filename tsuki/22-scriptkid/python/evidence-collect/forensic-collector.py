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
import time
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEBUG_MODE = False
DEFAULT_PORT = 22
DEFAULT_REMOTE_BASE = "/tmp"
DEFAULT_MAX_FILE_MB = 100
DEFAULT_MAX_MEMORY_MB = 512
DEFAULT_OUTPUT_PREFIX = "forensic"
DEFAULT_TOOL_NAMES = ["busybox"]
SUDO_MODES = {"auto", "always", "never"}


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
    password: str | None
    port: int
    sudo_mode: str
    sudo_password: str | None
    identity_file: Path | None


@dataclass(frozen=True)
class ForensicOptions:
    """Forensic collection options."""

    pids: list[int]
    process_names: list[str]
    dump_memory: bool
    copy_fd_files: bool
    max_file_mb: int
    max_memory_mb: int
    remote_base: str
    keep_remote: bool
    tool_dir: Path | None
    tool_url: str | None
    tools: list[str]


def debug(
    *args: Any, file: str | None = None, append: bool = True, **kwargs: Any
) -> None:
    """
    Print debug details.
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


def sanitize_output_name(value: str) -> str:
    """Convert a target name to a safe path suffix."""
    safe_value = re.sub(r"[^A-Za-z0-9._-]+", "_", value)
    return safe_value.strip("._-") or "target"


def resolve_output_dir(ip: str, output_dir: str | None) -> Path:
    """Resolve the local output directory path."""
    if output_dir:
        return Path(output_dir).expanduser().resolve()

    timestamp = time.strftime("%Y%m%d-%H%M%S")
    dirname = f"{DEFAULT_OUTPUT_PREFIX}-{sanitize_output_name(ip)}-{timestamp}"
    return (Path.cwd() / dirname).resolve()


def normalize_remote_base(value: str) -> str:
    """Validate the remote base directory."""
    if not value.startswith("/"):
        raise ValueError("Remote base directory must be absolute")
    if "\x00" in value:
        raise ValueError("Remote base directory contains invalid null byte")
    return value.rstrip("/") or "/"


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


def config_section(config_data: dict[str, Any], name: str) -> dict[str, Any]:
    """Return a config section object."""
    value = config_data.get(name, {})
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError(f"Config section must be an object: {name}")
    return value


def config_value(
    config_data: dict[str, Any],
    section_name: str,
    key: str,
    default: Any = None,
) -> Any:
    """Read a value from section first, then top-level config."""
    section = config_section(config_data, section_name)
    if key in section:
        return section[key]
    return config_data.get(key, default)


def config_list_value(
    config_data: dict[str, Any],
    section_name: str,
    key: str,
) -> list[str] | None:
    """Read a config value as a string list."""
    value = config_value(config_data, section_name, key)
    if value is None:
        return None
    if isinstance(value, list):
        return [str(item) for item in value]
    return [str(value)]


def resolve_method(args: argparse.Namespace, config_data: dict[str, Any]) -> str:
    """Resolve the target access method."""
    method = args.method or config_value(config_data, "target", "method")
    if method is None:
        method = "ssh"
    method_text = str(method).lower()
    if method_text not in {"ssh", "telnet"}:
        raise ValueError(f"Unsupported method: {method_text}")
    return method_text


def build_connection_config(
    args: argparse.Namespace,
    config_data: dict[str, Any],
) -> ConnectionConfig:
    """Build SSH connection configuration from CLI arguments."""
    ip = args.ip or config_value(config_data, "target", "ip")
    user = args.user or config_value(config_data, "target", "user")
    user = user or config_value(config_data, "target", "username")
    password = args.password or config_value(config_data, "target", "password")
    identity_file_value = args.identity_file or config_value(
        config_data,
        "target",
        "identity_file",
    )
    identity_file = (
        Path(identity_file_value).expanduser().resolve()
        if identity_file_value
        else None
    )
    if identity_file is not None and not identity_file.is_file():
        raise ValueError(f"Identity file does not exist: {identity_file}")
    port = args.port or config_value(config_data, "target", "port") or DEFAULT_PORT
    sudo_mode = args.sudo or config_value(config_data, "target", "sudo", "auto")
    sudo_mode = str(sudo_mode).lower()
    if sudo_mode not in SUDO_MODES:
        raise ValueError(f"Unsupported sudo mode: {sudo_mode}")
    sudo_password = (
        args.sudo_password
        or config_value(config_data, "target", "sudo_password")
        or password
    )
    missing_fields = [
        field
        for field, value in (
            ("ip", ip),
            ("user", user),
        )
        if not value
    ]
    if not password and identity_file is None:
        missing_fields.append("password or identity_file")
    if missing_fields:
        joined_fields = ", ".join(missing_fields)
        raise ValueError(f"Missing connection field(s): {joined_fields}. Try -h.")

    return ConnectionConfig(
        ip=str(ip),
        user=str(user),
        password=str(password) if password else None,
        port=int(port),
        sudo_mode=sudo_mode,
        sudo_password=str(sudo_password) if sudo_password else None,
        identity_file=identity_file,
    )


def parse_pid_values(values: list[str] | None) -> list[int]:
    """Parse repeated PID options."""
    if not values:
        return []

    pids: list[int] = []
    for value in values:
        for item in value.split(","):
            pid_text = item.strip()
            if not pid_text:
                continue
            if not pid_text.isdigit() or int(pid_text) <= 0:
                raise ValueError(f"Invalid PID: {pid_text}")
            pids.append(int(pid_text))
    return sorted(set(pids))


def parse_name_values(values: list[str] | None) -> list[str]:
    """Parse repeated process name options."""
    if not values:
        return []

    names: list[str] = []
    for value in values:
        name = value.strip()
        if name:
            names.append(name)
    return sorted(set(names))


def parse_tool_values(values: list[str] | None) -> list[str]:
    """Parse repeated staged tool names."""
    tool_names = list(DEFAULT_TOOL_NAMES)
    if not values:
        return sorted(set(tool_names))

    for value in values:
        for item in value.split(","):
            tool_name = item.strip()
            if not tool_name:
                continue
            if not re.fullmatch(r"[A-Za-z0-9._+-]+", tool_name):
                raise ValueError(f"Invalid tool name: {tool_name}")
            tool_names.append(tool_name)
    return sorted(set(tool_names))


def config_bool_value(
    config_data: dict[str, Any],
    section_name: str,
    key: str,
    default: bool = False,
) -> bool:
    """Read a boolean value from config."""
    value = config_value(config_data, section_name, key, default)
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.lower() in {"1", "true", "yes", "on"}
    return bool(value)


def config_int_value(
    config_data: dict[str, Any],
    section_name: str,
    key: str,
    default: int,
) -> int:
    """Read an integer value from config."""
    value = config_value(config_data, section_name, key, default)
    return int(value)


def build_forensic_options(
    args: argparse.Namespace,
    config_data: dict[str, Any],
) -> ForensicOptions:
    """Build forensic collection options from CLI arguments."""
    max_file_mb = int(
        args.max_file_mb
        if args.max_file_mb is not None
        else config_int_value(
            config_data,
            "forensics",
            "max_file_mb",
            DEFAULT_MAX_FILE_MB,
        )
    )
    if max_file_mb <= 0:
        raise ValueError("--max-file-mb must be greater than zero")
    max_memory_mb = int(
        args.max_memory_mb
        if args.max_memory_mb is not None
        else config_int_value(
            config_data,
            "forensics",
            "max_memory_mb",
            DEFAULT_MAX_MEMORY_MB,
        )
    )
    if max_memory_mb < 0:
        raise ValueError("--max-memory-mb must be zero or greater")

    tool_dir_value = args.tool_dir or config_value(config_data, "forensics", "tool_dir")
    tool_dir = Path(tool_dir_value).expanduser().resolve() if tool_dir_value else None
    if tool_dir is not None and not tool_dir.is_dir():
        raise ValueError(f"Tool directory does not exist: {tool_dir}")

    tool_values = args.tool or config_list_value(config_data, "forensics", "tool")
    tools = parse_tool_values(tool_values)
    dump_memory = bool(args.dump_memory) or config_bool_value(
        config_data,
        "forensics",
        "dump_memory",
        False,
    )
    copy_fd_files = bool(args.copy_fd_files) or config_bool_value(
        config_data,
        "forensics",
        "copy_fd_files",
        False,
    )
    if dump_memory and "gdb" not in tools:
        tools.append("gdb")

    pid_values = args.pid or config_list_value(config_data, "forensics", "pid")
    name_values = args.process_name or config_list_value(
        config_data,
        "forensics",
        "process_name",
    )
    remote_base = args.remote_base or config_value(
        config_data,
        "forensics",
        "remote_base",
        DEFAULT_REMOTE_BASE,
    )
    tool_url = args.tool_url or config_value(config_data, "forensics", "tool_url")
    keep_remote = bool(args.keep_remote) or config_bool_value(
        config_data,
        "forensics",
        "keep_remote",
        False,
    )

    return ForensicOptions(
        pids=parse_pid_values(pid_values),
        process_names=parse_name_values(name_values),
        dump_memory=dump_memory,
        copy_fd_files=copy_fd_files,
        max_file_mb=max_file_mb,
        max_memory_mb=max_memory_mb,
        remote_base=normalize_remote_base(str(remote_base)),
        keep_remote=keep_remote,
        tool_dir=tool_dir,
        tool_url=str(tool_url).rstrip("/") if tool_url else None,
        tools=sorted(set(tools)),
    )


def build_remote_shell_selector(config: ConnectionConfig) -> str:
    """Build a remote command prefix that selects a usable shell."""
    return (
        f"FORENSIC_SSH_USER={shlex.quote(config.user)}; "
        'FORENSIC_REMOTE_SHELL=$(awk -F: -v target_user="$FORENSIC_SSH_USER" '
        "'$1 == target_user && $7 ~ /^\\// && $7 !~ /(false|nologin)$/ "
        "{ print $7; exit }' /etc/passwd); "
        'if [ -z "$FORENSIC_REMOTE_SHELL" ] || [ ! -x "$FORENSIC_REMOTE_SHELL" ]; then '
        "FORENSIC_REMOTE_SHELL=''; "
        "for shell_name in zsh bash sh; do "
        'FORENSIC_REMOTE_SHELL=$(awk -F: -v shell_name="$shell_name" '
        '\'$7 ~ ("/" shell_name "$") && $7 !~ /(false|nologin)$/ '
        "{ print $7; exit }' /etc/passwd); "
        '[ -n "$FORENSIC_REMOTE_SHELL" ] && [ -x "$FORENSIC_REMOTE_SHELL" ] && break; '
        "done; "
        "fi; "
        'if [ -z "$FORENSIC_REMOTE_SHELL" ]; then FORENSIC_REMOTE_SHELL=/bin/sh; fi; '
        'if [ ! -x "$FORENSIC_REMOTE_SHELL" ]; then FORENSIC_REMOTE_SHELL=sh; fi'
    )


def build_ssh_args(
    config: ConnectionConfig,
    command_script: str,
    sudo: bool = True,
) -> list[str]:
    """Build sshpass and ssh argument list."""
    remote_shell_selector = build_remote_shell_selector(config)
    if sudo:
        if not config.sudo_password:
            raise ValueError("Sudo password is required when sudo is enabled")
        remote_command = (
            f"{remote_shell_selector}; "
            f"FORENSIC_SUDO_PASSWORD={shlex.quote(config.sudo_password)}; "
            "export FORENSIC_REMOTE_SHELL FORENSIC_SUDO_PASSWORD; "
            "printf '%s\\n' \"$FORENSIC_SUDO_PASSWORD\" "
            "| sudo -S -p '' \"$FORENSIC_REMOTE_SHELL\" "
            f"-c {shlex.quote(command_script)}"
        )
    else:
        remote_command = (
            f"{remote_shell_selector}; "
            "export FORENSIC_REMOTE_SHELL; "
            f'"$FORENSIC_REMOTE_SHELL" -c {shlex.quote(command_script)}'
        )

    ssh_args = [
        "ssh",
        "-F",
        "/dev/null",
        "-o",
        "StrictHostKeyChecking=no",
        "-o",
        "UserKnownHostsFile=/dev/null",
        "-p",
        str(config.port),
    ]
    if config.identity_file is not None:
        ssh_args.extend(["-i", str(config.identity_file)])
        return [*ssh_args, f"{config.user}@{config.ip}", f"{remote_command} 2>&1"]
    if not config.password:
        raise ValueError("SSH password is required when identity_file is not set")
    return [
        "sshpass",
        "-p",
        config.password,
        *ssh_args,
        f"{config.user}@{config.ip}",
        f"{remote_command} 2>&1",
    ]


def remote_is_root(config: ConnectionConfig) -> bool:
    """Check whether the SSH login user is root."""
    if config.user == "root":
        return True
    result = run_simple_remote(config, "id -u", sudo=False)
    if result.returncode != 0:
        return False
    return result.stdout.strip().splitlines()[-1:] == ["0"]


def resolve_ssh_sudo(config: ConnectionConfig) -> bool:
    """Resolve whether collection should run through sudo."""
    if config.sudo_mode == "never":
        return False
    if config.sudo_mode == "always":
        return True
    return not remote_is_root(config)


def build_scp_args(
    config: ConnectionConfig,
    remote_path: str,
    local_path: Path,
) -> list[str]:
    """Build sshpass and scp argument list."""
    scp_args = [
        "scp",
        "-F",
        "/dev/null",
        "-o",
        "StrictHostKeyChecking=no",
        "-o",
        "UserKnownHostsFile=/dev/null",
        "-P",
        str(config.port),
        "-r",
    ]
    if config.identity_file is not None:
        scp_args.extend(["-i", str(config.identity_file)])
        return [
            *scp_args,
            f"{config.user}@{config.ip}:{remote_path}",
            str(local_path),
        ]
    if not config.password:
        raise ValueError("SSH password is required when identity_file is not set")
    return [
        "sshpass",
        "-p",
        config.password,
        *scp_args,
        f"{config.user}@{config.ip}:{remote_path}",
        str(local_path),
    ]


def build_upload_scp_args(
    config: ConnectionConfig,
    local_path: Path,
    remote_path: str,
) -> list[str]:
    """Build sshpass and scp arguments for local-to-remote upload."""
    scp_args = [
        "scp",
        "-F",
        "/dev/null",
        "-o",
        "StrictHostKeyChecking=no",
        "-o",
        "UserKnownHostsFile=/dev/null",
        "-P",
        str(config.port),
    ]
    if config.identity_file is not None:
        scp_args.extend(["-i", str(config.identity_file)])
        return [
            *scp_args,
            str(local_path),
            f"{config.user}@{config.ip}:{remote_path}",
        ]
    if not config.password:
        raise ValueError("SSH password is required when identity_file is not set")
    return [
        "sshpass",
        "-p",
        config.password,
        *scp_args,
        str(local_path),
        f"{config.user}@{config.ip}:{remote_path}",
    ]


def run_simple_remote(
    config: ConnectionConfig,
    command_script: str,
    sudo: bool = False,
) -> subprocess.CompletedProcess[str]:
    """Run a small remote command and return the completed process."""
    return subprocess.run(
        build_ssh_args(config, command_script, sudo=sudo),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def detect_remote_arch(config: ConnectionConfig) -> str:
    """Detect the remote architecture with a minimal command."""
    result = run_simple_remote(config, "uname -m", sudo=False)
    if result.returncode != 0:
        debug("remote arch detection failed", result.stderr.strip())
        return "unknown"
    arch = result.stdout.strip().splitlines()[-1] if result.stdout.strip() else ""
    return sanitize_output_name(arch or "unknown")


def candidate_tool_paths(
    tool_name: str,
    remote_arch: str,
    tool_dir: Path | None,
) -> list[Path]:
    """Return local candidate paths for one staged tool."""
    search_dirs: list[Path] = []
    if tool_dir is not None:
        search_dirs.append(tool_dir)
    script_dir = Path(__file__).resolve().parent
    cwd = Path.cwd().resolve()
    search_dirs.append(script_dir)
    if cwd != script_dir:
        search_dirs.append(cwd)

    names = [
        f"{tool_name}-{remote_arch}",
        f"{tool_name}_{remote_arch}",
        f"{tool_name}.{remote_arch}",
        tool_name,
    ]
    candidates: list[Path] = []
    for directory in search_dirs:
        for name in names:
            candidates.append(directory / name)
    return candidates


def find_local_tool(
    tool_name: str,
    remote_arch: str,
    tool_dir: Path | None,
) -> Path | None:
    """Find a local static tool candidate."""
    for candidate in candidate_tool_paths(tool_name, remote_arch, tool_dir):
        if candidate.is_file():
            return candidate
    return None


def ensure_remote_tool_dir(config: ConnectionConfig, remote_tool_dir: str) -> bool:
    """Create the remote tool directory as the SSH user."""
    command = f"mkdir -p {shlex.quote(remote_tool_dir)} && chmod 700 {shlex.quote(remote_tool_dir)}"
    result = run_simple_remote(config, command, sudo=False)
    if result.returncode == 0:
        return True
    if result.stderr:
        CLIStyle.write(result.stderr.strip(), CLIStyle.COLORS["WARNING"], error=True)
    return False


def upload_tool(
    config: ConnectionConfig,
    local_path: Path,
    remote_path: str,
) -> bool:
    """Upload one local tool binary to the remote host."""
    scp_args = build_upload_scp_args(config, local_path, remote_path)
    result = subprocess.run(
        scp_args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode != 0:
        if result.stderr:
            CLIStyle.write(result.stderr.strip(), CLIStyle.COLORS["WARNING"], error=True)
        return False

    chmod_result = run_simple_remote(config, f"chmod 700 {shlex.quote(remote_path)}")
    return chmod_result.returncode == 0


def stage_local_tools(
    config: ConnectionConfig,
    remote_dir: str,
    options: ForensicOptions,
) -> list[str]:
    """Stage available local static tools and return missing tool names."""
    if not options.tools:
        return []

    remote_arch = detect_remote_arch(config)
    remote_tool_dir = f"{remote_dir}/tools"
    missing_tools: list[str] = []
    if not ensure_remote_tool_dir(config, remote_tool_dir):
        return list(options.tools)

    CLIStyle.write(f"Remote arch : {remote_arch}", CLIStyle.COLORS["CONTENT"])
    for tool_name in options.tools:
        local_tool = find_local_tool(tool_name, remote_arch, options.tool_dir)
        if local_tool is None:
            missing_tools.append(tool_name)
            continue

        remote_path = f"{remote_tool_dir}/{tool_name}"
        CLIStyle.write(
            f"Staging tool: {tool_name} <- {local_tool}",
            CLIStyle.COLORS["INFO"],
        )
        if not upload_tool(config, local_tool, remote_path):
            missing_tools.append(tool_name)
    return missing_tools


def quote_lines(values: list[str]) -> str:
    """Return newline separated single-quoted shell values."""
    return "\n".join(shlex.quote(value) for value in values)


def build_remote_collection_script(
    remote_dir: str,
    options: ForensicOptions,
) -> str:
    """Build the remote forensic collection shell script."""
    pid_values = "\n".join(str(pid) for pid in options.pids)
    name_values = quote_lines(options.process_names)
    tool_values = quote_lines(options.tools)
    tool_url = options.tool_url or ""
    max_file_bytes = options.max_file_mb * 1024 * 1024
    max_memory_bytes = options.max_memory_mb * 1024 * 1024
    dump_memory = "1" if options.dump_memory else "0"
    copy_fd_files = "1" if options.copy_fd_files else "0"

    return f"""set -u
WORK_DIR={shlex.quote(remote_dir)}
TOOL_DIR="$WORK_DIR/tools"
TOOL_BASE_URL={shlex.quote(tool_url)}
MAX_FD_FILE_BYTES={max_file_bytes}
MAX_RAW_MEMORY_BYTES={max_memory_bytes}
DUMP_MEMORY={dump_memory}
COPY_FD_FILES={copy_fd_files}
mkdir -p "$WORK_DIR"
mkdir -p "$TOOL_DIR"
chmod 700 "$WORK_DIR"

section() {{
    printf '\\n===== %s =====\\n' "$1"
}}

run_section() {{
    title="$1"
    shift
    section "$title"
    "$@" 2>&1 || true
}}

run_shell_section() {{
    title="$1"
    command_text="$2"
    section "$title"
    "$FORENSIC_REMOTE_SHELL" -c "$command_text" 2>&1 || true
}}

tool_path() {{
    tool_name="$1"
    if [ -x "$TOOL_DIR/$tool_name" ]; then
        printf '%s\\n' "$TOOL_DIR/$tool_name"
        return 0
    fi
    command -v "$tool_name" 2>/dev/null || true
}}

run_timeout_command() {{
    seconds="$1"
    shift
    timeout_bin=$(tool_path timeout)
    if [ -n "$timeout_bin" ]; then
        "$timeout_bin" "$seconds" "$@" 2>&1 || true
        return
    fi
    if [ -x "$TOOL_DIR/busybox" ]; then
        "$TOOL_DIR/busybox" timeout "$seconds" "$@" 2>&1 || true
        return
    fi
    "$@" 2>&1 || true
}}

run_shell_timeout_section() {{
    title="$1"
    seconds="$2"
    command_text="$3"
    section "$title"
    run_timeout_command "$seconds" "$FORENSIC_REMOTE_SHELL" -c "$command_text"
}}

download_tool() {{
    tool_name="$1"
    [ -n "$TOOL_BASE_URL" ] || return 0
    [ -x "$TOOL_DIR/$tool_name" ] && return 0

    arch=$(uname -m 2>/dev/null || echo unknown)
    for remote_name in "$tool_name-$arch" "$tool_name"; do
        url="$TOOL_BASE_URL/$remote_name"
        tmp_file="$TOOL_DIR/.$tool_name.download"
        rm -f "$tmp_file"
        if command -v wget >/dev/null 2>&1; then
            wget -q -O "$tmp_file" "$url" 2>/dev/null || true
        elif command -v curl >/dev/null 2>&1; then
            curl -fsSL -o "$tmp_file" "$url" 2>/dev/null || true
        else
            busybox_bin=$(tool_path busybox)
            if [ -n "$busybox_bin" ]; then
                "$busybox_bin" wget -q -O "$tmp_file" "$url" 2>/dev/null || true
            fi
        fi

        if [ -s "$tmp_file" ]; then
            mv "$tmp_file" "$TOOL_DIR/$tool_name"
            chmod 700 "$TOOL_DIR/$tool_name"
            printf 'downloaded tool %s from %s\\n' "$tool_name" "$url" >> "$WORK_DIR/tooling.log"
            return 0
        fi
    done
    printf 'missing tool %s and download failed\\n' "$tool_name" >> "$WORK_DIR/tooling.log"
}}

prepare_tools() {{
    : > "$WORK_DIR/tooling.log"
    while IFS= read -r tool_name; do
        [ -n "$tool_name" ] || continue
        download_tool "$tool_name"
        if [ -x "$TOOL_DIR/$tool_name" ]; then
            printf '%s\\t%s\\n' "$tool_name" "$TOOL_DIR/$tool_name" >> "$WORK_DIR/tools.tsv"
        fi
    done <<'FORENSIC_TOOL_LIST'
{tool_values}
FORENSIC_TOOL_LIST
}}

write_manifest() {{
    {{
        echo "collection_time=$(date -Is 2>/dev/null || date)"
        echo "hostname=$(hostname 2>/dev/null || true)"
        echo "kernel=$(uname -a 2>/dev/null || true)"
        echo "work_dir=$WORK_DIR"
        echo "tool_dir=$TOOL_DIR"
        echo "tool_base_url=$TOOL_BASE_URL"
        echo "dump_memory=$DUMP_MEMORY"
        echo "copy_fd_files=$COPY_FD_FILES"
        echo "max_fd_file_bytes=$MAX_FD_FILE_BYTES"
        echo "max_raw_memory_bytes=$MAX_RAW_MEMORY_BYTES"
    }} > "$WORK_DIR/manifest.txt"
}}

collect_system_network() {{
    {{
        run_section "date" date -Is
        run_section "hostname" hostname
        run_shell_section "os-release" "cat /etc/os-release"
        run_section "uname" uname -a
        run_section "uptime" uptime
        run_shell_section "cpu" "command -v lscpu >/dev/null && lscpu || true"
        run_section "memory" free -h
        run_shell_section "vmstat" "command -v vmstat >/dev/null && vmstat 1 5 || true"
        run_shell_section "iostat" "command -v iostat >/dev/null && iostat -xz 1 3 || true"
        run_shell_section "proc-diskstats" "cat /proc/diskstats"
        run_shell_section "proc-vmstat" "cat /proc/vmstat"
    }} > "$WORK_DIR/system_io.txt"

    {{
        run_shell_section "ip-addr" "ip -br addr"
        run_shell_section "ip-link-stats" "ip -s link"
        run_shell_section "routes" "ip route"
        run_shell_section "neighbors" "ip neigh"
        run_shell_section "ss-summary" "ss -s"
        run_shell_section "ss-process" "ss -plantu"
        run_shell_section "proc-net-dev" "cat /proc/net/dev"
        run_shell_section "proc-net-tcp" "cat /proc/net/tcp /proc/net/tcp6 2>/dev/null"
        run_shell_section "proc-net-udp" "cat /proc/net/udp /proc/net/udp6 2>/dev/null"
        run_shell_section "nstat" "command -v nstat >/dev/null && nstat -az || true"
        run_shell_section "sar-network" "command -v sar >/dev/null && sar -n DEV,TCP,ETCP 1 3 || true"
        run_shell_section "conntrack-sample" "command -v conntrack >/dev/null && conntrack -L 2>/dev/null | head -n 5000 || true"
        run_shell_section "resolv-conf" "cat /etc/resolv.conf"
        run_shell_section "hosts" "cat /etc/hosts"
    }} > "$WORK_DIR/network_io.txt"

    {{
        run_shell_section "ps-auxww" "ps auxww"
        run_shell_section "ps-detailed" "ps -eo pid,ppid,user,lstart,etime,stat,comm,args"
        run_shell_section "pstree" "command -v pstree >/dev/null && pstree -alp || true"
    }} > "$WORK_DIR/process_index.txt"
}}

resolve_targets() {{
    mkdir -p "$WORK_DIR/process"
    : > "$WORK_DIR/process/target_pids.txt"

    {{
        while IFS= read -r requested_pid; do
            [ -n "$requested_pid" ] || continue
            if [ -d "/proc/$requested_pid" ]; then
                printf '%s\\n' "$requested_pid"
            else
                printf 'missing pid: %s\\n' "$requested_pid" >> "$WORK_DIR/process/missing_targets.txt"
            fi
        done <<'FORENSIC_PID_LIST'
{pid_values}
FORENSIC_PID_LIST

        while IFS= read -r process_name; do
            [ -n "$process_name" ] || continue
            if command -v pgrep >/dev/null 2>&1; then
                pgrep -f -- "$process_name" 2>/dev/null || true
            else
                ps -eo pid=,args= | awk -v pattern="$process_name" 'index($0, pattern) {{ print $1 }}'
            fi
        done <<'FORENSIC_NAME_LIST'
{name_values}
FORENSIC_NAME_LIST
    }} | sort -un > "$WORK_DIR/process/target_pids.txt"
}}

collect_fd_links() {{
    pid="$1"
    pid_dir="$2"
    : > "$pid_dir/fd_links.tsv"
    : > "$pid_dir/files_from_fds.txt"
    for fd_path in /proc/"$pid"/fd/*; do
        [ -e "$fd_path" ] || continue
        fd_name="${{fd_path##*/}}"
        target_path=$(readlink "$fd_path" 2>/dev/null || true)
        printf '%s\\t%s\\n' "$fd_name" "$target_path" >> "$pid_dir/fd_links.tsv"
        case "$target_path" in
            /*)
                printf '%s\\n' "$target_path" | sed 's/ (deleted)$//' >> "$pid_dir/files_from_fds.txt"
                ;;
        esac
    done
    sort -u "$pid_dir/files_from_fds.txt" -o "$pid_dir/files_from_fds.txt" 2>/dev/null || true
}}

copy_regular_fd_files() {{
    pid="$1"
    pid_dir="$2"
    mkdir -p "$pid_dir/fd_files"
    : > "$pid_dir/copied_fd_files.tsv"
    for fd_path in /proc/"$pid"/fd/*; do
        [ -e "$fd_path" ] || continue
        fd_name="${{fd_path##*/}}"
        target_path=$(readlink "$fd_path" 2>/dev/null || true)
        file_type=$(stat -Lc '%F' "$fd_path" 2>/dev/null || true)
        file_size=$(stat -Lc '%s' "$fd_path" 2>/dev/null || echo 0)
        [ "$file_type" = "regular file" ] || continue
        [ "$file_size" -le "$MAX_FD_FILE_BYTES" ] || {{
            printf '%s\\tSKIP_SIZE\\t%s\\t%s\\n' "$fd_name" "$file_size" "$target_path" >> "$pid_dir/copied_fd_files.tsv"
            continue
        }}
        out_file="$pid_dir/fd_files/fd_${{fd_name}}.bin"
        if cp -L -- "$fd_path" "$out_file" 2>/dev/null; then
            printf '%s\\tCOPIED\\t%s\\t%s\\t%s\\n' "$fd_name" "$file_size" "$target_path" "$out_file" >> "$pid_dir/copied_fd_files.tsv"
        else
            printf '%s\\tCOPY_FAILED\\t%s\\t%s\\n' "$fd_name" "$file_size" "$target_path" >> "$pid_dir/copied_fd_files.tsv"
        fi
    done
}}

dump_raw_memory_regions() {{
    pid="$1"
    pid_dir="$2"
    raw_dir="$pid_dir/memory/raw"
    mkdir -p "$raw_dir"
    : > "$raw_dir/regions.tsv"
    total_bytes=0
    index=0

    while IFS= read -r map_line; do
        range=$(printf '%s\\n' "$map_line" | awk '{{ print $1 }}')
        perms=$(printf '%s\\n' "$map_line" | awk '{{ print $2 }}')
        path=$(printf '%s\\n' "$map_line" | cut -d' ' -f6-)
        case "$perms" in
            r*) ;;
            *) continue ;;
        esac

        start_hex="${{range%-*}}"
        end_hex="${{range#*-}}"
        start_dec=$((0x$start_hex))
        end_dec=$((0x$end_hex))
        size=$((end_dec - start_dec))
        [ "$size" -gt 0 ] || continue

        if [ "$MAX_RAW_MEMORY_BYTES" -gt 0 ]; then
            remaining=$((MAX_RAW_MEMORY_BYTES - total_bytes))
            [ "$remaining" -gt 0 ] || break
            [ "$size" -le "$remaining" ] || size="$remaining"
        fi

        index=$((index + 1))
        out_file=$(printf '%s/region_%05d_%s-%s.bin' "$raw_dir" "$index" "$start_hex" "$end_hex")
        log_file=$(printf '%s/region_%05d.log' "$raw_dir" "$index")
        if dd if="/proc/$pid/mem" of="$out_file" bs=4096 skip="$start_dec" count="$size" iflag=skip_bytes,count_bytes > "$log_file" 2>&1; then
            written=$(stat -c '%s' "$out_file" 2>/dev/null || echo 0)
            total_bytes=$((total_bytes + written))
            printf '%s\\t%s\\t%s\\t%s\\t%s\\t%s\\n' "$index" "$start_hex" "$end_hex" "$perms" "$written" "$path" >> "$raw_dir/regions.tsv"
        else
            printf '%s\\t%s\\t%s\\t%s\\tFAILED\\t%s\\n' "$index" "$start_hex" "$end_hex" "$perms" "$path" >> "$raw_dir/regions.tsv"
            rm -f "$out_file"
        fi
    done < "/proc/$pid/maps"
}}

dump_process_memory() {{
    pid="$1"
    pid_dir="$2"
    mkdir -p "$pid_dir/memory"
    {{
        echo "pid=$pid"
        echo "started=$(date -Is 2>/dev/null || date)"
        gcore_bin=$(tool_path gcore)
        gdb_bin=$(tool_path gdb)
        if [ -n "$gcore_bin" ]; then
            cd "$pid_dir/memory" && "$gcore_bin" -o "core.$pid" "$pid"
        elif [ -n "$gdb_bin" ]; then
            "$gdb_bin" --batch -ex "gcore $pid_dir/memory/core.$pid" -ex detach -ex quit -p "$pid"
        else
            echo "Neither gcore nor gdb is available."
        fi
        if ! find "$pid_dir/memory" -maxdepth 1 -type f -name "core.$pid*" | grep -q .; then
            echo "core dump not found; trying raw /proc/$pid/mem region dump"
            dump_raw_memory_regions "$pid" "$pid_dir"
        fi
        echo "finished=$(date -Is 2>/dev/null || date)"
    }} > "$pid_dir/memory/dump.log" 2>&1 || true
}}

collect_process() {{
    pid="$1"
    pid_dir="$WORK_DIR/process/$pid"
    mkdir -p "$pid_dir"

    {{
        run_shell_section "ps" "ps -p $pid -o pid,ppid,user,lstart,etime,stat,comm,args"
        run_shell_section "status" "cat /proc/$pid/status"
        run_shell_section "cmdline" "tr '\\000' ' ' < /proc/$pid/cmdline; echo"
        run_shell_section "environ" "tr '\\000' '\\n' < /proc/$pid/environ"
        run_shell_section "cwd-root-exe" "readlink /proc/$pid/cwd; readlink /proc/$pid/root; readlink /proc/$pid/exe"
        run_shell_section "limits" "cat /proc/$pid/limits"
        run_shell_section "cgroup" "cat /proc/$pid/cgroup"
        run_shell_section "mountinfo" "cat /proc/$pid/mountinfo"
        run_shell_section "smaps-rollup" "cat /proc/$pid/smaps_rollup 2>/dev/null || true"
    }} > "$pid_dir/summary.txt"

    cp "/proc/$pid/maps" "$pid_dir/maps.txt" 2>/dev/null || true
    cp "/proc/$pid/smaps" "$pid_dir/smaps.txt" 2>/dev/null || true
    cp -a "/proc/$pid/fdinfo" "$pid_dir/fdinfo" 2>/dev/null || true
    collect_fd_links "$pid" "$pid_dir"

    {{
        run_shell_timeout_section "lsof" 15 "command -v lsof >/dev/null && lsof -nP -p $pid || true"
        run_shell_section "sockets-by-ss" "ss -pan 2>/dev/null | grep -F \\"pid=$pid,\\" || true"
        run_shell_section "socket-fds" "ls -al /proc/$pid/fd 2>/dev/null | grep socket || true"
    }} > "$pid_dir/open_files_and_sockets.txt"

    if [ "$COPY_FD_FILES" = "1" ]; then
        copy_regular_fd_files "$pid" "$pid_dir"
    fi
    if [ "$DUMP_MEMORY" = "1" ]; then
        dump_process_memory "$pid" "$pid_dir"
    fi
}}

collect_targets() {{
    resolve_targets
    while IFS= read -r pid; do
        [ -n "$pid" ] || continue
        if [ -d "/proc/$pid" ]; then
            collect_process "$pid"
        fi
    done < "$WORK_DIR/process/target_pids.txt"
}}

finish_collection() {{
    sha256_bin=$(tool_path sha256sum)
    if [ -n "$sha256_bin" ]; then
        find "$WORK_DIR" -type f -exec "$sha256_bin" {{}} + > "$WORK_DIR/sha256sums.txt" 2>/dev/null || true
    elif [ -x "$TOOL_DIR/busybox" ]; then
        find "$WORK_DIR" -type f -exec "$TOOL_DIR/busybox" sha256sum {{}} + > "$WORK_DIR/sha256sums.txt" 2>/dev/null || true
    fi
    chmod -R u+rwX,go+rX "$WORK_DIR" 2>/dev/null || true
}}

prepare_tools
write_manifest
collect_system_network
collect_targets
finish_collection
printf 'REMOTE_DIR=%s\\n' "$WORK_DIR"
"""


def run_remote_script(
    config: ConnectionConfig,
    script: str,
    log_path: Path,
    sudo: bool,
) -> bool:
    """Run a remote script and write stdout/stderr to a local log."""
    ssh_args = build_ssh_args(config, script, sudo=sudo)
    debug("ssh command", " ".join(shlex.quote(arg) for arg in ssh_args))
    with open(log_path, "w", encoding="utf-8") as log_file:
        result = subprocess.run(
            ssh_args,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            text=True,
        )
    return result.returncode == 0


def fetch_remote_dir(
    config: ConnectionConfig,
    remote_dir: str,
    output_dir: Path,
) -> bool:
    """Fetch the remote evidence directory into the local output directory."""
    scp_args = build_scp_args(config, remote_dir, output_dir)
    debug("scp command", " ".join(shlex.quote(arg) for arg in scp_args))
    result = subprocess.run(
        scp_args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    if result.returncode != 0:
        if result.stderr:
            CLIStyle.write(result.stderr.strip(), CLIStyle.COLORS["ERROR"], error=True)
        return False
    return True


def cleanup_remote_dir(
    config: ConnectionConfig,
    remote_dir: str,
    sudo: bool,
) -> None:
    """Remove the remote temporary evidence directory."""
    cleanup_script = f"rm -rf -- {shlex.quote(remote_dir)}"
    ssh_args = build_ssh_args(config, cleanup_script, sudo=sudo)
    subprocess.run(
        ssh_args,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        text=True,
    )


def example_config() -> dict[str, Any]:
    """Return an example target configuration object."""
    return {
        "target": {
            "method": "ssh",
            "ip": "192.168.1.10",
            "port": 22,
            "username": "root",
            "password": "password",
            "identity_file": "",
            "sudo": "auto",
            "sudo_password": "password",
        },
        "forensics": {
            "pid": [1234],
            "process_name": ["boa"],
            "dump_memory": True,
            "copy_fd_files": True,
            "max_file_mb": DEFAULT_MAX_FILE_MB,
            "max_memory_mb": DEFAULT_MAX_MEMORY_MB,
            "remote_base": DEFAULT_REMOTE_BASE,
            "output_dir": "./forensic-target",
            "tool_dir": "./tool",
            "tool_url": "http://192.168.1.2:18080",
            "tool": ["busybox"],
            "keep_remote": False,
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
            "Collect system, network and IO forensic snapshot",
            "-i 192.168.1.10 -u user -p 'password'",
        ),
        (
            "Collect a target process by PID with file-handle paths",
            "-i 192.168.1.10 -u user -p 'password' --pid 1234",
        ),
        (
            "Dump memory and copy small regular files opened by a process",
            "-i 192.168.1.10 -u user -p 'password' --process-name nginx --dump-memory --copy-fd-files",
        ),
        (
            "Use local static tools or a maintained download server",
            "-i 192.168.1.10 -u user -p 'password' --dump-memory --tool-dir ./tools --tool-url https://example.local/forensic-tools",
        ),
        (
            "Collect from a JSON target config",
            "-c target-forensic.json",
        ),
        (
            "Create an example target config",
            "--example-config target-forensic.json",
        ),
    ]
    notes = [
        "Primary collection path is SSH target config or SSH CLI fields.",
        "Telnet configs are recognized, but telnet collection is not implemented yet.",
        "Memory dumping requires gcore or gdb on the target host and may briefly pause the process.",
        "If gdb/gcore fails, readable memory regions are dumped from /proc/<pid>/mem up to --max-memory-mb.",
        "Opened regular files are copied only when --copy-fd-files is set.",
        "Static tools are searched as <tool>-<arch>, <tool>_<arch>, <tool>.<arch>, then <tool>.",
        "Output includes sha256sums.txt for collected files.",
    ]
    parser = ColoredArgumentParser(
        description="Collect targeted Linux forensic evidence over network login.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=create_example_text(os.path.basename(sys.argv[0]), examples, notes),
    )
    parser.add_argument(
        "-c",
        "--config",
        metavar="FILE",
        help=CLIStyle.color("JSON target config file.", CLIStyle.COLORS["CONTENT"]),
    )
    parser.add_argument(
        "--example-config",
        metavar="FILE",
        nargs="?",
        const="target-forensic.json",
        help=CLIStyle.color(
            "Create an example target JSON config.",
            CLIStyle.COLORS["CONTENT"],
        ),
    )
    parser.add_argument(
        "--method",
        choices=["ssh", "telnet"],
        help=CLIStyle.color(
            "Target access method. Defaults to ssh.",
            CLIStyle.COLORS["CONTENT"],
        ),
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
        "--identity-file",
        metavar="FILE",
        help=CLIStyle.color(
            "SSH private key file. Password is optional when this is set.",
            CLIStyle.COLORS["CONTENT"],
        ),
    )
    parser.add_argument(
        "--port",
        metavar="PORT",
        type=int,
        help=CLIStyle.color("SSH port. Defaults to 22.", CLIStyle.COLORS["CONTENT"]),
    )
    parser.add_argument(
        "--sudo",
        choices=sorted(SUDO_MODES),
        help=CLIStyle.color(
            "Privilege mode for SSH collection: auto, always, or never.",
            CLIStyle.COLORS["CONTENT"],
        ),
    )
    parser.add_argument(
        "--sudo-password",
        metavar="PASSWORD",
        help=CLIStyle.color(
            "Sudo password. Defaults to SSH password.",
            CLIStyle.COLORS["CONTENT"],
        ),
    )
    parser.add_argument(
        "--pid",
        action="append",
        metavar="PID",
        help=CLIStyle.color(
            "Target PID. Can be repeated or comma-separated.",
            CLIStyle.COLORS["CONTENT"],
        ),
    )
    parser.add_argument(
        "--process-name",
        action="append",
        metavar="NAME",
        help=CLIStyle.color(
            "Target process name or command-line substring.",
            CLIStyle.COLORS["CONTENT"],
        ),
    )
    parser.add_argument(
        "--dump-memory",
        action="store_true",
        help=CLIStyle.color(
            "Create core dumps for target processes with gcore or gdb.",
            CLIStyle.COLORS["CONTENT"],
        ),
    )
    parser.add_argument(
        "--copy-fd-files",
        action="store_true",
        help=CLIStyle.color(
            "Copy regular files referenced by target process file descriptors.",
            CLIStyle.COLORS["CONTENT"],
        ),
    )
    parser.add_argument(
        "--max-file-mb",
        metavar="MB",
        type=int,
        help=CLIStyle.color(
            "Maximum size for each copied file descriptor file.",
            CLIStyle.COLORS["CONTENT"],
        ),
    )
    parser.add_argument(
        "--max-memory-mb",
        metavar="MB",
        type=int,
        help=CLIStyle.color(
            "Maximum raw /proc/<pid>/mem fallback dump size. 0 means unlimited.",
            CLIStyle.COLORS["CONTENT"],
        ),
    )
    parser.add_argument(
        "--remote-base",
        metavar="DIR",
        help=CLIStyle.color(
            "Remote temporary base directory. Defaults to /tmp.",
            CLIStyle.COLORS["CONTENT"],
        ),
    )
    parser.add_argument(
        "--tool-dir",
        metavar="DIR",
        help=CLIStyle.color(
            "Local directory for static tools. Defaults also search script directory.",
            CLIStyle.COLORS["CONTENT"],
        ),
    )
    parser.add_argument(
        "--tool-url",
        metavar="URL",
        help=CLIStyle.color(
            "Base URL used by the target to download missing tools.",
            CLIStyle.COLORS["CONTENT"],
        ),
    )
    parser.add_argument(
        "--tool",
        action="append",
        metavar="NAME",
        help=CLIStyle.color(
            "Additional static tool name to stage or download.",
            CLIStyle.COLORS["CONTENT"],
        ),
    )
    parser.add_argument(
        "-o",
        "--output-dir",
        metavar="DIR",
        dest="output_dir",
        help=CLIStyle.color(
            "Local output directory. Defaults to ./forensic-<ip>-<timestamp>.",
            CLIStyle.COLORS["CONTENT"],
        ),
    )
    parser.add_argument(
        "--keep-remote",
        action="store_true",
        help=CLIStyle.color(
            "Keep the remote temporary evidence directory after fetching.",
            CLIStyle.COLORS["CONTENT"],
        ),
    )
    parser.add_argument(
        "--log",
        action="store_true",
        help=CLIStyle.color("Enable debug logging.", CLIStyle.COLORS["CONTENT"]),
    )
    return parser


def move_collection_log(log_path: Path, output_dir: Path) -> None:
    """Move the SSH collection log into the evidence directory."""
    if not output_dir.exists():
        return
    target_path = output_dir / "collection.log"
    shutil.move(str(log_path), str(target_path))


def run_collection(args: argparse.Namespace) -> int:
    """Run forensic evidence collection."""
    global DEBUG_MODE
    DEBUG_MODE = bool(args.log)

    config_data = {}
    if args.config:
        config_data = parse_config_file(Path(args.config).expanduser())

    method = resolve_method(args, config_data)
    if method == "telnet":
        raise ValueError(
            "Telnet target config is recognized, but telnet collection is not "
            "implemented yet. Use method=ssh for collection."
        )
    return run_ssh_collection(args, config_data)


def run_ssh_collection(
    args: argparse.Namespace,
    config_data: dict[str, Any],
) -> int:
    """Run forensic evidence collection over SSH."""
    config = build_connection_config(args, config_data)
    options = build_forensic_options(args, config_data)
    if config.identity_file is None and shutil.which("sshpass") is None:
        raise RuntimeError("sshpass is required but was not found in PATH")

    output_dir_value = args.output_dir or config_value(
        config_data,
        "forensics",
        "output_dir",
    )
    output_dir = resolve_output_dir(config.ip, output_dir_value)
    if output_dir.exists():
        raise ValueError(f"Output directory already exists: {output_dir}")
    output_dir.parent.mkdir(parents=True, exist_ok=True)

    remote_name = output_dir.name
    remote_dir = f"{options.remote_base}/{remote_name}"
    log_path = output_dir.parent / f"{output_dir.name}.collection.log"

    CLIStyle.write("Forensic Collector", CLIStyle.COLORS["TITLE"])
    CLIStyle.write(
        f"Target      : {config.user}@{config.ip}:{config.port}",
        CLIStyle.COLORS["CONTENT"],
    )
    CLIStyle.write(f"Remote dir  : {remote_dir}", CLIStyle.COLORS["CONTENT"])
    CLIStyle.write(f"Output      : {output_dir}", CLIStyle.COLORS["CONTENT"])
    CLIStyle.write(
        f"Target PIDs : {', '.join(str(pid) for pid in options.pids) or '-'}",
        CLIStyle.COLORS["CONTENT"],
    )
    CLIStyle.write(
        f"Names       : {', '.join(options.process_names) or '-'}",
        CLIStyle.COLORS["CONTENT"],
    )
    CLIStyle.write(
        f"Tools       : {', '.join(options.tools) or '-'}",
        CLIStyle.COLORS["CONTENT"],
    )
    CLIStyle.write()

    use_sudo = resolve_ssh_sudo(config)
    CLIStyle.write(
        f"Sudo        : {'yes' if use_sudo else 'no'} ({config.sudo_mode})",
        CLIStyle.COLORS["CONTENT"],
    )

    missing_tools = stage_local_tools(config, remote_dir, options)
    if missing_tools and options.tool_url:
        CLIStyle.write(
            f"Remote will try downloading: {', '.join(missing_tools)}",
            CLIStyle.COLORS["WARNING"],
        )
    elif missing_tools:
        CLIStyle.write(
            f"No local static tool found: {', '.join(missing_tools)}",
            CLIStyle.COLORS["WARNING"],
        )

    script = build_remote_collection_script(remote_dir, options)

    CLIStyle.write("Collecting remote evidence", CLIStyle.COLORS["INFO"], end="")
    if not run_remote_script(config, script, log_path, sudo=use_sudo):
        CLIStyle.write(" failed", CLIStyle.COLORS["ERROR"])
        CLIStyle.write(f"Log: {log_path}", CLIStyle.COLORS["ERROR"], error=True)
        return 1
    CLIStyle.write(" done", CLIStyle.COLORS["OK"])

    CLIStyle.write("Fetching evidence directory", CLIStyle.COLORS["INFO"], end="")
    if not fetch_remote_dir(config, remote_dir, output_dir):
        CLIStyle.write(" failed", CLIStyle.COLORS["ERROR"])
        CLIStyle.write(f"Remote dir kept: {remote_dir}", CLIStyle.COLORS["WARNING"])
        return 1
    CLIStyle.write(" done", CLIStyle.COLORS["OK"])
    move_collection_log(log_path, output_dir)

    if not options.keep_remote:
        CLIStyle.write("Cleaning remote directory", CLIStyle.COLORS["INFO"], end="")
        cleanup_remote_dir(config, remote_dir, sudo=use_sudo)
        CLIStyle.write(" done", CLIStyle.COLORS["OK"])
    else:
        CLIStyle.write(f"Remote dir kept: {remote_dir}", CLIStyle.COLORS["WARNING"])

    CLIStyle.write()
    CLIStyle.write(f"Done. Evidence: {output_dir}", CLIStyle.COLORS["OK"])
    return 0


def main() -> int:
    """Main program entry point."""
    parser = create_parser()
    args = parser.parse_args()

    try:
        if args.example_config:
            return write_example_config(Path(args.example_config).expanduser())
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
