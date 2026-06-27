# Docker Dev-Command Bootstrap

## Goal

Integrate the base `dev-it-in-docker` skill into a Trellis project so development commands can run through a repo-local Docker wrapper, usually `./hako`, without repeatedly asking for agent approval.

This is a Trellis Plus sub-enhancement. It wires the existing base skill into the Trellis workflow; it does not reimplement the full wrapper generation logic.

## Required Source Skill

Before applying this enhancement, read skill `dev-it-in-docker`

That path is a symlink to the maintained base skill. Follow its rules for toolchain detection, `hako` generation, `.devhome`, `.gitignore`, agent registration, and verification.

## Trellis Placement

Do not add this as a new required phase in every task's plan -> execute -> finish loop.

Treat it as project bootstrap and before-development readiness:

- If the project has `.trellis/workflow.md`, add a short checkpoint near the first `trellis-before-dev` / Phase 2 implementation guidance: if no dev wrapper exists and the task needs local lint/test/build commands, apply `dev-it-in-docker` before implementation.
- If the project has a before-dev skill (`.claude/skills/trellis-before-dev/SKILL.md`, `.codex/skills/before-dev/SKILL.md`, `.agents/skills/before-dev/SKILL.md`, or equivalent), add the checkpoint there because before-dev is where Trellis refreshes project execution conventions.
- If the project has an init/onboard checklist, add a one-line bootstrap reminder there.

Keep the wording as a pointer to the base skill. Do not paste the full `dev-it-in-docker` instructions into Trellis workflow files.

## Detection

Before patching, inspect:

- `hako`, `dx`, `dev`, or similar wrapper scripts
- `.devhome` and `.gitignore`
- manifests: `bun.lockb`, `bunfig.toml`, `pnpm-lock.yaml`, `package-lock.json`, `package.json`, `pyproject.toml`, `requirements.txt`, `go.mod`, `Cargo.toml`
- `.claude/settings.local.json`
- `.codex/rules/default.rules`
- `.codex/config.toml`
- `opencode.json`

If a wrapper already exists, do not create a competing wrapper. Add Trellis pointers and missing allow rules only.

## Auto-Allow Targets

Write the narrow wrapper allow rule for the agent(s) present in the target project. Merge and deduplicate; never overwrite existing user rules.

### Claude Code

Target:

```text
.claude/settings.local.json
```

Add:

```json
"Bash(./hako *)"
```

If the project uses another wrapper name, substitute that name, such as `Bash(./dx *)`.

### Codex

Primary target:

```text
.codex/rules/default.rules
```

Add:

```python
prefix_rule(pattern=["./hako"], decision="allow")
```

If a project keeps Codex rules in another project-level rules file, use that existing file and report the path. Do not add broad `docker`, `bash`, `sh`, or package-manager allow rules for this enhancement; `hako` is the approval boundary.

Optional hook target:

```text
.codex/config.toml
```

Only add hooks when the project already uses Codex hooks or the user asks for policy/audit. If hooks are added, remind the user they may need to review and trust them through `/hooks`.

### OpenCode

Target:

```text
opencode.json
```

Add or merge under `permission.bash`:

```json
"./hako *": "allow"
```

Keep this after any catch-all `"*": "ask"` rule because OpenCode is last-match-wins.

## Suggested Trellis Patch Block

Adapt this block to the local before-dev skill or workflow wording:

```markdown
### Trellis Plus: Docker dev-command bootstrap

Before implementation or validation, check whether this repository has a dev-command wrapper such as `./hako`.

If no wrapper exists and the task needs install/lint/typecheck/test/build/dev-server commands, apply the `dev-it-in-docker` skill first:

- detect the project toolchain and dev-server ports
- create or update the repo-local `hako` wrapper
- ensure `.devhome` is gitignored
- register the narrow wrapper allow rule in the active agent config (`Bash(./hako *)`, `prefix_rule(pattern=["./hako"], decision="allow")`, or `./hako *`)
- verify with the cheapest available `./hako <tool> --version` command

Do not broaden allow rules to raw `docker`, `bash`, `sh`, or package-manager commands just to make validation convenient.
```

## Verification

After patching, verify:

- Trellis before-dev or workflow points to `dev-it-in-docker`
- existing wrapper scripts were reused instead of duplicated
- `.gitignore` contains `.devhome` when `hako` uses it
- the active agent has a narrow wrapper allow rule
- no broad Docker/package-manager allow rule was introduced by this enhancement
- any generated wrapper remains executable
