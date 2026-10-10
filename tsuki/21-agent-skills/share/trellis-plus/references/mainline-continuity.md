# Mainline Continuity

## Contents

- [Goal](#goal)
- [Import Existing Requirements](#import-existing-requirements)
- [Control Record](#control-record)
- [Lifecycle Maintenance](#lifecycle-maintenance)
- [Project Pulse](#project-pulse)
- [Continuation Authority](#continuation-authority)
- [Conductor and Worker Protocol](#conductor-and-worker-protocol)
- [Injection Guidance](#injection-guidance)
- [Verification](#verification)

## Goal

Preserve project intent across task boundaries without creating a second task system. `.trellis/mainline.md` summarizes direction, approval boundaries, and progress. Source PRDs/designs retain detailed requirements; Trellis parent and child tasks retain plans, checks, commits, and archive evidence.

## Import Existing Requirements

At bootstrap, inspect project-local requirements supplied or referenced by the user and documents serving the same role as `prd.md`, `design.md`, briefs, or roadmaps. Bound discovery to the project; exclude dependencies, generated examples, and archived alternatives unless the user identifies them as current. Filenames are clues, not proof of authority or recency.

Before Trellis initialization, inventory these sources read-only. If init is already authorized, use the installed initialization workflow, then import. Otherwise report the prerequisite and candidates without creating a partial `.trellis/` tree. Resume the import after initialization.

For each relevant source, extract:

- desired outcome, intended users, and core use cases;
- in-scope behavior, non-goals, and technical/product constraints;
- observable acceptance criteria and unresolved decisions;
- evidence of approval, supersession, or draft status;
- proposed work/dependencies only where the source actually establishes them.

Create or merge `.trellis/mainline.md` without moving, deleting, or rewriting the source documents. Cite repository-relative source paths and sections; use existing revision/date information when useful, without inventing metadata. Keep the mainline concise: summarize and link instead of copying entire PRDs.

Carry forward already approved requirements without requesting approval again. For drafts, preserve useful direction as `proposed`, set the active objective to `not yet approved` if necessary, and list the decision still needed. Preserve established approval and supersession precedence: an older unapproved design does not reopen an approved PRD merely because they differ. Record alternatives as unapproved or superseded. Conflicting authoritative sources, or genuinely unclear authority affecting current acceptance, require an unresolved choice; neither filename nor modification time alone authorizes selecting one. Proposed direction grants no implementation or serial-continuation authority.

On rerun, merge new evidence into the same record, preserving accepted decisions and user edits. Do not replace an established mainline with an older source or silently promote an inferred feature into approved work.

## Control Record

Create or update `.trellis/mainline.md` with this template. Keep the ordered child list explicit; task-tree position does not imply ordering or readiness.

```markdown
# Trellis Mainline

## Initiative

- title: <approved initiative name>
- parent task: <.trellis/tasks/<parent-slug>, or none>
- objective: <user-approved outcome>
- owner decision: <date and concise authorization/source>

## Requirements And Sources

- source documents: <repository-relative paths and relevant sections>
- approved scope and acceptance: <concise outcomes or links>
- constraints and non-goals: <current boundaries>
- proposed or conflicting requirements: <unapproved items, or none>

## Continuation

- mode: guided
- serial authorization: none
- next pulse: <no-task | after archive | user-requested>

## Ordered Work

| order | task / proposed child | state | readiness and dependency evidence |
| --- | --- | --- | --- |
| 1 | <task path or approved child slug> | <planned | active | complete | blocked> | <why it is ready, or what blocks it> |

## Evidence and Decisions

- completed evidence: <archived task, commit, validation, or none>
- current blocker / dirty-state warning: <none or concrete issue>
- next user decision: <none or the one decision needed>
```

For a draft-only import, label title/objective and work rows as proposed rather than filling the approved fields with assumptions. Use `guided` unless the user explicitly authorizes a bounded serial initiative. For serial mode, replace `serial authorization: none` with the approved initiative, allowed child list/order, and stop conditions. Do not infer an objective, rank an unapproved backlog, or use repository code as authority for product priority.

## Lifecycle Maintenance

Read mainline and source requirements at task start. Map the task's acceptance criteria to the approved outcome; if it does not fit, resolve the actual scope conflict before implementation instead of silently changing the objective.

- On an approved requirement change, update scope, constraints, acceptance, source references, affected work, and the decision record together. Reuse explicit authorization already in the conversation.
- On task creation/start, link the normal Trellis task and update its state, ordering, and dependencies only within approved work. Do not create a second task schema or scheduler.
- After checks, record verified results and unresolved limitations. Keep implemented-but-unverified behavior distinct from completed acceptance.
- At archive, update task location, work/archival evidence, completed scope, remaining work, and next decision. Follow the task-archive attribution reference for the archive commit; a later mainline-only update does not add another trailer.
- On later evidence or user corrections, reconcile the record without erasing still-applicable requirements. Implementation drift is not a reason to weaken acceptance criteria or mark unfinished work complete.

Preserve a concise record of meaningful decisions, not a second detailed journal. Keep task-specific diagnostics and test output in their task records.

## Project Pulse

Run a read-only Project Pulse only for project-relevant no-task requests, such as continuing work, asking for status or next steps, beginning implementation, or immediately after a task archive. Read the control record, parent/child records, active and archived task evidence, git state, and available validation results. Report:

1. current initiative and completed evidence;
2. blocker or dirty-state warning;
3. one ready candidate when uniquely determined; and
4. the next permitted action.

| Evidence | Pulse result | Permitted action |
| --- | --- | --- |
| No record or no declared objective | State the missing evidence. | Ask for one product-priority decision. |
| `paused` mode | Report the recorded state only. | Do not create a task or edit code. |
| Dirty worktree, unresolved check, or incomplete archive evidence | Report the exact condition. | Resolve or obtain direction before continuing. |
| `guided` mode with one ready child | Recommend that child and its evidence. | Wait for the user to choose. |
| `guided` mode with multiple or unclear candidates | Report the competing evidence. | Ask the user to order or choose. |
| Explicit `serial` authorization with one listed, ready child | Name the authorized child and boundaries. | Run its normal Trellis lifecycle. |
| Missing dependency, risk, scope change, or new decision | State the stop condition. | Stop and ask for direction. |

Do not run a Pulse merely because the user asks an unrelated question. Do not use `completed` as a continuation trigger: after archive the active-task resolver cannot expose that state. Run the next Pulse from the relevant no-task or post-archive request instead.

## Continuation Authority

| Mode | Default behavior | Authority boundary |
| --- | --- | --- |
| `guided` | Pulse and recommend one action. | Never create a task or edit product files until the user chooses. |
| `serial` | Continue one listed, ready child after a clean archive. | Requires explicit bounded authorization; stop on ambiguity, risk, scope change, or unmet dependency. |
| `paused` | Report state only. | No task creation or implementation. |

Serial authorization substitutes only for repeated consent to create or start a listed, ready child. It does not waive required PRD/design/plan artifacts, checks, human-review gates, commit decisions, or archive evidence. A proposed child becomes work only through the normal Trellis task lifecycle and must be linked to the declared initiative parent when one exists.

## Conductor and Worker Protocol

The main session owns phase selection, Pulse, acceptance-criteria mapping, task creation/start, dispatch, commit, archive, and control-record updates. Research, implementation, and check workers receive only a bounded active task. They report files changed, validation, and unresolved decisions; they do not choose the next child, archive independently, perform project-wide cleanup, or recursively dispatch implement/check workers.

## Injection Guidance

Patch only these durable project files:

1. Create or merge `.trellis/mainline.md` from the control-record template when the project has a declared initiative or relevant source requirements. Label proposed direction explicitly. With neither, leave the record absent rather than inventing a product goal.
2. Add a short `Trellis Plus: Mainline Continuity` section to the shared `.trellis/spec/trellis-plus/index.md` (or a detail file beside it). It must say to run the read-only Pulse for relevant requests, default to `guided`, honor `paused`, and permit serial work only under recorded explicit authorization.
3. Add the shared spec path to active task context when delegated work needs it. A personal/local adapter may point to the shared rule when a platform cannot load it. Do not patch `.trellis/workflow.md`, hooks, runtime scripts, or task schema.

Preserve existing wording and state names when reading the workflow. Trellis Plus reads the shared continuity rule on each relevant run; removing the project-owned rule and `.trellis/mainline.md` restores the prior Trellis Plus behavior without changing Trellis's workflow parser.

## Verification

- Confirm a plain `$trellis-plus` reads this reference as part of the default set.
- Confirm the record names an approved objective, parent when applicable, mode, ordered work, readiness/dependency evidence, and next decision, or explicitly labels a draft-only import as unapproved.
- Confirm approved source requirements import without redundant approval, conflicting drafts remain unresolved, and source documents stay intact.
- Confirm rerunning import preserves accepted decisions and does not duplicate work rows; task start, accepted changes, checks, and archive update the record.
- Confirm the shared continuity rule is in `.trellis/spec/trellis-plus/`.
- Confirm `.trellis/workflow.md` and other protected Trellis files were not modified or staged.
- Forward-read a no-record request: it reports evidence and asks for direction.
- Forward-read `guided`: it recommends but does not create work or edit code.
- Forward-read authorized `serial`: it advances one ready listed child through normal create/plan/implement/check/commit/archive flow, then returns to Pulse.
- Confirm ambiguous, dirty, risky, scope-changing, or blocked work stops for a user decision.
- Confirm no workflow text claims `completed` runs after archive and no new scheduler, daemon, hook, or task schema was introduced.
