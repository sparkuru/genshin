# armv7l-linux-3.10.108

Reusable QEMU base for Linux 3.10.108 on ARMv7 (`armv7l`). The directory
contains the rootfs template, build scripts, and runtime metadata. The large
source archives, extracted trees, build cache, and QEMU artifacts are local
generated inputs and are intentionally excluded by `.gitignore`.

## Quick start

For a checkout that already has local `out/` artifacts, the environment can
start without a rebuild:

```sh
./run-qemu.sh --background --share /path/to/programs
telnet 127.0.0.1 4545
./stop-qemu.sh
```

For a fresh checkout, build the ignored sources and artifacts first:

```sh
./build.sh
./validate.sh
```

Then use the quick-start commands above.

For a directly attached serial console, run `./run-qemu.sh` instead. The
guest starts a normal BusyBox `telnetd`; each connection gets its own
pseudo-terminal and an unprivileged `user` shell. The disposable guest also
has `su - root` for root-required lab setup.

No host root is required. QEMU uses restricted user-mode networking and
forwards only `127.0.0.1:4545` on the host to TCP port 23 in the guest. With
`--share`, one existing host directory is mounted read-only at `/mnt/host`;
the guest never executes its contents automatically. There is no LAN bridge,
host networking, USB passthrough, or clipboard integration. Background serial
output is written to `out/run/qemu-serial.log`.

## Reuse as a base

Use `--share` for programs that change frequently. Add guest support files
under `rootfs-template/` only when they must be embedded, then run `./build.sh`.
The template is rebuilt into an initramfs embedded in `out/zImage`; every boot
starts from a fresh ephemeral filesystem.

The main project components are:

```text
build.sh                  Build kernel, BusyBox, initramfs, and reports
run-qemu.sh               Foreground or background QEMU launcher
stop-qemu.sh              Background QEMU lifecycle stop command
validate.sh               Non-exploit boot and identity smoke test
rootfs-template/          Guest filesystem and init scripts
downloads/                Local checksummed source archives (ignored)
build/                    Local extracted sources and build cache (ignored)
out/                      Local artifacts, reports, and logs (ignored)
```

See `out/README.md` and `out/report.md` for the generated runtime details and
fidelity limitations.
