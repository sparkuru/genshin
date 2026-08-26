# 网络拓扑（公开演示）

状态：本文描述可复现的 WireGuard、站点 Prefix NAT、客户端策略路由和 road-warrior 架构；生产 endpoint、地址和管理入口不写入公开文档。Split DNS 尚未设计。

## 逻辑拓扑

```text
                           www / lan3
                         /             \\
                        /               \\
                 c WAN/PPPoE          g WAN
                 c LAN .1             <COMPANY_UPLINK_IP>
                    |                    |
              lan1 192.0.2.0/24  lan2 192.0.2.0/24
                    |                    |
             a1 / d / f              a2 / other hosts
                    \\                    /
                     \\                  /
                      \\                /
                       VPS 10.90.0.1
                      /       |        \\
                     /        |         \\
             c 10.90.0.2  g 10.90.0.3  away-demo 10.93.0.10
                       WG transit: 10.90.0.0/24
```

WireGuard 连接采用 hub-and-spoke：c、g、road-warrior 都主动连接 VPS。VPS 不需要知道两个重叠 LAN 的 `192.0.2.0/24`。

参考实现：c/g 使用 `/etc/init.d/overlap-vpn` 原生脚本，VPS 使用 `<VPS_PROJECT_DIR>` 的 host-network Docker 容器；客户端配置按需由 `wg-quick` 启停。VPS 原生 `wg-quick@wg0` 可保留为禁用的回滚服务。

VPS 容器挂载宿主机 `/etc/wireguard`、`/etc/overlap-vpn` 和 `/lib/modules`，因此 `wg0`、kernel route、`PostUp/PostDown` iptables 规则仍属于 VPS 宿主机网络命名空间。生产 Compose 不使用 `ports`，云防火墙需放行所选 UDP 端口；变更端口前以 `wg show wg0 listen-port` 为准。

## 站点边界

```text
家庭侧地址 192.0.2.X  <=>  家庭虚拟地址 10.91.0.X
公司侧地址 192.0.2.X  <=>  公司虚拟地址 10.92.0.X
```

Prefix NAT 位于 c/g 的站点边界，不放在 VPS。VPS 只转发演示中的 `10.91`、`10.92` 和 WG transit/road-warrior 地址。

## 管理访问链路（部署参考）

```text
客户端 -> <HOME_MANAGEMENT_HOST> -> www -> <COMPANY_UPLINK> -> g WAN SSH
```

若必须经家庭侧设备转发到公司上联，转发器只应绑定明确的管理入口：

```text
socat TCP-LISTEN:<MANAGEMENT_PORT>,reuseaddr,fork TCP:<COMPANY_UPLINK_IP>:22
```

访问命令使用部署时记录的管理主机、端口和管理员账号：

```text
ssh -p <MANAGEMENT_PORT> <ADMIN_USER>@<MANAGEMENT_HOST>
```

管理回退入口不是 g 的 LAN 地址；后续变更不得关闭或覆盖该回退链路。真实管理主机、端口和上联地址只记录在本地 handoff。

## 隔离要求

- 不桥接两个真实的 `192.0.2.0/24`。
- 不把两个真实 LAN 写入同一个 VPS peer 的 `AllowedIPs`。
- 默认不允许 VPN 侧无限制访问 c/g 的管理平面。
- `10.90.0.0/24` 是隧道基础设施地址；站点主机身份使用 `10.91` / `10.92`。
- road-warrior 设备只使用独立的 `10.93.0.X/32`，不把重叠 `192.0.2.0/24` 写进 peer。
- c 的 fw3/legacy `NETMAP` 规则位于 `/etc/overlap-vpn/firewall.user`，通过 fw3 script include 加载。
- g 的 nft Prefix NAT 位于 `/etc/nftables.d/90-overlap-vpn.nft`，以 chain-only include 接入 fw4。
- 示例 VPS 使用 `51820/udp`；TCP 放行不被 WireGuard 使用。

## Road-warrior 扩展

每台新增设备从 `10.93.0.11/32` 起分配一个未占用地址，生成自己的 WireGuard key，VPS 只登记该公钥和 `/32`。
VPS 上的 `/usr/local/sbin/overlap-vpn-road-peer` 会同时更新活动 peer、VPS 返回路由、`wg0.conf` 和登记表；不会改动 c/g 的站点 peer。生产地址池由部署环境配置，公开值只是演示。
