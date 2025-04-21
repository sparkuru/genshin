# -*- coding: utf-8 -*-
# pip install argparse rich

import os
import sys
import argparse
import re
import shutil
import signal
from rich.console import Console
from rich.panel import Panel

# Global variables
DEBUG_MODE = False
WORK_DIR = os.getcwd()
VERSION = "1.1.5"
SHOULD_EXIT = False

# File extensions
VIDEO_EXTENSIONS = (
    ".mp4",
    ".flv",
    ".wmv",
    ".avi",
    ".webm",
    "3gp",
    ".mpg",
    ".mov",
    ".rm",
    ".rmvb",
    ".mkv",
)

IMAGE_EXTENSIONS = (".jpg", ".png", ".jpeg", ".bmp")

# Files to ignore
IGNORE_FILES = [
    "desktop.ini",
    "Thumbs.db",
    "._.DS_Store",
    ".DS_Store",
    "._.localized",
    ".localized",
    "._",
    ".git",
    ".gitignore",
    ".gitattributes",
    ".vscode",
    "__pycache__",
]

SCRIPT_IGNORE_FILES = ["rename.py", "tools.py", "interact-rename.py"]

# CLI colors
CLI_COLORS = {
    "TITLE": 7,  # Cyan - Main title
    "SUB_TITLE": 2,  # Red - Subtitle
    "CONTENT": 3,  # Green - Normal content
    "EXAMPLE": 7,  # Cyan - Examples
    "WARNING": 4,  # Yellow - Warnings
    "ERROR": 2,  # Red - Errors
}


def natural_sort_key(s):
    """
    Natural sort key function for sorting strings with embedded numbers.
    This function will sort strings in a human intuitive way:
    e.g. ["1.txt", "2.txt", "10.txt"] instead of ["1.txt", "10.txt", "2.txt"]

    Args:
        s (str): String to convert to natural sort key

    Returns:
        list: A list of string and integer chunks that can be used as a sort key
    """
    return [
        int(text) if text.isdigit() else text.lower() for text in re.split(r"(\d+)", s)
    ]


class FileType:
    VIDEO = "video"
    IMAGE = "image"

    EXTENSIONS = {VIDEO: VIDEO_EXTENSIONS, IMAGE: IMAGE_EXTENSIONS}

    DEFAULT_OUTPUT = {VIDEO: ".mp4", IMAGE: ".png"}

    @classmethod
    def get_extensions(cls, file_type: str) -> tuple:
        return cls.EXTENSIONS.get(file_type, ())

    @classmethod
    def get_default_ext(cls, file_type: str) -> str:
        return cls.DEFAULT_OUTPUT.get(file_type, "")


def color(text: str, color_code: int = 0) -> str:
    color_table = {
        0: "{}",  # No color
        1: "\033[1;30m{}\033[0m",  # Bold black
        2: "\033[1;31m{}\033[0m",  # Bold red
        3: "\033[1;32m{}\033[0m",  # Bold green
        4: "\033[1;33m{}\033[0m",  # Bold yellow
        5: "\033[1;34m{}\033[0m",  # Bold blue
        6: "\033[1;35m{}\033[0m",  # Bold purple
        7: "\033[1;36m{}\033[0m",  # Bold cyan
        8: "\033[1;37m{}\033[0m",  # Bold white
    }
    return color_table[color_code].format(text)


def debug(*args, file=None, append=True, **kwargs):
    if not DEBUG_MODE:
        return

    import inspect

    frame = inspect.currentframe().f_back
    info = inspect.getframeinfo(frame)

    output = f"{color(os.path.basename(info.filename), 3)}: {color(info.lineno, 4)} {color('|', 7)} "

    for i, arg in enumerate(args):
        arg_str = str(arg)
        output += f"{color(arg_str, 2)} "

    for k, v in kwargs.items():
        output += f"{color(k + '=', 6)}{color(str(v), 2)} "

    output += "\n"

    if file:
        mode = "a" if append else "w"
        with open(file, mode) as f:
            clean_output = re.sub(r"\033\[\d+;\d+m|\033\[0m", "", output)
            f.write(clean_output)
    else:
        print(output, end="")


def divider(text: str = False, char: str = "=") -> None:
    divider_str = char * 10
    print(
        f"{color(divider_str, 5)} {text if text else 'Divider'} {color(divider_str, 5)}"
    )


class FileRenamer:
    def __init__(self, directory: str):
        self.directory = directory
        self.console = Console()
        self.total_files = 0
        self.modified_files = 0
        # Setup signal handler
        signal.signal(signal.SIGINT, self._signal_handler)

    def _signal_handler(self, signum, frame):
        global SHOULD_EXIT
        SHOULD_EXIT = True
        print("\nSafely exiting...")

    def _show_statistics(self) -> None:
        print()  # Empty line for better readability
        print(
            f"{color('Total Files', CLI_COLORS['SUB_TITLE'])}: {color(str(self.total_files), CLI_COLORS['CONTENT'])} | {color('Modified Files', CLI_COLORS['SUB_TITLE'])}: {color(str(self.modified_files), CLI_COLORS['CONTENT'])}"
        )

    def is_ignored(self, filename: str, ignore_list: list) -> bool:
        return filename in ignore_list

    def get_file_list(self, include_dirs: bool = False) -> list:
        files = [
            f
            for f in os.listdir(self.directory)
            if os.path.isfile(os.path.join(self.directory, f))
            or (include_dirs and os.path.isdir(os.path.join(self.directory, f)))
        ]
        # Use natural sort
        files.sort(key=natural_sort_key)
        file_list = [
            f
            for f in files
            if not self.is_ignored(f, IGNORE_FILES + SCRIPT_IGNORE_FILES)
        ]
        self.total_files = len(file_list)
        return file_list

    def show_files(self, file_list: list) -> None:
        divider("Files in workspace")
        for filename in file_list:
            print(color(filename, CLI_COLORS["CONTENT"]))
        print()

    def _move_file(
        self,
        src: str,
        dst: str,
        show_progress: bool = False,
        current: int = 0,
        total: int = 0,
        count_as_modified: bool = True,
    ) -> bool:
        if SHOULD_EXIT:
            return False

        try:
            if show_progress:
                self._show_progress(current, total, "Renaming: ")

            # Check file size
            file_size = os.path.getsize(src)
            is_large_file = file_size > 100 * 1024 * 1024  # Files larger than 100MB

            if is_large_file:
                print(
                    f"\nProcessing large file: {os.path.basename(src)} ({file_size / (1024 * 1024):.1f}MB)"
                )

            try:
                os.rename(src, dst)
            except OSError:
                if is_large_file:
                    print(
                        "Using alternative method for large file, this may take longer..."
                    )
                shutil.move(src, dst)

            # Only increment counter if requested
            if count_as_modified:
                self.modified_files += 1

            return True

        except OSError as e:
            print(color(f"Error moving file: {str(e)}", CLI_COLORS["ERROR"]))
            return False
        except Exception as e:
            print(color(f"Unexpected error: {str(e)}", CLI_COLORS["ERROR"]))
            return False

    def fast_rename(self, file_type: str, width: int = 3) -> None:
        if file_type not in [FileType.VIDEO, FileType.IMAGE]:
            print(
                color(
                    f"Error: type must be '{FileType.VIDEO}' or '{FileType.IMAGE}'",
                    CLI_COLORS["ERROR"],
                )
            )
            return

        extensions = FileType.get_extensions(file_type)
        if not extensions:
            print(
                color(
                    f"Error: No extensions defined for type '{file_type}'",
                    CLI_COLORS["ERROR"],
                )
            )
            return

        files = []
        for ext in extensions:
            files.extend(
                [f for f in os.listdir(self.directory) if f.lower().endswith(ext)]
            )

        if not files:
            print(
                color(f"No {file_type} files found in directory", CLI_COLORS["WARNING"])
            )
            return

        # Use natural sort
        files.sort(key=natural_sort_key)
        default_ext = FileType.get_default_ext(file_type)
        self.modified_files = 0

        # Preview changes to be made
        changes = []
        for index, filename in enumerate(files, 1):
            new_name = f"{str(index).zfill(width)}{default_ext}"
            if new_name == filename:
                continue

            # Check if target file already exists
            dst = os.path.join(self.directory, new_name)
            if os.path.exists(dst) and dst != os.path.join(self.directory, filename):
                print(
                    color(
                        f"Warning: '{new_name}' already exists, will be skipped",
                        CLI_COLORS["WARNING"],
                    )
                )
                continue

            changes.append((filename, new_name))
            print(f"{filename} => {color(new_name, CLI_COLORS['CONTENT'])}")

        if not changes:
            print(color("No files need to be renamed", CLI_COLORS["WARNING"]))
            return

        # Request user confirmation
        if self._confirm_changes(file_count=len(changes)):
            # Apply changes
            for old_name, new_name in changes:
                src = os.path.join(self.directory, old_name)
                dst = os.path.join(self.directory, new_name)
                self._move_file(src, dst)

            divider("Changes confirmed")
            self._show_statistics()
        else:
            divider("Changes cancelled")

    def prefix_rename(
        self, file_list: list, width: int = 3, mode: str = "add", start_num: int = 1
    ) -> None:
        if not file_list:
            print(color("No files to process", CLI_COLORS["WARNING"]))
            return

        if mode not in ["add", "remove"]:
            print(color("Error: mode must be 'add' or 'remove'", CLI_COLORS["ERROR"]))
            return

        changes = []  # Store changes to apply them after preview
        self.modified_files = 0

        if mode == "add":
            # First check for potential conflicts
            for index, filename in enumerate(file_list, start_num):
                new_name = f"{str(index).zfill(width)}-{filename}"
                dst = os.path.join(self.directory, new_name)

                if os.path.exists(dst) and dst != os.path.join(
                    self.directory, filename
                ):
                    print(
                        color(
                            f"Error: '{new_name}' already exists", CLI_COLORS["ERROR"]
                        )
                    )
                    return

                changes.append((filename, new_name))
                print(f"{filename} => {color(new_name, CLI_COLORS['CONTENT'])}")
        else:
            # Remove mode
            prefix_pattern = re.compile(r"^\d{%d,}-(.*)$" % width)
            for filename in file_list:
                match = prefix_pattern.match(filename)
                if match:
                    new_name = match.group(1)
                    dst = os.path.join(self.directory, new_name)

                    if os.path.exists(dst) and dst != os.path.join(
                        self.directory, filename
                    ):
                        print(
                            color(
                                f"Error: '{new_name}' already exists",
                                CLI_COLORS["ERROR"],
                            )
                        )
                        return

                    changes.append((filename, new_name))
                    print(f"{filename} => {color(new_name, CLI_COLORS['CONTENT'])}")

        if not changes:
            print(color("No files need to be renamed", CLI_COLORS["WARNING"]))
            return

        # Use common confirmation function
        if self._confirm_changes(file_count=len(changes)):
            try:
                # Apply changes
                for old_name, new_name in changes:
                    src = os.path.join(self.directory, old_name)
                    dst = os.path.join(self.directory, new_name)
                    self._move_file(src, dst)
                divider("Changes confirmed")
                self._show_statistics()
            except OSError as e:
                print(color(f"Error during rename: {str(e)}", CLI_COLORS["ERROR"]))
        else:
            divider("Changes cancelled")

    def interactive_rename(self, file_list: list) -> None:
        banner = Panel(
            "[cyan]Interactive Batch Rename[/cyan]\n\n"
            "Enter base name pattern with '>' symbol for custom input positions\n"
            "[red]Example files: ['24architecture15.pdf', '24architecture12.pdf', 'architecture11.pdf'][/red]\n"
            "[green]Target format: ['2024-architecture-11.pdf', '2024-architecture-12.pdf', '2024-architecture-15.pdf'][/green]\n"
            "Base pattern: [yellow]2024-architecture->[/yellow]\n"
            "Notes: \n"
            "1. Use '>' symbol to mark positions for custom input\n"
            "2. Use placeholders like {name}, {ext}, {num} for automatic substitution\n"
            "3. Regular expressions can be used with {regex:pattern:group}\n"
            "4. File extensions will be preserved automatically",
            title="Instructions",
            border_style="cyan",
        )
        self.console.print(banner)
        self.show_files(file_list)
        self.modified_files = 0

        while True:
            base_name = input(color("Base pattern: ", CLI_COLORS["CONTENT"]))
            if not base_name:
                continue

            # Show pattern preview with placeholders
            preview_pattern = base_name
            preview_pattern = preview_pattern.replace(
                ">", color("custom", CLI_COLORS["CONTENT"])
            )
            preview_pattern = preview_pattern.replace(
                "{name}", color("{filename}", CLI_COLORS["CONTENT"])
            )
            preview_pattern = preview_pattern.replace(
                "{ext}", color("{extension}", CLI_COLORS["CONTENT"])
            )
            preview_pattern = preview_pattern.replace(
                "{num}", color("{number}", CLI_COLORS["CONTENT"])
            )

            # Highlight regex patterns
            regex_patterns = re.findall(r"\{regex:(.*?):(.*?)\}", preview_pattern)
            for pattern, group in regex_patterns:
                preview_pattern = preview_pattern.replace(
                    f"{{regex:{pattern}:{group}}}",
                    color(
                        f'{{regex match of "{pattern}" group {group}}}',
                        CLI_COLORS["CONTENT"],
                    ),
                )

            print(f"Pattern preview: {preview_pattern}")

            if (
                input(
                    f"Confirm pattern? ({color('[F]', CLI_COLORS['WARNING'])} to modify, ENTER to confirm): "
                ).lower()
                != "f"
            ):
                break

        divider("Pattern confirmed")
        print()

        # Process each file with the pattern
        for old_file in file_list:
            if os.path.isdir(os.path.join(self.directory, old_file)):
                print(f"Skipping directory: {color(old_file, CLI_COLORS['WARNING'])}")
                print()
                continue

            file_name, ext = os.path.splitext(old_file)
            if not ext:
                continue

            print(f"Processing: {color(old_file, CLI_COLORS['CONTENT'])}")

            # First, handle automatic replacements
            new_parts = []
            pattern_copy = base_name

            # Replace built-in placeholders
            pattern_copy = pattern_copy.replace("{name}", file_name)
            pattern_copy = pattern_copy.replace("{ext}", ext)

            # Handle regex patterns if present
            regex_patterns = re.findall(r"\{regex:(.*?):(.*?)\}", pattern_copy)
            for pattern, group in regex_patterns:
                try:
                    match = re.search(pattern, old_file)
                    if match and group.isdigit():
                        # Replace with the specified capture group
                        group_value = (
                            match.group(int(group))
                            if int(group) <= len(match.groups())
                            else ""
                        )
                        pattern_copy = pattern_copy.replace(
                            f"{{regex:{pattern}:{group}}}", group_value
                        )
                    elif match and group == "all":
                        # Replace with the entire match
                        pattern_copy = pattern_copy.replace(
                            f"{{regex:{pattern}:{group}}}", match.group(0)
                        )
                    else:
                        # No match or invalid group
                        pattern_copy = pattern_copy.replace(
                            f"{{regex:{pattern}:{group}}}", ""
                        )
                except re.error:
                    print(
                        color(f"Invalid regex pattern: {pattern}", CLI_COLORS["ERROR"])
                    )
                    pattern_copy = pattern_copy.replace(
                        f"{{regex:{pattern}:{group}}}", ""
                    )

            # Handle custom input positions
            count = 1
            for char in pattern_copy:
                if char == ">":
                    custom = input(
                        f"Input {color(str(count), CLI_COLORS['CONTENT'])} => "
                    )
                    new_parts.append(custom)
                    count += 1
                else:
                    new_parts.append(char)

            # Create the new filename
            new_name = f"{''.join(new_parts)}"

            # If extension was not explicitly included in the pattern, add it
            if not new_name.endswith(ext):
                new_name = f"{new_name}{ext}"

            print(f"New name: {color(new_name, CLI_COLORS['CONTENT'])}")

            choice = input(
                f"Action? ({color('[F]', CLI_COLORS['WARNING'])} to modify, "
                f"{color('[S]', CLI_COLORS['WARNING'])} to skip, ENTER to confirm): "
            ).upper()

            if choice == "F":
                continue
            elif choice == "S":
                print(f"Skipped: {color(old_file, CLI_COLORS['CONTENT'])}")
                print()
                continue
            else:
                try:
                    old_path = os.path.join(self.directory, old_file)
                    new_path = os.path.join(self.directory, new_name)

                    if os.path.exists(new_path) and old_path != new_path:
                        print(
                            color(
                                f"Error: '{new_name}' already exists",
                                CLI_COLORS["ERROR"],
                            )
                        )
                        choice = input(
                            f"Overwrite? ({color('[Y/n]', CLI_COLORS['WARNING'])}, default is Yes): "
                        ).upper()
                        if choice == "N":
                            print(f"Skipped: {color(old_file, CLI_COLORS['CONTENT'])}")
                            print()
                            continue

                    if self._move_file(old_path, new_path):
                        print(
                            f"Renamed: {color(old_file, CLI_COLORS['CONTENT'])} => {color(new_name, CLI_COLORS['CONTENT'])}"
                        )
                        print()
                except OSError as e:
                    print(
                        color(
                            f"Error renaming '{old_file}': {str(e)}",
                            CLI_COLORS["ERROR"],
                        )
                    )
                    print()

        self._show_statistics()

    def replace_in_name(self, file_list: list, old_text: str, new_text: str) -> None:
        if not old_text:
            print(color("Error: old text cannot be empty", CLI_COLORS["ERROR"]))
            return

        changes = []
        self.modified_files = 0

        for filename in file_list:
            if SHOULD_EXIT:
                print("\nOperation interrupted by user")
                return

            new_name = filename.replace(old_text, new_text)
            if new_name == filename:
                continue

            # Check if target file already exists
            dst = os.path.join(self.directory, new_name)
            if os.path.exists(dst) and dst != os.path.join(self.directory, filename):
                print(color(f"Error: '{new_name}' already exists", CLI_COLORS["ERROR"]))
                return

            changes.append((filename, new_name))
            print(f"{filename} => {color(new_name, CLI_COLORS['CONTENT'])}")

        if not changes:
            print(color("No files need to be renamed", CLI_COLORS["WARNING"]))
            return

        # Request user confirmation
        if self._confirm_changes(file_count=len(changes)):
            for old_name, new_name in changes:
                if SHOULD_EXIT:
                    print("\nOperation interrupted by user")
                    return

                src = os.path.join(self.directory, old_name)
                dst = os.path.join(self.directory, new_name)
                self._move_file(src, dst)

            divider("Changes confirmed")
            self._show_statistics()
        else:
            divider("Changes cancelled")

    def sort_files(self, file_list: list, width: int = 3) -> None:
        changes = []
        self.modified_files = 0

        for index, filename in enumerate(file_list, 1):
            new_name = f"{str(index).zfill(width)}-{filename}"
            src = os.path.join(self.directory, filename)
            dst = os.path.join(self.directory, new_name)

            if os.path.exists(dst) and dst != src:
                print(color(f"Error: '{new_name}' already exists", CLI_COLORS["ERROR"]))
                return

            changes.append((src, dst))
            print(f"{filename} => {color(new_name, CLI_COLORS['CONTENT'])}")

        if not changes:
            print(color("No files need to be renamed", CLI_COLORS["WARNING"]))
            return

        # Use common confirmation function
        if self._confirm_changes(file_count=len(changes)):
            total = len(changes)
            for i, (src, dst) in enumerate(changes, 1):
                self._move_file(src, dst, show_progress=True, current=i, total=total)

            divider("Changes confirmed")
            self._show_statistics()
        else:
            divider("Changes cancelled")

    def lowercase_files(self, file_list: list) -> None:
        changes = []
        self.modified_files = 0
        temp_changes = []  # Store temporary renames for Windows system

        # First pass: check for case conflicts
        case_conflicts = {}
        for filename in file_list:
            lower_name = filename.lower()
            if lower_name in case_conflicts:
                case_conflicts[lower_name].append(filename)
            else:
                case_conflicts[lower_name] = [filename]

        # Handle case conflicts
        for lower_name, conflicting_files in case_conflicts.items():
            if len(conflicting_files) > 1:
                print(
                    color(
                        f"Warning: Case conflict detected for '{lower_name}':",
                        CLI_COLORS["WARNING"],
                    )
                )
                for i, f in enumerate(conflicting_files, 1):
                    print(color(f"  {i}. {f}", CLI_COLORS["WARNING"]))
                print(
                    color(
                        "Skipping these files to avoid data loss", CLI_COLORS["WARNING"]
                    )
                )
                continue

            # No conflict, process the file
            filename = conflicting_files[0]
            if filename == lower_name:
                continue

            # For Windows, we need to use a temporary name first
            if sys.platform == "win32" and filename.lower() == lower_name:
                temp_name = f"{filename}.tmp"
                temp_changes.append((filename, temp_name))
                changes.append((temp_name, lower_name))
            else:
                changes.append((filename, lower_name))

            print(f"{filename} => {color(lower_name, CLI_COLORS['CONTENT'])}")

        if not changes and not temp_changes:
            print(color("No files need to be renamed", CLI_COLORS["WARNING"]))
            return

        # Use common confirmation function
        if self._confirm_changes(file_count=len(changes)):
            try:
                # Handle temporary renames for Windows system
                for old_name, temp_name in temp_changes:
                    src = os.path.join(self.directory, old_name)
                    temp_path = os.path.join(self.directory, temp_name)
                    # Don't count temporary moves in the statistics
                    self._move_file(src, temp_path, count_as_modified=False)

                # Process all renames
                for old_name, new_name in changes:
                    src = os.path.join(self.directory, old_name)
                    dst = os.path.join(self.directory, new_name)
                    if os.path.exists(src):  # Check if source exists (for temp files)
                        # Only count non-temporary files as modifications
                        self._move_file(src, dst, count_as_modified=True)

                divider("Changes confirmed")
                self._show_statistics()
            except OSError as e:
                print(color(f"Error during rename: {str(e)}", CLI_COLORS["ERROR"]))
        else:
            divider("Changes cancelled")

    def _confirm_changes(
        self, changes_message="Confirm the above changes?", file_count=None
    ) -> bool:
        count_info = ""
        if file_count is not None:
            count_info = f"{color(str(file_count), CLI_COLORS['CONTENT'])} files will be modified | "
        return (
            input(
                f"\n{count_info}{changes_message} ({color('[Y/n]', CLI_COLORS['CONTENT'])}, default is Yes): "
            ).lower()
            != "n"
        )

    def _show_progress(self, current: int, total: int, prefix: str = "") -> None:
        if total == 0:
            return
        percent = (current / total) * 100
        progress = int(percent / 2)  # 50 character progress bar
        bar = "█" * progress + "░" * (50 - progress)
        self.console.print(
            f"\r{prefix} [{bar}] {percent:.1f}% {current}/{total}", end=""
        )
        if current == total:
            self.console.print()  # newline


def create_example_text() -> str:
    script_name = os.path.basename(sys.argv[0])

    examples = [
        ("Fast rename images", "fast -t image -w 3"),
        ("Fast rename videos", "fast -t video"),
        ("Add numeric prefix", "prefix -w 3 -m add -s 1"),
        ("Remove numeric prefix", "prefix -m remove"),
        ("Interactive rename", "interactive"),
        ("Replace text in filenames", "replace '_' '-'"),
        ("Sort and rename", "sort -w 3"),
        ("Convert to lowercase", "lowercase"),
        ("Debug mode", "--debug"),
    ]

    text = f"\n{color('Examples:', CLI_COLORS['SUB_TITLE'])}"

    for desc, cmd in examples:
        text += f"\n  {color(f'# {desc}', CLI_COLORS['EXAMPLE'])}"
        text += f"\n  {color(f'{script_name} {cmd}', CLI_COLORS['CONTENT'])}"
        text += "\n"

    notes = [
        "All commands support -d/--dirs option to include directories",
        "Use --debug option to enable debug mode",
        "Fast rename supports file types: image, video",
        "try replace 'sth' '\"\"' to remove the string",
        "Interactive rename uses '>' symbol to mark custom input positions",
        "Lowercase command converts all uppercase letters to lowercase in filenames",
        "Files are sorted using natural sort (e.g., 1.txt, 2.txt, 10.txt instead of 1.txt, 10.txt, 2.txt)",
    ]

    text += f"\n{color('Notes:', CLI_COLORS['SUB_TITLE'])}"
    for note in notes:
        text += f"\n  {color(f'- {note}', CLI_COLORS['CONTENT'])}"

    return text


def create_help_text(parser: argparse.ArgumentParser) -> str:
    help_parts = []

    # Add description
    if parser.description:
        help_parts.append(color(parser.description, CLI_COLORS["TITLE"]))
        help_parts.append("")

    # Add usage
    prog_name = parser.prog
    help_parts.append(
        f"{color('Usage:', CLI_COLORS['TITLE'])} {prog_name} [OPTIONS] COMMAND"
    )
    help_parts.append("")

    # Add global options
    help_parts.append(color("Global Options:", CLI_COLORS["TITLE"]))
    help_parts.extend(
        [
            f"  {color('-h, --help', CLI_COLORS['SUB_TITLE'])}         Show this help message and exit",
            f"  {color('-d, --dirs', CLI_COLORS['SUB_TITLE'])}         Include directories",
            f"  {color('--debug', CLI_COLORS['SUB_TITLE'])}            Enable debug mode",
            f"  {color('-v, --version', CLI_COLORS['SUB_TITLE'])}         Show program version",
        ]
    )
    help_parts.append("")

    # Add commands
    help_parts.append(color("Commands:", CLI_COLORS["TITLE"]))
    help_parts.extend(
        [
            f"  {color('fast', CLI_COLORS['SUB_TITLE'])}              Fast rename files with sequential numbers",
            f"  {color('prefix', CLI_COLORS['SUB_TITLE'])}            Add or remove numeric prefixes",
            f"  {color('interactive', CLI_COLORS['SUB_TITLE'])}        Interactive rename with pattern matching",
            f"  {color('replace', CLI_COLORS['SUB_TITLE'])}           Replace text in filenames",
            f"  {color('sort', CLI_COLORS['SUB_TITLE'])}              Sort and rename files",
            f"  {color('lowercase', CLI_COLORS['SUB_TITLE'])}          Convert filenames to lowercase",
        ]
    )
    help_parts.append("")

    # Add examples
    help_parts.append(create_example_text())

    return "\n".join(help_parts)


def create_command_help(parser: argparse.ArgumentParser, command: str) -> str:
    help_parts = []

    # Add description
    if parser.description:
        help_parts.append(color(parser.description, CLI_COLORS["TITLE"]))
        help_parts.append("")

    # Add usage based on command
    prog_name = parser.prog
    if command == "fast":
        help_parts.extend(
            [
                f"{color('Usage:', CLI_COLORS['TITLE'])} {prog_name} fast [OPTIONS]",
                "",
                color("Options:", CLI_COLORS["TITLE"]),
                f"  {color('-t, --type', CLI_COLORS['SUB_TITLE'])} TYPE     File type (image, video) [default: image]",
                f"  {color('-w, --width', CLI_COLORS['SUB_TITLE'])} WIDTH   Number width [default: 3]",
            ]
        )
    elif command == "prefix":
        help_parts.extend(
            [
                f"{color('Usage:', CLI_COLORS['TITLE'])} {prog_name} prefix [OPTIONS]",
                "",
                color("Options:", CLI_COLORS["TITLE"]),
                f"  {color('-w, --width', CLI_COLORS['SUB_TITLE'])} WIDTH   Number width [default: 3]",
                f"  {color('-m, --mode', CLI_COLORS['SUB_TITLE'])} MODE     Operation mode (add, remove) [default: add]",
                f"  {color('--start_num', CLI_COLORS['SUB_TITLE'])} START NUMBER   Starting number [default: 1]",
            ]
        )
    elif command == "replace":
        help_parts.extend(
            [
                f"{color('Usage:', CLI_COLORS['TITLE'])} {prog_name} replace OLD NEW",
                "",
                color("Arguments:", CLI_COLORS["TITLE"]),
                f"  OLD                  Text to replace",
                f"  NEW                  Replacement text",
            ]
        )
    elif command == "sort":
        help_parts.extend(
            [
                f"{color('Usage:', CLI_COLORS['TITLE'])} {prog_name} sort [OPTIONS]",
                "",
                color("Options:", CLI_COLORS["TITLE"]),
                f"  {color('-w, --width', CLI_COLORS['SUB_TITLE'])} WIDTH   Number width [default: 3]",
            ]
        )

    help_parts.append("")
    return "\n".join(help_parts)


def main():
    parser = argparse.ArgumentParser(
        description="Batch file renaming tool - supports multiple renaming modes",
        add_help=False,
    )

    # Global options
    parser.add_argument(
        "-h", "--help", action="store_true", help="Show this help message and exit"
    )
    parser.add_argument("-d", "--dirs", action="store_true", help="Include directories")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"%(prog)s {VERSION}",
        help="Show program version",
    )

    # Subcommands
    subparsers = parser.add_subparsers(dest="command")

    # Fast rename command
    fast_parser = subparsers.add_parser("fast", help="Fast rename files")
    fast_parser.add_argument(
        "-t",
        "--type",
        choices=[FileType.IMAGE, FileType.VIDEO],
        default=FileType.IMAGE,
        help=f"File type (default: {FileType.IMAGE})",
    )
    fast_parser.add_argument(
        "-w", "--width", type=int, default=3, help="Number width (default: 3)"
    )

    # Prefix rename command
    prefix_parser = subparsers.add_parser(
        "prefix", help="Add or remove numeric prefixes"
    )
    prefix_parser.add_argument(
        "-w", "--width", type=int, default=3, help="Number width (default: 3)"
    )
    prefix_parser.add_argument(
        "-m",
        "--mode",
        choices=["add", "remove"],
        default="add",
        help="Operation mode (default: add)",
    )
    prefix_parser.add_argument(
        "--start_num", type=int, default=1, help="Starting number (default: 1)"
    )

    # Interactive rename command
    subparsers.add_parser("interactive", help="Interactive rename")

    # Replace text command
    replace_parser = subparsers.add_parser("replace", help="Replace text in filenames")
    replace_parser.add_argument("old", help="Text to replace")
    replace_parser.add_argument("new", help="Replacement text")

    # Sort files command
    sort_parser = subparsers.add_parser("sort", help="Sort and rename files")
    sort_parser.add_argument(
        "-w", "--width", type=int, default=3, help="Number width (default: 3)"
    )

    # Lowercase command
    subparsers.add_parser("lowercase", help="Convert filenames to lowercase")

    args = parser.parse_args()

    # Show help
    if args.help:
        if args.command:
            print(create_command_help(parser, args.command))
        else:
            print(create_help_text(parser))
        return

    if args.debug:
        global DEBUG_MODE
        DEBUG_MODE = True
        debug("Debug mode enabled")

    renamer = FileRenamer(WORK_DIR)
    file_list = renamer.get_file_list(args.dirs)

    if not file_list and args.command:
        print(color("Error: No files found to process", CLI_COLORS["ERROR"]))
        return

    if args.command == "fast":
        renamer.fast_rename(args.type, args.width)
    elif args.command == "prefix":
        renamer.prefix_rename(file_list, args.width, args.mode, args.start_num)
    elif args.command == "interactive":
        renamer.interactive_rename(file_list)
    elif args.command == "replace":
        renamer.replace_in_name(file_list, args.old, args.new)
    elif args.command == "sort":
        renamer.sort_files(file_list, args.width)
    elif args.command == "lowercase":
        renamer.lowercase_files(file_list)
    else:
        print(create_help_text(parser))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(color("\nOperation interrupted by user", CLI_COLORS["ERROR"]))
        sys.exit(0)
    except Exception as e:
        if DEBUG_MODE:
            import traceback

            traceback.print_exc()
        print(color(f"\nError: {str(e)}", CLI_COLORS["ERROR"]))
        sys.exit(1)
