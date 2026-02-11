# -*- coding: utf-8 -*-
"""
Typora unreferenced image cleaner.

Scans .md/.markdown files for image references, identifies unreferenced
images in the assets directory, and moves or deletes them.
"""

import argparse
import re
import shutil
import sys
import tempfile
from pathlib import Path
from urllib.parse import unquote

DEBUG_MODE = False

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".svg", ".tiff", ".ico"}

MD_IMAGE_PATTERNS = [
    re.compile(r'!\[.*?\]\((.+?)\)'),
    re.compile(r'<img\s[^>]*src=["\']([^"\']+)["\']', re.IGNORECASE),
    re.compile(r'^\[.*?\]:\s*(.+)$', re.MULTILINE),
]


def debug(*args, **kwargs) -> None:
    if not DEBUG_MODE:
        return
    import inspect
    frame = inspect.currentframe().f_back
    prefix = f"[DEBUG {Path(frame.f_code.co_filename).name}:{frame.f_lineno}]"
    print(prefix, *args, **kwargs, file=sys.stderr)


class CLIStyle:
    COLORS = {
        "TITLE": 7, "SUB_TITLE": 2, "CONTENT": 3,
        "EXAMPLE": 7, "WARNING": 4, "ERROR": 2,
        "INFO": 5, "OK": 3,
    }

    @staticmethod
    def color(text: str, color: int = 3) -> str:
        codes = {
            0: "{}", 1: "\033[1;30m{}\033[0m", 2: "\033[1;31m{}\033[0m",
            3: "\033[1;32m{}\033[0m", 4: "\033[1;33m{}\033[0m",
            5: "\033[1;34m{}\033[0m", 6: "\033[1;35m{}\033[0m",
            7: "\033[1;36m{}\033[0m", 8: "\033[1;37m{}\033[0m",
        }
        return codes[color].format(text)

    @staticmethod
    def print(text: str, color: int = 0) -> None:
        print(CLIStyle.color(text, color) if color else text)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Clean unreferenced images from Typora markdown projects."
    )
    parser.add_argument(
        "-d", "--directory", default=".",
        help="Directory to scan for .md/.markdown files (default: cwd)",
    )
    parser.add_argument(
        "--assets", default="./assets",
        help="Path to the assets/images directory (default: ./assets)",
    )
    parser.add_argument("--rm", action="store_true",
                        help="Delete unreferenced images instead of moving to /tmp")
    parser.add_argument("-y", "--yes", action="store_true",
                        help="Skip confirmation prompt")
    parser.add_argument("--dry-run", action="store_true",
                        help="Only list unreferenced images, no action")
    parser.add_argument("--log", action="store_true",
                        help="Enable debug output")
    return parser.parse_args()


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
        CLIStyle.print(f"[ERROR] Directory not found: {scan_dir}", CLIStyle.COLORS["ERROR"])
        return False
    if not assets_dir.is_dir():
        CLIStyle.print(f"[ERROR] Assets directory not found: {assets_dir}", CLIStyle.COLORS["ERROR"])
        return False
    return True


def find_markdown_files(directory: Path) -> list[Path]:
    return [f for f in directory.iterdir()
            if f.is_file() and f.suffix.lower() in (".md", ".markdown")]


def normalize_image_path(raw: str, md_parent: Path) -> Path:
    raw = unquote(raw.strip())
    raw = re.sub(r'\s+"[^"]*"$', '', raw)
    raw = re.sub(r"\s+'[^']*'$", '', raw)
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
        (f for f in assets_dir.iterdir()
         if f.is_file() and f.suffix.lower() in IMAGE_EXTENSIONS),
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
    CLIStyle.print(f"Found {len(md_files)} markdown file(s):", CLIStyle.COLORS["SUB_TITLE"])
    for f in md_files:
        print(f"  - {f.name}")
    print()


def print_image_report(all_images: list[Path], unreferenced: list[Path]) -> None:
    referenced_count = len(all_images) - len(unreferenced)
    CLIStyle.print(f"Total images in assets : {len(all_images)}", CLIStyle.COLORS["CONTENT"])
    CLIStyle.print(f"Referenced images       : {referenced_count}", CLIStyle.COLORS["OK"])
    CLIStyle.print(f"Unreferenced images     : {len(unreferenced)}", CLIStyle.COLORS["WARNING"])
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
    CLIStyle.print(f"Moved {len(unreferenced)} file(s) to: {tmp_dir}", CLIStyle.COLORS["OK"])
    CLIStyle.print(f"Restore: cp {tmp_dir}/* {assets_dir}/", CLIStyle.COLORS["INFO"])


def execute_delete(unreferenced: list[Path]) -> None:
    for img in unreferenced:
        img.unlink()
        CLIStyle.print(f"  [DELETED] {img.name}", CLIStyle.COLORS["ERROR"])
    print()
    CLIStyle.print(f"Deleted {len(unreferenced)} file(s).", CLIStyle.COLORS["WARNING"])


def main() -> int:
    args = parse_args()

    global DEBUG_MODE
    DEBUG_MODE = args.log

    try:
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

        if args.dry_run:
            CLIStyle.print("[DRY-RUN] No files were moved or deleted.", CLIStyle.COLORS["INFO"])
            return 0

        action = "DELETE" if args.rm else "MOVE to /tmp"
        if not args.yes and not confirm(f"{action} {len(unreferenced)} unreferenced image(s)?"):
            CLIStyle.print("Cancelled.", CLIStyle.COLORS["WARNING"])
            return 0

        if args.rm:
            execute_delete(unreferenced)
        else:
            execute_move(unreferenced, assets_dir)

    except KeyboardInterrupt:
        CLIStyle.print("\nCancelled", CLIStyle.COLORS["WARNING"])
        return 1
    except Exception as e:
        if DEBUG_MODE:
            import traceback
            traceback.print_exc()
        CLIStyle.print(f"Error: {e}", CLIStyle.COLORS["ERROR"])
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
