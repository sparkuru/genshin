# browseros-neo in no-gui host with docker

for no gui host, like ubuntu server, pve, ...;

use noVNC to offer the browseros-neo;

all services in docker compose, require dirs mount only.

```text
docker/
├── compose.yaml
├── config/
│   ├── neo.toml
│   └── mcp-nginx.conf
└── data/                 # mount to Neo:/data, include browseros-neo's profile, cookie, downloads and agent records, it might contain login tokens.
```

## usage

```sh
docker compose up -d --wait
docker compose ps
```

noVNC: `http://HOST_IP:6080`, for human.
MCP: `http://HOST_IP:9010/mcp`

## agents' registration

```sh
codex mcp add browseros-neo --url http://127.0.0.1:9010/mcp
opencode mcp add --global browseros-neo --url http://127.0.0.1:9010/mcp
codex mcp get browseros-neo
opencode mcp list
```

check mcp handshake:

```sh
curl --noproxy '*' -sS \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -d '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2025-03-26","capabilities":{},"clientInfo":{"name":"diagnostic","version":"1.0"}}}' \
  http://127.0.0.1:9010/mcp
```

## nginx

allow lan's hosts use this MCP: `agent → HOST_IP:9010 → nginx → browseros-neo MCPs in docker`
