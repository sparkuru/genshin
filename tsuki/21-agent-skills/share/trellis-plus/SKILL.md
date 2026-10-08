---
name: trellis-plus
description: Enhance Trellis through project-owned specs for development defaults, Docker preview and environment setup, desktop/mobile validation, requirement-to-mainline continuity, task-archive Codex attribution, and third-party notices. Use when applying trellis-plus or adding these conventions to a Trellis project, including UI/UX Pro Max integration and evidence-based human review.
---

# Trellis Plus

## Purpose

Use this skill to improve a repository's Trellis workflow after `trellis init` or after a task already has partial results. Before initialization, identify existing project requirements for later mainline import without manufacturing a partial Trellis installation.

The job is to inspect the project, infer how mature validation and continuity should work, then record durable rules in project-owned configuration and task data so later Trellis Plus runs can reuse them.

## Operating Rules

- At the start of every initialization/bootstrap, application, reapplication, or audit, read [CHACKLIST.md](CHACKLIST.md) from the same skill directory as this `SKILL.md`. Use its current IDs, applicability, source references, and evidence criteria for self-checking; never use an old copied prompt or repository snapshot as the current checklist. Reading the checklist grants no write or execution authority.
- Before any write, read `references/license-safe-file-policy.md` and classify the target as protected Trellis material, project-shared configuration, personal/local configuration, or ordinary project code.
- Do not modify, replace, copy, or rewrite protected Trellis material. Use the dedicated project-owned `.trellis/spec/trellis-plus/` layer for durable shared rules instead of injecting them into Trellis's upstream workflow or runtime files.
- Treat new project-authored specs and task records as project data. Do not copy Trellis, UUPM, or another tool's source text/code into them unless its source and license permit that exact use.
- Preserve existing Trellis wording and state names. Add small, clearly titled sections instead of rewriting the whole workflow.
- Prefer repository evidence over generic advice: package files, test scripts, CI files, existing test directories, docs, and the current task's PRD/check context.
- Treat `.trellis/` project data as shared and normally trackable, while `.agents/`, `.codex/`, `.claude/`, `.opencode/`, and other platform settings are personal/local and untracked. Preserve the repository's existing ignore behavior. Trellis Plus never stages personal/local files and never uses `git add -f`, `git add --force`, `git add .`, `git add -A`, or an equivalent broad/forced staging operation to collect them.
- Keep the tracked `.trellis/spec/trellis-plus/` configuration as the single project-wide source of truth. Personal settings may add only narrow local execution rules and must not duplicate project policy.
- Treat README as human-owned presentation: read it for evidence, but create or edit it only when explicitly requested. Put agent development conventions in the project-owned spec layer.
- Apply development-stage defaults unless real users, releases, external contracts, or data-retention requirements establish narrower exceptions. Read `references/development-principles.md` for the actionable rules.
- Classify whether the repository or active task has a frontend/UI surface before applying frontend-specific enhancements. Do not trigger UI/UX Pro Max (UUPM) for a backend-only project merely because it contains a package manifest.
- For browser-automatable frontend work, prefer a reproducible Playwright validation over asking the user to perform a generic smoke test. Retain human review only for the residual judgment or environment the agent cannot test effectively.
- If a frontend/UI project has no project-local UI/UX Pro Max initialization for the active AI platform, ask the user whether to initialize it before running UUPM commands or adding UUPM-derived design artifacts. Do not silently install or overwrite it.
- If `.trellis/` is absent, read `references/mainline-continuity.md` and identify project-local requirement/design sources read-only. If initialization is already authorized, use the installed Trellis initialization procedure and resume discovery afterward; otherwise report the missing prerequisite and import candidates without writing `.trellis/` files. Never invent an initializer or treat a draft as approved scope.
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
   use `.trellis/mainline.md` for project direction with explicit approved versus
   proposed requirements. Keep exact third-party notices under `third_party/`.
2. **Personal/local configuration**: write narrow agent rules only in the
   active platform's local configuration (`.codex/`, `.claude/`, `.agents/`, or
   `.opencode/`) and leave those paths untracked. Trellis Plus never stages
   personal/local files; a user-requested tracking exception is a separate
   manual license and secrets review.
3. **Protected Trellis material**: read `.trellis/workflow.md`,
   `.trellis/scripts/**`, `.trellis/agents/**`, `.trellis/config.yaml`, update
   metadata, and Trellis-managed platform files, but never patch them in the
   normal Trellis Plus flow.

Read the shared configuration at the start of each Trellis Plus run and verify
its loading path using the Project Policy Loading procedure below. A written
spec is not proof that every Trellis phase automatically loads or enforces it.

Before staging, inspect the complete candidate path list. If a proposed change
contains a protected or personal path, stop or remove it from the commit plan;
never silently stage it. If the user explicitly requests a protected-file fork,
report the licensing/notice boundary and wait for a license-aware decision
instead of writing automatically.

## Discovery Workflow

Before step 1, load [CHACKLIST.md](CHACKLIST.md) and select the applicable checks within the user's scope. For authorized initialization, revisit applicability after the actual Trellis initializer finishes. For a read-only audit, report findings and proposed changes without applying enhancements. After authorized changes, self-check the resulting state against the same current checklist before reporting completion. Follow its reporting and maintenance contract below.

1. Locate Trellis files:
   - `.trellis/workflow.md`
   - `.trellis/mainline.md` when present
   - `.trellis/spec/trellis-plus/index.md` when present
   - `.trellis/spec/**/index.md`
   - `.trellis/tasks/**/task.json`
   - project-local PRD, design, brief, and roadmap documents referenced by the user or project; distinguish current requirements from examples and archived alternatives
2. Classify Trellis-managed update state:
   - Check `.trellis/.version`, `.trellis/.template-hashes.json`, and recent `.trellis/.backup-*` directories when present.
   - If the user just ran `trellis update`, inspect the newest backup for previously recorded Trellis Plus content before updating project-owned files; never restore it into a protected path.
   - Treat `.trellis/spec/**`, `.trellis/tasks/**`, and `.trellis/workspace/**` as user/project data, not normal template-overwrite targets; prefer a new `.trellis/spec/trellis-plus/` layer over changing an existing generated index. Treat existing spec indexes outside that dedicated layer as read-only unless their project authorship is proven and the user explicitly approves the mixed-file change.
   - Treat `.trellis/workflow.md`, `.trellis/scripts/**`, `.trellis/agents/**`, `.trellis/config.yaml`, update metadata, and managed platform files as read-only protected material.
   - Locate existing `LICENSE*`, `COPYING*`, `NOTICE*`, Trellis `COPYRIGHT`, or package license metadata without editing them. If protected Trellis files are present but their applicable notice is absent or unknown, record `license-notice-needed` and do not stage those files.
   - Inventory relevant bundled/copied third-party material and existing `third_party/` notices; follow the file policy for exact-version notice collection.
3. Identify the active or latest task:
   - Prefer Trellis runtime pointers when present.
   - Otherwise inspect non-archived `.trellis/tasks/*/task.json`.
   - Note current status: `planning`, `in_progress`, `completed`, or project-specific variants.
   - When adding mainline continuity, read the mainline record, parent/child task evidence, archive evidence, git state, and available validation results before recommending a next action.
   - Import existing requirements when mainline is absent or incomplete; preserve source references, approval status, scope boundaries, and unresolved decisions.
4. Infer project validation:
   - Read manifest and CI files such as `package.json`, `pnpm-lock.yaml`, `pyproject.toml`, `Cargo.toml`, `go.mod`, `Makefile`, `.github/workflows/*`, `justfile`, and existing docs.
   - Identify lint, format, type-check, unit, integration, e2e, build, smoke, visual, device, or manual validation commands.
   - Distinguish commands the agent can run from checks that require the user's environment, credentials, GUI inspection, hardware, production-like data, or paid/external services.
   - Classify frontend/UI presence and record the evidence used: frontend framework dependencies, UI source files, frontend scripts/configuration, mobile UI targets, or an explicit UI requirement in the active task.
   - Identify supported desktop/mobile use and any explicit desktop-only constraint. Classify mobile coverage for changed pages and interactions before implementation, not only after responsive CSS changes.
   - For frontend/UI work, inspect for `@playwright/test`, `playwright.config.*`, Playwright scripts, browser-test directories, test fixtures, screenshot baselines, and CI browser-install steps. Decide whether the changed acceptance criteria can be exercised against a local or test deployment without private credentials or real devices.
   - If another browser-test runner is already the project convention, record whether it provides equivalent coverage; do not silently migrate or duplicate the suite merely to introduce Playwright.
   - Read any existing `Trellis Plus: Playwright Validation Profile` before consulting external Playwright documentation. Reconcile its exact commands and constraints with current repository evidence, then update it only when a durable convention changed.
   - Check whether UI/UX Pro Max is initialized in the project for the active platform. A global installation does not count as project initialization.
5. Infer dev-command wrapper state:
   - Check for dev wrapper, service lifecycle, `preview.sh`, `.devhome`, environment examples/loaders, and local-file ignore rules. Inspect local configuration keys without exposing secret values.
   - If no dev wrapper exists and the project has a clear toolchain, prepare to apply the Docker dev-wrapper enhancement.
   - Reuse existing startup/stop commands; add the preview entry only for a previewable service. Record actual network constraints and required configuration.
6. Discover task-archive attribution:
   - Read `git log --format=%B -n 20` or equivalent recent history.
   - Read the installed archive and journal commands to establish auto-commit behavior, supported message/no-auto-commit interfaces, and staged paths.
   - Record a verified route for one Codex trailer on each Codex-assisted task's archive commit. Ordinary work and separate journal commits do not receive it through this rule. Keep message language/style consistent with the repository.
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
   - development-stage exceptions, preview entry/addresses, environment setup or newly required keys, and execution constraints
   - task-archive attribution route and any unsupported integration point
   - mainline continuity mode, current initiative, and any decision required before work may continue
   - source requirements imported and their approval status
   - project policy loading paths, verified contexts, and remaining loading gaps
   - `trellis update` risk: whether any patched file is a Trellis template target and whether backup recovery was used
   - checklist IDs, applicability, existing versus target state, evidence, and remaining `GAP`/`UNKNOWN` results
   - any manual follow-up the next Trellis task should request

## Checklist Self-Check And Skill Maintenance

[CHACKLIST.md](CHACKLIST.md) is the maintained inspection catalogue for this skill. `SKILL.md` and the referenced procedures define the requirements; the checklist maps them to observable checks and does not replace their details. The target repository's tracked Trellis Plus specs remain its project policy source of truth. Do not copy the skill checklist into a target repository as a second policy or make future project tasks depend on this skill installation.

- Before and after an authorized bootstrap/application, inspect every applicable checklist requirement, including policy content, actual loading, and available execution evidence. Do not claim successful integration solely because a file was written. When there is no relevant task or execution capability, record the precise unverified portion.
- A full audit or default application reports every current checklist ID, including `PASS` and conditional `N/A` entries, with the constraint, existing situation/evidence, target situation, and proposed change/path. Split independently failing requirements into subrows. Use `PASS`, `GAP`, `UNKNOWN`, and `N/A` as defined in the checklist; a partial result cannot pass the whole item.
- For an explicitly scoped enhancement, self-check the relevant IDs and identify the excluded scope as unexamined; do not run or install unrelated enhancements to fill the table. A read-only request remains read-only, and missing runtime evidence does not authorize running services, installing tools, or changing tasks.
- If the checklist is missing or contradicts its source procedures, report the exact gap and affected IDs. Continue independent authorized work using the available source procedures, but do not declare the affected self-check or a full audit complete. An audit of a target repo does not authorize repairing the skill itself.
- **Every update to Trellis Plus must synchronize `CHACKLIST.md` in the same change.** Reconcile changes to `SKILL.md`, the registry, reference procedures, and any supporting behavior with checklist applicability, expected state, evidence, and links. Add new checks, revise changed checks, and remove retired requirements without reusing their IDs. Keep unaffected IDs stable so users can approve changes by ID.
- Even when an update changes no check requirement, review the checklist against the updated material and update its latest synchronization note with the actual reviewed scope and whether requirements changed. Update the copyable prompt only when its loading/reporting/authorization contract changes; it must point to the current checklist rather than duplicate the item inventory.
- Before declaring a skill update complete, verify that every registry enhancement and cross-cutting rule is covered, every checklist source link resolves, and initialization/application/audit all load the checklist. Run the skill validator and diff checks. Treat an unsynchronized checklist as unfinished maintenance.

## Enhancement Registry

Default Enhancement Set:

- **License-safe file policy**: always read `references/license-safe-file-policy.md` before any write, staging, or commit recommendation.
- **Submit-ready human review gate**: read `references/submit-ready-human-review.md` when adding rules for the moment a Trellis task is implemented, checked, and ready to commit.
- **Development-stage principles**: read `references/development-principles.md` to install the shared rules for scope, compatibility, evidence, dev access, README ownership, and workspace protection.
- **Task-archive Codex attribution**: read `references/chatgpt-codex-commit-trailer.md` for once-per-task completion summaries and co-author trailers at archival.
- **Docker development and preview bootstrap**: read `references/dev-it-in-docker-bootstrap.md` for the wrapper, `.env`-configured preview with first-use preparation of missing images/dependencies, reusable start/stop lifecycle, and delegation of execution permissions to the base skill. When implementing or adapting the preview CLI, read `assets/refer-preview.sh` and the reference integration procedure; reuse its presentation/dispatch layer or verify an existing equivalent. Also read `references/preview-console-contract.md` for the mandatory service-grouped URL format, effective Docker endpoint/host address discovery, readiness, and redacted failure diagnostics before cleanup.
- **Environment configuration**: read `references/environment-configuration.md` when creating or adapting `preview.sh`, configuring `.env.example`/`.env` or equivalent project files, and communicating required values.
- **UI/UX Pro Max frontend integration**: read `references/ui-ux-pro-max-integration.md` when the repository or active task has a frontend/UI surface. This enhancement owns the initialization prompt and the UUPM Plan → Implement → Check → Update Spec workflow.
- **Playwright automated frontend validation**: read `references/playwright-automated-validation.md` when the repository or active task has a browser-accessible UI change. This enhancement owns the automate-first decision, Playwright test evidence, and residual manual-review handoff.
- **Mainline continuity**: read `references/mainline-continuity.md` for requirement/design import, lifecycle updates, read-only Project Pulse, and bounded continuation authority.

Future enhancements should be added as separate files under `references/`, listed in this registry with a one-line loading rule, and included in `CHACKLIST.md` in the same change.

## Injection Targets

Use the project-owned configuration layer, not the installed Trellis runtime:

- Create or update `.trellis/spec/trellis-plus/index.md` for the concise shared policy and add detail files beside it when needed.
- Add task-specific research, design decisions, implementation context, and check evidence under the active `.trellis/tasks/<TASK-ID>/` directory.
- Add the durable continuity record at `.trellis/mainline.md` for approved or explicitly labeled proposed direction; proposed content grants no implementation authority.
- Register the shared policy and relevant detail paths in active task context using the installed Trellis mechanism. Verify loading as described below.
- Keep personal allow rules in the active platform's local configuration. They adapt execution only and must not become a second project policy.
- Read `.trellis/workflow.md` and existing specs for context, but do not patch `.trellis/workflow.md`, `.trellis/scripts/**`, `.trellis/agents/**`, `.trellis/config.yaml`, update metadata, or managed platform files.

Do not create a parallel task system or runtime. The dedicated spec layer is
only a project-owned configuration namespace inside Trellis's normal spec
discovery model.

## Project Policy Loading And Generalization

The installed project must be usable by an agent that has only the repository,
not the author's home directory or this conversation. For each enhancement,
write its trigger, concrete action, relevant project paths/commands, exceptions,
and observable verification into the project-owned spec. Replace example
values with repository evidence; mark unresolved values explicitly instead of
inventing commands. Keep durable rules in specs and this task's results in task
evidence. Do not reduce an actionable procedure to a vague instruction such as
"follow best practices" or a pointer to an unavailable skill.

1. Keep the shared index short, with direct links and loading conditions for
   its detail files. Reuse existing equivalent project-owned files and avoid
   duplicating rules across indexes.
2. Inspect the installed task-start/context-loading path and applicable
   `AGENTS.md` read-only. Confirm whether the shared index is actually loaded;
   do not infer this from the existence of a spec directory.
3. For an active task, use the existing context mechanism to register the
   shared index and applicable detail files for implementation and checking.
   If the loader does not follow Markdown links, register the needed details
   explicitly. Preserve existing entries and deduplicate additions. Inspect
   the resulting context records or resolved input when available.
4. Ensure the main session reads mainline and the shared policy at task start,
   after a substantial interruption, before commit/archive, and when selecting
   subsequent work. Configure an existing project-owned startup extension if
   available. Otherwise a narrow personal/local adapter may point to the
   tracked policy, but it is not a portable replacement for project discovery.
   Never patch a Trellis-managed AGENTS block or other protected loader.
5. Record the actual loading path and any gap in the shared index. If future
   tasks lack an automatic loading path, state that limitation and the exact
   manual read/context-registration step. Do not report automatic integration
   complete while the entry point is missing.
6. Walk through one relevant task from start to check to archive using the
   generated rules. Confirm that its agent can identify the next action,
   execute the documented command when available, and distinguish success,
   missing prerequisites, and an unsupported operation. Reapplying the skill
   must preserve user values and work without duplicated rules or task records.

Generalize incidental names, machine paths, private endpoints, and one-off
conversation examples. Preserve standard filenames, real project command
syntax, requirement approval boundaries, and the exact Codex trailer. Keep
unknown capabilities explicit; removing specifics must not remove the evidence
needed to perform or verify the work.

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

- load the current skill-local `CHACKLIST.md` and report evidence-based self-check results before declaring initialization/application or a full audit complete
- read the tracked project-owned Trellis Plus configuration before applying its enhanced guidance
- keep project-shared rules in `.trellis/spec/trellis-plus/` and task evidence in the normal Trellis task tree
- keep personal agent settings local and out of the shared commit by default
- never modify or stage protected Trellis templates, runtime scripts, agents, metadata, or managed platform files through the normal Trellis Plus flow
- pause or explicitly continue at submit-ready time with a concrete human feedback request, based on project-specific validation evidence
- preserve development-stage defaults and documented release/data exceptions, keep README unchanged unless requested, and avoid speculative compatibility or unrelated cleanup
- ensure the project has a development wrapper, a reusable service lifecycle and preview entry that prepares missing resources after environment setup when applicable, or a concrete before-dev checkpoint; preserve explicit offline/no-install constraints and expose redacted startup diagnostics before cleanup
- document initial environment setup and append only missing local keys on later configuration changes while preserving user values
- retain exact third-party license/notice material with source and version provenance in `third_party/`
- detect frontend projects and ask before initializing project-local UI/UX Pro Max when it is absent
- use UI/UX Pro Max design-system output as shared task context for frontend implementation and verification
- run focused desktop and applicable mobile Playwright validation before requesting human feedback, with traces, screenshots, and logs available when it fails
- maintain one project-level Playwright Validation Profile so later tasks can reuse exact setup, commands, fixtures, browser projects, and artifact locations without rediscovering them
- ask for manual review only when browser automation is ineffective, unavailable, or cannot resolve the remaining product, visual, accessibility, device, or private-environment risk
- attribute each successfully archived Codex-assisted task once on its archive commit, using a verified supported archive route and a proportional completion summary
- omit this task-level trailer from ordinary work and separate journal commits; retries do not duplicate attribution
- import project-local requirements into mainline with approval/source boundaries and maintain verified progress across the task lifecycle
- preserve a declared project mainline across task archives with a read-only, evidence-first Project Pulse when no task is active
- verify policy loading for current and future tasks, reporting integration gaps instead of claiming a spec file enforces itself
- stage only explicit project-owned or user-authorized ordinary paths after a clean path classification and `git diff --check`
- default to guided recommendations; serially continue only the explicitly authorized, listed, ready work and stop for ambiguity, risk, scope change, or unmet dependencies
