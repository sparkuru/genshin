# sing-box Trojan configuration

`config.json` is the deployment configuration. `config.example.json` is a secret-free template. Replace every placeholder before deployment.

## ECH

ECH encrypts the ClientHello inner name. It requires a sing-box version with ECH support, an ECH private key on the server, and a matching public ECHConfigList on each client or in an authoritative DNS HTTPS record.

Generate an ECH key pair with a stable public name:

```sh
sing-box generate ech-keypair <public-name>
```

Save the generated ECH key PEM as `cert/ech-keys.pem` with mode `0600`. Keep it private. Save the generated ECH configuration separately as `cert/ech-config.pem`; it is public and is used by clients and DNS.

The server configuration is enabled in `config.example.json`:

```json
"ech": {
  "enabled": true,
  "key_path": "./cert/ech-keys.pem"
}
```

Validate the configuration before restarting the service:

```sh
sing-box check -c config.json
```

## Client configuration

For Mihomo, copy the base64 ECHConfigList from `ech-config.pem` into each proxy that should use ECH:

```yaml
ech-opts:
  enable: true
  config: <base64-ech-config-list>
```

Use a current Mihomo Meta core and keep `tls: true` and certificate verification enabled.

For a sing-box client, use the public configuration file:

```json
"ech": {
  "enabled": true,
  "config_path": "./cert/ech-config.pem"
}
```

## DNS publication

Clients without a static ECH configuration can obtain it from an authoritative DNS HTTPS record. Publish the public ECHConfigList only:

```text
<proxy-host> HTTPS 1 . ech=<base64-ech-config-list>
```

The proxy host and every same-name record must be DNS only for a manually managed HTTPS record to be served by Cloudflare. Confirm that the DNS provider accepts arbitrary `ech` SvcParam values, then verify with:

```sh
dig @1.1.1.1 HTTPS <proxy-host>
```

Never publish or commit `ech-keys.pem`, certificates' private keys, Trojan passwords, or API tokens.
