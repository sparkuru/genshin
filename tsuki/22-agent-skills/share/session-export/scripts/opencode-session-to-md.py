#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Convert OpenCode exported JSON or local SQLite sessions into Markdown."""

from __future__ import annotations

import argparse
import json
import sqlite3
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
DEFAULT_DB_PATH = Path("~/.local/share/opencode/opencode.db").expanduser()


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
class RenderOptions:
    """Markdown rendering options."""

    source: str
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
    debug("session", session_id="ses_...")

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


def json_loads_object(value: str) -> dict[str, Any]:
    """Load a JSON string that must contain an object."""
    data = json.loads(value)
    if not isinstance(data, dict):
        raise ValueError("expected JSON object")
    return data


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


def read_export_json(path: Path) -> dict[str, Any]:
    """Read an OpenCode JSON export file."""
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("OpenCode export must be a JSON object")
    return data


def connect_db(path: Path) -> sqlite3.Connection:
    """Open the OpenCode SQLite database in read-only mode."""
    if not path.is_file():
        raise FileNotFoundError(f"database not found: {path}")
    connection = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    return connection


def find_latest_session_id(connection: sqlite3.Connection) -> str:
    """Find the most recently updated OpenCode session id."""
    row = connection.execute(
        "select id from session order by time_updated desc limit 1"
    ).fetchone()
    if row is None:
        raise ValueError("no OpenCode sessions found")
    return str(row["id"])


def load_session_from_db(
    connection: sqlite3.Connection, session_id: str
) -> dict[str, Any]:
    """Load one OpenCode session from local SQLite storage."""
    session_row = connection.execute(
        "select * from session where id = ?",
        (session_id,),
    ).fetchone()
    if session_row is None:
        raise ValueError(f"session not found: {session_id}")

    session = dict(session_row)
    for key in ("model", "summary_diffs", "metadata"):
        value = session.get(key)
        if isinstance(value, str) and value:
            try:
                session[key] = json.loads(value)
            except json.JSONDecodeError:
                pass

    messages: list[dict[str, Any]] = []
    message_rows = connection.execute(
        "select id, session_id, data from message where session_id = ? order by time_created, id",
        (session_id,),
    ).fetchall()
    for message_row in message_rows:
        message_info = json_loads_object(str(message_row["data"]))
        message_info["id"] = message_row["id"]
        message_info["sessionID"] = message_row["session_id"]
        part_rows = connection.execute(
            "select id, session_id, message_id, data from part "
            "where session_id = ? and message_id = ? order by time_created, id",
            (session_id, message_row["id"]),
        ).fetchall()
        parts: list[dict[str, Any]] = []
        for part_row in part_rows:
            part = json_loads_object(str(part_row["data"]))
            part["id"] = part_row["id"]
            part["sessionID"] = part_row["session_id"]
            part["messageID"] = part_row["message_id"]
            parts.append(part)
        messages.append({"info": message_info, "parts": parts})

    info = {
        "id": session.get("id"),
        "slug": session.get("slug"),
        "projectID": session.get("project_id"),
        "directory": session.get("directory"),
        "path": session.get("path"),
        "title": session.get("title"),
        "agent": session.get("agent"),
        "model": session.get("model"),
        "version": session.get("version"),
        "cost": session.get("cost"),
        "tokens": {
            "input": session.get("tokens_input"),
            "output": session.get("tokens_output"),
            "reasoning": session.get("tokens_reasoning"),
            "cache": {
                "read": session.get("tokens_cache_read"),
                "write": session.get("tokens_cache_write"),
            },
        },
        "time": {
            "created": session.get("time_created"),
            "updated": session.get("time_updated"),
        },
    }
    return {"info": info, "messages": messages}


def render_session_meta(session: dict[str, Any], options: RenderOptions) -> str:
    """Render OpenCode session metadata."""
    info = get_object(session.get("info"))
    model = info.get("model")
    if isinstance(model, dict):
        model_text = "/".join(
            part
            for part in (
                get_string(model.get("providerID")),
                get_string(model.get("id")),
            )
            if part
        )
    else:
        model_text = str(model) if model not in ("", None) else ""
    rows = [
        ("source", options.source),
        ("session id", info.get("id")),
        ("title", info.get("title")),
        ("slug", info.get("slug")),
        ("directory", info.get("directory")),
        ("agent", info.get("agent")),
        ("model", model_text),
        ("version", info.get("version")),
        ("created", get_object(info.get("time")).get("created")),
        ("updated", get_object(info.get("time")).get("updated")),
    ]
    body = [render_heading(1, "OpenCode Session"), render_metadata_table(rows)]
    if options.include_usage:
        body.append(render_usage(info, "Session usage"))
    return "\n\n".join(part for part in body if part)


def render_usage(info: dict[str, Any], title: str) -> str:
    """Render token and cost accounting."""
    rows = [("cost", info.get("cost"))]
    tokens = get_object(info.get("tokens"))
    for key, value in tokens.items():
        if isinstance(value, dict):
            for nested_key, nested_value in value.items():
                rows.append((f"{key} {nested_key}", nested_value))
            continue
        rows.append((key, value))
    table = render_metadata_table(rows)
    if not table:
        return ""
    return "\n\n".join([render_heading(3, title), table])


def render_part_text(part: dict[str, Any]) -> str:
    """Render an OpenCode text part."""
    text = get_string(part.get("text"))
    return text.strip()


def render_tool_part(part: dict[str, Any], options: RenderOptions) -> str:
    """Render an OpenCode tool part."""
    state = get_object(part.get("state"))
    body = [
        render_heading(3, f"Tool call: {get_string(part.get('tool')) or 'tool'}"),
        render_metadata_table(
            [
                ("part id", part.get("id")),
                ("call id", part.get("callID")),
                ("status", state.get("status")),
                ("title", state.get("title")),
            ]
        ),
    ]
    tool_input = state.get("input")
    if tool_input not in ("", None):
        body.append(render_heading(4, "input"))
        body.append(code_fence(json_dumps(tool_input), "json"))
    output = state.get("output")
    if isinstance(output, str) and output:
        body.append(render_heading(4, "output"))
        body.append(code_fence(truncate_text(output, options.max_output_chars), "text"))
    elif output not in ("", None):
        body.append(render_heading(4, "output"))
        body.append(code_fence(json_dumps(output), "json"))
    metadata = state.get("metadata") or part.get("metadata")
    if options.include_system and metadata:
        body.append(details_block("tool metadata", metadata))
    return "\n\n".join(part_text for part_text in body if part_text)


def render_file_part(part: dict[str, Any]) -> str:
    """Render an OpenCode file attachment part."""
    return "\n\n".join(
        [
            render_heading(3, "File"),
            render_metadata_table(
                [
                    ("filename", part.get("filename")),
                    ("mime", part.get("mime")),
                    ("url", part.get("url")),
                    ("source", part.get("source")),
                ]
            ),
        ]
    )


def render_message(message: dict[str, Any], options: RenderOptions) -> str:
    """Render one OpenCode message with its parts."""
    info = get_object(message.get("info"))
    role = get_string(info.get("role")) or "message"
    parts = message.get("parts")
    if not isinstance(parts, list):
        parts = []

    body: list[str] = []
    text_parts = [
        render_part_text(get_object(part))
        for part in parts
        if get_object(part).get("type") == "text"
    ]
    text = "\n\n".join(part for part in text_parts if part)
    if text:
        body.append("\n\n".join([render_heading(2, role.capitalize()), text]))

    for raw_part in parts:
        part = get_object(raw_part)
        part_type = get_string(part.get("type"))
        if part_type in ("text",):
            continue
        if part_type == "tool":
            body.append(render_tool_part(part, options))
        elif part_type == "file":
            body.append(render_file_part(part))
        elif part_type == "reasoning" and options.include_system:
            reasoning = get_string(part.get("text"))
            if reasoning:
                body.append("\n\n".join([render_heading(3, "Reasoning"), reasoning]))
        elif part_type == "step-finish" and options.include_usage:
            body.append(render_usage(part, "Step usage"))
        elif part_type == "step-start" and options.include_system:
            body.append(details_block("step start", part))
        elif part_type in ("reasoning", "step-finish", "step-start"):
            continue
        elif options.include_unknown:
            body.append(details_block(f"part: {part_type or 'unknown'}", part))

    if options.include_usage:
        usage = render_usage(info, "Message usage")
        if usage:
            body.append(usage)
    if not body and options.include_unknown:
        body.append(details_block(f"message: {role}", message))
    return "\n\n".join(part for part in body if part)


def append_text(existing: str, addition: str) -> str:
    """Append Markdown text with a blank line separator."""
    cleaned = addition.strip()
    if not cleaned:
        return existing
    if not existing.strip():
        return cleaned
    return existing.rstrip() + "\n\n" + cleaned


def time_value(info: dict[str, Any], *keys: str) -> Any:
    """Find a timestamp in an OpenCode info object."""
    time_info = get_object(info.get("time"))
    for key in keys:
        if time_info.get(key) not in ("", None):
            return time_info.get(key)
    for key in keys:
        for alternate in (key, f"time_{key}", f"time{key.capitalize()}"):
            if info.get(alternate) not in ("", None):
                return info.get(alternate)
    return ""


def first_path_value(value: dict[str, Any]) -> str:
    """Find a likely file path in a tool input object."""
    for key in ("filePath", "file_path", "path", "filename", "url"):
        path = get_string(value.get(key))
        if path:
            return path
    return ""


def summarize_opencode_tool_part(
    part: dict[str, Any], activity: session_template.ActivityLog
) -> None:
    """Summarize one OpenCode tool part for the readable appendix."""
    tool = get_string(part.get("tool")) or "tool"
    state = get_object(part.get("state"))
    title = get_string(state.get("title"))
    tool_input = get_object(state.get("input"))
    lower_label = " ".join([tool, title]).lower()

    command = (
        get_string(tool_input.get("command"))
        or get_string(tool_input.get("cmd"))
        or get_string(tool_input.get("script"))
    )
    if command:
        session_template.append_unique(activity.commands, command, limit=140)
        return

    path = first_path_value(tool_input)
    if any(word in lower_label for word in ("edit", "write", "patch", "modify")):
        label = " ".join(part for part in (title or tool, path) if part)
        session_template.append_unique(activity.edits, label, limit=140)
        return
    if any(
        word in lower_label
        for word in ("read", "search", "grep", "glob", "list", "fetch", "find")
    ):
        query = (
            get_string(tool_input.get("query"))
            or get_string(tool_input.get("pattern"))
            or path
            or title
            or tool
        )
        session_template.append_unique(activity.searches, query, limit=140)
        return
    session_template.append_unique(activity.tools, title or tool, limit=120)


def readable_metadata_rows(
    session: dict[str, Any], options: RenderOptions
) -> list[tuple[str, Any]]:
    """Build metadata rows for the readable OpenCode renderer."""
    info = get_object(session.get("info"))
    model = info.get("model")
    if isinstance(model, dict):
        model_text = "/".join(
            part
            for part in (
                get_string(model.get("providerID")),
                get_string(model.get("id")),
            )
            if part
        )
    else:
        model_text = str(model) if model not in ("", None) else ""
    time_info = get_object(info.get("time"))
    return [
        ("source", options.source),
        ("session id", info.get("id")),
        ("title", info.get("title")),
        ("slug", info.get("slug")),
        ("directory", info.get("directory")),
        ("agent", info.get("agent")),
        ("model", model_text),
        ("version", info.get("version")),
        ("created", session_template.format_timestamp(time_info.get("created"))),
        ("updated", session_template.format_timestamp(time_info.get("updated"))),
    ]


def text_parts(parts: list[Any]) -> str:
    """Extract visible text parts from an OpenCode message."""
    rendered = [
        render_part_text(get_object(part))
        for part in parts
        if get_object(part).get("type") == "text"
    ]
    return "\n\n".join(part for part in rendered if part)


def render_readable_markdown(session: dict[str, Any], options: RenderOptions) -> str:
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
            if had_activity and len(assistant_segments) > 1:
                commentary_segments = assistant_segments[:-1]
                final_segments = assistant_segments[-1:]
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

    messages = session.get("messages")
    if not isinstance(messages, list):
        messages = []
    for raw_message in messages:
        message = get_object(raw_message)
        info = get_object(message.get("info"))
        role = get_string(info.get("role"))
        parts = message.get("parts")
        if not isinstance(parts, list):
            parts = []
        text = text_parts(parts)
        created = time_value(info, "created")
        completed = time_value(info, "completed", "updated") or created

        if role == "user":
            if not text.strip():
                continue
            finalize_current_turn()
            current_turn = session_template.ReadableTurn(
                user_text=text.strip(), user_time=created
            )
            turns.append(current_turn)
            continue

        if role != "assistant":
            continue
        if current_turn is None:
            current_turn = session_template.ReadableTurn(user_text="")
            turns.append(current_turn)

        if text.strip():
            assistant_segments.append((completed, text.strip()))

        for raw_part in parts:
            part = get_object(raw_part)
            part_type = get_string(part.get("type"))
            if part_type == "tool":
                summarize_opencode_tool_part(part, activity)
                activity_time = created
            elif part_type == "reasoning":
                reasoning = get_string(part.get("text"))
                if reasoning:
                    current_turn.attachments.append(
                        session_template.ReadableAttachment(
                            title="Reasoning",
                            timestamp=created,
                            content=reasoning,
                        )
                    )

    finalize_current_turn()
    return session_template.render_readable_markdown(
        "OpenCode Session",
        readable_metadata_rows(session, options),
        turns,
        options.include_appendix,
    )


def render_markdown(session: dict[str, Any], options: RenderOptions) -> str:
    """Render a full OpenCode session to Markdown."""
    if not options.include_system and not options.include_usage:
        return render_readable_markdown(session, options)
    blocks = [render_session_meta(session, options)]
    messages = session.get("messages")
    if isinstance(messages, list):
        for message in messages:
            block = render_message(get_object(message), options)
            if block.strip():
                blocks.append(block.strip())
    return "\n\n---\n\n".join(blocks) + "\n"


def sanitize_filename(value: str) -> str:
    """Convert a session title into a filesystem-friendly filename stem."""
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
    return cleaned or "opencode-session"


def default_output_path(session: dict[str, Any]) -> Path:
    """Return a default Markdown path near the current working directory."""
    info = get_object(session.get("info"))
    stem = (
        get_string(info.get("title"))
        or get_string(info.get("id"))
        or "opencode-session"
    )
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


def load_input(args: argparse.Namespace) -> tuple[dict[str, Any], str]:
    """Load an OpenCode session from JSON export or SQLite."""
    input_value = args.input
    db_path = Path(args.db).expanduser().resolve()

    if input_value:
        candidate = Path(input_value).expanduser()
        if candidate.is_file() and candidate.suffix.lower() == ".json":
            return read_export_json(candidate.resolve()), str(candidate.resolve())
        if candidate.is_file() and candidate.name.endswith(".db"):
            db_path = candidate.resolve()
            with connect_db(db_path) as connection:
                session_id = args.session_id or find_latest_session_id(connection)
                return load_session_from_db(
                    connection, session_id
                ), f"{db_path}:{session_id}"
        if input_value.startswith("ses_") and not args.session_id:
            args.session_id = input_value

    with connect_db(db_path) as connection:
        session_id = args.session_id or find_latest_session_id(connection)
        return load_session_from_db(connection, session_id), f"{db_path}:{session_id}"


def build_parser() -> argparse.ArgumentParser:
    """Build the command line parser."""
    script_name = Path(__file__).name
    epilog = create_example_text(
        script_name,
        [
            (
                "Convert a JSON file from opencode export",
                "opencode-export.json -o session.md",
            ),
            ("Convert a local SQLite session by id", "ses_abc123 -o session.md"),
            ("Convert the latest local session", "--default-output"),
            ("Include reasoning, step records, and usage", "ses_abc123 --include-all"),
        ],
        notes=[
            "OpenCode 1.17.x stores sessions in ~/.local/share/opencode/opencode.db.",
            "The official CLI can export JSON with: opencode export <sessionID> --sanitize.",
            "This script reads only session, message, and part tables when using SQLite.",
        ],
    )
    parser = ColoredArgumentParser(
        description="Convert OpenCode exported JSON or local SQLite sessions into Markdown.",
        epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "input",
        nargs="?",
        help=CLIStyle.color(
            "OpenCode export JSON, opencode.db path, or session id. Defaults to latest local session.",
            CLIStyle.COLORS["CONTENT"],
        ),
    )
    parser.add_argument(
        "--db",
        default=str(DEFAULT_DB_PATH),
        help=CLIStyle.color(
            "Path to local OpenCode SQLite database.", CLIStyle.COLORS["CONTENT"]
        ),
    )
    parser.add_argument(
        "--session-id",
        help=CLIStyle.color(
            "OpenCode session id to read from SQLite.", CLIStyle.COLORS["CONTENT"]
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
            "Include reasoning, step-start records, and tool metadata.",
            CLIStyle.COLORS["CONTENT"],
        ),
    )
    parser.add_argument(
        "--include-usage",
        action="store_true",
        help=CLIStyle.color(
            "Include cost and token usage blocks when present.",
            CLIStyle.COLORS["CONTENT"],
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
    if args.max_output_chars < 0:
        raise ValueError("max-output-chars must be >= 0")
    session, source = load_input(args)
    debug("source", source=source)
    output_path = Path(args.output).expanduser().resolve() if args.output else None
    if output_path is None and args.default_output:
        output_path = default_output_path(session).resolve()
    options = RenderOptions(
        source=source,
        include_system=args.include_system or args.include_all,
        include_usage=args.include_usage or args.include_all,
        include_unknown=not args.no_unknown,
        include_appendix=not args.quiet,
        max_output_chars=args.max_output_chars,
    )
    write_output(output_path, render_markdown(session, options))
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
