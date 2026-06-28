# -*- coding: utf-8 -*-
# pip install argparse

import argparse
import json
import os
import sys
from dataclasses import dataclass
from typing import Any

if sys.platform == "win32":
    from colorama import init as colorama_init

    colorama_init(autoreset=True)

VERSION = "1.2.0"
CONFIG_VERSION = 2
COMMAND_NAMES = {
    "list",
    "ls",
    "l",
    "add",
    "rm",
    "remove",
    "show",
    "s",
    "clean",
    "move",
    "config",
    "dump",
}

if os.environ.get("USERPROFILE") is not None:
    windows_user_home = os.environ.get("USERPROFILE", "").replace("\\", "/")
    CONFIG_FILE = f"{windows_user_home}/.lcd-path"
elif os.environ.get("HOME") is not None:
    CONFIG_FILE = f"{os.environ.get('HOME')}/.lcd-path"
else:
    CONFIG_FILE = f"{os.path.dirname(os.path.abspath(__file__))}/.lcd-path"


class CLIStyle:
    """CLI tool unified style config."""

    COLORS = {
        "TITLE": 7,
        "SUB_TITLE": 2,
        "CONTENT": 3,
        "EXAMPLE": 6,
        "WARNING": 4,
        "ERROR": 2,
        "PATH": 3,
        "NUMBER": 4,
        "ALIAS": 6,
    }

    @staticmethod
    def color(text: object = "", color_code: int = 0) -> str:
        """Colorize text for terminal output."""
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
        text_value = str(text)
        return color_table[color_code].format(
            clean_path(text_value) if os.path.sep in text_value else text_value
        )


def color(text: object = "", color_code: int = 0) -> str:
    """Colorize text for terminal output."""
    return CLIStyle.color(text, color_code)


@dataclass
class PathEntry:
    """Stored path entry."""

    path: str
    alias: str | None = None

    def to_dict(self) -> dict[str, str]:
        """Convert entry to JSON data."""
        data = {"path": self.path}
        if self.alias:
            data["alias"] = self.alias
        return data


def clean_path(path: str) -> str:
    """Clean path string, replace backslashes with forward slashes and strip whitespace."""
    return path.replace("\\", "/").strip()


def normalize_path(path: str) -> str:
    """Return an absolute path using the script's storage format."""
    return clean_path(os.path.abspath(path))


def parse_path_number(text: str) -> int | None:
    """Return a positive path number from text when it is numeric."""
    if not text.isdecimal():
        return None

    num = int(text)
    return num if num > 0 else None


def normalize_alias(alias: str | None) -> str | None:
    """Normalize an alias string."""
    if alias is None:
        return None

    alias_value = alias.strip()
    return alias_value or None


def is_valid_alias(alias: str) -> bool:
    """Return whether an alias can be used without target ambiguity."""
    return (
        parse_path_number(alias) is None
        and os.path.sep not in alias
        and alias not in COMMAND_NAMES
        and not alias.startswith("-")
    )


class PathManager:
    """Path Manager - Handles storage, deletion and display of paths."""

    def __init__(self, config_file: str):
        """Initialize the path manager."""
        self.config_file = config_file
        self.entries = self.load_entries()

    def load_entries(self) -> list[PathEntry]:
        """Load path entries from config file."""
        if not os.path.exists(self.config_file):
            self.entries = []
            self.save_entries()
            return []

        try:
            with open(self.config_file, "r", encoding="utf-8") as file:
                data = json.load(file)
        except json.JSONDecodeError:
            print(
                color(f"Config file corrupted: {self.config_file}", CLIStyle.COLORS["ERROR"]),
                file=sys.stderr,
            )
            print(color("Creating new config file...", CLIStyle.COLORS["WARNING"]))
            self.entries = []
            self.save_entries()
            return []

        return self.parse_config_data(data)

    def parse_config_data(self, data: Any) -> list[PathEntry]:
        """Parse current and legacy config formats."""
        if isinstance(data, list):
            return [
                PathEntry(path=clean_path(path))
                for path in data
                if isinstance(path, str) and path.strip()
            ]

        if not isinstance(data, dict):
            print(
                color(f"Invalid config file format: {self.config_file}", CLIStyle.COLORS["ERROR"]),
                file=sys.stderr,
            )
            return []

        paths = data.get("paths", [])
        if not isinstance(paths, list):
            print(
                color(f"Invalid paths section: {self.config_file}", CLIStyle.COLORS["ERROR"]),
                file=sys.stderr,
            )
            return []

        entries: list[PathEntry] = []
        for item in paths:
            if isinstance(item, str) and item.strip():
                entries.append(PathEntry(path=clean_path(item)))
            elif isinstance(item, dict):
                path = item.get("path")
                raw_alias = item.get("alias")
                alias = normalize_alias(raw_alias) if isinstance(raw_alias, str) else None
                if isinstance(path, str) and path.strip():
                    entries.append(PathEntry(path=clean_path(path), alias=alias))
        return entries

    def config_data(self) -> dict[str, Any]:
        """Return JSON-serializable config data."""
        return {
            "version": CONFIG_VERSION,
            "paths": [entry.to_dict() for entry in self.entries],
        }

    def save_entries(self) -> None:
        """Save path entries to config file."""
        with open(self.config_file, "w", encoding="utf-8") as file:
            json.dump(self.config_data(), file, indent=4, ensure_ascii=False)

    def find_alias_index(self, alias: str) -> int | None:
        """Find an entry index by alias."""
        for index, entry in enumerate(self.entries):
            if entry.alias == alias:
                return index
        return None

    def resolve_target_index(self, target: str) -> int | None:
        """Resolve a number or alias target to an entry index."""
        path_number = parse_path_number(target)
        if path_number is not None:
            index = path_number - 1
            return index if 0 <= index < len(self.entries) else None

        alias = normalize_alias(target)
        if alias is None:
            return None
        return self.find_alias_index(alias)

    def resolve_path_index(self, path: str) -> int | None:
        """Resolve an exact path to an entry index."""
        normalized_path = normalize_path(path)
        for index, entry in enumerate(self.entries):
            if entry.path == normalized_path:
                return index
        return None

    def print_target_error(self, target: str) -> None:
        """Print a target resolution error."""
        if parse_path_number(target) is not None:
            print(
                f"{color('|', CLIStyle.COLORS['TITLE'])} Path number [{color(target, CLIStyle.COLORS['NUMBER'])}] out of range.",
                file=sys.stderr,
            )
        else:
            print(
                f"{color('|', CLIStyle.COLORS['TITLE'])} Path alias [{color(target, CLIStyle.COLORS['ALIAS'])}] doesn't exist.",
                file=sys.stderr,
            )

    def add_path(self, path: str, alias: str | None, path_color: int) -> int:
        """Add new path to the list."""
        normalized_path = normalize_path(path)
        normalized_alias = normalize_alias(alias)

        if normalized_alias is not None:
            if not is_valid_alias(normalized_alias):
                print(
                    f"{color('|', CLIStyle.COLORS['TITLE'])} Alias [{color(normalized_alias, CLIStyle.COLORS['ALIAS'])}] cannot be a command, numeric, start with '-', or contain path separators.",
                    file=sys.stderr,
                )
                return 1

            alias_index = self.find_alias_index(normalized_alias)
            if alias_index is not None and self.entries[alias_index].path != normalized_path:
                print(
                    f"{color('|', CLIStyle.COLORS['TITLE'])} Alias [{color(normalized_alias, CLIStyle.COLORS['ALIAS'])}] already exists.",
                    file=sys.stderr,
                )
                return 1

        path_index = self.resolve_path_index(normalized_path)
        if path_index is not None:
            entry = self.entries[path_index]
            if normalized_alias and entry.alias != normalized_alias:
                entry.alias = normalized_alias
                self.save_entries()
                print(
                    f"{color('|', CLIStyle.COLORS['TITLE'])} Alias [{color(normalized_alias, CLIStyle.COLORS['ALIAS'])}] set for [{color(entry.path, path_color)}]."
                )
                return 0

            print(
                f"{color('|', CLIStyle.COLORS['TITLE'])} Path [{color(normalized_path, path_color)}] already exists."
            )
            return 0

        self.entries.append(PathEntry(path=normalized_path, alias=normalized_alias))
        self.save_entries()
        alias_text = (
            f" as [{color(normalized_alias, CLIStyle.COLORS['ALIAS'])}]"
            if normalized_alias
            else ""
        )
        print(
            f"{color('|', CLIStyle.COLORS['TITLE'])} Path [{color(normalized_path, path_color)}] added{alias_text}."
        )
        return 0

    def remove_path(self, target: str, path_color: int) -> int:
        """Remove an entry by number, alias, or path."""
        index = self.resolve_target_index(target)
        if index is None and (os.path.sep in target or target.startswith(".")):
            index = self.resolve_path_index(target)

        if index is None:
            self.print_target_error(target)
            return 1

        entry = self.entries.pop(index)
        self.save_entries()
        print(
            f"{color('|', CLIStyle.COLORS['TITLE'])} Path [{color(entry.path, path_color)}] removed."
        )
        return 0

    def clean_paths(self, path_color: int) -> None:
        """Remove stored paths that no longer exist."""
        missing_entries = [entry for entry in self.entries if not os.path.exists(entry.path)]
        if not missing_entries:
            print(f"{color('|', CLIStyle.COLORS['TITLE'])} No missing paths found.")
            return

        self.entries = [entry for entry in self.entries if os.path.exists(entry.path)]
        self.save_entries()
        print(
            f"{color('|', CLIStyle.COLORS['TITLE'])} Removed {color(len(missing_entries), CLIStyle.COLORS['NUMBER'])} missing path(s)."
        )
        for entry in missing_entries:
            print(f"{color('|', CLIStyle.COLORS['TITLE'])} {color(entry.path, path_color)}")

    def move_path(self, from_num: int, to_num: int, path_color: int) -> int:
        """Move a stored path to another position."""
        path_count = len(self.entries)
        if from_num <= 0 or from_num > path_count:
            print(
                f"{color('|', CLIStyle.COLORS['TITLE'])} Source path number [{color(from_num, CLIStyle.COLORS['NUMBER'])}] out of range.",
                file=sys.stderr,
            )
            return 1

        if to_num <= 0 or to_num > path_count:
            print(
                f"{color('|', CLIStyle.COLORS['TITLE'])} Target path number [{color(to_num, CLIStyle.COLORS['NUMBER'])}] out of range.",
                file=sys.stderr,
            )
            return 1

        if from_num == to_num:
            entry = self.entries[from_num - 1]
            print(
                f"{color('|', CLIStyle.COLORS['TITLE'])} Path [{color(entry.path, path_color)}] already at position {color(to_num, CLIStyle.COLORS['NUMBER'])}."
            )
            return 0

        entry = self.entries.pop(from_num - 1)
        self.entries.insert(to_num - 1, entry)
        self.save_entries()
        print(
            f"{color('|', CLIStyle.COLORS['TITLE'])} Moved [{color(entry.path, path_color)}] from {color(from_num, CLIStyle.COLORS['NUMBER'])} to {color(to_num, CLIStyle.COLORS['NUMBER'])}."
        )
        return 0

    def format_entry(self, index: int, entry: PathEntry, path_color: int) -> str:
        """Format an entry for list output."""
        exists = "✓" if os.path.exists(entry.path) else "✗"
        status_color = (
            CLIStyle.COLORS["CONTENT"] if os.path.exists(entry.path) else CLIStyle.COLORS["ERROR"]
        )
        alias_text = (
            f" {color(entry.alias, CLIStyle.COLORS['ALIAS'])}"
            if entry.alias
            else ""
        )
        return (
            f"{color('|', CLIStyle.COLORS['TITLE'])} "
            f"[{color(index, CLIStyle.COLORS['NUMBER'])}] "
            f"{color(exists, status_color)}{alias_text} {color(entry.path, path_color)}"
        )

    def list_paths(self, target: str | None, path_color: int) -> int:
        """List all stored paths or a specific target."""
        if not self.entries:
            print(f"{color('|', CLIStyle.COLORS['TITLE'])} No stored paths.")
            return 0

        if target is not None:
            index = self.resolve_target_index(target)
            if index is None:
                self.print_target_error(target)
                return 1

            print(self.format_entry(index + 1, self.entries[index], path_color))
            return 0

        print(f"{color('Stored paths:', CLIStyle.COLORS['TITLE'])}")
        for index, entry in enumerate(self.entries, 1):
            print(self.format_entry(index, entry, path_color))
        return 0

    def output_path(self, target: str) -> int:
        """Output a raw path by number or alias for shell command substitution."""
        index = self.resolve_target_index(target)
        if index is None:
            self.print_target_error(target)
            return 1

        entry = self.entries[index]
        if not os.path.exists(entry.path):
            print(
                f"{color('|', CLIStyle.COLORS['TITLE'])} Warning: Path [{color(entry.path, CLIStyle.COLORS['PATH'])}] doesn't exist.",
                file=sys.stderr,
            )

        print(entry.path)
        return 0

    def show_config_path(self, path_color: int) -> None:
        """Show config file path."""
        print(color(self.config_file, path_color))

    def dump_config(self) -> None:
        """Show config file data."""
        print(json.dumps(self.config_data(), indent=4, ensure_ascii=False))


class ColoredArgumentParser(argparse.ArgumentParser):
    """Argument parser with colored help output."""

    def _format_action_invocation(self, action: argparse.Action) -> str:
        if not action.option_strings:
            (metavar,) = self._metavar_formatter(action, action.dest)(1)
            return metavar

        parts = []
        if action.nargs == 0:
            parts.extend(
                color(option_string, CLIStyle.COLORS["SUB_TITLE"])
                for option_string in action.option_strings
            )
        else:
            args_string = self._format_args(action, action.dest.upper())
            for option_string in action.option_strings:
                parts.append(
                    color(
                        f"{option_string} {args_string}",
                        CLIStyle.COLORS["SUB_TITLE"],
                    )
                )
        return ", ".join(parts)

    def format_help(self) -> str:
        formatter = self._get_formatter()
        if self.description:
            formatter.add_text(color(self.description, CLIStyle.COLORS["TITLE"]))
        formatter.add_usage(self.usage, self._actions, self._mutually_exclusive_groups)
        formatter.add_text(color("\nOptions:", CLIStyle.COLORS["TITLE"]))
        for action_group in self._action_groups:
            formatter.start_section(action_group.title)
            formatter.add_arguments(action_group._group_actions)
            formatter.end_section()
        if self.epilog:
            formatter.add_text(self.epilog)
        return formatter.format_help()


def create_example_text(script_name: str) -> str:
    """Create formatted example text for help menu."""
    examples = [
        ("List all paths", ""),
        ("List all paths explicitly", "list"),
        ("List all paths with alias command", "ls"),
        ("Add path", "add /path/to/sw"),
        ("Add path with alias", "add /tmp/tmp -a workspace"),
        ("Remove path by number", "rm 2"),
        ("Remove path by alias", "remove workspace"),
        ("Show raw path by number", "show 1"),
        ("Show raw path by alias", "s workspace"),
        ("Show raw path by alias shorthand", "workspace"),
        ("Clean missing paths", "clean"),
        ("Move path number 4 to position 1", "move 4 1"),
        ("Show config file path", "config"),
        ("Dump config JSON", "dump"),
    ]

    notes = [
        "If the first argument is not a command, it is treated as show TARGET.",
        "show/s prints only the resolved path, suitable for command substitution.",
        "Targets can be an existing path number or alias.",
        "Alias names cannot be commands, numeric, start with '-', or contain path separators.",
    ]

    text = f"\n{color('Examples:', CLIStyle.COLORS['SUB_TITLE'])}"
    for desc, cmd in examples:
        text += f"\n  {color(f'# {desc}', CLIStyle.COLORS['EXAMPLE'])}"
        text += f"\n  {color(f'{script_name} {cmd}'.rstrip(), CLIStyle.COLORS['CONTENT'])}\n"

    text += f"\n{color('Notes:', CLIStyle.COLORS['SUB_TITLE'])}"
    for note in notes:
        text += f"\n  {color(f'- {note}', CLIStyle.COLORS['CONTENT'])}"

    return text


def add_target_argument(parser: argparse.ArgumentParser) -> None:
    """Add common target argument."""
    parser.add_argument(
        "target",
        metavar=color("TARGET", CLIStyle.COLORS["WARNING"]),
        help=color("Existing path number or alias", CLIStyle.COLORS["CONTENT"]),
    )


def create_parser() -> argparse.ArgumentParser:
    """Create command line parser."""
    script_name = os.path.basename(sys.argv[0])
    parser = ColoredArgumentParser(
        description="LCD - Path Manager, store and quickly access common paths",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=create_example_text(script_name),
    )
    parser.add_argument(
        "-p",
        "--plain",
        action="store_true",
        help=color("Do not color human-readable output", CLIStyle.COLORS["CONTENT"]),
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"%(prog)s {VERSION}",
        help=color("Show program version", CLIStyle.COLORS["CONTENT"]),
    )

    subparsers = parser.add_subparsers(
        dest="command",
        metavar="{list|ls|l,add,rm|remove,show|s,clean,move,config,dump}",
        help="Commands",
    )

    list_parser = subparsers.add_parser(
        "list",
        aliases=["ls", "l"],
        help=color("List stored paths", CLIStyle.COLORS["CONTENT"]),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    list_parser.add_argument(
        "target",
        nargs="?",
        default=None,
        metavar=color("TARGET", CLIStyle.COLORS["WARNING"]),
        help=color("Optional path number or alias", CLIStyle.COLORS["CONTENT"]),
    )

    add_parser = subparsers.add_parser(
        "add",
        help=color("Add a path", CLIStyle.COLORS["CONTENT"]),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    add_parser.add_argument(
        "path",
        nargs="?",
        default=os.getcwd(),
        metavar=color("PATH", CLIStyle.COLORS["WARNING"]),
        help=color("Path to add, default is current directory", CLIStyle.COLORS["CONTENT"]),
    )
    add_parser.add_argument(
        "-a",
        "--alias",
        metavar=color("NAME", CLIStyle.COLORS["WARNING"]),
        help=color("Alias to assign to this path", CLIStyle.COLORS["CONTENT"]),
    )

    remove_parser = subparsers.add_parser(
        "rm",
        aliases=["remove"],
        help=color("Remove a stored path", CLIStyle.COLORS["CONTENT"]),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    add_target_argument(remove_parser)

    show_parser = subparsers.add_parser(
        "show",
        aliases=["s"],
        help=color("Print a resolved path", CLIStyle.COLORS["CONTENT"]),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    add_target_argument(show_parser)

    clean_parser = subparsers.add_parser(
        "clean",
        help=color("Remove missing paths", CLIStyle.COLORS["CONTENT"]),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    clean_parser.set_defaults(command="clean")

    move_parser = subparsers.add_parser(
        "move",
        help=color("Move a path to another position", CLIStyle.COLORS["CONTENT"]),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    move_parser.add_argument(
        "from_num",
        type=int,
        metavar=color("FROM", CLIStyle.COLORS["WARNING"]),
        help=color("Source path number", CLIStyle.COLORS["CONTENT"]),
    )
    move_parser.add_argument(
        "to_num",
        type=int,
        metavar=color("TO", CLIStyle.COLORS["WARNING"]),
        help=color("Target path number", CLIStyle.COLORS["CONTENT"]),
    )

    subparsers.add_parser(
        "config",
        help=color("Show config file path", CLIStyle.COLORS["CONTENT"]),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers.add_parser(
        "dump",
        help=color("Dump config JSON", CLIStyle.COLORS["CONTENT"]),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    return parser


def normalize_args_for_target_fallback(args: list[str]) -> list[str]:
    """Treat a non-command first positional argument as show TARGET."""
    if not args:
        return args

    if args[0].startswith("-") or args[0] in COMMAND_NAMES:
        return args

    return ["show", *args]


def main() -> int:
    """Main program logic."""
    parser = create_parser()
    args = parser.parse_args(normalize_args_for_target_fallback(sys.argv[1:]))

    path_color = 0 if args.plain else CLIStyle.COLORS["PATH"]
    path_manager = PathManager(CONFIG_FILE)

    if args.command is None:
        return path_manager.list_paths(None, path_color)
    if args.command in ("list", "ls", "l"):
        return path_manager.list_paths(args.target, path_color)
    if args.command == "add":
        return path_manager.add_path(args.path, args.alias, path_color)
    if args.command in ("rm", "remove"):
        return path_manager.remove_path(args.target, path_color)
    if args.command in ("show", "s"):
        return path_manager.output_path(args.target)
    if args.command == "clean":
        path_manager.clean_paths(path_color)
        return 0
    if args.command == "move":
        return path_manager.move_path(args.from_num, args.to_num, path_color)
    if args.command == "config":
        path_manager.show_config_path(path_color)
        return 0
    if args.command == "dump":
        path_manager.dump_config()
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(color("\nOperation cancelled by user", CLIStyle.COLORS["ERROR"]))
        sys.exit(0)
    except Exception as e:
        print(color(f"\nError: {str(e)}", CLIStyle.COLORS["ERROR"]))
        sys.exit(1)
