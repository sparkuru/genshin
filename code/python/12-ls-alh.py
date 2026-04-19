# -*- coding: utf-8 -*-
# pip install colorama argparse

import argparse
import ctypes
import inspect
import os
import re
import shutil
import sys
import traceback
from datetime import datetime
from typing import Any

from colorama import Fore, Style, init as colorama_init

if sys.platform == "win32":
    colorama_init(autoreset=True)

if sys.platform != "win32":
    import grp
    import pwd
else:
    class _PwdModule:
        """Fallback pwd module for Windows."""

        def getpwuid(self, uid: int) -> Any:
            """Return a simple owner object for Windows."""

            class _Passwd:
                def __init__(self) -> None:
                    self.pw_name = "Unknown"

            return _Passwd()

    class _GrpModule:
        """Fallback grp module for Windows."""

        def getgrgid(self, gid: int) -> Any:
            """Return a simple group object for Windows."""

            class _Group:
                def __init__(self) -> None:
                    self.gr_name = "Unknown"

            return _Group()

    pwd = _PwdModule()
    grp = _GrpModule()


DEBUG_MODE = False
VERSION = "1.2.1"
DEFAULT_PATH = "."
DEFAULT_SORT = "name"
DEFAULT_DETAIL_LEVEL = 1
DEFAULT_DECIMAL_PLACES = 2
MODE_WIDTH = 5
SIZE_WIDTH = 10
USER_WIDTH = 8
GROUP_WIDTH = 8
TIME_WIDTH = 20
NAME_WIDTH = 40
NAME_PADDING = 4


class CLIStyle:
    """CLI tool unified style config."""

    COLORS = {
        "TITLE": 7,
        "SUB_TITLE": 2,
        "CONTENT": 3,
        "EXAMPLE": 7,
        "WARNING": 4,
        "ERROR": 2,
        "DIR": 4,
        "FILE": 5,
        "HIDDEN": 2,
        "HEADER": 3,
        "STATS_DIR": 7,
        "STATS_FILE": 5,
        "STATS_HIDDEN": 2,
        "STATS_SIZE": 3,
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
    """Argument parser with colored help output."""

    def _format_action_invocation(self, action: argparse.Action) -> str:
        """Format argument invocation with CLI colors."""
        if not action.option_strings:
            (metavar,) = self._metavar_formatter(action, action.dest)(1)
            return CLIStyle.color(metavar, CLIStyle.COLORS["SUB_TITLE"])

        parts: list[str] = []
        if action.nargs == 0:
            parts.extend(
                CLIStyle.color(option, CLIStyle.COLORS["SUB_TITLE"])
                for option in action.option_strings
            )
        else:
            args_string = self._format_args(action, action.dest.upper())
            for option in action.option_strings:
                parts.append(
                    CLIStyle.color(
                        f"{option} {args_string}",
                        CLIStyle.COLORS["SUB_TITLE"],
                    )
                )
        return ", ".join(parts)

    def format_help(self) -> str:
        """Render colored help text."""
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


def write_output(text: str = "") -> None:
    """Write a line to stdout."""
    print(text)


def write_error(message: str) -> None:
    """Write an error line with standard styling."""
    write_output(CLIStyle.color(message, CLIStyle.COLORS["ERROR"]))


def write_warning(message: str) -> None:
    """Write a warning line with standard styling."""
    write_output(CLIStyle.color(message, CLIStyle.COLORS["WARNING"]))


def debug(*args: Any, file: str | None = None, append: bool = True, **kwargs: Any) -> None:
    """
    Print the arguments with their file and line number.
    ```python
    debug("Hello", "World", file="debug.log", append=False)

    return = None
    ```
    """
    if not DEBUG_MODE:
        return

    frame = inspect.currentframe()
    caller_frame = frame.f_back if frame is not None else None
    if caller_frame is None:
        return

    info = inspect.getframeinfo(caller_frame)
    output = (
        f"{CLIStyle.color(os.path.basename(info.filename), 3)}: "
        f"{CLIStyle.color(str(info.lineno), 4)} "
        f"{CLIStyle.color('|', 7)} "
    )

    for arg in args:
        output += f"{CLIStyle.color(str(arg), 2)} "

    for key, value in kwargs.items():
        output += (
            f"{CLIStyle.color(f'{key}=', 6)}"
            f"{CLIStyle.color(str(value), 2)} "
        )

    output += "\n"

    if file is not None:
        file_mode = "a" if append else "w"
        with open(file, file_mode, encoding="utf-8") as file_handle:
            clean_output = re.sub(r"\033\[\d+;\d+m|\033\[0m", "", output)
            file_handle.write(clean_output)
        return

    print(output, end="")


def create_example_text(
    script_name: str,
    examples: list[tuple[str, str]],
    notes: list[str] | None = None,
) -> str:
    """Create the formatted examples section for help output."""
    text = f"\n{CLIStyle.color('Examples:', CLIStyle.COLORS['SUB_TITLE'])}"
    for description, command in examples:
        text += (
            f"\n  {CLIStyle.color(f'# {description}', CLIStyle.COLORS['EXAMPLE'])}"
        )
        text += (
            f"\n  {CLIStyle.color(f'{script_name} {command}'.rstrip(), CLIStyle.COLORS['CONTENT'])}\n"
        )

    if notes:
        text += f"\n{CLIStyle.color('Notes:', CLIStyle.COLORS['SUB_TITLE'])}"
        for note in notes:
            text += f"\n  {CLIStyle.color(f'- {note}', CLIStyle.COLORS['CONTENT'])}"

    return text


def human_readable_size(
    size: int,
    decimal_places: int = DEFAULT_DECIMAL_PLACES,
) -> str:
    """Convert file size to human readable format."""
    value = float(size)
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if abs(value) < 1024.0 or unit == "TB":
            return f"{value:>{decimal_places + 4}.{decimal_places}f} {unit}"
        value /= 1024.0
    return f"{value:>{decimal_places + 4}.{decimal_places}f} TB"


def is_hidden(path: str) -> bool:
    """Check whether the target path is hidden."""
    if sys.platform == "win32":
        try:
            attributes = ctypes.windll.kernel32.GetFileAttributesW(path)
            return attributes != -1 and bool(attributes & 2)
        except AttributeError:
            return False
    return os.path.basename(path).startswith(".")


def get_terminal_width() -> int:
    """Get terminal width."""
    return shutil.get_terminal_size(fallback=(80, 24)).columns


def natural_sort_key(text: str) -> list[Any]:
    """Generate a natural sort key."""
    return [
        int(item) if item.isdigit() else item.lower()
        for item in re.split(r"(\d+)", text)
    ]


class PathEntryAdapter:
    """Adapter that provides a DirEntry-like interface for one path."""

    def __init__(self, path: str) -> None:
        """Initialize a path adapter."""
        normalized_path = os.path.normpath(path)
        self.path = path
        self.name = os.path.basename(normalized_path) or normalized_path

    def is_dir(self) -> bool:
        """Return whether the path is a directory."""
        return os.path.isdir(self.path)

    def stat(self) -> os.stat_result:
        """Return file status."""
        return os.stat(self.path)


class FileFormatter:
    """Format rows, headers, and statistics for display."""

    def __init__(self, plain_output: bool = False, show_owner: bool = False) -> None:
        """Initialize the file formatter."""
        self.plain_output = plain_output
        self.show_owner = show_owner
        self.can_show_owner = sys.platform != "win32"

    def format_mode(self, entry: Any) -> str:
        """Format the mode column."""
        mode = "d" if entry.is_dir() else "-"
        mode += "r" if os.access(entry.path, os.R_OK) else "-"
        mode += "w" if os.access(entry.path, os.W_OK) else "-"
        mode += "x" if os.access(entry.path, os.X_OK) else "-"
        return mode

    def format_size(self, entry: Any) -> str:
        """Format the size column."""
        if entry.is_dir():
            return ""
        return human_readable_size(entry.stat().st_size)

    def format_time(self, entry: Any) -> str:
        """Format the last modified time column."""
        return datetime.fromtimestamp(entry.stat().st_mtime).strftime(
            "%Y/%m/%d %H:%M:%S"
        )

    def format_owner(self, entry: Any) -> tuple[str, str]:
        """Format user and group columns."""
        if not self.show_owner or not self.can_show_owner:
            return "", ""

        try:
            stat_info = entry.stat()
            return (
                pwd.getpwuid(stat_info.st_uid).pw_name,
                grp.getgrgid(stat_info.st_gid).gr_name,
            )
        except (AttributeError, ImportError, KeyError):
            return "", ""

    def get_name_style(self, entry: Any) -> tuple[int, str]:
        """Return name color and display text."""
        hidden = is_hidden(entry.path)
        if hidden:
            name = f"{entry.name} [hide]" if not self.plain_output else entry.name
            return CLIStyle.COLORS["HIDDEN"], name
        if entry.is_dir():
            return CLIStyle.COLORS["DIR"], entry.name
        return CLIStyle.COLORS["FILE"], entry.name

    def _base_row(
        self,
        entry: Any,
        mode_width: int,
        size_width: int,
        user_width: int,
        group_width: int,
        time_width: int,
        name_width: int,
    ) -> str:
        """Build the plain row text before color application."""
        mode = self.format_mode(entry)
        size = self.format_size(entry)
        _, name = self.get_name_style(entry)
        modified_time = self.format_time(entry)
        user, group = self.format_owner(entry)

        row = f"{mode:<{mode_width}} {size:<{size_width}} "
        if self.show_owner and self.can_show_owner:
            row += f"{user:<{user_width}} {group:<{group_width}} "
        row += f"{modified_time:<{time_width}} {name:<{name_width}}"
        return row

    def format_row(
        self,
        entry: Any,
        mode_width: int = MODE_WIDTH,
        size_width: int = SIZE_WIDTH,
        user_width: int = USER_WIDTH,
        group_width: int = GROUP_WIDTH,
        time_width: int = TIME_WIDTH,
        name_width: int = NAME_WIDTH,
    ) -> str:
        """Format one display row."""
        row = self._base_row(
            entry,
            mode_width,
            size_width,
            user_width,
            group_width,
            time_width,
            name_width,
        )
        if self.plain_output:
            return row

        color_code, _ = self.get_name_style(entry)
        return CLIStyle.color(row, color_code)

    def format_header(
        self,
        mode_width: int = MODE_WIDTH,
        size_width: int = SIZE_WIDTH,
        user_width: int = USER_WIDTH,
        group_width: int = GROUP_WIDTH,
        time_width: int = TIME_WIDTH,
        name_width: int = NAME_WIDTH,
    ) -> str:
        """Format the header row."""
        row = f"{'Mode':<{mode_width}} {'Size':<{size_width}} "
        if self.show_owner and self.can_show_owner:
            row += f"{'User':<{user_width}} {'Group':<{group_width}} "
        row += f"{'Last Modified':<{time_width}} {'Name':<{name_width}}"

        if self.plain_output:
            return row
        return CLIStyle.color(row, CLIStyle.COLORS["HEADER"])

    def format_stats(
        self,
        total_dirs: int,
        total_files: int,
        hidden_count: int,
        total_size: int,
    ) -> str:
        """Format the statistics block."""
        if self.plain_output:
            stats = [
                f"Dirs: {total_dirs}",
                f"Files: {total_files}",
                f"Hidden: {hidden_count}",
                f"Total Size: {human_readable_size(total_size)}",
            ]
        else:
            stats = [
                f"{CLIStyle.color('Dirs:', CLIStyle.COLORS['STATS_DIR'])} {total_dirs}",
                f"{CLIStyle.color('Files:', CLIStyle.COLORS['STATS_FILE'])} {total_files}",
                f"{CLIStyle.color('Hidden:', CLIStyle.COLORS['STATS_HIDDEN'])} {hidden_count}",
                (
                    f"{CLIStyle.color('Total Size:', CLIStyle.COLORS['STATS_SIZE'])} "
                    f"{human_readable_size(total_size)}"
                ),
            ]
        return "\n" + " | ".join(stats)


class DirectoryLister:
    """List one directory or one file target."""

    def __init__(
        self,
        path: str = DEFAULT_PATH,
        show_all: bool = False,
        sort_by: str = DEFAULT_SORT,
        plain_output: bool = False,
        detail_level: int = DEFAULT_DETAIL_LEVEL,
        show_owner: bool = False,
    ) -> None:
        """Initialize the directory lister."""
        self.path = path
        self.show_all = show_all
        self.sort_by = sort_by
        self.plain_output = plain_output
        self.detail_level = detail_level
        self.show_owner = show_owner
        self.single_target = False
        self.formatter = FileFormatter(
            plain_output=plain_output,
            show_owner=show_owner,
        )
        self.total_files = 0
        self.total_dirs = 0
        self.total_size = 0
        self.hidden_count = 0

    def _emit_error(self, message: str) -> None:
        """Emit an error according to the current output mode."""
        if self.plain_output:
            write_output(message)
            return
        write_error(message)

    def _sort_key(self, entry: Any) -> tuple[Any, ...]:
        """Build a stable directory-first sort key."""
        is_file = not entry.is_dir()
        stat_info = entry.stat()
        name_key = natural_sort_key(entry.name)

        if self.sort_by == "size":
            return (is_file, -stat_info.st_size, name_key)
        if self.sort_by == "time":
            return (is_file, -stat_info.st_mtime, name_key)
        return (is_file, name_key)

    def get_entries(self) -> list[Any]:
        """Get entries for either a directory target or a single file target."""
        try:
            if os.path.isfile(self.path):
                self.single_target = True
                return [PathEntryAdapter(self.path)]

            if not os.path.isdir(self.path):
                raise NotADirectoryError(self.path)

            with os.scandir(self.path) as scanner:
                entries = list(scanner)
            return sorted(entries, key=self._sort_key)
        except FileNotFoundError:
            self._emit_error(f"Error: Path '{self.path}' does not exist")
            return []
        except PermissionError:
            self._emit_error(f"Error: No permission to access '{self.path}'")
            return []
        except NotADirectoryError:
            self._emit_error(
                f"Error: Path '{self.path}' is not a directory or regular file"
            )
            return []
        except Exception as error:
            self._emit_error(f"Error: {str(error)}")
            return []

    def process_entry(self, entry: Any) -> bool:
        """Update statistics and decide whether the entry should be displayed."""
        if is_hidden(entry.path):
            self.hidden_count += 1
            if not self.show_all and not self.single_target:
                return False

        if entry.is_dir():
            self.total_dirs += 1
        else:
            self.total_files += 1
            self.total_size += entry.stat().st_size

        return True

    def display_detailed_list(self, entries: list[Any]) -> None:
        """Display a detailed listing."""
        write_output(
            self.formatter.format_header(
                MODE_WIDTH,
                SIZE_WIDTH,
                USER_WIDTH,
                GROUP_WIDTH,
                TIME_WIDTH,
                NAME_WIDTH,
            )
        )

        for entry in entries:
            if not self.process_entry(entry):
                continue
            write_output(
                self.formatter.format_row(
                    entry,
                    MODE_WIDTH,
                    SIZE_WIDTH,
                    USER_WIDTH,
                    GROUP_WIDTH,
                    TIME_WIDTH,
                    NAME_WIDTH,
                )
            )

    def display_simple_list(self, entries: list[Any]) -> None:
        """Display a compact listing."""
        visible_entries = [
            entry
            for entry in entries
            if self.process_entry(entry)
        ]
        if not visible_entries:
            return

        max_name_length = max(len(entry.name) for entry in visible_entries) + NAME_PADDING
        columns = max(1, get_terminal_width() // max_name_length)
        row: list[str] = []

        for index, entry in enumerate(visible_entries, start=1):
            color_code, name = self.formatter.get_name_style(entry)
            if self.plain_output:
                row.append(f"{name:<{max_name_length}}")
            else:
                row.append(
                    CLIStyle.color(f"{name:<{max_name_length}}", color_code)
                )

            if index % columns == 0:
                write_output("".join(row))
                row = []

        if row:
            write_output("".join(row))

    def list_target(self) -> int:
        """List directory or file content and print statistics."""
        entries = self.get_entries()
        if not entries:
            return 1

        if self.detail_level == 0:
            self.display_simple_list(entries)
        else:
            self.display_detailed_list(entries)

        write_output(
            self.formatter.format_stats(
                self.total_dirs,
                self.total_files,
                self.hidden_count,
                self.total_size,
            )
        )
        return 0


def build_examples(script_name: str) -> str:
    """Build help examples and notes."""
    examples = [
        ("List current directory", ""),
        ("List all files including hidden", "-a"),
        ("List a specific directory", "/path/to/dir"),
        ("List a specific file", "/path/to/file"),
        ("Sort entries by size", "-s size"),
        ("Sort entries by modification time", "-s time"),
        ("Use simple display mode", "-l 0"),
        ("Show owner and group on Unix-like systems", "-o"),
        ("Disable colors", "-p"),
        ("Enable debug logging", "--log"),
    ]
    notes = [
        "PATH accepts either a directory or a file.",
        "Directories always appear before regular files.",
        "The -a/--all option shows hidden files in directory listings.",
        "A hidden file passed as PATH is still shown explicitly.",
        "The -l/--level option supports 0 for simple and 1 for detailed output.",
    ]
    return create_example_text(script_name, examples, notes)


def build_parser() -> ColoredArgumentParser:
    """Build the CLI argument parser."""
    script_name = os.path.basename(sys.argv[0])
    parser = ColoredArgumentParser(
        prog=script_name,
        description="ls-alh - Enhanced directory listing with colors and statistics",
        epilog=build_examples(script_name),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument(
        "path",
        nargs="?",
        default=None,
        metavar=CLIStyle.color("PATH", CLIStyle.COLORS["SUB_TITLE"]),
        help=CLIStyle.color(
            "File or directory to list (default: current directory)",
            CLIStyle.COLORS["CONTENT"],
        ),
    )
    parser.add_argument(
        "-a",
        "--all",
        action="store_true",
        help=CLIStyle.color(
            "Show all files including hidden files",
            CLIStyle.COLORS["CONTENT"],
        ),
    )
    parser.add_argument(
        "-s",
        "--sort",
        choices=["name", "size", "time"],
        default=DEFAULT_SORT,
        metavar=CLIStyle.color("SORT", CLIStyle.COLORS["SUB_TITLE"]),
        help=CLIStyle.color(
            "Sort by name, size, or time (default: name)",
            CLIStyle.COLORS["CONTENT"],
        ),
    )
    parser.add_argument(
        "-l",
        "--level",
        type=int,
        choices=[0, 1],
        default=DEFAULT_DETAIL_LEVEL,
        metavar=CLIStyle.color("LEVEL", CLIStyle.COLORS["SUB_TITLE"]),
        help=CLIStyle.color(
            "Detail level (0=simple, 1=detailed)",
            CLIStyle.COLORS["CONTENT"],
        ),
    )
    parser.add_argument(
        "-o",
        "--owner",
        action="store_true",
        help=CLIStyle.color(
            "Show owner and group information (Unix/Linux only)",
            CLIStyle.COLORS["CONTENT"],
        ),
    )
    parser.add_argument(
        "-p",
        "--plain",
        action="store_true",
        help=CLIStyle.color(
            "Plain output without colors",
            CLIStyle.COLORS["CONTENT"],
        ),
    )
    parser.add_argument(
        "--log",
        "--debug",
        dest="log",
        action="store_true",
        help=CLIStyle.color(
            "Enable debug mode",
            CLIStyle.COLORS["CONTENT"],
        ),
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"%(prog)s {VERSION}",
        help=CLIStyle.color(
            "Show program version",
            CLIStyle.COLORS["CONTENT"],
        ),
    )
    return parser


def resolve_target_path(args: argparse.Namespace) -> str:
    """Resolve PATH into the final target path."""
    if args.path is None:
        return DEFAULT_PATH
    return args.path


def main() -> int:
    """Main program logic."""
    parser = build_parser()
    args = parser.parse_args()

    global DEBUG_MODE
    DEBUG_MODE = args.log
    if DEBUG_MODE:
        debug("Debug mode enabled", target=resolve_target_path(args))

    if args.owner and sys.platform == "win32":
        write_warning("Warning: Owner/group display is not supported on Windows")

    lister = DirectoryLister(
        path=resolve_target_path(args),
        show_all=args.all,
        sort_by=args.sort,
        plain_output=args.plain,
        detail_level=args.level,
        show_owner=args.owner,
    )
    return lister.list_target()


if __name__ == "__main__":
    try:
        sys.exit(main())
    except FileNotFoundError as error:
        write_error(f"Error: File not found: {str(error)}")
        sys.exit(1)
    except KeyboardInterrupt:
        write_error("Operation cancelled by user")
        sys.exit(0)
    except Exception as error:
        if DEBUG_MODE:
            traceback.print_exc()
        write_error(f"Error: {str(error)}")
        sys.exit(1)
