# -*- coding: utf-8 -*-
# pip install beautifulsoup4

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

DEBUG_MODE = False


class CLIStyle:
    """CLI tool unified style config"""

    COLORS = {
        "TITLE": 7,
        "SUB_TITLE": 2,
        "CONTENT": 3,
        "EXAMPLE": 7,
        "WARNING": 4,
        "ERROR": 2,
    }

    @staticmethod
    def color(text: str = "", color: int = 3) -> str:
        """Unified color processing function"""
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
    """Unified command line argument parser"""

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

        formatter.add_text(CLIStyle.color("\nOptions:", CLIStyle.COLORS["TITLE"]))
        for action_group in self._action_groups:
            formatter.start_section(action_group.title)
            formatter.add_arguments(action_group._group_actions)
            formatter.end_section()

        if self.epilog:
            formatter.add_text(self.epilog)

        return formatter.format_help()


def debug(*args, **kwargs) -> None:
    """
    Print debug information with file and line number
    ```python
    debug(
        'message',          # Debug message
        key='value',        # Key-value parameters
    )

    return = None
    ```
    """
    if not DEBUG_MODE:
        return

    import inspect

    frame = inspect.currentframe()
    if frame and frame.f_back:
        filename = os.path.basename(frame.f_back.f_code.co_filename)
        lineno = frame.f_back.f_lineno
        prefix = f"[{filename}:{lineno}]"
    else:
        prefix = "[DEBUG]"

    parts = [str(arg) for arg in args]
    for key, value in kwargs.items():
        parts.append(f"{key}={value}")

    print(CLIStyle.color(f"{prefix} {' '.join(parts)}", CLIStyle.COLORS["WARNING"]))


def create_example_text(script_name: str, examples: list, notes: list = None) -> str:
    """Create unified example text"""
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


def normalize_href(href: Optional[str]) -> str:
    """Convert protocol-relative Zhihu hrefs to absolute https URLs."""
    if not href:
        return ""
    return urljoin("https:", href)


def text_content(node: Optional[Tag]) -> str:
    """Return normalized text content from a BeautifulSoup node."""
    return node.get_text("\n", strip=True) if node else ""


def parse_int(value: Optional[str]) -> Optional[int]:
    """Extract the first integer from a string such as '赞同 553'."""
    if value is None:
        return None
    digits = "".join(ch for ch in value if ch.isdigit())
    return int(digits) if digits else None


def parse_card(card: Tag) -> Dict[str, Any]:
    """Parse a single Zhihu answer card into a structured dictionary."""
    title_link = card.select_one("h2.ContentItem-title a")
    author_meta = card.select_one('meta[itemprop="name"]')
    author_link = card.select_one(".AuthorInfo-content a.UserLink-link")
    answer_meta_url = card.select_one('meta[itemprop="url"]')
    upvote_meta = card.select_one('meta[itemprop="upvoteCount"]')
    created_meta = card.select_one('meta[itemprop="dateCreated"]')
    modified_meta = card.select_one('meta[itemprop="dateModified"]')
    rich_text = card.select_one("span.RichText")
    vote_button = card.find("button", attrs={"aria-label": lambda v: v and "赞同" in v})

    return {
        "title": text_content(title_link),
        "question_url": normalize_href(title_link["href"])
        if title_link and title_link.has_attr("href")
        else "",
        "author": (
            author_meta.get("content")
            if author_meta and author_meta.get("content")
            else text_content(author_link)
        ),
        "answer_url": normalize_href(answer_meta_url["content"])
        if answer_meta_url and answer_meta_url.has_attr("content")
        else "",
        "created_at": created_meta.get("content")
        if created_meta and created_meta.get("content")
        else "",
        "modified_at": modified_meta.get("content")
        if modified_meta and modified_meta.get("content")
        else "",
        "upvote_count": parse_int(upvote_meta.get("content") if upvote_meta else None)
        or parse_int(vote_button.get("aria-label") if vote_button else None),
        "answer_text": text_content(rich_text),
    }


def parse_html(html: str) -> List[Dict[str, Any]]:
    """Parse HTML containing Zhihu cards and return a list of answer dicts."""
    soup = BeautifulSoup(html, "html.parser")
    cards = soup.select("div.Card.TopstoryItem")
    return [parse_card(card) for card in cards]


def render_text(items: List[Dict[str, Any]]) -> str:
    """Render answers into a human-readable plain text block."""
    lines: List[str] = []
    for idx, item in enumerate(items, start=1):
        lines.append(f"[{idx}] {item.get('title')}")
        lines.append(f"Author   : {item.get('author')}")
        lines.append(f"Created  : {item.get('created_at')}")
        lines.append(f"Modified : {item.get('modified_at')}")
        lines.append(f"Upvotes  : {item.get('upvote_count')}")
        lines.append(f"Question : {item.get('question_url')}")
        lines.append(f"Answer   : {item.get('answer_url')}")
        lines.append("Content  :")
        lines.append(item.get("answer_text", ""))
        lines.append("-" * 40)
    return "\n".join(lines)


def render_markdown(items: List[Dict[str, Any]]) -> str:
    """Render answers into markdown format."""
    blocks: List[str] = []
    for idx, item in enumerate(items, start=1):
        blocks.append(f"## {idx}. {item.get('title')}")
        blocks.append(f"- Author: {item.get('author')}")
        blocks.append(f"- Created: {item.get('created_at')}")
        blocks.append(f"- Modified: {item.get('modified_at')}")
        blocks.append(f"- Upvotes: {item.get('upvote_count')}")
        blocks.append(f"- Question: {item.get('question_url')}")
        blocks.append(f"- Answer: {item.get('answer_url')}")
        blocks.append("\n" + item.get("answer_text", "") + "\n")
    return "\n".join(blocks)


def main() -> int:
    """CLI entry: parse Zhihu HTML and export in requested format."""
    script_name = os.path.basename(sys.argv[0])

    examples = [
        ("Export as JSON to stdout", "saved.html"),
        ("Export as JSON file", "saved.html -o output.json"),
        ("Export as plain text", "saved.html -o output.txt"),
        ("Export as markdown", "saved.html -o output.md"),
        ("Enable debug logging", "saved.html --log"),
    ]

    notes = [
        "Without -o option, JSON output will be printed to stdout",
        "Output format is determined by file extension: .json, .txt, or .md",
        "Use --log to enable debug mode for troubleshooting",
    ]

    parser = ColoredArgumentParser(
        description=CLIStyle.color(
            "Parse Zhihu answer cards from HTML and export in various formats",
            CLIStyle.COLORS["TITLE"],
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=create_example_text(script_name, examples, notes),
    )

    parser.add_argument(
        "input_html",
        type=Path,
        metavar=CLIStyle.color("HTML_FILE", CLIStyle.COLORS["WARNING"]),
        help=CLIStyle.color("Path to Zhihu HTML file", CLIStyle.COLORS["CONTENT"]),
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        metavar=CLIStyle.color("PATH", CLIStyle.COLORS["WARNING"]),
        help=CLIStyle.color(
            "Output file path (extension decides format: .json/.txt/.md)",
            CLIStyle.COLORS["CONTENT"],
        ),
    )
    parser.add_argument(
        "--log",
        action="store_true",
        help=CLIStyle.color("Enable debug logging", CLIStyle.COLORS["CONTENT"]),
    )

    args = parser.parse_args()

    global DEBUG_MODE
    DEBUG_MODE = args.log

    html_path: Path = args.input_html
    if not html_path.is_file():
        print(
            CLIStyle.color(
                f"Error: File not found: {html_path}", CLIStyle.COLORS["ERROR"]
            )
        )
        return 1

    debug("Reading HTML file", path=html_path)
    html = html_path.read_text(encoding="utf-8", errors="ignore")
    debug("Parsing HTML content", size=len(html))
    parsed = parse_html(html)
    debug("Parsed cards", count=len(parsed))

    if not args.output:
        debug("Outputting JSON to stdout")
        json.dump(parsed, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
        return 0

    suffix = args.output.suffix.lower()
    debug("Output format detected", format=suffix)

    try:
        if suffix == ".json":
            args.output.write_text(
                json.dumps(parsed, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            print(
                CLIStyle.color(
                    f"JSON output saved to: {args.output}", CLIStyle.COLORS["CONTENT"]
                )
            )
        elif suffix == ".txt":
            args.output.write_text(render_text(parsed), encoding="utf-8")
            print(
                CLIStyle.color(
                    f"Text output saved to: {args.output}", CLIStyle.COLORS["CONTENT"]
                )
            )
        elif suffix == ".md":
            args.output.write_text(render_markdown(parsed), encoding="utf-8")
            print(
                CLIStyle.color(
                    f"Markdown output saved to: {args.output}",
                    CLIStyle.COLORS["CONTENT"],
                )
            )
        else:
            print(
                CLIStyle.color(
                    "Error: Unsupported output format. Use .json, .txt, or .md",
                    CLIStyle.COLORS["ERROR"],
                )
            )
            return 1
    except Exception as e:
        if DEBUG_MODE:
            import traceback

            traceback.print_exc()
        print(
            CLIStyle.color(f"Error writing output: {str(e)}", CLIStyle.COLORS["ERROR"])
        )
        return 1

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(
            CLIStyle.color("\nOperation cancelled by user", CLIStyle.COLORS["WARNING"])
        )
        sys.exit(0)
    except Exception as e:
        if DEBUG_MODE:
            import traceback

            traceback.print_exc()
        print(CLIStyle.color(f"\nError: {str(e)}", CLIStyle.COLORS["ERROR"]))
        sys.exit(1)
