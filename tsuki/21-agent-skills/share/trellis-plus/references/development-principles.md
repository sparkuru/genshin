# Development-Stage Project Principles

## Applicability And Injection

Record these rules in `.trellis/spec/trellis-plus/development-principles.md`,
linked by the shared index and loaded at task start. Reuse an existing
project-owned equivalent. Retain the actionable rules below when adapting the
wording; a slogan or pointer to an unavailable skill is not sufficient.

Default to a system under active development unless repository evidence or the
user identifies released behavior, real users, external consumers, production
data, or a compatibility contract. Record those exceptions per affected
surface; one released interface does not make every prototype immutable, and
the label `dev` does not erase real data or existing commitments.

## Development Access And Interaction

For trusted-LAN development, allow the intended browser/device access path,
normally using configurable `0.0.0.0` listening and host publishing. Preserve
explicit network restrictions and known untrusted-network constraints. Follow
the Docker/preview profile for the exact commands and addresses.

Reduce unnecessary dev-only login, password, CAPTCHA, session-expiry, and
initialization friction when it obstructs repeated functional testing. Use an
explicit development configuration, separate credentials, and the existing
authentication design. Do not commit secrets, reuse production credentials,
weaken production defaults, or silently disable the behavior a test is meant
to validate. Dev convenience is not authority to remove authentication on an
untrusted network.

## Scope And Implementation

- Solve the current requirement and clearly evidenced near-term needs. Prefer
  direct code over speculative abstractions, plugin/provider/factory systems,
  feature flags, state machines, caches, and fallback chains.
- Inspect and reuse existing components, helpers, models, API clients, error
  handling, state management, configuration, and test facilities. Modify their
  real execution path rather than creating a parallel service or wrapper.
- For unreleased behavior without a compatibility obligation, change the
  implementation, schema, and callers together. Remove superseded paths and
  names instead of adding legacy aliases, dual interfaces, adapters,
  deprecated wrappers, or migration chains for discarded prototypes.
- Preserve data unless its disposability is established and the requested
  operation authorizes replacement. A disposable development database may use
  a direct rebuild; `dev` alone never authorizes deleting unknown data.
- Keep the diff limited to the requested outcome. Do not bundle nearby
  refactoring, renaming, mass formatting, directory rearrangement, dependency
  upgrades, or unrelated bug fixes. Include a discovered issue only if it
  blocks or invalidates the current result, or the user requests it.
- Add a dependency only for a concrete benefit that existing dependencies,
  standard facilities, or a small local implementation cannot reasonably
  supply. Do not add a framework to save a few lines.
- Handle expected failures clearly. Add guards or recovery paths for actual
  contracts and plausible failures, not an exhaustive set of unsupported
  hypothetical states.

## Diagnosis And Verification

Before fixing a bug, establish current behavior, reproduce it when possible,
and gather evidence for the root cause and the real execution path. When
reproduction is unavailable, state the limitation and distinguish a hypothesis
from a confirmed cause. Do not simultaneously rewrite code, contracts, and
tests around a guess and then cite the new tests as proof of the original bug.

Validate user behavior and agreed contracts. Do not weaken assertions to fit
incorrect code, mock away the behavior under test, cover only favorable
branches, or suppress errors to get a green result. Use controlled fixtures
for unavailable dependencies while naming what they do not verify.

Run the smallest useful existing checks and real execution when available:
UI interaction and final state, API requests/responses and mutations, or CLI
arguments, output, and exit status. Build, lint, types, unit tests, a loaded
page, and HTTP 200 each prove only their own scope. Report implemented but
unverified behavior explicitly.

Keep validation proportional. A local change does not automatically require
a new framework, checker, script, manifest, CI gate, audit document, multiple
agents, or repeated reviews. Reuse existing commands; introduce lasting
regression coverage when it protects a meaningful requirement. Browser and
mobile checks follow the project's validation profile.

Expose failures promptly. Do not swallow exceptions, supply a success-looking
default, silently fall back to old behavior, hide invalid configuration, or
downgrade a missing critical resource into an ignorable warning.

## Workspace, Documentation, And Continuity

Treat pre-existing changes as user-owned. Do not revert, overwrite, reset,
clean unknown files, or stage unrelated changes. If a touched area overlaps
existing work, inspect it and preserve its intent.

README is human-owned project presentation. Read it for context; create or
edit it only when the user explicitly requests that work. Store durable agent
development rules and command profiles in the project-owned Trellis Plus
specs. Keep necessary script help local to the script. Do not create redundant
guides, design documents, migration notes, changelogs, TODOs, or comments to
make a small change look complete. Required Trellis task artifacts still
belong in the normal task tree.

Remove task-created temporary debug code, disposable fixtures, and scratch
files when finished; retain intentional tests and task evidence. Do not delete
unknown artifacts during cleanup.

At task start and after a long interruption, read the approved mainline,
current task acceptance criteria, and shared policy. Keep the original scope
and constraints active throughout the work. Update mainline from approved
requirement changes and verified results, not from whatever the implementation
happened to produce. Follow the mainline continuity reference for transitions.

## Review Evidence

Before completion, identify the requested behavior, the checks that actually
exercised it, and any unverified portion. Confirm the diff has no unrelated
cleanup, speculative compatibility paths, accidental dependencies, README
expansion, or user-work loss. Record only meaningful exceptions and decisions
in the existing task evidence; do not create another audit system.
