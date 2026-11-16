# Initialization Delivery

## Trigger And Scope

Use this procedure for an authorized new-project bootstrap: idea → repository → current PRD → `trellis init` → Trellis Plus. Also use it when resuming an incomplete bootstrap. A plain application to a recently initialized project with an open `00-bootstrap-guidelines` task follows this route unless the user limits the scope. Audits remain read-only; a scoped enhancement or reapplication to an established project does not reopen initialization.

The deliverable is a repository ready for its next development task. It does not include implementing the product, deciding an unresolved stack, inventing code examples, or exercising features that do not exist yet. Preserve the user's narrower instructions, including an explicit choice to leave `00` open; report the resulting incomplete initialization rather than overriding that choice.

Read the current skill-local [checklist](../CHACKLIST.md), then the applicable registry procedures. This file defines delivery; [bootstrap closure](initialization-bootstrap-task-closure.md) defines how to close `00`, and the other references own their respective mechanisms. Keep results in normal task evidence, not a second initialization tracker.

## Authority And Task Ownership

Authorization to complete this bootstrap covers project-owned policy, requirement import, task context, stage-appropriate acceptance for `00`, and its archival after verification. It does not grant Git commit, push, deployment, tool installation, runtime execution, or product implementation authority beyond what the user and environment already permit. Reuse existing authority for each action. UUPM initialization follows its [authorization procedure](ui-ux-pro-max-integration.md); an explicit request to initialize applicable UUPM already supplies that decision.

Prefer the existing `00-bootstrap-guidelines` task as the initialization task and evidence home. If a separate enhancement task already exists, link its evidence from `00` and close both under their own acceptance and archive rules. Archiving the enhancement task alone does not complete initialization. Do not create a second task solely to claim success while `00` remains unresolved.

If a final commit is required but not authorized, finish the independent preparation and validation first, then present the concrete candidate paths and message for that decision. Use a supported no-commit archive route only when safe and consistent with the archive procedure; a pending required archive commit still blocks complete delivery. Do not run an auto-committing command without commit authority.

## Delivery Requirements

| Deliverable | Required current-stage evidence | Owning procedure |
| --- | --- | --- |
| Requirements and mainline | Current source PRD linked without rewriting it; objective, scope, non-goals, acceptance, decisions and approval status preserved; ordered work only where supported by the source | [Mainline continuity](mainline-continuity.md) |
| Shared policy and discovery | One project-owned spec index, actionable applicable details, a portable main-session entry, and verified implement/check context for the initialization task | [Policy loading](project-policy-loading.md) |
| Development and validation | Commands derived from existing code/tooling; applicable checks run; missing future infrastructure has a concrete before-development trigger and expected verification | [Development bootstrap](dev-it-in-docker-bootstrap.md), [review gate](submit-ready-human-review.md) |
| UI integration | For current product requirements that include UI, active-platform project-local UUPM is initialized and its required files/search entry verified, or the user's explicit decline is recorded | [UUPM integration](ui-ux-pro-max-integration.md) |
| Environment and preview | Existing service/configuration setup is usable when applicable; an idea-only project does not gain a speculative app, server or unused environment file | [Environment](environment-configuration.md), [development bootstrap](dev-it-in-docker-bootstrap.md) |
| Repository delivery | Explicit shared file set, upstream provenance/notices, local exclusions and an independent checkout check of required runtime and context dependencies | [File policy](license-safe-file-policy.md), Repository Verification below |
| Initialization closure | `00` archived with verified status/date and absent from active tasks; required archive commit and once-per-task attribution verified, or an evidenced skip when no task exists | [Bootstrap closure](initialization-bootstrap-task-closure.md) |

### Applicability Before Product Code Exists

Separate current setup obligations from future execution. An applicable tool installation or a broken existing command is a present requirement, not future work. A planned UI may require UUPM setup now without requiring a working application, design-system generation for an unchosen design, or Playwright execution against a nonexistent page.

For future-only work, record the trigger, responsible normal task or task category, shared policy path, and verification needed at that point. For example, the first browser implementation task must establish app startup/readiness, exact browser commands and desktop/mobile coverage before its own submit-ready gate. Do not invent command values or create follow-up tasks without authority just to fill the table.

In checklist evidence, split setup from execution: assess the installed rule/profile or checkpoint on its own evidence, and mark execution `N/A` only when its trigger has not occurred. If an existing app should run but cannot, use `GAP`/`UNKNOWN`; an all-unknown runnable profile does not pass. A recorded future obligation neither proves future behavior nor blocks this stage by itself. Apply the same distinction to update resilience and later lifecycle scenarios that have not occurred.

## Repository Verification

Choose the delivery route under the file policy: normally retain the verified upstream baseline in Git; preserve an established regenerate-on-setup route when the project deliberately uses one. For the latter, record the exact version, supported initialization command, required platform/local setup and restoration order, and verify that setup preserves project data. Do not merely omit runtime files and assume a later developer knows how to recover them.

With existing staging/commit authority, verify the proposed index snapshot or actual delivery commit in an isolated temporary checkout/export. Do not stage files just to test when that action is outside the authorized scope. If a candidate set is inspected before staging, label the check as candidate-only and verify the actual snapshot when available. Do not copy untracked working-tree dependencies into the checkout to make it pass.

Verify, using the installed interfaces where supported:

- required workflow/runtime files exist, and a read-only task command can operate without local identity/session state; if identity is required, exercise the documented setup in the isolated copy;
- shared policy/mainline links and initialization implement/check context references resolve inside the checkout, with source PRD and referenced guides present;
- the portable entry tells a new main session what to read and how to register context for a new task; local platform integrations are either separately initialized through documented setup or explicitly optional;
- task records show the actual bootstrap archive disposition; run the supported read-only task-list/context-validation commands when their prerequisites are available;
- local secrets, runtime pointers, ignored platform trees and unrelated user changes are excluded; do not execute copied lifecycle/install scripts or access the network without the applicable authority.

Retain only concise evidence in the existing task record. Missing execution capability is an unverified delivery check, not a pass. A working dirty checkout or passing application unit tests does not substitute for this verification.

## Completion Decision And Handoff

Report every current checklist ID for default initialization. Classify remaining entries by current requirement, future-only scenario or explicit user exception, with evidence and the affected scope; do not turn `GAP`/`UNKNOWN` into `PASS` by calling them follow-up work. An exception records an actual scope decision, not an agent-created waiver. Existing and new tasks retain their installed status vocabulary; the labels below describe the delivery report only.

- **Initialization complete**: all required current-stage deliverables verified, `00` closure verified or legitimately skipped, and the actual repository delivery snapshot verified. Future-only checks and explicit declined optional integrations are separately identified.
- **Initialization incomplete**: a current-stage requirement, required commit/archive, portable loading path or checkout check remains blocked or unverified. Name the completed subset, exact blocker, and next action. A user choice to keep `00` open has this outcome.

Finish with the PRD/mainline and shared policy locations, task archive/commit evidence, applicable integration result, checks actually run, local setup still needed on another machine, remaining future obligations and the next permitted development action. Do not start product implementation or push just because initialization is complete.
