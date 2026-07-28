# Virtual machines and disk images

Use this reference for OVA/OVF, VMDK, VDI, VHD/VHDX, QCOW2, raw disks, and cloud images.

## Inspect first

- List an OVA as a tar archive; inspect the OVF manifest and descriptor before extracting the virtual disk.
- Record disk format, virtual size, backing files, architecture, firmware, controller type, NIC model, CPU/RAM, and any embedded shared-folder or bridge configuration.
- Treat an exported bridge-interface name or host shared-folder setting as source metadata, not a setting to reproduce.
- Inspect with `qemu-img info`; use `qemu-img check` for formats it supports. Do not run repair mode on the source image.

## Conversion

- VMware commonly imports OVA directly. If it does not, unpack the OVA and attach the VMDK to a newly configured VM.
- For QEMU/KVM, retain a VMDK only when QEMU supports it well enough for the use case; otherwise derive a QCOW2 copy:

```text
qemu-img convert -p -f vmdk -O qcow2 source.vmdk target.qcow2
```

- Verify the derived image with `qemu-img info` and `qemu-img check`. Hash both source and derived artifacts in the report.
- Do not convert in place. Do not flatten a backing-chain image without documenting the loss of snapshot lineage.

## First boot fidelity

- Match the guest architecture and firmware. Do not silently switch BIOS to UEFI or vice versa.
- Preserve the original disk controller where possible. A VM exported with SATA/AHCI should first boot with a SATA/AHCI-compatible configuration; switching to VirtIO too soon can fail before drivers load.
- Preserve the expected NIC model, often `e1000`, before attempting `virtio-net`.
- Keep source CPU/RAM as a baseline. Hardware identifiers, MAC addresses, timing, and device names can change across hypervisors; document them when potentially relevant.
- Exclude VirtualBox shared folders, clipboard integration, USB passthrough, sound, and display extras unless the challenge requires them.

## QEMU launcher shape

Generate a launcher that keeps its state and display behavior explicit. Include the input disk only from the derived output directory, use the local-only network recipe from `network-isolation.md`, and make KVM optional.

For VM-derived targets, make the QEMU/KVM launcher the authoritative high-fidelity path. Use a derived writable overlay for validation and reset when practical; keep the original and its first derived preservation copy unchanged. A Docker convenience candidate must not replace this launcher.

For a newly converted BIOS/SATA guest, start with an emulated storage controller or QEMU defaults compatible with the detected source, then optimize only after boot validation. Do not guess guest login credentials or perform an interactive install.

## Outcome expectations

Changing disk formats alone ordinarily does not alter files, services, flags, or vulnerabilities inside the guest. Changing the virtual hardware can alter interface names, DHCP leases, drivers, timing, firmware behavior, and hardware-identity checks. Report that distinction plainly. Refer to `runtime-selection.md` before making any Docker comparison claim.
