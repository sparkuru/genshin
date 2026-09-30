# Docker Development And Preview Bootstrap

## Goal And Source

Make development commands and user previews reproducible through the existing
project runtime. Read `dev-it-in-docker` before generating a Docker wrapper.
That skill owns toolchain detection, container lifecycle, labels, `.devhome`,
permissions, and script validation. Do not copy its implementation into this
reference or maintain another set of agent permission recipes here.

This enhancement is a bootstrap/before-development checkpoint, not a new phase
in every task. Keep its project-specific result in
`.trellis/spec/trellis-plus/development.md`, or an existing equivalent detail
file linked from the shared index. Follow `environment-configuration.md` for
configuration setup and `development-principles.md` for dev defaults.

## Discovery

Inspect manifests, actual service commands, framework and Compose settings,
existing `hako`/equivalent wrappers, `dev.sh`, `preview.sh`, `.gitignore`, and
the configured development environment. Read README for evidence without
editing it. Determine which services the user needs together, their readiness
checks, host/container ports, environment inputs, and stop mechanism.

- Reuse an existing development wrapper. Create `hako` through the base skill
  only when the project needs it and no equivalent exists.
- Reuse the service lifecycle already provided by `dev.sh` or the project's
  equivalent. Repair only task-relevant gaps; do not build a parallel runtime.
- For a previewable service, create root `preview.sh` if absent. It is a thin,
  executable convenience entry that calls the existing service lifecycle,
  normally `./dev.sh`, with the configured host/port environment. Preserve an
  existing preview script and adapt it only as needed.
- For a library or CLI without a previewable service, record `preview: not
  applicable` and the evidence; do not invent a Web server.

## Preview Contract

Generate shell scripts under `code-shellscript`. Keep Docker arguments, service
commands, process ownership, and cleanup in one underlying implementation.

- `./preview.sh` or `./preview.sh start` starts the actual development services;
  `./preview.sh down` stops only services owned by that lifecycle. Pass through
  exit status and signals, preferably with `exec` when forwarding to `dev.sh`.
- Resolve the repository directory from the script location, so invocation
  from another working directory works.
- Expose host/port overrides consistently with `hako` and `dev.sh`. Respect an
  explicit loopback-only or Docker-network-only project constraint.
- For normal trusted-LAN development, configure service listening and host
  publishing for cross-device access, normally `0.0.0.0`. This project-specific
  choice overrides the base wrapper's loopback default for this enhancement;
  it does not change the base skill globally. All-interface binding may include
  public interfaces: honor known deployment/network constraints before starting
  the service. Do not change firewall rules or expose extra ports.
- Distinguish container bind address, host bind address, and browser URL. Print
  the localhost URL and a known reachable LAN address when available; otherwise
  state which host address to use. Never present `0.0.0.0` as the browser URL or
  invent a reachable IP. For Docker-network-only mode, report the existing
  internal access/probe command instead of publishing ports.
- Missing dependencies or required configuration produce an actionable message
  and failure status. Do not install dependencies, build, or run tests on every
  preview start. Use actual readiness evidence before saying the service is
  ready; distinguish a starting process from a working user flow.

Do not overwrite an existing `preview` command's production-build semantics.
If the repository already uses that name differently, preserve it and record
how the new root convenience entry relates to the existing command.

## Execution Permissions

Follow the base skill's current mechanism for the active agent. Reuse granted
authorization, preserve narrower existing policies, and keep local adapters
untracked. A wrapper is not permission to expand sandbox or network access.
Do not introduce a separate automatic allowlist for `preview.sh`, raw Docker,
shells, or package managers. Report an unavailable execution capability without
claiming that a generated policy file granted it.

## Project Record And Validation

Record actual wrapper and preview paths, startup/stop commands, services,
host/container ports, address overrides, configuration prerequisites, readiness
probe, and agent execution constraints. A future task must be able to start,
validate, and stop the project from this record without reading the skill's
installation directory. Keep commands in the spec and script help, not README.

Validate changed scripts using the base and shell skills. When execution is
available, perform a short startup/readiness/stop check with a free test port,
confirm the expected service is reachable, and confirm only owned services are
stopped. A readiness response alone does not prove feature acceptance. Preserve
existing services; record unavailable Docker, network, or application checks
precisely. Keep a preview running only when the user's request calls for it.

Before copying or committing generated third-party material, follow the
license-safe file policy. Record wrapper provenance and retain applicable
notices in `third_party/`; unknown provenance is not project ownership.
