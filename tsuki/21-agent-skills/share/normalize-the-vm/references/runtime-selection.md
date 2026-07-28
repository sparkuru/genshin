# Runtime selection and reproduction tiers

Read this reference for every input. Separate **artifact form** (what was supplied) from **runtime dependency** (what must be preserved). The former is often easy to identify; the latter determines whether Docker is safe to claim as a reproduction.

## Evidence collection

Record positive evidence and uncertainty. Inspect, without executing the target, the OVF/VM metadata, partition layout, boot configuration, init units, startup scripts, package manifests, service configuration, database files, container manifests, and source entrypoints. Use a read-only overlay or snapshot for any boot validation.

Classify every relevant dependency as `confirmed`, `absent`, or `unknown`:

| Dependency | Evidence that requires QEMU/KVM unless disproven as irrelevant |
| --- | --- |
| Boot and OS | ISO, firmware/bootloader requirement, init-system ordering, multiple OS services |
| Kernel and privilege | kernel module, kernel exploit, SUID/capability, namespace/cgroup, raw socket, iptables, device access |
| Hardware and topology | fixed disk/NIC model, MAC, interface name, DHCP, bridge/TAP topology, timing or hardware identity |
| Application state | unextractable runtime, missing package lock, undisclosed initial data, migration, queue, database, or dependency |

An `unknown` in a relevant category fails Docker eligibility. Do not equate an extracted web root with a complete service definition.

## Docker eligibility gate

Generate a Docker Compose convenience candidate only if all gates are confirmed:

1. Identify a complete application entrypoint, supported runtime, supplied dependencies, and initial state.
2. Reproduce every supplied service dependency, including a database or queue when it is part of the target.
3. Find no relevant boot, kernel, privilege, hardware, topology, filesystem, or timing dependency.
4. Preserve the target without privileged mode, host networking, Docker socket access, or broad writable host mounts.
5. Define a documented, non-exploit comparison contract for the service.

If the input includes a VM and any gate is unknown or false, use QEMU/KVM. If all gates pass, Docker remains a convenience runtime unless the source was already container-native.

## Validation scope

For a VM-derived Docker candidate, validate the QEMU/KVM runtime first and compare only documented normal behavior: service readiness, loopback listeners, documented request/response shape, supplied initial data, and reset behavior. Record exact requests or a compact script and the observed result in `report.md`.

Do not validate exploitation, flags, or vulnerability triggers by default. A passing contract supports `convenience-validated`, not vulnerability equivalence. Only an explicit user-authorized, bounded test plan may support an additional claim about a vulnerability.

## Writeup rule

Name the reproduction tier near the first start command. For `convenience-validated`, state that validation covers documented normal behavior only and link or include the QEMU/KVM authoritative command. For `authoritative-high-fidelity`, do not present a Docker recipe as an interchangeable substitute.
