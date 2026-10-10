# Trellis Update Revalidation

## Trigger

Read after `trellis update`, or when installed template/update state or provenance needs checking. Trellis may update project templates while preserving local edits through hash-based conflict handling and timestamped backups. Trellis Plus must keep its durable additions outside those template targets so an update does not turn them into mixed upstream files.

Read the [file policy](license-safe-file-policy.md) before selecting write targets. Template/update inspection does not authorize running an update or applying repairs during a read-only audit.

## Discovery And Revalidation

1. Check `.trellis/.version`, `.trellis/.template-hashes.json`, and recent `.trellis/.backup-*` directories when present. If the user just ran `trellis update`, inspect the newest backup for previously recorded Trellis Plus content before updating project-owned files; never restore it into a protected path.
2. Run or ask the user for `trellis update --dry-run` output when update state is unclear. Inspect the active protected files and newest `.trellis/.backup-*` snapshot read-only when provenance or update state is unclear.
3. Treat `.trellis/spec/**`, `.trellis/tasks/**`, and `.trellis/workspace/**` as user/project data, not normal template-overwrite targets. Prefer the dedicated `.trellis/spec/trellis-plus/` layer; treat existing spec indexes outside it as read-only unless their project authorship is proven and the user explicitly approves the mixed-file change.
4. Revalidate `.trellis/spec/trellis-plus/index.md`, its project-owned detail files, task context, and `.trellis/mainline.md`; do not restore a previous customization into a protected Trellis file. Verify loading through [Project Policy Loading And Generalization](project-policy-loading.md).
5. If an update removes behavior that used to be injected through `workflow.md`, do not recreate that pointer automatically. The shared project configuration remains the source of truth for the next Trellis Plus run.
6. If an update changes UUPM, Playwright, or wrapper paths, update only the project-owned policy/profile and preserve the user's existing test, fixture, wrapper, and personal configuration files.
7. Do not add protected Trellis files to `update.skip` as part of this skill. If the user deliberately maintains a fork, handle it as a separate license-aware maintenance decision.

Report template-target risk, inspected version/backup evidence, any recovery used, revalidated policy/context paths, and remaining gaps. Keep an audit read-only; apply only authorized project-owned repairs.
