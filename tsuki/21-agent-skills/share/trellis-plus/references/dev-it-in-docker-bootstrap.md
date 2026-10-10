# Docker Development And Preview Bootstrap

## Goal And Source

Make development commands and user previews reproducible through the existing project runtime. Read `dev-it-in-docker` before generating a Docker wrapper. That skill owns toolchain detection, container lifecycle, labels, `.devhome`, permissions, and script validation. Do not copy its implementation into this reference or maintain another set of agent permission recipes here.

This enhancement is a bootstrap/before-development checkpoint, not a new phase in every task. Keep its project-specific result in `.trellis/spec/trellis-plus/development.md`, or an existing equivalent detail file linked from the shared index. Follow `environment-configuration.md` for configuration setup and `development-principles.md` for dev defaults.

## Discovery

Inspect manifests, actual service commands, framework and Compose settings, existing `hako`/equivalent wrappers, `dev.sh`, `preview.sh`, `.devhome`, environment examples/loaders, local-file ignore rules, and the configured development environment. Inspect local configuration keys without revealing secret values. Read README for evidence without editing it. Determine which services the user needs together, their readiness checks, host/container ports, environment inputs, and stop mechanism.

- Reuse an existing development wrapper. Create `hako` through the base skill only when the project needs it and no equivalent exists.
- Reuse the service lifecycle already provided by `dev.sh` or the project's equivalent. Repair only task-relevant gaps; do not build a parallel runtime.
- Prefer Docker-backed preview startup, reusing the project's Docker/Compose lifecycle. If project constraints require another runtime, record the reason and actual startup path; do not silently fall back to host execution.
- For a previewable service, create root `preview.sh` if absent. It is a thin, executable convenience entry that calls the existing service lifecycle, normally `./dev.sh`, with the configured host/port environment. Preserve an existing preview script and adapt it only as needed.
- For a library or CLI without a previewable service, record `preview: not applicable` and the evidence; do not invent a Web server.

## Reference Script And Project Integration

Read [assets/refer-preview.sh](../assets/refer-preview.sh) when implementing or adapting the preview CLI. It is a Bash 4.4+ reference for the shared presentation and command-dispatch layer, not another Docker lifecycle. Run it directly with `--help` or `--demo` to inspect the interface without starting services. Normal lifecycle commands require a project adapter; the reference fails explicitly if invoked directly with `start`/`stop`/`status`/`build`.

For a new Bash entry, copy the reference into a project-owned path such as `scripts/preview-console.sh`, then source it once from `preview.sh` or the existing lifecycle. Keep the copy in the repository; never source the skill installation by an absolute machine path. Sourcing does not change shell options, install traps, load `.env`, print output, or invoke Docker. The caller owns strict mode and traps. Existing equivalent renderers may retain their implementation if they satisfy the same observable contract; do not add a second renderer or overwrite an existing adapter.

The reference provides:

- `preview_log`, `preview_warn`, `preview_error`: stderr lines with `[log]`, `[warn]`, `[error]`; cyan, yellow, and red respectively. Titles are bold cyan, section headings bold green, and readiness green. Color is enabled only for the actual destination TTY, with resets; `NO_COLOR` and `TERM=dumb` disable it. URL lines remain plain. These helpers accept already-safe messages; lifecycle logs still require project-specific redaction before calling them.
- `preview_usage`, `preview_main`: default/start, stop/down, status, build, `--verbose`, and `--help`; usage errors return 2, help returns 0, lifecycle exit codes propagate. `down` dispatches to the data-preserving stop adapter. Help does not load configuration or call an adapter. The project supplies concrete host prerequisites, required keys, loading order, and setup/rebuild information through `preview_help_*` values and its development spec.
- `preview_script_root`, `preview_require_command`, `preview_require_env_file`: path and prerequisite checks; the env helper checks existence only and never sources dotenv as shell code.
- `preview_summary_reset`, `preview_add_url`, `preview_add_line`, `preview_render_summary`: render the console contract's nonempty sections in order, grouping entries by service and deduplicating entry URLs. URL checks reject whitespace, authenticated URLs, wildcard destinations, and loopback URLs in `Open`; they are not full address or secret validation. The project supplies all actual listeners/mappings, local/internal scopes, eligible discovered addresses, routes, and notes. Set `preview_summary_ready=true` only after all required readiness checks pass; a success summary also requires at least one actual listener line.

Adapter shape (replace the illustrative `dev.sh` commands and flag mapping with the repository's verified lifecycle interface):

```bash
#!/usr/bin/env bash
set -Eeuo pipefail
script_dir=${BASH_SOURCE[0]%/*}
[[ $script_dir != "${BASH_SOURCE[0]}" ]] || script_dir=.
repo_root=$(cd -- "$script_dir" && pwd -P)
source "$repo_root/scripts/preview-console.sh"
preview_program=./preview.sh
preview_help_requirements='Docker daemon; required keys documented in .env.example'
preview_help_runtime='dev.sh loads root .env; see the development spec for precedence'
project_preview_run() {
    local -a args=("$1")
    [[ $preview_verbose != true ]] || args+=(--verbose)
    "$repo_root/dev.sh" "${args[@]}"
}
project_preview_start() { project_preview_run start; }
project_preview_stop() { project_preview_run stop; }
project_preview_status() { project_preview_run status; }
project_preview_build() { project_preview_run build; }
preview_main "$@"
```

The underlying lifecycle loads and validates `.env`, prepares missing resources, owns labels/signals/cleanup, discovers runtime addresses, checks readiness, and prints one summary. Use the reference renderer there if needed; the thin entry must not print a second summary. `preview_verbose` is a boolean request that the adapter translates to the lifecycle's real interface; it does not make raw logs safe. A lifecycle using this renderer calls `preview_summary_reset`, adds each browser URL with `preview_add_url open|local LABEL SERVICE URL`, adds single lines with `preview_add_line listeners|published|internal|notes LINE`, then marks readiness and calls `preview_render_summary`. Include all services' listeners, all published mappings, and applicable discovery/access limitations; omit sections only when they are actually empty.

## Preview Contract

Generate shell scripts under `code-shellscript`. Keep Docker arguments, service commands, process ownership, and cleanup in one underlying implementation. Before creating, adapting, or checking preview output, read [Mandatory Preview Console Contract](preview-console-contract.md). Its format, host-side `ip -br a` enumeration, and readiness rules are required across all projects and frameworks; preserve project-specific startup procedures behind that shared output contract.

- `./preview.sh` or `./preview.sh start` starts the actual development services; `./preview.sh stop` stops only services owned by that lifecycle and preserves persistent data. Map `stop` to the existing runtime's stop/down operation as appropriate; support `down` as the data-preserving teardown alias. Start services in the background, wait for readiness, print the summary, and return control so the user can manage them with `start`/`stop`. Repeated calls must not create duplicate services or fail merely because services are already stopped. Pass through failures and handle signals consistently with the underlying lifecycle; keep readiness and summary output there if forwarding with `exec`.
- Provide `status` to show the actual service state and health, and `build` to explicitly build preview images through the same lifecycle. Neither command should start services implicitly. After environment setup, ordinary `start` prepares missing images and dependencies as described below; keep `build` as the explicit rebuild entry for changes requiring an image rebuild. `status`, `stop`, `down`, and help must not install, build, or start services.
- Resolve the repository directory from the script location, so invocation from another working directory works.
- Load primary preview configuration from the repository's `.env`: account names/passwords, variable Docker settings, and every service's listening host and port, including host publishing settings. Follow the preview requirements in `environment-configuration.md`; keep `hako`, `dev.sh`, and the application on the same configuration path. Respect an explicit loopback-only or Docker-network-only project constraint.
- For normal trusted-LAN development, configure service listening and host publishing for cross-device access, normally `0.0.0.0`. This project-specific choice overrides the base wrapper's loopback default for this enhancement; it does not change the base skill globally. All-interface binding may include public interfaces: honor known deployment/network constraints before starting the service. Do not change firewall rules or expose extra ports.
- After successful one-command startup, print a console summary of **all listening host:port endpoints of the preview services**, labeled by service, with container endpoints and published host mappings distinguished. Use the effective runtime values, including dynamically assigned ports, rather than hard-coded defaults. Put service-grouped browser URLs first, one complete URL per line, using the exact sections in `preview-console-contract.md`. Wildcard host publishing must enumerate all eligible host addresses, not just one LAN hint. Keep local-only URLs and internal endpoints in their designated sections.
- Missing host prerequisites, invalid configuration, or failed preparation produce an actionable message and failure status. Reuse existing resources; do not unconditionally install or build on every start, and never run tests automatically as part of preview startup. Use actual readiness evidence before saying the service is ready.

Do not overwrite an existing `preview` command's production-build semantics. If the repository already uses that name differently, preserve it and record how the new root convenience entry relates to the existing command.

## First-Use Preparation

Default to `cp .env.example .env`, edit required values, then `./preview.sh`. Perform preparation in the existing lifecycle, keeping `preview.sh` thin:

1. Parse and validate configuration, host prerequisites, the effective Docker endpoint, and any required host-address discovery before preparing resources.
2. Check for existing owned preview services first. Reuse a healthy instance only when its effective configuration matches. Report incomplete, unhealthy, or changed instances with an explicit recovery command; do not silently remove or recreate them.
3. With no existing instance, build a missing configured development image through the existing build operation. Reuse an available image; do not rebuild it merely because `start` was called.
4. Install missing project dependencies inside the development container, reusing the wrapper's user/group, mounts, and home/cache convention. Use the package manager's locked/frozen installation mode; do not rewrite manifests or lockfiles. Define project-specific readiness checks for required dependency entries and repeat them after installation. Report what those checks cannot detect, such as stale versions after a branch or lockfile change.
5. Create the service group only after preparation succeeds, then run the existing readiness checks and console renderer. Preparation failure returns nonzero with no partially started service group or success summary.

Installation containers must not publish ports or receive runtime credentials through environment injection. Disable automatic dotenv loading when supported (for example, Bun's `--no-env-file`); a mounted source tree can still expose `.env`, so this does not provide file isolation. Use the actual package manager and dependency paths, not fixed framework entry names.

Print concise preparation stage messages to stderr. Capture detailed build and install output in temporary files, showing redacted details on failure or in explicit verbose mode; document whether verbose output streams or appears after each step. Helpers must return failures to this reporting layer rather than exit before it can show captured diagnostics. Remove temporary logs on exit.

Explicit offline, no-install, or other project constraints override automatic preparation; document the supported manual setup and actionable failure. First use may require downloads and several minutes. This is fewer manual commands, not a promise of instant or network-free startup.

## Execution Permissions

Follow the base skill's current mechanism for the active agent. Reuse granted authorization, preserve narrower existing policies, and keep local adapters untracked. A wrapper is not permission to expand sandbox or network access. Do not introduce a separate automatic allowlist for `preview.sh`, raw Docker, shells, or package managers. Report an unavailable execution capability without claiming that a generated policy file granted it.

## Project Record And Validation

Record actual wrapper and preview paths, startup/stop commands, services, host/container ports, `.env` keys and loading/override order, configuration prerequisites, readiness probe, the mandatory console contract and host address discovery procedure, preparation checks/limitations, and agent execution constraints. Distinguish host-installed prerequisites, required user values, and project resources prepared automatically. A future task must be able to build, start, inspect, and stop the project without reading the skill's installation directory. Keep commands in the spec and script help, not README.

Include the first-use flow in the handoff, substituting actual configuration paths and required keys:

```sh
cp .env.example .env  # only when .env is absent
# edit required values
./preview.sh
```

Also document explicit `build`, `status`, and `stop` (or `down`), explaining when rebuilding is needed and confirming that stopping preserves persistent data. On reapplication, reconcile the project's current requirements, help, and project-owned development spec with this flow. Preserve explicit runtime constraints and do not create a task solely to carry policy when the user has declined task creation.

Validate changed scripts using the base and shell skills. When execution is available, exercise `./preview.sh start` and `./preview.sh stop` with a free test port, check the renderer fixtures in `preview-console-contract.md`, confirm all preview listeners, published mappings, and enumerated host URLs appear in their required sections, verify printed browser URLs are reachable from the intended access environment, and confirm only owned services are stopped and persistent data is preserved. Check `build`, `status`, the `down` alias, repeated start/stop behavior, and that a failed readiness check never prints the success banner. Change a host/port setting in a temporary `.env` fixture and verify startup and printed addresses both reflect it. A readiness response alone does not prove feature acceptance. Preserve existing services; record unavailable Docker, network, or application checks precisely. Keep a preview running only when the user's request calls for it. Report syntax, ShellCheck, formatting, and real-container checks separately from unverified HTTPS/domain or physical-device LAN access. Preserve existing `.env` values when wiring configuration; report any required migration without exposing secrets. Record the durable contract and its loading steps in the project-owned spec, never in protected Trellis upstream files.

For changes to preparation or failure handling, cover the applicable branches with temporary fixtures/stubs: missing image, missing dependencies, both missing, prepared resources, healthy instance reuse, incomplete/unhealthy/changed owned instances, build/install failure (including missing build inputs), installation that still lacks required entries, missing/invalid configuration, older CLI capabilities, unsupported remote endpoints, readiness failure while a watcher remains running, and log-read failure. Verify nonzero failures, no success summary, no leftover newly created service group, preserved `.env`/lockfiles/ user data, and no preparation or startup from status/stop/down/help. Check the redaction and cleanup contract in `preview-console-contract.md`.

When Docker execution is available and authorized, verify first use in an isolated source copy with no dependency directory, a fresh test image name, secret-free configuration, and free/dynamic loopback ports. Check actual HTTP readiness, repeated-start reuse, and stop/down. For default persistent storage, also start from an empty data directory using the example's normal storage mode, confirm data creation and preservation after stop, and verify generated data files are ignored and untracked. An in-memory fixture does not cover that path. Use isolated data for a controlled application startup failure and confirm its real error is visible before cleanup, even if the watcher stays running. Do not reset/delete user databases as an automatic recovery step. Report stub results separately from real build/install/start evidence, and state whether build caches were available; neither proves an uncached/offline cold start.

Before copying or committing generated third-party material, follow the license-safe file policy. Record wrapper provenance and retain applicable notices in `third_party/`; unknown provenance is not project ownership.
