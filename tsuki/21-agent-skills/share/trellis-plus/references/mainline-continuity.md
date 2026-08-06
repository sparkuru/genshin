# Mainline Continuity

## Contents

- [Goal](#goal)
- [Control Record](#control-record)
- [Project Pulse](#project-pulse)
- [Continuation Authority](#continuation-authority)
- [Conductor and Worker Protocol](#conductor-and-worker-protocol)
- [Injection Guidance](#injection-guidance)
- [Verification](#verification)

## Goal

Preserve an approved project direction across task boundaries without creating a
second task system. `.trellis/mainline.md` is a small control record; Trellis
parent and child tasks remain the source of requirements, plans, checks,
commits, and archive history.

## Control Record

Create or update `.trellis/mainline.md` with this template. Keep the ordered
child list explicit; task-tree position does not imply ordering or readiness.

```markdown
# Trellis Mainline

## Initiative

- title: <approved initiative name>
- parent task: <.trellis/tasks/<parent-slug>, or none>
- objective: <user-approved outcome>
- owner decision: <date and concise authorization/source>

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

Use `guided` unless the user explicitly authorizes a bounded serial initiative.
For serial mode, replace `serial authorization: none` with the approved
initiative, allowed child list/order, and stop conditions. Do not infer an
objective, rank an unapproved backlog, or use repository code as authority for
product priority.

## Project Pulse

Run a read-only Project Pulse only for project-relevant no-task requests, such
as continuing work, asking for status or next steps, beginning implementation,
or immediately after a task archive. Read the control record, active and
archived task evidence, git state, and available validation results. Report:

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

Do not run a Pulse merely because the user asks an unrelated question. Do not
use `completed` as a continuation trigger: after archive the active-task
resolver cannot expose that state. Run the next Pulse from the relevant
no-task or post-archive request instead.

## Continuation Authority

| Mode | Default behavior | Authority boundary |
| --- | --- | --- |
| `guided` | Pulse and recommend one action. | Never create a task or edit product files until the user chooses. |
| `serial` | Continue one listed, ready child after a clean archive. | Requires explicit bounded authorization; stop on ambiguity, risk, scope change, or unmet dependency. |
| `paused` | Report state only. | No task creation or implementation. |

Serial authorization substitutes only for repeated consent to create or start a
listed, ready child. It does not waive required PRD/design/plan artifacts,
checks, human-review gates, commit decisions, or archive evidence. A proposed
child becomes work only through the normal Trellis task lifecycle and must be
linked to the declared initiative parent when one exists.

## Conductor and Worker Protocol

The main session owns phase selection, Pulse, acceptance-criteria mapping,
task creation/start, dispatch, commit, archive, and control-record updates.
Research, implementation, and check workers receive only a bounded active task.
They report files changed, validation, and unresolved decisions; they do not
choose the next child, archive independently, perform project-wide cleanup, or
recursively dispatch implement/check workers.

## Injection Guidance

Patch only these durable project files:

1. Create `.trellis/mainline.md` from the control-record template when the
   project has a declared initiative; otherwise leave it absent and keep the
   default conservative behavior.
2. Add a short `Trellis Plus: Mainline Continuity` section to the existing
   `[workflow-state:no_task]` block in `.trellis/workflow.md`. It must say to
   run the read-only Pulse for relevant requests, default to `guided`, honor
   `paused`, and permit serial work only under recorded explicit authorization.
3. Add short pointers elsewhere only if a local command or skill bypasses the
   workflow block. Do not patch hooks, runtime scripts, or task schema.

Preserve existing wording and state names. The existing workflow-state parser
reads the block verbatim, so workflow text is sufficient. Removing the
continuity block and `.trellis/mainline.md` restores the prior behavior.

## Verification

- Confirm a plain `$trellis-plus` reads this reference as part of the default set.
- Confirm the record names an approved objective, parent when applicable, mode,
  ordered work, readiness/dependency evidence, and next decision.
- Forward-read a no-record request: it reports evidence and asks for direction.
- Forward-read `guided`: it recommends but does not create work or edit code.
- Forward-read authorized `serial`: it advances one ready listed child through
  normal create/plan/implement/check/commit/archive flow, then returns to Pulse.
- Confirm ambiguous, dirty, risky, scope-changing, or blocked work stops for a
  user decision.
- Confirm no workflow text claims `completed` runs after archive and no new
  scheduler, daemon, hook, or task schema was introduced.
