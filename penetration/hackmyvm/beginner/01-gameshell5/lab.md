# GameShell5 Lab

## Identity

- Difficulty: beginner
- Source: <https://hackmyvm.eu/machines/machine.php?vm=Gameshell5>
- Artifact form: ZIP containing a VirtualBox OVA with a stream-optimized VMDK
- Artifact hashes: ZIP `a5a5c8b20f4a6bee3b02bfbfd60b5daaf38f1c00ee33ca36b001d17a18c86362`; OVA member `3a0cb08b90634d879d37dd92393d3efe05177050ed751c522208e8de243eb6e9`

## Reproduction status

- Runtime dependency profile: full Debian 10/systemd guest; SATA/AHCI, E1000, and guest state are relevant; see [report.md](report.md).
- Reproduction tier: `authoritative-high-fidelity` (QEMU, bridge DHCP, VNC, and host reachability validated; guest services not assessed)
- Normalization status: `normalized`; QEMU ran, VNC completed an RFB `003.008` handshake, and the host reached the assigned guest address with ICMP.
- Start: `./runtime/qemu/run-qemu.sh`; reset: `./runtime/qemu/reset-qemu.sh`
- Host-local endpoints: QEMU `10.160.0.10` on Docker `docker0` (`10.160.0.0/20`; host/router `10.160.0.1`); VNC `127.0.0.1:5901`; no guest service port is forwarded.
- Generated runtime: `runtime/qemu/` launch, stop, reset, bridge-helper setup, and DHCP wrappers; immutable base under ignored `runtime/images/`; mutable state under ignored `runtime/state/`.

Docker was not created: this is a VM-derived, multi-service target with confirmed OS and virtual-hardware dependencies and unresolved kernel/application-state dependencies. Keep `writeup.md` user-owned.

Docker `docker0` is a deliberate discovery/scanning topology. Its DHCP lease
also supplies Docker's gateway and DNS, so default Docker NAT may provide
external guest egress; it is not an isolated network.
