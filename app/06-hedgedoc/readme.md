# HedgeDoc

`hedgedoc-offline.yml` starts HedgeDoc, MariaDB, and Nginx on an isolated Docker network. Nginx is the only published service. HedgeDoc is configured with one explicit public origin, so login redirects, assets, Socket.IO, and session cookies use the same browser origin.

## First deployment

Choose a stable LAN address or DNS name, then generate the local runtime configuration and persistent session secret.

```sh
./deploy-hedgedoc.sh \
  --path /srv/hedgedoc \
  --public-url http://192.168.1.80:9426
```

The deployment script downloads the current templates from this repository's GitHub raw-content URL, generates local secrets, and starts the offline stack by default. Use `--download-only` to only download and initialize the installation directory.

For HTTPS behind an external reverse proxy, use the HTTPS origin instead. That proxy must forward `Host`, `X-Forwarded-For`, and `X-Forwarded-Proto`, including WebSocket upgrades for `/socket.io/`.

```sh
./init-hedgedoc.sh --public-url https://md.example.internal
docker compose --env-file .hedgedoc.env -f hedgedoc-offline.yml up -d
```

The generated `.hedgedoc.env` contains database passwords and is ignored by Git. `config/secrets/session-secret` is generated once with mode `0600`; do not remove it unless every existing browser session should be invalidated.

## Existing deployment

Do not run the initializer against an existing `db/` directory unless `.hedgedoc.env` already contains that database's current credentials. To change only the public origin while preserving those credentials, run:

```sh
./init-hedgedoc.sh --public-url http://192.168.1.80:9426 --force
```

## External database mode

`hedgedoc.yml` is for an existing database. Supply its connection URL while initializing, then start it with the same generated environment file.

```sh
./deploy-hedgedoc.sh \
  --path /srv/hedgedoc \
  --public-url https://md.example.internal \
  --external-db \
  --db-url 'mysql://hedgedoc:password@mysql.example.internal:3306/hedgedoc'
```

HedgeDoc 1.11 uses one port value for both its listener and generated public URLs. The bundled Nginx proxy keeps that listener private inside Docker while publishing the selected public port. Do not change Docker port mappings independently of the public URL.
