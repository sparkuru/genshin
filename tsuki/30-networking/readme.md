# 个人 Networking 探索

这是我的个人 networking 探索、实现与可公开复现参考，按 WireGuard、OpenVPN 区分。当前已有 WireGuard 重叠网段互联实现；OpenVPN 暂留入口。下文的地址均为公开演示值。

## 当前状态

- 已有可本地验证的 WireGuard hub、双向 Prefix NAT、客户端策略路由和 road-warrior 流程。
- Split DNS 尚未部署；历史设计输入见 [`docs/history/agent-prompts.md`](docs/history/agent-prompts.md)，它不是当前运行事实或配置来源。
- 私有运行上下文放在本机的 [`wireguard/handoff/handoff-overlap-lan-vpn.md`](wireguard/handoff/handoff-overlap-lan-vpn.md)；`wireguard/handoff/` 由 `.gitignore` 排除，不应提交。

## 阅读路径

1. 从 [`docs/network/topology.md`](docs/network/topology.md) 了解拓扑和隔离要求。
2. 查看 [`docs/network/address-plan.md`](docs/network/address-plan.md) 与 [`docs/network/packet-flow.md`](docs/network/packet-flow.md) 理解地址映射和数据包路径。
3. 用 [`wireguard/compose.yaml`](wireguard/compose.yaml) 复现，再按 [`docs/operations/rollback.md`](docs/operations/rollback.md) 评估变更与回滚。
4. 需要接手已部署环境时，只在本机查看 `wireguard/handoff/`；公开资料不能替代其中的运行事实。

## 网络代号

为了方便说明，下面用代号称域。

不同网络域：

- 家里称 lan1（`192.0.2.0/24`）
- 公司工位独立子网称 lan2（`192.0.2.0/24`）；lan2 掌管我实际各种网络设备，统一通过 lan3 分配的单个 IP 连接到 lan3
- 公司内网称 lan3（`172.x.x.x/22`），通过网关连 www
- 公网称 www
- 另有既有企业 overlay 网络，称 vpn1
- 还有个人 VPS，是买的云厂商服务，有公网 IP；平常会通过既有中转服务作中转联通各地网络设备，称 frp1；当前已用 WireGuard 数据面实现 vpn2，Split DNS 仍未部署

个人工作 Linux 设备（主力机）：

- 在家时是 a1
- 在公司是 a2
- 出差时是 a3

家里个人 Windows 生活游戏设备：b。

家里出网网关 OpenWrt：c（`192.0.2.1`），掌管 lan1，对外连接到 www。

家里 Wi-Fi 路由器：d（`.6`），平常 a1 都是通过 d 访问到 lan1；家里其他 Wi-Fi 设备：e，通过 d 连接 lan1；家里 aio/nas 设备：f（`.3`），是个 PVE，直连 c；内部各种 VM 就称作 cx，也是直连 c。

工位上的网关 OpenWrt：g（`192.0.2.1`），掌管 lan2，统一通过 lan3 分配的单个 IP 连接到 lan3。

## 公开演示参数（不代表生产）

以下是可公开复现的中性示例；生产 endpoint、地址、用户名、路径和密钥不从本文件推导。

- WG transit：`10.90.0.0/24`；VPS `10.90.0.1`、c `10.90.0.2`、g `10.90.0.3`
- 家庭 translated：`10.91.0.0/24`，`192.0.2.X <=> 10.91.0.X`
- 公司 translated：`10.92.0.0/24`，`192.0.2.X <=> 10.92.0.X`
- road-warrior：`10.93.0.0/24`；示例外出设备使用 `10.93.0.10/32`，后续设备从 `.11` 起逐台分配
- VPS WireGuard：演示 UDP `51820`（WireGuard 不使用 TCP）；实际部署端口以运行时 `wg show wg0 listen-port` 为准
- 实现：c/g 使用原生 `/etc/init.d/overlap-vpn`；VPS 使用 host-network Docker，原生 `wg-quick@wg0` 可作为禁用的回滚服务
- 演示状态：Compose、双向 Prefix NAT、客户端策略路由和 road-warrior 流程可在本地验证；Split DNS 尚未部署
- 客户端配置应保存在客户端的 root-only WireGuard 目录；VPS 容器挂载 `/etc/wireguard`、`/etc/overlap-vpn`，并使用 `overlap-vpn-road-peer` 扩展其他设备
- Docker 不改变 WireGuard 的宿主机网络命名空间；容器重启后需等待站点 keepalive 收敛，首个未完成握手的探测包可能丢失
- 客户端接口按需启停，避免在本地网络可直达时无必要绕行 VPS
- 若客户端已有 TUN/策略路由，只针对 VPN 前缀设置更高优先级的精确规则，不绕过整个 `10/8`

## 目录地图

- [`wireguard/`](wireguard/)：WireGuard 实验、客户端工具、VPS 实现和私有 handoff。
- [`openvpn/`](openvpn/)：OpenVPN 入口，尚无实现；私有上下文放在其 `handoff/` 中。
- [`configs/`](configs/)：公开配置参考，按 `vps/`、`corp-openwrt/`、`home-openwrt/` 区分；目前均服务于 WireGuard 方案。
- [`wireguard/compose.yaml`](wireguard/compose.yaml)：单文件本地复现入口，包含 VPS、家庭、公司、外出和验收主机。
- [`docs/network/`](docs/network/)：地址规划、拓扑和数据包路径；[`docs/operations/`](docs/operations/)：回滚与运维边界。
- [`docs/history/`](docs/history/)：已经归档的设计输入，不作为当前运行事实或配置来源。
- [`configs/home-openwrt/`](configs/home-openwrt/)、[`configs/corp-openwrt/`](configs/corp-openwrt/)：家庭 c、公司 g 的 WRT-like 配置参考。
- [`wireguard/clients/a1/`](wireguard/clients/a1/)：a1 本机策略路由脚本；[`wireguard/vps/`](wireguard/vps/)：VPS 文档、示例、脚本和 Docker 实现。
- [`wireguard/handoff/`](wireguard/handoff/)：仅接手运行环境所需的本地档案；默认由 `.gitignore` 排除，目录和文件均为 owner-only，不放置私钥。

## 快速复现与日常入口

[`wireguard/compose.yaml`](wireguard/compose.yaml) 包含 VPS hub、家庭 c、公司 g、外出 client，以及两个用于验收的 LAN 主机。示例把两个逻辑 LAN 都定义为 `192.0.2.0/24`；Docker 实验因不能创建重叠 bridge network，使用 `192.168.101.0/24` 和 `192.168.102.0/24` 替身。以下命令从仓库本目录执行。

```sh
docker compose -f wireguard/compose.yaml config --quiet
docker compose -f wireguard/compose.yaml up -d --build
docker compose -f wireguard/compose.yaml exec away-test ping -c 3 10.91.0.100
docker compose -f wireguard/compose.yaml exec away-test ping -c 3 10.92.0.100
docker compose -f wireguard/compose.yaml down -v
```

生产网络在 c/g 完成一次性接入后，新增外出设备只需在 VPS 项目目录执行 `./manage.sh road-issue client-name > client-name.conf`，再把配置导入外出设备；不需要再次修改 c/g。公开副本默认使用演示前缀和 `vpn.example.invalid`，生产部署应通过环境变量或生产 VPS 上的受控源配置真实值。

VPS 状态备份脚本保存在 [`wireguard/vps/scripts/backup-wireguard-state.sh`](wireguard/vps/scripts/backup-wireguard-state.sh)。它备份 root-only 的 `wg0.conf`、road-warrior 登记表、运行状态和 Docker 部署源文件，不把备份内容复制回本地；部署时应将脚本通过受控 SSH 管理入口送入 `sudo -n sh -s` 执行，归档默认写入 `/var/backups/overlap-vpn`。公开文档不记录该入口的真实主机、用户名或项目路径。

供后续 agent 接管的敏感运行上下文保存在本地 [`wireguard/handoff/handoff-overlap-lan-vpn.md`](wireguard/handoff/handoff-overlap-lan-vpn.md)，该目录由 `.gitignore` 排除且仅 owner 可读；它记录远端主机、路径、地址规划、公钥和验证证据，不记录私钥、密码或 token。公开复现副本不需要这个目录。

## 版本控制与隐私边界

本目录的公开复现内容包括

- `wireguard/compose.yaml`、文档、路由器配置参考、`*.example` 模板和脚本；
- 真实部署配置、客户端导出配置、WireGuard 私钥、road-warrior 登记表、`.env`、备份归档和 `wireguard/handoff/` 属于本机或 VPS 私有状态，不应提交
- `.gitignore` 只提供默认防护，提交前仍应检查 `git diff --cached`
- 不要用 `git add -f` 绕过这些规则
