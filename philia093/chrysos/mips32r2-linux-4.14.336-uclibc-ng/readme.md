# mips32r2-linux-4.14.336-uclibc-ng

Generic Buildroot/QEMU environment for big-endian MIPS32 Release 2 binaries.
It uses uClibc-ng, QEMU Malta, a disposable ext4 rootfs, and restricted user
networking.

```sh
./build.sh
./validate.sh
./run-qemu.sh --share /path/to/programs
```

For a background guest, use:

```sh
./run-qemu.sh --background --share /path/to/programs
telnet 127.0.0.1 4551
./stop-qemu.sh
```

The host directory is mounted read-only at `/mnt/host`. The profile uses
the o32 soft-float ABI and keeps its rootfs source separate from the little-endian
MIPS profile.
