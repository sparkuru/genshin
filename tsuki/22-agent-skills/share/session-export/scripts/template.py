#!/usr/bin/env python3
"""Shared helpers for session transcript exporters.

Agent-specific scripts should keep parsing logic local and use this module for
the common CLI, timestamp, Markdown, and readable QA rendering behavior.
"""

from __future__ import annotations

import argparse
import html
import json
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Sequence


class CLIStyle:
    """ANSI helpers for command-line help text."""

    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    CYAN = "\033[36m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"

    @staticmethod
    def enabled() -> bool:
        return sys.stdout.isatty()

    @classmethod
    def paint(cls, text: str, *styles: str) -> str:
        if not cls.enabled():
            return text
        return "".join(styles) + text + cls.RESET


class ColoredArgumentParser(argparse.ArgumentParser):
    """ArgumentParser with compact colored headings on interactive terminals."""

    def format_help(self) -> str:
        text = super().format_help()
        if not CLIStyle.enabled():
            return text
        replacements = {
            "usage:": CLIStyle.paint("usage:", CLIStyle.BOLD, CLIStyle.CYAN),
            "positional arguments:": CLIStyle.paint(
                "positional arguments:", CLIStyle.BOLD, CLIStyle.CYAN
            ),
            "options:": CLIStyle.paint("options:", CLIStyle.BOLD, CLIStyle.CYAN),
            "examples:": CLIStyle.paint("examples:", CLIStyle.BOLD, CLIStyle.GREEN),
        }
        for plain, styled in replacements.items():
            text = text.replace(plain, styled)
        return text


def create_example_text(lines: Sequence[str]) -> str:
    return "\n".join(lines)


def get_object(value: Any, key: str, default: Any = None) -> Any:
    if isinstance(value, dict):
        return value.get(key, default)
    return default


def get_string(value: Any, key: str, default: str = "") -> str:
    candidate = get_object(value, key)
    if isinstance(candidate, str):
        return candidate
    return default


def json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2, sort_keys=True)


def parse_json_string(value: str) -> Any:
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


def truncate_text(text: str, limit: int = 4000) -> str:
    if len(text) <= limit:
        return text
    return text[:limit].rstrip() + "\n\n... truncated ..."


def truncate_inline(text: str, limit: int = 120) -> str:
    compact = " ".join(text.split())
    if len(compact) <= limit:
        return compact
    return compact[: limit - 13].rstrip() + " ... truncated"


def markdown_escape(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def sanitize_filename(value: str, fallback: str) -> str:
    cleaned = "".join(
        character if character.isalnum() or character in "-_." else "-"
        for character in value.strip()
    )
    cleaned = "-".join(part for part in cleaned.split("-") if part)
    return cleaned[:120] or fallback


def code_fence(content: str, language: str = "") -> str:
    fence = "```"
    while fence in content:
        fence += "`"
    header = fence + language if language else fence
    return f"{header}\n{content.rstrip()}\n{fence}"


def details_block(summary: str, body: str) -> str:
    return (
        f"<details>\n<summary>{html.escape(summary)}</summary>\n\n{body}\n\n</details>"
    )


def render_heading(level: int, title: str) -> str:
    return f"{'#' * level} {title}"


def render_metadata_table(rows: Sequence[tuple[str, Any]]) -> str:
    visible_rows = [(key, value) for key, value in rows if value not in (None, "")]
    if not visible_rows:
        return ""
    lines = ["| Field | Value |", "| --- | --- |"]
    for key, value in visible_rows:
        lines.append(f"| {markdown_escape(str(key))} | {markdown_escape(str(value))} |")
    return "\n".join(lines)


def parse_timestamp(value: Any) -> datetime | None:
    if value in (None, ""):
        return None
    if isinstance(value, (int, float)):
        seconds = float(value)
        if seconds > 10_000_000_000:
            seconds /= 1000
        try:
            return datetime.fromtimestamp(seconds, tz=timezone.utc)
        except (OverflowError, OSError, ValueError):
            return None
    if not isinstance(value, str):
        return None
    text = value.strip()
    if not text:
        return None
    try:
        numeric = float(text)
    except ValueError:
        numeric = None
    if numeric is not None:
        return parse_timestamp(numeric)
    try:
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        return datetime.fromisoformat(text)
    except ValueError:
        return None


def format_timestamp(value: Any) -> str:
    parsed = parse_timestamp(value)
    if parsed is None:
        return str(value) if value not in (None, "") else ""
    local = parsed.astimezone()
    offset = local.utcoffset()
    if offset is None:
        suffix = "UTC"
    else:
        total_minutes = int(offset.total_seconds() // 60)
        sign = "+" if total_minutes >= 0 else "-"
        absolute = abs(total_minutes)
        hours, minutes = divmod(absolute, 60)
        suffix = f"UTC{sign}{hours:02d}:{minutes:02d}"
    return f"{local:%Y-%m-%d %H:%M:%S} ({suffix})"


def render_time_line(timestamp: Any) -> str:
    rendered = format_timestamp(timestamp)
    if not rendered:
        return ""
    return (
        f'<p align="right"><sub><strong>Time: {html.escape(rendered)}'
        "</strong></sub></p>"
    )


def render_aligned_heading(level: int, title: str, align: str) -> str:
    return f'<h{level} align="{align}"><strong>{html.escape(title)}</strong></h{level}>'


def render_role_heading(title: str) -> str:
    return render_aligned_heading(3, title.upper(), "center")


def render_text_html(text: str) -> str:
    paragraphs: list[str] = []
    buffer: list[str] = []
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if not line:
            if buffer:
                paragraphs.append(
                    "<p>" + "<br>\n".join(html.escape(part) for part in buffer) + "</p>"
                )
                buffer = []
            continue
        buffer.append(line)
    if buffer:
        paragraphs.append(
            "<p>" + "<br>\n".join(html.escape(part) for part in buffer) + "</p>"
        )
    return "\n".join(paragraphs) if paragraphs else "<p></p>"


@dataclass
class ActivityLog:
    searches: list[str] = field(default_factory=list)
    commands: list[str] = field(default_factory=list)
    edits: list[str] = field(default_factory=list)
    tools: list[str] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


@dataclass
class ReadableAttachment:
    title: str
    content: str
    timestamp: Any = ""
    content_is_html: bool = False


@dataclass
class ReadableTurn:
    user_text: str
    user_time: Any = ""
    assistant_text: str = ""
    assistant_time: Any = ""
    attachments: list[ReadableAttachment] = field(default_factory=list)


def create_activity_log() -> ActivityLog:
    return ActivityLog()


def activity_has_items(activity: ActivityLog) -> bool:
    return any(
        (
            activity.searches,
            activity.commands,
            activity.edits,
            activity.tools,
            activity.notes,
        )
    )


def append_unique(items: list[str], value: str, limit: int = 80) -> None:
    cleaned = " ".join(str(value).split())
    if not cleaned:
        return
    clipped = truncate_inline(cleaned, limit)
    if clipped not in items:
        items.append(clipped)


def summarize_items(items: Sequence[str], max_items: int = 6) -> list[str]:
    if len(items) <= max_items:
        return list(items)
    visible = list(items[:max_items])
    visible.append(f"... plus {len(items) - max_items} more")
    return visible


def render_activity_item(label: str, value: str) -> str:
    return f"<li><strong>{html.escape(label)}:</strong> <code>{html.escape(value)}</code></li>"


def render_activity(activity: ActivityLog) -> str:
    items: list[str] = []
    for value in summarize_items(activity.edits):
        items.append(render_activity_item("Changed", value))
    for value in summarize_items(activity.searches):
        items.append(render_activity_item("Searched", value))
    for value in summarize_items(activity.commands):
        items.append(render_activity_item("Ran", value))
    for value in summarize_items(activity.tools):
        items.append(render_activity_item("Used", value))
    for value in summarize_items(activity.notes):
        items.append(render_activity_item("Note", value))
    if not items:
        return ""
    return "<ul>\n" + "\n".join(items) + "\n</ul>"


def flush_activity_to_turn(
    turn: ReadableTurn | None, activity: ActivityLog, timestamp: Any = ""
) -> ActivityLog:
    if turn is None:
        return create_activity_log()
    rendered = render_activity(activity)
    if rendered:
        turn.attachments.append(
            ReadableAttachment(
                title="Operations",
                timestamp=timestamp,
                content=rendered,
                content_is_html=True,
            )
        )
    return create_activity_log()


def render_attachment_body(attachment: ReadableAttachment) -> str:
    if attachment.content_is_html:
        return f"<div>\n{attachment.content}\n</div>"
    return f"<div>\n{render_text_html(attachment.content)}\n</div>"


def render_attachment(attachment: ReadableAttachment) -> str:
    time_line = render_time_line(attachment.timestamp)
    body_parts = [
        part for part in [time_line, render_attachment_body(attachment)] if part
    ]
    body = "\n\n".join(body_parts)
    return (
        "<details>\n"
        f"<summary>{html.escape(attachment.title)}</summary>\n\n"
        f"{body}\n\n"
        "</details>"
    )


def render_readable_turn(turn: ReadableTurn, include_appendix: bool = True) -> str:
    blocks: list[str] = [
        render_role_heading("User"),
        render_time_line(turn.user_time),
        turn.user_text.strip(),
    ]
    visible_attachments = turn.attachments if include_appendix else []
    if turn.assistant_text.strip() or visible_attachments:
        blocks.extend(
            [
                render_role_heading("Assistant"),
                render_time_line(turn.assistant_time),
            ]
        )
        if turn.assistant_text.strip():
            blocks.append(turn.assistant_text.strip())
        if visible_attachments:
            blocks.append("#### Appendix")
            blocks.extend(
                render_attachment(attachment) for attachment in visible_attachments
            )
    return "\n\n".join(block for block in blocks if block)


def render_readable_markdown(
    title: str,
    metadata_rows: Sequence[tuple[str, Any]],
    turns: Sequence[ReadableTurn],
    include_appendix: bool = True,
) -> str:
    blocks = [render_heading(1, title)]
    metadata = render_metadata_table(metadata_rows)
    if metadata:
        blocks.append(metadata)
    blocks.extend(render_readable_turn(turn, include_appendix) for turn in turns)
    return "\n\n---\n\n".join(block for block in blocks if block) + "\n"


def write_output(path: Path | None, content: str) -> None:
    if path is None:
        sys.stdout.write(content)
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
