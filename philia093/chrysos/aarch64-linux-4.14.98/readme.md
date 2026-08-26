# aarch64-linux-4.14.98

Reusable Buildroot/QEMU base for Linux 4.14.98 on AArch64. This profile keeps
the older kernel and matching 4.14 kernel headers for compatibility work. It
is not a vendor firmware reproduction.

Buildroot 2024.05.3 is used because newer Buildroot releases no longer expose
4.14 as a supported target kernel-header series.

## Quick start

```sh
./build.sh
./validate.sh
./run-qemu.sh
```

For a background guest, use:

```sh
./run-qemu.sh --background
telnet 127.0.0.1 4546
./stop-qemu.sh
```

The guest uses QEMU's generic `virt` machine, a Cortex-A53-compatible AArch64
CPU, a 128 MiB ext4 disk image, and restricted user-mode networking. The
filesystem runs from a disposable copy of the image; no host directory is
shared.

Generated sources, downloads, Buildroot output, and runtime logs are ignored
by Git. Buildroot's downloaded archives are checksum-verified by the local
checksum records created in `downloads/`.
