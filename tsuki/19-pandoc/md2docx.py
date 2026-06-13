# -*- coding: utf-8 -*-
# pip install python-docx
# requires the `pandoc` binary in PATH

"""
Convert markdown files to docx via pandoc, then apply custom table/caption
styles through docx-table-style.py.

Resource resolution order for both `docx-table-style.py` and
`pandoc-template.docx`:

  1. same directory as this script
  2. local repo copy under `<local_repo_path>/tsuki/19-pandoc/`
  3. `~/.genshin/pandoc/` (downloaded from github on first use)
"""

import argparse
import datetime
import importlib.util
import shutil
import subprocess
import sys
import urllib.request
from pathlib import Path
from types import ModuleType

DEBUG_MODE = False

HOME = Path.home()
LEADER_PATH_NAME = "cargo"
LOCAL_REPO_PATH = HOME / LEADER_PATH_NAME / "repo/04-flyMe2theStar/03-genshin"
REPO_PANDOC_SUBPATH = "tsuki/19-pandoc"
GENSHIN_PANDOC_DIR = HOME / ".genshin" / "pandoc"
GITHUB_USERNAME = "sparkuru"
GITHUB_URL_BASE = f"https://raw.githubusercontent.com/{GITHUB_USERNAME}/genshin/main"

STYLE_SCRIPT_NAME = "docx-table-style.py"
TEMPLATE_NAME = "pandoc-template.docx"

CHAR_THRESHOLD = 60
MAX_MERGE_COLS = 3
FORMAT_TABLE = True


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
    """ArgumentParser with semantic colorized help output."""

    def _format_action_invocation(self, action: argparse.Action) -> str:
        if not action.option_strings:
            (metavar,) = self._metavar_formatter(action, action.dest)(1)
            return metavar

        parts = []
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
        formatter = self._get_formatter()
        if self.description:
            formatter.add_text(
                CLIStyle.color(self.description, CLIStyle.COLORS["TITLE"])
            )
        formatter.add_usage(
            self.usage, self._actions, self._mutually_exclusive_groups
        )
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
    script_name: str, examples: list, notes: list | None = None
) -> str:
    """Build a colorized examples/notes epilog block."""
    text = f"\n{CLIStyle.color('Examples:', CLIStyle.COLORS['SUB_TITLE'])}"
    for desc, cmd in examples:
        text += f"\n  {CLIStyle.color(f'# {desc}', CLIStyle.COLORS['EXAMPLE'])}"
        text += f"\n  {CLIStyle.color(f'{script_name} {cmd}', CLIStyle.COLORS['CONTENT'])}\n"
    if notes:
        text += f"\n{CLIStyle.color('Notes:', CLIStyle.COLORS['SUB_TITLE'])}"
        for note in notes:
            text += f"\n  {CLIStyle.color(f'- {note}', CLIStyle.COLORS['CONTENT'])}"
    return text


def log(message: str, color: int = CLIStyle.COLORS["CONTENT"]) -> None:
    """Print a timestamped colorized status line."""
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(CLIStyle.color(f"[{ts}] {message}", color))


def download_file(url: str, dst: Path) -> bool:
    """Download `url` to `dst`, creating parent dirs. Return success flag."""
    try:
        dst.parent.mkdir(parents=True, exist_ok=True)
        log(f"downloading {url}", CLIStyle.COLORS["WARNING"])
        urllib.request.urlretrieve(url, dst)
        return dst.is_file()
    except Exception as e:
        if DEBUG_MODE:
            import traceback

            traceback.print_exc()
        log(f"download failed: {e}", CLIStyle.COLORS["ERROR"])
        return False


def resolve_resource(name: str, script_dir: Path, downloadable: bool) -> Path | None:
    """Resolve a resource file by the script/repo/.genshin lookup chain."""
    same_dir = script_dir / name
    if same_dir.is_file():
        return same_dir

    repo_copy = LOCAL_REPO_PATH / REPO_PANDOC_SUBPATH / name
    if repo_copy.is_file():
        return repo_copy

    genshin_copy = GENSHIN_PANDOC_DIR / name
    if genshin_copy.is_file():
        return genshin_copy

    if downloadable:
        url = f"{GITHUB_URL_BASE}/{REPO_PANDOC_SUBPATH}/{name}"
        if download_file(url, genshin_copy):
            return genshin_copy
    return None


def load_style_module(style_script: Path) -> ModuleType:
    """Import docx-table-style.py as a module despite its hyphenated name."""
    spec = importlib.util.spec_from_file_location("docx_table_style", style_script)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load module from {style_script}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def apply_table_style(
    docx_path: Path,
    style_module: ModuleType,
    threshold: int,
    max_merge_cols: int,
    format_table: bool,
) -> None:
    """Apply custom table/caption styles in place using the style module."""
    style_module.CHAR_THRESHOLD = threshold
    style_module.MAX_MERGE_COLS = max(0, max_merge_cols)
    style_module.FORMAT_TABLE_ENABLED = format_table
    style_module.DEBUG_MODE = DEBUG_MODE
    doc = style_module.Document(str(docx_path))
    style_module.process_document(doc)
    doc.save(str(docx_path))


def collect_markdown_files(
    target: Path | None, work_dir: Path
) -> tuple[list[Path], Path]:
    """Return (markdown files, markdown dir) from an optional path target."""
    if target is None:
        return sorted(work_dir.glob("*.md")), work_dir
    if target.is_file():
        if target.suffix.lower() not in (".md", ".markdown"):
            raise ValueError(f"not a markdown file: {target}")
        return [target], target.parent
    if target.is_dir():
        return sorted(target.glob("*.md")), target
    raise FileNotFoundError(f"path not found: {target}")


def convert_one(
    src_md: Path,
    dst_docx: Path,
    template: Path | None,
    style_module: ModuleType | None,
    threshold: int,
    max_merge_cols: int,
    format_table: bool,
) -> bool:
    """Convert a single markdown file to docx and post-process it."""
    cmd = ["pandoc", "--from", "markdown", "--to", "docx", "--output", str(dst_docx)]
    if template is not None:
        cmd += ["--reference-doc", str(template)]
    cmd.append(str(src_md))

    result = subprocess.run(cmd)
    if result.returncode != 0:
        log(
            f"pandoc failed (exit {result.returncode}), skip: {src_md.name}",
            CLIStyle.COLORS["ERROR"],
        )
        return False

    if style_module is not None:
        apply_table_style(
            dst_docx, style_module, threshold, max_merge_cols, format_table
        )
    return True


def main() -> int:
    """Main program logic."""
    global DEBUG_MODE

    script_name = Path(sys.argv[0]).name
    epilog = create_example_text(
        script_name,
        examples=[
            ("convert every *.md in the current directory", ""),
            ("convert markdown files under a directory", "./markdown"),
            ("convert a single markdown file", "./notes/07-test.md"),
            ("overwrite existing docx outputs", "-f"),
            ("output beside the source instead of ./docx", "./a.md --same-dir"),
        ],
        notes=[
            "outputs land in <dir>/docx/ by default",
            "needs the `pandoc` binary and the python-docx package",
            f"styles resolve from: script dir -> {LOCAL_REPO_PATH}/{REPO_PANDOC_SUBPATH} -> ~/.genshin/pandoc",
        ],
    )

    parser = ColoredArgumentParser(
        description="Convert markdown to docx via pandoc with custom table styles.",
        epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "path",
        nargs="?",
        type=Path,
        default=None,
        help="markdown file or directory (default: current directory).",
    )
    parser.add_argument(
        "-f",
        "--force",
        action="store_true",
        help="overwrite existing docx outputs.",
    )
    parser.add_argument(
        "--same-dir",
        action="store_true",
        help="write output beside the source instead of ./docx.",
    )
    parser.add_argument(
        "--threshold",
        type=int,
        default=CHAR_THRESHOLD,
        help=f"long-cell character threshold (default: {CHAR_THRESHOLD}).",
    )
    parser.add_argument(
        "--max-merge-cols",
        type=int,
        default=MAX_MERGE_COLS,
        help=f"leading columns to vertically merge (default: {MAX_MERGE_COLS}).",
    )
    parser.add_argument(
        "--no-format-table",
        action="store_true",
        help="disable hierarchical column merging.",
    )
    parser.add_argument(
        "--log", action="store_true", help="enable debug logging."
    )
    args = parser.parse_args()
    DEBUG_MODE = args.log

    if shutil.which("pandoc") is None:
        log("pandoc not found in PATH; install: sudo apt install pandoc", CLIStyle.COLORS["ERROR"])
        return 1

    work_dir = Path.cwd()
    try:
        md_files, markdown_dir = collect_markdown_files(args.path, work_dir)
    except (ValueError, FileNotFoundError) as e:
        log(str(e), CLIStyle.COLORS["ERROR"])
        return 1

    md_files = [f for f in md_files if f.stat().st_size > 0]
    if not md_files:
        log(f"no markdown files found in: {markdown_dir}", CLIStyle.COLORS["WARNING"])
        log("tip: run beside *.md files or pass a directory", CLIStyle.COLORS["WARNING"])
        return 0

    template = resolve_resource(TEMPLATE_NAME, work_dir, downloadable=True)
    if template is None:
        log("pandoc-template.docx not found; using pandoc default", CLIStyle.COLORS["WARNING"])

    style_script = resolve_resource(STYLE_SCRIPT_NAME, work_dir, downloadable=True)
    style_module: ModuleType | None = None
    if style_script is not None:
        try:
            style_module = load_style_module(style_script)
        except ImportError as e:
            log(str(e), CLIStyle.COLORS["ERROR"])
            return 1
        except ModuleNotFoundError:
            log("python-docx not found; install: pip install python-docx", CLIStyle.COLORS["ERROR"])
            return 1
    else:
        log("docx-table-style.py not found; skipping style post-process", CLIStyle.COLORS["WARNING"])

    output_dir = markdown_dir if (args.same_dir and len(md_files) == 1) else markdown_dir / "docx"
    output_dir.mkdir(parents=True, exist_ok=True)

    converted = 0
    for src_md in md_files:
        dst_docx = output_dir / f"{src_md.stem}.docx"
        if dst_docx.exists() and not args.force:
            log(f"{dst_docx.name} already exists, skip...", CLIStyle.COLORS["ERROR"])
            continue
        log(f"convert {src_md.name} --> {dst_docx.name}", CLIStyle.COLORS["CONTENT"])
        try:
            if convert_one(
                src_md,
                dst_docx,
                template,
                style_module,
                args.threshold,
                args.max_merge_cols,
                not args.no_format_table,
            ):
                converted += 1
        except Exception as e:
            if DEBUG_MODE:
                import traceback

                traceback.print_exc()
            log(f"failed on {src_md.name}: {e}", CLIStyle.COLORS["ERROR"])

    log(f"done, {converted}/{len(md_files)} converted -> {output_dir}", CLIStyle.COLORS["CONTENT"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
