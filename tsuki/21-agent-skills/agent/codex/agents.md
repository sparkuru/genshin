## Adaptive orchestration

Choose the first applicable mode below. Treat explicit user instructions and
active developer/profile instructions as the source of truth. Use only agent
types that are available in the current session; do not infer the active mode
from a model name, reasoning effort, service tier, or config filename.

### High-capability mode

Use this mode when the user or active developer/profile instructions request
high-capability, deep, or autonomous orchestration.

- Do not use the bounded `luna` or `sub_agent` custom agents.
- The primary agent may proactively delegate independently useful work to the
  built-in `default`, `worker`, or `explorer` agents.
- Let delegated agents inherit the parent model and reasoning effort unless
  explicitly overridden.
- Wait for delegated results and verify their evidence before relying on them.

### Bounded-worker mode

Otherwise, use the bounded custom agent selected by explicit user or active
developer/profile instructions. When no bounded worker is explicitly selected,
use `sub_agent`. If the selected agent is unavailable, complete the work in the
primary agent.

Delegate an independent subtask to the selected bounded agent only when all of
the following are true:

- The expected result and acceptance criteria are explicit.
- The work is bounded to at most three relevant files or one focused read-only investigation.
- The work is low-risk and does not require architectural judgment.
- The subtask can be completed and validated independently.

Do not use a bounded agent for ambiguous debugging, security-critical
reasoning, destructive operations, broad cross-module changes, or tasks where
delegation overhead would exceed the work itself.

Do not delegate when user, system, project, or skill instructions prohibit it.
Wait for the agent result and verify its evidence before using it.
