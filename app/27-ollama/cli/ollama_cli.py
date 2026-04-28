#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from typing import Any

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
        """Apply ANSI color to a string."""
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
    """Argument parser with colorized help output."""

    def _format_action_invocation(self, action: argparse.Action) -> str:
        """Colorize action invocation display."""
        if not action.option_strings:
            metavar = self._format_args(action, action.dest.upper())
            return CLIStyle.color(metavar, CLIStyle.COLORS["SUB_TITLE"])

        parts: list[str] = []
        if action.nargs == 0:
            parts.extend(
                CLIStyle.color(x, CLIStyle.COLORS["SUB_TITLE"])
                for x in action.option_strings
            )
        else:
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
        """Render colorized help text."""
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


def create_example_text(
    script_name: str,
    examples: list[tuple[str, str]],
    notes: list[str] | None = None,
) -> str:
    """Build a colorized examples section for help output."""
    text = f"\n{CLIStyle.color('Examples:', CLIStyle.COLORS['SUB_TITLE'])}"
    for desc, cmd in examples:
        text += f"\n  {CLIStyle.color(f'# {desc}', CLIStyle.COLORS['EXAMPLE'])}"
        text += f"\n  {CLIStyle.color(f'{script_name} {cmd}', CLIStyle.COLORS['CONTENT'])}\n"
    if notes:
        text += f"\n{CLIStyle.color('Notes:', CLIStyle.COLORS['SUB_TITLE'])}"
        for note in notes:
            text += f"\n  {CLIStyle.color(f'- {note}', CLIStyle.COLORS['CONTENT'])}"
    return text


def write_line(text: str, color: int = CLIStyle.COLORS["CONTENT"]) -> None:
    """Write a colored line to stdout."""
    sys.stdout.write(CLIStyle.color(text, color) + "\n")
    sys.stdout.flush()


def write_error(text: str) -> None:
    """Write a colored line to stderr."""
    sys.stderr.write(CLIStyle.color(text, CLIStyle.COLORS["ERROR"]) + "\n")
    sys.stderr.flush()


def write_stream(text: str, end: str = "") -> None:
    """Write a colored stream fragment to stdout."""
    sys.stdout.write(CLIStyle.color(text, CLIStyle.COLORS["CONTENT"]) + end)
    sys.stdout.flush()


def debug_log(message: str) -> None:
    """Write a debug message when debug mode is enabled."""
    if DEBUG_MODE:
        sys.stderr.write(
            CLIStyle.color(f"[debug] {message}", CLIStyle.COLORS["WARNING"]) + "\n"
        )
        sys.stderr.flush()


def normalize_base_url(base_url: str) -> str:
    """Normalize the base URL string."""
    return base_url.rstrip("/")


def format_size(num_bytes: int) -> str:
    """Format a byte count into a human-readable string."""
    size = float(num_bytes)
    units = ["B", "KB", "MB", "GB", "TB"]
    index = 0
    while size >= 1024.0 and index < len(units) - 1:
        size /= 1024.0
        index += 1
    return f"{size:.1f}{units[index]}"


def format_timestamp(value: str) -> str:
    """Format an Ollama timestamp into a concise local string."""
    try:
        timestamp = datetime.fromisoformat(value)
        return timestamp.strftime("%Y-%m-%d %H:%M")
    except ValueError:
        return value


@dataclass(frozen=True)
class ClientConfig:
    """Connection settings for Ollama."""

    base_url: str
    timeout: int


class OllamaClient:
    """Minimal client for the Ollama HTTP API."""

    def __init__(self, config: ClientConfig) -> None:
        """Store the immutable client configuration."""
        self.config = config

    def _request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
        stream: bool = False,
    ) -> Any:
        """Perform an HTTP request against the Ollama server."""
        url = urllib.parse.urljoin(f"{self.config.base_url}/", path.lstrip("/"))
        debug_log(f"{method} {url}")
        data = None
        headers = {"Accept": "application/json"}
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"

        request = urllib.request.Request(
            url=url, data=data, headers=headers, method=method
        )

        try:
            response = urllib.request.urlopen(request, timeout=self.config.timeout)
            if stream:
                return response
            body = response.read().decode("utf-8")
            return json.loads(body) if body else {}
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"HTTP {exc.code}: {body}") from exc
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Connection failed: {exc.reason}") from exc

    def version(self) -> dict[str, Any]:
        """Fetch the server version."""
        return self._request("GET", "/api/version")

    def models(self) -> list[dict[str, Any]]:
        """Fetch the installed models list."""
        data = self._request("GET", "/api/tags")
        return data.get("models", [])

    def chat_once(
        self,
        model: str,
        messages: list[dict[str, str]],
        options: dict[str, Any],
    ) -> str:
        """Run a non-streaming chat request and return the full response."""
        data = self._request(
            "POST",
            "/api/chat",
            payload={
                "model": model,
                "messages": messages,
                "stream": False,
                "options": options or None,
            },
        )
        message = data.get("message", {})
        content = message.get("content", "")
        if not content:
            raise RuntimeError("The server returned an empty response.")
        return content

    def chat_stream(
        self,
        model: str,
        messages: list[dict[str, str]],
        options: dict[str, Any],
    ) -> str:
        """Run a streaming chat request and return the aggregated response."""
        response = self._request(
            "POST",
            "/api/chat",
            payload={
                "model": model,
                "messages": messages,
                "stream": True,
                "options": options or None,
            },
            stream=True,
        )

        fragments: list[str] = []
        while True:
            line = response.readline()
            if not line:
                break
            decoded = line.decode("utf-8").strip()
            if not decoded:
                continue
            payload = json.loads(decoded)
            if "error" in payload:
                raise RuntimeError(str(payload["error"]))
            content = payload.get("message", {}).get("content", "")
            if content:
                fragments.append(content)
                write_stream(content)
            if payload.get("done"):
                break

        if fragments:
            sys.stdout.write("\n")
            sys.stdout.flush()
        result = "".join(fragments)
        if not result:
            raise RuntimeError("The server returned an empty response.")
        return result


def build_client(args: argparse.Namespace) -> OllamaClient:
    """Build the Ollama API client from CLI arguments and environment."""
    base_url = normalize_base_url(
        args.base_url or os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")
    )
    timeout = args.timeout or int(os.getenv("OLLAMA_TIMEOUT", "600"))
    return OllamaClient(ClientConfig(base_url=base_url, timeout=timeout))


def resolve_model(args: argparse.Namespace, client: OllamaClient) -> str:
    """Resolve the target model from args, env, or the first installed model."""
    if getattr(args, "model", None):
        return str(args.model)

    env_model = os.getenv("OLLAMA_MODEL", "").strip()
    if env_model:
        return env_model

    models = client.models()
    if not models:
        raise RuntimeError("No models are installed on the remote Ollama server.")
    return str(models[0]["name"])


def build_options(args: argparse.Namespace) -> dict[str, Any]:
    """Build model options from CLI arguments."""
    options: dict[str, Any] = {}
    if getattr(args, "temperature", None) is not None:
        options["temperature"] = args.temperature
    if getattr(args, "top_p", None) is not None:
        options["top_p"] = args.top_p
    return options


def render_response(
    client: OllamaClient,
    model: str,
    messages: list[dict[str, str]],
    options: dict[str, Any],
    stream: bool,
) -> str:
    """Render a model response with optional streaming."""
    if stream:
        return client.chat_stream(model=model, messages=messages, options=options)
    response = client.chat_once(model=model, messages=messages, options=options)
    write_line(response)
    return response


def read_prompt_argument(args: argparse.Namespace) -> str:
    """Resolve a prompt from args or stdin."""
    if args.prompt:
        return str(args.prompt).strip()
    if not sys.stdin.isatty():
        return sys.stdin.read().strip()
    return ""


def run_version(args: argparse.Namespace) -> int:
    """Handle the version subcommand."""
    client = build_client(args)
    data = client.version()
    version = str(data.get("version", "unknown"))
    write_line(f"Server: {client.config.base_url}", CLIStyle.COLORS["TITLE"])
    write_line(f"Version: {version}")
    return 0


def run_models(args: argparse.Namespace) -> int:
    """Handle the models subcommand."""
    client = build_client(args)
    models = client.models()
    if args.json:
        write_line(json.dumps(models, indent=2), CLIStyle.COLORS["CONTENT"])
        return 0

    write_line(f"Server: {client.config.base_url}", CLIStyle.COLORS["TITLE"])
    if not models:
        write_line("No models found.", CLIStyle.COLORS["WARNING"])
        return 0

    for item in models:
        details = item.get("details", {})
        name = str(item.get("name", "unknown"))
        parameter_size = str(details.get("parameter_size", "-"))
        quantization_level = str(details.get("quantization_level", "-"))
        size = format_size(int(item.get("size", 0)))
        modified = format_timestamp(str(item.get("modified_at", "-")))
        write_line(f"- {name}", CLIStyle.COLORS["SUB_TITLE"])
        write_line(
            f"  size={size} params={parameter_size} quant={quantization_level} modified={modified}"
        )
    return 0


def interactive_chat(
    client: OllamaClient,
    model: str,
    system_prompt: str,
    options: dict[str, Any],
    stream: bool,
) -> int:
    """Handle a multi-turn interactive chat session."""
    messages: list[dict[str, str]] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})

    write_line(f"Server: {client.config.base_url}", CLIStyle.COLORS["TITLE"])
    write_line(f"Model: {model}", CLIStyle.COLORS["TITLE"])
    write_line("Type /exit or /quit to stop.", CLIStyle.COLORS["WARNING"])

    while True:
        try:
            prompt = input(CLIStyle.color("\n> ", CLIStyle.COLORS["SUB_TITLE"]))
        except EOFError:
            sys.stdout.write("\n")
            sys.stdout.flush()
            return 0
        except KeyboardInterrupt:
            sys.stdout.write("\n")
            sys.stdout.flush()
            return 0

        prompt = prompt.strip()
        if not prompt:
            continue
        if prompt in {"/exit", "/quit", "exit", "quit"}:
            return 0

        messages.append({"role": "user", "content": prompt})
        response = render_response(
            client=client,
            model=model,
            messages=messages,
            options=options,
            stream=stream,
        )
        messages.append({"role": "assistant", "content": response})


def run_chat(args: argparse.Namespace) -> int:
    """Handle the chat subcommand."""
    client = build_client(args)
    model = resolve_model(args, client)
    system_prompt = (args.system or "").strip()
    prompt = read_prompt_argument(args)
    options = build_options(args)

    if prompt:
        messages: list[dict[str, str]] = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})
        render_response(
            client=client,
            model=model,
            messages=messages,
            options=options,
            stream=not args.no_stream,
        )
        return 0

    return interactive_chat(
        client=client,
        model=model,
        system_prompt=system_prompt,
        options=options,
        stream=not args.no_stream,
    )


def build_parser() -> ColoredArgumentParser:
    """Construct the top-level argument parser."""
    parser = ColoredArgumentParser(
        prog="ollama-cli",
        description="Remote Ollama CLI with Docker-friendly interactive and one-shot chat.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=create_example_text(
            "ollama-cli",
            [
                ("list installed models", "models"),
                ("show server version", "version"),
                (
                    "one-shot chat",
                    'chat -m nemotron-3-nano:4b "Explain this repository."',
                ),
                ("interactive chat", "chat -m nemotron-3-nano:4b"),
                ("pipe a prompt from stdin", "chat -m nemotron-3-nano:4b < prompt.txt"),
            ],
            notes=[
                "Use OLLAMA_BASE_URL to point at a remote server.",
                "Use OLLAMA_MODEL to set a default model.",
            ],
        ),
    )
    parser.add_argument(
        "--base-url",
        default=os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
        help=CLIStyle.color("Remote Ollama base URL.", CLIStyle.COLORS["CONTENT"]),
    )
    parser.add_argument(
        "--timeout",
        default=int(os.getenv("OLLAMA_TIMEOUT", "600")),
        type=int,
        help=CLIStyle.color("HTTP timeout in seconds.", CLIStyle.COLORS["CONTENT"]),
    )
    parser.add_argument(
        "--log",
        action="store_true",
        help=CLIStyle.color("Enable debug logging.", CLIStyle.COLORS["CONTENT"]),
    )

    subparsers = parser.add_subparsers(
        dest="command",
        required=True,
        parser_class=ColoredArgumentParser,
    )

    version_parser = subparsers.add_parser(
        "version",
        description="Show the remote Ollama server version.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=create_example_text(
            "ollama-cli",
            [("show version from the default remote server", "version")],
        ),
    )
    version_parser.set_defaults(func=run_version)

    models_parser = subparsers.add_parser(
        "models",
        description="List installed models on the remote Ollama server.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=create_example_text(
            "ollama-cli",
            [
                ("show models in table form", "models"),
                ("show models as JSON", "models --json"),
            ],
        ),
    )
    models_parser.add_argument(
        "--json",
        action="store_true",
        help=CLIStyle.color("Render the raw JSON payload.", CLIStyle.COLORS["CONTENT"]),
    )
    models_parser.set_defaults(func=run_models)

    chat_parser = subparsers.add_parser(
        "chat",
        description="Start a one-shot or interactive chat against the remote Ollama server.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=create_example_text(
            "ollama-cli",
            [
                ("use the default model", 'chat "Summarize the last commit."'),
                (
                    "specify a model",
                    'chat -m nemotron-3-nano:4b "Write a bash script."',
                ),
                ("set a system prompt", 'chat -m nemotron-3-nano:4b -s "Be concise."'),
                ("start a REPL", "chat -m nemotron-3-nano:4b"),
            ],
            notes=[
                "When no prompt is given and stdin is a TTY, chat starts in interactive mode.",
                "Use --no-stream when the terminal should wait for a full response.",
            ],
        ),
    )
    chat_parser.add_argument(
        "prompt",
        nargs="?",
        help=CLIStyle.color(
            "Prompt text for a one-shot request.", CLIStyle.COLORS["CONTENT"]
        ),
    )
    chat_parser.add_argument(
        "-m",
        "--model",
        help=CLIStyle.color("Model name to use.", CLIStyle.COLORS["CONTENT"]),
    )
    chat_parser.add_argument(
        "-s",
        "--system",
        default="",
        help=CLIStyle.color("Optional system prompt.", CLIStyle.COLORS["CONTENT"]),
    )
    chat_parser.add_argument(
        "--temperature",
        type=float,
        help=CLIStyle.color("Sampling temperature.", CLIStyle.COLORS["CONTENT"]),
    )
    chat_parser.add_argument(
        "--top-p",
        dest="top_p",
        type=float,
        help=CLIStyle.color("Nucleus sampling top-p.", CLIStyle.COLORS["CONTENT"]),
    )
    chat_parser.add_argument(
        "--no-stream",
        action="store_true",
        help=CLIStyle.color("Disable response streaming.", CLIStyle.COLORS["CONTENT"]),
    )
    chat_parser.set_defaults(func=run_chat)
    return parser


def main() -> int:
    """Main program logic."""
    global DEBUG_MODE
    parser = build_parser()
    args = parser.parse_args()
    DEBUG_MODE = bool(args.log)
    try:
        return int(args.func(args))
    except FileNotFoundError:
        write_error("Error: required file not found.")
        return 1
    except Exception as exc:
        if DEBUG_MODE:
            import traceback

            traceback.print_exc()
        write_error(f"Error: {exc}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
