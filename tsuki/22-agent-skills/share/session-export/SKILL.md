---
name: session-export
description: "Export agent session transcripts to Markdown for long conversations and local transcript files. Use when the user invokes $session-export, asks to save/freeze/archive/export the current session as Markdown, or wants to convert Codex, Claude Code, OpenCode, or adjacent agent session logs into readable Markdown."
---

# Session Export

## Default Action

When the user invokes `$session-export` without a file path, locate the current agent's local session transcript if available, inspect it, then present an export proposal for confirmation before writing Markdown. If the current transcript cannot be located from the active environment, ask for the session file path or the agent name and session id.

When the user provides a transcript path, detect the agent from the file path and JSON shape, inspect it, then present the same export proposal before running the matching script in `scripts/`.

Skip the confirmation proposal only when the user explicitly asks for a direct export, unattended export, or exact command execution. Even then, still choose a safe title and remove clearly unrelated final export-request turns when the user has already authorized curation.

## Agent Scripts

- Shared template: `scripts/template.py` owns common CLI helpers, timestamp formatting, Markdown helpers, default QA turn rendering, collapsible appendix rendering, and operation summaries. Agent scripts should import it for shared presentation behavior and keep only agent-specific parsing local.
- Codex: run `scripts/codex-session-to-md.py` for `~/.codex/sessions/**/*.jsonl`, rollout JSONL files, and `codex exec --json` event streams.
- Claude Code: run `scripts/claude-session-to-md.py` for Claude Code JSONL session files under `~/.claude/projects/<encoded-cwd>/*.jsonl`.
- OpenCode: run `scripts/opencode-session-to-md.py` for OpenCode JSON exports from `opencode export <sessionID> --sanitize`, local session ids, or the SQLite database at `~/.local/share/opencode/opencode.db`.

Do not force one agent's parser onto another agent's transcript. Agents differ in event names, message roles, tool-call shapes, storage paths, and title fields.

## Export Workflow

1. Identify the agent: prefer explicit user input; otherwise infer from path and JSON shape.
2. Locate the transcript: use the provided path first; otherwise search the current agent's known session directory.
3. Inspect the readable QA turns and infer a concise export title.
4. Present the export proposal in the format below and ask for confirmation or adjustments.
5. After confirmation, run the matching script with the smallest useful detail mode and any selected title, turn exclusions, or content exclusions.
6. Save Markdown using the script's default naming rules unless the user provides an explicit output path.
7. Report the generated path and mention whether the title came from agent metadata, user confirmation, or inference.

## Export Proposal Format

Use this exact shape when asking the user to confirm a curated export plan. Match the transcript language for user-visible summaries when practical.

```markdown
**Session Export Plan**

Title: <short proposed Markdown H1>
Source: <agent and transcript path or current session>
Output: <planned output path or default naming rule>
Mode: <base | quiet | usage | system | all>

Turns:
| # | Export | Q | A | Note |
| --- | --- | --- | --- | --- |
| 1 | keep | <one-sentence user-request summary> | <one-sentence assistant-outcome summary> | <why keep / optional> |
| 2 | exclude | <summary> | <summary> | unrelated export request |

Options:
- Title: `--title "<title>"`
- Exclude turns: `<none | --exclude-turn ...>`
- Exclude items: `<none | --exclude ...>`
- Detail mode: `<base | -q | --include-usage | --include-system | --include-all>`
- Export plan JSON: `--export-plan <file>`
- Turn table: `<derived from export plan | --turn-table <file>>`
- QA summary: `<none | --qa-summary <file>>`
- Sensitive redaction: `<ask | enable | disable>` - <why this is suggested or not>
- Sandbox paths: `<ask | enable | disable>` - <path mapping, for example `/home/wkyuu -> /home/sandbox`>

Please confirm this export plan, or tell me which turn numbers or details to keep/remove.
```

Turn rows must be concise summaries, not full transcript copies. The `Export` column should be `keep`, `exclude`, or `review`. Use `exclude` for turns that are clearly unrelated to the export theme, such as a final turn where the user only asked the agent to export the session and the assistant only reported the output path. Use `review` when relevance is ambiguous.

Before proposing turn indexes, inspect the transcript's turn structure. Prefer explicit turn identifiers when the agent format provides them, such as Codex `internal_chat_message_metadata_passthrough.turn_id` on `response_item` user messages or `task_started` / `task_complete` boundaries. When a user sends follow-up messages before the assistant produces a final answer, treat those messages as additions to the same QA turn. In the proposal table, summarize this as one Q and mention the follow-up in the Q text, for example `Initial request; follow-up: requested token embedded in remote script`.

Useful optional notes include `setup context`, `main task`, `debugging`, `implementation`, `verification`, `follow-up`, `export request only`, `possible sensitive content`, or `low-value operational chatter`.

After the user confirms the export plan, write the confirmed structure to a temporary JSON file and pass it with `--export-plan`. This is the default path for curated Codex readable exports because it lets the script render the turn index table and per-turn `##` headings consistently.

Use this JSON shape:

```json
{
  "title": "游戏服务器脚本仓库命名",
  "turn_table_title": "Turn Index",
  "include_turn_table": true,
  "include_turn_headings": true,
  "turns": [
    {
      "index": 1,
      "export": "keep",
      "heading": "为自写游戏服务器脚本仓库起名，覆盖 Steam、Minecraft 和其他自建服脚本。",
      "q": "为自写游戏服务器脚本仓库起名，覆盖 Steam、Minecraft 和其他自建服脚本。",
      "a": "先从工房、据点、公会等方向给出候选，首推 server-koubou。",
      "note": "setup context"
    },
    {
      "index": 2,
      "export": "keep",
      "heading": "要往 RPG、工会大厅、中世纪、赏金猎人、做任务方向发散。",
      "q": "要往 RPG、工会大厅、中世纪、赏金猎人、做任务方向发散。",
      "a": "给出 guildhall、questboard、bounty-board 等候选，首推 questboard。",
      "note": "naming iteration"
    }
  ]
}
```

Rules for the structured export plan:

- `title` should match the confirmed document title. The script uses it when `--title` is not provided.
- `turns[].index` must match the visible QA turn number from the proposal table before exclusions.
- `turns[].heading` is rendered before each exported user turn as `## <index>. <heading>`.
- `turns[].q`, `turns[].a`, and `turns[].note` are rendered in the top `Turn Index` table.
- Include rows marked `exclude` when the user wants the final document to show curation decisions. Excluded rows appear in the top table but do not get per-turn headings when the actual turn is removed with `--exclude-turn`.
- Keep all fields concise. Do not copy full transcript text into the plan JSON.

The script renders the top table like this:

```markdown
## Turn Index

| # | Export | Q | A | Note |
| --- | --- | --- | --- | --- |
| 1 | keep | 把 acme 从 AliDNS 切到 Cloudflare DNS。 | 先检查到 token 无效并停下，未改远端。 | main task |
| 2 | keep | 用户更新 token。 | 重新验证，仍发现格式或接口问题并继续定位。 | debugging |
```

Only use `--turn-table` directly when a caller already has a prebuilt Markdown table and does not need per-turn headings. The fragment should not contain an H1.

When the user wants the export plan's per-turn summaries preserved in the final Markdown, create a small QA summary fragment and pass it with `--qa-summary`. The fragment should not contain an H1. Use one H2 per exported turn:

```markdown
## 1. 把 acme 从 AliDNS 切到 Cloudflare DNS

**Q:** 用户要求检查远端 acme 配置，并把 DNS 验证从 AliDNS 切到 Cloudflare。

**A:** 助手先验证 Cloudflare token，发现凭据无效并停止，没有改动远端。

**Note:** main task
```

The summary should include only turns marked `keep` unless the user asks to document excluded turns. Keep Q/A summaries concise and human-written; do not duplicate full transcript text.

The `Options` section is the extension point for export-time choices that are not simply keep/remove decisions. Keep it short and add options only when they are relevant to the inspected transcript or user request.

Supported extension: sensitive redaction.

- Sensitive redaction is not enabled by default.
- If the transcript appears to contain credentials, tokens, private IPs, internal hostnames, account identifiers, or similar sensitive material, set `Sensitive redaction` to `ask` and explain briefly what category was detected without repeating the sensitive value.
- Set it to `enable` only when the user explicitly requested redaction/sanitization or already gave standing permission to redact sensitive details.
- Set it to `disable` when there is no apparent sensitive content or the user explicitly wants a faithful archival export.

Supported extension: sandbox paths.

- Sandbox paths are not enabled by default.
- Use this when absolute local paths, usernames, project roots, or host-specific mount points should be preserved structurally but not literally. Example mapping: `/home/wkyuu -> /home/sandbox`.
- Set `Sandbox paths` to `ask` when path privacy would improve shareability but the user has not requested path rewriting.
- Set it to `enable` only when the user explicitly requests sandboxed paths or confirms the option in the export plan.
- Set it to `disable` when exact local paths matter for archival or follow-up work.
- This option may require exporter script support. If the current script lacks it, state the planned mapping in the export proposal and either ask before post-processing the generated Markdown or leave it disabled.

After the user confirms, translate the plan into script arguments. For Codex, use `--title` for the proposed title, `--exclude-turn` for whole QA turns, and `--exclude` only for item-category filtering such as commands, searches, reasoning, or appendix content.

For Codex:

```bash
python3 scripts/codex-session-to-md.py /path/to/rollout.jsonl --include-all
python3 scripts/codex-session-to-md.py /path/to/rollout.jsonl -o session.md
python3 scripts/codex-session-to-md.py /path/to/rollout.jsonl -o session.md --title "Release QA Session"
python3 scripts/codex-session-to-md.py /path/to/rollout.jsonl -o session.md --exclude commands,searches
python3 scripts/codex-session-to-md.py /path/to/rollout.jsonl -o session.md --exclude-turn=-1
python3 scripts/codex-session-to-md.py /path/to/rollout.jsonl -o session.md --export-plan /tmp/export-plan.json
python3 scripts/codex-session-to-md.py /path/to/rollout.jsonl -o session.md --turn-table /tmp/turn-table.md
python3 scripts/codex-session-to-md.py /path/to/rollout.jsonl -o session.md --qa-summary /tmp/qa-summary.md
```

Codex readable exports should use the agent thread name as the Markdown H1 when present. If Codex has no thread-name event, infer a short, sanitized title from the first substantial user request and record `title source` as `inferred from first user request` in the metadata. Use `Codex Session` only as a fallback when neither an agent title nor a usable request exists.

When the user gives a preferred document title, pass it with `--title` instead of editing the generated Markdown afterward. The script records `title source` as `manual override`, keeps the original session name in metadata when present, and uses the manual title for default title-based output names.

When the user asks for a focused export, choose `--exclude` values before running the script so the generated Markdown is already curated. Repeat `--exclude` or pass comma-separated values. Supported Codex exclude items are `appendix`, `assistant`, `commands`, `edits`, `errors`, `file-changes`, `lifecycle`, `metadata`, `operations`, `plan-updates`, `reasoning`, `searches`, `system`, `tool-calls`, `tool-outputs`, `tools`, `unknown`, `usage`, and `user`. Use `--exclude operations` to drop the compact operation appendix categories together, or use narrower values such as `commands,searches` when the user wants to preserve edits and tool names.

When the user wants a curated QA transcript and one or more complete turns are unrelated to the topic, use `--exclude-turn` instead of post-editing the Markdown. Turn numbers are 1-based, negative numbers count from the end, and `last` is accepted; for example, use `--exclude-turn=-1` or `--exclude-turn last` when the final QA only records the export request itself. This applies to the default readable QA output, not detail modes such as `--include-all`.

When exporting the current active session after the user confirms an export plan, append `-1` to the planned excluded turns so the confirmation/export-execution turn is also removed. For example, if turn 11 is the `$session-export` request, run `--exclude-turn 11,-1`. The readable renderer also drops a trailing incomplete user-only turn before applying `--exclude-turn`, which prevents an in-progress confirmation message from appearing as an orphan final `USER` block and keeps previously confirmed turn indexes stable.

Codex readable exports merge consecutive user messages into the same QA turn when no assistant final answer has been produced yet. The merged Q labels later messages with `Follow-up:` so the exported transcript shows that the user refined or supplemented the original request.

Codex readable exports should use `--export-plan <file>` for curated output. The script places the generated turn table after metadata, inserts generated per-turn `##` headings before each exported `USER` block, then renders the full transcript. It can also insert an agent-written turn table fragment with `--turn-table <file>` and an agent-written QA summary fragment with `--qa-summary <file>` for lower-level workflows. These options apply only to the default readable output, not `--include-all`, `--include-system`, `--include-usage`, or `--raw-tool-output`.

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

- Base: human-readable QA transcript. Render each turn with optional agent-curated level-2 headings from `--export-plan`, centered bold uppercase H3 role labels for USER and ASSISTANT, right-aligned bold local timestamps like `2026-06-27 18:25:49 (UTC+08:00)`, the original user prompt, and the assistant's final answer with its Markdown formatting preserved. Move commentary, reasoning summaries, searches, commands, tool use, and effective file changes into collapsible appendix blocks.
- Quiet or release: base without appendix blocks. Use `-q`, `--quiet`, or `--release` when the user wants only the public QA transcript and not commentary, reasoning, searches, commands, tool use, or change summaries.
- Usage: base plus token or cost accounting, if present.
- System: base plus hidden setup context such as developer messages, environment context, sandbox settings, and model settings.
- All: usage plus system.

Default to base for quick reading. Keep the main reading path as question and answer; avoid raw `Tool call`, `Tool output`, lifecycle, token, commentary, and per-search event spam in base mode. Render appendix bodies as real HTML children directly inside `<details>` with no blank Markdown paragraph between `<summary>` and the child nodes, because some Markdown viewers otherwise show folded content outside the collapsed block. Use all when the user asks to preserve a session completely or debug the exporter.

Script flags:

- Codex: `-q`/`--quiet`/`--release`, `--title`, `--exclude`, `--exclude-turn`/`--exclude-qa`, `--export-plan`, `--turn-table`, `--qa-summary`, `--include-usage`, `--include-system`, `--include-all`, `--no-unknown`, `--raw-tool-output`, `--max-output-chars`.
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
