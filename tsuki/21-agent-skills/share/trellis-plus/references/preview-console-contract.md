# Mandatory Preview Console Contract

## Scope

Read this reference before creating, adapting, or checking a project's `preview.sh` or its underlying summary renderer. Every Trellis Plus preview must use this output contract, regardless of framework, service names, Docker wrapper, or Compose topology. Project-specific startup and readiness procedures remain in the existing lifecycle; they do not authorize a different console format. Record this contract and its address-discovery procedure in the project-owned development spec so future tasks can enforce it without this skill installed.

[assets/refer-preview.sh](../assets/refer-preview.sh) implements the shared color, log/help, and summary presentation described here. Read the integration procedure in [dev-it-in-docker-bootstrap.md](dev-it-in-docker-bootstrap.md) before copying or sourcing it. The text contract remains authoritative for runtime facts, host discovery, readiness, and redaction; the reference renderer does not perform those checks itself.

The purpose is to let the user click or copy a complete URL to open a testing window, including from a different device. Put access URLs before listener and runtime diagnostics. Never advertise `0.0.0.0`, `::`, a container IP, or a Compose service name as a host-accessible browser destination.

## Required Output Template

Use the following `输出参考` code block as the mandatory output template. On successful `start`, including an already-running healthy preview, print one summary with these exact section labels and ordering. Omit empty sections. Within `Open` and `Local only`, use `<entry label> (<service>):` followed by one complete URL per line, without bullets, inline annotations, or trailing punctuation. Keep service/entry ordering stable and deduplicate URLs within each entry. `Website`, `Admin`, `API`, and `API docs` are standard entry labels when those routes exist; additional entries use their actual user-facing name.

```输出参考
System is ready.

Open:
Website (web):
http://192.0.2.10:7081
http://198.51.100.20:7081
Admin (web):
http://192.0.2.10:7081/admin
http://198.51.100.20:7081/admin
API docs (web):
http://192.0.2.10:7081/api/docs
http://198.51.100.20:7081/api/docs

Local only (preview host):
Website (web):
http://127.0.0.1:7081
Admin (web):
http://127.0.0.1:7081/admin
API docs (web):
http://127.0.0.1:7081/api/docs

Listeners:
Listening db: 0.0.0.0:5432 (container only; PostgreSQL/TCP)
Listening api: 0.0.0.0:8000 (container only; HTTP)
Listening web control: 127.0.0.1:2019 (container loopback only; admin API)
Listening web: 0.0.0.0:80 (container; HTTP)

Published:
Published web: 0.0.0.0:7081 -> 0.0.0.0:80 (active listener)
Published web: 0.0.0.0:7082 -> container port 443 (no active listener)

Internal only:
API docs (api): http://api:8000/api/docs (Compose network only)
Internal probe: <actual project command that probes the internal API>

Notes:
Host addresses enumerated with ip -br a; access from other devices is unverified.
```

The example IPs are documentation addresses; substitute discovered runtime values. Service topology, entries, routes, protocols, and ports vary; section labels, entry syntax, ordering, and one-URL-per-line layout are mandatory.

- Use effective runtime schemes, host ports (including dynamically assigned ports), and routes. Reverse-proxy entries use the proxy service and published port. Include only real interfaces; do not invent `/admin` or `/api/docs`.
- `Listeners` covers all preview services' active listeners, including internal-only, non-browser, and container-loopback control endpoints. State scope and protocol. For a host-native service, use `host` as its scope.
- `Published` covers actual Docker host mappings. A mapping alone is not proof of a listener. Mark inactive or unverified mappings explicitly and omit their browser URLs. Do not present an uninspected listener as active or absent.
- `Internal only` holds container-network destinations and the actual existing access/probe command, with the right env file, project directory, Compose file, and service. Do not publish an internal service to populate `Open`.
- `Notes` holds applicable TLS/self-signed-certificate instructions, address discovery limitations, and cross-device verification results. Never print credentials, tokens, authenticated URLs, or raw environment contents.
- Capture routine wrapper command echoes, container IDs, framework banners, and Compose progress during startup; show them through an explicit verbose mode or on failure, redacting secrets. Successful default startup must use the summary above rather than a project-specific mixture of startup logs and access lines.

## Host Address Discovery

For Docker previews, resolve the effective endpoint before choosing the address discovery host. Explicit `DOCKER_CONTEXT` takes precedence over `DOCKER_HOST`; with only `DOCKER_HOST`, inspect that endpoint; with neither, inspect the current context. Use supported CLI operations and distinguish unsupported subcommands from invalid configuration. For example, `docker context inspect` without a name can inspect the current context on CLIs that lack `docker context show`; use `docker context inspect <context>` for an explicit context. Validate the chosen commands against the supported CLI capabilities rather than assuming a version or requiring environment overrides to hide a script defect. A local Unix socket endpoint is the supported local discovery case; unsupported or remote endpoints require an authorized discovery route or explicit host-address configuration, never guessed caller addresses.

For wildcard host publishing, run `ip -br a` on the **host publishing the preview**, on every `start` summary and every ready `status` summary. This is required when the effective host bind is `0.0.0.0`; a container wildcard bind alone does not establish host exposure. For a remote Docker daemon, discover on that daemon host through an existing authorized route. Never substitute addresses from the caller's machine or a container network namespace. If that host cannot be inspected, report the limitation and request explicit host-address configuration.

1. Parse each interface row as interface name, state, and **all** remaining address fields. Accept interfaces in `UP` or `UNKNOWN` state that have addresses; skip `DOWN` interfaces. Strip CIDR prefixes, validate address fields, and deduplicate addresses while preserving discovery order.
2. For an IPv4 host bind of `0.0.0.0`, enumerate every assigned non-loopback, non-unspecified IPv4 address from those rows. Do not select only the first interface, first address, default-route address, or a configured LAN hint. Include secondary addresses and bridge/VPN/tunnel addresses as candidates; discovery does not prove that another device can reach them. Do not label every candidate as a verified LAN address.
3. For each browser entry with an active host-accessible listener, generate `<scheme>://<discovered-host-address>:<effective-host-port><actual-path>` for **every** eligible address. Repeat the whole address list for each entry, grouped by service as in `Open`. A configured host/domain may add a valid candidate but must not replace wildcard-bind enumeration.
4. For a specific non-loopback host bind, advertise only that bound address and applicable configured names. For a loopback host bind, emit `Local only` and no remote candidates. Do not convert a container-only or loopback-only endpoint into host-interface URLs. Put reachable host loopback URLs in `Local only (preview host)`, never in `Open`.
5. IPv4 wildcard publishing does not establish IPv6 publishing. Enumerate non-loopback IPv6 addresses only for an effective IPv6 host mapping/bind; bracket IPv6 literals in URLs. Exclude link-local IPv6 addresses requiring a client-specific zone identifier and explain the omission in `Notes` when relevant. Do not assume `[::]` also accepts IPv4 without runtime evidence.
6. Check for `ip` before startup when wildcard address discovery is required. If missing or enumeration fails, return an actionable dependency/discovery error; never silently fall back to only `127.0.0.1` or a guessed IP. If enumeration succeeds but finds no eligible addresses, omit `Open` and state `No non-loopback host address found.` in `Notes`; retain valid local/internal access. Preserve host network configuration.

## Readiness And Verification

Print `System is ready.` only after **every required preview service** passes its bounded readiness check. Container running state or a published port is insufficient. A failed check must return nonzero, name the failing service, and show actionable diagnostics, with no success banner or ready access list. Transient failed polls may be logged in verbose mode; a terminal failure must not be followed by a success summary. A ready `status` uses the same renderer; an unready `status` reports actual service state without the success banner.

On terminal startup failure, collect diagnostics **before** removing containers created by that attempt. Validate ownership against the repository identity, preview scope, and service labels used by the existing lifecycle; do not read unrelated containers. Fetch only a bounded recent log tail with a timeout (for example, 80 lines and 5 seconds). Redact sensitive injected environment values, configured private account identifiers, authenticated URLs, and bearer tokens before emitting logs in failure or verbose output. Do not dump `.env` or raw container inspection data. Log-read/redaction failures must not emit raw logs, prevent cleanup, or replace the original startup exit code. Remove only resources created by this attempt and preserve user data. If the error points to incompatible persistent data, name the configured data path and supported migration/recovery action without automatically resetting it. Watch processes can remain running after an import or application error; readiness timeout must still reveal that error through the same diagnostics path.

When changing a project's renderer, validate behavior with temporary address and runtime fixtures before the normal lifecycle smoke check:

- Two host interfaces and multiple addresses on one row: every eligible IPv4 URL appears for every entry, with the published host port rather than the container port; duplicates and CIDR suffixes never appear.
- `UP`, `UNKNOWN`, `DOWN`, loopback, bridge, and tunnel rows: eligible candidates are complete, local URLs are separated, and reachability is not overstated.
- IPv4 wildcard, specific-host, loopback-only, container-only, and IPv6 mappings: destinations respect actual exposure; no wildcard browser URL is printed.
- Missing/failing `ip`, no non-loopback addresses, HTTPS, and an inactive published port: errors/notes are accurate and unusable entries are omitted.
- One required service never becomes ready: nonzero exit, named diagnostics, no success banner. Repeated healthy starts and ready `status` keep the same summary layout without leaking startup logs or secrets.
- Effective Docker target: explicit context wins over host, host-only uses its endpoint, and no overrides use the current context. A CLI without `context show` still resolves the current context through supported `inspect`. Unsupported required operations and unsupported remote endpoints produce distinct actionable errors; caller addresses never stand in for remote-host discovery.
- Failure diagnostics: an application/watch error remains visible before cleanup; injected test secrets, private account identifiers, authenticated URLs, and bearer tokens are masked. Log-read timeout/failure and ownership mismatch still preserve the original failure and cleanup without raw output.

Fixture checks do not prove physical-device reachability. Report host probes and cross-device tests separately, and retain the unverified note until the intended device/network access has actually been checked.
