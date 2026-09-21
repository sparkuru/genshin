# -*- coding: utf-8 -*-
# pip install toml
# get *.tldr from https://github.com/sparkuru/tldr.git

import argparse
import os
import re
import shlex
import sys
import toml
from typing import Any, Dict, List, Optional, Tuple

if sys.platform == "win32":
    from colorama import init as colorama_init

    colorama_init(autoreset=True)

DEBUG_MODE = False
TLDR_EXTENSION = ".tldr"
DEFAULT_CONFIG_DIR = os.path.expanduser("~/.config/tldr")
COMMAND_NAMES = {
    "help",
    "list",
    "ls",
    "add",
}
GLOBAL_OPTIONS_WITH_VALUE = {
    "--config-dir",
}
GLOBAL_OPTIONS_WITHOUT_VALUE = {
    "--log",
}
SHELL_ASSIGNMENT_PATTERN = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")
SHELL_COMMAND_WRAPPERS = {
    "command",
    "doas",
    "env",
    "exec",
    "nice",
    "nohup",
    "sudo",
    "time",
}
SHELL_WRAPPER_OPTIONS_WITH_VALUE = {
    "doas": {"-u"},
    "env": {"-C", "--chdir", "-S", "--split-string", "-u", "--unset"},
    "exec": {"-a", "--argv0"},
    "nice": {"-n", "--adjustment"},
    "sudo": {
        "-C",
        "--chdir",
        "--close-from",
        "-D",
        "-g",
        "--group",
        "-p",
        "--prompt",
        "-R",
        "--chroot",
        "-r",
        "--role",
        "-t",
        "--type",
        "-u",
        "--user",
    },
    "time": {"-f", "--format", "-o", "--output"},
}


class CLIStyle:
    """CLI styling and color management"""

    COLORS = {
        "TITLE": 7,
        "SUB_TITLE": 2,
        "CONTENT": 3,
        "EXAMPLE": 7,
        "WARNING": 4,
        "ERROR": 2,
    }

    _COLOR_TABLE = {
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

    @staticmethod
    def color(text: str = "", color_code: int = None) -> str:
        if color_code is None:
            color_code = CLIStyle.COLORS["CONTENT"]
        return CLIStyle._COLOR_TABLE[color_code].format(text)


def debug(*args, file: Optional[str] = None, append: bool = True, **kwargs) -> None:
    """
    Debug logging with file and line number information

    Args:
        *args: Arguments to log
        file: Output file path, None for console output
        append: Whether to append to file
        **kwargs: Key-value parameters to log
    """
    if not DEBUG_MODE:
        return

    import inspect

    frame = inspect.currentframe().f_back
    filename = os.path.basename(frame.f_code.co_filename)
    line_number = frame.f_lineno

    debug_info = f"[{filename}:{line_number}]"
    message_parts = [str(arg) for arg in args]

    if kwargs:
        kwargs_str = ", ".join([f"{k}={v}" for k, v in kwargs.items()])
        message_parts.append(f"({kwargs_str})")

    message = f"{CLIStyle.color(debug_info, 6)} {' '.join(message_parts)}"

    if file:
        mode = "a" if append else "w"
        with open(file, mode, encoding="utf-8") as f:
            f.write(message + "\n")
    else:
        print(message)


def resolve_config_dir(config_dir: Optional[str] = None) -> str:
    """Resolve the effective config directory, falling back to the default"""
    return config_dir or DEFAULT_CONFIG_DIR


def normalize_args_for_target_fallback(args: List[str]) -> List[str]:
    """Treat the first non-command positional argument as help COMMAND."""
    if not args:
        return args

    normalized_args = []
    index = 0
    while index < len(args):
        arg = args[index]

        if arg == "--":
            return args

        if arg in GLOBAL_OPTIONS_WITH_VALUE:
            normalized_args.append(arg)
            if index + 1 >= len(args):
                return args
            normalized_args.append(args[index + 1])
            index += 2
            continue

        if any(arg.startswith(f"{option}=") for option in GLOBAL_OPTIONS_WITH_VALUE):
            normalized_args.append(arg)
            index += 1
            continue

        if arg in GLOBAL_OPTIONS_WITHOUT_VALUE:
            normalized_args.append(arg)
            index += 1
            continue

        if arg.startswith("-") or arg in COMMAND_NAMES:
            return args

        return [*normalized_args, "help", *args[index:]]

    return args


class ColoredArgumentParser(argparse.ArgumentParser):
    """Argument parser with colored output formatting"""

    def __init__(self, *args, **kwargs):
        """Capture optional config directory for display in help output"""
        self.config_dir = kwargs.pop("config_dir", None)
        self.show_config_in_help = kwargs.pop("show_config_in_help", False)
        super().__init__(*args, **kwargs)

    def _format_action_invocation(self, action):
        if not action.option_strings:
            (metavar,) = self._metavar_formatter(action, action.dest)(1)
            return metavar
        else:
            parts = []
            if action.nargs == 0:
                parts.extend(
                    map(
                        lambda x: CLIStyle.color(x, CLIStyle.COLORS["SUB_TITLE"]),
                        action.option_strings,
                    )
                )
            else:
                default = action.dest.upper()
                args_string = self._format_args(action, default)
                for option_string in action.option_strings:
                    parts.append(
                        CLIStyle.color(
                            f"{option_string} {args_string}",
                            CLIStyle.COLORS["SUB_TITLE"],
                        )
                    )
            return ", ".join(parts)

    def format_help(self):
        formatter = self._get_formatter()

        if self.description:
            formatter.add_text(
                CLIStyle.color(self.description, CLIStyle.COLORS["TITLE"])
            )

        formatter.add_usage(self.usage, self._actions, self._mutually_exclusive_groups)

        if self.show_config_in_help:
            formatter.add_text(
                CLIStyle.color("Config directory: ", CLIStyle.COLORS["SUB_TITLE"])
                + CLIStyle.color(
                    resolve_config_dir(self.config_dir), CLIStyle.COLORS["CONTENT"]
                )
            )

        formatter.add_text(CLIStyle.color("\nOptions:", CLIStyle.COLORS["TITLE"]))
        for action_group in self._action_groups:
            formatter.start_section(action_group.title)
            formatter.add_arguments(action_group._group_actions)
            formatter.end_section()

        if self.epilog:
            formatter.add_text(self.epilog)

        return formatter.format_help()


def create_example_text(
    script_name: str, examples: List[tuple], notes: Optional[List[str]] = None
) -> str:
    """Generate formatted example text for help output"""
    text = f"\n{CLIStyle.color('Examples:', CLIStyle.COLORS['SUB_TITLE'])}"

    for desc, cmd in examples:
        text += f"\n  {CLIStyle.color(f'# {desc}', CLIStyle.COLORS['EXAMPLE'])}"
        text += (
            f"\n  {CLIStyle.color(f'{script_name} {cmd}', CLIStyle.COLORS['CONTENT'])}"
        )
        text += "\n"

    if notes:
        text += f"\n{CLIStyle.color('Notes:', CLIStyle.COLORS['SUB_TITLE'])}"
        for note in notes:
            text += f"\n  {CLIStyle.color(f'- {note}', CLIStyle.COLORS['CONTENT'])}"

    return text


class TLDRParser:
    """TLDR configuration file parser and formatter"""

    def __init__(self, config_dir: str = None):
        """Initialize parser with configuration directory"""
        self.config_dir = resolve_config_dir(config_dir)
        debug("Initialized TLDRParser", config_dir=self.config_dir)

    @staticmethod
    def _tokenize_shell_command(
        command: str,
    ) -> List[Tuple[str, int, int, str]]:
        """Tokenize shell syntax while preserving source positions."""
        tokens: List[Tuple[str, int, int, str]] = []
        token_start: Optional[int] = None
        quote: Optional[str] = None
        index = 0

        while index < len(command):
            char = command[index]

            if quote:
                if char == "\\" and quote == '"':
                    index += 2 if index + 1 < len(command) else 1
                elif char == quote:
                    quote = None
                    index += 1
                else:
                    index += 1
                continue

            if char in ("'", '"'):
                if token_start is None:
                    token_start = index
                quote = char
                index += 1
                continue

            if char == "\\":
                if token_start is None:
                    token_start = index
                index += 2 if index + 1 < len(command) else 1
                continue

            if char == "\n":
                if token_start is not None:
                    tokens.append((command[token_start:index], token_start, index, "word"))
                    token_start = None
                tokens.append((char, index, index + 1, "separator"))
                index += 1
                continue

            if char.isspace():
                if token_start is not None:
                    tokens.append((command[token_start:index], token_start, index, "word"))
                    token_start = None
                index += 1
                continue

            if char in ";|&()":
                if token_start is not None:
                    tokens.append((command[token_start:index], token_start, index, "word"))
                    token_start = None

                operator_end = index + 1
                if command[index : index + 2] in ("&&", "||", "|&"):
                    operator_end = index + 2
                tokens.append((command[index:operator_end], index, operator_end, "separator"))
                index = operator_end
                continue

            if char in "<>":
                if token_start is not None:
                    tokens.append((command[token_start:index], token_start, index, "word"))
                    token_start = None

                operator_end = index + 1
                while operator_end < len(command) and command[operator_end] in "<>":
                    operator_end += 1
                if operator_end < len(command) and command[operator_end] == "&":
                    operator_end += 1
                    if operator_end < len(command) and command[operator_end] == "-":
                        operator_end += 1
                tokens.append(
                    (command[index:operator_end], index, operator_end, "redirection")
                )
                index = operator_end
                continue

            if token_start is None:
                token_start = index
            index += 1

        if token_start is not None:
            tokens.append((command[token_start:], token_start, len(command), "word"))

        return tokens

    @staticmethod
    def _decode_shell_word(token: str) -> str:
        """Decode one shell word for exact command-name comparison."""
        try:
            words = shlex.split(token, posix=True)
        except ValueError:
            return token
        return words[0] if len(words) == 1 else token

    @staticmethod
    def _matches_command(token: str, target_command: str) -> bool:
        """Return whether a shell word names the target command."""
        token_value = TLDRParser._decode_shell_word(token)
        target_value = target_command.strip()
        if not token_value or not target_value:
            return False
        if token_value == target_value:
            return True
        return "/" not in target_value and os.path.basename(token_value) == target_value

    @staticmethod
    def _is_redirection_file_descriptor(
        tokens: List[Tuple[str, int, int, str]], index: int
    ) -> bool:
        """Return whether a numeric word prefixes a shell redirection."""
        token, _, token_end, token_type = tokens[index]
        if token_type != "word" or not token.isdigit() or index + 1 >= len(tokens):
            return False

        _, next_start, _, next_type = tokens[index + 1]
        return next_type == "redirection" and token_end == next_start

    @staticmethod
    def _wrapper_option_requires_value(wrapper: str, token: str) -> bool:
        """Return whether a wrapper option consumes the next shell word."""
        for option in SHELL_WRAPPER_OPTIONS_WITH_VALUE.get(wrapper, set()):
            if token == option:
                return True
        return False

    @classmethod
    def _find_command_spans(
        cls, command: str, target_command: str
    ) -> List[Tuple[int, int]]:
        """Find matching executable spans in a shell command line."""
        tokens = cls._tokenize_shell_command(command)
        spans: List[Tuple[int, int]] = []
        at_command_start = True
        skip_redirection_word = False
        wrapper_name: Optional[str] = None
        skip_wrapper_word = False

        for index, (token, start, end, token_type) in enumerate(tokens):
            if token_type == "separator":
                at_command_start = True
                skip_redirection_word = False
                wrapper_name = None
                skip_wrapper_word = False
                continue

            if token_type == "redirection":
                skip_redirection_word = True
                continue

            if token_type != "word":
                continue

            if cls._is_redirection_file_descriptor(tokens, index):
                continue

            if skip_redirection_word:
                skip_redirection_word = False
                continue

            if not at_command_start:
                continue

            token_value = cls._decode_shell_word(token)
            if SHELL_ASSIGNMENT_PATTERN.match(token_value):
                continue

            if wrapper_name and skip_wrapper_word:
                skip_wrapper_word = False
                continue

            if wrapper_name and token_value == "--":
                continue

            if wrapper_name and token_value.startswith("-"):
                skip_wrapper_word = cls._wrapper_option_requires_value(
                    wrapper_name, token_value
                )
                continue

            if cls._matches_command(token, target_command):
                spans.append((start, end))
                at_command_start = False
                continue

            wrapper_candidate = os.path.basename(token_value)
            if wrapper_candidate in SHELL_COMMAND_WRAPPERS:
                wrapper_name = wrapper_candidate
                continue

            at_command_start = False

        return spans

    def format_command(
        self, command: str, target_command: Optional[str] = None
    ) -> str:
        """Format a command and highlight only its matching executable."""
        if not command:
            return ""

        target = target_command or ""
        spans = self._find_command_spans(command, target)
        if not spans:
            formatted = CLIStyle.color(command, CLIStyle.COLORS["EXAMPLE"])
            return f"`{formatted}`"

        formatted_parts: List[str] = []
        cursor = 0
        for start, end in spans:
            if cursor < start:
                formatted_parts.append(
                    CLIStyle.color(command[cursor:start], CLIStyle.COLORS["EXAMPLE"])
                )
            formatted_parts.append(
                CLIStyle.color(command[start:end], CLIStyle.COLORS["WARNING"])
            )
            cursor = end

        if cursor < len(command):
            formatted_parts.append(
                CLIStyle.color(command[cursor:], CLIStyle.COLORS["EXAMPLE"])
            )

        return f"`{''.join(formatted_parts)}`"

    def find_config_file(self, command: str) -> Optional[str]:
        """Locate configuration file for specified command"""
        config_file = os.path.join(self.config_dir, f"{command}{TLDR_EXTENSION}")
        debug("Looking for config file", path=config_file)

        if os.path.exists(config_file):
            return config_file

        local_config = f"{command}{TLDR_EXTENSION}"
        if os.path.exists(local_config):
            debug("Found local config file", path=local_config)
            return local_config

        return None

    def parse_config(self, config_file: str) -> Optional[Dict[str, Any]]:
        """Parse TOML configuration file and validate structure"""
        try:
            debug("Parsing config file", file=config_file)
            with open(config_file, "r", encoding="utf-8") as f:
                config = toml.load(f)

            if "meta" not in config:
                print(
                    CLIStyle.color(
                        f"Error: Missing 'meta' section in {config_file}",
                        CLIStyle.COLORS["ERROR"],
                    )
                )
                return None

            if "examples" not in config:
                print(
                    CLIStyle.color(
                        f"Warning: No 'examples' section in {config_file}",
                        CLIStyle.COLORS["WARNING"],
                    )
                )
                config["examples"] = []

            debug("Config parsed successfully", examples_count=len(config["examples"]))
            return config

        except Exception as e:
            print(
                CLIStyle.color(
                    f"Error parsing config file {config_file}: {str(e)}",
                    CLIStyle.COLORS["ERROR"],
                )
            )
            return None

    def format_output(self, config: Dict[str, Any]) -> str:
        """Format configuration data for terminal display"""
        meta = config.get("meta", {})
        hit = config.get("hit", [])
        examples = config.get("examples", [])

        output = []

        name = meta.get("name", "Unknown")
        description = meta.get("description", "No description available")
        url = meta.get("url", "")

        output.append(
            CLIStyle.color(f"{name}: {description}", CLIStyle.COLORS["TITLE"])
        )
        if url:
            output.append(CLIStyle.color(f"url: {url}", CLIStyle.COLORS["CONTENT"]))
        output.append("")

        if hit:
            output.append(CLIStyle.color("hit:", CLIStyle.COLORS["SUB_TITLE"]))
            output.append("")
            for i, example in enumerate(hit, 1):
                command = example.get("command", "")
                desc = example.get("description", "")

                output.append(
                    CLIStyle.color(f"{i}. {desc}", CLIStyle.COLORS["CONTENT"])
                )
                output.append("  " + self.format_command(command, name))
                output.append("")

        output.append(CLIStyle.color("usage:", CLIStyle.COLORS["SUB_TITLE"]))
        output.append("")

        for i, example in enumerate(examples, 1):
            title = example.get("title", f"Example {i}")
            command = example.get("command", "")
            desc = example.get("description", "")

            output.append(CLIStyle.color(f"{i}. {title}", CLIStyle.COLORS["CONTENT"]))
            if desc:
                output.append(CLIStyle.color(f"   {desc}", CLIStyle.COLORS["CONTENT"]))
            output.append(self.format_command(command, name))
            output.append("")

        return "\n".join(output)


class TLDRTool:
    """Main TLDR application interface"""

    def __init__(self, config_dir: str = None):
        """Initialize TLDR tool with parser"""
        self.parser = TLDRParser(config_dir)
        debug("Initialized TLDRTool")

    def _get_all_commands(self) -> List[str]:
        """Get sorted list of all available command names"""
        if not os.path.exists(self.parser.config_dir):
            return []
        return sorted(
            f[: -len(TLDR_EXTENSION)]
            for f in os.listdir(self.parser.config_dir)
            if f.endswith(TLDR_EXTENSION)
        )

    def _search_commands(self, query: str) -> List[str]:
        """Filter available commands by substring"""
        return [cmd for cmd in self._get_all_commands() if query in cmd]

    @staticmethod
    def _highlight_match(name: str, query: str) -> str:
        """Highlight matching substring in command name (grep-like)"""
        idx = name.find(query)
        if idx == -1:
            return CLIStyle.color(name, CLIStyle.COLORS["CONTENT"])
        before = CLIStyle.color(name[:idx], CLIStyle.COLORS["CONTENT"])
        match = CLIStyle.color(query, CLIStyle.COLORS["WARNING"])
        after = CLIStyle.color(name[idx + len(query) :], CLIStyle.COLORS["CONTENT"])
        return before + match + after

    def _display_matching_commands(self, query: str, matches: List[str]) -> None:
        """Display matching commands with highlighted query"""
        print(CLIStyle.color(f"Commands matching '{query}':", CLIStyle.COLORS["TITLE"]))
        for cmd in matches:
            print(f"  - {self._highlight_match(cmd, query)}")

    def _print_resolve(self, query: str, resolved: str) -> None:
        """Print auto-resolve message with highlighted match"""
        query_hl = CLIStyle.color(query, CLIStyle.COLORS["WARNING"])
        resolved_hl = self._highlight_match(resolved, query)
        arrow = CLIStyle.color("->", CLIStyle.COLORS["CONTENT"])
        quote = CLIStyle.color("'", CLIStyle.COLORS["CONTENT"])
        print(f"{quote}{query_hl}{quote} {arrow} {resolved_hl}")

    def _create_default_config(self, command: str, config_file: str) -> None:
        """Create default TLDR configuration file"""
        default_config = {
            "meta": {
                "name": command,
                "description": f"Quick reference for {command}",
                "url": "",
            },
            "hit": [],
            "examples": [],
        }

        os.makedirs(os.path.dirname(config_file), exist_ok=True)

        with open(config_file, "w", encoding="utf-8") as f:
            toml.dump(default_config, f)

        debug("Created default config file", path=config_file)

    def add_example(self, command: str, cmd: str, desc: str = "") -> bool:
        """Add command example to configuration file"""
        debug("Adding example", command=command, cmd=cmd)

        config_file = self.parser.find_config_file(command)

        if not config_file:
            config_file = os.path.join(
                self.parser.config_dir, f"{command}{TLDR_EXTENSION}"
            )
            print(
                CLIStyle.color(
                    f"Configuration file not found, creating: {config_file}",
                    CLIStyle.COLORS["WARNING"],
                )
            )
            self._create_default_config(command, config_file)

        try:
            config = self.parser.parse_config(config_file)
            if not config:
                return False

            if "hit" not in config:
                config["hit"] = []

            new_example = {
                "command": cmd,
                "description": desc,
            }

            config["hit"].append(new_example)

            with open(config_file, "w", encoding="utf-8") as f:
                toml.dump(config, f)

            print(
                CLIStyle.color(
                    f"Successfully added example to {command}{TLDR_EXTENSION}",
                    CLIStyle.COLORS["CONTENT"],
                )
            )
            return True

        except Exception as e:
            print(
                CLIStyle.color(
                    f"Error adding example: {str(e)}", CLIStyle.COLORS["ERROR"]
                )
            )
            return False

    def delete_hit(self, command: str, index: int) -> bool:
        """Delete hit entry at specified index"""
        debug("Deleting hit entry", command=command, index=index)

        config_file = self.parser.find_config_file(command)
        if not config_file:
            print(
                CLIStyle.color(
                    f"Error: No configuration found for command '{command}'",
                    CLIStyle.COLORS["ERROR"],
                )
            )
            return False

        try:
            config = self.parser.parse_config(config_file)
            if not config:
                return False

            if "hit" not in config or not config["hit"]:
                print(
                    CLIStyle.color("No hit entries found", CLIStyle.COLORS["WARNING"])
                )
                return False

            if index < 1 or index > len(config["hit"]):
                print(
                    CLIStyle.color(
                        f"Invalid index: {index}. Valid range: 1-{len(config['hit'])}",
                        CLIStyle.COLORS["ERROR"],
                    )
                )
                return False

            config["hit"].pop(index - 1)

            with open(config_file, "w", encoding="utf-8") as f:
                toml.dump(config, f)

            print(
                CLIStyle.color(
                    f"Successfully deleted hit entry {index}",
                    CLIStyle.COLORS["CONTENT"],
                )
            )
            return True

        except Exception as e:
            print(
                CLIStyle.color(
                    f"Error deleting entry: {str(e)}", CLIStyle.COLORS["ERROR"]
                )
            )
            return False

    def show_help(self, command: str, delete_index: Optional[int] = None) -> bool:
        """Display help information for specified command, with substring matching fallback"""
        debug("Showing help for command", command=command)

        config_file = self.parser.find_config_file(command)

        if not config_file:
            matches = self._search_commands(command)
            if len(matches) == 1:
                self._print_resolve(command, matches[0])
                return self.show_help(matches[0], delete_index)
            if matches:
                self._display_matching_commands(command, matches)
                return True

            print(
                CLIStyle.color(
                    f"No configuration found for '{command}'",
                    CLIStyle.COLORS["ERROR"],
                )
            )
            print(
                CLIStyle.color(
                    f"Looking for: {command}{TLDR_EXTENSION} in {self.parser.config_dir} or current directory",
                    CLIStyle.COLORS["CONTENT"],
                )
            )
            return False

        if delete_index is not None:
            return self.delete_hit(command, delete_index)

        config = self.parser.parse_config(config_file)
        if not config:
            return False

        config_path = os.path.abspath(config_file)
        print(
            CLIStyle.color(
                f"> load config from: {config_path}", CLIStyle.COLORS["CONTENT"]
            )
        )
        output = self.parser.format_output(config)
        print(output)
        return True

    def list_available(self, query: str = None) -> None:
        """Display available TLDR configurations, optionally filtered by substring"""
        debug("Listing available configurations", query=query)

        if not os.path.exists(self.parser.config_dir):
            print(
                CLIStyle.color(
                    f"Configuration directory does not exist: {self.parser.config_dir}",
                    CLIStyle.COLORS["WARNING"],
                )
            )
            return

        if query:
            matches = self._search_commands(query)
            if not matches:
                print(
                    CLIStyle.color(
                        f"No commands matching '{query}'", CLIStyle.COLORS["WARNING"]
                    )
                )
                return
            self._display_matching_commands(query, matches)
            return

        commands = self._get_all_commands()
        if not commands:
            print(
                CLIStyle.color(
                    "No TLDR configurations found", CLIStyle.COLORS["WARNING"]
                )
            )
            return

        print(
            CLIStyle.color("Available TLDR configurations:", CLIStyle.COLORS["TITLE"])
        )
        for cmd in commands:
            print(CLIStyle.color(f"  - {cmd}", CLIStyle.COLORS["CONTENT"]))


def main() -> int:
    """Application entry point and command line interface"""
    script_name = os.path.basename(sys.argv[0])

    examples = [
        ("List available configurations by default", ""),
        ("Show help without explicit help subcommand", "7z"),
        ("Show help for ip command", "help ip"),
        ("Show help for git command", "help git"),
        ("Substring match: auto-resolve or list candidates", "help i"),
        ("Delete hit entry at index 3", "help uv --delete 3"),
        ("List available configurations explicitly", "list/ls"),
        ("List commands matching pattern", "list i"),
        (
            "Add command example",
            'add magick --cmd "magick -resize 256x256 src.png dst.ico" --desc "Resize and convert"',
        ),
        ("Use custom config directory", "--config-dir /dir/path/to/*.tldr help ip"),
        ("Show current config directory", "--show-config"),
    ]

    notes = [
        "Configuration files should be named <command>.tldr and use TOML format",
        "Default config directory is ~/.config/tldr",
        "Running without a command lists available configurations",
        "If the first non-option argument is not a TLDR command, it is treated as help COMMAND",
        "Use --log to enable debug mode for troubleshooting",
    ]

    parser = ColoredArgumentParser(
        description=CLIStyle.color(
            "TLDR - Quick command reference tool", CLIStyle.COLORS["TITLE"]
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=create_example_text(script_name, examples, notes),
        show_config_in_help=True,
    )

    pre_parser = argparse.ArgumentParser(add_help=False)
    pre_parser.add_argument("--config-dir", type=str)
    pre_args, _ = pre_parser.parse_known_args()
    parser.config_dir = pre_args.config_dir

    parser.add_argument("--log", action="store_true", help="Enable debug logging")
    parser.add_argument(
        "--config-dir",
        type=str,
        metavar=CLIStyle.color("DIR", CLIStyle.COLORS["WARNING"]),
        help=CLIStyle.color(
            "Custom configuration directory", CLIStyle.COLORS["CONTENT"]
        ),
    )
    parser.add_argument(
        "--show-config",
        action="store_true",
        help=CLIStyle.color(
            "Display current configuration directory", CLIStyle.COLORS["CONTENT"]
        ),
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    help_parser = subparsers.add_parser(
        "help",
        help=CLIStyle.color("Show help for a command", CLIStyle.COLORS["CONTENT"]),
        description=CLIStyle.color(
            "Display TLDR help for specified command", CLIStyle.COLORS["TITLE"]
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    help_parser.add_argument(
        "target_command",
        metavar=CLIStyle.color("COMMAND", CLIStyle.COLORS["WARNING"]),
        help=CLIStyle.color("Command to show help for", CLIStyle.COLORS["CONTENT"]),
    )
    help_parser.add_argument(
        "--delete",
        type=int,
        metavar=CLIStyle.color("INDEX", CLIStyle.COLORS["WARNING"]),
        help=CLIStyle.color(
            "Delete hit entry at specified index", CLIStyle.COLORS["CONTENT"]
        ),
    )

    list_parser = subparsers.add_parser(
        "list",
        help=CLIStyle.color(
            "List available configurations", CLIStyle.COLORS["CONTENT"]
        ),
        description=CLIStyle.color(
            "List all available TLDR configurations", CLIStyle.COLORS["TITLE"]
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    list_parser.add_argument(
        "query",
        nargs="?",
        default=None,
        metavar=CLIStyle.color("PATTERN", CLIStyle.COLORS["WARNING"]),
        help=CLIStyle.color("Filter commands by substring", CLIStyle.COLORS["CONTENT"]),
    )
    ls_parser = subparsers.add_parser(
        "ls",
        help=argparse.SUPPRESS,
        description=list_parser.description,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ls_parser.add_argument(
        "query",
        nargs="?",
        default=None,
        metavar=CLIStyle.color("PATTERN", CLIStyle.COLORS["WARNING"]),
        help=CLIStyle.color("Filter commands by substring", CLIStyle.COLORS["CONTENT"]),
    )

    add_parser = subparsers.add_parser(
        "add",
        help=CLIStyle.color(
            "Add command example to configuration", CLIStyle.COLORS["CONTENT"]
        ),
        description=CLIStyle.color(
            "Add new command example to TLDR configuration", CLIStyle.COLORS["TITLE"]
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    add_parser.add_argument(
        "--cmd",
        "-c",
        required=True,
        metavar=CLIStyle.color("COMMAND", CLIStyle.COLORS["WARNING"]),
        help=CLIStyle.color("Command to add", CLIStyle.COLORS["CONTENT"]),
    )
    add_parser.add_argument(
        "--desc",
        "-d",
        default="",
        metavar=CLIStyle.color("DESCRIPTION", CLIStyle.COLORS["WARNING"]),
        help=CLIStyle.color("Command description", CLIStyle.COLORS["CONTENT"]),
    )
    add_parser.add_argument(
        "command_name",
        metavar=CLIStyle.color("NAME", CLIStyle.COLORS["WARNING"]),
        help=CLIStyle.color(
            "Target command name (e.g., magick, git)", CLIStyle.COLORS["CONTENT"]
        ),
    )

    args = parser.parse_args(normalize_args_for_target_fallback(sys.argv[1:]))

    global DEBUG_MODE
    DEBUG_MODE = args.log

    if args.show_config:
        config_dir = resolve_config_dir(args.config_dir)
        print(CLIStyle.color("Configuration directory:", CLIStyle.COLORS["TITLE"]))
        print(CLIStyle.color(f"  {config_dir}", CLIStyle.COLORS["CONTENT"]))
        if os.path.exists(config_dir):
            print(CLIStyle.color("  (exists)", CLIStyle.COLORS["CONTENT"]))
        else:
            print(CLIStyle.color("  (not exists)", CLIStyle.COLORS["WARNING"]))
        return 0

    try:
        tldr_tool = TLDRTool(args.config_dir)

        if not args.command:
            tldr_tool.list_available()
            return 0
        elif args.command == "help":
            success = tldr_tool.show_help(args.target_command, args.delete)
            return 0 if success else 1
        elif args.command in ("list", "ls"):
            tldr_tool.list_available(args.query)
            return 0
        elif args.command == "add":
            success = tldr_tool.add_example(args.command_name, args.cmd, args.desc)
            return 0 if success else 1
        else:
            print(
                CLIStyle.color(
                    f"Unknown command: {args.command}", CLIStyle.COLORS["ERROR"]
                )
            )
            return 1

    except KeyboardInterrupt:
        print(
            CLIStyle.color("\nOperation cancelled by user", CLIStyle.COLORS["WARNING"])
        )
        return 0
    except Exception as e:
        if DEBUG_MODE:
            import traceback

            traceback.print_exc()
        print(CLIStyle.color(f"\nError: {str(e)}", CLIStyle.COLORS["ERROR"]))
        return 1


if __name__ == "__main__":
    sys.exit(main())
