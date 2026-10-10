# Task-Archive Completion Summary And Codex Co-Author Trailer

## Goal And Trigger

Record Codex attribution once per task, at successful task archival. The archive commit is the attribution anchor for the completed task, regardless of task size. Ordinary implementation, fix, checkpoint, and separate journal commits do not acquire a trailer through this rule.

Use this exact trailer in the commit message, separated from its body by a blank line:

```text
Co-authored-by: OpenAI Codex <codex@openai.com>
```

This rule applies to tasks completed with ChatGPT/Codex participation. Do not attribute someone else's historical work merely because Codex later inspects or moves its task record. An explicit user attribution instruction takes precedence. Keep the user's Git author/committer identity unchanged.

## Discover The Actual Archive Path

Read the installed workflow and archive command implementation/help before choosing commands. Do not assume a Trellis version, phase number, option name, automatic staging scope, or commit-message extension point.

Read `git log --format=%B -n 20` or equivalent recent history to establish the repository's message language/style and existing archive attribution.

Record in the project-owned commit policy:

- archive command and whether it commits automatically;
- supported way to supply the archive commit message, or to disable its automatic commit and create the archive commit explicitly;
- exact archive paths and other task bookkeeping paths it changes/stages;
- separate journal command and its commit behavior;
- the command used to inspect the resulting commit message and paths.

Choose the first supported route:

1. If the normal archive command accepts a message or trailer through a documented interface, supply the completion message through that interface.
2. Otherwise, if the command supports disabling its auto-commit, use that mode, verify successful archive state, and commit only the explicit archive and related project-owned task paths with the prepared message.
3. If neither route exists, report `archive-attribution-blocked` before running the archive command. Name the missing capability and continue any independent authorized work. Obtain direction for this specific integration gap; do not silently archive without the promised attribution or claim it succeeded.

Never invent flags, patch protected Trellis runtime, install a global Git hook, rewrite an existing commit, or create an empty attribution-only commit to make the rule appear implemented. A runtime fork or history rewrite requires a separate explicit request. An existing supported project adapter may be reused.

## Archive Procedure

1. Read the shared policy, task PRD, actual validation results, work-commit references, Git status, and archive evidence. Finish the normal task checks and any required review before archiving. Honor existing commit/archive authorization; do not request it again when already granted.
2. Confirm the task is not already archived and attributed. Prepare one archive commit per task. If the installed command batches tasks, use its supported single-task path or report that limitation rather than fabricating commits.
3. Draft a task completion summary: requested outcome, delivered behavior, relevant validation and limitations, task identity, and work-commit links when available. Scale the body to the task; a small task may need only one sentence. Attribution does not require a long body or a contribution-size threshold.
4. Show the message and explicit candidate paths as part of the normal archive plan. Check the license-safe staging boundary, including any paths staged internally by the archive command. Do not collect unrelated dirty files.
5. Execute the supported archive route. Only successful archive state may receive the task's archive attribution commit. On partial failure, inspect state and commits before retrying; do not repeat the archive blindly.
6. Inspect the resulting commit message and changed paths. Verify exactly one matching Codex trailer, the correct task, and successful archive evidence. Update mainline evidence with the archive path and commit reference. A later mainline or journal-only commit does not repeat the trailer.

Do not amend old work commits to add task-level attribution. Preserve other valid co-author trailers, and deduplicate an already present matching trailer. Re-running finish-work for an already archived task must not produce another attribution commit when its archive commit already exists. If archival succeeded with auto-commit disabled but the explicit commit failed, inspect the recorded attempt, archived task, pending archive changes, and Git history. Resume only the pending explicit commit after verifying it has not already been created; do not rerun archive or collect new unrelated changes. If an archive commit already exists without a trailer, report the missing attribution without repairing history automatically.

## Message Shape

Use the repository's language and subject style. Prefer a temporary message file with `git commit -F` when explicitly creating the archive commit; keep the file outside tracked project paths and remove it after use.

```text
<archive subject identifying TASK-ID>

<completed outcome; actual validation and any material limitation>
<work-commit references when available>

Co-authored-by: OpenAI Codex <codex@openai.com>
```

Implementation commits can still carry useful change and validation summaries; the absence of a trailer does not require subject-only commits.

## Project Injection And Verification

Write the rule and repository-confirmed archive route to `.trellis/spec/trellis-plus/commit-policy.md`, linked by the shared index. Reuse an existing equivalent project-owned detail file instead of duplicating it. The main session reads it before archive; add its path to existing task context when another agent performs completion work. A spec is guidance, not a Git hook: verify the loading path through [Project Policy Loading And Generalization](project-policy-loading.md).

Before reporting integration complete, check these scenarios:

- several work commits followed by one task archive: only the archive commit receives the trailer;
- a small Codex-assisted task: archive attribution still applies;
- separate archive and journal commits: only the archive commit is attributed;
- a failed archive or unavailable message interface: no false success;
- repeated finish-work: no second archive or duplicate trailer;
- an unrelated user-authored task: no invented Codex authorship;
- protected runtime, unrelated work, Git identity, and existing history remain unchanged.
