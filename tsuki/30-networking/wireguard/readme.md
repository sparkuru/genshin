# WireGuard

当前实现为 VPS hub、站点边界 1:1 Prefix NAT 和 road-warrior，支持两个重叠 IPv4 LAN 互通。Split DNS 尚未部署。

- 网络说明：[拓扑](../docs/network/topology.md)、[地址规划](../docs/network/address-plan.md)、[数据包路径](../docs/network/packet-flow.md)。
- 公开配置：[VPS](../configs/vps/)、[公司 OpenWrt](../configs/corp-openwrt/)、[家庭 OpenWrt](../configs/home-openwrt/)。
- 本地实验：[compose.yaml](compose.yaml)。在本目录执行 `docker compose -f compose.yaml config --quiet` 可检查配置；构建路径相对于 Compose 文件。
- VPS 工具与部署：[vps/README.md](vps/README.md)、[Docker runtime](vps/docker/wireguard-server/README.md)。部署包内的 `wg0.conf.example` 随 runtime 保留。
- 客户端：[clients/a1/](clients/a1/)。

## 私有 handoff 与 agent 接管

本地档案位于 `handoff/handoff-overlap-lan-vpn.md`，整个 `handoff/` 被 Git 忽略。迁移前的根目录 `handoff/` 内容已完整移到这里；历史档案中的旧仓库相对路径需要按新目录定位，远端部署路径不因本次整理而改变。

接管时先读档案的当前摘要、权限范围、证据和下一步，再核对实际环境。真实地址、管理入口和操作记录留在该目录；密码、私钥和 token 只引用安全存储位置。目录应限制为 owner-only，并单独备份；Git 忽略不提供备份。

公开克隆不包含 handoff，可在本目录执行 `mkdir -p -m 700 handoff` 创建。
