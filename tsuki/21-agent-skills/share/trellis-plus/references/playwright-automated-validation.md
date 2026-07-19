# Playwright Automated Frontend Validation

## Goal

Make reproducible browser validation the default for eligible Trellis frontend tasks. The agent must implement and run focused Playwright coverage for the changed acceptance criteria before requesting a generic user smoke test.

Playwright reduces the browser-validation gap between implementation and submit-ready. It does not replace product judgment, subjective visual review, real-device testing, or environments the agent cannot safely reproduce.

## Quick Execution Matrix

Use this matrix before consulting external Playwright documentation. Resolve the project-specific command and constraints from the Playwright Validation Profile; consult documentation only when the profile or repository evidence does not cover the required capability.

| Task signal | Default action | Required evidence |
| --- | --- | --- |
| Page, route, form, or interaction changed | Add or extend a focused Playwright Test using semantic locators | Test name, exact command, covered flow |
| Loading, empty, error, disabled, permission, or success state changed | Drive the state with the project's fixture, seed, or network mock | State setup and assertion |
| Responsive behavior changed | Run the target flow at the supported desktop and narrow-mobile viewports | Viewports and assertions |
| API or third-party service is unavailable | Reuse an approved fixture or route mock; do not use production credentials | Fixture/mock boundary |
| Semantic, label, focus, or keyboard behavior changed | Assert roles, accessible names, focus, and keyboard flow; run configured accessibility scan | Assertions and scan result |
| Stable visual baseline exists | Run the approved screenshot assertion without silently updating snapshots | Baseline name and review reason for changes |
| Browser test fails | Preserve reporter output, console/network evidence, screenshot, and configured trace | Artifact paths or report link |
| Browser automation is ineffective or unavailable | Record the classification and request only the smallest replacement manual/CI check | Exact blocker or residual risk |

## Execution Environment Templates

Resolve one execution mode from repository evidence and record its exact command in the project profile. These are command shapes, not commands to copy blindly:

| Mode | Use when | Command shape | Environment requirement |
| --- | --- | --- | --- |
| `project-local` | Node, browser binaries, and application dependencies run on the workstation | `<package-manager> exec playwright test <target> --project=<browser>` | Local project dependency and matching Playwright browser binary |
| `docker-wrapper` | The project validates through `hako`, `dx`, or another approved container wrapper | `<wrapper> <project Playwright test command>` | Browser binaries and system libraries live in the container; use the wrapper's documented argument form |
| `ci` | Browser validation is only reproducible in the CI image or service topology | `<CI job name>: <project Playwright test command>` | Pin the image/browser version and preserve the CI artifact location |

Do not require a global Playwright or system Chrome installation. The selected execution environment needs the project Playwright dependency, matching browser binary, browser system dependencies, and a runnable application. Record browser installation/bootstrap separately from the test command when it is not already handled by project install or CI.

## Scope And Decision

Run this enhancement when the repository or active task has a browser-accessible UI change: a page, component interaction, route, form, responsive behavior, client-side error state, accessibility behavior, or web workflow.

Before implementation or final check, classify the task:

- `playwright-required`: the changed behavior can be exercised from a local or test deployment with controlled data, mocks, or test accounts.
- `playwright-existing-equivalent`: the project standardizes another browser-test runner that already covers the changed path. Use that suite; do not silently migrate or duplicate it.
- `playwright-not-effective`: browser automation would not give useful evidence. Examples include purely subjective visual approval with no stable baseline, a native-only interaction, real hardware, an unautomatable third-party flow, or a private environment that cannot be reproduced safely.
- `playwright-unavailable`: automation is appropriate but cannot run because of a missing runtime, browser binary, dependency, fixture, permission, network/service dependency, or an unstartable application. Record the exact blocker and its attempted command.

Do not choose `playwright-not-effective` merely because the task changes UI, needs a browser, or requires writing a test. Browser-accessible acceptance criteria should normally be `playwright-required`.

## Discovery

Inspect repository evidence before changing test infrastructure:

- package manifests, lockfiles, scripts, and CI workflows
- `@playwright/test`, `playwright.config.*`, test directories, reporters, fixtures, `storageState`, and snapshot baselines
- the app's local/test startup command, readiness URL, base URL, API dependencies, and seeded-data strategy
- existing E2E conventions and a project's existing browser runner
- the active PRD, approved `design.md`, frontend specs, and target states/routes

Record the command that will run during final validation. Prefer an existing narrow command such as `pnpm test:e2e -- --grep "checkout"` over the whole suite when the task has a focused, stable test selection.

## Durable Project Profile

For every project where this enhancement applies, create or update one durable section named `### Trellis Plus: Playwright Validation Profile`.

Place it in the existing frontend or testing `.trellis/spec/**/index.md` entry point. If no suitable spec exists, place it in `.trellis/workflow.md` near final verification. Do not create a parallel test framework or a task-local substitute just to hold this profile.

The profile must contain only repository-confirmed values and these fields:

```markdown
### Trellis Plus: Playwright Validation Profile

- execution mode: <project-local | docker-wrapper | ci>
- setup/install: <exact dependency/browser bootstrap command, or already provided by CI/image>
- app readiness: <startup command, readiness URL, and base URL>
- focused test command: <exact command with an example narrow selection>
- full/CI browser command: <exact command or CI job name>
- test location and config: <path(s)>
- browser projects and supported viewports: <names and sizes>
- fixtures and test-data boundary: <seed, mock, test account, storage state, or none>
- accessibility policy: <configured scan/assertions, or not configured>
- visual baseline policy: <approved snapshot command/environment, or diagnostic-only>
- failure artifacts: <report, trace, screenshot, console/network locations>
```

On every eligible task, read this profile before inspecting external documentation. Reconcile it with current manifests, config, and CI only when it is missing, stale, or contradicted by repository evidence. Update it when a durable command, browser project, fixture convention, readiness requirement, or artifact location changes. Task check evidence records this task's coverage and result; it does not duplicate the profile.

## Adoption And Test Design

Use Playwright Test for persistent, repeatable validation. Interactive browser exploration may help develop a test, but it is not final validation unless its commands and evidence are reproducible.

When Playwright already exists:

1. Extend or add the smallest test that exercises the changed acceptance criteria.
2. Reuse the project's package manager, config, fixtures, reporter, browser projects, and test-data conventions.
3. Do not update snapshots automatically. Review an intentional snapshot change against the PRD and design decisions before accepting it.

When Playwright is absent but the task is `playwright-required`:

1. Add it as a development-only test dependency using the project's package manager and lockfile.
2. Add the smallest project-consistent config, test command, and deterministic local/test-server startup needed to run the targeted test.
3. Prefer a `webServer`/base-URL configuration or the repository's existing dev wrapper over manually started, untracked background processes.
4. Commit durable regression coverage when the path is likely to change again or represents an acceptance criterion. Do not create a permanent broad E2E suite for a one-line visual-only change without a stable, meaningful assertion.

Do not replace a maintained project-standard browser runner without an explicit migration request. Do not use production credentials, production data, paid accounts, or a user's personal session. Prefer deterministic fixtures, a test account, seeded data, and network mocking where repository conventions allow them.

## Required Coverage

For each `playwright-required` task, implement only the assertions justified by the diff and acceptance criteria. Cover the applicable items:

- target route/page loads and has the intended accessible name or primary content
- primary user action and expected navigation, mutation, or confirmation
- changed loading, empty, error, disabled, permission, and success states
- relevant keyboard/focus behavior and accessible control names
- supported desktop viewport and a narrow mobile viewport when responsive behavior changed
- request/response behavior with deterministic mocks or fixtures when the UI depends on unavailable services

Use semantic locators (`getByRole`, labels, and visible user-facing text) rather than fragile DOM structure or CSS selectors, unless no stable semantic surface exists.

Use screenshot assertions only when the repository can control the OS, browser version, fonts, viewport, data, animation, and baseline-review process. Otherwise capture screenshots as diagnostic artifacts, not pass/fail baselines. Add automated accessibility scanning when it is already available or when the change meaningfully affects semantic structure, labels, contrast, or interaction; treat it as partial coverage, not proof of accessibility.

## Execution And Evidence

Before submit-ready:

1. Run the narrow focused Playwright test, then any required broader browser suite or CI-equivalent command.
2. Preserve the exact command, selected browser project, result, and whether fixtures/mocks were used in the task's check evidence.
3. On failure, retain the reporter output, console/network evidence, screenshot, and Playwright trace when configured. Use traces on first retry or failure rather than collecting them for every passing run unless the project requires otherwise.
4. Fix the implementation or the test only after comparing the failure with the PRD and approved design decisions. Do not mask failures by increasing timeouts, broadening selectors, suppressing assertions, or accepting changed screenshots without a reason.

If the implementation changes a browser-facing behavior but no test is appropriate, record why under `playwright-not-effective` and name the smallest manual check that replaces it. If a test is appropriate but cannot run, record `playwright-unavailable`, the exact blocker, and the manual or CI evidence still needed.

## Submit-Ready Handoff

Feed the classification and evidence into the submit-ready human review gate:

- A passing `playwright-required` check is automated validation, not a reason to request a generic "please check the page" review.
- `playwright-not-effective` requires targeted human review only for the aspect automation cannot judge.
- `playwright-unavailable` requires human review or CI follow-up for the missing material check; it must not be reported as a passing browser validation.
- A passing browser test does not eliminate human review for subjective visual quality, business decisions, real-device behavior, assistive-technology assessment, security-sensitive flows, or inaccessible private environments.

Use this compact evidence shape in check results and commit plans:

```markdown
Browser validation: Playwright passed
- command: <exact command>
- coverage: <routes, states, interactions, viewports>
- fixtures: <none or controlled fixture/mock summary>
- residual human review: <none or specific remaining risk>
```

## Suggested Workflow Block

Adapt this block to the project's existing check or verification phase:

```markdown
### Trellis Plus: Playwright automated frontend validation

For every browser-accessible UI change, decide whether Playwright can exercise the changed acceptance criteria. When it can, implement and run focused, reproducible browser coverage before submit-ready. Reuse the project's browser-test convention; when no equivalent runner exists, add the smallest Playwright Test setup justified by the task.

Record the exact command, covered routes/states/viewports, fixture strategy, and result. Preserve traces, screenshots, and logs on failure. Do not ask the user for a generic browser smoke test after relevant Playwright checks pass. Request human review only for the specific subjective, real-device, private-environment, or otherwise unautomatable risk that remains.
```

## Patch Guidance

Patch in this order:

1. `.trellis/workflow.md`: add the automate-first decision before final check or submit-ready.
2. Existing frontend or testing `.trellis/spec/**/index.md`: add or update the `Trellis Plus: Playwright Validation Profile` with repository-confirmed exact commands and constraints. Use `.trellis/workflow.md` only when no suitable spec exists.
3. Existing check skill or command: point to the profile and add the task evidence format; do not repeat a generic command list.
4. Existing frontend validation spec: add stable test routes, fixture conventions, viewport policy, and approved visual-baseline policy when those conventions exist.

Add the detailed rule once and short pointers elsewhere. Do not create a parallel E2E workflow or rewrite existing Playwright configuration just to install the enhancement.

## Verification After Injection

After patching, verify:

- browser-accessible UI changes are classified before human review is requested
- existing Playwright or equivalent browser-test conventions are discovered and preserved
- the project has one current `Trellis Plus: Playwright Validation Profile` at the prescribed durable location
- the profile identifies the execution mode, bootstrap, exact focused and CI commands, readiness/base URL, browser projects, fixtures, and artifact locations
- eligible tasks read the profile before external documentation and record only task-specific coverage/results
- eligible work requires an implemented, runnable focused browser test rather than a generic manual smoke-test request
- unavailable automation records the exact failed prerequisite and does not count as a pass
- test evidence includes the exact command and covered user-facing behavior
- snapshot changes require intentional review and failure artifacts are retained
- human review requests name only residual risks that automation cannot resolve
