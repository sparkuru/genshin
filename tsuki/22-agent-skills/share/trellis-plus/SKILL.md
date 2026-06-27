---
name: trellis-plus
description: Enhances an existing or newly initialized Trellis workflow with local project conventions. Use when the user asks to apply `trellis-plus`, improve Trellis templates, inject personalized Trellis workflow rules, add submit-ready human review gates, add ChatGPT/Codex commit completion summaries and co-author trailers, bootstrap Docker-based dev commands, or make a Trellis project infer its testing and feedback process from the repository.
---

# Trellis Plus

## Purpose

Use this skill to customize a repository's Trellis workflow after `trellis init` or after a task already has partial results.

The job is to inspect the project, infer how mature validation should work, then inject durable rules into Trellis project-level files so later Trellis tasks inherit them automatically.

## Operating Rules

- Modify project-level Trellis templates and specs, not one-off active task notes, unless the user explicitly asks for a task-local patch.
- Preserve existing Trellis wording and state names. Add small, clearly titled sections instead of rewriting the whole workflow.
- Prefer repository evidence over generic advice: package files, test scripts, CI files, existing test directories, docs, and the current task's PRD/check context.
- If there is no `.trellis/` directory, stop after reporting that Trellis has not been initialized.
- If there are unrecognized local changes, do not overwrite them. Read the affected files and patch around the user's work.

## Discovery Workflow

1. Locate Trellis files:
   - `.trellis/workflow.md`
   - `.trellis/spec/**/index.md`
   - `.trellis/tasks/**/task.json`
   - `.claude/skills/trellis-*`, `.claude/commands/trellis/**`, or equivalent agent templates if present
   - `AGENTS.md`, `CLAUDE.md`, `.codex/**`, or other agent instruction files when Trellis refers to them
2. Identify the active or latest task:
   - Prefer Trellis runtime pointers when present.
   - Otherwise inspect non-archived `.trellis/tasks/*/task.json`.
   - Note current status: `planning`, `in_progress`, `completed`, or project-specific variants.
3. Infer project validation:
   - Read manifest and CI files such as `package.json`, `pnpm-lock.yaml`, `pyproject.toml`, `Cargo.toml`, `go.mod`, `Makefile`, `.github/workflows/*`, `justfile`, and existing docs.
   - Identify lint, format, type-check, unit, integration, e2e, build, smoke, visual, device, or manual validation commands.
   - Distinguish commands the agent can run from checks that require the user's environment, credentials, GUI inspection, hardware, production-like data, or paid/external services.
4. Infer dev-command wrapper state:
   - Check for `hako`, `dx`, `dev`, `.devhome`, `.gitignore`, and agent config files such as `.claude/settings.local.json`, `.codex/rules/default.rules`, `.codex/config.toml`, and `opencode.json`.
   - If no dev wrapper exists and the project has a clear toolchain, prepare to apply the Docker dev-wrapper enhancement.
5. Infer commit attribution style:
   - Read `git log --format=%B -n 20` or equivalent recent history.
   - Check whether larger AI-assisted commits use detailed completion bodies before their `Co-authored-by` / `Co-Authored-By` trailers.
   - Preserve an existing project-specific Codex/OpenAI trailer if one is already established.
6. Select enhancement references:
   - If the user invokes `$trellis-plus` without narrowing the scope, read every file in the Default Enhancement Set below and apply all of them.
   - If the user asks for a specific enhancement, read only that enhancement's reference file.
   - If a reference file named in the registry is missing, report that exact missing path before patching.
7. Patch durable Trellis files and summarize:
   - files changed
   - rules injected
   - inferred validation profile
   - dev wrapper state and auto-allow target
   - inferred commit attribution trailer
   - any manual follow-up the next Trellis task should request

## Enhancement Registry

Default Enhancement Set:

- **Submit-ready human review gate**: read `references/submit-ready-human-review.md` when adding rules for the moment a Trellis task is implemented, checked, and ready to commit.
- **ChatGPT/Codex commit completion summary and co-author trailer**: read `references/chatgpt-codex-commit-trailer.md` when adding commit body and attribution rules for commits made during Trellis Phase 3.4.
- **Docker dev-command bootstrap**: read `references/dev-it-in-docker-bootstrap.md` when adding a before-dev/init checkpoint that creates a `hako` dev wrapper and writes matching agent auto-allow rules.

Future enhancements should be added as separate files under `references/` and listed in this registry with a one-line loading rule.

## Injection Targets

Use the narrowest durable target that exists in the project:

- Add state-machine behavior to `.trellis/workflow.md` when the rule must apply every time the workflow reaches a phase.
- Add review or validation expectations to an existing `.trellis/spec/**/index.md` when the rule is a reusable project convention.
- Add agent-specific wording to `.claude/skills/trellis-before-dev/SKILL.md`, `.claude/skills/trellis-check/SKILL.md`, `.claude/skills/trellis-update-spec/SKILL.md`, `.codex/skills/before-dev/SKILL.md`, or similar files only when Trellis delegates that exact phase to those skills.
- Add commit-command wording to the Phase 3.4 section of `.trellis/workflow.md` when the rule changes how work commits are drafted or executed.
- Add a short pointer in `AGENTS.md` only if the project already uses it as the agent entry point.

Do not create a parallel Trellis framework. Extend the installed one.

## Expected Result

After applying this skill with the default enhancement set, a future Trellis run should:

- automatically pause or explicitly continue at submit-ready time with a concrete human feedback request, based on project-specific validation evidence
- ensure the project has a Docker-backed dev command wrapper or a before-dev checkpoint that can bootstrap one
- decide whether each Phase 3.4 work commit deserves ChatGPT/Codex co-author attribution
- draft a useful task completion summary body for commits above that threshold
- add the ChatGPT/Codex co-author trailer only when that attribution threshold is met
