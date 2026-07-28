# GameShell5 inventory evidence

The source ZIP was inspected read-only. Its single `GameShell5.ova` member
contains an OVF descriptor, a stream-optimized VMDK, and an SHA-1 manifest.

| Item | Evidence |
| --- | --- |
| Guest OS and architecture | OVF: `Debian_64`; `virt-inspector`: Debian GNU/Linux 10.13, x86_64 |
| Firmware | VirtualBox default BIOS configuration; no UEFI declaration |
| Storage | 30 GiB stream-optimized VMDK; OVF: SATA/AHCI |
| Network | OVF: E1000; source MAC `08:00:27:EF:C9:BA`; guest DHCP interface `enp0s3` |
| Guest services | systemd units include InspIRCd, a Python IRC bot, and SSH |
| Source-only integrations | VirtualBox bridge interface, shared folder, USB tablet, audio, and clipboard metadata |

`qemu-img check` reported no errors for both the extracted VMDK and the derived
QCOW2. No target process was started during inventory.
