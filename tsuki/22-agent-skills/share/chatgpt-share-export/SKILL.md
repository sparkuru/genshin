---
name: chatgpt-share-export
description: "Export public ChatGPT shared conversation URLs or saved ChatGPT share HTML pages into readable Markdown. Use when Codex needs to fetch, parse, archive, or curate chatgpt.com/share/... transcripts, especially when session-export does not apply because the source is a ChatGPT web share rather than a local Codex, Claude Code, or OpenCode transcript."
---

# ChatGPT Share Export

## Default Workflow

Use this skill for `https://chatgpt.com/share/...` links and saved ChatGPT share HTML files.

1. Fetch the share page with a browser-like user agent, or use an already downloaded HTML file.
2. Run `scripts/chatgpt-share-to-md.py` once with `--messages-json` and `--plan-template` to extract visible turns for inspection.
3. Read the extracted turns and rewrite the plan template so every row has a concise semantic `heading`, `q`, `a`, and `note`, following the same curation standard as `session-export`.
4. Run `scripts/chatgpt-share-to-md.py` again with `--plan <file>` to render the final Markdown.
5. Prefer base readable output: metadata, a turn index, and user/final-assistant QA turns.
6. Omit hidden reasoning, tool-call JSON, searches, redacted tool outputs, empty system/custom-instruction placeholders, ChatGPT internal citation tokens, and renderer-only Markdown directive containers unless the user explicitly asks for raw diagnostics.
7. Keep the export framework at `#` / `##`, and demote Markdown headings inside message bodies by 2 levels by default so assistant answer headings do not compete with turn headings.
8. Write to the user-requested path. If the path is outside the writable workspace, generate under `/tmp` first and then request write approval for the final copy.
9. Validate the export with `rg` for known noise markers before reporting completion.

## Common Commands

Export a public share URL directly:

```bash
python3 scripts/chatgpt-share-to-md.py \
  'https://chatgpt.com/share/<share-id>' \
  -o /tmp/chatgpt-share.md
```

Export from a saved HTML page:

```bash
python3 scripts/chatgpt-share-to-md.py \
  /tmp/chatgpt-share.html \
  -o /tmp/chatgpt-share.md \
  --source-url 'https://chatgpt.com/share/<share-id>'
```

Use a curated turn plan for headings and turn-index summaries:

```bash
python3 scripts/chatgpt-share-to-md.py \
  /tmp/chatgpt-share.html \
  -o /tmp/chatgpt-share.draft.md \
  --messages-json /tmp/chatgpt-visible-messages.json \
  --plan-template /tmp/chatgpt-share-plan.json
```

After editing `/tmp/chatgpt-share-plan.json`, render the final export:

```bash
python3 scripts/chatgpt-share-to-md.py \
  /tmp/chatgpt-share.html \
  -o /tmp/chatgpt-share.md \
  --plan /tmp/chatgpt-share-plan.json
```

Save extracted visible messages for inspection:

```bash
python3 scripts/chatgpt-share-to-md.py \
  /tmp/chatgpt-share.html \
  --messages-json /tmp/chatgpt-visible-messages.json \
  -o /tmp/chatgpt-share.md
```

Preserve ChatGPT internal citation tokens for archival fidelity:

```bash
python3 scripts/chatgpt-share-to-md.py \
  /tmp/chatgpt-share.html \
  -o /tmp/chatgpt-share.md \
  --keep-chatgpt-cites
```

Preserve original message heading levels:

```bash
python3 scripts/chatgpt-share-to-md.py \
  /tmp/chatgpt-share.html \
  -o /tmp/chatgpt-share.md \
  --content-heading-offset 0
```

Noise check:

```bash
rg -n 'The output of this plugin|Original custom instructions|system1_search_query|content_type|source_analysis_msg_id|reasoning_recap|cite|writing\{variant=' /tmp/chatgpt-share.md
```

No matches means the common hidden/runtime artifacts were removed.

ChatGPT citation tokens such as `citeturn123view0` are not durable Markdown citations. Strip them by default when exporting a document for reading or later project notes. Keep them only when the user wants a faithful raw-ish archive of what the ChatGPT answer displayed.

ChatGPT writing containers such as `:::writing{variant="document" id="..."}` are renderer-only markers. Strip the opening and closing directive lines by default, but keep the content inside.

## Heading Policy

Use heading demotion, not wrappers, for readable Markdown:

- Export framework: `#` for the document title, `##` for metadata, turn index, and turn headings.
- Message bodies: demote ATX headings by `--content-heading-offset`, default `2`.
- Fenced code blocks are not modified.
- Use `--content-heading-offset 0` for exact heading preservation.

This keeps the user's answer content readable while making the transcript scaffold visually distinct.

## Export Plan

Always use a curated plan for final exports unless the user explicitly asks for a mechanical draft. The script's automatic rows are only placeholders; they are not acceptable as final turn summaries.

Create a starter plan with `--plan-template`, then rewrite it before final export:

```json
{
  "title": "游戏剧情小说化分析",
  "turns": [
    {
      "index": 1,
      "export": "keep",
      "heading": "用 R8-5 样例测试剧情小说化回顾输出",
      "q": "以明日方舟 R8-5 文本为例，测试 LLM 能否整理剧情。",
      "a": "输出 R8-5 的成品样例，包含背景、情节和人物动机。",
      "note": "prototype sample"
    }
  ]
}
```

Rules:

- `turns[].index` is 1-based and refers to visible QA turns after hidden artifacts are filtered.
- `export: "exclude"` keeps the row in the turn index but omits the full turn body.
- Missing plan rows fall back to automatic short summaries; avoid this in final output.
- Use `--title` to override both share metadata and plan title.
- `heading`, `q`, `a`, and `note` should be semantic summaries of each turn's role in the conversation, not copied or truncated prompt text.

## Fallbacks

- If the backend JSON endpoint returns HTML or a challenge page, parse the full share HTML instead. The public page usually contains the conversation in `window.__reactRouterContext.streamController.enqueue(...)`.
- If the page cannot be fetched from the sandbox, rerun the fetch command with network approval.
- If no React Router stream is found, save the HTML and inspect it manually before inventing a parser. See `references/chatgpt-share-rsc.md` for the observed structure.
- If the output must preserve every internal event, do not use the base renderer. Save visible messages with `--messages-json` and inspect the original HTML/RSC payload separately.
