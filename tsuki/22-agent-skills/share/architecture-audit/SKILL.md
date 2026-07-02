---
name: architecture-audit
description: "Audit a software project's architecture, architecture documents, Trellis specs/tasks/workflow fit, module boundaries, dependency direction, maintainability, extensibility, and fit to engineering best/major practices. Use when the user asks to review whether a project's architecture is reasonable, whether an existing architecture design or Trellis spec satisfies requirements, whether the project is low-coupling/high-cohesion, or how to evolve the codebase toward better architecture."
---

# Architecture Audit

## Purpose

Use this skill to inspect a repository as an engineering system, not just as isolated code. Ground every conclusion in project evidence, then guide the project toward lower coupling, higher cohesion, clearer boundaries, easier extension, and easier maintenance.

Prefer concrete project fit over generic architecture slogans. A small script repo does not need the same structure as a distributed service; a product with compliance, data integrity, or deployment risk needs stronger design records and validation gates.

## Operating Rules

- Respond in the user's language unless they ask otherwise.
- Read repository evidence before judging. Do not infer architecture quality from directory names alone.
- Separate confirmed facts, reasoned inferences, and open questions.
- Prefer incremental, behavior-preserving evolution over big rewrites unless the current design blocks delivery or creates clear operational risk.
- Treat "best practice" as context-sensitive major practice: explain why a practice fits this project's scale, team, domain, risk, and change rate.
- When proposing changes, include the smallest useful next step, the validation needed, and the expected reduction in coupling, ambiguity, or risk.

## Discovery Workflow

1. Establish project shape:
   - Identify languages, frameworks, runtimes, package managers, entrypoints, build/test commands, deployment files, data stores, external services, generated code, and monorepo/workspace boundaries.
   - Read project instructions such as `README*`, `AGENTS.md`, `CLAUDE.md`, `.codex/**`, `.github/workflows/**`, `Makefile`, `justfile`, manifests, and package/workspace files.
2. Find architecture intent:
   - Search for `docs/**`, `architecture`, `design`, `adr`, `rfc`, `decision`, `proposal`, `system`, `overview`, `roadmap`, diagrams, and domain model files.
   - Check whether architecture decisions live in issue specs, Trellis files, task specs, or agent skill/workflow files.
   - In Trellis projects, inspect `.trellis/workflow.md`, `.trellis/spec/**/index.md`, `.trellis/tasks/**/task.json`, and related task notes as architecture-intent sources.
3. Compare intent to implementation:
   - Map major modules/packages/components to responsibilities.
   - Trace dependency direction across layers, packages, services, UI/state/data boundaries, and shared utilities.
   - Check whether runtime entrypoints match documented flows.
   - Verify tests and CI cover the architectural contracts that matter.
4. If architecture design exists:
   - Evaluate whether it states goals, non-goals, constraints, quality attributes, component boundaries, data ownership, APIs/contracts, deployment topology, operational concerns, risks, and decision rationale.
   - Report drift between design and code as explicit findings.
5. If no credible architecture design exists:
   - State that no authoritative architecture design was found and list the searched locations.
   - Continue with a lightweight inferred architecture map from code evidence if enough exists.
   - Ask whether the user wants a first architecture design/ADR drafted before making broad structural changes.

## Trellis Adaptation

When `.trellis/` exists, treat Trellis as part of the architecture evidence model:

- Treat `.trellis/spec/**` as durable product and architecture intent when specs describe components, data flows, user journeys, constraints, or acceptance criteria.
- Treat `.trellis/tasks/**` as planned or in-progress change evidence, not necessarily as final architecture.
- Treat `.trellis/workflow.md` as governance evidence: check whether the workflow asks for design review, validation, human feedback, architecture docs, or task completion gates.
- Report whether architecture gaps belong in an ADR, a Trellis spec update, a workflow rule, or a task-local note. Prefer the narrowest durable location that matches the project's existing Trellis conventions.
- Do not apply `$trellis-plus` enhancements unless the user asks for Trellis workflow changes. This skill audits architecture; Trellis workflow injection is a separate concern.

## Evaluation Dimensions

Use the relevant dimensions for the project. Skip dimensions that do not apply, and say when evidence is missing.

- Requirements fit: current design supports the known user journeys, domain rules, non-functional requirements, and expected change areas.
- Cohesion: each module has a clear reason to change; domain logic is not scattered across unrelated layers.
- Coupling: dependencies point inward or downward in a deliberate direction; shared code does not become an implicit dependency hub.
- Boundaries: UI, application orchestration, domain rules, infrastructure, persistence, external APIs, and generated code are separated where the project scale justifies it.
- Contracts: interfaces, schemas, events, API clients, configuration, and persistence models have clear ownership and compatibility expectations.
- Extensibility: common future changes can be added by extending a bounded area rather than editing many unrelated files.
- Maintainability: naming, file layout, error handling, logging, configuration, migration, and dependency management make routine changes understandable.
- Testability: important rules can be tested without full production infrastructure; integration and end-to-end checks exist where unit seams are insufficient.
- Operational readiness: deploy, rollback, observability, security, secrets, data migration, performance, and failure modes match project risk.
- Governance: architecture decisions are recorded when they affect long-term structure, data contracts, or cross-team work.

## Findings

Prefer evidence-backed findings over broad advice. Each finding should include:

- Severity: `critical`, `high`, `medium`, or `low`.
- Evidence: file paths, commands, dependency traces, or design-doc excerpts.
- Impact: what breaks, slows delivery, blocks extension, or increases operational risk.
- Recommendation: a concrete change with the smallest reasonable scope.
- Validation: how to prove the change preserved behavior and improved the architecture.

Avoid presenting style preferences as architecture findings. If a recommendation is optional or taste-based, label it as a tradeoff.

## Evolution Guidance

When the user asks to improve the architecture, proceed in this order:

1. Protect behavior with the repository's existing tests or a small targeted test harness.
2. Stabilize boundaries before moving code: introduce interfaces/contracts, clarify ownership, or split dependency hubs only where the call graph shows real coupling.
3. Move responsibilities in thin vertical steps. Keep each step reviewable and reversible.
4. Update architecture docs or ADRs when a change establishes a durable boundary, data contract, deployment assumption, or tradeoff.
5. Re-run validation and summarize remaining architecture debt.

Do not introduce heavyweight patterns by default. Use layered architecture, hexagonal/ports-and-adapters, clean architecture, DDD, event-driven design, plugin systems, or microservices only when the project evidence shows the pattern solves a current or near-term problem.

## Output Shape

For an audit, produce:

1. Architecture summary: what the system appears to be and its main moving parts.
2. Design-document status: found, missing, stale, or partial; include searched locations.
3. Findings: ordered by severity, with evidence and recommendations.
4. Evolution roadmap: immediate, next, and later steps; keep it practical.
5. Open questions: only questions that materially affect the architectural judgment.

For a design-drafting request, produce a concise architecture design or ADR that includes context, goals, non-goals, constraints, chosen structure, component responsibilities, dependency rules, data/contracts, operational considerations, alternatives, risks, and validation plan.
