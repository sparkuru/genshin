---
name: trellis-plus
description: Enhances an existing or newly initialized Trellis workflow through project-owned shared configuration and personal execution settings. Use when the user asks to apply `trellis-plus`, maintain an approved project mainline across task boundaries, add Playwright-based frontend validation, add submit-ready human review gates, add ChatGPT/Codex commit completion summaries and co-author trailers, bootstrap Docker-based dev commands, integrate UI/UX Pro Max (UUPM) for frontend projects, or make a Trellis project infer its testing and feedback process from the repository.
---

# Trellis Plus

## Purpose

Use this skill to improve a repository's Trellis workflow after `trellis init` or after a task already has partial results.

The job is to inspect the project, infer how mature validation and continuity should work, then record durable rules in project-owned configuration and task data so later Trellis Plus runs can reuse them.

## Operating Rules

- Before any write, read `references/license-safe-file-policy.md` and classify the target as protected Trellis material, project-shared configuration, personal/local configuration, or ordinary project code.
- Do not modify, replace, copy, or rewrite protected Trellis material. Use the dedicated project-owned `.trellis/spec/trellis-plus/` layer for durable shared rules instead of injecting them into Trellis's upstream workflow or runtime files.
- Treat new project-authored specs and task records as project data. Do not copy Trellis, UUPM, or another tool's source text/code into them unless its source and license permit that exact use.
- Preserve existing Trellis wording and state names. Add small, clearly titled sections instead of rewriting the whole workflow.
- Prefer repository evidence over generic advice: package files, test scripts, CI files, existing test directories, docs, and the current task's PRD/check context.
- Treat `.trellis/` project data as shared and normally trackable, while `.agents/`, `.codex/`, `.claude/`, `.opencode/`, and other platform settings are personal/local and untracked. Preserve the repository's existing ignore behavior. Trellis Plus never stages personal/local files and never uses `git add -f`, `git add --force`, `git add .`, `git add -A`, or an equivalent broad/forced staging operation to collect them.
- Keep the tracked `.trellis/spec/trellis-plus/` configuration as the single project-wide source of truth. Personal settings may add only narrow local execution rules and must not duplicate project policy.
- Classify whether the repository or active task has a frontend/UI surface before applying frontend-specific enhancements. Do not trigger UI/UX Pro Max (UUPM) for a backend-only project merely because it contains a package manifest.
- For browser-automatable frontend work, prefer a reproducible Playwright validation over asking the user to perform a generic smoke test. Retain human review only for the residual judgment or environment the agent cannot test effectively.
- If a frontend/UI project has no project-local UI/UX Pro Max initialization for the active AI platform, ask the user whether to initialize it before running UUPM commands or adding UUPM-derived design artifacts. Do not silently install or overwrite it.
- If there is no `.trellis/` directory, stop after reporting that Trellis has not been initialized.
- If there are unrecognized local changes, do not overwrite them. Read the affected files and patch around the user's work.
- After `trellis update`, revalidate project-owned Trellis Plus configuration and task context; never restore it into a protected upstream file.

## License-Safe Write Boundary

The exact file policy is in `references/license-safe-file-policy.md`; it is part
of this skill's required procedure, not optional background reading.

Trellis upstream is AGPL-licensed. A project can contain independent
project-authored files alongside it, but a file that copies from or modifies an
upstream Trellis file must retain the applicable upstream license and notices.
File location alone does not make copied material project-owned.

Use this split:

1. **Project-shared configuration**: create or update
   `.trellis/spec/trellis-plus/index.md` and new detail files in that directory;
   keep task-specific decisions and evidence in `.trellis/tasks/<TASK-ID>/`, and
   use `.trellis/mainline.md` for an approved project initiative.
2. **Personal/local configuration**: write narrow agent rules only in the
   active platform's local configuration (`.codex/`, `.claude/`, `.agents/`, or
   `.opencode/`) and leave those paths untracked. Trellis Plus never stages
   personal/local files; a user-requested tracking exception is a separate
   manual license and secrets review.
3. **Protected Trellis material**: read `.trellis/workflow.md`,
   `.trellis/scripts/**`, `.trellis/agents/**`, `.trellis/config.yaml`, update
   metadata, and Trellis-managed platform files, but never patch them in the
   normal Trellis Plus flow.

Do not promise that a rule is automatically enforced by every Trellis phase
when the protected workflow file was not changed. Instead, read the shared
configuration at the start of each Trellis Plus run and add that path to active
task implement/check context using Trellis's existing context mechanism. This
keeps the repository-consistent policy in a trackable project file without
making it a modified Trellis runtime file.

Before staging, inspect the complete candidate path list. If a proposed change
contains a protected or personal path, stop or remove it from the commit plan;
never silently stage it. If the user explicitly requests a protected-file fork,
report the licensing/notice boundary and wait for a license-aware decision
instead of writing automatically.

## Discovery Workflow

1. Locate Trellis files:
   - `.trellis/workflow.md`
   - `.trellis/mainline.md` when present
   - `.trellis/spec/trellis-plus/index.md` when present
   - `.trellis/spec/**/index.md`
   - `.trellis/tasks/**/task.json`
2. Classify Trellis-managed update state:
   - Check `.trellis/.version`, `.trellis/.template-hashes.json`, and recent `.trellis/.backup-*` directories when present.
   - If the user just ran `trellis update`, inspect the newest backup for previously recorded Trellis Plus content before updating project-owned files; never restore it into a protected path.
   - Treat `.trellis/spec/**`, `.trellis/tasks/**`, and `.trellis/workspace/**` as user/project data, not normal template-overwrite targets; prefer a new `.trellis/spec/trellis-plus/` layer over changing an existing generated index. Treat existing spec indexes outside that dedicated layer as read-only unless their project authorship is proven and the user explicitly approves the mixed-file change.
   - Treat `.trellis/workflow.md`, `.trellis/scripts/**`, `.trellis/agents/**`, `.trellis/config.yaml`, update metadata, and managed platform files as read-only protected material.
   - Locate existing `LICENSE*`, `COPYING*`, `NOTICE*`, Trellis `COPYRIGHT`, or package license metadata without editing them. If protected Trellis files are present but their applicable notice is absent or unknown, record `license-notice-needed` and do not stage those files.
3. Identify the active or latest task:
   - Prefer Trellis runtime pointers when present.
   - Otherwise inspect non-archived `.trellis/tasks/*/task.json`.
   - Note current status: `planning`, `in_progress`, `completed`, or project-specific variants.
   - When adding mainline continuity, read the mainline record, parent/child task evidence, archive evidence, git state, and available validation results before recommending a next action.
4. Infer project validation:
   - Read manifest and CI files such as `package.json`, `pnpm-lock.yaml`, `pyproject.toml`, `Cargo.toml`, `go.mod`, `Makefile`, `.github/workflows/*`, `justfile`, and existing docs.
   - Identify lint, format, type-check, unit, integration, e2e, build, smoke, visual, device, or manual validation commands.
   - Distinguish commands the agent can run from checks that require the user's environment, credentials, GUI inspection, hardware, production-like data, or paid/external services.
   - Classify frontend/UI presence and record the evidence used: frontend framework dependencies, UI source files, frontend scripts/configuration, mobile UI targets, or an explicit UI requirement in the active task.
   - For frontend/UI work, inspect for `@playwright/test`, `playwright.config.*`, Playwright scripts, browser-test directories, test fixtures, screenshot baselines, and CI browser-install steps. Decide whether the changed acceptance criteria can be exercised against a local or test deployment without private credentials or real devices.
   - If another browser-test runner is already the project convention, record whether it provides equivalent coverage; do not silently migrate or duplicate the suite merely to introduce Playwright.
   - Read any existing `Trellis Plus: Playwright Validation Profile` before consulting external Playwright documentation. Reconcile its exact commands and constraints with current repository evidence, then update it only when a durable convention changed.
   - Check whether UI/UX Pro Max is initialized in the project for the active platform. A global installation does not count as project initialization.
5. Infer dev-command wrapper state:
   - Check for dev wrapper and `.devhome`.
   - If no dev wrapper exists and the project has a clear toolchain, prepare to apply the Docker dev-wrapper enhancement.
6. Infer commit attribution style:
   - Read `git log --format=%B -n 20` or equivalent recent history.
   - Check whether larger AI-assisted commits use detailed completion bodies before their `Co-authored-by` / `Co-Authored-By` trailers.
   - Preserve an existing project-specific Codex/OpenAI trailer if one is already established.
7. Select the write boundary:
   - Read `references/license-safe-file-policy.md`.
   - Create or update only the project-shared configuration and task data needed by the selected enhancement.
   - Keep agent allow rules and other machine-specific settings in personal/local files, untracked by default.
   - If the selected enhancement would require a protected Trellis file, stop and report the target rather than patching it.
8. Select enhancement references:
   - If the user invokes `$trellis-plus` without narrowing the scope, read every file in the Default Enhancement Set below and apply all of them.
   - If the user asks for a specific enhancement, read only that enhancement's reference file.
   - If a reference file named in the registry is missing, report that exact missing path before patching.
9. Write only classified targets and summarize:
   - files changed
   - protected files inspected but not changed
   - Trellis license/notice status (`present`, `missing`, or `unknown`)
   - project-shared versus personal/local files
   - explicit paths proposed for `git add`, or why no staging is allowed
   - rules injected
   - inferred validation profile
   - Playwright execution mode and profile location when browser validation applies
   - dev wrapper state and auto-allow target
   - inferred commit attribution trailer
   - mainline continuity mode, current initiative, and any decision required before work may continue
   - `trellis update` risk: whether any patched file is a Trellis template target and whether backup recovery was used
   - any manual follow-up the next Trellis task should request

## Enhancement Registry

Default Enhancement Set:

- **License-safe file policy**: always read `references/license-safe-file-policy.md` before any write, staging, or commit recommendation.
- **Submit-ready human review gate**: read `references/submit-ready-human-review.md` when adding rules for the moment a Trellis task is implemented, checked, and ready to commit.
- **ChatGPT/Codex commit completion summary and co-author trailer**: read `references/chatgpt-codex-commit-trailer.md` when adding commit body and attribution rules for commits made during Trellis Phase 3.4.
- **Docker dev-command bootstrap**: read `references/dev-it-in-docker-bootstrap.md` when adding a before-dev/init checkpoint that creates a `hako` dev wrapper and writes matching agent auto-allow rules.
- **UI/UX Pro Max frontend integration**: read `references/ui-ux-pro-max-integration.md` when the repository or active task has a frontend/UI surface. This enhancement owns the initialization prompt and the UUPM Plan → Implement → Check → Update Spec workflow.
- **Playwright automated frontend validation**: read `references/playwright-automated-validation.md` when the repository or active task has a browser-accessible UI change. This enhancement owns the automate-first decision, Playwright test evidence, and residual manual-review handoff.
- **Mainline continuity**: read `references/mainline-continuity.md` when adding a durable project direction record and safe no-task continuation policy. This default enhancement owns the read-only Project Pulse, continuation authorization boundaries, and conductor/worker split.

Future enhancements should be added as separate files under `references/` and listed in this registry with a one-line loading rule.

## Injection Targets

Use the project-owned configuration layer, not the installed Trellis runtime:

- Create or update `.trellis/spec/trellis-plus/index.md` for the concise shared policy and add detail files beside it when needed.
- Add task-specific research, design decisions, implementation context, and check evidence under the active `.trellis/tasks/<TASK-ID>/` directory.
- Add the durable continuity control record at `.trellis/mainline.md` when the user has approved an initiative.
- For an active task, register the shared policy path in existing implement/check context with Trellis's context command when that context is needed.
- Keep personal allow rules in the active platform's local configuration. They adapt execution only and must not become a second project policy.
- Read `.trellis/workflow.md` and existing specs for context, but do not patch `.trellis/workflow.md`, `.trellis/scripts/**`, `.trellis/agents/**`, `.trellis/config.yaml`, update metadata, or managed platform files.

Do not create a parallel task system or runtime. The dedicated spec layer is
only a project-owned configuration namespace inside Trellis's normal spec
discovery model.

## Update Resilience

Trellis may update project templates while preserving local edits through hash-based conflict handling and timestamped backups. Trellis Plus must keep its durable additions outside those template targets so an update does not turn them into mixed upstream files.

When applying Trellis Plus after an update:

- Run or ask the user for `trellis update --dry-run` output when update state is unclear.
- Inspect the active protected files and newest `.trellis/.backup-*` snapshot read-only when provenance or update state is unclear.
- Revalidate `.trellis/spec/trellis-plus/index.md`, its project-owned detail files, task context, and `.trellis/mainline.md`; do not restore a previous customization into a protected Trellis file.
- If an update removes behavior that used to be injected through `workflow.md`, do not recreate that pointer automatically. The shared project configuration remains the source of truth for the next Trellis Plus run.
- If an update changes UUPM, Playwright, or wrapper paths, update only the project-owned policy/profile and preserve the user's existing test, fixture, wrapper, and personal configuration files.
- Do not add protected Trellis files to `update.skip` as part of this skill. If the user deliberately maintains a fork, handle it as a separate license-aware maintenance decision.

## Expected Result

After applying this skill with the default enhancement set, a future Trellis Plus run should:

- read the tracked project-owned Trellis Plus configuration before applying its enhanced guidance
- keep project-shared rules in `.trellis/spec/trellis-plus/` and task evidence in the normal Trellis task tree
- keep personal agent settings local and out of the shared commit by default
- never modify or stage protected Trellis templates, runtime scripts, agents, metadata, or managed platform files through the normal Trellis Plus flow
- pause or explicitly continue at submit-ready time with a concrete human feedback request, based on project-specific validation evidence
- ensure the project has a Docker-backed dev command wrapper or a before-dev checkpoint that can bootstrap one
- detect frontend projects and ask before initializing project-local UI/UX Pro Max when it is absent
- use UI/UX Pro Max design-system output as shared task context for frontend implementation and verification
- run focused Playwright validation for eligible UI changes before requesting human feedback, with traces, screenshots, and logs available when it fails
- maintain one project-level Playwright Validation Profile so later tasks can reuse exact setup, commands, fixtures, browser projects, and artifact locations without rediscovering them
- ask for manual review only when browser automation is ineffective, unavailable, or cannot resolve the remaining product, visual, accessibility, device, or private-environment risk
- decide whether each Phase 3.4 work commit deserves ChatGPT/Codex co-author attribution
- draft a useful task completion summary body for commits above that threshold
- add the ChatGPT/Codex co-author trailer only when that attribution threshold is met
- preserve a declared project mainline across task archives with a read-only, evidence-first Project Pulse when no task is active
- stage only explicit project-owned or user-authorized ordinary paths after a clean path classification and `git diff --check`
- default to guided recommendations; serially continue only the explicitly authorized, listed, ready work and stop for ambiguity, risk, scope change, or unmet dependencies
