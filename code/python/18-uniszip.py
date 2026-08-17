#!/usr/bin/env python3
# refer to article: [一款可分享密码的解压缩 app 分析学习](https://bbs.kanxue.com/thread-291970.htm)
# pip install requests pycryptodome


import argparse
import base64
import binascii
import hashlib
import hmac
import json
import os
import sys
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

import requests
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

DEBUG_MODE = False

REGION = "CN"
PACKAGE_NAME = "com.fileunzip.zxwknight"
VERSION_NAME = "3.2.23"
APP_ID = "zipa"
PLATFORM = "android"
CTX_VALUE = 516622220

QUERY_URL = "https://file.unisapps.com/api/v3/search/info"
SUBMIT_URL = "https://file.unisapps.com/api/v3/sync/ads"

ACCESS_KEY = b"gwFG#9P!ad+*PMUnisapps$Rs#L!_1G9"
AES_KEY = b"EyR2JvBXJXaUdY9auxetvhpEeQ8DmC6L"
REQUEST_TIMEOUT = 20
MD5_CHUNK_SIZE = 1024 * 1024


class CLIStyle:
    """Define semantic colors for command-line output."""

    COLORS = {
        "TITLE": 7,
        "SUB_TITLE": 2,
        "CONTENT": 3,
        "EXAMPLE": 7,
        "WARNING": 4,
        "ERROR": 2,
    }

    @staticmethod
    def color(text: str = "", color: int = 3) -> str:
        """Return text wrapped in the requested terminal color."""
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
        return color_table.get(color, color_table[0]).format(text)


class ColoredArgumentParser(argparse.ArgumentParser):
    """Apply semantic colors to argparse usage and help text."""

    def _format_action_invocation(self, action: argparse.Action) -> str:
        if not action.option_strings:
            (metavar,) = self._metavar_formatter(action, action.dest)(1)
            return CLIStyle.color(metavar, CLIStyle.COLORS["SUB_TITLE"])

        if action.nargs == 0:
            return ", ".join(
                CLIStyle.color(option, CLIStyle.COLORS["SUB_TITLE"])
                for option in action.option_strings
            )

        args_string = self._format_args(action, action.dest.upper())
        colored_args = CLIStyle.color(args_string, CLIStyle.COLORS["CONTENT"])
        return ", ".join(
            CLIStyle.color(option, CLIStyle.COLORS["SUB_TITLE"])
            + f" {colored_args}"
            for option in action.option_strings
        )

    def _format_action(self, action: argparse.Action) -> str:
        original_help = action.help
        if original_help not in (None, argparse.SUPPRESS):
            action.help = CLIStyle.color(original_help, CLIStyle.COLORS["CONTENT"])
        try:
            return super()._format_action(action)
        finally:
            action.help = original_help

    def format_help(self) -> str:
        """Render help with colored descriptions and section titles."""
        formatter = self._get_formatter()
        if self.description:
            formatter.add_text(
                CLIStyle.color(self.description, CLIStyle.COLORS["TITLE"])
            )
        formatter.add_usage(
            self.usage,
            self._actions,
            self._mutually_exclusive_groups,
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


def create_example_text(
    script_name: str,
    examples: list[tuple[str, str]],
    notes: list[str] | None = None,
) -> str:
    """Build the structured, colorized help epilog."""
    text = f"\n{CLIStyle.color('Examples:', CLIStyle.COLORS['SUB_TITLE'])}"
    for description, command in examples:
        text += (
            f"\n  {CLIStyle.color(f'# {description}', CLIStyle.COLORS['EXAMPLE'])}"
            f"\n  {CLIStyle.color(f'{script_name} {command}', CLIStyle.COLORS['CONTENT'])}\n"
        )
    if notes:
        text += f"\n{CLIStyle.color('Notes:', CLIStyle.COLORS['SUB_TITLE'])}"
        for note in notes:
            text += f"\n  {CLIStyle.color(f'- {note}', CLIStyle.COLORS['CONTENT'])}"
    return text


@dataclass(frozen=True)
class ArchiveMetadata:
    """Store the archive fields shared by submit and query requests."""

    file_name: str
    file_size: int
    md5: str

    @classmethod
    def from_path(
        cls,
        file_path: Path,
        file_name: str | None = None,
    ) -> "ArchiveMetadata":
        """Read local archive metadata with an optional service filename."""
        if not file_path.is_file():
            raise FileNotFoundError(f"file not found: {file_path}")

        return cls(
            file_name=file_name if file_name is not None else file_path.name,
            file_size=file_path.stat().st_size,
            md5=file_md5(file_path),
        )


def file_md5(file_path: Path) -> str:
    """Calculate an archive MD5 digest without loading it into memory."""
    digest = hashlib.md5()
    with file_path.open("rb") as file_handle:
        for chunk in iter(
            lambda: file_handle.read(MD5_CHUNK_SIZE),
            b"",
        ):
            digest.update(chunk)
    return digest.hexdigest()


def build_user_client_access(file_name: str, file_size: int) -> str:
    """Build the HMAC-based access header used by the query endpoint."""
    tail = 2 * ((CTX_VALUE >> 2) - 169) + 127
    message = f"{CTX_VALUE}{PACKAGE_NAME}{file_name}{file_size}{tail}"
    digest = hmac.new(
        ACCESS_KEY,
        message.encode("utf-8"),
        hashlib.sha1,
    ).digest()
    return base64.b64encode(digest).decode("ascii")


def encrypt_json(payload: Mapping[str, object]) -> str:
    """Serialize and encrypt a request payload with AES-CBC and PKCS#7."""
    plaintext = json.dumps(
        dict(payload),
        ensure_ascii=False,
        separators=(",", ":"),
    ).encode("utf-8")
    iv = os.urandom(AES.block_size)
    cipher = AES.new(AES_KEY, AES.MODE_CBC, iv)
    ciphertext = cipher.encrypt(pad(plaintext, AES.block_size))
    envelope = {
        "data": base64.b64encode(ciphertext).decode("ascii"),
        "iv": base64.b64encode(iv).decode("ascii"),
    }
    return json.dumps(envelope, ensure_ascii=False, separators=(",", ":"))


def try_decrypt_response(response_text: str) -> str | None:
    """Decrypt a response envelope, returning None for non-encrypted data."""
    try:
        envelope: Any = json.loads(response_text)
        if not isinstance(envelope, dict):
            return None

        encoded_data = envelope.get("data")
        encoded_iv = envelope.get("iv")
        if not isinstance(encoded_data, str) or not isinstance(encoded_iv, str):
            return None

        ciphertext = base64.b64decode(encoded_data, validate=True)
        iv = base64.b64decode(encoded_iv, validate=True)
        if (
            len(iv) != AES.block_size
            or not ciphertext
            or len(ciphertext) % AES.block_size != 0
        ):
            return None

        cipher = AES.new(AES_KEY, AES.MODE_CBC, iv)
        plaintext = unpad(cipher.decrypt(ciphertext), AES.block_size)
        return plaintext.decode("utf-8", errors="replace")
    except (binascii.Error, TypeError, ValueError):
        return None


def extract_password(decrypted_response: str) -> str | None:
    """Extract the password field from a decrypted response object."""
    try:
        payload: Any = json.loads(decrypted_response)
    except (TypeError, ValueError):
        return None

    if not isinstance(payload, dict):
        return None

    password = payload.get("pd")
    return password if isinstance(password, str) else None


def build_headers(user_client_access: str | None = None) -> dict[str, str]:
    """Build common request headers and an optional query access header."""
    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "appid": APP_ID,
        "version": VERSION_NAME,
        "platform": PLATFORM,
    }
    if user_client_access is not None:
        headers["User-Client-Access"] = user_client_access
    return headers


class UnisappsClient:
    """Send encrypted archive metadata to the two service endpoints."""

    def __init__(self, session: requests.Session) -> None:
        """Initialize the client with an injectable requests session."""
        self._session = session

    def submit_password(
        self,
        archive: ArchiveMetadata,
        password: str,
    ) -> requests.Response:
        """Submit a password associated with an archive."""
        payload = {
            "fileName": archive.file_name,
            "fileSize": archive.file_size,
            "pd": password,
            "region": REGION,
            "md5": archive.md5,
        }
        return self._post(SUBMIT_URL, payload, build_headers())

    def query_password(self, archive: ArchiveMetadata) -> requests.Response:
        """Query the service for a password associated with an archive."""
        access_header = build_user_client_access(
            archive.file_name,
            archive.file_size,
        )
        payload = {
            "fileName": archive.file_name,
            "fileSize": archive.file_size,
            "md5": archive.md5,
        }
        return self._post(
            QUERY_URL,
            payload,
            build_headers(access_header),
        )

    def _post(
        self,
        url: str,
        payload: Mapping[str, object],
        headers: Mapping[str, str],
    ) -> requests.Response:
        """Encrypt and send one API request."""
        request_body = encrypt_json(payload).encode("utf-8")
        debug(f"POST {url}")
        return self._session.post(
            url,
            data=request_body,
            headers=dict(headers),
            timeout=REQUEST_TIMEOUT,
        )


def debug(message: str) -> None:
    """Print a diagnostic message when debug mode is enabled."""
    if DEBUG_MODE:
        print(
            CLIStyle.color(
                f"[debug] {message}",
                CLIStyle.COLORS["WARNING"],
            ),
            file=sys.stderr,
        )


def emit(label: str, value: object, color: int = 3) -> None:
    """Print one colorized key-value line."""
    print(CLIStyle.color(f"{label} = {value}", color))


def emit_response(action: str, response: requests.Response) -> None:
    """Print the HTTP status and raw response body."""
    emit(
        f"[{action}] status",
        response.status_code,
        CLIStyle.COLORS["TITLE"],
    )
    emit(f"[{action}] body", response.text, CLIStyle.COLORS["CONTENT"])


def print_error(message: str) -> None:
    """Print one colorized error message to stderr."""
    print(
        CLIStyle.color(
            f"Error: {message}",
            CLIStyle.COLORS["ERROR"],
        ),
        file=sys.stderr,
    )


def create_parser(script_name: str) -> ColoredArgumentParser:
    """Create the submit/query command-line parser."""
    parser = ColoredArgumentParser(
        prog=script_name,
        description="Minimal encrypted archive password submit/query client.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=create_example_text(
            script_name,
            [
                ("Submit a password", 'submit "a.zip" "123456"'),
                (
                    "Query with a service filename",
                    'query "local.zip" --file-name "remote.zip"',
                ),
            ],
            [
                "Place --log before the subcommand to enable diagnostics.",
                "The password is sent only for the submit operation.",
                "Query uses the local archive path, its computed fileSize and md5, and the server's original fileName.",
                "Use --file-name to supply the server's fileName for lookup and request signing; otherwise the local filename is used.",
            ],
        ),
    )
    parser.add_argument(
        "--log",
        action="store_true",
        help="Enable diagnostic logging.",
    )
    subparsers = parser.add_subparsers(
        dest="action",
        required=True,
        title="Commands",
        metavar="{submit,query}",
        parser_class=ColoredArgumentParser,
    )

    submit_parser = subparsers.add_parser(
        "submit",
        description="Submit one archive password.",
        help="Submit one archive password.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=create_example_text(
            script_name,
            [("Submit a password", 'submit "a.zip" "123456"')],
        ),
    )
    submit_parser.add_argument(
        "path",
        metavar="ARCHIVE",
        help="Path to the local archive.",
    )
    submit_parser.add_argument(
        "password",
        metavar="PASSWORD",
        help="Password to submit.",
    )
    submit_parser.add_argument(
        "--file-name",
        dest="file_name",
        metavar="NAME",
        help="Filename sent to the service; defaults to the local filename.",
    )

    query_parser = subparsers.add_parser(
        "query",
        description="Query by the service fileName, fileSize, and md5.",
        help="Query one archive password.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=create_example_text(
            script_name,
            [
                (
                    "Query with a service filename",
                    'query "local.zip" --file-name "remote.zip"',
                )
            ],
            [
                "Query uses the local archive path, its computed fileSize and md5, and the server's original fileName.",
                "Use --file-name to supply the server's fileName for lookup and request signing; otherwise the local filename is used.",
            ],
        ),
    )
    query_parser.add_argument(
        "path",
        metavar="ARCHIVE",
        help="Local archive path; fileSize and md5 are computed from it.",
    )
    query_parser.add_argument(
        "--file-name",
        dest="file_name",
        metavar="NAME",
        help="Server's original fileName for lookup and request signing; it does not rename the local file.",
    )
    return parser


def parse_args(arguments: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments."""
    script_name = Path(sys.argv[0]).name
    return create_parser(script_name).parse_args(arguments)


def main() -> int:
    """Run the selected archive password operation."""
    global DEBUG_MODE

    args = parse_args()
    DEBUG_MODE = args.log
    try:
        archive = ArchiveMetadata.from_path(Path(args.path), args.file_name)
        emit("fileName", archive.file_name, CLIStyle.COLORS["TITLE"])
        emit("fileSize", archive.file_size)
        emit("md5", archive.md5)

        with requests.Session() as session:
            client = UnisappsClient(session)
            if args.action == "submit":
                response = client.submit_password(archive, args.password)
                emit_response("submit", response)
            else:
                response = client.query_password(archive)
                emit_response("query", response)
                decrypted = try_decrypt_response(response.text)
                if decrypted is not None:
                    emit("[query] decrypted", decrypted, CLIStyle.COLORS["TITLE"])
                    password = extract_password(decrypted)
                    if password is not None:
                        emit("[query] password", password, CLIStyle.COLORS["TITLE"])
        return 0
    except FileNotFoundError as error:
        print_error(str(error))
        return 1
    except requests.RequestException as error:
        if DEBUG_MODE:
            traceback.print_exc()
        print_error(f"request failed: {error}")
        return 1
    except Exception as error:
        if DEBUG_MODE:
            traceback.print_exc()
        print_error(str(error))
        return 1


if __name__ == "__main__":
    sys.exit(main())
