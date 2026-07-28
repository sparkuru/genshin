# Existing container artifacts

Use this reference for Dockerfiles, Compose files, OCI layouts, and Docker image archives.

## Inspect without broadening exposure

- Inventory manifests, image configuration, entrypoints, exposed ports, volumes, environment files, and Compose network settings.
- Do not import or start an untrusted image until the user has requested runtime preparation.
- Treat published `0.0.0.0` ports, `network_mode: host`, privileged containers, Docker socket mounts, and broad host mounts as unsafe defaults requiring replacement or explicit confirmation.

## Normalize faithfully

- Reuse the supplied image and manifest when it already reproduces the intended service. Treat it as `container-native`, not a conversion from a VM.
- Bind only necessary published ports to `127.0.0.1` and use the internal network recipe in `network-isolation.md`.
- Preserve a service's required command, working directory, user, and persistent data semantics. Do not silently add hardening that changes the challenge's permissions or filesystem behavior.
- Pin a base image by digest when feasible; otherwise record its resolved digest and the Compose implementation/version used for validation.
- Do not force a full VM into a container just because a service can be extracted. Use QEMU when the challenge depends on the guest OS, init system, kernel, device model, or boot path.

## Validate

- Start using the generated local Compose/project command.
- Test only the documented local entry point.
- Confirm all container ports are loopback-bound and no container has unintended external egress.
- Record the image digest/derived hash, reset procedure, and every intentional deviation from the supplied configuration.
