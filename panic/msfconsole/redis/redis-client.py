#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""A small redis-cli compatible client implemented with the Python standard library."""

import argparse
import json
import os
import shlex
import socket
import ssl
import sys
import traceback
from typing import Any

DEBUG_MODE = False


class CLIStyle:
    """CLI tool unified style configuration."""

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
        """Return text wrapped in the requested ANSI color."""
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
    """Argument parser with consistently colored help text."""

    def _format_action_invocation(self, action: argparse.Action) -> str:
        """Render option names with the shared CLI style."""
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

    def format_help(self) -> str:
        """Format parser help with colored headings and descriptions."""
        formatter = self._get_formatter()
        if self.description:
            formatter.add_text(CLIStyle.color(self.description, CLIStyle.COLORS["TITLE"]))
        formatter.add_usage(self.usage, self._actions, self._mutually_exclusive_groups)
        for action_group in self._action_groups:
            title = CLIStyle.color(action_group.title.title(), CLIStyle.COLORS["TITLE"])
            formatter.start_section(title)
            formatter.add_arguments(action_group._group_actions)
            formatter.end_section()
        if self.epilog:
            formatter.add_text(self.epilog)
        return formatter.format_help()


class RedisProtocolError(Exception):
    """Raised when a server reply is not valid RESP data."""


class RedisCommandError(Exception):
    """Raised when Redis returns an error reply."""


class RedisConnection:
    """Minimal RESP2/RESP3 Redis connection."""

    def __init__(
        self,
        host: str,
        port: int,
        timeout: float,
        use_tls: bool,
    ) -> None:
        """Store connection parameters without opening a socket."""
        self.host = host
        self.port = port
        self.timeout = timeout
        self.use_tls = use_tls
        self.socket: socket.socket | ssl.SSLSocket | None = None
        self.buffer = b""

    def connect(self) -> None:
        """Open the configured TCP or TLS connection."""
        connection = socket.create_connection((self.host, self.port), self.timeout)
        if self.use_tls:
            context = ssl.create_default_context()
            connection = context.wrap_socket(connection, server_hostname=self.host)
        self.socket = connection

    def close(self) -> None:
        """Close the socket if it was opened."""
        if self.socket:
            self.socket.close()
            self.socket = None

    def execute(self, *parts: str) -> Any:
        """Send one Redis command and decode its RESP reply."""
        if not self.socket:
            raise ConnectionError("Connection is not open")
        request = self._encode_command(parts)
        self.socket.sendall(request)
        return self._read_response()

    def _encode_command(self, parts: tuple[str, ...]) -> bytes:
        """Encode command parts as a RESP array of bulk strings."""
        encoded_parts = [part.encode("utf-8") for part in parts]
        payload = [f"*{len(encoded_parts)}\r\n".encode("ascii")]
        for part in encoded_parts:
            payload.extend((f"${len(part)}\r\n".encode("ascii"), part, b"\r\n"))
        return b"".join(payload)

    def _read_response(self) -> Any:
        """Read and decode one complete RESP response."""
        prefix = self._read_exact(1)
        if prefix == b"+":
            return self._read_line().decode("utf-8", errors="replace")
        if prefix == b"-":
            raise RedisCommandError(self._read_line().decode("utf-8", errors="replace"))
        if prefix == b":":
            return int(self._read_line())
        if prefix == b"$":
            return self._read_bulk_string()
        if prefix in (b"*", b"~", b">"):
            return self._read_collection()
        if prefix == b"%":
            return self._read_map()
        if prefix == b"_":
            self._read_line()
            return None
        if prefix == b"#":
            return self._read_line() == b"t"
        if prefix == b",":
            return float(self._read_line())
        if prefix == b"!":
            raise RedisCommandError(self._read_bulk_string() or "Redis error")
        raise RedisProtocolError(f"Unsupported RESP prefix: {prefix!r}")

    def _read_bulk_string(self) -> str | None:
        """Read a RESP bulk string, including the null representation."""
        length = int(self._read_line())
        if length == -1:
            return None
        value = self._read_exact(length)
        if self._read_exact(2) != b"\r\n":
            raise RedisProtocolError("Bulk string does not end in CRLF")
        return value.decode("utf-8", errors="replace")

    def _read_collection(self) -> list[Any] | None:
        """Read a RESP array, set, or push collection."""
        length = int(self._read_line())
        if length == -1:
            return None
        return [self._read_response() for _ in range(length)]

    def _read_map(self) -> dict[str, Any]:
        """Read a RESP3 map reply."""
        length = int(self._read_line())
        return {
            str(self._read_response()): self._read_response() for _ in range(length)
        }

    def _read_line(self) -> bytes:
        """Read one CRLF-terminated RESP line."""
        while b"\r\n" not in self.buffer:
            self._receive()
        line, self.buffer = self.buffer.split(b"\r\n", 1)
        return line

    def _read_exact(self, size: int) -> bytes:
        """Read exactly size bytes from the buffered socket."""
        while len(self.buffer) < size:
            self._receive()
        value, self.buffer = self.buffer[:size], self.buffer[size:]
        return value

    def _receive(self) -> None:
        """Receive another socket chunk into the internal buffer."""
        if not self.socket:
            raise ConnectionError("Connection is not open")
        chunk = self.socket.recv(65536)
        if not chunk:
            raise ConnectionError("Redis closed the connection")
        self.buffer += chunk


def create_example_text(script_name: str) -> str:
    """Build colored examples shared by the main help screen."""
    examples = [
        ("Set and get a string", "set greeting hello && redis-client.py get greeting"),
        ("List matching keys", "keys 'session:*'"),
        ("Run an arbitrary Redis command", "raw CONFIG GET maxmemory"),
        ("Start an interactive prompt", "shell"),
    ]
    lines = [f"\n{CLIStyle.color('Examples:', CLIStyle.COLORS['SUB_TITLE'])}"]
    for description, command in examples:
        lines.append(CLIStyle.color(f"  # {description}", CLIStyle.COLORS["EXAMPLE"]))
        lines.append(CLIStyle.color(f"  {script_name} {command}", CLIStyle.COLORS["CONTENT"]))
    lines.append(f"\n{CLIStyle.color('Notes:', CLIStyle.COLORS['SUB_TITLE'])}")
    lines.append(CLIStyle.color("  - Use --raw for script-friendly output.", CLIStyle.COLORS["CONTENT"]))
    lines.append(CLIStyle.color("  - Passwords can be supplied with REDIS_PASSWORD.", CLIStyle.COLORS["CONTENT"]))
    return "\n".join(lines)


def add_connection_options(
    parser: argparse.ArgumentParser, suppress_defaults: bool = False
) -> None:
    """Add connection options accepted by every command."""
    default = argparse.SUPPRESS if suppress_defaults else None
    parser.add_argument("-h", "--host", default=default or "127.0.0.1", help=CLIStyle.color("Redis host"))
    parser.add_argument("-p", "--port", type=int, default=default or 6379, help=CLIStyle.color("Redis port"))
    parser.add_argument("-n", "--db", type=int, default=default or 0, help=CLIStyle.color("Database number"))
    parser.add_argument("-a", "--password", default=default or os.getenv("REDIS_PASSWORD"), help=CLIStyle.color("Authentication password"))
    parser.add_argument("--user", default=default, help=CLIStyle.color("ACL username"))
    parser.add_argument("--tls", action="store_true", default=default, help=CLIStyle.color("Use TLS"))
    parser.add_argument("--timeout", type=float, default=default or 5.0, help=CLIStyle.color("Socket timeout in seconds"))
    parser.add_argument("--raw", action="store_true", default=default, help=CLIStyle.color("Print replies without Redis decorations"))
    parser.add_argument("--json", action="store_true", default=default, help=CLIStyle.color("Print replies as JSON"))
    parser.add_argument("--log", action="store_true", default=default, help=CLIStyle.color("Show traceback on failures"))


def add_command(
    subparsers: Any,
    name: str,
    help_text: str,
    arguments: list[tuple[tuple[str, ...], dict[str, Any]]],
) -> None:
    """Add a Redis command parser with common connection options."""
    parser = subparsers.add_parser(
        name,
        add_help=False,
        help=CLIStyle.color(help_text),
        description=CLIStyle.color(help_text, CLIStyle.COLORS["TITLE"]),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=create_example_text("redis-client.py"),
    )
    parser.add_argument("--help", action="help", help=CLIStyle.color("Show this help message and exit"))
    add_connection_options(parser, suppress_defaults=True)
    for option_names, options in arguments:
        parser.add_argument(*option_names, **options)


def create_parser() -> ColoredArgumentParser:
    """Create the command-line parser and supported Redis commands."""
    parser = ColoredArgumentParser(
        prog="redis-client.py",
        add_help=False,
        description="A compact Redis client for common redis-cli workflows.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=create_example_text("redis-client.py"),
    )
    parser.add_argument("--help", action="help", help=CLIStyle.color("Show this help message and exit"))
    add_connection_options(parser)
    subparsers = parser.add_subparsers(dest="command", required=True, metavar="COMMAND")
    commands = [
        ("ping", "Test Redis connectivity", []),
        ("get", "Read a string value", [(('key',), {'help': CLIStyle.color('Key name')})]),
        ("set", "Set a string value", [(('key',), {'help': CLIStyle.color('Key name')}), (('value',), {'help': CLIStyle.color('Value')}), (('--ex',), {'type': int, 'help': CLIStyle.color('Expiry in seconds')})]),
        ("del", "Delete one or more keys", [(('keys',), {'nargs': '+', 'help': CLIStyle.color('Key names')})]),
        ("exists", "Count existing keys", [(('keys',), {'nargs': '+', 'help': CLIStyle.color('Key names')})]),
        ("expire", "Set a key expiry", [(('key',), {'help': CLIStyle.color('Key name')}), (('seconds',), {'type': int, 'help': CLIStyle.color('Expiry in seconds')})]),
        ("ttl", "Show a key time to live", [(('key',), {'help': CLIStyle.color('Key name')})]),
        ("type", "Show a key type", [(('key',), {'help': CLIStyle.color('Key name')})]),
        ("keys", "Find keys matching a pattern", [(('pattern',), {'help': CLIStyle.color('Glob pattern')})]),
        ("scan", "Incrementally scan keys", [(('cursor',), {'nargs': '?', 'default': '0', 'help': CLIStyle.color('Scan cursor')}), (('--match',), {'help': CLIStyle.color('Glob pattern')}), (('--count',), {'type': int, 'help': CLIStyle.color('Suggested batch size')})]),
        ("hset", "Set a hash field", [(('key',), {'help': CLIStyle.color('Hash key')}), (('field',), {'help': CLIStyle.color('Field name')}), (('value',), {'help': CLIStyle.color('Field value')})]),
        ("hget", "Read a hash field", [(('key',), {'help': CLIStyle.color('Hash key')}), (('field',), {'help': CLIStyle.color('Field name')})]),
        ("hgetall", "Read every hash field", [(('key',), {'help': CLIStyle.color('Hash key')})]),
        ("lpush", "Push values to a list head", [(('key',), {'help': CLIStyle.color('List key')}), (('values',), {'nargs': '+', 'help': CLIStyle.color('Values')})]),
        ("rpush", "Push values to a list tail", [(('key',), {'help': CLIStyle.color('List key')}), (('values',), {'nargs': '+', 'help': CLIStyle.color('Values')})]),
        ("lrange", "Read a range from a list", [(('key',), {'help': CLIStyle.color('List key')}), (('start',), {'type': int, 'help': CLIStyle.color('Start index')}), (('stop',), {'type': int, 'help': CLIStyle.color('Stop index')})]),
        ("sadd", "Add values to a set", [(('key',), {'help': CLIStyle.color('Set key')}), (('members',), {'nargs': '+', 'help': CLIStyle.color('Members')})]),
        ("smembers", "Read every set member", [(('key',), {'help': CLIStyle.color('Set key')})]),
        ("zadd", "Add a scored sorted-set member", [(('key',), {'help': CLIStyle.color('Sorted-set key')}), (('score',), {'help': CLIStyle.color('Score')}), (('member',), {'help': CLIStyle.color('Member')})]),
        ("zrange", "Read a sorted-set range", [(('key',), {'help': CLIStyle.color('Sorted-set key')}), (('start',), {'type': int, 'help': CLIStyle.color('Start index')}), (('stop',), {'type': int, 'help': CLIStyle.color('Stop index')}), (('--withscores',), {'action': 'store_true', 'help': CLIStyle.color('Include scores')})]),
        ("info", "Show Redis server information", [(('section',), {'nargs': '?', 'help': CLIStyle.color('Optional INFO section')})]),
        ("dbsize", "Return the number of keys", []),
        ("flushdb", "Delete every key in the selected database", [(('--yes',), {'action': 'store_true', 'help': CLIStyle.color('Confirm this destructive command')})]),
        ("raw", "Execute any Redis command", [(('parts',), {'nargs': '+', 'help': CLIStyle.color('Redis command and arguments')})]),
        ("shell", "Open an interactive Redis prompt", []),
    ]
    for name, help_text, arguments in commands:
        add_command(subparsers, name, help_text, arguments)
    return parser


def build_redis_command(arguments: argparse.Namespace) -> list[str]:
    """Translate a command subparser namespace into Redis protocol parts."""
    command = arguments.command.upper()
    if arguments.command == "raw":
        return arguments.parts
    if arguments.command == "set":
        return [command, arguments.key, arguments.value] + (["EX", str(arguments.ex)] if arguments.ex else [])
    if arguments.command == "scan":
        parts = [command, arguments.cursor]
        if arguments.match:
            parts.extend(("MATCH", arguments.match))
        if arguments.count:
            parts.extend(("COUNT", str(arguments.count)))
        return parts
    if arguments.command == "zrange":
        return [command, arguments.key, str(arguments.start), str(arguments.stop)] + (["WITHSCORES"] if arguments.withscores else [])
    command_arguments = {
        "get": [arguments.key], "del": arguments.keys, "exists": arguments.keys,
        "expire": [arguments.key, str(arguments.seconds)], "ttl": [arguments.key],
        "type": [arguments.key], "keys": [arguments.pattern],
        "hset": [arguments.key, arguments.field, arguments.value],
        "hget": [arguments.key, arguments.field], "hgetall": [arguments.key],
        "lpush": [arguments.key, *arguments.values], "rpush": [arguments.key, *arguments.values],
        "lrange": [arguments.key, str(arguments.start), str(arguments.stop)],
        "sadd": [arguments.key, *arguments.members], "smembers": [arguments.key],
        "zadd": [arguments.key, arguments.score, arguments.member],
        "info": [arguments.section] if arguments.section else [], "dbsize": [],
        "ping": [],
    }
    return [command, *command_arguments[arguments.command]]


def open_connection(arguments: argparse.Namespace) -> RedisConnection:
    """Connect and perform optional authentication and database selection."""
    connection = RedisConnection(arguments.host, arguments.port, arguments.timeout, arguments.tls)
    connection.connect()
    if arguments.password:
        authentication = ["AUTH"]
        if arguments.user:
            authentication.append(arguments.user)
        authentication.append(arguments.password)
        connection.execute(*authentication)
    if arguments.db:
        connection.execute("SELECT", str(arguments.db))
    return connection


def flatten_raw(value: Any) -> list[str]:
    """Flatten a response into lines appropriate for --raw output."""
    if value is None:
        return []
    if isinstance(value, dict):
        return [item for pair in value.items() for item in flatten_raw(pair)]
    if isinstance(value, (list, tuple, set)):
        return [item for part in value for item in flatten_raw(part)]
    return [str(value).lower() if isinstance(value, bool) else str(value)]


def format_reply(value: Any, raw: bool, as_json: bool) -> str:
    """Format a Redis reply in default, raw, or JSON mode."""
    if as_json:
        return json.dumps(value, ensure_ascii=False, indent=2, default=str)
    if raw:
        return "\n".join(flatten_raw(value))
    if value is None:
        return "(nil)"
    if isinstance(value, int):
        return f"(integer) {value}"
    if isinstance(value, list):
        return "\n".join(f"{index}) {item}" for index, item in enumerate(value, 1))
    if isinstance(value, dict):
        return "\n".join(f"{key}: {item}" for key, item in value.items())
    return str(value)


def write_output(text: str, color: int = 0) -> None:
    """Write one formatted result to standard output."""
    if text:
        print(CLIStyle.color(text, color))


def normalize_command_arguments(values: list[str]) -> list[str]:
    """Accept redis-cli style uppercase names for built-in command subparsers."""
    option_values = {"-h", "--host", "-p", "--port", "-n", "--db", "-a", "--password", "--user", "--timeout"}
    command_names = {
        "ping", "get", "set", "del", "exists", "expire", "ttl", "type", "keys",
        "scan", "hset", "hget", "hgetall", "lpush", "rpush", "lrange", "sadd",
        "smembers", "zadd", "zrange", "info", "dbsize", "flushdb", "raw", "shell",
    }
    normalized = list(values)
    skip_next = False
    for index, value in enumerate(normalized):
        if skip_next:
            skip_next = False
            continue
        if value in option_values:
            skip_next = True
            continue
        if value.startswith("-"):
            continue
        if value.lower() in command_names:
            normalized[index] = value.lower()
        break
    return normalized


def run_shell(connection: RedisConnection, arguments: argparse.Namespace) -> int:
    """Run an interactive prompt until EOF, exit, or quit."""
    while True:
        try:
            line = input(f"{arguments.host}:{arguments.port}[{arguments.db}]> ").strip()
        except EOFError:
            write_output("")
            return 0
        if not line:
            continue
        if line.lower() in {"exit", "quit"}:
            return 0
        try:
            reply = connection.execute(*shlex.split(line))
            write_output(format_reply(reply, arguments.raw, arguments.json))
        except ValueError as error:
            write_output(f"Error: {error}", CLIStyle.COLORS["ERROR"])
        except (ConnectionError, RedisCommandError, RedisProtocolError) as error:
            write_output(f"Error: {error}", CLIStyle.COLORS["ERROR"])


def main() -> int:
    """Parse arguments, execute a Redis command, and display its reply."""
    global DEBUG_MODE
    parser = create_parser()
    arguments = parser.parse_args(normalize_command_arguments(sys.argv[1:]))
    DEBUG_MODE = arguments.log
    if arguments.command == "flushdb" and not arguments.yes:
        write_output("Error: flushdb requires --yes", CLIStyle.COLORS["ERROR"])
        return 2
    connection: RedisConnection | None = None
    try:
        connection = open_connection(arguments)
        if arguments.command == "shell":
            return run_shell(connection, arguments)
        reply = connection.execute(*build_redis_command(arguments))
        write_output(format_reply(reply, arguments.raw, arguments.json))
        return 0
    except (ConnectionError, OSError, RedisCommandError, RedisProtocolError) as error:
        if DEBUG_MODE:
            traceback.print_exc()
        write_output(f"Error: {error}", CLIStyle.COLORS["ERROR"])
        return 1
    except Exception as error:
        if DEBUG_MODE:
            traceback.print_exc()
        write_output(f"Error: {error}", CLIStyle.COLORS["ERROR"])
        return 1
    finally:
        if connection:
            connection.close()


if __name__ == "__main__":
    sys.exit(main())
