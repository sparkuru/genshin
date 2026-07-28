# ISO and boot media

Use this reference for installer, live, rescue, and challenge ISO images.

- Inspect the ISO volume metadata and boot records without modifying the image.
- Detect architecture and firmware expectation before choosing a QEMU machine type.
- Run ISO media in QEMU/KVM. Do not convert an installer or live environment to Docker unless the user supplies a separately reproducible application workload and the conversion cannot affect the challenge.
- Keep writable state in a separate derived disk or overlay. Preserve the ISO as read-only and record its hash.
- Apply local-only QEMU networking from `network-isolation.md` only if the media requires a network service; otherwise disable the NIC.
- Report whether the ISO is expected to install to disk, boot live, or attach to an existing disk image. Do not run an unattended installer without explicit user authorization.
