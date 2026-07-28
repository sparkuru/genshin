# GameShell5 local runtime

Reproduction tier: `authoritative-high-fidelity` (QEMU, bridge DHCP, VNC, and
host-to-guest reachability validated; guest services not assessed).

This lab is a VirtualBox OVA containing a full Debian 10 guest. Use the QEMU
runtime as the authoritative reproduction path; no Docker conversion is
provided.

## Start and stop

Prerequisites: `qemu-system-x86_64`, `qemu-img`, Docker, Python 3, and
passwordless `sudo` for the lab's bridge-bound DHCP process. Bootstrap the
QEMU helper once as root:

```sh
sudo ./runtime/qemu/setup-bridge-helper.sh
```

```sh
./runtime/qemu/run-qemu.sh
```

The guest uses DHCP on Docker's default `docker0` bridge. This host currently
uses subnet `10.160.0.0/20`: host bridge and guest router `10.160.0.1`, fixed
QEMU lease `10.160.0.10`, and DNS `1.1.1.1`. The host can scan the QEMU
address directly. VNC remains host-loopback-only at `127.0.0.1:5901` (display
`:1`); no guest service port is forwarded. Stop it with:

```sh
./runtime/qemu/stop-qemu.sh
```

Reset mutable guest state only after stopping it:

```sh
./runtime/qemu/reset-qemu.sh
```

## Isolation and fidelity

The launcher attaches QEMU to Docker's managed default bridge `docker0` through
a whitelisted bridge helper and runs a DHCP server bound only to that bridge.
The lease supplies the recorded Docker gateway as router and a DNS server, so
Docker's usual NAT routing may give the guest external access. Treat this as a
deliberate discovery/scanning topology, not an isolated runtime. The scripts
validate the recorded subnet, host address, and unused fixed QEMU address
before launch, and never create, modify, or remove Docker's default network.
This is not a Docker conversion of the target. The launcher creates no shared
folder, USB passthrough, clipboard integration, or guest port forward; VNC is
explicitly bound to loopback.

The original VM used VirtualBox SATA/AHCI storage, E1000 networking, 2 GiB
memory, one vCPU, and a BIOS-style configuration. The launcher carries those
material settings forward, but exact CPU identity, VirtualBox timing, USB,
audio, and display behavior are not identical. KVM is unavailable on the
current host, so the launcher falls back to TCG emulation.

The generated base disk passed `qemu-img check`. See [report.md](report.md)
for inventory, dependencies, and validation evidence.
