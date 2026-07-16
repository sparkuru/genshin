---
name: trellis-plus
description: Enhances an existing or newly initialized Trellis workflow with project-specific conventions. Use when the user asks to apply `trellis-plus`, improve Trellis templates, inject durable Trellis workflow rules, add submit-ready human review gates, add ChatGPT/Codex commit completion summaries and co-author trailers, bootstrap Docker-based dev commands, integrate UI/UX Pro Max (UUPM) for frontend projects, or make a Trellis project infer its testing and feedback process from the repository.
---

# Trellis Plus

## Purpose

Use this skill to customize a repository's Trellis workflow after `trellis init` or after a task already has partial results.

The job is to inspect the project, infer how mature validation should work, then inject durable rules into Trellis project-level files so later Trellis tasks inherit them automatically.

## Operating Rules

- Modify project-level Trellis templates and specs, not one-off active task notes, unless the user explicitly asks for a task-local patch.
- Preserve existing Trellis wording and state names. Add small, clearly titled sections instead of rewriting the whole workflow.
- Prefer repository evidence over generic advice: package files, test scripts, CI files, existing test directories, docs, and the current task's PRD/check context.
- Classify whether the repository or active task has a frontend/UI surface before applying frontend-specific enhancements. Do not trigger UI/UX Pro Max (UUPM) for a backend-only project merely because it contains a package manifest.
- If a frontend/UI project has no project-local UI/UX Pro Max initialization for the active AI platform, ask the user whether to initialize it before running UUPM commands or adding UUPM-derived design artifacts. Do not silently install or overwrite it.
- If there is no `.trellis/` directory, stop after reporting that Trellis has not been initialized.
- If there are unrecognized local changes, do not overwrite them. Read the affected files and patch around the user's work.
- Before modifying agent-specific or platform-specific files, inspect their tracked/ignored state, Trellis delegation, existing project convention, and user intent. Apply the narrowest suitable change and report its version-control effect.
- After `trellis update`, reapply Trellis Plus to affected customizations that were overwritten, skipped, or emitted as `.new`.

## Discovery Workflow

1. Locate Trellis files:
   - `.trellis/workflow.md`
   - `.trellis/spec/**/index.md`
   - `.trellis/tasks/**/task.json`
   - agent templates or platform configuration when Trellis refers to them
2. Classify Trellis-managed update state:
   - Check `.trellis/.version`, `.trellis/.template-hashes.json`, and recent `.trellis/.backup-*` directories when present.
   - If the user just ran `trellis update`, inspect the newest backup for previously injected Trellis Plus blocks before patching.
   - Treat `.trellis/spec/**`, `.trellis/tasks/**`, and `.trellis/workspace/**` as user/project data, not normal template-overwrite targets.
3. Identify the active or latest task:
   - Prefer Trellis runtime pointers when present.
   - Otherwise inspect non-archived `.trellis/tasks/*/task.json`.
   - Note current status: `planning`, `in_progress`, `completed`, or project-specific variants.
4. Infer project validation:
   - Read manifest and CI files such as `package.json`, `pnpm-lock.yaml`, `pyproject.toml`, `Cargo.toml`, `go.mod`, `Makefile`, `.github/workflows/*`, `justfile`, and existing docs.
   - Identify lint, format, type-check, unit, integration, e2e, build, smoke, visual, device, or manual validation commands.
   - Distinguish commands the agent can run from checks that require the user's environment, credentials, GUI inspection, hardware, production-like data, or paid/external services.
   - Classify frontend/UI presence and record the evidence used: frontend framework dependencies, UI source files, frontend scripts/configuration, mobile UI targets, or an explicit UI requirement in the active task.
   - Check whether UI/UX Pro Max is initialized in the project for the active platform. A global installation does not count as project initialization.
5. Infer dev-command wrapper state:
   - Check for `hako`, `dev`, `.devhome`, and active-platform configuration needed for local wrapper approval.
   - If no dev wrapper exists and the project has a clear toolchain, prepare to apply the Docker dev-wrapper enhancement.
6. Infer commit attribution style:
   - Read `git log --format=%B -n 20` or equivalent recent history.
   - Check whether larger AI-assisted commits use detailed completion bodies before their `Co-authored-by` / `Co-Authored-By` trailers.
   - Preserve an existing project-specific Codex/OpenAI trailer if one is already established.
7. Select enhancement references:
   - If the user invokes `$trellis-plus` without narrowing the scope, read every file in the Default Enhancement Set below and apply all of them.
   - If the user asks for a specific enhancement, read only that enhancement's reference file.
   - If a reference file named in the registry is missing, report that exact missing path before patching.
8. Patch durable Trellis files and summarize:
   - files changed
   - rules injected
   - inferred validation profile
   - dev wrapper state and auto-allow target
   - inferred commit attribution trailer
   - version-control handling for any agent-specific or platform-specific target changed
   - `trellis update` risk: whether any patched file is a Trellis template target and whether backup recovery was used
   - any manual follow-up the next Trellis task should request

## Enhancement Registry

Default Enhancement Set:

- **Submit-ready human review gate**: read `references/submit-ready-human-review.md` when adding rules for the moment a Trellis task is implemented, checked, and ready to commit.
- **ChatGPT/Codex commit completion summary and co-author trailer**: read `references/chatgpt-codex-commit-trailer.md` when adding commit body and attribution rules for commits made during Trellis Phase 3.4.
- **Docker dev-command bootstrap**: read `references/dev-it-in-docker-bootstrap.md` when adding a before-dev/init checkpoint that creates a `hako` dev wrapper and writes matching agent auto-allow rules.
- **UI/UX Pro Max frontend integration**: read `references/ui-ux-pro-max-integration.md` when the repository or active task has a frontend/UI surface. This enhancement owns the initialization prompt and the UUPM Plan → Implement → Check → Update Spec workflow.

Future enhancements should be added as separate files under `references/` and listed in this registry with a one-line loading rule.

## Injection Targets

Use the narrowest durable target that exists in the project:

- Add state-machine behavior to `.trellis/workflow.md` when the rule must apply every time the workflow reaches a phase.
- Add review or validation expectations to an existing `.trellis/spec/**/index.md` when the rule is a reusable project convention.
- Add agent-specific wording only when Trellis delegates that exact phase to the target file and the repository's convention supports it.
- Add frontend planning wording to the project's plan/brainstorm skill or equivalent when it exists; otherwise add a short pointer to `.trellis/workflow.md`. Keep UUPM's detailed procedure in its reference file.
- Add commit-command wording to the Phase 3.4 section of `.trellis/workflow.md` when the rule changes how work commits are drafted or executed.

Keep reusable phase behavior in `.trellis/workflow.md` and project conventions in `.trellis/spec/**`. Handle agent-specific and platform-specific files according to their role in the active project rather than a fixed directory policy.

Do not create a parallel Trellis framework. Extend the installed one.

## Update Resilience

Trellis may update project templates while preserving local edits through hash-based conflict handling and timestamped backups. Treat Trellis Plus blocks as project customizations that may be prompted, skipped, copied to `.new`, or overwritten with `trellis update -f`.

When applying Trellis Plus after an update:

- Run or ask the user for `trellis update --dry-run` output when update state is unclear.
- Inspect the active files and the newest `.trellis/.backup-*` snapshot for prior `Trellis Plus:` sections.
- Reapply the enhancement to the current active file, adapting to the updated upstream wording instead of restoring the old file wholesale.
- If an update removes a UUPM workflow pointer, reapply the pointer without silently rerunning `uipro init` or overwriting the project-local UUPM installation. Ask again only when the project-local installation is actually absent or incomplete.
- Do not add `.trellis/workflow.md` to `update.skip` by default; that prevents upstream workflow fixes from landing. Use `update.skip` only when the user deliberately forks a target and accepts manual merges after each Trellis update.

## Expected Result

After applying this skill with the default enhancement set, a future Trellis run should:

- automatically pause or explicitly continue at submit-ready time with a concrete human feedback request, based on project-specific validation evidence
- ensure the project has a Docker-backed dev command wrapper or a before-dev checkpoint that can bootstrap one
- detect frontend projects and ask before initializing project-local UI/UX Pro Max when it is absent
- use UI/UX Pro Max design-system output as shared task context for frontend implementation and verification
- decide whether each Phase 3.4 work commit deserves ChatGPT/Codex co-author attribution
- draft a useful task completion summary body for commits above that threshold
- add the ChatGPT/Codex co-author trailer only when that attribution threshold is met
