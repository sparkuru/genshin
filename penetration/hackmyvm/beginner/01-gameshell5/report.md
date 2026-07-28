# GameShell5 normalization report

## Result

- Normalization status: `normalized`
- Reproduction tier: `authoritative-high-fidelity` (QEMU, bridge DHCP, VNC, and host reachability validated; guest services not assessed)
- Recommended runtime: `./runtime/qemu/run-qemu.sh`
- Host-local endpoints: QEMU `10.160.0.10` on Docker `docker0` (`10.160.0.0/20`, host/router `10.160.0.1`); VNC `127.0.0.1:5901`; no guest ports are forwarded

With explicit authorization, the launcher started the target successfully. The
QEMU process remained alive after the guest DHCP exchange and its VNC endpoint
completed a minimal RFB `003.008` handshake on loopback. The bridge DHCP server
logged a DHCP Request/ACK exchange for the source E1000 MAC and the host reached
`10.160.0.10` with one ICMP echo. No guest service was contacted.

## Artifact inventory

| Artifact | SHA-256 | Notes |
| --- | --- | --- |
| `archive/gameshell5.zip` | `a5a5c8b20f4a6bee3b02bfbfd60b5daaf38f1c00ee33ca36b001d17a18c86362` | Original, unchanged ZIP |
| OVA member `GameShell5.ova` | `3a0cb08b90634d879d37dd92393d3efe05177050ed751c522208e8de243eb6e9` | Original VirtualBox export, inspected from ZIP |
| VMDK member `GameShell5-disk001.vmdk` | `118de1b1612b86a73f4985a236db416bb4f14faa04e9fca1f417ce7e3ffc64ac` | Stream-optimized, 30 GiB virtual capacity |
| Derived `runtime/images/gameshell5-base.qcow2` | `1b9653bad753f3dcec47c144ededa75c56ea87d018cd5617872f19bd5086b5ed` | 3,203,530,752 bytes allocated; `qemu-img check` passed |

The OVA manifest's SHA-1 entries matched its OVF and VMDK members. The source
VMDK and derived QCOW2 both passed `qemu-img check` with no errors.

## Dependency profile

| Category | Status | Evidence and consequence |
| --- | --- | --- |
| Boot, OS, init system | confirmed | Debian 10 x86_64, an ext4 root filesystem, swap, and systemd were identified read-only. A full guest must boot. |
| Firmware | unknown | The OVF describes VirtualBox's default BIOS state and declares no UEFI; QEMU uses BIOS-compatible defaults. |
| Kernel, privilege, cgroups, devices | unknown | No exhaustive kernel or privilege audit was performed. This independently fails Docker eligibility. |
| Storage and hardware | confirmed | OVF specifies SATA/AHCI, 2 GiB RAM, one vCPU, and E1000; the guest uses `enp0s3` and the source MAC. |
| Application entrypoints and state | confirmed/unknown | Systemd service definitions identify InspIRCd, SSH, and a Python IRC bot at `/usr/local/bin/irc_bot.py`; complete package/dependency and initial-data equivalence outside the guest remain unknown. |

Docker was rejected. The supplied artifact is VM-derived; confirmed boot and
hardware dependencies plus unresolved kernel and application-state dependencies
fail the Docker eligibility gate. No Compose candidate was created.

## Runtime and isolation

The launcher keeps the derived QCOW2 immutable in practice by creating a
writable QCOW2 overlay at `runtime/state/gameshell5-overlay.qcow2`. It uses
Q35 with an AHCI-attached disk, source E1000 MAC at the guest's expected PCI
slot `00:03.0`, 2 GiB RAM, one vCPU, VMware-SVGA-compatible display, UTC RTC,
and Docker's default bridge for host-side discovery.

Docker's managed `docker0` bridge uses `10.160.0.0/20`; its host address and
guest router are `10.160.0.1`, and QEMU receives fixed address `10.160.0.10`.
QEMU attaches through a helper that allows only `docker0`. A root-owned DHCP
process is bound with `SO_BINDTODEVICE` to that bridge and supplies the Docker
gateway plus DNS `1.1.1.1`. Docker's default NAT therefore may permit guest
egress; this runtime is not isolated from external networks. The launcher does
not create, alter, or remove Docker's default bridge, nor does it add a LAN
bridge, shared folder, USB passthrough, clipboard, host networking, privileged
container, or guest `hostfwd`. The QEMU VNC listener was verified on
`127.0.0.1:5901`. KVM was unavailable during preparation, so the launcher
selects TCG unless `/dev/kvm` later becomes readable and writable.

## Validation record and limitations

Static validation passed: the wrappers pass Bash syntax, ShellCheck, and shfmt
checks; both QEMU image checks passed; and a paused QEMU configuration test
accepted the selected storage, NIC, VNC, and TCG arguments while attached only
to a temporary blank disk. Dynamic validation then started the target through
`run-qemu.sh`, confirmed that the QEMU process remained alive, verified the
`127.0.0.1:5901` listener, logged DHCP Request/ACK for
`08:00:27:ef:c9:ba`, and reached only the assigned bridge address
`10.160.0.10` with ICMP. Guest login, graphical boot state, and service
readiness remain unassessed. Any later check must be limited to the documented
QEMU address and normal endpoints; it must not retrieve flags or exercise
vulnerabilities.
