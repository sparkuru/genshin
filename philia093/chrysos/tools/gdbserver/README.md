# Static gdbserver sidecars

This directory creates one static `gdbserver` for every Chrysos target
profile. Each profile build installs its matching sidecar in `/usr/bin/gdbserver`
before it packages the root filesystem.

`src/` contains the downloaded GNU GDB source archive and its extraction.
`builds/` contains all generated binaries, intermediate objects, and an
artifact manifest. Both are ignored by Git. The tracked [`build.sh`](build.sh)
is the complete provenance and build entry point.

## Build

Build one or more architecture groups:

```sh
./tools/gdbserver/build.sh --arch armv7l,aarch64,x86_64,mipsel32r2
```

`aarch64` deliberately builds two artifacts: one for the Linux 4.14.98
profile and one for Linux 6.18.7. Use `--arch all` for every profile. Set
`JOBS=N` to control compilation parallelism.

Each selected profile must already have been built with its normal
`./build.sh`, because this script consumes that profile's fixed cross toolchain.
GDB 14.2 needs a C++ target toolchain; the Buildroot AArch64 profiles therefore
enable that toolchain component as part of this repository's debug baseline.

To install a prebuilt sidecar into its profile's rootfs source without building
other architectures, use its exact profile name:

```sh
./tools/gdbserver/build.sh --profile x86_64-linux-6.18.7-glibc --install-rootfs
```

The installed binary is ignored by Git. Run the profile's `./build.sh` to
package it into the published rootfs image.

## Trust and verification

The script downloads `gdb-14.2.tar.xz` from GNU's HTTPS mirror and verifies its
SHA-512 before extraction. The pinned digest is the one published in
Buildroot's GDB package hash file for the same GNU release.

For every output, `build.sh` refuses a dynamically linked executable and
checks that ELF program headers contain no `INTERP` segment. It emits:

```text
builds/<profile>/gdb-14.2/
├── gdbserver
└── manifest.yml
```

The manifest records the source URL and digest, target tuple, binary SHA-256,
and the static-ELF check. A static binary still has to match the target profile:
do not substitute an ARM, AArch64, x86-64, or MIPSel artifact for another.
For glibc targets, static linking removes the ELF interpreter but does not make
every optional libc feature self-contained: `gdbserver` can use facilities such
as NSS or thread debugging that load matching libc modules. Validate on the
intended profile before relying on those paths.

## Use in a guest

`gdbserver` is available at `/usr/bin/gdbserver`. Bind it to loopback unless
remote network access is deliberately required:

```sh
/usr/bin/gdbserver --once 127.0.0.1:2345 /mnt/host/program
```

The current QEMU launchers only forward their login port. Add an explicit local
QEMU port forward before connecting a host cross-GDB to guest port 2345; do not
expose `gdbserver` on a LAN by default.
