# ChatGPT/Codex Commit Completion Summary And Co-Author Trailer

## Goal

Inject a durable Trellis rule so work commits created by ChatGPT/Codex during Trellis Phase 3.4 decide whether they deserve a detailed task completion summary and AI co-author trailer, mirroring Claude Code's selective commit behavior.

Default trailer:

```text
Co-authored-by: OpenAI Codex <codex@openai.com>
```

Use this exact default when attribution is warranted, unless the project already has a clear local convention for Codex/OpenAI attribution.

## Background

Trellis itself does not add the Claude footer. Trellis puts work commits in `.trellis/workflow.md` Phase 3.4: inspect dirty state, learn recent commit style, classify AI-edited vs unrecognized files, draft a batched commit plan, ask for one-shot confirmation, then run `git add` and `git commit`.

`finish-work` is later bookkeeping. It refuses to replace Phase 3.4 when current-task code is still dirty, then archives tasks and records the journal with the work-commit hashes.

Therefore, inject this rule into the Phase 3.4 commit step, before the `git commit` commands are executed.

In observed Trellis history, Claude-style attribution is not applied to every work commit. It appears mainly on larger task commits with substantial bodies, non-trivial implementation reasoning, cross-layer changes, or explicit validation narratives. Small follow-up feature/fix commits, task archive commits, and journal commits often omit it. Match that selective pattern.

The long body matters as much as the trailer. Those commits read like a compact task-completion report: what broke or was requested, what changed, which architectural boundary was preserved, how it was validated, and what remains out of scope. The user can approve the commit after skimming that report instead of re-deriving the whole task from the diff.

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

## Attribution Threshold

For each proposed Phase 3.4 work commit, classify AI attribution as `yes`, `no`, or `ask`.

Use `yes` when ChatGPT/Codex made a substantial author-level contribution, such as:

- implementing a full Trellis task or a meaningful slice of a larger task
- changing behavior across multiple files, packages, layers, protocols, schemas, or UI states
- designing or debugging non-obvious logic, not merely applying a direct edit
- producing a commit body that explains rationale, edge cases, and validation results
- adding significant tests, validation strategy, or research-backed implementation
- generating or restructuring enough code that omitting AI attribution would hide material authorship
- the user explicitly asks for AI attribution

Use `no` when the change is small or mostly mechanical, such as:

- one-shot typo, formatting, copy, comment, or trivial docs changes
- narrow config tweaks, dependency metadata, ignore-list changes, or simple script edits
- small follow-up fixes after the main task is already committed
- Trellis template/skill housekeeping that does not materially change project behavior
- exact user-directed edits where the agent mostly executed instructions
- commits containing only user-authored or unrecognized dirty files
- Trellis auto-commits created by `task.py archive`
- Trellis auto-commits created by `add_session.py`
- commits the user says they will make manually

Use `ask` only when recent project history has a clear but ambiguous local convention and the current commit sits near the threshold. Otherwise, prefer `no` over noisy over-attribution.

Do not equate "ChatGPT/Codex touched a file" with "add the trailer". The threshold is material authorship, not file edit involvement.

## Completion Summary Body

When attribution is `yes`, write a commit body that summarizes the completed Trellis task. Keep it dense and reviewable, not ceremonial.

Include the parts that apply:

- original problem, product request, or bug symptom
- root cause or key design reason when non-obvious
- implementation summary grouped by subsystem, layer, or user-visible behavior
- important constraints preserved, such as no protocol change, no store mutation, no auth bypass, or no UI regression
- tests, lint, type-check, build, manual/browser/device validation, and known skipped checks
- explicit out-of-scope or known follow-up only when it affects future work

Match local commit style:

- If recent large AI-assisted commits use Chinese bodies, write Chinese bodies.
- If they use English bodies, write English bodies.
- If they use terse bullets, use terse bullets.
- If they use dense paragraphs, use dense paragraphs.

Do not pad small commits into fake summaries. If the body would only say "updated file X", keep the commit subject-only and omit the trailer.

## Body Length Guidance

Use the smallest body that preserves review value:

- **Small/no attribution**: subject only, or one short body paragraph if local style requires it.
- **Medium attribution**: 1-3 short paragraphs or 3-5 bullets covering change and validation.
- **Large task attribution**: multi-paragraph body like the local Claude commits, covering problem/root cause, implementation, boundaries, and validation.

The body should explain why this commit is complete, not narrate every edit.

## When To Add The Trailer

Add the trailer only to work commits classified `yes`.

Do not add the trailer to:

- Trellis auto-commits created by `task.py archive`
- Trellis auto-commits created by `add_session.py`
- commits the user says they will make manually

If a commit mixes AI-edited and user-edited files after explicit user confirmation, include the AI trailer only when the AI contribution still meets the threshold. Keep the user as the primary git author/committer.

## Commit Plan Behavior

When drafting the Phase 3.4 commit plan, show attribution only where it matters:

- For `yes`, show the trailer, a short attribution reason, and a commit body preview.
- For `ask`, ask one concise question before committing.
- For `no`, omit the trailer line unless the user asked for an attribution audit.

Recommended plan shape:

```markdown
Proposed commits (in order):
  1. <message>
     - <file>
     - <file>
     AI attribution: yes - substantial cross-layer implementation
     body: includes problem/root cause, implementation summary, validation, and preserved boundaries
     trailer: Co-authored-by: OpenAI Codex <codex@openai.com>

  2. <message>
     - <file>
     - <file>

Unrecognized dirty files (NOT in any commit - confirm include/exclude):
  - <file>

Reply 'ok' / '行' to execute. Reply with edits, or '我自己来' / 'manual' to abort.
```

If a project already uses multi-line commit bodies, place the trailer after the body with one blank line before the trailer.

## Command Form

Prefer a command form that cannot lose body paragraphs or the blank line before the trailer.

For an attributed commit with no body beyond the trailer:

```bash
git commit -m "<subject>" -m "Co-authored-by: OpenAI Codex <codex@openai.com>"
```

For a commit with a body:

```bash
git commit -m "<subject>" -m "<body>" -m "Co-authored-by: OpenAI Codex <codex@openai.com>"
```

Do not append the trailer into the subject line.

For a longer Claude-style summary, use a commit message file when quoting would be fragile:

```bash
git commit -F /tmp/trellis-commit-message.txt
```

The file content should be:

```text
<subject>

<task completion summary body>

Co-authored-by: OpenAI Codex <codex@openai.com>
```

## Suggested Template Block

Adapt this block to the local `.trellis/workflow.md` Phase 3.4 wording:

```markdown
**AI co-author trailer**:
Before creating each Phase 3.4 work commit, decide whether ChatGPT/Codex made a substantial author-level contribution. For commits above that threshold, write a useful task completion summary body and add this trailer:

`Co-authored-by: OpenAI Codex <codex@openai.com>`

The body should summarize the problem/request, root cause or design rationale when relevant, implementation by subsystem, preserved boundaries, and validation results. Show a commit body preview, the trailer, and a short attribution reason in the proposed commit plan before asking for confirmation. Do not add attribution merely because Codex touched a file, and do not invent a long body for small commits. Omit it for small/mechanical follow-ups, user-authored/unrecognized files, and `/finish-work` archive or journal commits. Preserve any existing project-specific Codex/OpenAI trailer convention if recent history already uses one.
```

## Verification After Injection

After patching, verify:

- the rule is in or pointed from `.trellis/workflow.md` Phase 3.4
- the rule applies before `git commit`
- the rule has a threshold and does not add trailers to every Codex-touched commit
- substantial attributed commits get a task completion summary body, not just a trailer
- the default trailer is exactly `Co-authored-by: OpenAI Codex <codex@openai.com>`
- archive and journal commits are excluded
- the commit plan shows the body preview and trailer only when attribution is warranted
