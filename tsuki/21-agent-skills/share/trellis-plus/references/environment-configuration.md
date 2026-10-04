# Environment Configuration

## Trigger And Placement

Apply when the project needs configurable development values, already uses
environment files, or a task adds/changes configuration. Reuse the established
framework, service-specific files, variable names, and precedence. Do not add
an unused `.env` mechanism to a project that does not need one.

Record the actual loader, file paths, required keys, safe defaults, override
order, and restart/rebuild requirements in the project-owned
`.trellis/spec/trellis-plus/development.md` or its existing equivalent. Link it
from the index and relevant task context. Keep one authoritative convention.

## Preview Configuration

When creating or adapting `preview.sh` for user visual acceptance, the root
`.env` must provide the primary preview configuration: account names/passwords,
variable Docker settings (such as image tags, mount paths, and service options
where applicable), service listening hosts/ports, and published host bindings
and ports. Document these keys in `.env.example`; do not hard-code their values
in `preview.sh`, `dev.sh`, or Compose files. Once initial configuration is
complete, `./preview.sh` must load it without requiring inline environment
assignments or edits to scripts.

Reuse the existing dotenv loader and variable names. If services use their own
configuration files, explicitly wire the root `.env` preview inputs into those
consumers and document precedence; do not leave competing, unsynchronized
values. Ensure Compose interpolation and container/application injection both
receive the settings they need. Keep secrets local and out of startup output.
Follow `dev-it-in-docker-bootstrap.md` for the required listener and URL summary.

## First Setup

1. Create or update `.env.example` with the keys consumed by the real execution
   path, safe dev defaults, and concise explanations. Use empty values or clear
   placeholders for user-supplied secrets; never copy real credentials into it.
2. If `.env` does not exist, show `cp .env.example .env` from the repository root
   and list exactly which keys the user must edit, what each means, and where
   its value comes from. Substitute the actual paths for framework-specific or
   multi-service files. If setup authorization includes creating the local
   file, copy it only after confirming it is absent and still report required
   edits. Never overwrite an existing local environment file.
3. Ensure local secret files are ignored while the example remains trackable.
   If a local file is already tracked, report it; do not assume an ignore rule
   removes it from history or automatically rewrite repository history.
4. Confirm how the app receives the values. Framework dotenv loading, Compose
   interpolation, and container environment injection are different mechanisms;
   use the project's actual route and avoid silently supplying a value only to
   the wrong layer. Do not source a dotenv file as shell code.
5. Missing required values must yield an actionable startup error or clearly
   block readiness. Do not report a usable preview until prerequisites hold.

## Incremental Changes

When a task adds configuration, update the example and its actual consumer
together. Compare **key presence**, not values, against the local file using
the project's dotenv syntax. Treat empty existing values as existing entries
to report, not permission to replace them.

- If the local file exists, append only missing keys with safe defaults or
  placeholders. Preserve comments, quoting, existing values, and line endings;
  ensure a separating newline. Use a format-aware edit or correctly quoted
  `printf` rather than repeated unconditional `echo >> .env` commands.
- Re-running the update must not append duplicate keys. Report duplicate keys
  already present when they make loading ambiguous; do not guess which value
  the user wants.
- If the local file is absent, keep the first-setup instruction; do not create
  a partial file containing only newly added keys.
- List the keys added and those needing user input, with their purpose and
  restart/rebuild action. Do not print secret values or a local-file diff.
- For a renamed or removed key, update known consumers and the example.
  Report the required local-file change; do not silently delete user values or
  keep an unsupported compatibility alias merely to avoid the change.

Example of a handoff shape; replace tokens with repository-confirmed names:

```text
Setup: cp .env.example .env (only when .env is absent)
Edit: REQUIRED-KEY — purpose and source of the value
Added locally: NEW-KEY — safe placeholder; user input still required
Apply changes: ACTUAL-RESTART-OR-REBUILD-COMMAND
```

## Verification

Confirm that examples contain no secrets, local files are excluded from the
commit, the real application reads the documented configuration, and preview
uses the same settings. For changed synchronization logic, test missing local
file, existing custom values, an existing empty value, a newly added key, and
a second identical run in a temporary fixture. Test behavior, not matching
prose; do not add a permanent synchronization tool unless repeated project
needs justify one.
