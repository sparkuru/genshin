---
name: trellis-plus
description: Bootstrap a Trellis project from its current PRD into shared development rules, mainline, applicable UI/UX Pro Max integration, and verified initialization-task closure. Also apply, reapply, or audit Trellis Plus conventions for development, preview, validation, continuity, attribution, and third-party notices without customizing Trellis runtime.
---

# Trellis Plus

## Purpose

Use this skill to improve a repository's Trellis workflow after `trellis init` or after a task already has partial results. Before initialization, identify existing project requirements for later mainline import without manufacturing a partial Trellis installation.

The job is to inspect the project, infer how mature validation and continuity should work, then record durable rules in project-owned configuration and task data so later Trellis Plus runs can reuse them.

## Modes And Delivery

Select the mode from the user's request and repository evidence:

- **Initialization/bootstrap**: a new project with a current PRD, a recent `trellis init`, or an incomplete `00-bootstrap-guidelines` setup. Read [Initialization Delivery](references/initialization-delivery.md) before applying enhancements. The result is development readiness, including `00` closure and repository delivery verification, without requiring product implementation first.
- **Application/reapplication**: enhance an established installation; preserve existing decisions and use only applicable enhancements. Do not reopen a completed bootstrap.
- **Scoped enhancement**: apply only the requested enhancement and its dependencies.
- **Read-only audit**: inspect and propose; do not apply, install, execute lifecycle actions or change tasks.

For bootstrap, archiving a separate enhancement task is not initialization completion. Use the delivery procedure's current-stage acceptance and completion decision; report incomplete initialization when a required check, loading path or closure remains unresolved. Follow the same current `CHACKLIST.md` before and after the work.

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
- If a frontend/UI project lacks active-platform project-local UUPM, reuse explicit initialization authorization or ask once before UUPM commands or derived artifacts. Current PRD UI requirements can establish applicability before UI code exists. Do not silently install or overwrite it.
- If `.trellis/` is absent, read `references/mainline-continuity.md` and identify project-local requirement/design sources read-only. If initialization is already authorized, use the installed Trellis initialization procedure and resume discovery afterward; otherwise report the missing prerequisite and import candidates without writing `.trellis/` files. Never invent an initializer or treat a draft as approved scope.
- If there are unrecognized local changes, do not overwrite them. Read the affected files and patch around the user's work.
- After `trellis update`, follow [Trellis Update Revalidation](references/trellis-update-revalidation.md) for project-owned configuration and task context; never restore it into a protected upstream file.

## License-Safe Write Boundary

The exact file policy is in `references/license-safe-file-policy.md`; it is part of this skill's required procedure, not optional background reading.

Trellis upstream is AGPL-licensed. A project can contain independent project-authored files alongside it, but a file that copies from or modifies an upstream Trellis file must retain the applicable upstream license and notices. File location alone does not make copied material project-owned.

Use this split:

1. **Project-shared configuration**: create or update `.trellis/spec/trellis-plus/index.md` and new detail files in that directory; keep task-specific decisions and evidence in `.trellis/tasks/<TASK-ID>/`, and use `.trellis/mainline.md` for project direction with explicit approved versus proposed requirements. Keep exact third-party notices under `third_party/`.
2. **Personal/local configuration**: write narrow agent rules only in the active platform's local configuration (`.codex/`, `.claude/`, `.agents/`, or `.opencode/`) and leave those paths untracked. Trellis Plus never stages personal/local files; a user-requested tracking exception is a separate manual license and secrets review.
3. **Protected Trellis material**: read `.trellis/workflow.md`, `.trellis/scripts/**`, `.trellis/agents/**`, `.trellis/config.yaml`, update metadata, and Trellis-managed platform files, but never patch them in the normal Trellis Plus flow.

Read the shared configuration at the start of each Trellis Plus run and verify its loading path using [Project Policy Loading And Generalization](references/project-policy-loading.md). A written spec is not proof that every Trellis phase automatically loads or enforces it.

Before staging, inspect the complete candidate path list. Protected files cannot be customization targets. The file policy permits an explicitly reviewed, unchanged upstream initialization baseline to be tracked; this does not permit staging personal platform files, backups or local state. Otherwise stop or remove protected/personal paths from the commit plan. A protected-file fork remains a separate license-aware decision.

## Discovery Workflow

1. Determine scope and mode. Load the current [CHACKLIST.md](CHACKLIST.md) and select the mode above. For bootstrap, read the delivery procedure and use `00-bootstrap-guidelines` as the normal initialization evidence home when present. Select checks within scope; an audit reports evidence and proposals without applying enhancements.
2. Perform minimal discovery to choose routes:
   - Locate `.trellis/workflow.md`, `.trellis/spec/trellis-plus/index.md`, existing `.trellis/spec/**/index.md`, `.trellis/mainline.md`, and task records when present.
   - Prefer runtime pointers for the active task; otherwise inspect non-archived `.trellis/tasks/*/task.json`. Record the actual status without changing it.
   - Identify current requirement/design sources and inspect manifests, CI, existing commands, and task scope only far enough to classify UI, previewable services, and initialization/update state. Keep archived alternatives and examples distinct from current requirements.
   - If authorized Trellis initialization runs, resume discovery and reassess applicability from the resulting installation before selecting enhancements.
3. Select references before specialized discovery or writes. For `$trellis-plus` without a narrower scope, read every reference in the Default Enhancement Set and its required dependencies; execute only applicable, authorized steps. For a scoped enhancement, read its reference and the shared procedures/dependencies needed by its actual targets. If a required reference is missing, report its exact path before modifying the affected targets.
4. Run the selected references' discovery and applicability checks. Derive validation commands from repository evidence and distinguish runnable checks from checks requiring the user's environment. Classify candidate writes through the file policy; retain personal settings locally and report any protected target instead of patching it. Do not run or install unrelated enhancements to fill checklist gaps.
5. Apply authorized changes only to classified targets. For shared rules and task context, follow [Project Policy Loading And Generalization](references/project-policy-loading.md) to verify usable project rules and actual loading. Self-check the resulting state against the current checklist; report unverified execution or loading as a gap rather than successful integration.
6. For bootstrap, follow [Initialization Bootstrap Task Closure](references/initialization-bootstrap-task-closure.md) and verify the delivery snapshot under [Initialization Delivery](references/initialization-delivery.md) before reporting complete. Assess policy/checkpoint installation separately from future product execution; never use a nonexistent future UI as a reason to leave initialization open indefinitely. Read-only audits and unrelated scoped enhancements do not trigger closure.
7. Report evidence and remaining work:
   - changed files, protected files inspected, Trellis license/notice status, shared versus local ownership, and explicit staging paths or why staging is unavailable
   - applied rules, validation profile, actual checks and limitations, and applicable Playwright execution mode/profile location
   - development-stage exceptions, preview entry/addresses, environment setup or new keys, and execution constraints
   - archive-attribution route, unsupported integration points, and applicable initialization closure outcome
   - mainline mode/initiative, imported requirements and approval status, required decisions, and policy loading paths, verified contexts, and gaps
   - template-update risk and backup use, current checklist IDs/applicability, existing versus target evidence, remaining `GAP`/`UNKNOWN` results, and manual follow-up

## Checklist Self-Check And Skill Maintenance

[CHACKLIST.md](CHACKLIST.md) is the maintained inspection catalogue for this skill. `SKILL.md` and the referenced procedures define the requirements; the checklist maps them to observable checks and does not replace their details. The target repository's tracked Trellis Plus specs remain its project policy source of truth. Do not copy the skill checklist into a target repository as a second policy or make future project tasks depend on this skill installation.

- Before and after an authorized bootstrap/application, inspect every applicable checklist requirement, including policy content, actual loading, and available execution evidence. Do not claim successful integration solely because a file was written. When there is no relevant task or execution capability, record the precise unverified portion.
- A full audit or default application reports every current checklist ID, including `PASS` and conditional `N/A` entries, with the constraint, existing situation/evidence, target situation, and proposed change/path. Split independently failing requirements into subrows. Use `PASS`, `GAP`, `UNKNOWN`, and `N/A` as defined in the checklist; a partial result cannot pass the whole item.
- For an explicitly scoped enhancement, self-check the relevant IDs and identify the excluded scope as unexamined; do not run or install unrelated enhancements to fill the table. A read-only request remains read-only, and missing runtime evidence does not authorize running services, installing tools, or changing tasks.
- If the checklist is missing or contradicts its source procedures, report the exact gap and affected IDs. Continue independent authorized work using the available source procedures, but do not declare the affected self-check or a full audit complete. An audit of a target repo does not authorize repairing the skill itself.
- When updating `SKILL.md`, the registry, reference procedures, or supporting behavior, review affected checklist requirements and synchronize changed applicability, expected state, evidence, and links in the same change. Add new checks and remove retired requirements without reusing their IDs; keep unaffected IDs stable. If no checklist requirement changes, leave `CHACKLIST.md` unchanged.
- Update the copyable prompt only when its loading/reporting/authorization contract changes; it must point to the current checklist rather than duplicate the item inventory. Keep only current guidance in the skill; record change history and review conclusions in commit messages or the delivery report instead of appending synchronization notes.
- Before declaring a skill update complete, verify that every registry enhancement and cross-cutting rule is covered, every checklist source link resolves, and initialization/application/audit all load the checklist. Run the skill validator and diff checks. Treat an unsynchronized checklist as unfinished maintenance.

## Enhancement Registry

Default Enhancement Set:

- **Initialization delivery**: read `references/initialization-delivery.md` for new-project bootstrap, incomplete-initialization recovery, or an audit of initialization completion; it defines stage-appropriate deliverables and the final completion decision.
- **License-safe file policy**: always read `references/license-safe-file-policy.md` before any write, staging, or commit recommendation.
- **Project policy loading and generalization**: read `references/project-policy-loading.md` when creating, reapplying, or auditing shared rules and task context.
- **Trellis update revalidation**: read `references/trellis-update-revalidation.md` after `trellis update` or when template/update state or provenance needs checking.
- **Submit-ready human review gate**: read `references/submit-ready-human-review.md` when adding rules for the moment a Trellis task is implemented, checked, and ready to commit.
- **Development-stage principles**: read `references/development-principles.md` to install the shared rules for scope, compatibility, evidence, dev access, README ownership, and workspace protection.
- **Task-archive Codex attribution**: read `references/chatgpt-codex-commit-trailer.md` for once-per-task completion summaries and co-author trailers at archival.
- **Initialization bootstrap task closure**: read `references/initialization-bootstrap-task-closure.md` to adapt `00` acceptance to the actual project stage and close it after applicable bootstrap checks.
- **Docker development and preview bootstrap**: read `references/dev-it-in-docker-bootstrap.md` for wrapper/service setup and preview integration; it routes to the reference script, console contract, environment setup, and base skill when applicable.
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
- Register the shared policy and relevant detail paths in active task context using the installed Trellis mechanism. Verify loading through `references/project-policy-loading.md`.
- Keep personal allow rules in the active platform's local configuration. They adapt execution only and must not become a second project policy.
- Read `.trellis/workflow.md` and existing specs for context, but do not patch `.trellis/workflow.md`, `.trellis/scripts/**`, `.trellis/agents/**`, `.trellis/config.yaml`, update metadata, or managed platform files.

Do not create a parallel task system or runtime. The dedicated spec layer is only a project-owned configuration namespace inside Trellis's normal spec discovery model.

## Expected Result

The selected reference procedures define each enhancement's acceptance; the current checklist maps those requirements to evidence. A completed application leaves one reusable project-owned policy source, verified loading for the applicable scope, concrete development/validation guidance and truthful execution limits. Keep upstream content unchanged, personal settings local, notices exact and staging explicit.

For bootstrap, use the delivery procedure's completion decision: current PRD/mainline, stage-appropriate shared rules and integrations, verified `00` closure and an independently checked repository snapshot. Future product work has explicit triggers rather than fabricated implementation evidence. Required current gaps mean initialization is incomplete even if a separate enhancement task is archived.

End with the evidence report in Discovery Workflow. Preserve guided continuation unless bounded serial work is explicitly authorized; initialization does not itself start product development, deployment or a push.
