# -*- coding: utf-8 -*-
"""
Markdown helper toolkit for better Typora / Markdown writing experience.

Sub-commands:
- cleanimg / ci       : Clean unreferenced images in assets directory.
- datamasking / dm    : Mask sensitive strings in markdown files using Faker, with undo support.
- tableformat / tf    : Unflatten Word-pasted tables (restore merged-cell hierarchy).
"""

import argparse
import json
import re
import shutil
import sys
import tempfile
from glob import glob
from typing import Dict, List

from faker import Faker
from pathlib import Path
from urllib.parse import unquote

DEBUG_MODE = False

IMAGE_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".gif",
    ".bmp",
    ".svg",
    ".tiff",
    ".ico",
}

MD_IMAGE_PATTERNS = [
    re.compile(r"!\[.*?\]\((.+?)\)"),
    re.compile(r'<img\s[^>]*src=["\']([^"\']+)["\']', re.IGNORECASE),
    re.compile(r"^\[.*?\]:\s*(.+)$", re.MULTILINE),
]

DM_BACKUP_PREFIX = "mdtool-dm-"
DM_MAP_PREFIX = DM_BACKUP_PREFIX + "map-"
TF_BACKUP_PREFIX = "mdtool-tf-"


def debug(*args, **kwargs) -> None:
    if not DEBUG_MODE:
        return
    import inspect

    frame = inspect.currentframe().f_back
    prefix = f"[DEBUG {Path(frame.f_code.co_filename).name}:{frame.f_lineno}]"
    print(prefix, *args, **kwargs, file=sys.stderr)


class CLIStyle:
    COLORS = {
        "TITLE": 7,
        "SUB_TITLE": 2,
        "CONTENT": 3,
        "EXAMPLE": 7,
        "WARNING": 4,
        "ERROR": 2,
        "INFO": 5,
        "OK": 3,
    }

    @staticmethod
    def color(text: str, color: int = 3) -> str:
        codes = {
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
        return codes[color].format(text)

    @staticmethod
    def print(text: str, color: int = 0) -> None:
        print(CLIStyle.color(text, color) if color else text)


def _build_main_epilog(script_name: str) -> str:
    C = CLIStyle.color
    T = CLIStyle.COLORS
    lines = [
        C("Examples:", T["TITLE"]),
        C("  # 1) Clean unreferenced images", T["SUB_TITLE"]),
        C(f"  {script_name} cleanimg -d ~/notes --assets assets", T["EXAMPLE"]),
        C(f"  {script_name} cleanimg -d ~/notes --dry-run", T["EXAMPLE"]),
        C(f"  {script_name} cleanimg --rm -y", T["EXAMPLE"]),
        "",
        C("  # 2) Data masking in markdown files (and undo)", T["SUB_TITLE"]),
        C(f'  {script_name} datamasking "SECRET1" "SECRET2"', T["EXAMPLE"]),
        C(
            f'  {script_name} datamasking /path/to/file.md "SECRET"',
            T["EXAMPLE"],
        ),
        C(
            f'  {script_name} datamasking --path "*.md" "SECRET"',
            T["EXAMPLE"],
        ),
        C(
            f"  {script_name} datamasking --marker --sensitive-file secrets.txt --path file.md",
            T["EXAMPLE"],
        ),
        C(
            f"  {script_name} datamasking --restore --path file.md --field DB_PASSWORD",
            T["EXAMPLE"],
        ),
        C(f"  {script_name} datamasking undo", T["EXAMPLE"]),
        C(f"  {script_name} datamasking undo -y", T["EXAMPLE"]),
        "",
        C("  # 3) Unflatten Word-pasted tables", T["SUB_TITLE"]),
        C(f"  {script_name} tableformat -d .", T["EXAMPLE"]),
        C(f"  {script_name} tableformat path/to/file.md", T["EXAMPLE"]),
        C(f"  {script_name} tableformat --dry-run path/to/file.md", T["EXAMPLE"]),
        C(f"  {script_name} tableformat undo", T["EXAMPLE"]),
        C(f"  {script_name} tableformat undo -y", T["EXAMPLE"]),
        "",
        C("Notes:", T["TITLE"]),
        C(
            "  cleanimg        : Unreferenced images are MOVED to /tmp by default.",
            T["CONTENT"],
        ),
        C(
            "                   Use --rm only when you are sure they are no longer needed.",
            T["WARNING"],
        ),
        C(
            "  datamasking     : Target can be directory, file path or glob pattern.",
            T["CONTENT"],
        ),
        C(
            "                   Per-string and per-file replacement counts are reported.",
            T["CONTENT"],
        ),
        C(
            "                   Non-dry-run runs create /tmp backups, which 'undo' can restore.",
            T["CONTENT"],
        ),
        C(
            "  tableformat      : Restores empty cells for merged columns (e.g. domain/device) from Word.",
            T["CONTENT"],
        ),
        C(
            "                   Non-dry-run runs create /tmp backups, which 'undo' can restore.",
            T["CONTENT"],
        ),
    ]
    return "\n".join(lines)


def _build_parser() -> argparse.ArgumentParser:
    script_name = Path(sys.argv[0]).name
    parser = argparse.ArgumentParser(
        description=(
            "Markdown helper toolkit.\n"
            "- cleanimg / ci     : Clean unreferenced images in assets directory.\n"
            "- datamasking / dm  : Mask sensitive strings in markdown files using Faker or reversible markers.\n"
            "- tableformat / tf  : Unflatten Word-pasted tables (restore merged-cell hierarchy)."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=_build_main_epilog(script_name),
    )
    parser.add_argument(
        "--log",
        action="store_true",
        help="Enable debug output (prints to stderr)",
    )

    subparsers = parser.add_subparsers(dest="command", help="Sub-commands")

    clean_parser = subparsers.add_parser(
        "cleanimg",
        aliases=["ci"],
        help="Clean unreferenced images in assets directory",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description="Scan markdown files and move/delete unreferenced images in assets directory.",
    )
    clean_parser.add_argument(
        "-d",
        "--directory",
        default=".",
        metavar="DIR",
        help="Directory to scan for .md/.markdown files (default: cwd)",
    )
    clean_parser.add_argument(
        "--assets",
        default="./assets",
        metavar="DIR",
        help="Path to the assets/images directory (default: ./assets)",
    )
    clean_parser.add_argument(
        "--rm",
        action="store_true",
        help="Permanently delete unreferenced images instead of moving to /tmp",
    )
    clean_parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Skip confirmation prompt and proceed immediately",
    )
    clean_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List unreferenced images only, perform no file operations",
    )

    mask_parser = subparsers.add_parser(
        "datamasking",
        aliases=["dm"],
        help=(
            "Mask sensitive strings in markdown files using Faker or reversible markers"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=(
            "Data masking for markdown content.\n"
            "- Faker mode (default): replace sensitive values with random fake strings.\n"
            "- Marker mode (--marker): replace values with readable placeholders "
            "like [[MASK:LABEL:0000]] and save mappings to /tmp for later restore.\n"
            "Use --sensitive-file to load keys from a file and --restore/--field to "
            "restore markers back to original values."
        ),
    )
    mask_parser.add_argument(
        "sensitive",
        nargs="*",
        help=(
            "Sensitive strings to be masked. "
            "In marker mode, supports LABEL=VALUE format."
        ),
    )
    mask_parser.add_argument(
        "-d",
        "--directory",
        default=".",
        metavar="DIR",
        help="Directory containing markdown files to process when no explicit path is provided (default: cwd)",
    )
    mask_parser.add_argument(
        "--path",
        metavar="PATH",
        help=(
            "Target directory / file / glob pattern to process. "
            "If omitted, use -d/--directory. "
            "If not set but the first sensitive argument looks like a path or glob, "
            "it will be treated as PATH automatically."
        ),
    )
    mask_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show planned replacements without modifying any files",
    )
    mask_parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Skip confirmation prompt (e.g. for 'dm undo')",
    )
    mask_parser.add_argument(
        "-i",
        "--ignore-case",
        action="store_true",
        help="Ignore case when matching sensitive strings",
    )
    mask_parser.add_argument(
        "--marker",
        action="store_true",
        help=(
            "Use reversible marker placeholders instead of random fake data. "
            "Markers are written as [[MASK:LABEL:NNNN]]."
        ),
    )
    mask_parser.add_argument(
        "--restore",
        action="store_true",
        help=(
            "Restore marker placeholders in files using the latest mapping in /tmp. "
            "Use together with --path or -d/--directory."
        ),
    )
    mask_parser.add_argument(
        "--field",
        action="append",
        metavar="LABEL",
        help=(
            "When restoring markers, only restore entries with the given LABEL. "
            "Can be specified multiple times."
        ),
    )
    mask_parser.add_argument(
        "--sensitive-file",
        metavar="FILE",
        help=(
            "Load sensitive values from file. Each non-empty, non-comment line "
            "is parsed as LABEL:VALUE (for marker mode, e.g. fsm:787) or VALUE "
            "(for faker mode). LABEL is a human-readable name, VALUE is the "
            "exact sensitive text that appears in markdown."
        ),
    )

    tf_parser = subparsers.add_parser(
        "tableformat",
        aliases=["tf"],
        help="Unflatten markdown tables (restore merged-cell hierarchy from Word paste)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description=(
            "Fix tables pasted from Word where the first column had merged cells.\n"
            "Content is shifted left in raw paste; this restores empty cells by carrying\n"
            "the previous row's values for leading columns."
        ),
    )
    tf_parser.add_argument(
        "path",
        nargs="?",
        default=None,
        metavar="PATH",
        help="File, directory, or glob pattern to process (default: use -d)",
    )
    tf_parser.add_argument(
        "-d",
        "--directory",
        default=".",
        metavar="DIR",
        help="Directory to scan when PATH is not given (default: cwd)",
    )
    tf_parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print transformed tables without modifying files",
    )
    tf_parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Skip confirmation prompt (e.g. for 'tf undo')",
    )

    return parser


def _parse_md_table_row(line: str) -> List[str]:
    """Parse a markdown table row into list of cell strings (strip)."""
    if not line.strip().startswith("|"):
        return []
    parts = line.split("|")
    return [p.strip() for p in parts[1:-1]] if len(parts) >= 2 else []


def _is_separator_row(cells: List[str]) -> bool:
    """True if row looks like | --- | --- |."""
    if not cells:
        return False
    return all(re.match(r"^:?-+:?$", c.strip()) or c.strip() == "" for c in cells)


def _unflatten_table_rows(
    rows_cells: List[List[str]], num_cols: int
) -> List[List[str]]:
    """
    Restore merged-cell hierarchy: carry previous row for leading columns, then blank
    cells that repeat the row above (by logical value) so the table shows merged-cell structure.
    """
    if num_cols <= 0 or not rows_cells:
        return rows_cells
    prev: List[str] = [""] * num_cols
    full: List[List[str]] = []
    for row in rows_cells:
        if len(row) != num_cols:
            row = (row + [""] * num_cols)[:num_cols]
        non_empty_count = sum(1 for c in row if c.strip() != "")
        leading = max(0, num_cols - non_empty_count)
        non_empty_cells = [c for c in row if c.strip() != ""]
        tail_len = num_cols - leading
        tail = (non_empty_cells + [""] * tail_len)[:tail_len]
        new_row = prev[:leading] + tail
        full.append(new_row)
        prev = new_row
    hierarchy_cols = min(2, num_cols)
    out: List[List[str]] = []
    for i, row in enumerate(full):
        if i == 0:
            out.append(list(row))
        else:
            out.append(
                [
                    "" if (j < hierarchy_cols and row[j] == full[i - 1][j]) else row[j]
                    for j in range(num_cols)
                ]
            )
    return out


def _format_table_rows(rows: List[List[str]]) -> str:
    """Format table rows as markdown lines."""
    lines = []
    for row in rows:
        lines.append("| " + " | ".join(row) + " |")
    return "\n".join(lines)


def _transform_tables_in_content(content: str) -> tuple[str, int]:
    """
    Find markdown table blocks, unflatten each, replace in content. Return (new_content, tables_transformed_count).
    """
    lines = content.split("\n")
    i = 0
    result: List[str] = []
    count = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip().startswith("|"):
            result.append(line)
            i += 1
            continue
        block_lines: List[str] = []
        while i < len(lines) and lines[i].strip().startswith("|"):
            block_lines.append(lines[i])
            i += 1
        if len(block_lines) < 3:
            result.extend(block_lines)
            continue
        header_cells = _parse_md_table_row(block_lines[0])
        sep_cells = _parse_md_table_row(block_lines[1])
        if not _is_separator_row(sep_cells) or len(header_cells) != len(sep_cells):
            result.extend(block_lines)
            continue
        num_cols = len(header_cells)
        data_cells = [_parse_md_table_row(ln) for ln in block_lines[2:]]
        if not data_cells:
            result.extend(block_lines)
            continue
        normalized_data: List[List[str]] = []
        for r in data_cells:
            if len(r) < num_cols:
                r = (r + [""] * num_cols)[:num_cols]
            elif len(r) > num_cols:
                r = r[:num_cols]
            normalized_data.append(r)
        unflattened = _unflatten_table_rows(normalized_data, num_cols)
        new_table_lines = [block_lines[0], block_lines[1]] + _format_table_rows(
            unflattened
        ).split("\n")
        result.extend(new_table_lines)
        count += 1
    return "\n".join(result), count


def resolve_directories(args: argparse.Namespace) -> tuple[Path, Path]:
    scan_dir = Path(args.directory).resolve()
    assets_dir = Path(args.assets)
    if not assets_dir.is_absolute():
        assets_dir = (scan_dir / assets_dir).resolve()
    else:
        assets_dir = assets_dir.resolve()
    return scan_dir, assets_dir


def validate_directories(scan_dir: Path, assets_dir: Path) -> bool:
    if not scan_dir.is_dir():
        CLIStyle.print(
            f"[ERROR] Directory not found: {scan_dir}", CLIStyle.COLORS["ERROR"]
        )
        return False
    if not assets_dir.is_dir():
        CLIStyle.print(
            f"[ERROR] Assets directory not found: {assets_dir}",
            CLIStyle.COLORS["ERROR"],
        )
        return False
    return True


def find_markdown_files(directory: Path) -> list[Path]:
    return [
        f
        for f in directory.iterdir()
        if f.is_file() and f.suffix.lower() in (".md", ".markdown")
    ]


def normalize_image_path(raw: str, md_parent: Path) -> Path:
    raw = unquote(raw.strip())
    raw = re.sub(r'\s+"[^"]*"$', "", raw)
    raw = re.sub(r"\s+'[^']*'$", "", raw)
    path = Path(raw)
    if not path.is_absolute():
        return (md_parent / path).resolve()
    return path.resolve()


def extract_referenced_images(md_files: list[Path], assets_dir: Path) -> set[str]:
    referenced: set[str] = set()
    resolved_assets = assets_dir.resolve()
    for md_file in md_files:
        try:
            content = md_file.read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            debug(f"Cannot read {md_file}: {e}")
            continue
        for pattern in MD_IMAGE_PATTERNS:
            for match in pattern.finditer(content):
                img_path = normalize_image_path(match.group(1), md_file.parent)
                try:
                    img_path.relative_to(resolved_assets)
                    referenced.add(img_path.name)
                    debug(f"Referenced: {img_path.name} (from {md_file.name})")
                except ValueError:
                    pass
    return referenced


def collect_asset_images(assets_dir: Path) -> list[Path]:
    if not assets_dir.is_dir():
        return []
    return sorted(
        (
            f
            for f in assets_dir.iterdir()
            if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS
        ),
        key=lambda p: p.name,
    )


def format_size(size_bytes: int) -> str:
    for unit in ("B", "KB", "MB", "GB"):
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}" if unit != "B" else f"{size_bytes} B"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def confirm(prompt: str, default_yes: bool = True) -> bool:
    suffix = " [Y/n]: " if default_yes else " [y/N]: "
    try:
        answer = input(prompt + suffix).strip().lower()
    except (EOFError, KeyboardInterrupt):
        print()
        return False
    return default_yes if not answer else answer in ("y", "yes")


def print_scan_summary(scan_dir: Path, assets_dir: Path, md_files: list[Path]) -> None:
    CLIStyle.print(f"Scan directory : {scan_dir}", CLIStyle.COLORS["TITLE"])
    CLIStyle.print(f"Assets directory: {assets_dir}", CLIStyle.COLORS["TITLE"])
    print()
    CLIStyle.print(
        f"Found {len(md_files)} markdown file(s):", CLIStyle.COLORS["SUB_TITLE"]
    )
    for f in md_files:
        print(f"  - {f.name}")
    print()


def print_image_report(all_images: list[Path], unreferenced: list[Path]) -> None:
    referenced_count = len(all_images) - len(unreferenced)
    CLIStyle.print(
        f"Total images in assets : {len(all_images)}", CLIStyle.COLORS["CONTENT"]
    )
    CLIStyle.print(
        f"Referenced images       : {referenced_count}", CLIStyle.COLORS["OK"]
    )
    CLIStyle.print(
        f"Unreferenced images     : {len(unreferenced)}", CLIStyle.COLORS["WARNING"]
    )
    print()
    if not unreferenced:
        CLIStyle.print("[OK] All images are referenced.", CLIStyle.COLORS["OK"])
        return
    total_size = 0
    for img in unreferenced:
        size = img.stat().st_size
        total_size += size
        print(f"  - {img.name}  ({format_size(size)})")
    CLIStyle.print(f"  Total: {format_size(total_size)}", CLIStyle.COLORS["WARNING"])
    print()


def execute_move(unreferenced: list[Path], assets_dir: Path) -> None:
    tmp_dir = Path(tempfile.mkdtemp(prefix="typora-img-clean-", dir="/tmp"))
    for img in unreferenced:
        shutil.move(str(img), str(tmp_dir / img.name))
        CLIStyle.print(f"  [MOVED] {img.name}", CLIStyle.COLORS["CONTENT"])
    print()
    CLIStyle.print(
        f"Moved {len(unreferenced)} file(s) to: {tmp_dir}", CLIStyle.COLORS["OK"]
    )
    CLIStyle.print(f"Restore: cp {tmp_dir}/* {assets_dir}/", CLIStyle.COLORS["INFO"])


def execute_delete(unreferenced: list[Path]) -> None:
    for img in unreferenced:
        img.unlink()
        CLIStyle.print(f"  [DELETED] {img.name}", CLIStyle.COLORS["ERROR"])
    print()
    CLIStyle.print(f"Deleted {len(unreferenced)} file(s).", CLIStyle.COLORS["WARNING"])


def _run_cleanimg(args: argparse.Namespace) -> int:
    scan_dir, assets_dir = resolve_directories(args)
    if not validate_directories(scan_dir, assets_dir):
        return 1

    md_files = find_markdown_files(scan_dir)
    if not md_files:
        CLIStyle.print("[INFO] No .md/.markdown files found.", CLIStyle.COLORS["INFO"])
        return 0

    print_scan_summary(scan_dir, assets_dir, md_files)

    referenced = extract_referenced_images(md_files, assets_dir)
    all_images = collect_asset_images(assets_dir)
    if not all_images:
        CLIStyle.print("[INFO] No image files in assets.", CLIStyle.COLORS["INFO"])
        return 0

    unreferenced = [img for img in all_images if img.name not in referenced]
    print_image_report(all_images, unreferenced)
    if not unreferenced:
        return 0

    if getattr(args, "dry_run", False):
        CLIStyle.print(
            "[DRY-RUN] No files were moved or deleted.", CLIStyle.COLORS["INFO"]
        )
        return 0

    action = "DELETE" if getattr(args, "rm", False) else "MOVE to /tmp"
    if not getattr(args, "yes", False) and not confirm(
        f"{action} {len(unreferenced)} unreferenced image(s)?"
    ):
        CLIStyle.print("Cancelled.", CLIStyle.COLORS["WARNING"])
        return 0

    if getattr(args, "rm", False):
        execute_delete(unreferenced)
    else:
        execute_move(unreferenced, assets_dir)
    return 0


def _run_datamasking(args: argparse.Namespace) -> int:
    raw_sensitive: List[str] = list(getattr(args, "sensitive", []))

    if len(raw_sensitive) == 1 and raw_sensitive[0] == "undo":
        return _run_datamasking_undo(args)

    marker_mode = getattr(args, "marker", False)
    restore_mode = getattr(args, "restore", False)

    if restore_mode or (len(raw_sensitive) == 1 and raw_sensitive[0] == "restore"):
        return _run_datamasking_restore(args)

    target_spec = args.path
    if target_spec:
        target_spec = str(target_spec)
    else:
        if raw_sensitive:
            first = raw_sensitive[0]
            first_path = Path(first)
            if first_path.exists() or any(ch in first for ch in "*?"):
                target_spec = first
                raw_sensitive = raw_sensitive[1:]
        if not target_spec:
            target_spec = args.directory

    paths: List[Path] = []
    if any(ch in target_spec for ch in "*?"):
        from glob import glob as _glob

        for p in _glob(target_spec):
            candidate = Path(p)
            if candidate.is_file():
                paths.append(candidate.resolve())
    else:
        target_path = Path(target_spec).resolve()
        if target_path.is_dir():
            paths.extend(find_markdown_files(target_path))
        elif target_path.is_file():
            paths.append(target_path)
        else:
            CLIStyle.print(
                f"[ERROR] Target path not found: {target_path}",
                CLIStyle.COLORS["ERROR"],
            )
            return 1

    if not paths:
        CLIStyle.print(
            "[INFO] No markdown files found for data masking.",
            CLIStyle.COLORS["INFO"],
        )
        return 0

    sensitive_file = getattr(args, "sensitive_file", None)
    file_items: List[str] = []
    if sensitive_file:
        file_path = Path(str(sensitive_file)).expanduser().resolve()
        try:
            lines = file_path.read_text(encoding="utf-8").splitlines()
        except OSError as e:
            CLIStyle.print(
                f"[ERROR] Cannot read sensitive file: {file_path} ({e})",
                CLIStyle.COLORS["ERROR"],
            )
            return 1
        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            file_items.append(stripped)

    ignore_case = getattr(args, "ignore_case", False)
    dry_run = getattr(args, "dry_run", False)

    if not marker_mode:
        all_values: List[str] = []
        all_values.extend(raw_sensitive)
        all_values.extend(file_items)
        if not all_values:
            CLIStyle.print(
                "[ERROR] No sensitive strings provided for data masking.",
                CLIStyle.COLORS["ERROR"],
            )
            return 1

        faker = Faker()
        mapping: Dict[str, str] = {}
        for value in all_values:
            if value not in mapping:
                length = max(6, min(32, len(value)))
                mapping[value] = faker.pystr(min_chars=length, max_chars=length)

        CLIStyle.print(
            "Planned mask mapping (input -> fake):", CLIStyle.COLORS["SUB_TITLE"]
        )
        for src, dst in mapping.items():
            print(f"  {src!r} -> {dst!r}")
        print()

        CLIStyle.print("Target markdown files:", CLIStyle.COLORS["SUB_TITLE"])
        for p in paths:
            print(f"  - {p}")
        print()

        if not dry_run and not getattr(args, "yes", False):
            if not confirm("Proceed with data masking?"):
                CLIStyle.print("Cancelled.", CLIStyle.COLORS["WARNING"])
                return 0

        overall_counts: Dict[str, int] = {key: 0 for key in mapping.keys()}

        backup_dir: Path | None = None
        if not dry_run:
            backup_dir = _create_datamasking_backup(paths)
            CLIStyle.print(
                f"[BACKUP] Original files saved to: {backup_dir}",
                CLIStyle.COLORS["INFO"],
            )

        total_replacements = 0
        for md_file in paths:
            try:
                content = md_file.read_text(encoding="utf-8", errors="replace")
            except OSError as e:
                debug(f"Cannot read {md_file}: {e}")
                continue

            original_content = content
            file_replacements = 0
            per_string_counts: Dict[str, int] = {key: 0 for key in mapping.keys()}
            for src, dst in mapping.items():
                flags = re.IGNORECASE if ignore_case else 0
                pattern = re.compile(
                    rf"(?<![0-9A-Za-z_]){re.escape(src)}(?![0-9A-Za-z_])", flags
                )

                def _repl(match: re.Match, *, _src: str = src, _dst: str = dst) -> str:
                    nonlocal file_replacements
                    file_replacements += 1
                    per_string_counts[_src] = per_string_counts.get(_src, 0) + 1
                    overall_counts[_src] = overall_counts.get(_src, 0) + 1
                    return _dst

                content = pattern.sub(_repl, content)

            if not file_replacements:
                CLIStyle.print(
                    f"[MASKED] {md_file.name}: 0 replacement(s)",
                    CLIStyle.COLORS["INFO"],
                )
                continue

            total_replacements += file_replacements
            CLIStyle.print(
                f"[MASKED] {md_file.name}: {file_replacements} replacement(s)",
                CLIStyle.COLORS["CONTENT"],
            )
            for src_key, count in per_string_counts.items():
                CLIStyle.print(
                    f"  - {src_key!r}: {count} replacement(s)",
                    CLIStyle.COLORS["CONTENT"],
                )
            if not dry_run:
                try:
                    md_file.write_text(content, encoding="utf-8")
                except OSError as e:
                    debug(f"Cannot write {md_file}: {e}")
                    CLIStyle.print(
                        f"[ERROR] Failed to write file: {md_file}",
                        CLIStyle.COLORS["ERROR"],
                    )
                    content = original_content

        if total_replacements == 0:
            CLIStyle.print(
                "[INFO] No sensitive strings found in markdown files.",
                CLIStyle.COLORS["INFO"],
            )
        else:
            CLIStyle.print(
                "Summary per sensitive string:",
                CLIStyle.COLORS["SUB_TITLE"],
            )
            for src_key, count in overall_counts.items():
                CLIStyle.print(
                    f"  {src_key!r}: {count} replacement(s)",
                    CLIStyle.COLORS["CONTENT"],
                )
            CLIStyle.print(
                f"[OK] Data masking completed, total replacements: {total_replacements}",
                CLIStyle.COLORS["OK"],
            )
            if dry_run:
                CLIStyle.print(
                    "[DRY-RUN] No files were modified.",
                    CLIStyle.COLORS["INFO"],
                )

        return 0

    marker_items: List[Dict[str, str]] = []
    for item in raw_sensitive:
        if not item:
            continue
        if "=" in item:
            label, value = item.split("=", 1)
            marker_items.append({"label": label.strip(), "value": value.strip()})
        else:
            marker_items.append({"label": "", "value": item})
    for line in file_items:
        if ":" in line:
            label, value = line.split(":", 1)
            marker_items.append({"label": label.strip(), "value": value.strip()})
        else:
            marker_items.append({"label": "", "value": line})

    if not marker_items:
        CLIStyle.print(
            "[ERROR] No sensitive strings provided for marker mode.",
            CLIStyle.COLORS["ERROR"],
        )
        return 1

    marker_items.sort(key=lambda item: len(item["value"]), reverse=True)

    for idx, item in enumerate(marker_items):
        label = item["label"] if item["label"] else "FIELD"
        item["token"] = f"[[MASK:{label}:{idx:04d}]]"

    CLIStyle.print(
        "Planned marker mapping (value -> token):",
        CLIStyle.COLORS["SUB_TITLE"],
    )
    for item in marker_items:
        display_label = item["label"] or "FIELD"
        print(
            f"  [{display_label}] {item['value']!r} -> {item['token']!r}",
        )
    print()

    CLIStyle.print("Target markdown files:", CLIStyle.COLORS["SUB_TITLE"])
    for p in paths:
        print(f"  - {p}")
    print()

    if not dry_run and not getattr(args, "yes", False):
        if not confirm("Proceed with data masking (marker mode)?"):
            CLIStyle.print("Cancelled.", CLIStyle.COLORS["WARNING"])
            return 0

    backup_dir_marker: Path | None = None
    if not dry_run:
        backup_dir_marker = _create_datamasking_backup(paths)
        CLIStyle.print(
            f"[BACKUP] Original files saved to: {backup_dir_marker}",
            CLIStyle.COLORS["INFO"],
        )

    mapping_manifest: Dict[str, Dict[str, Dict[str, str]]] = {"files": {}}

    total_replacements_marker = 0
    for md_file in paths:
        try:
            content = md_file.read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            debug(f"Cannot read {md_file}: {e}")
            continue

        original_content = content
        file_replacements = 0
        file_mapping: Dict[str, Dict[str, str]] = {}

        for item in marker_items:
            src_val = item["value"]
            token = item["token"]
            label = item["label"]

            flags = re.IGNORECASE if ignore_case else 0
            pattern = re.compile(re.escape(src_val), flags)

            def _marker_repl(match: re.Match, *, _token: str = token) -> str:
                nonlocal file_replacements
                file_replacements += 1
                return _token

            before_replacements = file_replacements
            content = pattern.sub(_marker_repl, content)
            if file_replacements > before_replacements:
                file_mapping[token] = {"original": src_val, "label": label}

        if not file_replacements:
            CLIStyle.print(
                f"[MASKED] {md_file.name}: 0 marker replacement(s)",
                CLIStyle.COLORS["INFO"],
            )
            continue

        total_replacements_marker += file_replacements
        CLIStyle.print(
            f"[MASKED] {md_file.name}: {file_replacements} marker replacement(s)",
            CLIStyle.COLORS["CONTENT"],
        )

        if not dry_run:
            try:
                md_file.write_text(content, encoding="utf-8")
            except OSError as e:
                debug(f"Cannot write {md_file}: {e}")
                CLIStyle.print(
                    f"[ERROR] Failed to write file: {md_file}",
                    CLIStyle.COLORS["ERROR"],
                )
                content = original_content
                continue

        if file_mapping:
            mapping_manifest["files"][str(md_file.resolve())] = file_mapping

    if not dry_run and mapping_manifest["files"]:
        mapping_dir = Path(tempfile.mkdtemp(prefix=DM_MAP_PREFIX, dir="/tmp")).resolve()
        (mapping_dir / "mapping.json").write_text(
            json.dumps(mapping_manifest, indent=2),
            encoding="utf-8",
        )
        CLIStyle.print(
            f"[MAP] Marker mapping saved to: {mapping_dir / 'mapping.json'}",
            CLIStyle.COLORS["INFO"],
        )

    if total_replacements_marker == 0:
        CLIStyle.print(
            "[INFO] No marker replacements were applied.",
            CLIStyle.COLORS["INFO"],
        )
    else:
        CLIStyle.print(
            f"[OK] Marker data masking completed, total replacements: {total_replacements_marker}",
            CLIStyle.COLORS["OK"],
        )
        if dry_run:
            CLIStyle.print(
                "[DRY-RUN] No files were modified.",
                CLIStyle.COLORS["INFO"],
            )

    return 0


def _create_datamasking_backup(paths: List[Path]) -> Path:
    backup_dir = Path(tempfile.mkdtemp(prefix=DM_BACKUP_PREFIX, dir="/tmp")).resolve()
    manifest = {
        "files": [str(p) for p in paths],
    }
    for p in paths:
        if p.is_file():
            shutil.copy2(str(p), str(backup_dir / p.name))
    (backup_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    return backup_dir


def _find_latest_datamasking_mapping() -> Path | None:
    tmp_dir = Path("/tmp")
    candidates: List[Path] = []
    for child in tmp_dir.iterdir():
        if child.is_dir() and child.name.startswith(DM_MAP_PREFIX):
            if (child / "mapping.json").is_file():
                candidates.append(child)
    if not candidates:
        return None
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0]


def _run_datamasking_restore(args: argparse.Namespace) -> int:
    mapping_dir = _find_latest_datamasking_mapping()
    if not mapping_dir:
        CLIStyle.print(
            "[INFO] No marker mapping found in /tmp to restore.",
            CLIStyle.COLORS["INFO"],
        )
        return 0

    mapping_path = mapping_dir / "mapping.json"
    try:
        manifest = json.loads(mapping_path.read_text(encoding="utf-8"))
    except Exception as e:
        CLIStyle.print(
            f"[ERROR] Failed to read marker mapping: {e}",
            CLIStyle.COLORS["ERROR"],
        )
        return 1

    files_mapping = manifest.get("files", {})
    if not isinstance(files_mapping, dict) or not files_mapping:
        CLIStyle.print(
            "[INFO] Marker mapping has no files.",
            CLIStyle.COLORS["INFO"],
        )
        return 0

    target_spec = args.path
    if target_spec:
        target_spec = str(target_spec)
    else:
        target_spec = args.directory

    target_paths: List[Path] = []
    if any(ch in target_spec for ch in "*?"):
        from glob import glob as _glob

        for p in _glob(target_spec):
            candidate = Path(p)
            if candidate.is_file():
                target_paths.append(candidate.resolve())
    else:
        target_path = Path(target_spec).resolve()
        if target_path.is_dir():
            target_paths.extend(find_markdown_files(target_path))
        elif target_path.is_file():
            target_paths.append(target_path)

    if not target_paths:
        CLIStyle.print(
            "[INFO] No markdown files found for marker restore.",
            CLIStyle.COLORS["INFO"],
        )
        return 0

    target_set = {str(p.resolve()) for p in target_paths}
    fields_filter = set(getattr(args, "field", []) or [])
    dry_run = getattr(args, "dry_run", False)

    CLIStyle.print(
        f"Latest marker mapping: {mapping_dir}",
        CLIStyle.COLORS["TITLE"],
    )
    CLIStyle.print(
        "Files considered for restore:",
        CLIStyle.COLORS["SUB_TITLE"],
    )
    for p in target_paths:
        print(f"  - {p}")
    print()

    if not dry_run and not getattr(args, "yes", False):
        if not confirm("Restore marker placeholders in these files?"):
            CLIStyle.print("Cancelled.", CLIStyle.COLORS["WARNING"])
            return 0

    total_restored = 0
    for file_str, token_map in files_mapping.items():
        if file_str not in target_set:
            continue
        file_path = Path(file_str)
        try:
            content = file_path.read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            debug(f"Cannot read {file_path}: {e}")
            continue

        file_restored = 0
        for token, entry in token_map.items():
            original_value = entry.get("original", "")
            label = entry.get("label", "")
            if fields_filter and label not in fields_filter:
                continue
            count = content.count(token)
            if count == 0:
                continue
            content = content.replace(token, original_value)
            file_restored += count

        if not file_restored:
            continue

        if not dry_run:
            try:
                file_path.write_text(content, encoding="utf-8")
            except OSError as e:
                debug(f"Cannot write {file_path}: {e}")
                CLIStyle.print(
                    f"[ERROR] Failed to restore {file_path}: {e}",
                    CLIStyle.COLORS["ERROR"],
                )
                continue

        total_restored += file_restored
        CLIStyle.print(
            f"[RESTORE] {file_path}: {file_restored} placeholder(s) restored",
            CLIStyle.COLORS["CONTENT"],
        )

    if total_restored == 0:
        CLIStyle.print(
            "[INFO] No marker placeholders restored.",
            CLIStyle.COLORS["INFO"],
        )
    else:
        CLIStyle.print(
            f"[OK] Marker restore completed, total restored: {total_restored}",
            CLIStyle.COLORS["OK"],
        )
        if dry_run:
            CLIStyle.print(
                "[DRY-RUN] No files were modified.",
                CLIStyle.COLORS["INFO"],
            )

    return 0


def _find_latest_datamasking_backup() -> Path | None:
    tmp_dir = Path("/tmp")
    candidates: List[Path] = []
    for child in tmp_dir.iterdir():
        if child.is_dir() and child.name.startswith(DM_BACKUP_PREFIX):
            if (child / "manifest.json").is_file():
                candidates.append(child)
    if not candidates:
        return None
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0]


def _run_datamasking_undo(args: argparse.Namespace) -> int:
    backup_dir = _find_latest_datamasking_backup()
    if not backup_dir:
        CLIStyle.print(
            "[INFO] No previous datamasking backup found to undo.",
            CLIStyle.COLORS["INFO"],
        )
        return 0

    manifest_path = backup_dir / "manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as e:
        CLIStyle.print(
            f"[ERROR] Failed to read backup manifest: {e}",
            CLIStyle.COLORS["ERROR"],
        )
        return 1

    files = [Path(p) for p in manifest.get("files", [])]
    if not files:
        CLIStyle.print(
            "[INFO] No files in backup manifest.",
            CLIStyle.COLORS["INFO"],
        )
        return 0

    CLIStyle.print(
        f"Latest backup: {backup_dir}",
        CLIStyle.COLORS["TITLE"],
    )
    CLIStyle.print(
        f"Files to restore ({len(files)}):",
        CLIStyle.COLORS["SUB_TITLE"],
    )
    for p in files:
        print(f"  - {p}")
    print()

    if not getattr(args, "yes", False) and not confirm(
        f"Restore {len(files)} file(s) from backup (overwrite current content)?"
    ):
        CLIStyle.print("Cancelled.", CLIStyle.COLORS["WARNING"])
        return 0

    restored = 0
    for original in files:
        backup_file = backup_dir / original.name
        if backup_file.is_file():
            try:
                shutil.copy2(str(backup_file), str(original))
                CLIStyle.print(
                    f"[UNDO] Restored {original}",
                    CLIStyle.COLORS["CONTENT"],
                )
                restored += 1
            except OSError as e:
                CLIStyle.print(
                    f"[ERROR] Failed to restore {original}: {e}",
                    CLIStyle.COLORS["ERROR"],
                )

    if restored == 0:
        CLIStyle.print(
            "[INFO] No files restored from latest backup.",
            CLIStyle.COLORS["INFO"],
        )
    else:
        CLIStyle.print(
            f"[OK] Undo completed, restored {restored} file(s) from {backup_dir}",
            CLIStyle.COLORS["OK"],
        )

    return 0


def _resolve_tableformat_paths(args: argparse.Namespace) -> List[Path]:
    """Resolve PATH (file/dir/glob) or -d to list of markdown file paths."""
    path_spec = getattr(args, "path", None)
    base_dir = Path(getattr(args, "directory", ".")).resolve()
    if path_spec:
        path_str = str(path_spec)
        if "*" in path_str or "?" in path_str:
            return [Path(p).resolve() for p in glob(path_str) if Path(p).is_file()]
        p = Path(path_str).resolve()
        if p.is_dir():
            return find_markdown_files(p)
        if p.is_file():
            return [p]
        return []
    return find_markdown_files(base_dir)


def _create_tableformat_backup(paths: List[Path]) -> Path:
    backup_dir = Path(tempfile.mkdtemp(prefix=TF_BACKUP_PREFIX, dir="/tmp")).resolve()
    files_dir = backup_dir / "files"
    files_dir.mkdir(parents=True, exist_ok=True)
    manifest: Dict[str, List[Dict[str, str]]] = {"files": []}
    for idx, p in enumerate(paths):
        if not p.is_file():
            continue
        backup_name = f"{idx:04d}--{p.name}"
        backup_file = files_dir / backup_name
        shutil.copy2(str(p), str(backup_file))
        manifest["files"].append(
            {
                "original": str(p),
                "backup": str(backup_file),
            }
        )
    (backup_dir / "manifest.json").write_text(
        json.dumps(manifest, indent=2), encoding="utf-8"
    )
    return backup_dir


def _find_latest_tableformat_backup() -> Path | None:
    tmp_dir = Path("/tmp")
    candidates: List[Path] = []
    for child in tmp_dir.iterdir():
        if child.is_dir() and child.name.startswith(TF_BACKUP_PREFIX):
            if (child / "manifest.json").is_file():
                candidates.append(child)
    if not candidates:
        return None
    candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    return candidates[0]


def _run_tableformat_undo(args: argparse.Namespace) -> int:
    backup_dir = _find_latest_tableformat_backup()
    if not backup_dir:
        CLIStyle.print(
            "[INFO] No previous tableformat backup found to undo.",
            CLIStyle.COLORS["INFO"],
        )
        return 0

    manifest_path = backup_dir / "manifest.json"
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except Exception as e:
        CLIStyle.print(
            f"[ERROR] Failed to read backup manifest: {e}",
            CLIStyle.COLORS["ERROR"],
        )
        return 1

    entries = manifest.get("files", [])
    if not isinstance(entries, list) or not entries:
        CLIStyle.print(
            "[INFO] No files in backup manifest.",
            CLIStyle.COLORS["INFO"],
        )
        return 0

    originals = [Path(e.get("original", "")) for e in entries if e.get("original")]
    CLIStyle.print(f"Latest backup: {backup_dir}", CLIStyle.COLORS["TITLE"])
    CLIStyle.print(
        f"Files to restore ({len(originals)}):",
        CLIStyle.COLORS["SUB_TITLE"],
    )
    for p in originals:
        print(f"  - {p}")
    print()

    if not getattr(args, "yes", False) and not confirm(
        f"Restore {len(originals)} file(s) from backup (overwrite current content)?"
    ):
        CLIStyle.print("Cancelled.", CLIStyle.COLORS["WARNING"])
        return 0

    restored = 0
    for e in entries:
        original = Path(e.get("original", ""))
        backup_file = Path(e.get("backup", ""))
        if not original or not backup_file:
            continue
        if not backup_file.is_file():
            CLIStyle.print(
                f"[ERROR] Backup file missing: {backup_file}",
                CLIStyle.COLORS["ERROR"],
            )
            continue
        try:
            shutil.copy2(str(backup_file), str(original))
            CLIStyle.print(
                f"[UNDO] Restored {original}",
                CLIStyle.COLORS["CONTENT"],
            )
            restored += 1
        except OSError as e2:
            CLIStyle.print(
                f"[ERROR] Failed to restore {original}: {e2}",
                CLIStyle.COLORS["ERROR"],
            )

    if restored == 0:
        CLIStyle.print(
            "[INFO] No files restored from latest backup.",
            CLIStyle.COLORS["INFO"],
        )
    else:
        CLIStyle.print(
            f"[OK] Undo completed, restored {restored} file(s) from {backup_dir}",
            CLIStyle.COLORS["OK"],
        )
    return 0


def _run_tableformat(args: argparse.Namespace) -> int:
    if getattr(args, "path", None) == "undo":
        return _run_tableformat_undo(args)

    paths = _resolve_tableformat_paths(args)
    if not paths:
        CLIStyle.print(
            "[INFO] No markdown files found to process.",
            CLIStyle.COLORS["INFO"],
        )
        return 0
    dry_run = getattr(args, "dry_run", False)
    if not dry_run:
        backup_dir = _create_tableformat_backup(paths)
        CLIStyle.print(
            f"[BACKUP] Original files saved to: {backup_dir}",
            CLIStyle.COLORS["INFO"],
        )
    total_tables = 0
    for md_file in paths:
        try:
            content = md_file.read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            debug(f"Cannot read {md_file}: {e}")
            CLIStyle.print(
                f"[ERROR] Cannot read {md_file}: {e}",
                CLIStyle.COLORS["ERROR"],
            )
            continue
        new_content, count = _transform_tables_in_content(content)
        if count == 0:
            continue
        total_tables += count
        CLIStyle.print(
            f"[TABLE] {md_file.name}: {count} table(s) reformatted",
            CLIStyle.COLORS["CONTENT"],
        )
        if not dry_run:
            try:
                md_file.write_text(new_content, encoding="utf-8")
            except OSError as e:
                CLIStyle.print(
                    f"[ERROR] Failed to write {md_file}: {e}",
                    CLIStyle.COLORS["ERROR"],
                )
    if total_tables == 0:
        CLIStyle.print(
            "[INFO] No tables were transformed.",
            CLIStyle.COLORS["INFO"],
        )
    else:
        CLIStyle.print(
            f"[OK] Table format completed, {total_tables} table(s) transformed.",
            CLIStyle.COLORS["OK"],
        )
        if dry_run:
            CLIStyle.print("[DRY-RUN] No files were modified.", CLIStyle.COLORS["INFO"])
    return 0


def main() -> int:
    parser = _build_parser()
    args = parser.parse_args()

    global DEBUG_MODE
    DEBUG_MODE = getattr(args, "log", False)

    if DEBUG_MODE:
        CLIStyle.print("[DEBUG] Debug mode enabled", CLIStyle.COLORS["CONTENT"])

    if not args.command:
        parser.print_help()
        return 0

    try:
        if args.command in ("cleanimg", "ci"):
            return _run_cleanimg(args)
        if args.command in ("datamasking", "dm"):
            return _run_datamasking(args)
        if args.command in ("tableformat", "tf"):
            return _run_tableformat(args)
        CLIStyle.print(
            f"[ERROR] Unknown command: {args.command}", CLIStyle.COLORS["ERROR"]
        )
        return 1
    except KeyboardInterrupt:
        CLIStyle.print("\nCancelled", CLIStyle.COLORS["WARNING"])
        return 1
    except Exception as e:
        if DEBUG_MODE:
            import traceback

            traceback.print_exc()
        CLIStyle.print(f"Error: {e}", CLIStyle.COLORS["ERROR"])
        return 1


if __name__ == "__main__":
    sys.exit(main())
