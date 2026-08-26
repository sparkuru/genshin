# 回滚方案（公共模板）

状态：模板；VPS WireGuard 采用 host-network Docker 的参考架构。执行前必须以目标机当前状态和本地 handoff 为准。

## 变更前必须保存

每次变更前，都应在 c、g、VPS 和必要的管理跳板上创建 owner-only 快照；具体路径只记录在本地 handoff，不写入公开文档。

变更前保存的内容包括：

- OpenWrt UCI network/firewall 配置；
- 当前 nftables/iptables 渲染结果；
- 当前路由表、策略路由和 sysctl；
- 当前监听端口和 WireGuard 状态；
- 当前 f 上的 g SSH 转发状态。

备份可放在远端 `/tmp` 会话目录或配置所在目录，权限必须为 owner-only。PPPoE 凭据、任何私钥和客户端配置必须脱敏或排除。

## 参考实现

1. c/g 安装 WireGuard 工具；VPS 安装 nftables 工具但未启用 nftables service。
2. VPS 使用 `<VPS_PROJECT_DIR>` 的 host-network Docker；c/g 使用独立 `/etc/init.d/overlap-vpn`，避免重启整体 OpenWrt network。
3. c 使用 legacy `NETMAP`，g 使用 fw4 nft Prefix NAT；VPS 不做站点 NAT。
4. 客户端只对指定 NetworkManager 连接注入 translated/road-warrior 策略路由；按需启用的 Linux road-warrior 使用独立 table `2023`，不自动接管默认路由。
5. 客户端配置与私钥留在客户端的 root-only WireGuard 目录；VPS road-warrior 登记表为 `/etc/overlap-vpn/road-warriors.tsv`。

任一步失败都停止，不在同一窗口继续扩大变更范围。

## 回滚触发条件

- c 或 g 的 LAN 终端失去本地网关；
- c/g/VPS 的原有互联网或管理路径异常；
- 原有 DNAT/端口转发行为改变；
- 发现源地址仍是真实的 `192.0.2.X`；
- WireGuard 配置导致现有 SSH 回退链路不可用。

## 回滚原则

- 先禁用新建的 `wg0`、translated 路由和 NAT 链；
- 恢复变更前的 UCI、fw3/fw4/nftables/iptables 和 sysctl；
- 不删除现有 Docker、端口映射或 PPPoE 配置；
- 不重启整个网络，除非已经确认 SSH 回退路径可用；
- 回滚后重新验证 c、g 的原有默认路由和端口映射。

## 回滚顺序

1. VPS：在 `<VPS_PROJECT_DIR>` 执行 `./manage.sh down`；确认所选 UDP 监听消失，再执行 `sudo systemctl enable --now wg-quick@wg0`（仅当该回滚服务已准备好）。
2. c/g：执行 `/etc/init.d/overlap-vpn stop`；删除本轮新增的 `/etc/init.d/overlap-vpn`、`/usr/sbin/overlap-vpn` 和 `/etc/wireguard/privatekey`。
3. c：删除 `firewall.overlap_vpn*` UCI section，删除 `/etc/overlap-vpn/firewall.user`，执行 `/etc/init.d/firewall reload`；按需恢复 `/etc/opkg/distfeeds.conf` 的备份。
4. g：删除 `firewall.overlap_vpn*` UCI section 和 `/etc/nftables.d/90-overlap-vpn.nft`，执行 `/etc/init.d/firewall reload`。
5. 客户端：如 road-warrior 接口正在运行，先执行 `sudo wg-quick down <CLIENT_INTERFACE>`；仅在确认不再需要时删除对应的 root-only 配置/私钥，以及 dispatcher 脚本和 table 2022 中的演示 translated/road-warrior 路由。
6. VPS：从 `/etc/wireguard/wg0.conf` 和 `/etc/overlap-vpn/road-warriors.tsv` 删除对应 road-warrior peer，执行 `sudo wg set wg0 peer <public-key> remove`、`sudo ip route del <address>/32 dev wg0`，然后重启或重新加载 `wg-quick@wg0`；操作前保留当前备份。

本轮生成的私钥不在变更前备份中；回滚时删除对应文件即可，不要把私钥复制到项目或恢复档案。

## 连接安全

g 的管理入口依赖 f 上的 `socat`。任何 g 侧变更前必须保留当前 SSH 会话，并准备第二个通过 f 的回退会话。远程 SSH 环境下默认不允许可能立即断开连接的网络 reload。
