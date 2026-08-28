# License-Safe File Policy

## Goal

Keep Trellis upstream material separate from Trellis Plus project additions.
This is an engineering guardrail for file ownership and staging; it is not a
legal opinion or a substitute for checking the exact Trellis version's license
and notices before distribution.

The current Trellis upstream boundary is especially important because Trellis
is distributed under AGPL-3.0. A new, independent project file can remain a
project work, but copying upstream text/code into it or modifying an upstream
file creates a different licensing question. Never use the repository's root
license as a reason to remove or override an upstream notice.

## Protected Trellis paths

Treat these paths as read-only to Trellis Plus:

- `.trellis/workflow.md`
- `.trellis/scripts/**`
- `.trellis/agents/**`
- `.trellis/config.yaml`
- `.trellis/.gitignore`
- `.trellis/.version`
- `.trellis/.template-hashes.json`
- `.trellis/.backup-*`
- a Trellis-managed block in `AGENTS.md`
- any platform skill, command, hook, or agent file produced by `trellis init`

Do not patch, replace, copy, or rewrite protected paths. Read them when needed
to understand the installed workflow, but do not turn them into Trellis Plus
customization targets. Do not restore an old Trellis Plus block into a
protected file after `trellis update`; leave the current upstream file intact.

If the user explicitly requests a protected-file fork, stop before writing and
report the exact path, the upstream source/version that must be preserved, and
the required license/notice review. This skill does not perform that exception
automatically.

## Project-shared paths

These are the default durable write targets when the content is authored for
the project and does not copy Trellis or another tool's source material:

- `.trellis/spec/trellis-plus/index.md`
- new detail files under `.trellis/spec/trellis-plus/`
- `.trellis/tasks/<TASK-ID>/` task documents, research summaries, and check
  evidence
- `.trellis/mainline.md`
- `.trellis/workspace/**` when the repository intentionally tracks workspace
  history
- project-owned `hako`, `tools/**`, `tests/**`, `playwright.config.*`,
  `package.json`, lockfiles, and `.gitignore` when the active task requires
  them and the content is written or licensed as project material

`.trellis/spec/trellis-plus/index.md` is the canonical shared Trellis Plus
configuration. Create it only after Trellis has been initialized. Keep it
short, link to project-owned detail files, and write original project rules.
Do not append the same rules to every existing spec index.

Use a stable heading and explicit ownership marker so a later run can find the
same source of truth without guessing:

```markdown
# Trellis Plus Project Policy

- ownership: project-shared
- source: project-authored
- tracking: commit this file and its referenced project-owned detail files

## Rules

<concise project-specific rules>
```

The ownership marker describes the intended origin of the file; do not retain
it if the file contains copied third-party text that has not been reviewed.

Existing `.trellis/spec/**/index.md` files are mixed or provenance-sensitive
unless the repository proves that they are entirely project-authored. Read
them for context, but prefer the dedicated `trellis-plus` spec layer instead
of modifying them.

Task files may reference the canonical shared configuration through Trellis's
existing context mechanism. That updates project task data; it does not modify
Trellis runtime code.

If the repository already contains protected Trellis files, check for the
corresponding Trellis license/copyright/notice before recommending their
distribution. If the notice is missing or the installed version is unknown,
report `license-notice-needed` and do not invent, replace, or silently add a
root license. A user can supply the exact notice from the installed Trellis
distribution as a separate third-party notice file.

## Personal and local paths

These paths may receive narrow, machine- or user-specific settings, but must
remain untracked. Trellis Plus never stages them; a user-requested tracking
exception is a separate manual license and secrets review:

- `.codex/**`
- `.claude/**`
- `.agents/**`
- `.opencode/**`
- `.git/info/exclude`
- Trellis runtime pointers and local state already ignored by the installed
  `.trellis/.gitignore`

Personal files may contain a narrow pointer or allow rule for the shared
project wrapper. They must not contain a second copy of the project policy,
and they must never be staged or force-added by Trellis Plus.

## Staging and repository consistency

Before any `git add` or commit:

1. Inspect `git status --short` and `git diff --name-only`.
2. Classify every candidate path as protected, project-shared, personal/local,
   or ordinary user code.
3. Stop if a protected path is in the proposed Trellis Plus change set.
4. Stage explicit project-shared and user-authorized ordinary paths only. Never
   use `git add .`, `git add -A`, `git add -f`, or an equivalent broad/forced
   staging operation to collect personal files.
5. Leave personal/local paths untracked or ignored and report that they are
   intentionally local.
6. Run `git diff --check` and inspect the staged path list before committing.

If a personal path is not already ignored, prefer `.git/info/exclude` for the
current clone rather than changing the shared `.gitignore` without approval.

The repository's single source of truth is the tracked
`.trellis/spec/trellis-plus/` configuration plus normal project files. Personal
agent settings only adapt local execution; they do not define project policy.
After a project config change, verify that the same tracked file is referenced
by active task implement/check context when such context exists.

## Enhancement mapping

- Mainline continuity: `.trellis/mainline.md` and the shared Trellis Plus spec.
- Human review, commit summaries, and attribution: the shared Trellis Plus
  spec; the commit message itself is not a Trellis source modification.
- Playwright: project-owned test/config files plus the shared profile; keep
  task-specific evidence in the task directory.
- Docker development: a project-owned wrapper and `.gitignore`; keep narrow
  agent allow rules personal/local.
- UUPM: keep generated platform skill files personal/local unless their exact
  source and license are reviewed. Promote only reviewed, original project
  decisions into the shared spec.

Do not claim that a generated third-party artifact is covered by the project's
license merely because it lives under `.trellis/`.
