---
name: session-export
description: "Export agent session transcripts to Markdown for long conversations and local transcript files. Use when the user invokes $session-export, asks to save/freeze/archive/export the current session as Markdown, or wants to convert Codex, Claude Code, OpenCode, or adjacent agent session logs into readable Markdown."
---

# Session Export

## Default Action

When the user invokes `$session-export` without a file path, locate the current agent's local session transcript if available, then export it to Markdown. If the current transcript cannot be located from the active environment, ask for the session file path or the agent name and session id.

When the user provides a transcript path, detect the agent from the file path and JSON shape, then run the matching script in `scripts/`.

## Agent Scripts

- Shared template: `scripts/template.py` owns common CLI helpers, timestamp formatting, Markdown helpers, default QA turn rendering, collapsible appendix rendering, and operation summaries. Agent scripts should import it for shared presentation behavior and keep only agent-specific parsing local.
- Codex: run `scripts/codex-session-to-md.py` for `~/.codex/sessions/**/*.jsonl`, rollout JSONL files, and `codex exec --json` event streams.
- Claude Code: run `scripts/claude-session-to-md.py` for Claude Code JSONL session files under `~/.claude/projects/<encoded-cwd>/*.jsonl`.
- OpenCode: run `scripts/opencode-session-to-md.py` for OpenCode JSON exports from `opencode export <sessionID> --sanitize`, local session ids, or the SQLite database at `~/.local/share/opencode/opencode.db`.

Do not force one agent's parser onto another agent's transcript. Agents differ in event names, message roles, tool-call shapes, storage paths, and title fields.

## Export Workflow

1. Identify the agent: prefer explicit user input; otherwise infer from path and JSON shape.
2. Locate the transcript: use the provided path first; otherwise search the current agent's known session directory.
3. Run the matching script with the smallest useful detail mode.
4. Save Markdown using the script's default naming rules unless the user provides an explicit output path.
5. Report the generated path and mention whether the title came from agent metadata or was inferred.

For Codex:

```bash
python3 scripts/codex-session-to-md.py /path/to/rollout.jsonl --include-all
python3 scripts/codex-session-to-md.py /path/to/rollout.jsonl -o session.md
```

For Claude Code:

```bash
python3 scripts/claude-session-to-md.py ~/.claude/projects/-path-to-project/session.jsonl -o session.md
python3 scripts/claude-session-to-md.py ~/.claude/projects/-path-to-project/session.jsonl --include-all --default-output
```

Current observed Claude Code 2.1.x local session shape:

- Storage: `~/.claude/projects/<encoded-cwd>/*.jsonl`.
- Resume CLI: `claude --resume <session-id>` and `claude --continue` from the current directory.
- Title records: `{"type":"ai-title","aiTitle":"...","sessionId":"..."}`.
- Conversation records: top-level `type` values `user` and `assistant`, with `message.role` and `message.content`.
- Common content blocks: `text`, `tool_use`, `tool_result`, `thinking`, and `redacted_thinking`.
- Other observed records: `queue-operation`, `attachment`, `file-history-snapshot`, `last-prompt`, and `mode`.

For OpenCode:

```bash
opencode export <sessionID> --sanitize > /tmp/opencode-session.json
python3 scripts/opencode-session-to-md.py /tmp/opencode-session.json -o session.md
python3 scripts/opencode-session-to-md.py <sessionID> --include-all -o session.md
python3 scripts/opencode-session-to-md.py --default-output
```

Current observed OpenCode 1.17.x local session shape:

- Official export CLI: `opencode export [sessionID]` with `--sanitize` to redact sensitive transcript and file data.
- Storage: `~/.local/share/opencode/opencode.db`.
- SQLite tables used by the parser: `session`, `message`, and `part` only.
- Session title: `session.title`; stable id: `session.id`; model/accounting fields live on `session` and assistant `message.data`.
- Export JSON shape: top-level `info` plus `messages[]`; each message has `info` and `parts[]`.
- Common part types: `text`, `reasoning`, `tool`, `step-start`, `step-finish`, and `file`.

## Session Naming

Prefer names in this order:

1. Agent-provided session title or thread name.
2. Stable session id when no title exists and exact archival naming matters.
3. Generated title from content when no agent title exists and readable naming matters.

When generating a title from content, use the first substantial user request plus the final outcome. Produce a short filename-safe title in the transcript language when possible. Keep it under 32 characters for CJK text or under 6 kebab-case words for English. Remove secrets, absolute home paths, access tokens, IP credentials, and large ids. If the generated title is uncertain, say `title inferred from first user request`.

Never state that a title came from the agent if the transcript has no title field.

## Detail Modes

- Base: human-readable QA transcript. Render each turn with centered bold uppercase H3 role labels for USER and ASSISTANT, right-aligned bold local timestamps like `2026-06-27 18:25:49 (UTC+08:00)`, the original user prompt, and the assistant's final answer with its Markdown formatting preserved. Move commentary, reasoning summaries, searches, commands, tool use, and effective file changes into collapsible appendix blocks.
- Quiet or release: base without appendix blocks. Use `-q`, `--quiet`, or `--release` when the user wants only the public QA transcript and not commentary, reasoning, searches, commands, tool use, or change summaries.
- Usage: base plus token or cost accounting, if present.
- System: base plus hidden setup context such as developer messages, environment context, sandbox settings, and model settings.
- All: usage plus system.

Default to base for quick reading. Keep the main reading path as question and answer; avoid raw `Tool call`, `Tool output`, lifecycle, token, commentary, and per-search event spam in base mode. Render appendix bodies as real HTML children inside `<details>` instead of Markdown lists, because some Markdown viewers otherwise show folded content outside the collapsed block. Use all when the user asks to preserve a session completely or debug the exporter.

Script flags:

- Codex: `-q`/`--quiet`/`--release`, `--include-usage`, `--include-system`, `--include-all`, `--no-unknown`, `--raw-tool-output`, `--max-output-chars`.
- Claude Code: `-q`/`--quiet`/`--release`, `--include-usage`, `--include-system`, `--include-all`, `--no-unknown`, `--max-output-chars`, `--default-output`.
- OpenCode: `-q`/`--quiet`/`--release`, `--include-usage`, `--include-system`, `--include-all`, `--no-unknown`, `--max-output-chars`, `--default-output`, `--db`, `--session-id`.

## Update Rules

Use these rules when the user asks to modify or extend `session-export` itself.

1. Check official upstream behavior for the target agent before changing parser logic. Use official documentation, release notes, CLI help, or source code for Codex, Claude Code, OpenCode, or the named agent. Prefer current primary sources over memory.
2. Capture the observed transcript shape from real sample files with structured queries before editing. Record event names, role fields, tool-call fields, title fields, and session-id fields.
3. Keep one script per agent under `scripts/`. Put shared presentation behavior in `scripts/template.py`; keep wire-format parsing inside the agent script. When changing the default readable Markdown shape, update the template first and sync agent scripts to it.
4. Apply `$code-python` to every Python script update. Preserve consistent CLI conventions: colored help, `--log`, typed functions, English identifiers, deterministic errors, and no Chinese comments.
5. Keep each parser conservative. Unknown event types should be preserved as collapsible JSON or skipped only behind an explicit flag.
6. Validate every changed script with `python3 -m py_compile` and at least one representative sample transcript. Use `/tmp` for generated test output unless the user requests a project path.
7. Update this `SKILL.md` when a new agent script is added, when an agent changes session storage, or when default naming behavior changes.

## Output Rules

Default output should be a Markdown file or a directory of Markdown variants near the working directory or requested output path. Avoid writing into a managed agent state directory unless the user explicitly asks for in-place output.

If the user invokes `$session-export` in a long active conversation, prefer preserving a complete Markdown export over summarizing. This skill is for archival fidelity; retrospective summarization belongs in a separate workflow.
