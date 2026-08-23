#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# pip install rich colorama

"""Batch file renaming tool with preview, confirmation, and safe commits."""

from __future__ import annotations

import argparse
import inspect
import json
import os
import re
import signal
import sys
import traceback
from dataclasses import dataclass
from pathlib import Path
from types import FrameType
from typing import Iterable, Sequence
from uuid import uuid4

from rich.console import Console
from rich.panel import Panel

if sys.platform == "win32":
    try:
        from colorama import init as colorama_init
    except ImportError:
        colorama_init = None
    if colorama_init is not None:
        colorama_init(autoreset=True)


DEBUG_MODE = False
VERSION = "1.2.0"
TRANSACTION_JOURNAL_NAME = ".rename-transaction.json"
TRANSACTION_JOURNAL_TEMP_NAME = f"{TRANSACTION_JOURNAL_NAME}.tmp"
RENAME_TEMP_PREFIX = ".rename-tmp-"
TRANSACTION_VERSION = 1
TRANSACTION_STATES = frozenset({"staging", "committing", "committed", "rolled_back"})

VIDEO_EXTENSIONS = (
    ".mp4",
    ".flv",
    ".wmv",
    ".avi",
    ".webm",
    ".3gp",
    ".mpg",
    ".mov",
    ".rm",
    ".rmvb",
    ".mkv",
)

IMAGE_EXTENSIONS = (
    ".jpg",
    ".png",
    ".jpeg",
    ".bmp",
    ".webp",
    ".jfif",
    ".avif",
    ".gif",
)

IGNORED_NAMES = frozenset(
    {
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
        TRANSACTION_JOURNAL_NAME,
        TRANSACTION_JOURNAL_TEMP_NAME,
        "rename.py",
        "tools.py",
        "interact-rename.py",
        "14-interact-rename.py",
        "14-rename.py",
    }
)

REGEX_PLACEHOLDER = re.compile(r"\{regex:(.*?):(.*?)\}")
ANSI_ESCAPE = re.compile(r"\033\[[0-9;]*m")


class CLIStyle:
    """Centralized terminal colors used by the command-line interface."""

    COLORS = {
        "TITLE": 7,
        "SUB_TITLE": 2,
        "CONTENT": 3,
        "EXAMPLE": 7,
        "WARNING": 4,
        "ERROR": 2,
    }

    COLOR_TABLE = {
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

    @classmethod
    def color(cls, text: object = "", color_code: int = 0) -> str:
        """Return text wrapped in the selected ANSI color."""
        template = cls.COLOR_TABLE.get(color_code, cls.COLOR_TABLE[0])
        return template.format(text)


class ColoredArgumentParser(argparse.ArgumentParser):
    """Argument parser that keeps help output aligned with the CLI colors."""

    def add_argument(self, *args: str, **kwargs: object) -> argparse.Action:
        help_text = kwargs.get("help")
        if isinstance(help_text, str) and help_text != argparse.SUPPRESS:
            kwargs["help"] = CLIStyle.color(help_text, CLIStyle.COLORS["CONTENT"])
        return super().add_argument(*args, **kwargs)

    def _format_action_invocation(self, action: argparse.Action) -> str:
        if not action.option_strings:
            (metavar,) = self._metavar_formatter(action, action.dest.upper())(1)
            return CLIStyle.color(metavar, CLIStyle.COLORS["CONTENT"])

        parts = []
        if action.nargs == 0:
            parts.extend(
                CLIStyle.color(option, CLIStyle.COLORS["SUB_TITLE"])
                for option in action.option_strings
            )
        else:
            metavar = action.metavar or action.dest.upper()
            args_string = self._format_args(
                action, CLIStyle.color(metavar, CLIStyle.COLORS["CONTENT"])
            )
            for option in action.option_strings:
                parts.append(
                    CLIStyle.color(
                        f"{option} {args_string}", CLIStyle.COLORS["SUB_TITLE"]
                    )
                )
        return ", ".join(parts)

    def format_help(self) -> str:
        formatter = self._get_formatter()
        if self.description:
            formatter.add_text(
                CLIStyle.color(self.description, CLIStyle.COLORS["TITLE"])
            )
        formatter.add_usage(self.usage, self._actions, self._mutually_exclusive_groups)
        for action_group in self._action_groups:
            if not action_group._group_actions:
                continue
            formatter.start_section(
                CLIStyle.color(action_group.title, CLIStyle.COLORS["TITLE"])
            )
            formatter.add_arguments(action_group._group_actions)
            formatter.end_section()
        if self.epilog:
            formatter.add_text(self.epilog)
        return formatter.format_help()


class FileType:
    """Supported file categories for the fast command."""

    VIDEO = "video"
    IMAGE = "image"
    ALL = "all"
    EXTENSIONS = {
        VIDEO: VIDEO_EXTENSIONS,
        IMAGE: IMAGE_EXTENSIONS,
        ALL: IMAGE_EXTENSIONS + VIDEO_EXTENSIONS,
    }

    @classmethod
    def get_extensions(cls, file_type: str) -> tuple[str, ...]:
        """Return the extensions associated with a file category."""
        return cls.EXTENSIONS.get(file_type, ())


@dataclass(frozen=True, slots=True)
class RenameChange:
    """A validated source-to-destination rename pair."""

    old_name: str
    new_name: str


@dataclass(frozen=True, slots=True)
class TransactionEntry:
    """Persisted mapping for one file in an interrupted rename."""

    old_name: str
    new_name: str
    temporary_name: str

    def to_dict(self) -> dict[str, str]:
        """Serialize the entry for the transaction journal."""
        return {
            "old_name": self.old_name,
            "new_name": self.new_name,
            "temporary_name": self.temporary_name,
        }


@dataclass(slots=True)
class TransactionJournal:
    """Describe a rename transaction that can be recovered after interruption."""

    state: str
    entries: list[TransactionEntry]

    def to_dict(self) -> dict[str, object]:
        """Serialize the journal for atomic persistence."""
        return {
            "version": TRANSACTION_VERSION,
            "state": self.state,
            "changes": [entry.to_dict() for entry in self.entries],
        }


class RenameCancelled(Exception):
    """Raised when an interrupt arrives during a staged rename."""


def natural_sort_key(value: str) -> tuple[tuple[int, object], ...]:
    """Build a natural sort key that handles text-only and numeric names."""
    chunks = re.split(r"(\d+)", value)
    return tuple(
        (0, int(chunk)) if chunk.isdigit() else (1, chunk.casefold())
        for chunk in chunks
    )


def print_status(message: str, color_code: int = CLIStyle.COLORS["CONTENT"]) -> None:
    """Print a status message with the standard CLI color."""
    print(CLIStyle.color(message, color_code))


def debug(
    *args: object,
    file: str | Path | None = None,
    append: bool = True,
    **kwargs: object,
) -> None:
    """Print debug information when debug mode is enabled."""
    if not DEBUG_MODE:
        return

    frame = inspect.currentframe()
    caller = frame.f_back if frame is not None else None
    if caller is not None:
        frame_info = inspect.getframeinfo(caller)
        location = f"{Path(frame_info.filename).name}:{frame_info.lineno}"
    else:
        location = "unknown:0"

    parts = [str(argument) for argument in args]
    parts.extend(f"{key}={value}" for key, value in kwargs.items())
    message = (
        f"{CLIStyle.color(location, CLIStyle.COLORS['CONTENT'])} "
        f"{CLIStyle.color('|', CLIStyle.COLORS['EXAMPLE'])} "
        f"{CLIStyle.color(' '.join(parts), CLIStyle.COLORS['ERROR'])}\n"
    )

    if file is None:
        print(message, end="")
        return

    mode = "a" if append else "w"
    clean_message = ANSI_ESCAPE.sub("", message)
    with Path(file).open(mode, encoding="utf-8") as output_file:
        output_file.write(clean_message)


def divider(text: str = "Divider", char: str = "=") -> None:
    """Print a compact colored section divider."""
    line = char * 10
    label = text or "Divider"
    print(f"{CLIStyle.color(line, 5)} {label} {CLIStyle.color(line, 5)}")


def positive_int(value: str) -> int:
    """Parse an argparse integer that must be greater than zero."""
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("value must be greater than zero")
    return number


def nonnegative_int(value: str) -> int:
    """Parse an argparse integer that may be zero but not negative."""
    number = int(value)
    if number < 0:
        raise argparse.ArgumentTypeError("value must not be negative")
    return number


def normalize_extension(value: str) -> str:
    """Normalize and validate an explicitly requested filename extension."""
    extension = value.strip()
    if not extension:
        raise argparse.ArgumentTypeError("extension must not be empty")
    if not extension.startswith("."):
        extension = f".{extension}"
    if re.fullmatch(r"\.[A-Za-z0-9]+", extension) is None:
        raise argparse.ArgumentTypeError(
            "extension must contain only letters and numbers"
        )
    return extension.lower()


class FileRenamer:
    """Collect, preview, validate, and safely apply filename changes."""

    def __init__(
        self,
        directory: Path,
        include_dirs: bool = False,
        excluded_names: Iterable[str] | None = None,
        dry_run: bool = False,
        assume_yes: bool = False,
    ) -> None:
        self.directory = directory.expanduser().resolve()
        self.include_dirs = include_dirs
        self.excluded_names = set(IGNORED_NAMES)
        self.excluded_names.update(
            name for name in (Path(__file__).name, Path(sys.argv[0]).name) if name
        )
        if excluded_names is not None:
            self.excluded_names.update(excluded_names)
        self.dry_run = dry_run
        self.assume_yes = assume_yes
        self.console = Console()
        self.total_files = 0
        self.modified_files = 0
        self.stop_requested = False
        self._install_signal_handler()
        if not self._recover_transaction():
            raise RuntimeError(
                "A previous rename transaction could not be recovered safely."
            )

    def _install_signal_handler(self) -> None:
        for signal_number in (signal.SIGINT, signal.SIGTERM):
            try:
                signal.signal(signal_number, self._signal_handler)
            except (OSError, ValueError):
                continue

    def _signal_handler(self, signum: int, frame: FrameType | None) -> None:
        del signum, frame
        self.stop_requested = True
        print_status(
            "\nOperation interrupted; finishing the current safe step.",
            CLIStyle.COLORS["WARNING"],
        )

    @staticmethod
    def _exists(path: Path) -> bool:
        return os.path.lexists(os.fspath(path))

    @staticmethod
    def _collision_key(name: str) -> str:
        return name.casefold()

    @staticmethod
    def _valid_target_name(name: str) -> bool:
        if not name or name in {".", ".."}:
            return False
        if name in {TRANSACTION_JOURNAL_NAME, TRANSACTION_JOURNAL_TEMP_NAME}:
            return False
        if name.startswith(RENAME_TEMP_PREFIX):
            return False
        return not any(character in name for character in "\x00/:\\")

    def _transaction_path(self) -> Path:
        return self.directory / TRANSACTION_JOURNAL_NAME

    def _transaction_journal_temp_path(self) -> Path:
        return self.directory / TRANSACTION_JOURNAL_TEMP_NAME

    def _temporary_paths(self) -> list[Path]:
        return [
            entry
            for entry in self.directory.iterdir()
            if entry.name.startswith(RENAME_TEMP_PREFIX)
        ]

    @staticmethod
    def _sync_directory(directory: Path) -> None:
        try:
            descriptor = os.open(os.fspath(directory), os.O_RDONLY)
        except OSError:
            return
        try:
            os.fsync(descriptor)
        except OSError:
            pass
        finally:
            os.close(descriptor)

    def _validate_transaction_journal(self, journal: TransactionJournal) -> None:
        if journal.state not in TRANSACTION_STATES:
            raise ValueError(f"unknown transaction state: {journal.state}")
        if not journal.entries:
            raise ValueError("transaction journal contains no changes")

        source_names: set[str] = set()
        destination_keys: set[str] = set()
        temporary_keys: set[str] = set()
        for entry in journal.entries:
            for name in (entry.old_name, entry.new_name):
                if Path(name).name != name or not self._valid_target_name(name):
                    raise ValueError(f"invalid transaction filename: {name!r}")
            if (
                Path(entry.temporary_name).name != entry.temporary_name
                or not entry.temporary_name.startswith(RENAME_TEMP_PREFIX)
                or any(character in entry.temporary_name for character in "\x00/:\\")
            ):
                raise ValueError(
                    f"invalid transaction temporary filename: {entry.temporary_name!r}"
                )

            destination_key = self._collision_key(entry.new_name)
            temporary_key = entry.temporary_name
            if entry.old_name in source_names:
                raise ValueError(f"duplicate transaction source: {entry.old_name!r}")
            if destination_key in destination_keys:
                raise ValueError(
                    f"duplicate transaction destination: {entry.new_name!r}"
                )
            if temporary_key in temporary_keys:
                raise ValueError(
                    f"duplicate transaction temporary: {entry.temporary_name!r}"
                )
            source_names.add(entry.old_name)
            destination_keys.add(destination_key)
            temporary_keys.add(temporary_key)

    def _load_transaction_journal(self) -> TransactionJournal:
        with self._transaction_path().open("r", encoding="utf-8") as input_file:
            payload = json.load(input_file)
        if not isinstance(payload, dict):
            raise ValueError("transaction journal must contain an object")
        if payload.get("version") != TRANSACTION_VERSION:
            raise ValueError("unsupported transaction journal version")

        state = payload.get("state")
        raw_entries = payload.get("changes")
        if not isinstance(state, str) or not isinstance(raw_entries, list):
            raise ValueError("transaction journal has invalid fields")

        entries: list[TransactionEntry] = []
        for raw_entry in raw_entries:
            if not isinstance(raw_entry, dict):
                raise ValueError("transaction journal contains an invalid change")
            old_name = raw_entry.get("old_name")
            new_name = raw_entry.get("new_name")
            temporary_name = raw_entry.get("temporary_name")
            if not all(
                isinstance(value, str) for value in (old_name, new_name, temporary_name)
            ):
                raise ValueError("transaction journal contains invalid filenames")
            entries.append(TransactionEntry(old_name, new_name, temporary_name))

        journal = TransactionJournal(state, entries)
        self._validate_transaction_journal(journal)
        return journal

    def _write_transaction_journal(self, journal: TransactionJournal) -> None:
        journal_path = self._transaction_path()
        temporary_path = self._transaction_journal_temp_path()
        try:
            with temporary_path.open("w", encoding="utf-8") as output_file:
                json.dump(
                    journal.to_dict(),
                    output_file,
                    ensure_ascii=False,
                    indent=2,
                )
                output_file.write("\n")
                output_file.flush()
                os.fsync(output_file.fileno())
            os.replace(temporary_path, journal_path)
            self._sync_directory(self.directory)
        except (OSError, TypeError, ValueError):
            try:
                temporary_path.unlink()
            except (FileNotFoundError, OSError):
                pass
            raise

    def _clear_transaction_journal(self) -> bool:
        try:
            for path in (
                self._transaction_path(),
                self._transaction_journal_temp_path(),
            ):
                try:
                    path.unlink()
                except FileNotFoundError:
                    continue
            self._sync_directory(self.directory)
        except OSError as error:
            print_status(
                f"Could not clear rename transaction journal: {error}",
                CLIStyle.COLORS["ERROR"],
            )
            return False
        return True

    def _restore_transaction(self, journal: TransactionJournal) -> None:
        known_temporary_names = {entry.temporary_name for entry in journal.entries}
        unexpected_temporary_paths = [
            path
            for path in self._temporary_paths()
            if path.name not in known_temporary_names
        ]
        if unexpected_temporary_paths:
            names = ", ".join(path.name for path in unexpected_temporary_paths)
            raise OSError(f"unexpected temporary files found: {names}")

        if journal.state == "staging":
            source_names = {entry.old_name for entry in journal.entries}
            for entry in journal.entries:
                old_exists = self._exists(self.directory / entry.old_name)
                temporary_exists = self._exists(self.directory / entry.temporary_name)
                if old_exists and temporary_exists:
                    raise OSError(
                        f"both source and temporary file exist for '{entry.old_name}'"
                    )
                if not old_exists and not temporary_exists:
                    raise OSError(
                        f"missing source and temporary file for '{entry.old_name}'"
                    )
                if entry.new_name not in source_names and self._exists(
                    self.directory / entry.new_name
                ):
                    raise OSError(
                        f"transaction target appeared externally: '{entry.new_name}'"
                    )

            for entry in journal.entries:
                temporary_path = self.directory / entry.temporary_name
                if not self._exists(temporary_path):
                    continue
                source = self.directory / entry.old_name
                if self._exists(source):
                    raise OSError(
                        f"source reappeared during recovery: '{entry.old_name}'"
                    )
                temporary_path.rename(source)
            return

        if self._transaction_is_restored(journal):
            return

        destination_entries = {
            self._collision_key(entry.new_name): entry for entry in journal.entries
        }
        for entry in journal.entries:
            source = self.directory / entry.old_name
            temporary_path = self.directory / entry.temporary_name
            destination = self.directory / entry.new_name
            if self._exists(source):
                destination_entry = destination_entries.get(
                    self._collision_key(entry.old_name)
                )
                if destination_entry is None or self._exists(
                    self.directory / destination_entry.temporary_name
                ):
                    raise OSError(
                        f"source appeared during recovery: '{entry.old_name}'"
                    )
            if self._exists(temporary_path) and self._exists(destination):
                raise OSError(
                    f"both destination and temporary file exist for '{entry.old_name}'"
                )
            if not self._exists(temporary_path) and not self._exists(destination):
                raise OSError(
                    f"missing destination and temporary file for '{entry.old_name}'"
                )

        for entry in journal.entries:
            temporary_path = self.directory / entry.temporary_name
            destination = self.directory / entry.new_name
            if self._exists(destination):
                destination.rename(temporary_path)

        for entry in journal.entries:
            source = self.directory / entry.old_name
            temporary_path = self.directory / entry.temporary_name
            if self._exists(source):
                raise OSError(f"source appeared during recovery: '{entry.old_name}'")
            if not self._exists(temporary_path):
                raise OSError(f"temporary file disappeared for '{entry.old_name}'")
            temporary_path.rename(source)

    def _transaction_is_restored(self, journal: TransactionJournal) -> bool:
        if self._temporary_paths():
            return False
        source_names = {entry.old_name for entry in journal.entries}
        for entry in journal.entries:
            if not self._exists(self.directory / entry.old_name):
                return False
            if entry.new_name not in source_names and self._exists(
                self.directory / entry.new_name
            ):
                return False
        return True

    def _recover_transaction(self) -> bool:
        journal_path = self._transaction_path()
        if not self._exists(journal_path):
            try:
                self._transaction_journal_temp_path().unlink()
            except (FileNotFoundError, OSError):
                pass
            try:
                orphaned_paths = self._temporary_paths()
            except OSError as error:
                print_status(
                    f"Could not inspect rename recovery files: {error}",
                    CLIStyle.COLORS["ERROR"],
                )
                return False
            if orphaned_paths:
                names = ", ".join(path.name for path in orphaned_paths)
                print_status(
                    f"Orphaned rename temporary files require manual recovery: {names}",
                    CLIStyle.COLORS["ERROR"],
                )
                return False
            return True

        try:
            journal = self._load_transaction_journal()
            if journal.state == "rolled_back":
                if not self._transaction_is_restored(journal):
                    raise OSError("rolled-back transaction still has active files")
            elif journal.state != "committed":
                self._restore_transaction(journal)
            elif self._temporary_paths():
                raise OSError("completed transaction still has temporary files")
        except (OSError, ValueError) as error:
            print_status(
                f"Rename transaction recovery failed: {error}",
                CLIStyle.COLORS["ERROR"],
            )
            return False

        if not self._clear_transaction_journal():
            return False
        if journal.state == "committed":
            print_status(
                "Cleared completed rename transaction journal.",
                CLIStyle.COLORS["WARNING"],
            )
        else:
            print_status(
                "Recovered interrupted rename transaction.",
                CLIStyle.COLORS["WARNING"],
            )
        return True

    def _create_transaction_journal(
        self, changes: Sequence[RenameChange]
    ) -> TransactionJournal:
        if self._exists(self._transaction_path()):
            raise OSError("another rename transaction is already active")
        entries = [
            TransactionEntry(
                old_name=change.old_name,
                new_name=change.new_name,
                temporary_name=self._temporary_name(index).name,
            )
            for index, change in enumerate(changes, start=1)
        ]
        journal = TransactionJournal("staging", entries)
        self._write_transaction_journal(journal)
        return journal

    def _show_statistics(self) -> None:
        print("")
        print(
            f"{CLIStyle.color('Total Files', CLIStyle.COLORS['SUB_TITLE'])}: "
            f"{CLIStyle.color(self.total_files, CLIStyle.COLORS['CONTENT'])} | "
            f"{CLIStyle.color('Modified Files', CLIStyle.COLORS['SUB_TITLE'])}: "
            f"{CLIStyle.color(self.modified_files, CLIStyle.COLORS['CONTENT'])}"
        )

    def get_file_list(self, include_dirs: bool | None = None) -> list[str]:
        """Return sorted eligible entries in the working directory."""
        should_include_dirs = (
            self.include_dirs if include_dirs is None else include_dirs
        )
        entries = []
        for entry in self.directory.iterdir():
            if entry.name in self.excluded_names or entry.name.startswith(
                RENAME_TEMP_PREFIX
            ):
                continue
            if entry.is_file() or (should_include_dirs and entry.is_dir()):
                entries.append(entry.name)

        entries.sort(key=lambda name: (natural_sort_key(name), name.casefold(), name))
        self.total_files = len(entries)
        return entries

    def show_files(self, file_list: Sequence[str]) -> None:
        """Print the entries selected for processing."""
        divider("Files in workspace")
        for filename in file_list:
            print(CLIStyle.color(filename, CLIStyle.COLORS["CONTENT"]))
        print("")

    def _prepare_changes(
        self, pairs: Iterable[tuple[str, str]]
    ) -> list[RenameChange] | None:
        changes: list[RenameChange] = []
        source_names: set[str] = set()
        destination_keys: dict[str, str] = {}

        for old_name, new_name in pairs:
            if old_name == new_name:
                continue
            if old_name in source_names:
                print_status(
                    f"Duplicate source name: '{old_name}'",
                    CLIStyle.COLORS["ERROR"],
                )
                return None
            if not self._valid_target_name(new_name):
                print_status(
                    f"Invalid target name: '{new_name}'",
                    CLIStyle.COLORS["ERROR"],
                )
                return None
            if not self._exists(self.directory / old_name):
                print_status(
                    f"Source no longer exists: '{old_name}'",
                    CLIStyle.COLORS["ERROR"],
                )
                return None

            destination_key = self._collision_key(new_name)
            previous_source = destination_keys.get(destination_key)
            if previous_source is not None:
                print_status(
                    f"Multiple files would become '{new_name}': "
                    f"'{previous_source}' and '{old_name}'",
                    CLIStyle.COLORS["ERROR"],
                )
                return None

            source_names.add(old_name)
            destination_keys[destination_key] = old_name
            changes.append(RenameChange(old_name, new_name))

        current_names = {entry.name for entry in self.directory.iterdir()}
        moving_keys = {self._collision_key(name) for name in source_names}
        for change in changes:
            destination_key = self._collision_key(change.new_name)
            occupied_names = {
                name
                for name in current_names
                if self._collision_key(name) == destination_key
            }
            external_names = occupied_names - source_names
            if external_names:
                occupied_name = sorted(external_names, key=natural_sort_key)[0]
                print_status(
                    f"Target already exists: '{occupied_name}' "
                    f"(needed for '{change.new_name}')",
                    CLIStyle.COLORS["ERROR"],
                )
                return None
            if destination_key not in moving_keys and occupied_names:
                print_status(
                    f"Target already exists: '{change.new_name}'",
                    CLIStyle.COLORS["ERROR"],
                )
                return None

        return changes

    def _preview_changes(self, changes: Sequence[RenameChange]) -> None:
        for change in changes:
            print(
                f"{CLIStyle.color(change.old_name, CLIStyle.COLORS['CONTENT'])} "
                f"=> {CLIStyle.color(change.new_name, CLIStyle.COLORS['CONTENT'])}"
            )

    def _confirm_changes(self, file_count: int) -> bool:
        if self.assume_yes:
            return True
        try:
            answer = input(
                f"\n{CLIStyle.color(file_count, CLIStyle.COLORS['CONTENT'])} "
                f"files will be modified. Confirm? "
                f"({CLIStyle.color('[Y/n]', CLIStyle.COLORS['CONTENT'])}, "
                "default is Yes): "
            )
        except EOFError:
            print_status("No confirmation received.", CLIStyle.COLORS["WARNING"])
            return False
        return answer.strip().lower() not in {"n", "no"}

    def _temporary_name(self, index: int) -> Path:
        while True:
            candidate = self.directory / f"{RENAME_TEMP_PREFIX}{index}-{uuid4().hex}"
            if not self._exists(candidate):
                return candidate

    def _rollback(
        self,
        staged: Sequence[tuple[RenameChange, Path]],
        completed: Sequence[tuple[RenameChange, Path]],
    ) -> bool:
        rollback_succeeded = True
        completed_names = {change.new_name for change, _ in completed}
        for change, temporary_path in reversed(staged):
            destination = self.directory / change.new_name
            if change.new_name not in completed_names:
                continue
            if not self._exists(destination):
                print_status(
                    f"Rollback could not find '{change.new_name}'.",
                    CLIStyle.COLORS["ERROR"],
                )
                rollback_succeeded = False
                continue
            if self._exists(temporary_path):
                print_status(
                    f"Rollback temporary path is occupied: '{temporary_path.name}'",
                    CLIStyle.COLORS["ERROR"],
                )
                rollback_succeeded = False
                continue
            try:
                destination.rename(temporary_path)
            except OSError as error:
                print_status(
                    f"Rollback failed for '{change.new_name}': {error}",
                    CLIStyle.COLORS["ERROR"],
                )
                rollback_succeeded = False

        for change, temporary_path in reversed(staged):
            source = self.directory / change.old_name
            if not self._exists(temporary_path):
                print_status(
                    f"Rollback temporary file is missing for '{change.old_name}'.",
                    CLIStyle.COLORS["ERROR"],
                )
                rollback_succeeded = False
                continue
            if self._exists(source):
                print_status(
                    f"Rollback skipped because the source now exists: "
                    f"'{change.old_name}'",
                    CLIStyle.COLORS["ERROR"],
                )
                rollback_succeeded = False
                continue
            try:
                temporary_path.rename(source)
            except OSError as error:
                print_status(
                    f"Rollback failed for '{change.old_name}': {error}",
                    CLIStyle.COLORS["ERROR"],
                )
                rollback_succeeded = False
        return rollback_succeeded

    def _apply_changes(
        self, changes: Sequence[RenameChange], show_progress: bool = False
    ) -> bool:
        staged: list[tuple[RenameChange, Path]] = []
        completed: list[tuple[RenameChange, Path]] = []
        journal: TransactionJournal | None = None

        try:
            if self.stop_requested:
                raise RenameCancelled
            journal = self._create_transaction_journal(changes)
            for change, entry in zip(changes, journal.entries):
                if self.stop_requested:
                    raise RenameCancelled
                source = self.directory / change.old_name
                temporary_path = self.directory / entry.temporary_name
                source.rename(temporary_path)
                staged.append((change, temporary_path))

            journal.state = "committing"
            self._write_transaction_journal(journal)
            for index, (change, entry) in enumerate(
                zip(changes, journal.entries), start=1
            ):
                if self.stop_requested:
                    raise RenameCancelled
                temporary_path = self.directory / entry.temporary_name
                destination = self.directory / change.new_name
                if self._exists(destination):
                    raise OSError(f"target appeared during rename: '{change.new_name}'")
                temporary_path.rename(destination)
                completed.append((change, destination))
                if show_progress:
                    self._show_progress(index, len(staged), "Renaming")
            journal.state = "committed"
            self._write_transaction_journal(journal)
            self._clear_transaction_journal()
        except RenameCancelled:
            rollback_succeeded = self._rollback(staged, completed)
            if journal is not None and rollback_succeeded:
                journal.state = "rolled_back"
                try:
                    self._write_transaction_journal(journal)
                except (OSError, TypeError, ValueError):
                    pass
                self._clear_transaction_journal()
            elif journal is not None:
                print_status(
                    "Rename recovery journal retained for the next run.",
                    CLIStyle.COLORS["WARNING"],
                )
            print_status("Rename cancelled safely.", CLIStyle.COLORS["WARNING"])
            return False
        except (OSError, TypeError, ValueError) as error:
            rollback_succeeded = self._rollback(staged, completed)
            if journal is not None and rollback_succeeded:
                journal.state = "rolled_back"
                try:
                    self._write_transaction_journal(journal)
                except (OSError, TypeError, ValueError):
                    pass
                self._clear_transaction_journal()
            elif journal is not None:
                print_status(
                    "Rename recovery journal retained for the next run.",
                    CLIStyle.COLORS["WARNING"],
                )
            print_status(f"Rename failed: {error}", CLIStyle.COLORS["ERROR"])
            return False

        self.modified_files += len(changes)
        return True

    def _execute_changes(
        self,
        pairs: Iterable[tuple[str, str]],
        show_progress: bool = False,
    ) -> None:
        self.modified_files = 0
        changes = self._prepare_changes(pairs)
        if changes is None:
            return
        if not changes:
            print_status("No files need to be renamed.", CLIStyle.COLORS["WARNING"])
            return

        self._preview_changes(changes)
        if self.dry_run:
            print_status("Dry run: no files were changed.", CLIStyle.COLORS["WARNING"])
            return
        if not self._confirm_changes(len(changes)):
            divider("Changes cancelled")
            return
        if self._apply_changes(changes, show_progress):
            divider("Changes confirmed")
            self._show_statistics()

    def fast_rename(
        self,
        file_type: str,
        width: int | None = None,
        start_num: int = 1,
        target_extension: str | None = None,
    ) -> None:
        """Rename matching media files while preserving their content suffix."""
        extensions = FileType.get_extensions(file_type)
        if not extensions:
            print_status(f"Unknown file type: '{file_type}'", CLIStyle.COLORS["ERROR"])
            return

        files = [
            filename
            for filename in self.get_file_list()
            if (self.directory / filename).is_file()
            and Path(filename).suffix.lower() in extensions
        ]
        if not files:
            print_status(
                f"No {file_type} files found in directory",
                CLIStyle.COLORS["WARNING"],
            )
            return

        if width is None:
            end_num = start_num + len(files) - 1
            width = max(
                len(str(len(files))),
                len(str(start_num)),
                len(str(end_num)),
            )

        pairs = []
        for index, filename in enumerate(files, start_num):
            extension = target_extension or Path(filename).suffix.lower()
            pairs.append((filename, f"{index:0{width}d}{extension}"))
        self._execute_changes(pairs)

    def prefix_rename(
        self,
        file_list: Sequence[str],
        width: int = 3,
        mode: str = "add",
        start_num: int = 1,
    ) -> None:
        """Add or remove numeric filename prefixes."""
        if mode not in {"add", "remove"}:
            print_status("Mode must be 'add' or 'remove'.", CLIStyle.COLORS["ERROR"])
            return

        if mode == "add":
            pairs = [
                (filename, f"{index:0{width}d}-{filename}")
                for index, filename in enumerate(file_list, start_num)
            ]
        else:
            pattern = re.compile(rf"^\d{{{width},}}-(.+)$")
            pairs = [
                (filename, match.group(1))
                for filename in file_list
                if (match := pattern.match(filename)) is not None
            ]
        self._execute_changes(pairs)

    def _pattern_preview(self, pattern: str) -> str:
        preview = pattern
        replacements = {
            ">": CLIStyle.color("custom", CLIStyle.COLORS["CONTENT"]),
            "{name}": CLIStyle.color("{filename}", CLIStyle.COLORS["CONTENT"]),
            "{ext}": CLIStyle.color("{extension}", CLIStyle.COLORS["CONTENT"]),
            "{num}": CLIStyle.color("{number}", CLIStyle.COLORS["CONTENT"]),
        }
        for source, target in replacements.items():
            preview = preview.replace(source, target)
        for match in REGEX_PLACEHOLDER.finditer(pattern):
            token = match.group(0)
            replacement = CLIStyle.color(
                f'{{regex match of "{match.group(1)}" group {match.group(2)}}}',
                CLIStyle.COLORS["CONTENT"],
            )
            preview = preview.replace(token, replacement, 1)
        return preview

    def _prompt_pattern(self) -> str:
        while True:
            try:
                pattern = input(
                    CLIStyle.color("Base pattern: ", CLIStyle.COLORS["CONTENT"])
                )
            except EOFError:
                return ""
            if not pattern:
                print_status("Pattern must not be empty.", CLIStyle.COLORS["WARNING"])
                continue
            print(f"Pattern preview: {self._pattern_preview(pattern)}")
            try:
                answer = input(
                    f"Confirm pattern? "
                    f"({CLIStyle.color('[F]', CLIStyle.COLORS['WARNING'])} "
                    "to modify, ENTER to confirm): "
                )
            except EOFError:
                return ""
            if answer.strip().lower() != "f":
                return pattern

    def _render_pattern(self, pattern: str, old_file: str, number: int) -> str | None:
        path = Path(old_file)
        extension = path.suffix
        rendered = (
            pattern.replace("{name}", path.stem)
            .replace("{ext}", extension)
            .replace("{num}", str(number))
        )

        for match in list(REGEX_PLACEHOLDER.finditer(rendered)):
            token = match.group(0)
            regex_pattern = match.group(1)
            group = match.group(2)
            try:
                regex_match = re.search(regex_pattern, old_file)
            except re.error as error:
                print_status(
                    f"Invalid regex pattern '{regex_pattern}': {error}",
                    CLIStyle.COLORS["ERROR"],
                )
                return None

            replacement = ""
            if regex_match is not None:
                if group == "all":
                    replacement = regex_match.group(0)
                elif group.isdigit() and int(group) <= len(regex_match.groups()):
                    replacement = regex_match.group(int(group))
            rendered = rendered.replace(token, replacement, 1)

        if ">" in rendered:
            parts = []
            count = 1
            for character in rendered:
                if character == ">":
                    try:
                        custom_value = input(
                            f"Input {CLIStyle.color(count, CLIStyle.COLORS['CONTENT'])} "
                            "=> "
                        )
                    except EOFError:
                        return None
                    parts.append(custom_value)
                    count += 1
                else:
                    parts.append(character)
            rendered = "".join(parts)

        if extension and not rendered.casefold().endswith(extension.casefold()):
            rendered = f"{rendered}{extension}"
        return rendered

    def interactive_rename(self, file_list: Sequence[str]) -> None:
        """Rename files one by one with pattern and per-file confirmation."""
        banner = Panel(
            "[cyan]Pattern Batch Rename[/cyan]\n\n"
            "Use '>' for custom input positions.\n"
            "Placeholders: {name}, {ext}, {num}.\n"
            "Regex: {regex:pattern:group}, where group can be a number or all.\n"
            "The original extension is preserved automatically.",
            title="Instructions",
            border_style="cyan",
        )
        self.console.print(banner)
        self.show_files(file_list)
        self.modified_files = 0

        pattern = self._prompt_pattern()
        if not pattern:
            print_status("Interactive rename cancelled.", CLIStyle.COLORS["WARNING"])
            return

        for number, old_file in enumerate(file_list, start=1):
            if self.stop_requested:
                break
            if (self.directory / old_file).is_dir():
                print(
                    f"Skipping directory: "
                    f"{CLIStyle.color(old_file, CLIStyle.COLORS['WARNING'])}"
                )
                continue
            if not Path(old_file).suffix:
                print(
                    f"Skipping extensionless file: "
                    f"{CLIStyle.color(old_file, CLIStyle.COLORS['WARNING'])}"
                )
                continue

            while True:
                new_name = self._render_pattern(pattern, old_file, number)
                if new_name is None:
                    pattern = self._prompt_pattern()
                    if not pattern:
                        return
                    continue

                print(
                    f"New name: {CLIStyle.color(new_name, CLIStyle.COLORS['CONTENT'])}"
                )
                try:
                    choice = (
                        input(
                            f"Action? "
                            f"({CLIStyle.color('[F]', CLIStyle.COLORS['WARNING'])} "
                            f"modify pattern, "
                            f"{CLIStyle.color('[S]', CLIStyle.COLORS['WARNING'])} "
                            "skip, ENTER to confirm): "
                        )
                        .strip()
                        .upper()
                    )
                except EOFError:
                    return

                if choice == "F":
                    pattern = self._prompt_pattern()
                    if not pattern:
                        return
                    continue
                if choice == "S":
                    print(
                        f"Skipped: "
                        f"{CLIStyle.color(old_file, CLIStyle.COLORS['CONTENT'])}"
                    )
                    break

                changes = self._prepare_changes([(old_file, new_name)])
                if changes is None:
                    break
                if self.dry_run:
                    print_status(
                        "Dry run: file was not changed.",
                        CLIStyle.COLORS["WARNING"],
                    )
                    break
                if self._apply_changes(changes):
                    print(
                        f"Renamed: "
                        f"{CLIStyle.color(old_file, CLIStyle.COLORS['CONTENT'])} "
                        f"=> {CLIStyle.color(new_name, CLIStyle.COLORS['CONTENT'])}"
                    )
                break

        self._show_statistics()

    def replace_in_name(
        self, file_list: Sequence[str], old_text: str, new_text: str
    ) -> None:
        """Replace text in selected filenames."""
        if not old_text:
            print_status("Old text must not be empty.", CLIStyle.COLORS["ERROR"])
            return
        self._execute_changes(
            (filename, filename.replace(old_text, new_text)) for filename in file_list
        )

    def sort_files(self, file_list: Sequence[str], width: int = 3) -> None:
        """Add an ordered prefix based on the current natural sort."""
        self._execute_changes(
            (
                filename,
                f"{index:0{width}d}-{filename}",
            )
            for index, filename in enumerate(file_list, start=1)
        )

    def lowercase_files(self, file_list: Sequence[str]) -> None:
        """Convert selected filenames to lowercase safely."""
        self._execute_changes((filename, filename.lower()) for filename in file_list)

    def _show_progress(self, current: int, total: int, prefix: str = "") -> None:
        if total == 0:
            return
        percent = current / total * 100
        filled = min(50, max(0, int(percent / 2)))
        bar = "█" * filled + "░" * (50 - filled)
        self.console.print(
            f"\r{prefix} [{bar}] {percent:.1f}% {current}/{total}",
            end="",
        )
        if current == total:
            self.console.print()


def create_example_text(script_name: str) -> str:
    """Build colored examples for the top-level help output."""
    examples = [
        ("Fast rename images and preserve extensions", "fast --type image"),
        ("Fast rename videos", "fast --type video --width 3"),
        ("Fast rename images and videos together", "fast --type all"),
        ("Preview a prefix operation", "--dry-run prefix --width 3"),
        ("Add numeric prefixes without prompting", "prefix --yes"),
        ("Interactive pattern rename", "interactive"),
        ("Replace text in filenames", "replace '_' '-'"),
        ("Sort and rename files", "sort --width 3"),
        ("Convert filenames to lowercase", "lowercase"),
    ]

    lines = [f"\n{CLIStyle.color('Examples:', CLIStyle.COLORS['SUB_TITLE'])}"]
    for description, command in examples:
        lines.append(
            f"  {CLIStyle.color(f'# {description}', CLIStyle.COLORS['EXAMPLE'])}"
        )
        lines.append(
            f"  {CLIStyle.color(f'{script_name} {command}', CLIStyle.COLORS['CONTENT'])}"
        )
        lines.append("")

    lines.extend(
        [
            f"{CLIStyle.color('Notes:', CLIStyle.COLORS['SUB_TITLE'])}",
            f"  {CLIStyle.color('- Fast rename preserves suffixes by default; --extension only changes the name.', CLIStyle.COLORS['CONTENT'])}",
            f"  {CLIStyle.color('- All changes are previewed before confirmation.', CLIStyle.COLORS['CONTENT'])}",
            f"  {CLIStyle.color('- --dry-run never changes files.', CLIStyle.COLORS['CONTENT'])}",
            f"  {CLIStyle.color('- Interactive placeholders: {{name}}, {{ext}}, {{num}}, and {{regex:pattern:group}}.', CLIStyle.COLORS['CONTENT'])}",
        ]
    )
    return "\n".join(lines)


def add_runtime_options(
    parser: argparse.ArgumentParser, suppress_defaults: bool = False
) -> None:
    """Add options shared by the root parser and every subcommand."""
    default = argparse.SUPPRESS if suppress_defaults else False
    parser.add_argument(
        "-d",
        "--dirs",
        "--directories",
        dest="include_dirs",
        action="store_true",
        default=default,
        help="Include directories in the rename queue.",
    )
    parser.add_argument(
        "-p",
        "--path",
        type=Path,
        default=argparse.SUPPRESS if suppress_defaults else None,
        metavar="DIR",
        help="Process DIR instead of the current directory.",
    )
    parser.add_argument(
        "-x",
        "--exclude",
        action="append",
        default=argparse.SUPPRESS if suppress_defaults else [],
        metavar="NAME",
        help="Exclude NAME; repeat the option for multiple names.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        default=default,
        help="Preview changes without modifying files.",
    )
    parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        default=default,
        help="Apply changes without asking for confirmation.",
    )
    parser.add_argument(
        "--debug",
        action="store_true",
        default=default,
        help="Enable debug output.",
    )


def build_parser() -> ColoredArgumentParser:
    """Create the complete command-line parser."""
    script_name = Path(sys.argv[0]).name
    parser = ColoredArgumentParser(
        description="Batch file renaming tool with safe, previewable operations.",
        epilog=create_example_text(script_name),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    add_runtime_options(parser)
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"%(prog)s {VERSION}",
        help="Show program version.",
    )

    subparsers = parser.add_subparsers(
        dest="command",
        metavar="COMMAND",
        parser_class=ColoredArgumentParser,
    )

    fast_parser = subparsers.add_parser(
        "fast",
        help="Rename supported media files sequentially.",
        description="Rename supported media files sequentially.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    add_runtime_options(fast_parser, suppress_defaults=True)
    fast_parser.add_argument(
        "-t",
        "--type",
        choices=[FileType.IMAGE, "img", FileType.VIDEO, FileType.ALL],
        default=FileType.IMAGE,
        help="File type to process; image, img, video, or all.",
    )
    fast_parser.add_argument(
        "-w",
        "--width",
        type=positive_int,
        default=None,
        help="Number width; defaults to the digits in the matching file count.",
    )
    fast_parser.add_argument(
        "-s",
        "--start-num",
        "--start_num",
        dest="start_num",
        type=nonnegative_int,
        default=1,
        help="Starting number.",
    )
    fast_parser.add_argument(
        "-e",
        "--extension",
        type=normalize_extension,
        default=None,
        help="Explicit target suffix; this does not convert file contents.",
    )

    prefix_parser = subparsers.add_parser(
        "prefix",
        help="Add or remove numeric prefixes.",
        description="Add or remove numeric prefixes.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    add_runtime_options(prefix_parser, suppress_defaults=True)
    prefix_parser.add_argument(
        "-w", "--width", type=positive_int, default=3, help="Number width."
    )
    prefix_parser.add_argument(
        "-m",
        "--mode",
        choices=["add", "remove"],
        default="add",
        help="Operation mode.",
    )
    prefix_parser.add_argument(
        "-s",
        "--start-num",
        "--start_num",
        dest="start_num",
        type=nonnegative_int,
        default=1,
        help="Starting number for add mode.",
    )

    interactive_parser = subparsers.add_parser(
        "interactive",
        aliases=["interact"],
        help="Rename files with an interactive pattern.",
        description="Rename files with an interactive pattern.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    add_runtime_options(interactive_parser, suppress_defaults=True)

    replace_parser = subparsers.add_parser(
        "replace",
        help="Replace text in filenames.",
        description="Replace text in filenames.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    add_runtime_options(replace_parser, suppress_defaults=True)
    replace_parser.add_argument("old", help="Text to replace.")
    replace_parser.add_argument(
        "new", nargs="?", default=None, help="Replacement text."
    )
    replace_parser.add_argument(
        "--blank",
        action="store_true",
        help="Replace with an empty string.",
    )

    sort_parser = subparsers.add_parser(
        "sort",
        help="Sort files and add an ordered prefix.",
        description="Sort files and add an ordered prefix.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    add_runtime_options(sort_parser, suppress_defaults=True)
    sort_parser.add_argument(
        "-w", "--width", type=positive_int, default=3, help="Number width."
    )

    lowercase_parser = subparsers.add_parser(
        "lowercase",
        help="Convert filenames to lowercase.",
        description="Convert filenames to lowercase.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    add_runtime_options(lowercase_parser, suppress_defaults=True)

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Parse arguments and execute one rename command."""
    global DEBUG_MODE

    parser = build_parser()
    args = parser.parse_args(argv)
    if args.debug:
        DEBUG_MODE = True
        debug("Debug mode enabled")

    if args.command is None:
        parser.print_help()
        return 0

    directory = Path(args.path or Path.cwd()).expanduser()
    if not directory.exists():
        print_status(
            f"Directory does not exist: '{directory}'",
            CLIStyle.COLORS["ERROR"],
        )
        return 1
    if not directory.is_dir():
        print_status(
            f"Path is not a directory: '{directory}'",
            CLIStyle.COLORS["ERROR"],
        )
        return 1

    renamer = FileRenamer(
        directory=directory,
        include_dirs=args.include_dirs,
        excluded_names=args.exclude,
        dry_run=args.dry_run,
        assume_yes=args.yes,
    )
    file_list = renamer.get_file_list()
    debug(
        "Selected directory",
        directory=renamer.directory,
        candidates=len(file_list),
    )

    if args.command == "fast":
        file_type = FileType.IMAGE if args.type == "img" else args.type
        renamer.fast_rename(
            file_type,
            args.width,
            args.start_num,
            args.extension,
        )
    elif args.command == "prefix":
        renamer.prefix_rename(file_list, args.width, args.mode, args.start_num)
    elif args.command in {"interactive", "interact"}:
        renamer.interactive_rename(file_list)
    elif args.command == "replace":
        if args.blank:
            replacement = ""
        elif args.new is not None:
            replacement = args.new
        else:
            print_status(
                "Provide replacement text or use --blank to delete it.",
                CLIStyle.COLORS["ERROR"],
            )
            return 2
        renamer.replace_in_name(file_list, args.old, replacement)
    elif args.command == "sort":
        renamer.sort_files(file_list, args.width)
    elif args.command == "lowercase":
        renamer.lowercase_files(file_list)

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print_status("\nOperation interrupted by user.", CLIStyle.COLORS["WARNING"])
        sys.exit(130)
    except Exception as error:
        if DEBUG_MODE:
            traceback.print_exc()
        print_status(f"\nError: {error}", CLIStyle.COLORS["ERROR"])
        sys.exit(1)
