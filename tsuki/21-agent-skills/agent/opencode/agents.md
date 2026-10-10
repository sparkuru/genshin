## Adaptive orchestration

Choose the first applicable mode below. Treat explicit user instructions and
active system/profile instructions as the source of truth. Use only agents
available in the current session; do not infer the active mode from a model
name, reasoning effort, service tier, or config filename.

### High-capability mode

Use this mode when the user or active system/profile instructions request
high-capability, deep, or autonomous orchestration.

- Do not use bounded custom agents such as `sub_agent`.
- The primary agent may proactively delegate independently useful work to
  available agents. In OpenCode, use `general` for execution and `explore` for
  focused read-only codebase investigation.
- Let delegated agents inherit the parent model unless explicitly overridden.
- Wait for delegated results and verify their evidence before relying on them.

### Bounded-worker mode

Otherwise, use the bounded custom agent selected by explicit user or active
system/profile instructions. When no bounded worker is explicitly selected,
use `sub_agent`. If the selected agent is unavailable, complete the work in
the primary agent.

Delegate an independent subtask to the selected bounded agent only when all of
the following are true:

- The expected result and acceptance criteria are explicit.
- The work is bounded to at most three relevant files or one focused read-only
  investigation.
- The work is low-risk and does not require architectural judgment.
- The subtask can be completed and validated independently.

Do not use a bounded agent for ambiguous debugging, security-critical
reasoning, destructive operations, broad cross-module changes, or tasks where
delegation overhead would exceed the work itself.

Do not delegate when user, system, project, or skill instructions prohibit it.
Wait for the agent result and verify its evidence before using it.
