# Katheryne Archive Instructions

## Scope

These instructions apply to every file under `katheryne/`.

Agents that support repository or directory-scoped `AGENTS.md` files should read and follow this file before creating, editing, moving, or exporting Markdown into this directory. If an agent or external tool does not implement `AGENTS.md` discovery, this file is not automatically enforced; in that case, include the filename rule explicitly in the export request.

## Purpose

This directory archives Markdown documents produced from agent conversations, learning sessions, shared ChatGPT exports, and local session exports.

The exporter or skill that creates a document owns the Markdown body structure. Do not rewrite generated content only to match this directory, unless the user explicitly asks for curation.

## Public Archive Safety

This repository is public. Before adding or replacing any Markdown document in this directory, agents must run the document through the `generalize-doc-content` workflow, or an equivalent manual generalization pass when that skill is unavailable.

The goal is to preserve reusable learning value while removing details that identify the original user, machine, private network, account, repository, incident, or one-off local setup.

Required import flow:

1. Generate the export draft using the appropriate source skill, such as `chatgpt-share-export` or `session-export`.
2. For exports produced by `chatgpt-share-export` or `session-export`, omit provenance metadata and per-turn timestamps at export time. Do not keep metadata only to later replace it with placeholders.
3. Generalize and desensitize the draft before committing it to this directory.
4. Preserve the useful teaching structure: symptoms, affected file categories, likely causes, diagnostic steps, repair steps, commands, and lessons learned.
5. Replace private concrete values with semantic placeholders, not vague redactions.
6. Remove credentials, tokens, cookies, private keys, passwords, and session secrets instead of placeholdering their exact values. Tell the user those values should be rotated if any were present.
7. Keep public product names, public tool names, public project names, file formats, and technical concepts when they are needed to understand the document.
8. Do not over-generalize away requirements that affect correctness.

Export presentation rules:

- `chatgpt-share-export` outputs must be rendered with `--exclude-section metadata --hide-timestamps`.
- `session-export` outputs must be rendered with `--exclude-section metadata --hide-timestamps`; keep `-q` when a quiet/readable transcript is enough.
- If the exporter accepts comma-separated sections, `--exclude-section metadata` is equivalent to the metadata part of `--exclude-section metadata,turn-index,qa-summary`; do not remove `turn-index` unless the user explicitly asks for no turn index.
- If a document was already exported with metadata or visible timestamps and the source transcript/share is still available, prefer regenerating it with the flags above.
- If regeneration is not practical, post-process only those presentation artifacts: remove the top `## Metadata` section or top metadata table, and remove right-aligned timestamp paragraphs under user/assistant turns. Do not rewrite the document body just to satisfy this rule.

Common replacements:

- Local user or host paths: `USERNAME`, `HOSTNAME`, `REPO-PATH`, `PROJECT-PATH`, `INPUT-PATH`, `OUTPUT-PATH`.
- Network details: `LAN-IP`, `PRIVATE-IP`, `SERVER-IP`, `DNS-SERVER`, `DOMAIN-NAME`, `PRIVATE-DOMAIN`, `HOSTNAME`.
- Accounts and identities: `ACCOUNT-NAME`, `EMAIL`, `ORG-NAME`, `USER-ID`.
- Secrets and session material: remove the value and use `API-KEY`, `TOKEN`, `COOKIE`, `PASSWORD`, or `PRIVATE-KEY` only as a category marker.
- One-off task details: `TASK-SUMMARY`, `INCIDENT-SUMMARY`, `PROJECT-NAME`, `SERVICE-NAME`, `CONFIG-FILE`.

For troubleshooting and engineering notes, prefer public reusable phrasing:

- Explain what kind of file or setting can cause the issue.
- Explain how to recognize the failure mode.
- Show command shapes with placeholders.
- Keep the reasoning and fix path, not the private target values.

Before reporting completion, check the final Markdown for obvious sensitive residue such as absolute home paths, private hosts, credentials, cookies, tokens, private URLs, exact private IPs, account identifiers, and copied conversation-only context.

## Filename Rule

All new Markdown documents in this directory must use:

```text
INDEX-MODEL-DOCNAME.md
```

Rules:

- `INDEX` must be a zero-padded sortable number such as `001`, `002`, or `003`.
- `MODEL` must be a lowercase model or agent family name such as `gpt`, `claude`, `glm`, `gemini`, `qwen`, or `kimi`.
- `DOCNAME` must be a lowercase kebab-case summary of the document topic.
- Use only ASCII letters, numbers, and hyphens in filenames.
- Do not overwrite an existing archive document. Pick the next available `INDEX`.

Examples:

```text
001-gpt-prompt-engineering-notes.md
002-claude-session-export-workflow.md
003-glm-agent-qa-archive.md
```
