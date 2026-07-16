---
name: repo-audit
description: "Audit a software repository as an engineering system. Use when the user asks whether a repository's architecture, module boundaries, dependency direction, maintainability, extensibility, design documentation, tests, CI, deployment posture, or engineering practices are reasonable; or asks for evidence-backed, incremental improvements."
---

# Repository Audit

Inspect a repository as an engineering system, not merely as isolated code. Ground conclusions in repository evidence, distinguish confirmed facts from inferences and open questions, and recommend the smallest useful, behavior-preserving change.

## Audit Modules

Select the narrowest module that covers the user's question. Read every selected module before auditing. Do not apply a module's rules when its scope is not relevant.

- **Architecture and evolution**: Read [reference/architecture-audit.md](reference/architecture-audit.md) when assessing project structure, architecture documents, Trellis specs/tasks/workflow fit, responsibility boundaries, dependency direction, maintainability, extensibility, testability, operational readiness, or architecture evolution. This is the default module until other audit modules exist.

Add future audit concerns as sibling files under `reference/` and register them here with a clear selection rule. Keep cross-cutting rules in this file; keep detailed, concern-specific workflows in their module.

## Shared Rules

- Respond in the user's language unless they ask otherwise.
- Read the relevant repository evidence before judging; never infer quality from directory names alone.
- Treat "best practice" as context-sensitive major practice. Explain fit to the project's scale, team, domain, risk, and change rate.
- Prefer incremental evolution over a big rewrite unless the current design blocks delivery or creates clear operational risk.
- For each recommendation, give the smallest useful next step, validation, and the expected reduction in coupling, ambiguity, or risk.

## Output

State the audit scope and selected modules. Present evidence-backed findings in severity order, then a practical evolution roadmap and only the open questions that materially affect the judgment.
