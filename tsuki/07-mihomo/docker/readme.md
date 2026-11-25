
build: `docker build -t mihomua:v1 .`

docker compose: `docker compose -f $PWD/mihomua.yaml up -d`

tree like this:

```bash
mihomua
├── config
│   ├── config.yaml
│   └── cache.db
├── bypass                # sidecar: un-hijack inbound DNAT replies
│   ├── Dockerfile
│   └── apply.sh
└── mihomua.yaml
```

## Remote deployment

Set the required values in `deploy.sh`, including `WAN_INTERFACE`. Generating a new configuration also requires `LAN_CIDR` and `SUBSCRIPTION_URL`. The WAN interface must exist on the target; it is used as Mihomo's outbound interface and by the bypass service. `TUN_DEVICE` defaults to `mihomo`, must have a different name from the WAN interface, and must be available on the target.

`BUILD_PROXY` is optional. When set, it is passed to remote image builds, GeoIP downloads, and the Mihomua container; local image builds use the local Docker configuration. When empty, the script passes no explicit proxy settings, though system or Docker proxy settings may still apply.

When generating a configuration, the script adds a provider named `subscription` but leaves proxy groups and rules unchanged. The template must reference that provider from whichever groups should use it and must define every policy referenced by its rules.

The interface names can also be supplied on the command line:

```bash
./deploy.sh --wan-interface vmbr0 --tun-device mihomo
```

To retain an existing configuration directory, add `--config-dir /path/to/config`. The script keeps its files and updates the selected WAN and TUN settings in `config.yaml`; set `CONTROLLER_PORT` to match the existing configuration for verification. Set `SSH_CONFIG_FILE` when a non-default SSH configuration is needed.

The deployment uses the host network and TUN automatic routing, so its routing rules can also affect traffic from other services on the host. With `--force`, the existing deployment is stopped before the script checks that its TUN interface has been released.

## bypass sidecar

mihomo `tun.auto-route: true` 会注入一条 `ip rule: not iif lo lookup <table>`，把所有非 lo 入向流量推进代理表

后果是将从 WAN 进来的连接被 DNAT 到 docker 容器后，容器的回包从 docker bridge 进入主机（`iif != lo`）

目的 IP 是公网（`main` 表里只有被 suppress 的默认路由），于是回包被发往 mihomo TUN —— 连接超时

LAN 内访问、host 自身访问都正常，**只有 WAN→docker 服务的入向连接挂掉**

`bypass/` 是同 compose 项目里的 sidecar：

- 用 mangle PREROUTING 给 vmbr0 上来自非本机源的 NEW 连接打 `fwmark 0x100`，存到 conntrack；
- 后续每个包从 conntrack 恢复 mark，回包路径自动继承；
- `ip rule pref 8500 fwmark 0x100/0x100 lookup main`（pref 早于 mihomo 的 9002）让带 mark 的流量走 main 表（含默认路由），回包从 vmbr0 出去。
- 容器主动出网（`iif=br-...`）不被 `-i vmbr0` 命中，仍走 mihomo —— 代理出网能力保留。

环境变量（`mihomua.yaml` 里调）：

- `WAN_IFACE`：宿主机 WAN/LAN 接口名，默认 `vmbr0`。
- `TUN_IFACE`：mihomo 的 `tun.device`，默认 `paimon`。
- `MARK` / `RULE_PREF`：fwmark 位段与 ip rule 优先级，默认 `0x100/0x100` / `8500`，与其它 fwmark 工具冲突时再调。

`docker compose down` 会触发 sidecar 内的 SIGTERM trap，自动拆除 mangle 规则与 ip rule，宿主 netns 恢复干净。
