# mipsel32r2-linux-4.14.336-uclibc-ng

Generic Buildroot/QEMU environment for little-endian MIPS32 Release 2 binaries.
It uses uClibc-ng, QEMU Malta, a disposable ext4 rootfs, and restricted user
networking.

```sh
./build.sh
./validate.sh
./run-qemu.sh --share /path/to/programs
```

The host directory is mounted read-only at `/mnt/host`. Background mode exposes
guest telnetd only on `127.0.0.1:4549`:

```sh
./run-qemu.sh --background --share /path/to/programs
telnet 127.0.0.1 4549
./stop-qemu.sh
```
