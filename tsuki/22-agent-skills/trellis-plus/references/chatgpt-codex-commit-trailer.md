# ChatGPT/Codex Commit Co-Author Trailer

## Goal

Inject a durable Trellis rule so work commits created by ChatGPT/Codex during Trellis Phase 3.4 include an AI co-author trailer, mirroring Claude Code's commit attribution behavior.

Default trailer:

```text
Co-authored-by: OpenAI Codex <codex@openai.com>
```

Use this exact default unless the project already has a clear local convention for Codex/OpenAI attribution.

## Background

Trellis itself does not add the Claude footer. Trellis puts work commits in `.trellis/workflow.md` Phase 3.4: inspect dirty state, learn recent commit style, classify AI-edited vs unrecognized files, draft a batched commit plan, ask for one-shot confirmation, then run `git add` and `git commit`.

`finish-work` is later bookkeeping. It refuses to replace Phase 3.4 when current-task code is still dirty, then archives tasks and records the journal with the work-commit hashes.

Therefore, inject this rule into the Phase 3.4 commit step, before the `git commit` commands are executed.

## Trailer Selection

Use GitHub's standard co-author trailer shape:

```text
Co-authored-by: Name <email@example.com>
```

Observed public Codex/OpenAI commit trailers include:

- `Co-authored-by: OpenAI Codex <codex@openai.com>`
- `Co-authored-by: Codex <codex@openai.com>`
- `Co-authored-by: Codex <noreply@openai.com>`

Prefer `OpenAI Codex <codex@openai.com>` because it is explicit, vendor-scoped, and appears in public Codex-authored commit history. Preserve a project's existing convention if recent commits already use a different Codex/OpenAI trailer.

Do not use the user's Git identity for the AI trailer.

## When To Add The Trailer

Add the trailer to every work commit that contains files edited by ChatGPT/Codex in the current Trellis session.

Do not add the trailer to:

- commits containing only user-authored or unrecognized dirty files
- Trellis auto-commits created by `task.py archive`
- Trellis auto-commits created by `add_session.py`
- commits the user says they will make manually

If a commit mixes AI-edited and user-edited files after explicit user confirmation, include the AI trailer and keep the user as the primary git author/committer.

## Commit Plan Behavior

When drafting the Phase 3.4 commit plan, show the trailer in each proposed commit entry so the user can see it before approving.

Recommended plan shape:

```markdown
Proposed commits (in order):
  1. <message>
     - <file>
     - <file>
     trailer: Co-authored-by: OpenAI Codex <codex@openai.com>

Unrecognized dirty files (NOT in any commit - confirm include/exclude):
  - <file>

Reply 'ok' / '行' to execute. Reply with edits, or '我自己来' / 'manual' to abort.
```

If a project already uses multi-line commit bodies, place the trailer after the body with one blank line before the trailer.

## Command Form

Prefer a command form that cannot lose the blank line before the trailer.

For a subject-only commit:

```bash
git commit -m "<subject>" -m "Co-authored-by: OpenAI Codex <codex@openai.com>"
```

For a commit with a body:

```bash
git commit -m "<subject>" -m "<body>" -m "Co-authored-by: OpenAI Codex <codex@openai.com>"
```

Do not append the trailer into the subject line.

## Suggested Template Block

Adapt this block to the local `.trellis/workflow.md` Phase 3.4 wording:

```markdown
**AI co-author trailer**:
When ChatGPT/Codex creates a work commit for files it edited in this Trellis session, include this trailer in the commit message:

`Co-authored-by: OpenAI Codex <codex@openai.com>`

Show the trailer in the proposed commit plan before asking for confirmation. Add it only to Phase 3.4 work commits, not to `/finish-work` archive or journal commits. Preserve any existing project-specific Codex/OpenAI trailer convention if recent history already uses one.
```

## Verification After Injection

After patching, verify:

- the rule is in or pointed from `.trellis/workflow.md` Phase 3.4
- the rule applies before `git commit`
- the default trailer is exactly `Co-authored-by: OpenAI Codex <codex@openai.com>`
- archive and journal commits are excluded
- the commit plan tells the user which trailer will be used
