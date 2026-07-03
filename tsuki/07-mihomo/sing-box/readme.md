# sing-box

This folder mirrors the sing-box deployment.

## Files

- `sing-box.yml`: source Docker Compose file from the target server.
- `config.json`: source runtime config from the target server. It contains real credentials and is ignored by Git.
- `sing-box.example.yml`: generic Compose reference file.
- `config.example.json`: desensitized reference config with the same runtime shape.

## Users

- `full-access`: keeps the original `wkyuu` password and allows all proxied traffic.
- `guest`: uses a generated password and can only proxy the LLM domain allowlist in `route.rules`; all other traffic is rejected.

## Usage

```sh
docker compose -f sing-box.yml up -d
```

The Compose file mounts `./data` to `/etc/sing-box`, while the copied source config is kept at this folder root for reference. For a direct deployment, place the runtime config at `./data/config.json` and provide the referenced certificate files.
