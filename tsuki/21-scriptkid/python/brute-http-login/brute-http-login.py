#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# pip install requests

import argparse
import datetime
import json
import os
import sys
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from threading import Lock, local
from typing import Any
from urllib.parse import urljoin, urlparse

import requests
import urllib3
from urllib3.exceptions import InsecureRequestWarning

DEBUG_MODE = False

DEFAULT_INTERVAL_SECONDS = 0.0
DEFAULT_THREADS = 1
DEFAULT_TIMEOUT_SECONDS = 30.0
DEFAULT_VERIFY_TLS = False
DEFAULT_PROGRESS_EVERY = 1000

DEFAULT_USERNAME_FIELD = "username"
DEFAULT_PASSWORD_FIELD = "password"


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
    output_line("Status: 200", CLIStyle.COLORS["CONTENT"])

    return = None
    ```
    """
    print(CLIStyle.color(text, color))


def debug(message: str, *, enabled: bool) -> None:
    """
    Print debug messages when enabled.

    ```python
    debug("starting", enabled=True)

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
class BaseRequest:
    """Immutable base request definition."""

    method: str
    url: str
    headers: dict[str, str]
    raw_body: str | None


@dataclass(frozen=True)
class Account:
    """Username and password pair."""

    username: str
    password: str


@dataclass(frozen=True)
class SendResult:
    """Result of one HTTP request."""

    requested_at: str
    username: str
    password: str
    ok: bool
    status_code: int | None
    json_data: Any | None
    text: str | None
    error: str | None


@dataclass(frozen=True)
class BatchSpec:
    """Batch mode payload specification."""

    payload_template: dict[str, Any]
    username_field: str
    password_field: str


def get_header_value(headers: dict[str, str], header_name: str) -> str | None:
    """Read a header value by name, case-insensitive."""
    target = header_name.lower()
    for key, value in headers.items():
        if key.lower() == target:
            return value
    return None


def infer_scheme(headers: dict[str, str], base_url: str | None = None) -> str:
    """Infer URL scheme from base URL or forwarding headers."""
    if base_url:
        parsed_base = urlparse(base_url)
        if parsed_base.scheme in {"http", "https"}:
            return parsed_base.scheme

    forwarded_proto = get_header_value(headers, "X-Forwarded-Proto")
    if forwarded_proto:
        candidate = forwarded_proto.split(",", 1)[0].strip().lower()
        if candidate in {"http", "https"}:
            return candidate

    for header_name in ("Origin", "Referer"):
        header_value = get_header_value(headers, header_name)
        if not header_value:
            continue
        parsed = urlparse(header_value)
        if parsed.scheme in {"http", "https"}:
            return parsed.scheme

    return "http"


def resolve_request_url(
    path_or_url: str, *, headers: dict[str, str], base_url: str | None
) -> str:
    """Resolve absolute URL for request-line path or absolute URL."""
    if path_or_url.startswith("http://") or path_or_url.startswith("https://"):
        return path_or_url

    if base_url and base_url.strip():
        return urljoin(base_url.rstrip("/") + "/", path_or_url)

    host = get_header_value(headers, "Host")
    if not host:
        raise ValueError(
            "base_url is required for relative path when Host header is missing"
        )

    scheme = infer_scheme(headers, base_url=base_url)
    inferred_base = f"{scheme}://{host}"
    return urljoin(inferred_base.rstrip("/") + "/", path_or_url)


def parse_raw_request(raw: str, base_url: str | None = None) -> BaseRequest:
    """
    Parse raw HTTP request text.

    Supported formats:
    - Absolute URL in request line: "POST https://example.com/path HTTP/1.1"
    - Relative path in request line: "POST /path HTTP/1.1" (uses base_url or Host)
    """
    normalized_raw = raw.strip().replace("\r\n", "\n")
    if not normalized_raw:
        raise ValueError("raw request is empty")

    lines = normalized_raw.split("\n")
    request_line = lines[0].strip()
    parts = request_line.split()
    if len(parts) < 2:
        raise ValueError("invalid request line")

    method = parts[0].upper()
    path_or_url = parts[1]

    headers: dict[str, str] = {}
    body_lines: list[str] = []
    in_body = False

    for line in lines[1:]:
        if not in_body:
            if line.strip() == "":
                in_body = True
                continue
            if ":" in line:
                key, value = line.split(":", 1)
                headers[key.strip()] = value.strip()
            continue
        body_lines.append(line)

    body = "\n".join(body_lines) if body_lines else None
    url = resolve_request_url(path_or_url, headers=headers, base_url=base_url)
    return BaseRequest(method=method, url=url, headers=headers, raw_body=body)


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


def parse_http_target_file(path: str) -> dict[str, Any]:
    """Load HTTP target JSON from file (same pattern as FTP/Telnet --target-file)."""
    text = load_text_file(path).strip()
    if not text:
        raise ValueError("target file is empty")
    return parse_json_object(text)


def cli_flag_provided(flag: str) -> bool:
    """Return True if argv contains the given long option (e.g. --threads)."""
    for arg in sys.argv[1:]:
        if arg == flag or arg.startswith(f"{flag}="):
            return True
    return False


def pick_str(cli: str, file_val: Any, default: str) -> str:
    """Prefer non-empty CLI, then file string, then default."""
    stripped = (cli or "").strip()
    if stripped:
        return stripped
    if isinstance(file_val, str) and file_val.strip():
        return file_val.strip()
    return default


def json_int(value: Any) -> int | None:
    """Parse JSON number to int for thread counts etc."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)
    return None


def json_float(value: Any) -> float | None:
    """Parse JSON number to float."""
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    return None


def infer_http_method(fv: dict[str, Any]) -> str:
    """
    Infer GET vs POST when method is omitted: body object -> POST, params object -> GET.
    """
    explicit = fv.get("method")
    if isinstance(explicit, str) and explicit.strip():
        return explicit.strip().upper()

    has_body = isinstance(fv.get("body"), dict)
    has_params = isinstance(fv.get("params"), dict)
    if has_body and has_params:
        raise ValueError(
            "target file: set method when both body and params are present"
        )
    if has_body:
        return "POST"
    if has_params:
        return "GET"
    raise ValueError("target file: set method or provide body (POST) or params (GET)")


def get_payload_template_from_target(fv: dict[str, Any], method: str) -> dict[str, Any]:
    """Batch payload template from target file: body for non-GET, params for GET."""
    method_u = method.upper()
    if method_u == "GET":
        params = fv.get("params")
        if not isinstance(params, dict):
            raise ValueError("target file: GET batch requires params object")
        return dict(params)

    body = fv.get("body")
    if isinstance(body, dict):
        return dict(body)

    raise ValueError("target file: non-GET batch requires body object")


def target_has_body_or_params(fv: dict[str, Any]) -> bool:
    """Return True when target JSON defines batch body or query template."""
    return isinstance(fv.get("body"), dict) or isinstance(fv.get("params"), dict)


def effective_batch_method(fv: dict[str, Any], raw: BaseRequest) -> str:
    """Prefer target body/params for verb; else explicit method in JSON; else raw request line."""
    if isinstance(fv.get("body"), dict) and isinstance(fv.get("params"), dict):
        raise ValueError(
            "target file: set method when both body and params are present"
        )
    if isinstance(fv.get("body"), dict):
        return "POST"
    if isinstance(fv.get("params"), dict):
        return "GET"
    explicit = fv.get("method")
    if isinstance(explicit, str) and explicit.strip():
        return explicit.strip().upper()
    return raw.method.upper()


def merge_raw_and_target(
    raw: BaseRequest,
    fv: dict[str, Any],
    args: argparse.Namespace,
) -> BaseRequest:
    """
    Merge Burp raw request with http-target.json.

    URL and Host (and other raw headers) win on conflict. Target headers and
    --headers-json apply first; raw headers overwrite.
    """
    merged_headers: dict[str, str] = {}
    if isinstance(fv.get("headers"), dict):
        merged_headers.update({str(k): str(v) for k, v in fv["headers"].items()})
    cli_headers = parse_headers_json(args.headers_json)
    if cli_headers:
        merged_headers.update(cli_headers)
    merged_headers.update(raw.headers)
    merged_headers = remove_content_length_header(merged_headers)

    method = effective_batch_method(fv, raw)
    return BaseRequest(
        method=method,
        url=raw.url,
        headers=merged_headers,
        raw_body=raw.raw_body,
    )


def parse_raw_body_as_template_object(raw_body: str) -> dict[str, Any]:
    """Parse raw HTTP body as JSON object for batch template."""
    try:
        data = json.loads(raw_body.strip())
    except json.JSONDecodeError as error:
        raise ValueError(
            "raw request body must be a JSON object when used as batch template"
        ) from error
    if not isinstance(data, dict):
        raise ValueError("raw request body JSON must be an object")
    return dict(data)


def resolve_batch_payload_args(
    args: argparse.Namespace,
    target_data: dict[str, Any] | None,
    raw_base: BaseRequest | None,
    base_request: BaseRequest,
) -> None:
    """
    Set args.body_json / args.body_file for batch mode.

    Priority: target body or params > --body-json/--body-file > raw body as JSON.
    """
    if target_data and target_has_body_or_params(target_data):
        template = get_payload_template_from_target(
            target_data,
            base_request.method.upper(),
        )
        args.body_json = json.dumps(template, ensure_ascii=False)
        args.body_file = ""
        return
    if args.body_json.strip() or args.body_file.strip():
        return
    if raw_base is not None and raw_base.raw_body and raw_base.raw_body.strip():
        template = parse_raw_body_as_template_object(raw_base.raw_body)
        args.body_json = json.dumps(template, ensure_ascii=False)
        args.body_file = ""
        return
    raise ValueError(
        "batch payload: set body or params in target JSON, or --body-json/--body-file, "
        "or put a JSON object in the raw request body"
    )


def load_raw_base_request(args: argparse.Namespace) -> BaseRequest:
    """Parse raw request file into BaseRequest without merging --headers-json."""
    raw_text = load_text_file(args.raw_request_file).strip()
    if not raw_text:
        raise ValueError("raw request file is empty")

    base_url = args.base_url.strip() or None
    parsed = parse_raw_request(raw_text, base_url=base_url)
    return BaseRequest(
        method=parsed.method,
        url=parsed.url,
        headers=remove_content_length_header(dict(parsed.headers)),
        raw_body=parsed.raw_body,
    )


def build_base_request_from_target(
    fv: dict[str, Any],
    args: argparse.Namespace,
) -> BaseRequest:
    """Build BaseRequest from http-target.json fields (target-only mode, no raw file)."""
    url_raw = fv.get("url")
    if not isinstance(url_raw, str) or not url_raw.strip():
        raise ValueError(
            "target file: url is required when no --raw-request-file is provided"
        )

    base_url = pick_str(args.base_url, fv.get("base_url"), "")
    headers: dict[str, str] = {}
    if isinstance(fv.get("headers"), dict):
        headers = {str(k): str(v) for k, v in fv["headers"].items()}
    extra_headers = parse_headers_json(args.headers_json)
    if extra_headers:
        headers.update(extra_headers)

    method = infer_http_method(fv)
    path_or_url = url_raw.strip()
    url = resolve_request_url(path_or_url, headers=headers, base_url=base_url or None)
    return BaseRequest(
        method=method,
        url=url,
        headers=remove_content_length_header(headers),
        raw_body=None,
    )


@dataclass(frozen=True)
class MergedRunOptions:
    """Runtime options after merging CLI with optional target file."""

    threads: int
    interval_seconds: float
    timeout_seconds: float
    progress_every: int
    verify_tls: bool
    pause_on_success: bool
    fail_if_body_contains: list[str]


def merge_run_options(
    args: argparse.Namespace, fv: dict[str, Any] | None
) -> MergedRunOptions:
    """Merge --target-file JSON with CLI; CLI wins when the corresponding flag is present."""
    threads = args.threads
    interval_seconds = args.interval_seconds
    timeout_seconds = args.timeout_seconds
    progress_every = args.progress_every

    if fv:
        if not cli_flag_provided("--threads"):
            t = json_int(fv.get("threads"))
            if t is not None:
                threads = t
        if not cli_flag_provided("--interval-seconds"):
            v = json_float(fv.get("interval_seconds"))
            if v is not None:
                interval_seconds = v
        if not cli_flag_provided("--timeout-seconds"):
            v = json_float(fv.get("timeout_seconds"))
            if v is not None:
                timeout_seconds = v
        if not cli_flag_provided("--progress-every"):
            p = json_int(fv.get("progress_every"))
            if p is not None:
                progress_every = p

    verify_tls = bool(args.verify_tls)
    if fv:
        verify_tls = verify_tls or bool(fv.get("verify_tls", False))

    if cli_flag_provided("--pause-on-success"):
        pause_on_success = bool(args.pause_on_success)
    elif fv:
        pause_on_success = bool(fv.get("pause_on_success", False))
    else:
        pause_on_success = bool(args.pause_on_success)

    markers = list(args.fail_if_body_contains or [])
    if fv and isinstance(fv.get("fail_if_body_contains"), list):
        for item in fv["fail_if_body_contains"]:
            if isinstance(item, str) and item.strip():
                markers.append(item.strip())

    return MergedRunOptions(
        threads=threads,
        interval_seconds=interval_seconds,
        timeout_seconds=timeout_seconds,
        progress_every=progress_every,
        verify_tls=verify_tls,
        pause_on_success=pause_on_success,
        fail_if_body_contains=markers,
    )


def parse_headers_json(raw_headers_json: str) -> dict[str, str] | None:
    """Parse optional headers JSON string."""
    if not raw_headers_json.strip():
        return None
    parsed = parse_json_object(raw_headers_json)
    return {str(key): str(value) for key, value in parsed.items()}


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


def remove_content_length_header(headers: dict[str, str]) -> dict[str, str]:
    """Drop Content-Length header to avoid stale values after body changes."""
    sanitized: dict[str, str] = {}
    for key, value in headers.items():
        if key.lower() == "content-length":
            continue
        sanitized[key] = value
    return sanitized


def parse_batch_payload_source(body_json: str, body_file: str) -> dict[str, Any]:
    """Parse batch payload template from --body-json or --body-file."""
    has_body_json = bool(body_json.strip())
    has_body_file = bool(body_file.strip())

    if has_body_json and has_body_file:
        raise ValueError("use either --body-json or --body-file, not both")
    if not has_body_json and not has_body_file:
        raise ValueError("batch mode requires --body-json or --body-file")

    if has_body_json:
        return parse_json_object(body_json)

    file_text = load_text_file(body_file)
    return parse_json_object(file_text)


def validate_batch_template_fields(
    payload_template: dict[str, Any],
    username_field: str,
    password_field: str,
) -> None:
    """Validate required username/password fields in batch template."""
    if username_field not in payload_template:
        raise ValueError(
            f"batch payload template must include username field '{username_field}'"
        )
    if password_field not in payload_template:
        raise ValueError(
            f"batch payload template must include password field '{password_field}'"
        )


def build_batch_spec(
    args: argparse.Namespace, accounts: list[Account]
) -> BatchSpec | None:
    """Build batch spec when account inputs are provided."""
    if not accounts:
        return None

    username_field = args.account_field_username.strip()
    password_field = args.account_field_password.strip()
    if not username_field:
        raise ValueError("--account-field-username cannot be empty")
    if not password_field:
        raise ValueError("--account-field-password cannot be empty")

    payload_template = parse_batch_payload_source(args.body_json, args.body_file)
    validate_batch_template_fields(payload_template, username_field, password_field)

    return BatchSpec(
        payload_template=payload_template,
        username_field=username_field,
        password_field=password_field,
    )


def build_payload_for_account(
    template: dict[str, Any], spec: BatchSpec, account: Account
) -> dict[str, Any]:
    """Build one payload from template and account pair."""
    payload = dict(template)
    payload[spec.username_field] = account.username
    payload[spec.password_field] = account.password
    return payload


def send_raw_once(
    session: requests.Session,
    base_request: BaseRequest,
    *,
    timeout_seconds: float,
    verify_tls: bool,
) -> requests.Response:
    """Send one request exactly as parsed from raw request file."""
    return session.request(
        base_request.method,
        base_request.url,
        headers=base_request.headers,
        data=base_request.raw_body,
        timeout=timeout_seconds,
        verify=verify_tls,
    )


def header_is_form_urlencoded(headers: dict[str, str]) -> bool:
    """True when Content-Type is application/x-www-form-urlencoded (Burp form login)."""
    ct = get_header_value(headers, "Content-Type") or ""
    return "application/x-www-form-urlencoded" in ct.lower()


def send_batch_one(
    session: requests.Session,
    base_request: BaseRequest,
    payload: dict[str, Any],
    *,
    timeout_seconds: float,
    verify_tls: bool,
) -> requests.Response:
    """Send one batch request with payload and raw-derived method/url/headers."""
    method = base_request.method.upper()
    headers = dict(base_request.headers)
    headers = remove_content_length_header(headers)

    if method == "GET":
        return session.request(
            method,
            base_request.url,
            headers=headers,
            params=payload,
            timeout=timeout_seconds,
            verify=verify_tls,
        )

    if header_is_form_urlencoded(headers):
        form_data = {str(key): str(value) for key, value in payload.items()}
        return session.request(
            method,
            base_request.url,
            headers=headers,
            data=form_data,
            timeout=timeout_seconds,
            verify=verify_tls,
        )

    headers["Content-Type"] = "application/json"
    return session.request(
        method,
        base_request.url,
        headers=headers,
        json=payload,
        timeout=timeout_seconds,
        verify=verify_tls,
    )


def response_body_matches_failure_markers(body: str, markers: list[str]) -> bool:
    """Return True if body contains any non-empty failure marker substring."""
    cleaned = [m for m in markers if m]
    if not cleaned:
        return False
    return any(marker in body for marker in cleaned)


def response_to_result(
    response: requests.Response,
    *,
    requested_at: str,
    username: str,
    password: str,
    fail_if_body_contains: list[str] | None = None,
) -> SendResult:
    """Convert response to printable SendResult."""
    markers = fail_if_body_contains or []
    body_text = response.text or ""
    http_ok = response.ok
    ok = http_ok
    if http_ok and response_body_matches_failure_markers(body_text, markers):
        ok = False

    try:
        return SendResult(
            requested_at=requested_at,
            username=username,
            password=password,
            ok=ok,
            status_code=response.status_code,
            json_data=response.json(),
            text=None,
            error=None,
        )
    except Exception:
        return SendResult(
            requested_at=requested_at,
            username=username,
            password=password,
            ok=ok,
            status_code=response.status_code,
            json_data=None,
            text=response.text,
            error=None,
        )


def to_single_line_preview(result: SendResult, max_length: int = 120) -> str:
    """Convert response content to a single-line preview."""
    if result.error is not None:
        preview = f"error: {result.error}"
    elif result.json_data is not None:
        preview = json.dumps(
            result.json_data, ensure_ascii=False, separators=(",", ":")
        )
    else:
        preview = result.text or ""

    normalized = " ".join(preview.split())
    if len(normalized) <= max_length:
        return normalized
    return normalized[: max_length - 3] + "..."


def print_run_summary(results: list[SendResult]) -> None:
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
    Ask whether to keep trying after a successful response.

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
    result: SendResult,
    *,
    user_pos: tuple[int, int] | None = None,
    pass_pos: tuple[int, int] | None = None,
) -> None:
    """Print one result line in real time."""
    status = result.status_code if result.status_code is not None else "-"
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
            CLIStyle.color(f"http={status}", status_color),
            CLIStyle.color("response=", CLIStyle.COLORS["SUB_TITLE"])
            + CLIStyle.color(preview, status_color),
        ]
    )
    print(" ".join(parts))


def execute_requests(
    base_request: BaseRequest,
    *,
    accounts: list[Account],
    batch_spec: BatchSpec | None,
    interval_seconds: float,
    threads: int,
    timeout_seconds: float,
    verify_tls: bool,
    progress_every: int,
    users_list: list[str] | None = None,
    passwords_list: list[str] | None = None,
    show_user_file_indices: bool = False,
    show_password_file_indices: bool = False,
    pause_on_success: bool = False,
    fail_if_body_contains: list[str] | None = None,
) -> list[SendResult]:
    """Execute one request or batch requests with optional threading."""
    if pause_on_success and threads > 1:
        output_line(
            "Warning: --pause-on-success uses sequential tries only; forcing threads=1.",
            CLIStyle.COLORS["WARNING"],
        )
        threads = 1

    is_batch = batch_spec is not None

    debug(f"method={base_request.method} url={base_request.url}", enabled=DEBUG_MODE)
    debug(f"batch_mode={is_batch}", enabled=DEBUG_MODE)
    debug(f"threads={threads} interval_seconds={interval_seconds}", enabled=DEBUG_MODE)
    debug(f"verify_tls={verify_tls}", enabled=DEBUG_MODE)
    if fail_if_body_contains:
        debug(
            f"fail_if_body_contains={fail_if_body_contains!r}",
            enabled=DEBUG_MODE,
        )

    cookie_value = get_header_value(base_request.headers, "Cookie")
    if cookie_value:
        debug(f"cookie={cookie_value}", enabled=DEBUG_MODE)

    session_local = local()
    sessions_lock = Lock()
    created_sessions: list[requests.Session] = []

    def get_session() -> requests.Session:
        existing = getattr(session_local, "session", None)
        if existing is not None:
            return existing

        session = requests.Session()
        session_local.session = session
        with sessions_lock:
            created_sessions.append(session)
        return session

    items: list[Account | None] = accounts if is_batch else [None]
    total_items = len(items)
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
                CLIStyle.COLORS["SUB_TITLE"],
            )

    def run_one(item: Account | None) -> SendResult:
        requested_at = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        username = item.username if item is not None else "-"
        password = item.password if item is not None else "-"
        try:
            session = get_session()
            if not is_batch or item is None or batch_spec is None:
                response = send_raw_once(
                    session,
                    base_request,
                    timeout_seconds=timeout_seconds,
                    verify_tls=verify_tls,
                )
                return response_to_result(
                    response,
                    requested_at=requested_at,
                    username=username,
                    password=password,
                    fail_if_body_contains=fail_if_body_contains,
                )

            payload = build_payload_for_account(
                batch_spec.payload_template, batch_spec, item
            )
            response = send_batch_one(
                session,
                base_request,
                payload,
                timeout_seconds=timeout_seconds,
                verify_tls=verify_tls,
            )
            return response_to_result(
                response,
                requested_at=requested_at,
                username=username,
                password=password,
                fail_if_body_contains=fail_if_body_contains,
            )
        except (ValueError, requests.RequestException) as error:
            return SendResult(
                requested_at=requested_at,
                username=username,
                password=password,
                ok=False,
                status_code=None,
                json_data=None,
                text=None,
                error=str(error),
            )

    def position_for(
        item: Account | None,
    ) -> tuple[tuple[int, int] | None, tuple[int, int] | None]:
        if item is None:
            return None, None
        return account_file_positions(
            item,
            users_list or [],
            passwords_list or [],
            show_user_file=show_user_file_indices,
            show_password_file=show_password_file_indices,
        )

    def run_one_capture(item: Account | None) -> tuple[Account | None, SendResult]:
        return item, run_one(item)

    results: list[SendResult] = []
    try:
        if threads <= 1:
            for index, item in enumerate(items):
                if index > 0 and interval_seconds > 0:
                    time.sleep(interval_seconds)
                result = run_one(item)
                u_pos, p_pos = position_for(item)
                print_result_line(result, user_pos=u_pos, pass_pos=p_pos)
                results.append(result)
                mark_progress()
                if (
                    pause_on_success
                    and result.ok
                    and not prompt_continue_after_success()
                ):
                    break
            print_run_summary(results)
            return results

        executor = ThreadPoolExecutor(max_workers=threads)
        try:
            futures = []
            for index, item in enumerate(items):
                if index > 0 and interval_seconds > 0:
                    time.sleep(interval_seconds)
                futures.append(executor.submit(run_one_capture, item))
            for future in as_completed(futures):
                item, result = future.result()
                u_pos, p_pos = position_for(item)
                print_result_line(result, user_pos=u_pos, pass_pos=p_pos)
                results.append(result)
                mark_progress()
            print_run_summary(results)
            return results
        except KeyboardInterrupt:
            executor.shutdown(wait=False, cancel_futures=True)
            os._exit(130)
        finally:
            executor.shutdown(wait=True)
    finally:
        with sessions_lock:
            sessions = list(created_sessions)
            created_sessions.clear()
        for session in sessions:
            try:
                session.close()
            except Exception:
                continue


def print_results(results: list[SendResult]) -> int:
    """Return process exit code from results."""
    failed_count = 0
    for result in results:
        if not result.ok:
            failed_count += 1

    if failed_count > 0:
        return 1
    return 0


def build_parser() -> argparse.ArgumentParser:
    """Build CLI parser."""
    script_name = "python brute-http-login.py"
    examples = [
        (
            "Connectivity check mode",
            "--raw-request-file /path/to/bp-copy.txt",
        ),
        (
            "Batch mode with file lists",
            "--raw-request-file /path/to/bp-copy.txt --users users.txt "
            "--passwords passwords.txt --body-file payload.json",
        ),
        (
            "Batch mode with inline body JSON",
            "--raw-request-file /path/to/bp-copy.txt --user admin --password 123456 "
            '--body-json \'{"username":"admin","password":"123456"}\'',
        ),
        (
            "Batch with Burp raw + http-target.json (URL/Host from raw, body from JSON)",
            "--raw-request-file bp.txt --target-file http-target.json --users users.txt "
            "--passwords passwords.txt",
        ),
        (
            "Treat 200 + login page HTML as failure",
            "--raw-request-file /path/to/bp-copy.txt --user admin --passwords pass.txt "
            "--body-file payload.json --fail-if-body-contains InvalidLogin",
        ),
    ]
    notes = [
        "Provide either --user or --users, and either --password or --passwords.",
        "Use --raw-request-file (Burp), --target-file (JSON), or both. With both: request URL "
        "and Host come from the raw file (highest priority); target JSON headers and "
        "--headers-json apply first, then raw headers overwrite. Batch body/params template: "
        "target JSON wins over raw body; if omitted in JSON, use --body-json/--body-file or "
        "a JSON object in the raw body.",
        "Target-only mode needs url in JSON. With --raw-request-file, url may be omitted in JSON.",
        "Target JSON body object implies POST, params object implies GET when method is omitted.",
        "POST batch: Content-Type application/json uses JSON body; "
        "application/x-www-form-urlencoded (e.g. from Burp) uses form-encoded body.",
        "Use --account-field-username and --account-field-password to rename keys.",
        "End of run prints a summary; --pause-on-success stops after each success until you confirm.",
        "When the server returns HTTP 2xx but redirects to a generic page, use "
        "--fail-if-body-contains so attempts matching that page count as failed.",
    ]
    epilog = create_example_text(script_name, examples, notes=notes)

    parser = ColoredArgumentParser(
        description="Send raw request once, or run batch requests with username/password lists.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=epilog,
    )

    parser.add_argument(
        "--raw-request-file",
        type=str,
        default="",
        help=(
            "Raw HTTP request from Burp Suite. With --target-file, URL/Host come from here first."
        ),
    )
    parser.add_argument(
        "--target-file",
        type=str,
        default="",
        help=(
            "JSON target (optional url): headers, body/params template, account_field_*, options. "
            "Combine with --raw-request-file to merge (Burp + JSON)."
        ),
    )
    parser.add_argument(
        "--base-url",
        type=str,
        default="",
        help="Optional base URL when request line or target url is a relative path.",
    )
    parser.add_argument(
        "--headers-json",
        type=str,
        default="",
        help='Extra headers as JSON object, e.g. {"Authorization":"Bearer ..."}.',
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
        "--body-json",
        type=str,
        default="",
        help="Batch payload template as JSON object string.",
    )
    parser.add_argument(
        "--body-file",
        type=str,
        default="",
        help="Batch payload template file path (JSON object).",
    )
    parser.add_argument(
        "--account-field-username",
        type=str,
        default=DEFAULT_USERNAME_FIELD,
        help="Username field key in batch JSON template.",
    )
    parser.add_argument(
        "--account-field-password",
        type=str,
        default=DEFAULT_PASSWORD_FIELD,
        help="Password field key in batch JSON template.",
    )

    parser.add_argument(
        "--interval-seconds",
        type=float,
        default=DEFAULT_INTERVAL_SECONDS,
        help="Seconds between request submissions.",
    )
    parser.add_argument(
        "--threads", type=int, default=DEFAULT_THREADS, help="Concurrent thread count."
    )
    parser.add_argument(
        "--timeout-seconds",
        type=float,
        default=DEFAULT_TIMEOUT_SECONDS,
        help="Request timeout in seconds.",
    )
    parser.add_argument(
        "--progress-every",
        type=int,
        default=DEFAULT_PROGRESS_EVERY,
        help="Print progress every N completed requests (default: 1000, use 0 to disable).",
    )
    parser.add_argument(
        "--verify-tls",
        action="store_true",
        default=DEFAULT_VERIFY_TLS,
        help="Enable TLS certificate verification. Default is disabled.",
    )
    parser.add_argument(
        "--pause-on-success",
        action="store_true",
        help=(
            "After a successful response (HTTP ok), prompt to continue (Y) or stop (n). "
            "Forces sequential mode (threads=1)."
        ),
    )
    parser.add_argument(
        "--fail-if-body-contains",
        action="append",
        dest="fail_if_body_contains",
        metavar="SUBSTRING",
        help=(
            "If the response body contains this substring while HTTP status is still successful "
            "(2xx), treat the attempt as failed. Useful when failures look like 200 + login page. "
            "Repeatable; any substring match marks failure."
        ),
    )
    parser.add_argument("--log", action="store_true", help="Enable debug output.")

    return parser


def build_base_request_from_raw(args: argparse.Namespace) -> BaseRequest:
    """Build base request from raw file; --headers-json overlays raw headers (CLI wins on duplicate keys)."""
    raw = load_raw_base_request(args)
    merged_headers = dict(raw.headers)
    headers_json = parse_headers_json(args.headers_json)
    if headers_json:
        merged_headers.update(headers_json)
    return BaseRequest(
        method=raw.method,
        url=raw.url,
        headers=remove_content_length_header(merged_headers),
        raw_body=raw.raw_body,
    )


def main() -> int:
    """Main program logic."""
    parser = build_parser()
    args = parser.parse_args()

    global DEBUG_MODE
    DEBUG_MODE = bool(args.log)

    has_raw = bool(args.raw_request_file.strip())
    has_target = bool(args.target_file.strip())
    if not has_raw and not has_target:
        output_line(
            "Error: provide --raw-request-file and/or --target-file",
            CLIStyle.COLORS["ERROR"],
        )
        return 2

    try:
        target_data: dict[str, Any] | None = None
        if has_target:
            target_data = parse_http_target_file(args.target_file.strip())

        if (
            has_target
            and target_data is not None
            and target_has_body_or_params(target_data)
            and (args.body_json.strip() or args.body_file.strip())
        ):
            raise ValueError(
                "omit --body-json/--body-file when target JSON defines body or params"
            )

        if has_target and target_data is not None:
            args.account_field_username = pick_str(
                args.account_field_username,
                target_data.get("account_field_username"),
                DEFAULT_USERNAME_FIELD,
            )
            args.account_field_password = pick_str(
                args.account_field_password,
                target_data.get("account_field_password"),
                DEFAULT_PASSWORD_FIELD,
            )

        raw_base_for_merge: BaseRequest | None = None
        if has_raw and has_target and target_data is not None:
            raw_base_for_merge = load_raw_base_request(args)
            base_request = merge_raw_and_target(raw_base_for_merge, target_data, args)
        elif has_target and target_data is not None:
            base_request = build_base_request_from_target(target_data, args)
        else:
            base_request = build_base_request_from_raw(args)

        run_opts = merge_run_options(args, target_data)

        if not run_opts.verify_tls:
            urllib3.disable_warnings(InsecureRequestWarning)

        accounts, users_list, passwords_list = build_accounts_from_cli(
            user_value=args.user,
            users_file=args.users,
            password_value=args.password,
            passwords_file=args.passwords,
        )

        if accounts and has_target and target_data is not None:
            if has_raw:
                resolve_batch_payload_args(
                    args,
                    target_data,
                    raw_base_for_merge,
                    base_request,
                )
            else:
                resolve_batch_payload_args(args, target_data, None, base_request)

        batch_spec = build_batch_spec(args, accounts)

        if not accounts and (args.body_json.strip() or args.body_file.strip()):
            raise ValueError(
                "--body-json/--body-file is only used in batch mode; "
                "provide user/password inputs to enable batch mode"
            )

        show_user_file_indices = bool(args.users.strip())
        show_password_file_indices = bool(args.passwords.strip())
        results = execute_requests(
            base_request,
            accounts=accounts,
            batch_spec=batch_spec,
            interval_seconds=run_opts.interval_seconds,
            threads=run_opts.threads,
            timeout_seconds=run_opts.timeout_seconds,
            verify_tls=run_opts.verify_tls,
            progress_every=run_opts.progress_every,
            users_list=users_list,
            passwords_list=passwords_list,
            show_user_file_indices=show_user_file_indices,
            show_password_file_indices=show_password_file_indices,
            pause_on_success=run_opts.pause_on_success,
            fail_if_body_contains=run_opts.fail_if_body_contains,
        )
        return print_results(results)
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
