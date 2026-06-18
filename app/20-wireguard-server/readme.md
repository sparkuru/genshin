# WireGuard Server

## Prerequisites

```bash
sudo modprobe wireguard
lsmod | grep wireguard
```

## Configuration

Create `.env` from the template:

```bash
cp .env.example .env
```

Edit `.env`:

| Variable | Description | Example |
|----------|-------------|---------|
| `SERVERURL` | Public domain/IP, or `auto` | `iida.ro` |
| `SERVERPORT` | UDP port | `51820` |
| `PEERS` | Number of clients or comma-separated names | `3` or `phone,laptop,desktop` |
| `INTERNAL_SUBNET` | VPN subnet | `10.13.13.0` |
| `ALLOWEDIPS` | Client routed IPs | `10.13.13.0/24` or `0.0.0.0/0` |

## Deploy

```bash
./init-wireguard-server.sh
./wireguard-server.sh up
```

## Client Setup

```bash
./wireguard-server.sh list
./wireguard-server.sh qr localtest
./wireguard-server.sh conf localtest
```

Named peer config path: `./config/peer_<name>/peer_<name>.conf`

Numeric peer config path: `./config/peer<index>/peer<index>.conf`

## Management

```bash
./wireguard-server.sh status
./wireguard-server.sh logs
./wireguard-server.sh restart
./wireguard-server.sh down
```

## Firewall

```bash
sudo ufw allow "$SERVERPORT/udp"
```

When `PEERS`, `SERVERURL`, `SERVERPORT`, `INTERNAL_SUBNET`, or `ALLOWEDIPS` changes, recreate the container:

```bash
./wireguard-server.sh down
./wireguard-server.sh up
```
