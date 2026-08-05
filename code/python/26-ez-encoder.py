# -*- coding: utf-8 -*-
"""Encode, decode, and hash text or files from one command-line interface."""

import argparse
import base64
import binascii
import hashlib
import re
import sys
import traceback
from pathlib import Path
from typing import Sequence
from urllib.parse import quote_plus, unquote_plus


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
        """Return text wrapped in the configured ANSI color."""
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
    def color_bytes(data: bytes, color: int = COLORS["CONTENT"]) -> bytes:
        """Return bytes wrapped in ANSI color codes without changing their content."""
        prefix, suffix = CLIStyle.color("\x00", color).split("\x00")
        return prefix.encode("ascii") + data + suffix.encode("ascii")


class ColoredHelpFormatter(argparse.RawDescriptionHelpFormatter):
    """Help formatter with semantic colors for actions and descriptions."""

    def _format_action_invocation(self, action: argparse.Action) -> str:
        """Format an action using the shared CLI colors."""
        if not action.option_strings:
            metavar = self._metavar_formatter(action, action.dest)(1)[0]
            return CLIStyle.color(metavar, CLIStyle.COLORS["SUB_TITLE"])

        if action.nargs == 0:
            return ", ".join(
                CLIStyle.color(option, CLIStyle.COLORS["SUB_TITLE"])
                for option in action.option_strings
            )

        args_string = self._format_args(action, action.dest.upper())
        return ", ".join(
            CLIStyle.color(
                f"{option} {args_string}", CLIStyle.COLORS["SUB_TITLE"]
            )
            for option in action.option_strings
        )

    def _format_action(self, action: argparse.Action) -> str:
        """Color help descriptions that do not already contain ANSI codes."""
        original_help = action.help
        if original_help and "\033[" not in original_help:
            action.help = CLIStyle.color(original_help, CLIStyle.COLORS["CONTENT"])
        try:
            return super()._format_action(action)
        finally:
            action.help = original_help


class ColoredArgumentParser(argparse.ArgumentParser):
    """Argument parser with colorized headings and help sections."""

    def _colorize_usage_block(self, match: re.Match[str]) -> str:
        """Color command options and metavariables in one usage block."""
        usage_text = match.group(0)
        option_strings = sorted(
            {
                option
                for action in self._actions
                for option in action.option_strings
            },
            key=len,
            reverse=True,
        )
        for option in option_strings:
            pattern = re.compile(
                rf"(?<![A-Za-z0-9_-]){re.escape(option)}(?![A-Za-z0-9_-])"
            )
            usage_text = pattern.sub(
                CLIStyle.color(option, CLIStyle.COLORS["SUB_TITLE"]), usage_text
            )
        for metavar in ("FUNCTION", "TEXT", "PATH"):
            usage_text = re.sub(
                rf"(?<![A-Za-z0-9_]){metavar}(?![A-Za-z0-9_])",
                CLIStyle.color(metavar, CLIStyle.COLORS["SUB_TITLE"]),
                usage_text,
            )
        return usage_text

    def format_help(self) -> str:
        """Return help text with semantic color roles."""
        formatter = self._get_formatter()
        if self.description:
            formatter.add_text(CLIStyle.color(self.description, CLIStyle.COLORS["TITLE"]))
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
        help_text = formatter.format_help()
        usage_pattern = re.compile(r"(?m)^usage:.*(?:\n[ \t]+.*)*")
        return usage_pattern.sub(self._colorize_usage_block, help_text)


def create_example_text(
    script_name: str, examples: list[tuple[str, str]], notes: list[str] | None = None
) -> str:
    """Create a colorized examples block for parser help."""
    text = f"\n{CLIStyle.color('Examples:', CLIStyle.COLORS['SUB_TITLE'])}"
    for description, command in examples:
        text += f"\n  {CLIStyle.color(f'# {description}', CLIStyle.COLORS['EXAMPLE'])}"
        text += f"\n  {CLIStyle.color(f'{script_name} {command}', CLIStyle.COLORS['CONTENT'])}\n"
    if notes:
        text += f"\n{CLIStyle.color('Notes:', CLIStyle.COLORS['SUB_TITLE'])}"
        for note in notes:
            text += f"\n  {CLIStyle.color(f'- {note}', CLIStyle.COLORS['CONTENT'])}"
    return text


def read_input(value: str | None, file_path: str | None) -> bytes:
    """Read input bytes from a value, a file, or standard input."""
    if file_path:
        return Path(file_path).read_bytes()
    if value == "-":
        return sys.stdin.buffer.read()
    if value is None:
        raise ValueError("Provide TEXT, --file PATH, or '-' for standard input.")
    return value.encode("utf-8")


def decode_base64(data: bytes) -> bytes | None:
    """Return decoded Base64 bytes when data is canonical Base64, else None."""
    compact_data = b"".join(data.split())
    if not compact_data:
        return None
    padding = b"=" * (-len(compact_data) % 4)
    try:
        decoded_data = base64.b64decode(compact_data + padding, validate=True)
    except (binascii.Error, ValueError):
        return None
    if base64.b64encode(decoded_data).rstrip(b"=") != compact_data.rstrip(b"="):
        return None
    return decoded_data


def process_base64(data: bytes, direction: str) -> bytes:
    """Encode or decode Base64 data according to the selected direction."""
    decoded_data = decode_base64(data)
    if direction == "decode":
        if decoded_data is None:
            raise ValueError("Input is not valid Base64 data.")
        return decoded_data
    if direction == "auto" and decoded_data is not None and (
        b"=" in data or _is_utf8(decoded_data)
    ):
        return decoded_data
    return base64.b64encode(data)


def has_url_encoding(text: str) -> bool:
    """Return whether text contains percent-encoded URL data."""
    return bool(re.search(r"%(?:[0-9A-Fa-f]{2})", text))


def _is_utf8(data: bytes) -> bool:
    """Return whether data can be represented as UTF-8 text."""
    try:
        data.decode("utf-8")
    except UnicodeDecodeError:
        return False
    return True


def process_url(text: str, function: str, direction: str) -> str:
    """Encode or decode a URL component according to the selected direction."""
    should_decode = direction == "decode" or (
        direction == "auto" and has_url_encoding(text)
    )
    if function == "urlencode" and direction == "decode":
        raise ValueError("urlencode does not accept --decode; use urldecode instead.")
    if function == "urldecode" and direction == "encode":
        raise ValueError("urldecode does not accept --encode; use urlencode instead.")
    return unquote_plus(text) if should_decode else quote_plus(text)


def has_unicode_escape(text: str) -> bool:
    """Return whether text contains a supported Unicode escape sequence."""
    return bool(re.search(r"\\(?:u[0-9A-Fa-f]{4}|U[0-9A-Fa-f]{8})", text))


def encode_unicode(text: str) -> str:
    """Encode non-ASCII characters as Unicode escape sequences."""
    return text.encode("unicode_escape").decode("ascii")


def decode_unicode(text: str) -> str:
    """Decode Unicode escapes without changing ordinary non-ASCII characters."""
    pattern = re.compile(r"\\u([0-9A-Fa-f]{4})|\\U([0-9A-Fa-f]{8})")

    def replace_escape(match: re.Match[str]) -> str:
        """Convert one Unicode escape match to its character."""
        code_point = int(match.group(1) or match.group(2), 16)
        return chr(code_point)

    return pattern.sub(replace_escape, text)


def process_unicode(text: str, direction: str) -> str:
    """Encode or decode Unicode escapes according to the selected direction."""
    should_decode = direction == "decode" or (
        direction == "auto" and has_unicode_escape(text)
    )
    return decode_unicode(text) if should_decode else encode_unicode(text)


def calculate_hashes(data: bytes) -> str:
    """Return the requested digest values in a stable, readable format."""
    algorithms = ("md5", "sha1", "sha256", "sha512")
    return "\n".join(
        f"{algorithm.upper():<6}  {hashlib.new(algorithm, data).hexdigest()}"
        for algorithm in algorithms
    )


def colorize_hash_output(data: bytes) -> bytes:
    """Color hash labels, separators, and digest values independently."""
    colored_lines = []
    for line in data.decode("ascii").splitlines():
        algorithm, separator, digest = line[:6], line[6:8], line[8:]
        colored_lines.append(
            "".join(
                (
                    CLIStyle.color(algorithm, CLIStyle.COLORS["TITLE"]),
                    CLIStyle.color(separator, 1),
                    CLIStyle.color(digest, CLIStyle.COLORS["CONTENT"]),
                )
            )
        )
    return "\n".join(colored_lines).encode("ascii")


def write_output(
    data: bytes, output_path: str | None, plain: bool, is_hash: bool
) -> None:
    """Write raw file output or optionally colorized standard output."""
    if output_path:
        Path(output_path).write_bytes(data)
        message = f"Saved output to: {output_path}\n"
        sys.stdout.write(message if plain else CLIStyle.color(message, CLIStyle.COLORS["CONTENT"]))
        return
    if plain:
        output_data = data
    elif is_hash:
        output_data = colorize_hash_output(data)
    else:
        output_data = CLIStyle.color_bytes(data, CLIStyle.COLORS["CONTENT"])
    sys.stdout.buffer.write(output_data)


def add_input_arguments(parser: argparse.ArgumentParser) -> None:
    """Add common text and file input arguments to a subcommand parser."""
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "text",
        nargs="?",
        metavar="TEXT",
        help="Literal text, or '-' for standard input.",
    )
    input_group.add_argument(
        "-f",
        "--file",
        metavar="PATH",
        help="Read input bytes from a file.",
    )
    parser.add_argument(
        "-o",
        "--output",
        metavar="PATH",
        help="Write the result to a file.",
    )
    parser.add_argument(
        "-p",
        "--plain",
        action="store_true",
        help="Do not add ANSI colors to standard output.",
    )


def add_direction_arguments(parser: argparse.ArgumentParser) -> None:
    """Add explicit direction choices for automatic transformations."""
    direction_group = parser.add_mutually_exclusive_group()
    direction_group.add_argument(
        "--encode",
        action="store_const",
        const="encode",
        dest="direction",
        help="Force encoding.",
    )
    direction_group.add_argument(
        "--decode",
        action="store_const",
        const="decode",
        dest="direction",
        help="Force decoding.",
    )
    parser.set_defaults(direction="auto")


def create_parser() -> argparse.ArgumentParser:
    """Create the command-line parser and all supported subcommands."""
    script_name = Path(sys.argv[0]).name
    parser = ColoredArgumentParser(
        description="Universal encoder, decoder, and hash calculator.",
        formatter_class=ColoredHelpFormatter,
        epilog=create_example_text(
            script_name,
            [
                ("Encode text", "base64 'hello world'"),
                ("Hash a file", "hash --file archive.tar.gz"),
            ],
            ["Run FUNCTION --help to view command-specific options."],
        ),
    )
    parser.add_argument(
        "--log",
        action="store_true",
        help="Show tracebacks for unexpected errors.",
    )
    subparsers = parser.add_subparsers(
        dest="function",
        required=True,
        metavar="FUNCTION",
        parser_class=ColoredArgumentParser,
        title="Functions",
        description=CLIStyle.color("Available operations:", CLIStyle.COLORS["CONTENT"]),
    )

    for name, description, examples in (
        (
            "base64",
            "Automatically encode plain data or decode canonical Base64.",
            [("Encode text", "base64 'hello world'"), ("Decode to a file", "base64 SGVsbG8= -o hello.txt")],
        ),
        (
            "urlencode",
            "Encode text for a URL; auto-decodes percent-encoded input.",
            [("Encode a query", "urlencode 'name=Ada Lovelace'")],
        ),
        (
            "urldecode",
            "Decode percent-encoded text; auto-encodes ordinary input.",
            [("Decode a query", "urldecode 'name%3DAda+Lovelace'")],
        ),
        (
            "unicode",
            "Encode non-ASCII text or decode Unicode escape sequences.",
            [("Encode text", "unicode 'Hello, world'"), ("Decode escapes", r"unicode '\\u4f60\\u597d'")],
        ),
    ):
        command_parser = subparsers.add_parser(
            name,
            description=description,
            formatter_class=ColoredHelpFormatter,
            epilog=create_example_text(script_name, examples, ["Use --encode or --decode when input is ambiguous."]),
            help=CLIStyle.color(description, CLIStyle.COLORS["CONTENT"]),
        )
        add_input_arguments(command_parser)
        add_direction_arguments(command_parser)

    hash_parser = subparsers.add_parser(
        "hash",
        description="Calculate MD5, SHA-1, SHA-256, and SHA-512.",
        formatter_class=ColoredHelpFormatter,
        epilog=create_example_text(
            script_name,
            [("Hash text", "hash 'hello world'"), ("Hash a file", "hash --file archive.tar.gz")],
        ),
        help=CLIStyle.color(
            "Calculate MD5, SHA-1, SHA-256, and SHA-512.", CLIStyle.COLORS["CONTENT"]
        ),
    )
    add_input_arguments(hash_parser)
    return parser


def run_command(arguments: argparse.Namespace) -> bytes:
    """Run the selected command and return its raw output bytes."""
    input_data = read_input(arguments.text, arguments.file)
    if arguments.function == "hash":
        return calculate_hashes(input_data).encode("utf-8")
    if arguments.function == "base64":
        return process_base64(input_data, arguments.direction)

    try:
        input_text = input_data.decode("utf-8")
    except UnicodeDecodeError as error:
        raise ValueError(f"{arguments.function} requires UTF-8 text input.") from error

    if arguments.function in ("urlencode", "urldecode"):
        return process_url(input_text, arguments.function, arguments.direction).encode("utf-8")
    return process_unicode(input_text, arguments.direction).encode("utf-8")


def main(argv: Sequence[str] | None = None) -> int:
    """Parse arguments, run the selected operation, and write the result."""
    global DEBUG_MODE
    parser = create_parser()
    command_arguments = list(sys.argv[1:] if argv is None else argv)
    if not command_arguments:
        parser.print_help()
        return 0
    arguments = parser.parse_args(command_arguments)
    DEBUG_MODE = arguments.log
    try:
        output_data = run_command(arguments)
        write_output(
            output_data,
            arguments.output,
            arguments.plain,
            arguments.function == "hash",
        )
    except FileNotFoundError as error:
        sys.stderr.write(CLIStyle.color(f"Error: File not found: {error.filename}\n", CLIStyle.COLORS["ERROR"]))
        return 1
    except (UnicodeError, ValueError) as error:
        sys.stderr.write(CLIStyle.color(f"Error: {error}\n", CLIStyle.COLORS["ERROR"]))
        return 1
    except Exception as error:
        if DEBUG_MODE:
            traceback.print_exc()
        sys.stderr.write(CLIStyle.color(f"Error: {error}\n", CLIStyle.COLORS["ERROR"]))
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
