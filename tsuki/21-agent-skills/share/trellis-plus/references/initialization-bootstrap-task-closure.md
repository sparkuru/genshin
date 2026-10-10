# Initialization Bootstrap Task Closure

## Trigger

After `trellis init` and an authorized Trellis Plus application have completed with their applicable initialization/application checks, close `.trellis/tasks/00-bootstrap-guidelines/` as part of initialization wrap-up. A read-only audit or an unrelated scoped enhancement does not trigger closure.

Reuse existing initialization, archive, and commit authorization only for the actions each covers; initialization permission alone does not authorize a Git commit. Do not repeat approval requests already granted.

## Procedure

- Before deciding to skip, inspect any recorded archive attempt, archived task, pending archive changes, and Git history. If the move succeeded but the commit failed, verify that no archive commit exists and resume only the pending commit through the referenced retry procedure; do not archive again. If the archive/commit state is uncertain, report closure as blocked.

- If the active directory is absent and no incomplete archive attempt remains, skip it. If an archive commit already exists, do not repeat archival or attribution; report any missing attribution under the referenced retry rules. Do not recreate an absent task or produce another archive commit.

- Read its task record and PRD. Record the actual initialization result and project-specific policy paths. When those policies supersede the generic backend/frontend scaffold, say so and retain any unfulfilled checklist items unchecked. Preserve task history and distinguish supersession from completed generic guidelines. Block closure while substantive acceptance work remains unresolved. Resume only when it is completed, demonstrably superseded, or transferred with authorization to a linked follow-up task; record that disposition without marking undelivered work complete.

- Use the installed `task.py archive 00-bootstrap-guidelines` interface through the supported archive/message route in the [task-archive procedure](chatgpt-codex-commit-trailer.md). Apply the existing [submit-ready human review gate](submit-ready-human-review.md) before completion, staging, commit, or archive. Honor the existing checks, commit authority, explicit staging boundary and retry rules; never patch the runtime or include unrelated dirty files.

- Verify the archived path, status/date and removal from the active task list; verify the archive commit and applicable Codex trailer. Update existing mainline evidence and report archived, skipped, or blocked with its reason. Do not report a blocked closure as completed initialization wrap-up.
