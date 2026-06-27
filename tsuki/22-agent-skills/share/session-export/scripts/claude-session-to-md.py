#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Convert Claude Code JSONL session transcripts into readable Markdown."""

from __future__ import annotations

import argparse
import json
import re
import sys
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import template as session_template


DEBUG_MODE = False


class CLIStyle:
    """CLI tool unified style config."""

    COLORS = {
        "TITLE": 7,
        "SUB_TITLE": 2,
        "CONTENT": 3,
        "EXAMPLE": 7,
        "WARNING": 4,
        "ERROR": 2,
        "OK": 3,
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

    @staticmethod
    def write(
        text: str = "", color: int = COLORS["CONTENT"], error: bool = False
    ) -> None:
        """Write styled terminal output."""
        stream = sys.stderr if error else sys.stdout
        stream.write(f"{CLIStyle.color(text, color)}\n")
        stream.flush()


class ColoredArgumentParser(argparse.ArgumentParser):
    """Argument parser with colored help output."""

    def _format_action_invocation(self, action: argparse.Action) -> str:
        """Format option names with semantic terminal colors."""
        if not action.option_strings:
            (metavar,) = self._metavar_formatter(action, action.dest)(1)
            return metavar
        parts: list[str] = []
        if action.nargs == 0:
            parts.extend(
                CLIStyle.color(option, CLIStyle.COLORS["SUB_TITLE"])
                for option in action.option_strings
            )
            return ", ".join(parts)
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
        """Return colored help text."""
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


@dataclass(frozen=True)
class JsonLineRecord:
    """One parsed JSONL record with source position."""

    line_number: int
    data: dict[str, Any]


@dataclass(frozen=True)
class RenderOptions:
    """Markdown rendering options."""

    input_path: Path
    session_name: str
    include_system: bool
    include_usage: bool
    include_unknown: bool
    include_appendix: bool
    max_output_chars: int


def debug(
    *args: Any, file: str | None = None, append: bool = True, **kwargs: Any
) -> None:
    """
    Print debug details with optional file output.
    ```python
    debug("records", count=10)

    return = None
    ```
    """
    if not DEBUG_MODE:
        return
    output = " ".join(str(arg) for arg in args)
    if kwargs:
        output += " " + " ".join(f"{key}={value}" for key, value in kwargs.items())
    output += "\n"
    if file is not None:
        file_mode = "a" if append else "w"
        with open(file, file_mode, encoding="utf-8") as file_handle:
            file_handle.write(output)
        return
    CLIStyle.write(output.rstrip(), CLIStyle.COLORS["WARNING"], error=True)


def create_example_text(
    script_name: str,
    examples: list[tuple[str, str]],
    notes: list[str] | None = None,
) -> str:
    """Create colored example help text."""
    text = f"\n{CLIStyle.color('Examples:', CLIStyle.COLORS['SUB_TITLE'])}"
    for desc, cmd in examples:
        text += f"\n  {CLIStyle.color(f'# {desc}', CLIStyle.COLORS['EXAMPLE'])}"
        text += f"\n  {CLIStyle.color(f'{script_name} {cmd}', CLIStyle.COLORS['CONTENT'])}\n"
    if notes:
        text += f"\n{CLIStyle.color('Notes:', CLIStyle.COLORS['SUB_TITLE'])}"
        for note in notes:
            text += f"\n  {CLIStyle.color(f'- {note}', CLIStyle.COLORS['CONTENT'])}"
    return text


def get_object(value: Any) -> dict[str, Any]:
    """Return value if it is a dict, otherwise an empty dict."""
    if isinstance(value, dict):
        return value
    return {}


def get_string(value: Any) -> str:
    """Return value if it is a string, otherwise an empty string."""
    if isinstance(value, str):
        return value
    return ""


def json_dumps(value: Any) -> str:
    """Dump JSON for Markdown display."""
    return json.dumps(value, ensure_ascii=False, indent=2)


def truncate_text(text: str, limit: int) -> str:
    """Truncate text to a positive character limit."""
    if limit <= 0 or len(text) <= limit:
        return text
    omitted = len(text) - limit
    return f"{text[:limit]}\n\n[truncated {omitted} characters]"


def markdown_escape(text: str) -> str:
    """Escape text for inline Markdown positions."""
    return text.replace("|", "\\|").replace("\n", " ")


def code_fence(text: str, language: str = "") -> str:
    """Wrap text in a Markdown code fence."""
    max_run = 0
    current = 0
    for char in text:
        if char == "`":
            current += 1
            max_run = max(max_run, current)
            continue
        current = 0
    fence = "`" * max(3, max_run + 1)
    return f"{fence}{language}\n{text}\n{fence}"


def details_block(summary: str, value: Any) -> str:
    """Render a collapsible JSON details block."""
    return "\n".join(
        [
            f"<details><summary>{markdown_escape(summary)}</summary>",
            "",
            code_fence(json_dumps(value), "json"),
            "",
            "</details>",
        ]
    )


def render_heading(level: int, text: str) -> str:
    """Render a Markdown heading."""
    return f"{'#' * level} {text}"


def render_metadata_table(rows: list[tuple[str, Any]]) -> str:
    """Render key value metadata as a Markdown table."""
    visible_rows = [(key, value) for key, value in rows if value not in ("", None)]
    if not visible_rows:
        return ""
    lines = ["| Key | Value |", "| --- | --- |"]
    for key, value in visible_rows:
        lines.append(f"| {markdown_escape(key)} | {markdown_escape(str(value))} |")
    return "\n".join(lines)


def read_jsonl(path: Path) -> list[JsonLineRecord]:
    """Read a JSONL file and return object records."""
    records: list[JsonLineRecord] = []
    with open(path, "r", encoding="utf-8") as file_handle:
        for line_number, line in enumerate(file_handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            data = json.loads(stripped)
            if not isinstance(data, dict):
                raise ValueError(f"line {line_number} is not a JSON object")
            records.append(JsonLineRecord(line_number=line_number, data=data))
    return records


def extract_text_content(content: Any) -> str:
    """Extract visible text from Claude message content."""
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    parts: list[str] = []
    for item in content:
        if isinstance(item, str):
            parts.append(item)
            continue
        item_object = get_object(item)
        if item_object.get("type") == "text":
            text = get_string(item_object.get("text"))
            if text:
                parts.append(text)
    return "\n\n".join(parts)


def render_message(role: str, text: str) -> str:
    """Render one user or assistant message."""
    if not text.strip():
        return ""
    return "\n\n".join([render_heading(2, role.capitalize()), text.strip()])


def render_tool_use(item: dict[str, Any]) -> str:
    """Render a Claude tool_use content block."""
    name = get_string(item.get("name")) or "tool"
    rows = [("id", item.get("id"))]
    body = [render_heading(3, f"Tool call: {name}"), render_metadata_table(rows)]
    tool_input = item.get("input")
    if tool_input not in ("", None):
        body.append(code_fence(json_dumps(tool_input), "json"))
    return "\n\n".join(part for part in body if part)


def render_tool_result(item: dict[str, Any], options: RenderOptions) -> str:
    """Render a Claude tool_result content block."""
    rows = [
        ("tool use id", item.get("tool_use_id")),
        ("is error", item.get("is_error")),
    ]
    body = [render_heading(3, "Tool result"), render_metadata_table(rows)]
    content = item.get("content")
    if isinstance(content, (dict, list)):
        body.append(code_fence(json_dumps(content), "json"))
    elif isinstance(content, str) and content:
        body.append(
            code_fence(truncate_text(content, options.max_output_chars), "text")
        )
    return "\n\n".join(part for part in body if part)


def render_usage(message: dict[str, Any], options: RenderOptions) -> str:
    """Render token usage if requested."""
    if not options.include_usage:
        return ""
    usage = get_object(message.get("usage"))
    if not usage:
        return ""
    rows: list[tuple[str, Any]] = []
    for key, value in usage.items():
        if isinstance(value, (str, int, float, bool)) or value is None:
            rows.append((key.replace("_", " "), value))
    body = [render_heading(3, "Usage"), render_metadata_table(rows)]
    nested = {
        key: value
        for key, value in usage.items()
        if isinstance(value, (dict, list)) and value
    }
    if nested:
        body.append(details_block("usage details", nested))
    return "\n\n".join(part for part in body if part)


def render_message_record(record: JsonLineRecord, options: RenderOptions) -> str:
    """Render a Claude user or assistant record."""
    data = record.data
    message = get_object(data.get("message"))
    role = get_string(message.get("role")) or get_string(data.get("type")) or "message"
    content = message.get("content")
    body: list[str] = []

    text = extract_text_content(content)
    if text:
        body.append(render_message(role, text))

    if isinstance(content, list):
        for item in content:
            item_object = get_object(item)
            item_type = get_string(item_object.get("type"))
            if item_type == "tool_use":
                body.append(render_tool_use(item_object))
            elif item_type == "tool_result":
                body.append(render_tool_result(item_object, options))
            elif item_type in ("thinking", "redacted_thinking"):
                if options.include_system:
                    body.append(
                        details_block(
                            f"thinking line {record.line_number}", item_object
                        )
                    )
            elif item_type and item_type != "text" and options.include_unknown:
                body.append(details_block(f"content: {item_type}", item_object))

    usage = render_usage(message, options)
    if usage:
        body.append(usage)
    if not body and options.include_system and options.include_unknown:
        body.append(details_block(f"message line {record.line_number}: {role}", data))
    return "\n\n".join(part for part in body if part)


def find_session_name(records: list[JsonLineRecord]) -> str:
    """Find the Claude AI-generated session title when present."""
    title = ""
    for record in records:
        data = record.data
        if data.get("type") == "ai-title":
            title = get_string(data.get("aiTitle"))
    return title


def find_session_id(records: list[JsonLineRecord]) -> str:
    """Find a stable Claude session id."""
    for record in records:
        session_id = get_string(record.data.get("sessionId"))
        if session_id:
            return session_id
    return ""


def render_session_meta(records: list[JsonLineRecord], options: RenderOptions) -> str:
    """Render top-level Claude session metadata."""
    first_rich_record = next(
        (
            record.data
            for record in records
            if record.data.get("sessionId") or record.data.get("cwd")
        ),
        {},
    )
    rows = [
        ("source file", options.input_path),
        ("session id", find_session_id(records)),
        ("session title", options.session_name),
        ("cwd", first_rich_record.get("cwd")),
        ("entrypoint", first_rich_record.get("entrypoint")),
        ("version", first_rich_record.get("version")),
        ("git branch", first_rich_record.get("gitBranch")),
        ("timestamp", first_rich_record.get("timestamp")),
    ]
    return "\n\n".join(
        [render_heading(1, "Claude Code Session"), render_metadata_table(rows)]
    )


def render_system_record(record: JsonLineRecord, options: RenderOptions) -> str:
    """Render non-conversation Claude records when requested."""
    data = record.data
    record_type = get_string(data.get("type")) or "unknown"
    if record_type == "ai-title":
        return ""
    if record_type == "last-prompt" and options.include_system:
        prompt = get_string(data.get("lastPrompt"))
        return "\n\n".join([render_heading(3, "Last prompt"), prompt]) if prompt else ""
    if record_type == "mode" and options.include_system:
        return "\n\n".join(
            [
                render_heading(3, "Mode"),
                render_metadata_table(
                    [("mode", data.get("mode")), ("session id", data.get("sessionId"))]
                ),
            ]
        )
    if options.include_system:
        return details_block(f"record line {record.line_number}: {record_type}", data)
    return ""


def render_record(record: JsonLineRecord, options: RenderOptions) -> str:
    """Render one Claude JSONL record."""
    record_type = get_string(record.data.get("type"))
    if record_type in ("user", "assistant"):
        return render_message_record(record, options)
    if record_type in (
        "queue-operation",
        "attachment",
        "file-history-snapshot",
        "last-prompt",
        "mode",
        "ai-title",
    ):
        return render_system_record(record, options)
    if options.include_unknown:
        return details_block(
            f"record line {record.line_number}: {record_type or 'unknown'}", record.data
        )
    return ""


def append_text(existing: str, addition: str) -> str:
    """Append Markdown text with a blank line separator."""
    cleaned = addition.strip()
    if not cleaned:
        return existing
    if not existing.strip():
        return cleaned
    return existing.rstrip() + "\n\n" + cleaned


def clean_user_text(text: str) -> str:
    """Remove Claude IDE metadata tags from a visible user prompt."""
    cleaned = re.sub(
        r"<ide_opened_file>.*?</ide_opened_file>",
        "",
        text,
        flags=re.DOTALL,
    )
    return cleaned.strip()


def is_low_value_assistant_text(text: str) -> bool:
    """Return whether assistant text is a transport marker, not an answer."""
    return text.strip() == "No response requested."


def is_process_assistant_text(text: str) -> bool:
    """Return whether assistant text is a short process narration."""
    lowered = text.strip().lower()
    return lowered.startswith(
        (
            "now ",
            "now let ",
            "let me ",
            "i need to ",
            "all behaviors verified. now ",
        )
    )


def content_blocks(content: Any) -> list[dict[str, Any]]:
    """Return object-like Claude content blocks."""
    if not isinstance(content, list):
        return []
    return [get_object(item) for item in content if isinstance(item, dict)]


def content_has_type(content: Any, block_type: str) -> bool:
    """Return whether Claude content has a block type."""
    return any(
        get_string(block.get("type")) == block_type for block in content_blocks(content)
    )


def first_path_value(value: dict[str, Any]) -> str:
    """Find a likely file path in a tool input object."""
    for key in ("file_path", "path", "notebook_path", "filename"):
        path = get_string(value.get(key))
        if path:
            return path
    return ""


def summarize_claude_tool_use(
    item: dict[str, Any], activity: session_template.ActivityLog
) -> None:
    """Summarize one Claude tool call for the readable appendix."""
    name = get_string(item.get("name")) or "tool"
    tool_input = item.get("input")
    input_object = get_object(tool_input)
    lower_name = name.lower()
    if name == "Bash":
        command = get_string(input_object.get("command"))
        if command:
            session_template.append_unique(activity.commands, command, limit=140)
            return
    if name in ("Edit", "MultiEdit", "Write", "NotebookEdit"):
        path = first_path_value(input_object)
        label = f"{name} {path}".strip()
        session_template.append_unique(activity.edits, label, limit=140)
        return
    if name in ("Read", "LS", "Glob", "Grep", "WebSearch", "WebFetch"):
        query = (
            get_string(input_object.get("pattern"))
            or get_string(input_object.get("query"))
            or first_path_value(input_object)
            or name
        )
        session_template.append_unique(activity.searches, f"{name} {query}", limit=140)
        return
    if "search" in lower_name or "grep" in lower_name or "read" in lower_name:
        session_template.append_unique(activity.searches, name, limit=120)
        return
    session_template.append_unique(activity.tools, name, limit=120)


def readable_metadata_rows(
    records: list[JsonLineRecord], options: RenderOptions
) -> list[tuple[str, Any]]:
    """Build metadata rows for the readable Claude renderer."""
    first_rich_record = next(
        (
            record.data
            for record in records
            if record.data.get("sessionId") or record.data.get("cwd")
        ),
        {},
    )
    return [
        ("source file", options.input_path),
        ("session id", find_session_id(records)),
        ("session title", options.session_name),
        ("cwd", first_rich_record.get("cwd")),
        ("entrypoint", first_rich_record.get("entrypoint")),
        ("version", first_rich_record.get("version")),
        ("git branch", first_rich_record.get("gitBranch")),
        (
            "timestamp",
            session_template.format_timestamp(first_rich_record.get("timestamp")),
        ),
    ]


def render_readable_markdown(
    records: list[JsonLineRecord], options: RenderOptions
) -> str:
    """Render a low-noise QA transcript for default output."""
    turns: list[session_template.ReadableTurn] = []
    current_turn: session_template.ReadableTurn | None = None
    activity = session_template.create_activity_log()
    activity_time: Any = ""
    assistant_segments: list[tuple[Any, str]] = []

    def finalize_current_turn() -> None:
        nonlocal activity, activity_time, assistant_segments
        if current_turn is None:
            return
        if assistant_segments:
            had_activity = session_template.activity_has_items(activity)
            if had_activity:
                commentary_segments = assistant_segments[:-1]
                final_segments = assistant_segments[-1:]
                if final_segments and is_process_assistant_text(final_segments[0][1]):
                    commentary_segments = assistant_segments
                    final_segments = []
            else:
                commentary_segments = []
                final_segments = assistant_segments
            for segment_time, segment_text in commentary_segments:
                current_turn.attachments.append(
                    session_template.ReadableAttachment(
                        title="Assistant commentary",
                        timestamp=segment_time,
                        content=segment_text.strip(),
                    )
                )
            for segment_time, segment_text in final_segments:
                current_turn.assistant_text = append_text(
                    current_turn.assistant_text, segment_text
                )
                current_turn.assistant_time = segment_time
        activity = session_template.flush_activity_to_turn(
            current_turn, activity, activity_time
        )
        activity_time = ""
        assistant_segments = []

    for record in records:
        data = record.data
        record_type = get_string(data.get("type"))
        timestamp = data.get("timestamp")
        message = get_object(data.get("message"))
        content = message.get("content")
        text = extract_text_content(content)

        if record_type == "user":
            if data.get("isMeta") is True:
                continue
            text = clean_user_text(text)
            if not text.strip() or content_has_type(content, "tool_result"):
                continue
            finalize_current_turn()
            current_turn = session_template.ReadableTurn(
                user_text=text.strip(), user_time=timestamp
            )
            turns.append(current_turn)
            continue

        if record_type != "assistant":
            continue
        if current_turn is None:
            current_turn = session_template.ReadableTurn(user_text="")
            turns.append(current_turn)

        blocks = content_blocks(content)
        if text.strip() and not is_low_value_assistant_text(text):
            assistant_segments.append((timestamp, text.strip()))

        for block in blocks:
            block_type = get_string(block.get("type"))
            if block_type == "tool_use":
                summarize_claude_tool_use(block, activity)
                activity_time = timestamp
            elif block_type == "thinking":
                thinking = get_string(block.get("thinking"))
                if thinking:
                    current_turn.attachments.append(
                        session_template.ReadableAttachment(
                            title="Reasoning",
                            timestamp=timestamp,
                            content=thinking,
                        )
                    )

    finalize_current_turn()
    return session_template.render_readable_markdown(
        "Claude Code Session",
        readable_metadata_rows(records, options),
        turns,
        options.include_appendix,
    )


def render_markdown(records: list[JsonLineRecord], options: RenderOptions) -> str:
    """Render all records to Markdown."""
    if not options.include_system and not options.include_usage:
        return render_readable_markdown(records, options)
    blocks = [render_session_meta(records, options)]
    for record in records:
        block = render_record(record, options)
        if block.strip():
            blocks.append(block.strip())
    return "\n\n---\n\n".join(blocks) + "\n"


def sanitize_filename(value: str) -> str:
    """Convert a session name into a filesystem-friendly filename stem."""
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._- ")
    chars: list[str] = []
    previous_dash = False
    for char in value.strip():
        if char in allowed or ord(char) > 127:
            chars.append(char)
            previous_dash = False
            continue
        if not previous_dash:
            chars.append("-")
            previous_dash = True
    cleaned = "".join(chars).strip(" .-_")
    while "--" in cleaned:
        cleaned = cleaned.replace("--", "-")
    return cleaned or "claude-session"


def default_output_path(records: list[JsonLineRecord], input_path: Path) -> Path:
    """Return a default Markdown path near the current working directory."""
    stem = find_session_name(records) or find_session_id(records) or input_path.stem
    return Path.cwd() / f"{sanitize_filename(stem)}.md"


def write_output(output_path: Path | None, markdown: str) -> None:
    """Write Markdown to a file or stdout."""
    if output_path is None:
        sys.stdout.write(markdown)
        sys.stdout.flush()
        return
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(markdown, encoding="utf-8")
    CLIStyle.write(f"Wrote Markdown: {output_path}", CLIStyle.COLORS["OK"], error=True)


def build_parser() -> argparse.ArgumentParser:
    """Build the command line parser."""
    script_name = Path(__file__).name
    epilog = create_example_text(
        script_name,
        [
            (
                "Convert a Claude Code project session",
                "~/.claude/projects/-path-to-project/session.jsonl -o session.md",
            ),
            (
                "Include hidden setup records and token accounting",
                "session.jsonl --include-all",
            ),
            (
                "Write a title-based Markdown file in the current directory",
                "session.jsonl --default-output",
            ),
        ],
        notes=[
            "Claude Code 2.1.x stores resumable sessions as JSONL under ~/.claude/projects/<encoded-cwd>/.",
            "Known records: user, assistant, ai-title, attachment, queue-operation, file-history-snapshot, last-prompt, and mode.",
            "Unknown records are kept as collapsible JSON by default.",
        ],
    )
    parser = ColoredArgumentParser(
        description="Convert Claude Code JSONL session transcripts into Markdown.",
        epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "session_jsonl",
        help=CLIStyle.color(
            "Path to a Claude Code session JSONL file.", CLIStyle.COLORS["CONTENT"]
        ),
    )
    parser.add_argument(
        "-o",
        "--output",
        help=CLIStyle.color(
            "Output Markdown file. Defaults to stdout.", CLIStyle.COLORS["CONTENT"]
        ),
    )
    parser.add_argument(
        "--default-output",
        action="store_true",
        help=CLIStyle.color(
            "Write TITLE.md in the current directory when --output is omitted.",
            CLIStyle.COLORS["CONTENT"],
        ),
    )
    parser.add_argument(
        "--include-system",
        action="store_true",
        help=CLIStyle.color(
            "Include setup, attachment, queue, mode, and hidden thinking records.",
            CLIStyle.COLORS["CONTENT"],
        ),
    )
    parser.add_argument(
        "--include-usage",
        action="store_true",
        help=CLIStyle.color(
            "Include token usage blocks when present.", CLIStyle.COLORS["CONTENT"]
        ),
    )
    parser.add_argument(
        "--include-all",
        action="store_true",
        help=CLIStyle.color(
            "Include both usage blocks and system context records.",
            CLIStyle.COLORS["CONTENT"],
        ),
    )
    parser.add_argument(
        "-q",
        "--quiet",
        "--release",
        action="store_true",
        dest="quiet",
        help=CLIStyle.color(
            "Omit appendix blocks in the default QA output.",
            CLIStyle.COLORS["CONTENT"],
        ),
    )
    parser.add_argument(
        "--no-unknown",
        action="store_true",
        help=CLIStyle.color(
            "Skip unknown records instead of rendering JSON details.",
            CLIStyle.COLORS["CONTENT"],
        ),
    )
    parser.add_argument(
        "--max-output-chars",
        type=int,
        default=12000,
        help=CLIStyle.color(
            "Maximum characters per rendered tool output; 0 disables truncation.",
            CLIStyle.COLORS["CONTENT"],
        ),
    )
    parser.add_argument(
        "--log",
        action="store_true",
        help=CLIStyle.color(
            "Enable traceback output for debugging.", CLIStyle.COLORS["CONTENT"]
        ),
    )
    return parser


def run(args: argparse.Namespace) -> int:
    """Run the conversion command."""
    input_path = Path(args.session_jsonl).expanduser().resolve()
    if not input_path.is_file():
        raise FileNotFoundError(f"input file not found: {input_path}")
    if args.max_output_chars < 0:
        raise ValueError("max-output-chars must be >= 0")

    records = read_jsonl(input_path)
    debug("records", count=len(records))
    output_path = Path(args.output).expanduser().resolve() if args.output else None
    if output_path is None and args.default_output:
        output_path = default_output_path(records, input_path).resolve()
    options = RenderOptions(
        input_path=input_path,
        session_name=find_session_name(records),
        include_system=args.include_system or args.include_all,
        include_usage=args.include_usage or args.include_all,
        include_unknown=not args.no_unknown,
        include_appendix=not args.quiet,
        max_output_chars=args.max_output_chars,
    )
    write_output(output_path, render_markdown(records, options))
    return 0


def main() -> int:
    """Main program logic."""
    global DEBUG_MODE
    parser = build_parser()
    args = parser.parse_args()
    DEBUG_MODE = args.log
    try:
        return run(args)
    except KeyboardInterrupt:
        CLIStyle.write("Interrupted by user", CLIStyle.COLORS["WARNING"], error=True)
        return 130
    except FileNotFoundError as exc:
        CLIStyle.write(f"Error: {exc}", CLIStyle.COLORS["ERROR"], error=True)
        return 1
    except Exception as exc:
        if DEBUG_MODE:
            traceback.print_exc()
        CLIStyle.write(f"Error: {exc}", CLIStyle.COLORS["ERROR"], error=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
