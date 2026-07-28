---
name: normalize-the-vm
description: Inspect, classify, and safely normalize local lab-machine artifacts such as HackMyVM/CTF downloads, VM exports, disk images, ISOs, container bundles, and service archives. Generate an authoritative QEMU/KVM runtime when a full guest matters, and a conditional Docker Compose convenience runtime only when evidence supports it. Use when given a local artifact and asked to identify, run, convert, compare, document, or package it for reproducible host-local use.
---

# Normalize Lab Machine

Turn an untrusted lab artifact into a reproducible local runtime. Separate artifact format from runtime dependency, preserve an authoritative runtime whenever a full guest matters, and treat Docker conversion as a claim that needs evidence.

## Safety contract

- Treat every input as an intentionally vulnerable, untrusted artifact.
- Inspect the original read-only. Record an SHA-256 before extraction or conversion. Never overwrite, delete, execute, or mount the source read-write.
- Keep all derived files in a new named output directory. Do not modify the user's current project unless they explicitly request it.
- Default to no external connectivity, no LAN bridge, no Docker host networking, no shared folders, no USB passthrough, no clipboard integration, and no privileged container. When the host needs a directly scannable QEMU guest address, prefer Docker's managed default `docker0` bridge and record its resolved subnet, host/gateway address, and fixed QEMU address in both launcher output and documentation. `docker0` normally has Docker NAT and may give the guest external egress, so require explicit user authorization before launching it and label the runtime non-isolated.
- Interpret “only the host can access it” as host-local exposure. Bind consoles and explicit forwarded ports to `127.0.0.1`; this is **not** Docker `--network host`. A guest address on a dedicated internal bridge is host-local when the bridge has no LAN uplink, no published ports, and no DHCP router or DNS option.
- Do not exploit the target, retrieve flags, alter guest data, or scan beyond its intended local endpoints unless explicitly asked.

## Workflow

### 1. Inventory and classify

1. Resolve the input path and create a read-only inventory: file type, size, SHA-256, archive listing, nested artifact types, and relevant metadata.
2. Never extract directly into the input directory. Extract only into a fresh staging directory when inspection requires it.
3. Identify the **artifact form** from evidence, then load exactly the needed reference:

| Evidence | Read |
| --- | --- |
| `.ova`, `.ovf`, `.vmdk`, `.vdi`, `.vhd`, `.vhdx` | [virtual-machines.md](references/virtual-machines.md) |
| `.qcow2`, raw disk, cloud image | [virtual-machines.md](references/virtual-machines.md) |
| `.iso`, bootable/live/install media | [boot-media.md](references/boot-media.md) |
| `Dockerfile`, Compose, OCI/Docker archive | [containers.md](references/containers.md) |
| Source archive, web root, service config | [service-bundles.md](references/service-bundles.md) |
| Every runtime that exposes a service | [network-isolation.md](references/network-isolation.md) |

4. For every artifact, read [runtime-selection.md](references/runtime-selection.md). Build a **runtime-dependency profile** with each item marked `confirmed`, `absent`, or `unknown`, backed by a path or command output:
   - boot, firmware, init system, and kernel dependencies;
   - privilege, capability, namespace, cgroup, device, and filesystem dependencies;
   - hardware, disk-controller, NIC, MAC, interface-name, and timing dependencies;
   - application entrypoint, runtime, data store, migrations, and supplied dependencies.

Do not infer that a dependency is absent merely because it was not found. A VM disk or ISO establishes the input format, not Docker eligibility. Report artifact-form evidence, detected OS/architecture, boot/firmware requirements, disk controller, NIC model, discovered entrypoint, and the dependency profile.

### 2. Select the runtime

Apply the decision gate in [runtime-selection.md](references/runtime-selection.md). Use these rules:

1. Reuse an existing OCI/Docker workload when it is the supplied target; call it `container-native`, not a conversion.
2. Build a Docker Compose **convenience candidate** only when every Docker eligibility gate is confirmed. Pin or record every resolvable image digest and preserve supplied commands, users, data, and initialization semantics.
3. Use QEMU/KVM as the authoritative high-fidelity runtime for full OS appliances, disk images, ISOs, boot-chain or kernel-level tasks, and every case with a relevant `unknown` or confirmed VM dependency.
4. When a VM has a Docker-eligible service bundle, retain the QEMU/KVM runtime as authoritative and make Docker an additional convenience runtime. Do not replace the VM artifact.
5. Preserve the original format and return `blocked` when neither runtime can be prepared safely.

Reject Docker explicitly when it would make a VM-only challenge merely appear runnable. Do not call a Docker candidate equivalent to a VM source without an authorized equivalence test. Do not require KVM acceleration: detect it, use it when available, and provide an emulation fallback.

### 3. Materialize the runtime

Create a new output directory containing:

- `README.md` — artifact form, dependency profile, reproduction tier, prerequisites, start/stop commands, host-local entry points, reset procedure, and limitations.
- `run.sh` and `stop.sh` — idempotent, non-interactive lifecycle commands. In a dual-runtime result, expose unambiguous `run-qemu.sh`, `stop-qemu.sh`, `run-compose.sh`, and `stop-compose.sh` wrappers instead.
- Runtime configuration: Compose/Dockerfile, QEMU launch configuration, or both. A QEMU `docker0` bridge runtime must validate rather than create or delete Docker's default network; include a narrow QEMU bridge-helper allowlist, DHCP service, mutable PID/log/socket state, and explicit subnet/host/QEMU address constants.
- Derived images only where necessary; preserve original input unchanged.
- `report.md` — source and derived hashes, dependency-profile evidence, runtime decision, image digests or base-image references, chosen virtual hardware, isolation policy, listeners, comparison scope, and validation results.

Use `qemu-img info` and `qemu-img check` where applicable before and after conversion. Prefer a derived `qcow2` image for QEMU when conversion is needed. Initially preserve the source disk-controller and NIC model; optimize only after a successful boot.

### 4. Validate and state the reproduction tier

1. Start the authoritative runtime through its generated launcher. For a VM-derived target, use a writable overlay or other derived state; keep the original disk read-only.
2. Confirm the guest boots or the intended service becomes ready. Test only documented endpoints through `127.0.0.1` or the recorded assigned guest address.
3. When a Compose candidate exists, start it independently and compare a written, non-exploit contract: required listeners, documented normal requests, expected status/response shape, supplied initial data, and any declared reset behavior.
4. Confirm consoles and explicit forwards are loopback-only. For the default `docker0` topology, confirm Docker's current subnet, host/gateway, exact bridge-helper allowlist, fixed DHCP lease, router/DNS options, and that the documented QEMU address is unused by Docker endpoints. Record that Docker NAT may provide external egress. Confirm there is no host network mode, privileged container, or unintended mount.
5. Stop cleanly and retain the report. Never retrieve flags, trigger a vulnerability, or claim vulnerability equivalence unless the user explicitly authorizes a bounded test plan.

Record one reproduction tier in `README.md` and `report.md`:

- `authoritative-high-fidelity` — QEMU/KVM preserves the supplied guest and is the recommended reproduction path.
- `container-native` — the supplied target was already an OCI/Compose workload.
- `convenience-validated` — Docker matched the documented, non-exploit comparison contract; this does not prove vulnerability equivalence.
- `convenience-candidate` — Docker starts, but comparison is incomplete or failed; retain the authoritative runtime.
- `blocked` — name the concrete missing artifact, unsupported feature, or prerequisite and the smallest next action.

Use one final normalization status:

- `normalized` — generated and validated a Docker or QEMU/KVM runtime.
- `runnable-with-exceptions` — generated a safe runnable setup but deliberately avoided a requested conversion; explain why.
- `blocked` — name the concrete missing artifact, unsupported feature, or prerequisite and the smallest next action.

## Final response

State the artifact form, dependency-profile result, reproduction tier, selection rationale, output directory, exact start command, loopback endpoint, isolation policy, validation evidence, and fidelity limitations. For a writeup, lead with the recommended reproduction path and include the authoritative path whenever it differs. Never imply that a Dockerized target is equivalent to its VM source without evidence.
