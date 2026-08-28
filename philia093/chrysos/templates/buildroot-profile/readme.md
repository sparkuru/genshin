# @PROFILE_NAME@

Reusable generic Buildroot/QEMU profile for Linux @LINUX_VERSION@ on AArch64.
Its pinned inputs and profile-specific settings are stored in `profile.env`.

## Quick start

```sh
./build.sh
./validate.sh
./run-qemu.sh --share /path/to/programs
```

For a background guest, use:

```sh
./run-qemu.sh --background --share /path/to/programs
telnet 127.0.0.1 @QEMU_PORT@
./stop-qemu.sh
```

The guest uses QEMU's generic `virt` machine, a Cortex-A53-compatible AArch64
CPU, a 128 MiB ext4 disk image, and restricted user-mode networking. The
filesystem runs from a disposable copy of the image. `--share` mounts one
existing host directory read-only at `/mnt/host`.

Generated sources, downloads, Buildroot output, and runtime logs are ignored
by Git. Extend the guest through `board/rootfs-overlay/`. Each generated
profile contains its own `common.sh` and has no runtime dependency on
`templates/` or the repository root.
