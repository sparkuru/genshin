# Submit-Ready Human Review Gate

## Goal

Inject a durable Trellis rule for the moment a task has been implemented, checked, and appears ready to commit.

At that point, the agent must decide whether human review is required, optional, or unnecessary. When human input is needed, the agent must ask for specific feedback before committing.

## Trigger Point

Apply this gate when Trellis reaches any equivalent of:

- implementation is done
- `trellis-check` or final verification passed, or all runnable checks have been attempted
- the next planned action is a commit plan, `git add`, or `git commit`
- task status is about to move to `completed` or archive

This gate belongs before commit, not after commit.

## Decision Rules

Require human review when any of these apply:

- UI, UX, copy, visual layout, animation, accessibility, or workflow ergonomics changed.
- Product behavior depends on preference, business judgment, stakeholder expectations, or ambiguous acceptance criteria.
- Validation needs a browser, local app run, mobile device, real hardware, credentials, paid APIs, external services, production-like data, or private environment.
- The agent could not run a material check, or a check was skipped because dependencies, network, time, permissions, fixtures, or services were unavailable.
- The change touches auth, billing, data migration, deletion, permissions, security, deployment, CI/CD, generated assets, or irreversible operations.
- Existing tests cover only implementation mechanics and not the user-facing behavior promised in `prd.md`.

Make human review optional when:

- All relevant automated checks passed.
- The remaining risk is low but a user smoke test would improve confidence.
- The change is visible but small and the expected result is easy to verify.

Do not request human review when:

- The change is purely mechanical, documentation-only, or covered by focused tests.
- There is no meaningful judgment left for the user.
- The agent can state a concrete reason that manual review would not add signal.

## Project Validation Profile

When injecting this gate, also add or update a short validation profile in the most appropriate project-level Trellis spec or workflow section.

Infer it from repository evidence:

- manifests and scripts
- CI workflows
- existing test directories and naming
- current task's `prd.md`, `implement.jsonl`, and `check.jsonl`
- framework conventions already present in the repository

Record:

- required automated checks before submit-ready
- optional deeper checks for risky changes
- manual checks the user is uniquely able to perform
- known unavailable checks and what evidence should replace them

Keep the profile concrete. Prefer `npm run test:e2e` over "run e2e tests" when the command exists.

## Suggested Template Block

Adapt this block to the target Trellis file's style and status names:

```markdown
### Trellis Plus: Submit-Ready Human Review Gate

Before proposing a commit or marking a task complete, evaluate whether the finished work needs human participation.

1. Compare the implemented diff, `prd.md`, and the validation results.
2. Decide one of: `human-required`, `human-optional`, or `human-not-needed`.
3. If `human-required`, stop before commit and ask for targeted feedback.
4. If `human-optional`, present the review request and say whether it blocks commit.
5. If `human-not-needed`, state the reason in one sentence in the commit plan.

The feedback request must include:

- what changed
- what automated checks already ran and their result
- what the user should test manually
- what feedback format is useful: pass/fail, screenshots, logs, browser console output, reproduction steps, expected vs actual behavior, environment details
- any specific questions that affect whether the task should be committed

Do not ask a generic "please review". Ask for the smallest useful human signal.
```

## Feedback Request Shape

Use this shape when the gate blocks or asks for optional review:

```markdown
Human review: required

Implemented:
- <short scope summary>

Already validated:
- <command/result>
- <command/result>

Please test:
- <specific manual path or scenario>
- <specific edge case or visual state>

Please send back:
- pass/fail for each item
- screenshots or logs for failures
- browser console/server logs if relevant
- expected vs actual behavior
- environment details if behavior differs

Open questions:
- <only questions whose answers affect commit readiness>
```

For optional review, change the first line to `Human review: optional` and say whether the agent can proceed if the user confirms.

For no review, include a compact line in the commit plan:

```markdown
Human review: not needed because <specific reason tied to tests/risk>.
```

## Patch Guidance

Patch the installed Trellis files in this order of preference:

1. `.trellis/workflow.md`: add the gate to the finish, verify, submit-ready, or commit phase.
2. `.trellis/spec/**/index.md`: add the validation profile where project testing conventions already live.
3. `.claude/skills/trellis-check/SKILL.md` or equivalent: add the decision and feedback request requirement when final verification is delegated to that skill.
4. `.claude/commands/trellis/**`: patch only when the commit command bypasses workflow text.

If several targets exist, add the core rule once and add short pointers elsewhere.

## Verification After Injection

After patching, verify:

- the gate is before commit
- the gate says when to block
- the request format is concrete
- project-specific commands or manual checks are recorded
- no current task status was changed just by installing the enhancement
