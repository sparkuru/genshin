# WireGuard Server

## Prerequisites

```bash
# Load WireGuard kernel module
sudo modprobe wireguard

# Verify module loaded
lsmod | grep wireguard
```

## Configuration

Edit `wireguard-server.yml`:

| Variable | Description | Example |
|----------|-------------|---------|
| `SERVERURL` | Public domain or IP | `vpn.example.com` |
| `SERVERPORT` | UDP port | `51820` |
| `PEERS` | Number of clients (or comma-separated names) | `3` or `phone,laptop,desktop` |
| `INTERNAL_SUBNET` | VPN subnet | `10.13.13.0` |
| `ALLOWEDIPS` | Client allowed IPs | `0.0.0.0/0` (all traffic) |

## Deploy

```bash
# Initialize
./init-wireguard-server.sh

# Start
docker-compose -f wireguard-server.yml up -d
```

## Client Setup

```bash
# List all peers
./wireguard-server.sh list

# Show QR code (for mobile)
./wireguard-server.sh qr peer1

# Show config file
./wireguard-server.sh conf peer1
```

Config files location: `./config/peer_<name>/peer_<name>.conf`

## Management

```bash
# View logs
./wireguard-server.sh logs

# Restart after config change
./wireguard-server.sh restart

# Add more peers: modify PEERS in yml, then restart
```

## Firewall

```bash
# Open UDP port
sudo ufw allow 51820/udp
```
