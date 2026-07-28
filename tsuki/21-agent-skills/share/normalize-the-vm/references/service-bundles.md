# Service and source bundles

Use this reference for web roots, source archives, application bundles, and unknown archives that contain an identifiable service rather than a bootable operating system.

## Determine whether Docker is faithful

Docker is appropriate only when the intended service can be reproduced without relying on a guest kernel, boot sequence, hardware identity, init system, or VM-specific network/filesystem behavior. Read deployment manifests, package metadata, startup scripts, and service configuration before deciding.

If a source archive also includes a VM image, treat the VM as the authoritative target unless evidence shows the source bundle is the intended standalone challenge.

## Build conservatively

- Use a minimal non-privileged base image compatible with the supplied runtime requirements.
- Copy the artifact into a new build context; do not modify source files in place.
- Do not invent secrets, credentials, data fixtures, or network dependencies.
- Bind service ports to loopback and use an internal Docker network as described in `network-isolation.md`.
- Treat database or queue dependencies as part of the target only when supplied or explicitly requested; do not download internet dependencies without authorization.

## Report fidelity

State the evidence that the container reproduces the intended workload and list any behavior that could differ from its original environment. If evidence is insufficient, return `blocked` or use the supplied VM/bootable artifact instead.
