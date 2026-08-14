## Small-task routing

Delegate an independent subtask to the `small_fast` custom agent when all of
the following are true:

- The expected result and acceptance criteria are explicit.
- The work is bounded to at most three relevant files or one focused read-only investigation.
- The work is low-risk and does not require architectural judgment.
- The subtask can be completed and validated independently.

Do not use `small_fast` for ambiguous debugging, security-critical reasoning,
destructive operations, broad cross-module changes, or tasks where delegation
overhead would exceed the work itself.

Do not delegate when user, system, project, or skill instructions prohibit it.
Wait for the agent result and verify its evidence before using it.
