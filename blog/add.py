#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Create Firefly posts and memos beside this authoring entry point."""

import argparse
import datetime
import importlib.util
import os
import re
import shlex
import shutil
import subprocess
import sys
import traceback
from pathlib import Path
from types import ModuleType
from typing import NoReturn, Sequence, TextIO

try:
    import readline  # noqa: F401 -- enables editable terminal input
except ImportError:
    pass


class CLIStyle:
    """Apply semantic colors only to interactive output destinations."""

    COLORS = {
        "TITLE": "1;36",
        "SUB_TITLE": "1;34",
        "CONTENT": "1;37",
        "OPTION": "1;32",
        "PATH": "1;35",
        "DEFAULT": "1;33",
        "EXAMPLE": "2",
        "SUCCESS": "1;32",
        "WARNING": "1;33",
        "ERROR": "1;31",
    }

    @staticmethod
    def color(text: str, role: str = "CONTENT", stream: TextIO | None = None) -> str:
        """Respect NO_COLOR and keep redirected output free of ANSI codes."""
        destination = stream if stream is not None else sys.stdout
        if "NO_COLOR" in os.environ or not destination.isatty():
            return text
        return f"\033[{CLIStyle.COLORS[role]}m{text}\033[0m"


class ColoredArgumentParser(argparse.ArgumentParser):
    """Color CLI help sections, option descriptions, examples, and errors."""

    def format_help(self) -> str:
        """Render readable help without color when stdout is redirected."""
        lines = []
        for line in super().format_help().splitlines():
            role = "CONTENT"
            if line.endswith(":") or line.startswith("usage:"):
                role = "TITLE"
            elif line.lstrip().startswith("--") or line.lstrip().startswith("-h"):
                role = "OPTION"
            elif line.lstrip().startswith("./"):
                role = "EXAMPLE"
            lines.append(CLIStyle.color(line, role))
        return "\n".join(lines) + "\n"

    def error(self, message: str) -> NoReturn:
        """Report argument errors with the same terminal styling."""
        self.print_usage(sys.stderr)
        self.exit(2, CLIStyle.color(f"Error: {message}\n", "ERROR", sys.stderr))


class AuthoringError(Exception):
    """Represent a recoverable authoring or environment error."""


class Cancelled(Exception):
    """Represent an explicit menu cancellation."""


def emit(message: str, role: str = "CONTENT") -> None:
    """Write one consistently styled line."""
    destination = sys.stderr if role == "ERROR" else sys.stdout
    print(CLIStyle.color(message, role, destination), file=destination)


def section(step: str, title: str) -> None:
    """Separate workflow steps with a visible title."""
    emit(f"\n[{step}] {title}", "TITLE")


def read_line(label: str, default: str | None = None, hint: str = "") -> str:
    """Read editable input with a visible default and an optional explanation."""
    if hint:
        emit(f"  {hint}", "EXAMPLE")
    prompt = CLIStyle.color(f"  {label}", "CONTENT")
    if default is not None:
        prompt += CLIStyle.color(f" [{default or 'empty'}]", "DEFAULT")
    prompt += CLIStyle.color(" > ", "SUB_TITLE")
    if sys.stdin.isatty() and sys.stdout.isatty() and "readline" in sys.modules:
        prompt = re.sub(r"(\x1b\[[0-9;]*m)", r"\001\1\002", prompt)
    try:
        answer = input(prompt)
    except EOFError as exception:
        raise AuthoringError(
            "Input ended; nothing else will be created."
        ) from exception
    return default if answer == "" and default is not None else answer


def choose(label: str, options: Sequence[tuple[str, str]], back: bool = False) -> int:
    """Return a numbered choice, or -1 when optional parent navigation is chosen."""
    for index, (name, detail) in enumerate(options, 1):
        line = CLIStyle.color(f"  {index:>2}) ", "SUB_TITLE")
        line += CLIStyle.color(name, "OPTION")
        if detail:
            line += CLIStyle.color(f"  {detail}", "EXAMPLE")
        print(line)
    if back:
        emit("   b) Back to parent folder", "EXAMPLE")
    emit("   q) Cancel", "EXAMPLE")
    while True:
        answer = read_line(label, "1").strip().lower()
        if answer in ("q", "quit"):
            raise Cancelled
        if back and answer in ("b", "back"):
            return -1
        numbers = [str(index) for index in range(1, len(options) + 1)]
        if answer in numbers:
            return numbers.index(answer)
        navigation = ", b to go back" if back else ""
        emit(
            f"Choose a number from 1 to {len(options)}{navigation}, or q to cancel.",
            "WARNING",
        )


def build_parser() -> ColoredArgumentParser:
    """Expose interactive mode and direct post/memo commands with shared options."""
    parser = ColoredArgumentParser(
        description="Create a post or memo next to add.py. Run without a type for the menu.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n  ./add.py\n  ./add.py post --editor 'code --wait'\n"
            "  ./add.py memo\n  ./add.py --init\n  ./add.py --env-file /path/to/blog.env\n\n"
            "Configuration:\n  Read .env beside add.py, or the file selected with --env-file.\n"
            "  A missing file starts setup: create it or provide an existing file.\n"
            "  Priority: command-line options > process environment > .env > defaults.\n"
            "  Relative FIREFLY_REPO_ROOT values in .env are based on its directory.\n"
            "  Values are literal; comments and single/double quotes are supported.\n\n"
            "Environment / .env keys:\n"
            "  FIREFLY_REPO_ROOT: tooling checkout\n"
            "  VISUAL, EDITOR: editor command (default: vi)\n"
            "  NO_COLOR: disable terminal colors\n\n"
            "  FIREFLY_SITE_CONFIG_PATH: optional repository-relative site TOML path\n\n"
            "Browse existing post folders one level at a time; /.. marks a folder with subfolders.\n"
            "Create additional folders yourself under posts/."
        ),
    )
    commands = parser.add_subparsers(dest="content_type", title="content type")
    children = [
        commands.add_parser(
            name,
            help=help_text,
            description=help_text,
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog=f"Examples:\n  ./add.py {name}\n  ./add.py {name} --editor 'code --wait'\n\n"
            "Files are saved next to add.py. Creating a file does not deploy the site.",
        )
        for name, help_text in (
            ("post", "Choose a post folder, then write an article."),
            ("memo", "Create a timestamped memo draft, then edit it."),
        )
    ]
    for command_parser in [parser, *children]:
        command_parser.add_argument(
            "--editor",
            metavar="COMMAND",
            default=argparse.SUPPRESS,
            help="editor command; quoted arguments are supported",
        )
        command_parser.add_argument(
            "--firefly-root",
            metavar="PATH",
            default=argparse.SUPPRESS,
            help="Firefly checkout containing tooling/",
        )
        command_parser.add_argument(
            "--env-file",
            metavar="PATH",
            default=argparse.SUPPRESS,
            help=".env configuration path; defaults to .env beside add.py",
        )
        command_parser.add_argument(
            "--init",
            action="store_true",
            default=argparse.SUPPRESS,
            help="prepare/read .env configuration and exit without creating content",
        )
        command_parser.add_argument(
            "--log",
            action="store_true",
            default=argparse.SUPPRESS,
            help="show a traceback for unexpected errors",
        )
    return parser


def read_env_file(env_path: Path) -> dict[str, str]:
    """Read single-line dotenv assignments as data without shell expansion."""
    settings = {}
    if not env_path.is_file():
        raise AuthoringError(f"Configuration must be a readable file: {env_path}")
    for number, line in enumerate(
        env_path.read_text(encoding="utf-8-sig").splitlines(), 1
    ):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        match = re.fullmatch(r"(?:export\s+)?([A-Za-z_][A-Za-z_0-9]*)\s*=(.*)", line)
        if match is None:
            raise AuthoringError(f"Invalid .env assignment at {env_path}:{number}.")
        key, raw_value = match.groups()
        if key in settings:
            raise AuthoringError(f"Repeated .env key {key} at {env_path}:{number}.")
        raw_value = raw_value.strip()
        if raw_value.startswith(("'", '"')):
            try:
                tokens = shlex.split(raw_value, comments=True, posix=True)
            except ValueError as exception:
                raise AuthoringError(
                    f"Invalid quoted .env value at {env_path}:{number}."
                ) from exception
            if len(tokens) != 1:
                raise AuthoringError(
                    f"Expected one quoted .env value at {env_path}:{number}."
                )
            value = tokens[0]
        else:
            value = (
                ""
                if raw_value.startswith("#")
                else re.split(r"\s+#", raw_value, maxsplit=1)[0].rstrip()
            )
        if "\x00" in value:
            raise AuthoringError(f"Invalid control character at {env_path}:{number}.")
        settings[key] = value
    return settings


def configured_path(value: str | Path, base: Path) -> Path:
    """Resolve a user path relative to its documented configuration source."""
    path = Path(value).expanduser()
    return (path if path.is_absolute() else base / path).resolve()


def validate_firefly_root(root: Path) -> None:
    """Require the existing post and memo tool entry points before authoring."""
    required = ("tooling/new-article.py", "tooling/memo-documents/cli.mjs")
    if not all((root / relative).is_file() for relative in required):
        raise AuthoringError(
            f"Not a Firefly checkout: {root}. Set FIREFLY_REPO_ROOT in .env or use --firefly-root."
        )


def create_env_file(
    env_path: Path, content_root: Path, options: argparse.Namespace
) -> None:
    """Collect basic settings and create an owner-only file without overwriting one."""
    if not env_path.parent.is_dir():
        raise AuthoringError(
            f"The configuration directory does not exist: {env_path.parent}"
        )
    suggested = getattr(options, "firefly_root", None) or os.environ.get(
        "FIREFLY_REPO_ROOT"
    )
    if suggested:
        suggested = str(configured_path(suggested, Path.cwd()))
    elif (content_root.parent / "tooling/new-article.py").is_file():
        suggested = os.path.relpath(content_root.parent, env_path.parent)
    while True:
        repo_value = read_line(
            "FIREFLY_REPO_ROOT",
            suggested,
            "Enter your Firefly checkout path, not the blog folder. Relative paths are based on the .env folder.",
        ).strip()
        if not repo_value:
            emit("A Firefly repository path is required.", "WARNING")
            continue
        try:
            validate_firefly_root(configured_path(repo_value, env_path.parent))
        except AuthoringError as exception:
            emit(str(exception), "WARNING")
            continue
        break
    editor_default = (
        getattr(options, "editor", None)
        or os.environ.get("VISUAL")
        or os.environ.get("EDITOR")
        or "vi"
    )
    while True:
        editor_value = read_line(
            "EDITOR",
            editor_default,
            "Examples: vi, nvim, or code --wait. The editor must be installed before authoring.",
        )
        try:
            if not shlex.split(editor_value) or any(
                ord(char) < 32 for char in editor_value
            ):
                raise ValueError
        except ValueError:
            emit(
                "Enter a nonempty, single-line editor command with balanced quotes.",
                "WARNING",
            )
            continue
        break
    contents = (
        "# Local settings for add.py. Relative repo paths use this file's folder.\n"
        f"FIREFLY_REPO_ROOT={shlex.quote(repo_value)}\n"
        f"EDITOR={shlex.quote(editor_value)}\n"
    )
    descriptor = os.open(env_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
        stream.write(contents)
    emit(f"Created configuration: {env_path}", "SUCCESS")


def choose_existing_env_file() -> Path:
    """Ask for an existing configuration without copying or modifying it."""
    while True:
        provided = read_line(
            "Existing .env path",
            hint="This file is used for this run; use --env-file PATH on future runs.",
        ).strip()
        candidate = Path(provided).expanduser().absolute()
        if provided and candidate.is_file():
            return candidate
        emit("Provide the path to an existing readable .env file.", "WARNING")


def load_configuration(
    content_root: Path, options: argparse.Namespace
) -> tuple[Path, dict[str, str]]:
    """Load the chosen dotenv file or guide first-time setup without implicit overwrites."""
    requested = getattr(options, "env_file", None)
    env_path = (
        Path(requested).expanduser().absolute() if requested else content_root / ".env"
    )
    if not env_path.exists():
        section("Setup", "Choose your configuration")
        emit(f"Configuration not found: {env_path}", "PATH")
        action = choose(
            "Setup option",
            [
                ("Create .env", f"write {env_path}"),
                ("Use an existing .env", "enter its path"),
            ],
        )
        if action == 0:
            create_env_file(env_path, content_root, options)
        else:
            env_path = choose_existing_env_file()
    settings = read_env_file(env_path)
    return env_path, settings


def load_article_tools(firefly_root: Path) -> ModuleType:
    """Load the existing article helpers without generating a tooling bytecode cache."""
    script = firefly_root / "tooling/new-article.py"
    if not script.is_file():
        raise AuthoringError(f"Post tooling not found: {script}. Set --firefly-root.")
    spec = importlib.util.spec_from_file_location("firefly_authoring_article", script)
    if spec is None or spec.loader is None:
        raise AuthoringError("Cannot load Firefly article tooling.")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    previous = sys.dont_write_bytecode
    sys.dont_write_bytecode = True
    try:
        spec.loader.exec_module(module)
    finally:
        sys.dont_write_bytecode = previous
    return module


def child_directories(directory: Path) -> list[Path]:
    """Discover sorted immediate subfolders without following symlinks."""
    if directory.is_symlink() or not directory.is_dir():
        raise AuthoringError(f"A regular directory is required: {directory}")
    return sorted(
        (
            item
            for item in directory.iterdir()
            if not item.is_symlink() and item.is_dir()
        ),
        key=lambda item: item.name,
    )


def choose_directory(content_root: Path) -> Path:
    """Browse folders by level, selecting leaves or explicitly choosing the current folder."""
    posts_root = content_root / "posts"
    current = posts_root
    section("1/3", "Choose the post folder")
    emit(
        "Choose a /.. folder to browse its subfolders. Other folders are selected directly.",
        "EXAMPLE",
    )
    while True:
        directories = child_directories(current)
        current_label = f"{current.relative_to(content_root).as_posix()}/"
        emit(f"\nCurrent folder: {current_label}", "PATH")
        has_children = [bool(child_directories(item)) for item in directories]
        options = [("Write in this folder", current_label)] + [
            (
                f"{item.name}/.." if nested else f"{item.name}/",
                "browse subfolders" if nested else "select folder",
            )
            for item, nested in zip(directories, has_children)
        ]
        choice = choose("Folder number", options, back=current != posts_root)
        if choice == -1:
            current = current.parent
        elif choice == 0:
            return current
        elif has_children[choice - 1]:
            current = directories[choice - 1]
        else:
            return directories[choice - 1]


def choose_filename(
    directory: Path, default: str, article: ModuleType | None = None
) -> Path:
    """Retry invalid filenames and protect existing files before invoking tooling."""
    emit(f"Save folder: {directory}", "PATH")
    while True:
        filename = read_line(
            "Filename", default, "Enter a filename only; .md is added automatically."
        )
        if not filename.endswith(".md"):
            filename += ".md"
        if article is None and filename.startswith("--"):
            emit("Memo filenames cannot begin with --. Choose another name.", "WARNING")
            continue
        if filename.startswith(".") or re.search(r"[\\/?#%:\x00-\x1f\x7f]", filename):
            emit(
                "Use a nonhidden filename without directory separators or URL/control characters.",
                "WARNING",
            )
            continue
        if article is not None:
            try:
                article.validate_path_segment(filename, "filename")
            except article.ArticleError as exception:
                emit(str(exception), "WARNING")
                continue
        target = directory / filename
        if target.exists() or target.is_symlink():
            emit(f"Already exists: {target.name}. Choose another filename.", "WARNING")
            continue
        emit(f"Save as: {target}", "PATH")
        return target


def read_post_field(prompt: str, default: str | None = None) -> str:
    """Adapt existing post metadata prompts while retaining backend validation."""
    hints = {
        "Title": "The heading readers will see.",
        "Description": "A short summary shown in article previews.",
        "Publication date": "Use YYYY-MM-DD; the default is today's UTC date.",
        "Tags (comma-separated, optional)": "Separate tags with commas, or press Enter for no tags.",
        "Access (public or private:OWNER)": "Use public or private:OWNER; this is separate from draft status.",
    }
    if prompt.startswith("Publish immediately?"):
        return read_line(
            "Visible on the next site build? [y/N]",
            hint="Enter keeps draft: true; y sets draft: false. This command only saves locally.",
        )
    if prompt.startswith("Create this article?"):
        return read_line(
            "Save this post? [Y/n]",
            hint="Press Enter to save, or n to discard the temporary content.",
        )
    return read_line(prompt, default, hints.get(prompt, ""))


def default_post_filename(directory: Path) -> str:
    """Suggest the next local Markdown index using the folder's existing padding."""
    indices = []
    for item in directory.iterdir():
        if item.is_symlink() or not item.is_file():
            continue
        match = re.fullmatch(r"([0-9]+)-.+\.md", item.name)
        if match:
            prefix = match.group(1)
            indices.append((int(prefix), len(prefix)))
    next_index = max((index for index, _ in indices), default=0) + 1
    width = max((width for _, width in indices), default=2)
    return f"{next_index:0{width}d}-new-post.md"


def create_post(
    content_root: Path, firefly_root: Path, editor_spec: str, log: bool = False
) -> int:
    """Delegate post creation and schema validation to the existing article tool."""
    article = load_article_tools(firefly_root)
    directory = choose_directory(content_root)
    section("2/3", "Name the post")
    emit(
        "The suggested filename uses this folder's highest Markdown index + 1. You can change it.",
        "EXAMPLE",
    )
    target = choose_filename(directory, default_post_filename(directory), article)
    section("3/3", "Metadata, editor, and save confirmation")
    emit(f"Editor: {editor_spec}", "SUB_TITLE")
    emit(
        "Answer the metadata questions, then save and close the editor.\n"
        "The final confirmation saves the Markdown file in the selected folder.",
        "EXAMPLE",
    )
    article.read_line = read_post_field
    previous_directory = Path.cwd()
    try:
        os.chdir(content_root)
        arguments = [
            "--blog-root",
            str(content_root),
            "--collection",
            "posts",
            "--editor",
            editor_spec,
            target.relative_to(content_root).as_posix(),
        ]
        if log:
            arguments.append("--log")
        result = article.main(arguments)
    finally:
        os.chdir(previous_directory)
    if result == 0:
        emit(
            f"Saved post: {target}"
            if target.is_file()
            else "Cancelled; the post was not saved.",
            "SUCCESS" if target.is_file() else "WARNING",
        )
    return result


def create_memo(content_root: Path, firefly_root: Path, editor_spec: str) -> int:
    """Create an absent-only memo draft with the existing stable-identity tooling."""
    script = firefly_root / "tooling/memo-documents/cli.mjs"
    if not script.is_file():
        raise AuthoringError(f"Memo tooling not found: {script}. Set --firefly-root.")
    section("1/2", "Name the memo")
    emit("A memo is a short Markdown note. It starts as a draft.", "EXAMPLE")
    timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d-%H%M%S")
    target = choose_filename(content_root / "memos", f"{timestamp}.md")
    result = subprocess.run(
        ["node", str(script), "new", target.name, "--source-root", str(target.parent)],
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode:
        raise AuthoringError(result.stderr.strip() or "Memo creation failed.")
    section("2/2", "Write the memo in the editor")
    emit(f"Created draft: {target}", "SUCCESS")
    emit(f"Editor: {editor_spec}", "SUB_TITLE")
    emit(
        "Write your note after the closing --- line. Save and close the editor to finish.",
        "EXAMPLE",
    )
    emit(
        'Keep id and date unchanged. You may add title: "Your title" in the metadata.',
        "EXAMPLE",
    )
    emit(
        "draft: true keeps it hidden; set draft: false for visibility on the next site build.",
        "WARNING",
    )
    try:
        result = subprocess.run([*shlex.split(editor_spec), str(target)], check=False)
    except OSError as exception:
        raise AuthoringError(
            f"Editor could not start; the draft remains at {target}: {exception}"
        ) from exception
    if result.returncode:
        raise AuthoringError(
            f"Editor failed ({result.returncode}); the draft remains at {target}."
        )
    if target.is_symlink() or not target.is_file():
        raise AuthoringError(
            f"The editor did not leave a regular memo file at {target}."
        )
    emit(f"Saved memo: {target}", "SUCCESS")
    emit(
        "The file is saved locally. Its draft field controls visibility on the next site build.",
        "EXAMPLE",
    )
    return 0


def main(arguments: Sequence[str] | None = None) -> int:
    """Run authoring with friendly cancellation and actionable errors."""
    options = build_parser().parse_args(arguments)
    try:
        content_root = Path(__file__).resolve().parent
        env_path, settings = load_configuration(content_root, options)
        for key in ("NO_COLOR", "FIREFLY_SITE_CONFIG_PATH"):
            if key in settings:
                os.environ.setdefault(key, settings[key])
        emit("\nFirefly / Add content", "TITLE")
        emit(f"Content root: {content_root}", "PATH")
        emit(f"Configuration: {env_path}", "PATH")
        emit(
            "Press Enter to accept a value in brackets. Use q in menus or Ctrl+C to cancel.",
            "EXAMPLE",
        )
        root_override = getattr(options, "firefly_root", None) or os.environ.get(
            "FIREFLY_REPO_ROOT"
        )
        root_value = (
            root_override or settings.get("FIREFLY_REPO_ROOT") or content_root.parent
        )
        firefly_root = configured_path(
            root_value, Path.cwd() if root_override else env_path.parent
        )
        validate_firefly_root(firefly_root)
        if getattr(options, "init", False):
            emit(f"Configuration ready. Firefly repository: {firefly_root}", "SUCCESS")
            return 0
        content_type = options.content_type
        if content_type is None:
            section("Start", "What would you like to write?")
            content_type = ("post", "memo")[
                choose(
                    "Content type",
                    [
                        ("Add post", "article with title, summary, tags, and access"),
                        (
                            "Add memo",
                            "short note with an automatic ID and UTC timestamp",
                        ),
                    ],
                )
            ]
        editor_spec = (
            getattr(options, "editor", None)
            or os.environ.get("VISUAL")
            or os.environ.get("EDITOR")
            or settings.get("VISUAL")
            or settings.get("EDITOR")
            or "vi"
        )
        command = shlex.split(editor_spec)
        if not command or shutil.which(command[0]) is None:
            raise AuthoringError(
                f"Editor not found: {editor_spec}. Set --editor, VISUAL, or EDITOR."
            )
        if shutil.which("node") is None:
            raise AuthoringError(
                "Node.js is required by Firefly tooling; node was not found in PATH."
            )
        if content_type == "post":
            return create_post(
                content_root, firefly_root, editor_spec, getattr(options, "log", False)
            )
        return create_memo(content_root, firefly_root, editor_spec)
    except Cancelled:
        emit("Cancelled; no content file was created.", "WARNING")
        return 0
    except KeyboardInterrupt:
        emit(
            "\nCancelled. Any memo draft already created is kept at the displayed path.",
            "WARNING",
        )
        return 130
    except (AuthoringError, OSError, ValueError) as exception:
        emit(f"Error: {exception}", "ERROR")
        return 1
    except Exception as exception:
        if getattr(options, "log", False):
            traceback.print_exc()
        emit(f"Error: {exception}. Run again with --log for details.", "ERROR")
        return 1


if __name__ == "__main__":
    sys.exit(main())
