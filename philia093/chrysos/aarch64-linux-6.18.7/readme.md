# aarch64-linux-6.18.7

Reusable generic Buildroot/QEMU base for Linux 6.18.7 on AArch64. This is the
modern companion to the older ARMv7 profile and is intended for general
userspace, kernel, and cross-compilation experiments.

Buildroot 2026.05.2 is pinned as the stable Buildroot release used by this
profile. The kernel and Buildroot versions are independent inputs and are both
recorded in `out/` after a build.

## Quick start

```sh
./build.sh
./validate.sh
./run-qemu.sh
```

For a background guest, use:

```sh
./run-qemu.sh --background
telnet 127.0.0.1 4547
./stop-qemu.sh
```

The guest uses QEMU's generic `virt` machine, a Cortex-A53-compatible AArch64
CPU, a 128 MiB ext4 disk image, and restricted user-mode networking. The
filesystem runs from a disposable copy of the image; no host directory is
shared.

Generated sources, downloads, Buildroot output, and runtime logs are ignored
by Git. Buildroot's downloaded archives are checksum-verified by the local
checksum records created in `downloads/`.
