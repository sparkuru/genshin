# riscv64-linux-6.18.7-glibc

Generic Buildroot/QEMU environment for little-endian RISC-V 64-bit binaries.
It uses glibc, the lp64d ABI, QEMU's virt machine, a disposable ext4 rootfs,
and restricted user networking.

```sh
./build.sh
./validate.sh
./run-qemu.sh --share /path/to/programs
```

For a background guest, use:

```sh
./run-qemu.sh --background --share /path/to/programs
telnet 127.0.0.1 4550
./stop-qemu.sh
```

The host directory is mounted read-only at `/mnt/host`. Buildroot and the
kernel inputs are checksum-pinned in `profile.env`.
