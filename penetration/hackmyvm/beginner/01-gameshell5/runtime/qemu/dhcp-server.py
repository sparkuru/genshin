#!/usr/bin/env python3

import os
import signal
import socket
import struct
import sys
from pathlib import Path
from types import FrameType


def ipv4_bytes(address: str) -> bytes:
    """Convert an IPv4 address to four bytes."""
    return socket.inet_aton(address)


def message_type(packet: bytes) -> int | None:
    """Return the DHCP message type from a BOOTP packet."""
    offset = 240

    while offset < len(packet):
        code = packet[offset]
        if code == 255:
            return None
        if code == 0:
            offset += 1
            continue
        if offset + 1 >= len(packet):
            return None
        length = packet[offset + 1]
        if offset + length + 2 > len(packet):
            return None
        if code == 53 and length == 1:
            return packet[offset + 2]
        offset += length + 2

    return None


def response_for(
    request: bytes,
    response_type: int,
    server_address: str,
    lease_address: str,
    subnet_mask: str,
    broadcast_address: str,
    router_address: str,
    dns_server: str,
) -> bytes:
    """Build a DHCP offer or acknowledgement for the fixed lab lease."""
    response = bytearray(240)
    response[0] = 2
    response[1] = request[1]
    response[2] = request[2]
    response[4:12] = request[4:12]
    response[16:20] = ipv4_bytes(lease_address)
    response[20:24] = ipv4_bytes(server_address)
    response[28:44] = request[28:44]
    response[236:240] = struct.pack("!I", 0x63825363)

    options = b"".join(
        (
            bytes((53, 1, response_type)),
            bytes((54, 4)) + ipv4_bytes(server_address),
            bytes((1, 4)) + ipv4_bytes(subnet_mask),
            bytes((28, 4)) + ipv4_bytes(broadcast_address),
            bytes((3, 4)) + ipv4_bytes(router_address),
            bytes((6, 4)) + ipv4_bytes(dns_server),
            bytes((51, 4)) + struct.pack("!I", 86400),
            bytes((255,)),
        )
    )
    return bytes(response) + options


def stop_handler(_signal_number: int, _frame: FrameType | None) -> None:
    """Stop the DHCP server cleanly on a lifecycle signal."""
    raise SystemExit(0)


def main() -> int:
    """Serve one fixed DHCP lease only on the selected Docker bridge."""
    bridge_name = os.environ["GAMESHELL5_DHCP_INTERFACE"]
    pid_path = Path(os.environ["GAMESHELL5_DHCP_PID_FILE"])
    server_address = os.environ["GAMESHELL5_DHCP_SERVER_ADDRESS"]
    lease_address = os.environ["GAMESHELL5_DHCP_LEASE_ADDRESS"]
    subnet_mask = os.environ["GAMESHELL5_DHCP_SUBNET_MASK"]
    broadcast_address = os.environ["GAMESHELL5_DHCP_BROADCAST_ADDRESS"]
    router_address = os.environ["GAMESHELL5_DHCP_ROUTER_ADDRESS"]
    dns_server = os.environ["GAMESHELL5_DHCP_DNS_SERVER"]

    signal.signal(signal.SIGTERM, stop_handler)
    signal.signal(signal.SIGINT, stop_handler)

    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as server_socket:
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_BINDTODEVICE, f"{bridge_name}\0".encode())
        server_socket.bind(("0.0.0.0", 67))
        pid_path.write_text(f"{os.getpid()}\n", encoding="utf-8")
        sys.stdout.write(
            f"DHCP server ready on {bridge_name}: lease={lease_address}; "
            f"router={router_address}; dns={dns_server}\n"
        )
        sys.stdout.flush()

        try:
            while True:
                packet, _ = server_socket.recvfrom(4096)
                if len(packet) < 240 or packet[236:240] != struct.pack("!I", 0x63825363):
                    continue
                request_type = message_type(packet)
                response_type = 2 if request_type == 1 else 5 if request_type == 3 else None
                if response_type is None:
                    continue
                server_socket.sendto(
                    response_for(
                        packet,
                        response_type,
                        server_address,
                        lease_address,
                        subnet_mask,
                        broadcast_address,
                        router_address,
                        dns_server,
                    ),
                    (broadcast_address, 68),
                )
                client_mac = ":".join(f"{byte:02x}" for byte in packet[28:34])
                sys.stdout.write(f"DHCP {request_type} {client_mac} -> {lease_address}\n")
                sys.stdout.flush()
        finally:
            if pid_path.exists() and pid_path.read_text(encoding="utf-8").strip() == str(os.getpid()):
                pid_path.unlink()


if __name__ == "__main__":
    sys.exit(main())
