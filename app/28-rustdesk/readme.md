# RustDesk Server OSS

This package runs the official RustDesk Server OSS backend on the `lan1` host
`192.168.9.3`. It contains the ID/rendezvous server (`hbbs`) and relay server
(`hbbr`) for native RustDesk clients.

The stack publishes only the ports needed by the Windows, macOS, Debian, and
iPad clients:

| Port | Protocol | Purpose |
| --- | --- | --- |
| 21115 | TCP | NAT type test |
| 21116 | TCP + UDP | ID registration, rendezvous, and hole punching |
| 21117 | TCP | Relay |

WebSocket ports `21118` and `21119` are intentionally not published because
the native clients do not need the RustDesk web client. Port `21114` is also
not published because it is for the Pro API.

## First start

The remote host currently uses the legacy `docker-compose` command:

```sh
cp .env.example .env
chmod 600 .env
./init-rustdesk.sh
docker-compose -p rustdesk -f rustdesk.yml config
docker-compose -p rustdesk -f rustdesk.yml pull
docker-compose -p rustdesk -f rustdesk.yml up -d
```

The first start creates `data/id_ed25519` and
`data/id_ed25519.pub`. Keep `data/id_ed25519` private. The data directory and
`.env` are ignored by Git.

Verify the private-key mode after the first start. The upstream image may
create it as a root-owned file:

```sh
sudo chmod 600 data/id_ed25519
chmod 644 data/id_ed25519.pub
```

Check the service and retrieve the public key with:

```sh
docker-compose -p rustdesk -f rustdesk.yml ps
docker-compose -p rustdesk -f rustdesk.yml logs --tail=100 hbbs hbbr
cat data/id_ed25519.pub
```

## Client configuration on lan1

Install the official RustDesk client for [Windows, macOS, Linux/Debian, or
iPad](https://rustdesk.com/docs/en/client/). In each client, open
`Settings -> Network -> Unlock Network Settings` and set:

- ID Server: `192.168.9.3`
- Relay Server: leave blank (or use `192.168.9.3:21117`)
- API Server: leave blank; it is only needed by RustDesk Server Pro
- Key: the complete contents of `data/id_ed25519.pub`

The iPad client can connect to and control desktop clients, but the official
client documentation notes that iOS devices cannot be controlled remotely.

For devices outside `lan1`, use a stable public DNS name and configure the
router/firewall to forward the same TCP/UDP ports. Do not expose the WebSocket
ports directly; use a correctly configured reverse proxy if the web client is
needed.

## Operations

```sh
docker-compose -p rustdesk -f rustdesk.yml logs -f hbbs hbbr
docker-compose -p rustdesk -f rustdesk.yml restart
docker-compose -p rustdesk -f rustdesk.yml down
```

To upgrade, change `RUSTDESK_IMAGE` in `.env`, then run `pull` followed by
`up -d`. Do not run `down -v`: the server key and client identity data live in
`data/` and must survive upgrades.

Official references:

- [RustDesk Server OSS installation](https://rustdesk.com/docs/en/self-host/rustdesk-server-oss/install/)
- [RustDesk client configuration](https://rustdesk.com/docs/en/self-host/client-configuration/)
- [Official Docker Compose example](https://github.com/rustdesk/rustdesk-server/blob/master/docker-compose.yml)
