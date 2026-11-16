# Initialization Bootstrap Task Closure

## Trigger

For an authorized bootstrap under [Initialization Delivery](initialization-delivery.md), use `.trellis/tasks/00-bootstrap-guidelines/` for development-readiness acceptance and close it after the applicable checks. Read this procedure early enough to define that acceptance before implementation; do not wait until wrap-up to discover a product-code prerequisite. A read-only audit or an unrelated scoped enhancement does not trigger closure.

The bootstrap scope includes managing and archiving this initialization task. It does not authorize changing unrelated tasks or a Git commit. Preserve explicit user instructions to keep it open, report initialization incomplete, and reuse existing commit/install/archive authority without repeated questions. Reapplication does not reverse an earlier explicit decision to defer closure.

## Inspect Existing State

Before deciding to skip, inspect recorded archive attempts, archived tasks, pending archive changes, and Git history. If the move succeeded but the commit failed, verify that no archive commit exists and resume only the pending commit through the [archive retry procedure](chatgpt-codex-commit-trailer.md); do not archive again. If the archive/commit state is uncertain, report closure as blocked.

If the active directory is absent and no incomplete archive attempt remains, skip it with evidence. If an archive commit already exists, do not repeat archival or attribution; report missing attribution under the retry rules. Do not recreate an absent task or produce another archive commit. A skip satisfies only task disposition, not the other initialization deliverables.

## Stage-Appropriate Acceptance

Read the task record, original PRD/checklist, current source requirements and actual code/tooling. Record a project-specific acceptance section in this task's project-data PRD; do not rewrite upstream scaffold/spec templates or erase the original criteria. Map each original item to one disposition with evidence:

- **Delivered**: actual project rules/examples exist, and required current-stage checks passed.
- **Superseded**: an actionable project-owned policy demonstrably meets the same present need; link its path and loading evidence instead of filling a generic template merely for appearances.
- **Future-stage**: the item requires product code or infrastructure that is outside this bootstrap and does not yet exist. Record why, the next-task trigger, the responsible task/category and required later verification. Keep the original item unchecked and make clear that it is not delivered. This disposition completes only the initialization assessment of the item.
- **Unresolved**: a necessary current-stage requirement is missing, or an existing applicable command/integration is broken. This blocks closure.

For a PRD-only project, complete the applicable [delivery requirements](initialization-delivery.md): current requirements/mainline, original shared development rules, source-backed commands where they exist, policy loading, applicable integration setup, and repository delivery. Do not invent component, hook or state examples, choose an unrequested stack, or implement a frontend just to archive `00`. Label any adopted development defaults as decisions and any undecided conventions as unresolved future decisions, not observed code patterns.

Future-stage disposition is allowed within authorized bootstrap acceptance when it does not remove a user-required present deliverable. An existing test failure, missing UUPM setup that was authorized and required, or missing portable loading is not future-stage. Explicit user acceptance requiring real examples now cannot be weakened this way. Resolve it, obtain an actual scope decision, or transfer the work to a linked follow-up task with authorization. Do not create product tasks or silently change agreed acceptance to get a clean task list.

Store the acceptance mapping and concise checks in `00`, or link existing initialization-task evidence. Validate both implement/check context against the project policy. The task's present acceptance must be satisfied; future product work remains visibly undelivered and must be discoverable from the shared policy/mainline after archival.

## Archive And Verify

1. Apply the [submit-ready gate](submit-ready-human-review.md), current-stage delivery checks and [file policy](license-safe-file-policy.md). A task move changes context paths: inspect the installed archive behavior, then validate/update project-owned references after the move as needed.
2. Use the installed `task.py archive 00-bootstrap-guidelines` interface through the supported message/no-commit route in the [archive procedure](chatgpt-codex-commit-trailer.md). Honor commit authority and explicit staging paths, including a separately verified upstream initialization baseline when applicable. Do not include unrelated dirty files or patch the runtime.
3. Verify the archived path, status/date and removal from active tasks; verify the required archive commit and Codex trailer. Update mainline links, future obligations and actual closure evidence. Verify the final repository snapshot under the delivery procedure.
4. Report archived, skipped or blocked with evidence. An archive move with a pending required commit, or an unresolved delivery check, is partial progress. Do not report it as completed initialization.
