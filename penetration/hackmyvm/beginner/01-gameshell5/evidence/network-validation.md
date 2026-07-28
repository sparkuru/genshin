# Docker bridge validation

- Docker bridge: Docker-managed default network `bridge`, Linux bridge `docker0`, subnet `10.160.0.0/20`.
- Host bridge/gateway: `10.160.0.1`; fixed QEMU lease: `10.160.0.10`; DHCP DNS: `1.1.1.1`.
- Guest lease: `10.160.0.10` assigned to source MAC `08:00:27:ef:c9:ba`.
- DHCP evidence: the bridge-bound DHCP process logged a DHCP Request/ACK exchange for that MAC.
- Host reachability: one ICMP echo to `10.160.0.10` succeeded.
- Console isolation: QEMU VNC listens on `127.0.0.1:5901` only.
- DHCP provides Docker's gateway and DNS. Docker default NAT may give the guest external egress; this is an explicit, non-isolated topology.
