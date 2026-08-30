# ppc64-linux-6.18.7-glibc

Generic Buildroot/QEMU environment for big-endian 64-bit PowerPC Linux
binaries. It uses glibc, a POWER7 CPU on QEMU's `pseries` machine, a disposable
ext4 rootfs, and restricted user networking.

```sh
./build.sh
./validate.sh
./run-qemu.sh --share /path/to/programs
```

The host directory is mounted read-only at `/mnt/host`. Background mode exposes
guest telnetd only on `127.0.0.1:4556`:

```sh
./run-qemu.sh --background --share /path/to/programs
telnet 127.0.0.1 4556
./stop-qemu.sh
```
