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
- Prefer Docker-backed preview startup, reusing the project's Docker/Compose
  lifecycle. If project constraints require another runtime, record the reason
  and actual startup path; do not silently fall back to host execution.
- For a previewable service, create root `preview.sh` if absent. It is a thin,
  executable convenience entry that calls the existing service lifecycle,
  normally `./dev.sh`, with the configured host/port environment. Preserve an
  existing preview script and adapt it only as needed.
- For a library or CLI without a previewable service, record `preview: not
  applicable` and the evidence; do not invent a Web server.

## Preview Contract

Generate shell scripts under `code-shellscript`. Keep Docker arguments, service
commands, process ownership, and cleanup in one underlying implementation.
Before creating, adapting, or checking preview output, read
[Mandatory Preview Console Contract](preview-console-contract.md). Its format,
host-side `ip -br a` enumeration, and readiness rules are required across all
projects and frameworks; preserve project-specific startup procedures behind
that shared output contract.

- `./preview.sh` or `./preview.sh start` starts the actual development services;
  `./preview.sh stop` stops only services owned by that lifecycle and preserves
  persistent data. Map `stop` to the existing runtime's stop/down operation as
  appropriate; support `down` as the data-preserving teardown alias. Start services
  in the background, wait for readiness, print the summary, and return control
  so the user can manage them with `start`/`stop`. Repeated calls must not create
  duplicate services or fail merely because services are already stopped.
  Pass through failures and handle signals consistently with the underlying
  lifecycle; keep readiness and summary output there if forwarding with `exec`.
- Provide `status` to show the actual service state and health, and `build` to
  explicitly build preview images through the same lifecycle. Neither command
  should start services implicitly. Document `build` then `start` for first use
  or changes requiring an image rebuild; ordinary startup reuses prepared images.
- Resolve the repository directory from the script location, so invocation
  from another working directory works.
- Load primary preview configuration from the repository's `.env`: account
  names/passwords, variable Docker settings, and every service's listening host
  and port, including host publishing settings. Follow the preview requirements
  in `environment-configuration.md`; keep `hako`, `dev.sh`, and the application
  on the same configuration path. Respect an explicit loopback-only or
  Docker-network-only project constraint.
- For normal trusted-LAN development, configure service listening and host
  publishing for cross-device access, normally `0.0.0.0`. This project-specific
  choice overrides the base wrapper's loopback default for this enhancement;
  it does not change the base skill globally. All-interface binding may include
  public interfaces: honor known deployment/network constraints before starting
  the service. Do not change firewall rules or expose extra ports.
- After successful one-command startup, print a console summary of **all
  listening host:port endpoints of the preview services**, labeled by service,
  with container endpoints and published host mappings distinguished. Use the
  effective runtime values, including dynamically assigned ports, rather than
  hard-coded defaults. Put service-grouped browser URLs first, one complete URL
  per line, using the exact sections in `preview-console-contract.md`. Wildcard
  host publishing must enumerate all eligible host addresses, not just one LAN
  hint. Keep local-only URLs and internal endpoints in their designated sections.
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
host/container ports, `.env` keys and loading/override order, configuration
prerequisites, readiness probe, the mandatory console contract and host address
discovery procedure, and agent execution constraints. A future task must be
able to build, start, inspect, and stop the project without reading the skill's
installation directory. Keep commands in the spec and script help, not README.

For projects with locally built images, include these first-use commands in the
handoff after environment setup, and explain when rebuilding is needed:

```sh
./preview.sh build
./preview.sh start
```

Also document `./preview.sh status` and `./preview.sh stop` (or `down`), with
explicit confirmation that stopping preserves data volumes.

Validate changed scripts using the base and shell skills. When execution is
available, exercise `./preview.sh start` and `./preview.sh stop` with a free test port,
check the renderer fixtures in `preview-console-contract.md`, confirm all preview
listeners, published mappings, and enumerated host URLs appear in their required
sections,
verify printed browser URLs are reachable from the intended access environment,
and confirm only owned services are stopped and persistent data is preserved.
Check `build`, `status`, the `down` alias, repeated start/stop behavior, and that
a failed readiness check never prints the success banner. Change a host/port setting in a
temporary `.env` fixture and verify startup and printed addresses both reflect
it. A readiness response alone does not prove feature acceptance. Preserve
existing services; record unavailable Docker, network, or application checks
precisely. Keep a preview running only when the user's request calls for it.
Report syntax, ShellCheck, formatting, and real-container checks separately
from unverified HTTPS/domain or physical-device LAN access. Preserve existing
`.env` values when wiring configuration; report any required migration without
exposing secrets. Record the durable contract and its loading steps in the
project-owned spec, never in protected Trellis upstream files.

Before copying or committing generated third-party material, follow the
license-safe file policy. Record wrapper provenance and retain applicable
notices in `third_party/`; unknown provenance is not project ownership.
