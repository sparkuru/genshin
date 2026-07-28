# Local-only network isolation

Apply this reference whenever a generated runtime listens on a network port.

## Required invariant

Consoles and forwarded ports use `127.0.0.1`. The default QEMU discovery topology uses Docker's managed `docker0` bridge so the host can scan a stable guest address. Unlike an internal bridge, `docker0` normally uses Docker NAT and may provide external guest egress: label it non-isolated and obtain explicit user authorization before launch. Do not use Docker `--network host` or a LAN bridge.

Before launch, list every published port, mount, requested Linux capability, and network mode. Stop for explicit user confirmation before allowing LAN access, an external route, host networking, privileged mode, or a writable host mount.

## Docker / Compose

- Prefer a dedicated `internal: true` bridge network to prevent container egress.
- Publish only known-required ports and bind them explicitly: `127.0.0.1:8080:80`, never `8080:80`.
- Omit `privileged: true`, `network_mode: host`, broad bind mounts, and Docker socket mounts.
- Use a read-only root filesystem and dropped capabilities only if they do not change challenge behavior; document each exception.
- If the target does not need networking, use `network_mode: none` and do not publish ports.

Example:

```yaml
services:
  target:
    ports:
      - "127.0.0.1:8080:80"
    networks: [lab]
networks:
  lab:
    internal: true
```

## QEMU

Use Docker's managed default `docker0` bridge by default when the host needs direct guest discovery or scanning. This is QEMU networking, not a Docker conversion of the guest. Its NAT behavior is an intentional exception to the usual local-only isolation policy and needs explicit authorization.

- Inspect Docker's `bridge` network and `docker0` before launch. Record and validate its subnet, host/gateway address, and prefix; never create, alter, or remove Docker's default network.
- Select a fixed QEMU address inside that subnet after checking Docker endpoint allocations, and print the subnet, host/gateway, and QEMU address from the launcher.
- Attach QEMU through `-netdev bridge` and a QEMU bridge helper whose root-owned configuration allows exactly `docker0`. Do not use a broad `allow all` rule.
- Run DHCP only on `docker0`. Bind a host DHCP daemon with `SO_BINDTODEVICE`, or use an equivalently constrained service; issue the fixed lease for the preserved source MAC and provide the recorded Docker gateway and documented DNS server as router/DNS options.
- Preserve the source NIC model, MAC, PCI address, and guest interface-name expectations. A network-configured guest may depend on a stable PCI address such as `00:03.0` for `enp0s3`.
- Keep VNC, QMP, serial consoles, and any exceptional host forwards on `127.0.0.1`. A `127.0.0.1` bind is a host-side console address, not the guest subnet and cannot collide with a LAN subnet.
- Run bridge setup as a narrow, explicit privileged prerequisite. Do not run the target QEMU process as root merely to create a TAP interface.
- Use QEMU user networking with `restrict=on` only as an explicit fallback when `docker0` cannot be prepared safely; record the loss of direct host discovery.

Example bridge launch shape:

```text
-netdev bridge,id=net0,br=docker0,helper=/usr/lib/qemu/qemu-bridge-helper \
-device e1000,netdev=net0,mac=SOURCE_MAC,addr=0x3 \
-vnc 127.0.0.1:1
```

Docker `docker0` is not a LAN bridge, but its NAT can enable external egress. Stop for explicit confirmation before using it, enabling Docker host networking, a LAN bridge, privileged containers, or writable host mounts.

## Verify

- Confirm every console/forward bind is `127.0.0.1`, not `0.0.0.0`, `::`, or a LAN interface.
- Inspect Docker's `bridge` network and `docker0`: confirm the recorded subnet, host/gateway, prefix, and that the fixed QEMU address is not a Docker endpoint.
- Confirm the bridge helper allows only `docker0`; verify DHCP logs the preserved MAC and assigned lease, then test only the recorded guest address when host discovery is in scope.
- Confirm the DHCP response provides the recorded router and DNS, and record that default Docker NAT may supply external egress.
- Record the result and every intentional exception in `report.md`.
