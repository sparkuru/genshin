# Chrysos architecture

## Boundary

Chrysos is a small collection of independently runnable Linux/QEMU profiles.
Each profile builds, validates, starts, and stops its own guest. A selected host
directory may be mounted at `/mnt/host` read-only for manual testing. The
project does not identify binaries, schedule tests, or execute shared files
automatically.

## Profile registry

Every profile has a `profile.env` descriptor. The descriptor is the source of
truth for the target tuple and runtime identity:

- `PROFILE_KIND`: `buildroot` or `static-busybox`.
- `TARGET_ARCHITECTURE`, `TARGET_ENDIAN`, `PROFILE_ABI`, `PROFILE_FLOAT_ABI`, and
  `PROFILE_ELF_CLASS`: the executable compatibility contract. The `PROFILE_*`
  names intentionally avoid colliding with Buildroot's make variables.
- `TARGET_LIBC` and `USERSPACE_MODE`: the userland boundary.
- `QEMU_SYSTEM_BINARY`, `QEMU_BACKEND`, `QEMU_MACHINE`, and the kernel fields:
  the guest boot contract.
- `QEMU_PORT` and `ROOTFS_INSTALL_DIR`: host integration and generated-tool
  installation points.

`tools/check-profiles.sh` validates descriptors, lifecycle entries, rootfs
boundaries, and unique telnet ports. `templates/tools/check-shell.sh` also
invokes it and skips generated third-party sources under
`tools/gdbserver/src/`.

## Current matrix

| Profile | Userland | Kernel/QEMU | Reason to keep |
| --- | --- | --- | --- |
| ARMv7 | Static BusyBox/initramfs | Linux 3.10.108 / vexpress-a9 | Old kernel and static-userland cases |
| AArch64 | glibc | Linux 4.14.98 / virt | Older ARM64 baseline |
| AArch64 | glibc | Linux 6.18.7 / virt | Current ARM64 baseline |
| x86-64 | glibc | Linux 6.18.7 / pc | PC, server, NAS, and common VM cases |
| MIPS32r2 little-endian | uClibc-ng | Linux 4.14.336 / Malta | Little-endian embedded samples |
| MIPS32r2 big-endian | uClibc-ng | Linux 4.14.336 / Malta | Big-endian embedded samples |
| RISC-V 64 | glibc, lp64d | Linux 6.18.7 / virt | Modern RISC-V samples |

This is a representative set, not a Cartesian product of architectures,
kernels, ABIs, and C libraries. New profiles should be sample-driven.

## Reusable debugger sidecar

`tools/gdbserver/build.sh` discovers profiles from `profile.env`, builds a
static GNU GDB `gdbserver` with each profile's cross compiler, writes a manifest,
and installs the result into the descriptor's `ROOTFS_INSTALL_DIR`. The
Buildroot profiles package the sidecar during `build.sh`; ARMv7 packages it
into the static initramfs. The sidecar must have no ELF interpreter so it can be
used without changing the target's dynamic loader or libc contract.

## Addition policy

Prefer the nearest existing Buildroot profile for lifecycle structure, then
change the target descriptor, Buildroot architecture option, kernel config,
QEMU device model, and identity overlay together. Keep architecture-specific
logic in the profile. Do not add armv5, i686, musl, or additional kernel
versions without a real sample or compatibility requirement.
