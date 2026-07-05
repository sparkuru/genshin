#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Convert Codex JSONL session transcripts into readable Markdown."""

from __future__ import annotations

import argparse
import html
import json
import re
import shlex
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
        "INFO": 5,
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
        text: str = "",
        color: int = COLORS["CONTENT"],
        error: bool = False,
        end: str = "\n",
    ) -> None:
        """Write styled terminal output."""
        stream = sys.stderr if error else sys.stdout
        stream.write(f"{CLIStyle.color(text, color)}{end}")
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
class ExportPlanTurn:
    """One curated QA turn summary from an agent export plan."""

    index: int
    export: str
    heading: str
    question: str
    answer: str
    note: str


@dataclass(frozen=True)
class ExportPlan:
    """Structured export plan authored by the agent before rendering."""

    title: str
    turn_table_title: str
    include_turn_table: bool
    include_turn_headings: bool
    turns: tuple[ExportPlanTurn, ...]


@dataclass(frozen=True)
class RenderOptions:
    """Markdown rendering options."""

    input_path: Path
    session_name: str
    document_title: str
    title_source: str
    include_system: bool
    include_usage: bool
    include_unknown: bool
    include_appendix: bool
    raw_tool_output: bool
    max_output_chars: int
    excluded_items: frozenset[str]
    excluded_turns: tuple[int, ...]
    export_plan: ExportPlan | None
    turn_table: str
    qa_summary: str


@dataclass(frozen=True)
class RenderContext:
    """Indexes built from the transcript before rendering."""

    event_by_call_id: dict[str, dict[str, Any]]
    has_visible_event_messages: bool


@dataclass(frozen=True)
class OutputVariant:
    """One Markdown output variant."""

    suffix: str
    include_system: bool
    include_usage: bool


ActivityLog = session_template.ActivityLog
ReadableAttachment = session_template.ReadableAttachment
ReadableTurn = session_template.ReadableTurn


def debug(
    *args: Any, file: str | None = None, append: bool = True, **kwargs: Any
) -> None:
    """
    Print debug details with optional file output.
    ```python
    debug("message", key="value")

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


def build_render_context(records: list[JsonLineRecord]) -> RenderContext:
    """Build lookup tables for records that reference the same call id."""
    event_by_call_id: dict[str, dict[str, Any]] = {}
    has_visible_event_messages = False
    for record in records:
        payload = get_object(record.data.get("payload"))
        payload_type = get_string(payload.get("type"))
        call_id = payload.get("call_id")
        if isinstance(call_id, str) and record.data.get("type") == "event_msg":
            event_by_call_id[call_id] = payload
        if payload_type in ("user_message", "agent_message"):
            has_visible_event_messages = True
    return RenderContext(
        event_by_call_id=event_by_call_id,
        has_visible_event_messages=has_visible_event_messages,
    )


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


def is_excluded(options: RenderOptions, *items: str) -> bool:
    """Return whether any item category is excluded."""
    return any(item in options.excluded_items for item in items)


def include_appendix_enabled(options: RenderOptions) -> bool:
    """Return whether readable appendix blocks should be rendered."""
    return options.include_appendix and not is_excluded(options, "appendix")


def get_exclude_item_choices() -> frozenset[str]:
    """Return supported item categories for content exclusion."""
    return frozenset(
        {
            "appendix",
            "assistant",
            "commands",
            "edits",
            "errors",
            "file-changes",
            "lifecycle",
            "metadata",
            "operations",
            "plan-updates",
            "reasoning",
            "searches",
            "system",
            "tool-calls",
            "tool-outputs",
            "tools",
            "unknown",
            "usage",
            "user",
        }
    )


def get_exclude_item_aliases() -> dict[str, str]:
    """Return accepted aliases for exclude item categories."""
    return {
        "files": "file-changes",
        "file-change": "file-changes",
        "plans": "plan-updates",
        "plan": "plan-updates",
        "search": "searches",
        "web-search": "searches",
        "web-searches": "searches",
        "tool-call": "tool-calls",
        "tool-output": "tool-outputs",
    }


def parse_excluded_items(raw_values: list[str] | None) -> frozenset[str]:
    """Parse repeated or comma-separated exclude item names."""
    if not raw_values:
        return frozenset()

    choices = get_exclude_item_choices()
    aliases = get_exclude_item_aliases()
    parsed: set[str] = set()
    for raw_value in raw_values:
        for raw_item in raw_value.split(","):
            item = raw_item.strip().lower().replace("_", "-")
            if not item:
                continue
            item = aliases.get(item, item)
            if item not in choices:
                allowed = ", ".join(sorted(choices))
                raise ValueError(
                    f"unknown exclude item '{raw_item}'; allowed: {allowed}"
                )
            parsed.add(item)
    if "operations" in parsed:
        parsed.update({"commands", "edits", "searches", "tools"})
    return frozenset(parsed)


def parse_excluded_turns(raw_values: list[str] | None) -> tuple[int, ...]:
    """Parse repeated or comma-separated QA turn selectors."""
    if not raw_values:
        return ()

    selectors: list[int] = []
    for raw_value in raw_values:
        for raw_item in raw_value.split(","):
            item = raw_item.strip().lower()
            if not item:
                continue
            if item in ("last", "final"):
                selector = -1
            else:
                try:
                    selector = int(item)
                except ValueError as exc:
                    raise ValueError(
                        f"invalid turn selector '{raw_item}'; use 1, 2, -1, or last"
                    ) from exc
            if selector == 0:
                raise ValueError("turn selector must not be 0")
            if selector not in selectors:
                selectors.append(selector)
    return tuple(selectors)


def read_optional_text_file(path_text: str, label: str) -> str:
    """Read an optional UTF-8 text file argument."""
    if not path_text:
        return ""
    path = Path(path_text).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"{label} file not found: {path}")
    return path.read_text(encoding="utf-8").strip()


def read_export_plan(path_text: str) -> ExportPlan | None:
    """Read an optional structured export plan JSON file."""
    if not path_text:
        return None
    path = Path(path_text).expanduser().resolve()
    if not path.is_file():
        raise FileNotFoundError(f"export plan file not found: {path}")
    with open(path, "r", encoding="utf-8") as file_handle:
        data = json.load(file_handle)
    if not isinstance(data, dict):
        raise ValueError("export plan must be a JSON object")
    return parse_export_plan(data)


def parse_export_plan(data: dict[str, Any]) -> ExportPlan:
    """Parse a structured export plan JSON object."""
    raw_turns = data.get("turns")
    if not isinstance(raw_turns, list):
        raise ValueError("export plan field 'turns' must be an array")
    turns = tuple(
        parse_export_plan_turn(item, index)
        for index, item in enumerate(raw_turns, start=1)
    )
    return ExportPlan(
        title=get_string(data.get("title")),
        turn_table_title=get_string(data.get("turn_table_title")) or "Turn Index",
        include_turn_table=get_bool(data.get("include_turn_table"), True),
        include_turn_headings=get_bool(data.get("include_turn_headings"), True),
        turns=turns,
    )


def parse_export_plan_turn(data: Any, fallback_index: int) -> ExportPlanTurn:
    """Parse one turn entry from a structured export plan."""
    if not isinstance(data, dict):
        raise ValueError("export plan turn entries must be JSON objects")
    raw_index = data.get("index", fallback_index)
    if not isinstance(raw_index, int) or raw_index <= 0:
        raise ValueError("export plan turn field 'index' must be a positive integer")
    export = get_string(data.get("export")) or "keep"
    heading = get_string(data.get("heading")) or get_string(data.get("q"))
    return ExportPlanTurn(
        index=raw_index,
        export=export,
        heading=heading,
        question=get_string(data.get("q")) or get_string(data.get("question")),
        answer=get_string(data.get("a")) or get_string(data.get("answer")),
        note=get_string(data.get("note")),
    )


def get_bool(value: Any, default: bool) -> bool:
    """Return value if it is a boolean, otherwise a default."""
    if isinstance(value, bool):
        return value
    return default


def resolve_excluded_turn_indexes(
    selectors: tuple[int, ...], turn_count: int
) -> frozenset[int]:
    """Resolve 1-based and negative QA turn selectors against a turn count."""
    excluded: set[int] = set()
    for selector in selectors:
        if selector > 0:
            turn_index = selector
        else:
            turn_index = turn_count + selector + 1
        if turn_index < 1 or turn_index > turn_count:
            raise ValueError(
                f"turn selector {selector} is out of range for {turn_count} turns"
            )
        excluded.add(turn_index)
    return frozenset(excluded)


def truncate_text(text: str, limit: int) -> str:
    """Truncate text to a positive character limit."""
    if limit <= 0 or len(text) <= limit:
        return text
    omitted = len(text) - limit
    return f"{text[:limit]}\n\n[truncated {omitted} characters]"


def json_dumps(value: Any) -> str:
    """Dump JSON for Markdown display."""
    return json.dumps(value, ensure_ascii=False, indent=2)


def parse_json_string(value: Any) -> Any:
    """Parse a JSON string when possible."""
    if not isinstance(value, str):
        return value
    try:
        return json.loads(value)
    except json.JSONDecodeError:
        return value


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
    language_suffix = language if language else ""
    return f"{fence}{language_suffix}\n{text}\n{fence}"


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


def content_text(content: Any) -> str:
    """Extract text from Codex message content arrays."""
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
        text = get_string(item_object.get("text"))
        if text:
            parts.append(text)
    return "\n\n".join(parts)


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


def render_message(role: str, text: str, phase: str = "") -> str:
    """Render one user or assistant message."""
    if not text.strip():
        return ""
    title = role.capitalize()
    if phase:
        title = f"{title} ({phase})"
    return "\n\n".join([render_heading(2, title), text.strip()])


def render_session_meta(record: dict[str, Any], options: RenderOptions) -> str:
    """Render internal session metadata."""
    if is_excluded(options, "metadata"):
        return render_heading(1, options.document_title)

    payload = get_object(record.get("payload"))
    rows = [
        ("source file", options.input_path),
        ("session id", payload.get("id")),
        ("session name", options.session_name),
        ("title source", options.title_source),
        ("timestamp", payload.get("timestamp") or record.get("timestamp")),
        ("cwd", payload.get("cwd")),
        ("source", payload.get("source")),
        ("originator", payload.get("originator")),
        ("cli version", payload.get("cli_version")),
        ("model provider", payload.get("model_provider")),
    ]
    return "\n\n".join(
        [render_heading(1, options.document_title), render_metadata_table(rows)]
    )


def render_turn_context(record: dict[str, Any], options: RenderOptions) -> str:
    """Render turn context when requested."""
    if not options.include_system or is_excluded(options, "system"):
        return ""

    payload = get_object(record.get("payload"))
    rows = [
        ("turn id", payload.get("turn_id")),
        ("cwd", payload.get("cwd")),
        ("date", payload.get("current_date")),
        ("timezone", payload.get("timezone")),
        ("approval", payload.get("approval_policy")),
        ("model", payload.get("model")),
        ("effort", payload.get("effort")),
    ]
    return "\n\n".join([render_heading(3, "Turn context"), render_metadata_table(rows)])


def render_internal_message(
    payload: dict[str, Any], context: RenderContext, options: RenderOptions
) -> str:
    """Render an internal response_item message."""
    role = get_string(payload.get("role"))
    if role in ("system", "developer") and not options.include_system:
        return ""
    if role in ("system", "developer") and is_excluded(options, "system"):
        return ""
    if role == "user" and is_excluded(options, "user"):
        return ""
    if role == "assistant" and is_excluded(options, "assistant"):
        return ""
    if role in ("user", "assistant") and context.has_visible_event_messages:
        return ""

    text = content_text(payload.get("content"))
    return render_message(role or "message", text, get_string(payload.get("phase")))


def render_reasoning(payload: dict[str, Any], options: RenderOptions) -> str:
    """Render reasoning summaries when present."""
    if is_excluded(options, "reasoning", "appendix"):
        return ""

    summary = payload.get("summary")
    text = content_text(summary)
    if not text:
        text = content_text(payload.get("content"))
    if not text:
        return ""
    return "\n\n".join([render_heading(3, "Reasoning"), text.strip()])


def render_function_call(payload: dict[str, Any], options: RenderOptions) -> str:
    """Render a model tool call."""
    name = get_string(payload.get("name")) or "tool"
    if name == "exec_command" and is_excluded(options, "commands", "appendix"):
        return ""
    if name in ("apply_patch", "apply_patch_tool") and is_excluded(
        options, "edits", "file-changes", "appendix"
    ):
        return ""
    if is_excluded(options, "tool-calls", "tools", "appendix"):
        return ""

    call_id = get_string(payload.get("call_id"))
    arguments = parse_json_string(payload.get("arguments"))
    rows = [("call id", call_id)]
    body = [render_heading(3, f"Tool call: {name}")]
    table = render_metadata_table(rows)
    if table:
        body.append(table)
    if arguments != "":
        body.append(code_fence(json_dumps(arguments), "json"))
    return "\n\n".join(body)


def render_function_output(
    payload: dict[str, Any], context: RenderContext, options: RenderOptions
) -> str:
    """Render raw function output when no richer event exists."""
    if is_excluded(options, "tool-outputs", "tools", "appendix"):
        return ""

    call_id = get_string(payload.get("call_id"))
    if call_id in context.event_by_call_id and not options.raw_tool_output:
        return ""

    output = get_string(payload.get("output"))
    parsed_output = parse_json_string(output)
    body = [render_heading(3, "Tool output")]
    table = render_metadata_table([("call id", call_id)])
    if table:
        body.append(table)
    if isinstance(parsed_output, (dict, list)):
        body.append(code_fence(json_dumps(parsed_output), "json"))
    elif output:
        body.append(code_fence(truncate_text(output, options.max_output_chars), "text"))
    return "\n\n".join(body)


def render_exec_result(payload: dict[str, Any], options: RenderOptions) -> str:
    """Render a shell or exec command result."""
    if is_excluded(options, "commands", "appendix"):
        return ""

    command = payload.get("command")
    if isinstance(command, list):
        command_text = shlex.join(str(part) for part in command)
    else:
        command_text = get_string(command)

    rows = [
        ("call id", payload.get("call_id")),
        ("cwd", payload.get("cwd")),
        ("status", payload.get("status")),
        ("exit code", payload.get("exit_code")),
    ]
    body = [render_heading(3, "Command result"), render_metadata_table(rows)]
    if command_text:
        body.append(code_fence(command_text, "bash"))

    stdout = get_string(payload.get("stdout"))
    stderr = get_string(payload.get("stderr"))
    aggregate = get_string(payload.get("aggregated_output"))
    formatted = get_string(payload.get("formatted_output"))

    if stdout:
        body.append(render_heading(4, "stdout"))
        body.append(code_fence(truncate_text(stdout, options.max_output_chars), "text"))
    if stderr:
        body.append(render_heading(4, "stderr"))
        body.append(code_fence(truncate_text(stderr, options.max_output_chars), "text"))
    if not stdout and not stderr and aggregate:
        body.append(
            code_fence(truncate_text(aggregate, options.max_output_chars), "text")
        )
    if not stdout and not stderr and not aggregate and formatted:
        body.append(
            code_fence(truncate_text(formatted, options.max_output_chars), "text")
        )
    return "\n\n".join(part for part in body if part)


def render_token_count(payload: dict[str, Any], options: RenderOptions) -> str:
    """Render token usage if requested."""
    if not options.include_usage or is_excluded(options, "usage"):
        return ""
    info = get_object(payload.get("info"))
    usage = get_object(info.get("total_token_usage") or info.get("last_token_usage"))
    if not usage:
        return ""
    rows = [(key.replace("_", " "), value) for key, value in usage.items()]
    return "\n\n".join([render_heading(3, "Token usage"), render_metadata_table(rows)])


def render_task_marker(payload: dict[str, Any], options: RenderOptions) -> str:
    """Render task lifecycle events."""
    if is_excluded(options, "lifecycle", "appendix"):
        return ""

    event_type = get_string(payload.get("type"))
    if event_type == "task_started":
        rows = [
            ("turn id", payload.get("turn_id")),
            ("started at", payload.get("started_at")),
            ("context window", payload.get("model_context_window")),
            ("mode", payload.get("collaboration_mode_kind")),
        ]
        return "\n\n".join(
            [render_heading(3, "Turn started"), render_metadata_table(rows)]
        )
    if event_type == "task_complete":
        rows = [
            ("turn id", payload.get("turn_id")),
            ("completed at", payload.get("completed_at")),
            ("duration ms", payload.get("duration_ms")),
        ]
        return "\n\n".join(
            [render_heading(3, "Turn completed"), render_metadata_table(rows)]
        )
    if event_type == "turn_aborted":
        return render_heading(3, "Turn aborted")
    return ""


def render_event_message(payload: dict[str, Any], options: RenderOptions) -> str:
    """Render internal event_msg records."""
    event_type = get_string(payload.get("type"))
    if event_type == "user_message":
        if is_excluded(options, "user"):
            return ""
        return render_message("user", get_string(payload.get("message")))
    if event_type == "agent_message":
        if is_excluded(options, "assistant"):
            return ""
        return render_message(
            "assistant",
            get_string(payload.get("message")),
            get_string(payload.get("phase")),
        )
    if event_type == "exec_command_end":
        return render_exec_result(payload, options)
    if event_type == "patch_apply_end":
        return render_patch_event(payload, options)
    if event_type == "web_search_end":
        return render_web_search_event(payload, options)
    if event_type == "token_count":
        return render_token_count(payload, options)
    if event_type in ("task_started", "task_complete", "turn_aborted"):
        return render_task_marker(payload, options)
    if event_type in ("thread_name_updated",):
        return ""
    if event_type == "error":
        if is_excluded(options, "errors"):
            return ""
        return render_error(payload)
    if options.include_unknown:
        if is_excluded(options, "unknown", "appendix"):
            return ""
        return details_block(f"event: {event_type or 'unknown'}", payload)
    return ""


def render_patch_event(payload: dict[str, Any], options: RenderOptions) -> str:
    """Render apply patch events."""
    if is_excluded(options, "edits", "file-changes", "appendix"):
        return ""

    rows = [
        ("call id", payload.get("call_id")),
        ("status", payload.get("status")),
        ("exit code", payload.get("exit_code")),
    ]
    body = [render_heading(3, "Patch result"), render_metadata_table(rows)]
    output = (
        get_string(payload.get("stdout"))
        or get_string(payload.get("stderr"))
        or get_string(payload.get("aggregated_output"))
    )
    if output:
        body.append(code_fence(truncate_text(output, options.max_output_chars), "text"))
    return "\n\n".join(part for part in body if part)


def render_web_search_event(payload: dict[str, Any], options: RenderOptions) -> str:
    """Render web search result events."""
    if is_excluded(options, "searches", "appendix"):
        return ""

    rows = [
        ("call id", payload.get("call_id")),
        ("query", payload.get("query")),
        ("status", payload.get("status")),
    ]
    body = [render_heading(3, "Web search"), render_metadata_table(rows)]
    output = get_string(payload.get("output")) or get_string(payload.get("result"))
    if output:
        body.append(code_fence(truncate_text(output, options.max_output_chars), "text"))
    return "\n\n".join(part for part in body if part)


def render_error(payload: dict[str, Any]) -> str:
    """Render error records."""
    message = get_string(payload.get("message")) or get_string(payload.get("error"))
    if not message:
        message = json_dumps(payload)
    return "\n\n".join([render_heading(3, "Error"), code_fence(message, "text")])


def render_response_item(
    payload: dict[str, Any], context: RenderContext, options: RenderOptions
) -> str:
    """Render internal response_item records."""
    item_type = get_string(payload.get("type"))
    if item_type == "message":
        return render_internal_message(payload, context, options)
    if item_type == "reasoning":
        return render_reasoning(payload, options)
    if item_type in ("function_call", "custom_tool_call"):
        return render_function_call(payload, options)
    if item_type in ("function_call_output", "custom_tool_call_output"):
        return render_function_output(payload, context, options)
    if item_type in ("web_search", "web_search_call"):
        if is_excluded(options, "searches", "appendix"):
            return ""
        return render_public_web_search(payload)
    if options.include_unknown:
        if is_excluded(options, "unknown", "appendix"):
            return ""
        return details_block(f"response item: {item_type or 'unknown'}", payload)
    return ""


def render_public_lifecycle(record: dict[str, Any], options: RenderOptions) -> str:
    """Render documented codex exec --json lifecycle events."""
    event_type = get_string(record.get("type"))
    if event_type == "thread.started":
        if is_excluded(options, "metadata"):
            return render_heading(1, options.document_title)

        rows = [
            ("source file", options.input_path),
            ("thread id", record.get("thread_id")),
            ("session name", options.session_name),
            ("title source", options.title_source),
        ]
        return "\n\n".join(
            [render_heading(1, options.document_title), render_metadata_table(rows)]
        )
    if event_type == "turn.started":
        if is_excluded(options, "lifecycle", "appendix"):
            return ""
        return render_heading(3, "Turn started")
    if event_type == "turn.completed":
        if is_excluded(options, "lifecycle", "appendix"):
            return ""
        usage = get_object(record.get("usage"))
        rows = [(key.replace("_", " "), value) for key, value in usage.items()]
        body = [render_heading(3, "Turn completed")]
        if options.include_usage and rows:
            body.append(render_metadata_table(rows))
        return "\n\n".join(body)
    if event_type == "turn.failed":
        if is_excluded(options, "errors"):
            return ""
        return "\n\n".join(
            [render_heading(3, "Turn failed"), details_block("details", record)]
        )
    if event_type == "error":
        if is_excluded(options, "errors"):
            return ""
        return render_error(record)
    return ""


def render_public_item(payload: dict[str, Any], options: RenderOptions) -> str:
    """Render documented codex exec --json item payloads."""
    item_type = get_string(payload.get("type"))
    if item_type == "agent_message":
        if is_excluded(options, "assistant"):
            return ""
        return render_message("assistant", get_string(payload.get("text")))
    if item_type == "reasoning":
        return render_reasoning(payload, options)
    if item_type == "command_execution":
        return render_public_command(payload, options)
    if item_type == "file_change":
        return render_public_file_change(payload, options)
    if item_type in ("mcp_tool_call", "tool_call"):
        return render_public_tool_call(payload, options)
    if item_type == "web_search":
        if is_excluded(options, "searches", "appendix"):
            return ""
        return render_public_web_search(payload)
    if item_type == "plan_update":
        return render_public_plan_update(payload, options)
    if options.include_unknown:
        if is_excluded(options, "unknown", "appendix"):
            return ""
        return details_block(f"item: {item_type or 'unknown'}", payload)
    return ""


def render_public_command(payload: dict[str, Any], options: RenderOptions) -> str:
    """Render public JSONL command execution items."""
    if is_excluded(options, "commands", "appendix"):
        return ""

    rows = [
        ("id", payload.get("id")),
        ("status", payload.get("status")),
        ("exit code", payload.get("exit_code")),
    ]
    body = [render_heading(3, "Command execution"), render_metadata_table(rows)]
    command = get_string(payload.get("command"))
    if command:
        body.append(code_fence(command, "bash"))
    output = get_string(payload.get("output")) or get_string(payload.get("text"))
    if output:
        body.append(code_fence(truncate_text(output, options.max_output_chars), "text"))
    return "\n\n".join(part for part in body if part)


def render_public_file_change(payload: dict[str, Any], options: RenderOptions) -> str:
    """Render public JSONL file change items."""
    if is_excluded(options, "edits", "file-changes", "appendix"):
        return ""

    rows = [
        ("id", payload.get("id")),
        ("status", payload.get("status")),
        ("path", payload.get("path") or payload.get("file")),
    ]
    body = [render_heading(3, "File change"), render_metadata_table(rows)]
    diff = get_string(payload.get("diff")) or get_string(payload.get("patch"))
    if diff:
        body.append(code_fence(diff, "diff"))
    return "\n\n".join(part for part in body if part)


def render_public_tool_call(payload: dict[str, Any], options: RenderOptions) -> str:
    """Render public JSONL MCP or generic tool call items."""
    if is_excluded(options, "tool-calls", "tools", "appendix"):
        return ""

    name = get_string(payload.get("name")) or get_string(payload.get("tool")) or "tool"
    rows = [
        ("id", payload.get("id")),
        ("status", payload.get("status")),
        ("server", payload.get("server")),
    ]
    body = [render_heading(3, f"Tool call: {name}"), render_metadata_table(rows)]
    arguments = payload.get("arguments") or payload.get("input")
    if arguments not in ("", None):
        body.append(code_fence(json_dumps(parse_json_string(arguments)), "json"))
    output = get_string(payload.get("output")) or get_string(payload.get("result"))
    if output:
        body.append(code_fence(output, "text"))
    return "\n\n".join(part for part in body if part)


def render_public_web_search(payload: dict[str, Any]) -> str:
    """Render public JSONL web search items."""
    rows = [
        ("id", payload.get("id")),
        ("status", payload.get("status")),
        ("query", payload.get("query")),
    ]
    return "\n\n".join([render_heading(3, "Web search"), render_metadata_table(rows)])


def render_public_plan_update(payload: dict[str, Any], options: RenderOptions) -> str:
    """Render public JSONL plan update items."""
    if is_excluded(options, "plan-updates", "appendix"):
        return ""

    plan = payload.get("plan")
    body = [render_heading(3, "Plan update")]
    if isinstance(plan, list):
        for item in plan:
            item_object = get_object(item)
            step = get_string(item_object.get("step"))
            status = get_string(item_object.get("status"))
            if step:
                body.append(f"- `{status or 'pending'}` {step}")
        return "\n".join(body)
    return "\n\n".join([body[0], details_block("plan", payload)])


def find_session_meta_record(records: list[JsonLineRecord]) -> dict[str, Any]:
    """Find the first session metadata record."""
    for record in records:
        if record.data.get("type") == "session_meta":
            return record.data
    return {}


def readable_metadata_rows(
    records: list[JsonLineRecord], options: RenderOptions
) -> list[tuple[str, Any]]:
    """Build concise metadata rows for the default readable export."""
    if is_excluded(options, "metadata"):
        return []

    record = find_session_meta_record(records)
    payload = get_object(record.get("payload"))

    return [
        ("source file", options.input_path),
        ("session id", payload.get("id") or find_session_id(records)),
        ("session name", options.session_name),
        ("title source", options.title_source),
        ("cwd", payload.get("cwd")),
        ("model", payload.get("model")),
        ("approval policy", payload.get("approval_policy")),
        ("sandbox", payload.get("sandbox_policy")),
        ("git branch", payload.get("git_branch")),
        ("timestamp", session_template.format_timestamp(record.get("timestamp"))),
    ]


def create_readable_turn(user_text: str, timestamp: str) -> ReadableTurn:
    """Create a readable QA turn from a user message."""
    return session_template.ReadableTurn(
        user_text=user_text,
        user_time=timestamp,
        assistant_text="",
        assistant_time="",
        attachments=[],
    )


def append_user_follow_up(turn: ReadableTurn, user_text: str) -> None:
    """Append a user follow-up to an unfinished readable turn."""
    text = user_text.strip()
    if not text:
        return
    if turn.user_text.strip():
        turn.user_text = f"{turn.user_text.strip()}\n\nFollow-up: {text}"
        return
    turn.user_text = text


def flush_activity_to_turn(turn: ReadableTurn | None, activity: ActivityLog) -> None:
    """Render pending activity with the shared template and clear it."""
    session_template.flush_activity_to_turn(turn, activity)
    activity.searches.clear()
    activity.commands.clear()
    activity.edits.clear()
    activity.tools.clear()
    activity.notes.clear()


def collect_search_activity(
    payload: dict[str, Any], activity: ActivityLog, options: RenderOptions
) -> None:
    """Collect web search activity without rendering raw tool events."""
    if is_excluded(options, "searches", "operations", "appendix"):
        return

    query = get_string(payload.get("query"))
    action = get_object(payload.get("action"))
    if not query:
        query = get_string(action.get("query"))
    if query:
        session_template.append_unique(activity.searches, query, limit=140)
        return
    queries = action.get("queries")
    if isinstance(queries, list):
        for item in queries:
            if isinstance(item, str):
                session_template.append_unique(activity.searches, item, limit=140)


def collect_function_call_activity(
    payload: dict[str, Any], activity: ActivityLog, options: RenderOptions
) -> None:
    """Collect model tool-call activity for readable export."""
    name = get_string(payload.get("name")) or "tool"
    arguments = parse_json_string(payload.get("arguments"))
    argument_object = get_object(arguments)
    if name == "exec_command":
        if is_excluded(options, "commands", "operations", "appendix"):
            return
        command = get_string(argument_object.get("cmd"))
        if command:
            session_template.append_unique(activity.commands, command, limit=140)
            return
    if name in ("apply_patch", "apply_patch_tool"):
        if is_excluded(options, "edits", "operations", "appendix"):
            return
        session_template.append_unique(activity.edits, "Applied a patch", limit=140)
        return
    if is_excluded(options, "tools", "tool-calls", "operations", "appendix"):
        return
    session_template.append_unique(activity.tools, name, limit=120)


def collect_event_activity(
    payload: dict[str, Any], activity: ActivityLog, options: RenderOptions
) -> None:
    """Collect event-message activity for readable export."""
    event_type = get_string(payload.get("type"))
    if event_type == "web_search_end":
        collect_search_activity(payload, activity, options)
        return
    if event_type == "exec_command_end":
        if is_excluded(options, "commands", "operations", "appendix"):
            return
        command = payload.get("command")
        if isinstance(command, list):
            command_text = shlex.join(str(part) for part in command)
        else:
            command_text = get_string(command)
        if command_text:
            session_template.append_unique(activity.commands, command_text, limit=140)
        return
    if event_type == "patch_apply_end":
        if is_excluded(options, "edits", "file-changes", "operations", "appendix"):
            return
        output = (
            get_string(payload.get("stdout"))
            or get_string(payload.get("stderr"))
            or get_string(payload.get("aggregated_output"))
        )
        session_template.append_unique(
            activity.edits, output or "Applied a patch", limit=140
        )


def collect_public_item_activity(
    payload: dict[str, Any], activity: ActivityLog, options: RenderOptions
) -> None:
    """Collect documented codex exec --json item activity for readable export."""
    item_type = get_string(payload.get("type"))
    if item_type == "command_execution":
        if is_excluded(options, "commands", "operations", "appendix"):
            return
        command = get_string(payload.get("command"))
        if command:
            session_template.append_unique(activity.commands, command, limit=140)
        return
    if item_type == "file_change":
        if is_excluded(options, "edits", "file-changes", "operations", "appendix"):
            return
        path = get_string(payload.get("path")) or get_string(payload.get("file"))
        status = get_string(payload.get("status"))
        label = f"{status} {path}".strip()
        session_template.append_unique(
            activity.edits, label or "Changed files", limit=140
        )
        return
    if item_type in ("mcp_tool_call", "tool_call"):
        if is_excluded(options, "tools", "tool-calls", "operations", "appendix"):
            return
        name = (
            get_string(payload.get("name")) or get_string(payload.get("tool")) or "tool"
        )
        session_template.append_unique(activity.tools, name, limit=120)
        return
    if item_type == "web_search":
        collect_search_activity(payload, activity, options)


def render_readable_record(
    record: JsonLineRecord,
    context: RenderContext,
    options: RenderOptions,
    activity: ActivityLog,
    turns: list[ReadableTurn],
) -> ReadableTurn | None:
    """Render or collect one record for the default readable export."""
    data = record.data
    record_type = get_string(data.get("type"))
    payload = get_object(data.get("payload"))
    payload_type = get_string(payload.get("type"))
    current_turn = turns[-1] if turns else None

    if record_type == "event_msg" and payload_type == "user_message":
        flush_activity_to_turn(current_turn, activity)
        if is_excluded(options, "user"):
            turn = create_readable_turn("", "")
            turns.append(turn)
            return turn
        if current_turn is not None and not current_turn.assistant_text.strip():
            append_user_follow_up(current_turn, get_string(payload.get("message")))
            if not current_turn.user_time:
                current_turn.user_time = get_string(data.get("timestamp"))
            return current_turn
        turn = create_readable_turn(
            get_string(payload.get("message")),
            get_string(data.get("timestamp")),
        )
        turns.append(turn)
        return turn
    if record_type == "event_msg" and payload_type == "agent_message":
        flush_activity_to_turn(current_turn, activity)
        if is_excluded(options, "assistant"):
            return current_turn
        message = get_string(payload.get("message"))
        phase = get_string(payload.get("phase"))
        if current_turn is None:
            current_turn = create_readable_turn("", "")
            turns.append(current_turn)
        if phase == "final_answer" or not phase:
            if current_turn.assistant_text:
                current_turn.assistant_text += "\n\n" + message
            else:
                current_turn.assistant_text = message
            current_turn.assistant_time = get_string(data.get("timestamp"))
            return current_turn
        current_turn.attachments.append(
            ReadableAttachment(
                title=f"Assistant {phase}",
                timestamp=get_string(data.get("timestamp")),
                content=message,
            )
        )
        return current_turn
    if record_type == "response_item" and payload_type == "message":
        block = render_internal_message(payload, context, options)
        if block:
            flush_activity_to_turn(current_turn, activity)
            if current_turn is None:
                current_turn = create_readable_turn("", "")
                turns.append(current_turn)
            role = get_string(payload.get("role")) or "message"
            if role == "assistant":
                text = content_text(payload.get("content"))
                current_turn.assistant_text = (
                    f"{current_turn.assistant_text}\n\n{text}".strip()
                )
                current_turn.assistant_time = get_string(data.get("timestamp"))
            else:
                current_turn.attachments.append(
                    ReadableAttachment(
                        title=role.capitalize(),
                        timestamp=get_string(data.get("timestamp")),
                        content=block,
                    )
                )
        return current_turn
    if record_type == "response_item" and payload_type == "reasoning":
        block = render_reasoning(payload, options)
        if block:
            flush_activity_to_turn(current_turn, activity)
            if current_turn is None:
                current_turn = create_readable_turn("", "")
                turns.append(current_turn)
            current_turn.attachments.append(
                ReadableAttachment(
                    title="Reasoning",
                    timestamp=get_string(data.get("timestamp")),
                    content=block,
                )
            )
        return current_turn
    if record_type == "response_item" and payload_type in (
        "function_call",
        "custom_tool_call",
    ):
        collect_function_call_activity(payload, activity, options)
        return current_turn
    if record_type == "response_item" and payload_type in (
        "web_search",
        "web_search_call",
    ):
        collect_search_activity(payload, activity, options)
        return current_turn
    if record_type == "event_msg":
        if payload_type == "thread_rolled_back":
            rollback_count = payload.get("num_turns")
            if isinstance(rollback_count, int):
                for _ in range(min(rollback_count, len(turns))):
                    turns.pop()
            activity.searches.clear()
            activity.commands.clear()
            activity.tools.clear()
            activity.edits.clear()
            activity.notes.clear()
            return turns[-1] if turns else None
        collect_event_activity(payload, activity, options)
        return current_turn
    if record_type.startswith("item."):
        item = get_object(data.get("item"))
        item_type = get_string(item.get("type"))
        if item_type == "agent_message":
            flush_activity_to_turn(current_turn, activity)
            if is_excluded(options, "assistant"):
                return current_turn
            if current_turn is None:
                current_turn = create_readable_turn("", "")
                turns.append(current_turn)
            text = get_string(item.get("text"))
            current_turn.assistant_text = (
                f"{current_turn.assistant_text}\n\n{text}".strip()
            )
            current_turn.assistant_time = get_string(data.get("timestamp"))
            return current_turn
        if item_type == "reasoning":
            block = render_reasoning(item, options)
            if block:
                flush_activity_to_turn(current_turn, activity)
                if current_turn is None:
                    current_turn = create_readable_turn("", "")
                    turns.append(current_turn)
                current_turn.attachments.append(
                    ReadableAttachment(
                        title="Reasoning",
                        timestamp=get_string(data.get("timestamp")),
                        content=block,
                    )
                )
            return current_turn
        collect_public_item_activity(item, activity, options)
        return current_turn
    return current_turn


def trim_incomplete_trailing_turns(
    turns: list[ReadableTurn], options: RenderOptions
) -> list[ReadableTurn]:
    """Drop a final user-only turn from readable QA output."""
    if not turns or is_excluded(options, "assistant"):
        return turns
    last_turn = turns[-1]
    if last_turn.user_text.strip() and not last_turn.assistant_text.strip():
        return turns[:-1]
    return turns


def render_export_plan_table(plan: ExportPlan | None) -> str:
    """Render a structured export plan as a Markdown turn index table."""
    if plan is None or not plan.include_turn_table or not plan.turns:
        return ""
    lines = [
        session_template.render_heading(2, plan.turn_table_title),
        "",
        "| # | Export | Q | A | Note |",
        "| --- | --- | --- | --- | --- |",
    ]
    for turn in plan.turns:
        lines.append(
            " | ".join(
                [
                    f"| {turn.index}",
                    session_template.markdown_escape(turn.export),
                    session_template.markdown_escape(turn.question),
                    session_template.markdown_escape(turn.answer),
                    f"{session_template.markdown_escape(turn.note)} |",
                ]
            )
        )
    return "\n".join(lines)


def build_export_plan_heading_map(plan: ExportPlan | None) -> dict[int, str]:
    """Build readable turn headings keyed by original turn index."""
    if plan is None or not plan.include_turn_headings:
        return {}
    headings: dict[int, str] = {}
    for turn in plan.turns:
        if turn.export.lower() == "exclude":
            continue
        heading = turn.heading.strip()
        if heading:
            headings[turn.index] = f"{turn.index}. {heading}"
    return headings


def render_readable_markdown(
    records: list[JsonLineRecord], options: RenderOptions
) -> str:
    """Render a low-noise Markdown transcript for human reading."""
    context = build_render_context(records)
    activity = session_template.create_activity_log()
    turns: list[ReadableTurn] = []
    for record in records:
        render_readable_record(record, context, options, activity, turns)
    flush_activity_to_turn(turns[-1] if turns else None, activity)
    turns = trim_incomplete_trailing_turns(turns, options)
    indexed_turns = list(enumerate(turns, start=1))
    if options.excluded_turns:
        excluded_indexes = resolve_excluded_turn_indexes(
            options.excluded_turns, len(turns)
        )
        indexed_turns = [
            (index, turn)
            for index, turn in indexed_turns
            if index not in excluded_indexes
        ]
    turns = [turn for _, turn in indexed_turns]
    heading_map = build_export_plan_heading_map(options.export_plan)
    turn_headings = [heading_map.get(index, "") for index, _ in indexed_turns]
    turn_table = options.turn_table or render_export_plan_table(options.export_plan)
    return session_template.render_readable_markdown(
        title=options.document_title,
        metadata_rows=readable_metadata_rows(records, options),
        turns=turns,
        include_appendix=include_appendix_enabled(options),
        turn_table=turn_table,
        qa_summary=options.qa_summary,
        turn_headings=turn_headings,
    )


def readable_mode_enabled(options: RenderOptions) -> bool:
    """Return whether to use the low-noise default renderer."""
    return (
        not options.include_system
        and not options.include_usage
        and not options.raw_tool_output
    )


def render_record(
    record: JsonLineRecord, context: RenderContext, options: RenderOptions
) -> str:
    """Render one JSONL record."""
    data = record.data
    record_type = get_string(data.get("type"))
    payload = get_object(data.get("payload"))

    if record_type == "session_meta":
        return render_session_meta(data, options)
    if record_type == "turn_context":
        return render_turn_context(data, options)
    if record_type == "response_item":
        return render_response_item(payload, context, options)
    if record_type == "event_msg":
        return render_event_message(payload, options)
    if record_type in (
        "thread.started",
        "turn.started",
        "turn.completed",
        "turn.failed",
        "error",
    ):
        return render_public_lifecycle(data, options)
    if record_type.startswith("item."):
        return render_public_item(get_object(data.get("item")), options)
    if options.include_unknown:
        if is_excluded(options, "unknown", "appendix"):
            return ""
        return details_block(f"record line {record.line_number}: {record_type}", data)
    return ""


def render_markdown(records: list[JsonLineRecord], options: RenderOptions) -> str:
    """Render all records to Markdown."""
    if readable_mode_enabled(options):
        return render_readable_markdown(records, options)

    context = build_render_context(records)
    blocks: list[str] = []
    for record in records:
        block = render_record(record, context, options)
        if block.strip():
            blocks.append(block.strip())

    if blocks:
        return "\n\n---\n\n".join(blocks) + "\n"
    return (
        render_heading(1, options.document_title) + "\n\nNo renderable records found.\n"
    )


def write_output(output_path: Path | None, markdown: str) -> None:
    """Write Markdown to a file or stdout."""
    if output_path is None:
        sys.stdout.write(markdown)
        sys.stdout.flush()
        return
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(markdown, encoding="utf-8")
    CLIStyle.write(
        f"Wrote Markdown: {output_path}",
        CLIStyle.COLORS["OK"],
        error=True,
    )


def find_session_name(records: list[JsonLineRecord]) -> str:
    """Find the Codex generated thread name when present."""
    thread_name = ""
    for record in records:
        payload = get_object(record.data.get("payload"))
        if payload.get("type") == "thread_name_updated":
            thread_name = get_string(payload.get("thread_name"))
    if thread_name:
        return thread_name

    for record in records:
        if record.data.get("type") == "thread.started":
            for key in ("thread_name", "name", "title"):
                thread_name = get_string(record.data.get(key))
                if thread_name:
                    return thread_name
    return ""


def find_session_id(records: list[JsonLineRecord]) -> str:
    """Find a stable session or thread id."""
    for record in records:
        payload = get_object(record.data.get("payload"))
        session_id = get_string(payload.get("id"))
        if record.data.get("type") == "session_meta" and session_id:
            return session_id
        thread_id = get_string(record.data.get("thread_id"))
        if record.data.get("type") == "thread.started" and thread_id:
            return thread_id
    return ""


def find_first_user_message(records: list[JsonLineRecord]) -> str:
    """Find the first substantial visible user request."""
    for record in records:
        data = record.data
        payload = get_object(data.get("payload"))
        if data.get("type") != "event_msg" or payload.get("type") != "user_message":
            continue
        text = normalize_user_request(get_string(payload.get("message")))
        if text:
            return text

    for record in records:
        data = record.data
        payload = get_object(data.get("payload"))
        if data.get("type") == "response_item" and payload.get("role") == "user":
            text = normalize_user_request(content_text(payload.get("content")))
            if text:
                return text
        if get_string(data.get("type")).startswith("item."):
            item = get_object(data.get("item"))
            if item.get("type") == "user_message":
                text = normalize_user_request(get_string(item.get("text")))
                if text:
                    return text
    return ""


def normalize_user_request(text: str) -> str:
    """Return the request part of a user message, skipping setup wrappers."""
    stripped = text.strip()
    if not stripped:
        return ""
    if stripped.startswith("<environment_context>"):
        return ""

    marker = "## My request for Codex:"
    if marker in stripped:
        return stripped.split(marker, 1)[1].strip()
    return stripped


def strip_title_secrets(text: str) -> str:
    """Remove path-like and secret-like values before title inference."""
    cleaned = re.sub(r"`[^`]*`", " ", text)
    cleaned = re.sub(r"\$[A-Za-z][A-Za-z0-9_-]*", " ", cleaned)
    cleaned = re.sub(r"(?:~|/)[^\s，。！？；：、,!?;:]+", " ", cleaned)
    cleaned = re.sub(
        r"\b[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-"
        r"[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\b",
        " ",
        cleaned,
    )
    cleaned = re.sub(r"\b(?:[A-Za-z0-9_-]{24,}|sk-[A-Za-z0-9_-]+)\b", " ", cleaned)
    cleaned = re.sub(r"\b\d{1,3}(?:\.\d{1,3}){3}\b", " ", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def infer_cjk_title(text: str) -> str:
    """Infer a compact CJK-friendly title."""
    sentence = re.split(r"[。！？?!\n\r]", text, maxsplit=1)[0].strip()
    if not sentence:
        return ""
    prefix = re.split(r"[：:]", sentence, maxsplit=1)[0].strip()
    if len(prefix) >= 6:
        sentence = prefix
    sentence = re.sub(r"[“”\"'<>#*_~|\\[\]{}]+", " ", sentence)
    sentence = re.sub(r"\s+", " ", sentence).strip(" -_，,。.")
    return sentence[:32].strip()


def infer_english_title(text: str) -> str:
    """Infer a compact English title."""
    words = re.findall(r"[A-Za-z0-9]+", text.lower())
    stop_words = {
        "a",
        "an",
        "and",
        "are",
        "for",
        "from",
        "how",
        "the",
        "this",
        "to",
        "with",
        "please",
    }
    visible_words = [word for word in words if word not in stop_words]
    if not visible_words:
        return ""
    return " ".join(visible_words[:6])


def infer_session_title(records: list[JsonLineRecord]) -> str:
    """Infer a readable document title when Codex has no thread name."""
    first_user_message = strip_title_secrets(find_first_user_message(records))
    if not first_user_message:
        return ""
    if re.search(r"[\u3400-\u9fff]", first_user_message):
        return infer_cjk_title(first_user_message)
    return infer_english_title(first_user_message)


def build_document_title(
    records: list[JsonLineRecord],
    manual_title: str = "",
    manual_title_source: str = "manual override",
) -> tuple[str, str, str]:
    """Return session name, document title, and title source label."""
    session_name = find_session_name(records)
    if manual_title:
        return session_name, manual_title, manual_title_source
    if session_name:
        return session_name, session_name, "agent metadata"
    inferred_title = infer_session_title(records)
    if inferred_title:
        return "", inferred_title, "inferred from first user request"
    return "", "Codex Session", "fallback"


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
    return cleaned or "codex-session"


def get_output_stem(
    records: list[JsonLineRecord], input_path: Path, manual_title: str = ""
) -> str:
    """Return the default output filename stem."""
    if manual_title:
        return sanitize_filename(manual_title)

    session_name = find_session_name(records)
    if session_name:
        return sanitize_filename(session_name)
    inferred_title = infer_session_title(records)
    if inferred_title:
        return sanitize_filename(inferred_title)
    session_id = find_session_id(records)
    if session_id:
        return sanitize_filename(session_id)
    return sanitize_filename(input_path.stem)


def build_render_options(
    args: argparse.Namespace,
    input_path: Path,
    session_name: str,
    document_title: str,
    title_source: str,
    include_system: bool,
    include_usage: bool,
) -> RenderOptions:
    """Build render options for one output variant."""
    return RenderOptions(
        input_path=input_path,
        session_name=session_name,
        document_title=document_title,
        title_source=title_source,
        include_system=include_system,
        include_usage=include_usage,
        include_unknown=not args.no_unknown,
        include_appendix=not args.quiet,
        raw_tool_output=args.raw_tool_output,
        max_output_chars=args.max_output_chars,
        excluded_items=args.excluded_items,
        excluded_turns=args.excluded_turns,
        export_plan=args.export_plan_data,
        turn_table=args.turn_table_text,
        qa_summary=args.qa_summary_text,
    )


def build_requested_variants(args: argparse.Namespace) -> list[OutputVariant]:
    """Build default output variants requested by include flags."""
    variants = [OutputVariant("", False, False)]
    if args.include_all:
        variants.append(OutputVariant("-all", True, True))
        return variants
    if args.include_usage:
        variants.append(OutputVariant("-usage", False, True))
    if args.include_system:
        variants.append(OutputVariant("-system", True, False))
    if args.include_usage and args.include_system:
        variants.append(OutputVariant("-all", True, True))
    return variants


def include_mode_enabled(args: argparse.Namespace) -> bool:
    """Return whether any include output mode is active."""
    return bool(args.include_usage or args.include_system or args.include_all)


def write_default_variant_outputs(
    records: list[JsonLineRecord],
    args: argparse.Namespace,
    input_path: Path,
) -> None:
    """Write default include-mode files into a generated output directory."""
    output_stem = get_output_stem(records, input_path, args.title)
    session_name, document_title, title_source = build_document_title(
        records, args.title
    )
    output_dir = Path.cwd() / f"session-{output_stem}"
    for variant in build_requested_variants(args):
        output_path = output_dir / f"{output_stem}{variant.suffix}.md"
        options = build_render_options(
            args,
            input_path,
            session_name,
            document_title,
            title_source,
            variant.include_system,
            variant.include_usage,
        )
        write_output(output_path, render_markdown(records, options))


def build_parser() -> argparse.ArgumentParser:
    """Build the command line parser."""
    script_name = Path(__file__).name
    epilog = create_example_text(
        script_name,
        [
            (
                "Convert a saved Codex rollout transcript",
                "~/.codex/sessions/.../rollout.jsonl -o session.md",
            ),
            (
                "Convert codex exec --json output",
                "/tmp/codex-exec.jsonl -o /tmp/codex-exec.md --include-usage",
            ),
            (
                "Set the Markdown H1 directly",
                'session.jsonl -o session.md --title "Release QA Session"',
            ),
            (
                "Drop low-value appendix items",
                "session.jsonl -o session.md --exclude commands,searches",
            ),
            (
                "Drop the final unrelated QA turn",
                "session.jsonl -o session.md --exclude-turn=-1",
            ),
            (
                "Use a structured export plan for the turn index and headings",
                "session.jsonl -o session.md --export-plan /tmp/export-plan.json",
            ),
            (
                "Insert a curated turn index table",
                "session.jsonl -o session.md --turn-table /tmp/turn-table.md",
            ),
            (
                "Insert a curated QA summary section",
                "session.jsonl -o session.md --qa-summary /tmp/qa-summary.md",
            ),
            ("Write default base and all-details files", "session.jsonl --include-all"),
            ("Include system and developer messages", "session.jsonl --include-system"),
        ],
        notes=[
            "Supports documented codex exec --json event streams and local rollout transcripts.",
            "Known item families: messages, reasoning, command execution, file changes, MCP/tool calls, web search, and plan updates.",
            "Default render keeps visible conversation and compact activity summaries, not raw tool/event logs.",
            "Usage render adds accounting details; for example, token usage blocks like input/output/reasoning totals.",
            "System render adds setup context; for example, hidden records like developer messages and sandbox/model settings.",
            "All render combines usage and system details.",
            "Without --output, include modes write session-NAME/NAME.md plus NAME-usage.md, NAME-system.md, or NAME-all.md.",
            "Unknown records are kept as collapsible JSON by default.",
            "Repeat --exclude or pass comma-separated values. Allowed values: "
            + ", ".join(sorted(get_exclude_item_choices()))
            + ".",
            "Use --exclude-turn for whole QA turns in readable output; "
            "positive numbers are 1-based and -1/last means the final turn.",
            "Use --export-plan with an agent-written JSON file to render both "
            "the turn index table and per-turn level-2 headings.",
            "Use --turn-table with an agent-written Markdown table fragment; "
            "the script inserts it after metadata as a table of contents.",
            "Use --qa-summary with an agent-written Markdown fragment; "
            "each QA item should use level-2 headings like ## 1. Summary.",
        ],
    )
    parser = ColoredArgumentParser(
        description="Convert Codex JSONL session transcripts into Markdown.",
        epilog=epilog,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "session_jsonl",
        help=CLIStyle.color(
            "Path to a Codex session JSONL file.", CLIStyle.COLORS["CONTENT"]
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
        "--title",
        help=CLIStyle.color(
            "Override the Markdown H1 and default title-based output name.",
            CLIStyle.COLORS["CONTENT"],
        ),
    )
    parser.add_argument(
        "--exclude",
        action="append",
        metavar="ITEM",
        help=CLIStyle.color(
            "Omit a content item. Repeat or use commas, for example: "
            "--exclude commands,searches.",
            CLIStyle.COLORS["CONTENT"],
        ),
    )
    parser.add_argument(
        "--exclude-turn",
        "--exclude-qa",
        action="append",
        metavar="TURN",
        help=CLIStyle.color(
            "Omit a whole QA turn from readable output. Use 1-based numbers, "
            "negative numbers from the end, or last.",
            CLIStyle.COLORS["CONTENT"],
        ),
    )
    parser.add_argument(
        "--export-plan",
        metavar="FILE",
        help=CLIStyle.color(
            "Read structured JSON for title, turn index, and turn headings.",
            CLIStyle.COLORS["CONTENT"],
        ),
    )
    parser.add_argument(
        "--turn-table",
        metavar="FILE",
        help=CLIStyle.color(
            "Insert a curated turn index Markdown table after metadata.",
            CLIStyle.COLORS["CONTENT"],
        ),
    )
    parser.add_argument(
        "--qa-summary",
        metavar="FILE",
        help=CLIStyle.color(
            "Insert a curated QA summary Markdown fragment before the transcript.",
            CLIStyle.COLORS["CONTENT"],
        ),
    )
    parser.add_argument(
        "--include-system",
        action="store_true",
        help=CLIStyle.color(
            "Include system, developer, and turn context records.",
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
        "--raw-tool-output",
        action="store_true",
        help=CLIStyle.color(
            "Keep raw function output even when a richer tool event exists.",
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
    output_path = Path(args.output).expanduser().resolve() if args.output else None
    args.export_plan_data = read_export_plan(args.export_plan or "")
    raw_title = args.title
    args.title_source_label = "manual override"
    if raw_title is None and args.export_plan_data is not None:
        raw_title = args.export_plan_data.title or None
        if raw_title is not None:
            args.title_source_label = "export plan"
    args.title = (raw_title or "").strip()
    args.excluded_items = parse_excluded_items(args.exclude)
    args.excluded_turns = parse_excluded_turns(args.exclude_turn)
    args.turn_table_text = read_optional_text_file(args.turn_table or "", "turn table")
    args.qa_summary_text = read_optional_text_file(args.qa_summary or "", "QA summary")
    if not input_path.is_file():
        raise FileNotFoundError(f"input file not found: {input_path}")
    if raw_title is not None and not args.title:
        raise ValueError("title must not be empty")
    if args.max_output_chars < 0:
        raise ValueError("max-output-chars must be >= 0")
    if args.excluded_turns and (include_mode_enabled(args) or args.raw_tool_output):
        raise ValueError(
            "exclude-turn applies only to default readable QA output"
        )
    if args.export_plan_data and args.turn_table_text:
        raise ValueError("export-plan cannot be combined with turn-table")
    if args.export_plan_data and (include_mode_enabled(args) or args.raw_tool_output):
        raise ValueError("export-plan applies only to default readable QA output")
    if args.turn_table_text and (include_mode_enabled(args) or args.raw_tool_output):
        raise ValueError("turn-table applies only to default readable QA output")
    if args.qa_summary_text and (include_mode_enabled(args) or args.raw_tool_output):
        raise ValueError("qa-summary applies only to default readable QA output")

    records = read_jsonl(input_path)
    debug("records", count=len(records))
    session_name, document_title, title_source = build_document_title(
        records, args.title, args.title_source_label
    )
    if output_path is None and include_mode_enabled(args):
        write_default_variant_outputs(records, args, input_path)
        return 0

    options = build_render_options(
        args,
        input_path,
        session_name,
        document_title,
        title_source,
        args.include_system or args.include_all,
        args.include_usage or args.include_all,
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
