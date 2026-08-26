
为了方便说明，下面用代号称域

不同网络域：
	- 家里称 lan1（192.0.2.0/24）
	- 公司工位独立子网称 lan2（192.0.2.0/24）；lan2 掌管我实际各种网络设备，统一通过 lan3 分配的单个 ip 连接到 lan3
	- 公司内网称 lan3（172.x.x.x/22），通过网关连 www
	- 公网称 www
	- 另有既有企业 overlay 网络，称 vpn1
	- 还有个人 vps，是买的云厂商服务，有公网 ip；平常会通过 既有中转服务 作中转联通各地网络设备，称 frp1；当前已用 WireGuard 数据面实现 vpn2，Split DNS 仍未部署
个人工作 linux 设备（主力机）：
	- 在家时是 a1
	- 在公司是 a2
	- 出差时是 a3

家里个人 windows 生活游戏设备：b

家里出网网关 openwrt：c（192.0.2.1），掌管 lan1，对外连接到 www

家里 wifi 路由器：d（.6），平常 a1 都是通过 d 访问到 lan1
家里其他 wifi 设备：e，通过 d 连接 lan1
家里 aio/nas 设备；f（.3），是个 pve，直连 c；内部各种 vm 就称作 cx，也是直连 c

工位上的网关 openwrt：g（192.0.2.1），掌管 lan2，统一通过 lan3 分配的单个 ip 连接到 lan3

---

## 公开演示参数（不代表生产）

以下是可公开复现的中性示例；生产 endpoint、地址、用户名、路径和密钥不从本文件推导。下面较早的 Agent A/B prompt 保留作设计历史，不能直接覆盖当前参数。

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

## 目录结构

- `compose.yaml`：单文件本地复现入口，包含 VPS、家庭、公司、外出和验收主机。
- `docs/network/`：地址规划、拓扑和数据包路径；`docs/operations/`：回滚与运维边界。
- `routers/home-openwrt/`、`routers/company-openwrt/`：家庭 c、公司 g 的 WRT-like 配置参考。
- `clients/a1/`：a1 本机策略路由脚本；`vps/`：VPS 文档、示例、脚本和 Docker 实现。
- `agent/`：仅 agent 接管使用的本地运行档案；默认由 `.gitignore` 排除，目录和文件均为 owner-only，不放置私钥。

## 快速复现与日常入口

本目录根部的 [`compose.yaml`](compose.yaml) 是单文件实验复现入口：它包含 VPS hub、家庭 c、公司 g、外出 client，以及两个用于验收的 LAN 主机。示例把两个逻辑 LAN 都定义为 `192.0.2.0/24`，Docker 实验因不能创建重叠 bridge network，使用 `192.168.101.0/24` 和 `192.168.102.0/24` 替身；演示 WireGuard/translated/road-warrior 前缀也仅用于复现。WRT 一次性配置清单和 fw3/fw4、Prefix NAT、`rp_filter`、默认网关注意事项均写在该文件顶部注释中。

```sh
docker compose -f compose.yaml config --quiet
docker compose -f compose.yaml up -d --build
docker compose -f compose.yaml exec away-test ping -c 3 10.91.0.100
docker compose -f compose.yaml exec away-test ping -c 3 10.92.0.100
docker compose -f compose.yaml down -v
```

生产网络在 c/g 完成一次性接入后，新增外出设备只需在 VPS 项目目录执行 `./manage.sh road-issue client-name > client-name.conf`，再把配置导入外出设备；不需要再次修改 c/g。公开副本默认使用演示前缀和 `vpn.example.invalid`，生产部署应通过环境变量或生产 VPS 上的受控源配置真实值。

VPS 状态备份脚本保存在 [`vps/scripts/backup-wireguard-state.sh`](vps/scripts/backup-wireguard-state.sh)。它备份 root-only 的 `wg0.conf`、road-warrior 登记表、运行状态和 Docker 部署源文件，不把备份内容复制回本地；部署时应将脚本通过受控 SSH 管理入口送入 `sudo -n sh -s` 执行，归档默认写入 `/var/backups/overlap-vpn`。公开文档不记录该入口的真实主机、用户名或项目路径。

供后续 agent 接管的敏感运行上下文保存在本地 `agent/handoff-overlap-lan-vpn.md`，该目录由 `.gitignore` 排除且仅 owner 可读；它记录远端主机、路径、地址规划、公钥和验证证据，不记录私钥、密码或 token。公开复现副本不需要这个目录。

## 版本控制与隐私边界

本目录的公开复现内容包括 `compose.yaml`、文档、路由器配置参考、`*.example` 模板和脚本；真实部署配置、客户端导出配置、WireGuard 私钥、road-warrior 登记表、`.env`、备份归档和 `agent/` 属于本机或 VPS 私有状态，不应提交。`.gitignore` 只提供默认防护，提交前仍应检查 `git diff --cached`；不要用 `git add -f` 绕过这些规则。

# prompt

下面按可直接交给 Codex Agent 的形式写。这里把之前的两个方案定义为：

* **方案 A：WireGuard + 重叠网段 1:1 Prefix NAT**
* **方案 B：方案 A + Split DNS，实现主机名层面的无感访问**

注意：这里 IPv4 不使用严格意义上的 NPTv6；实现时统一称 **1:1 Prefix NAT / subnet address translation**，避免 Codex 错用 IPv6 NPT 方案。

## Agent A：WireGuard + 重叠网段 1:1 NAT

```text
你是一名 Linux/OpenWrt 网络工程 Agent。

目标：
设计并实现一套基于 WireGuard 的 site-to-site VPN，使两个地址完全重叠的 IPv4 LAN 可以互相访问。

网络定义：

1. lan1：家庭网络
   - 实际网段：192.0.2.0/24
   - 默认网关：OpenWrt c
   - c LAN IP：192.0.2.1
   - c 可以主动访问公网
   - c 可以安装/配置 WireGuard、nftables、OpenWrt fw4

2. lan2：公司工位独立网络
   - 实际网段：192.0.2.0/24
   - 有一台可控的 Linux/OpenWrt 网关，称 lan2-gw
   - lan2-gw 可以访问公司网络 lan3，并经 lan3 访问公网
   - lan2-gw 可以主动连接公网 VPS
   - lan2-gw 可以运行 WireGuard 和 nftables
   - lan2 普通终端不得要求安装 WireGuard 客户端

3. VPS：
   - 有固定公网 IPv4
   - Linux
   - 作为 WireGuard Hub
   - WG 地址规划：
       VPS      = 10.90.0.1/24
       c        = 10.90.0.2/24
       lan2-gw  = 10.90.0.3/24

4. 两个真实 LAN 地址发生冲突：
       lan1 = 192.0.2.0/24
       lan2 = 192.0.2.0/24

因此禁止直接在 WireGuard 中同时路由两个 192.0.2.0/24。

采用以下虚拟地址空间：

       lan1 对其他站点暴露为：10.91.0.0/24
       lan2 对其他站点暴露为：10.92.0.0/24

必须保持 host 部分一致：

       lan1 192.0.2.3  <=> 10.91.0.3
       lan1 192.0.2.50 <=> 10.91.0.50

       lan2 192.0.2.3  <=> 10.92.0.3
       lan2 192.0.2.50 <=> 10.92.0.50

最终访问规则：

lan1 内：
    192.0.2.x = 本地 lan1
    10.92.0.x  = 远端 lan2

lan2 内：
    192.0.2.x = 本地 lan2
    10.91.0.x  = 远端 lan1

VPS：
    10.91.0.0/24 经 WireGuard 发给 c
    10.92.0.0/24 经 WireGuard 发给 lan2-gw

核心要求：

一、WireGuard

设计 hub-and-spoke：

                VPS
           10.90.0.1
              /     \
             /       \
            c       lan2-gw
      10.90.0.2   10.90.0.3

c 和 lan2-gw 均主动连接 VPS。

VPS 不需要直接知道真实的 192.0.2.0/24，只处理：

    10.91.0.0/24
    10.92.0.0/24

合理设置：
    AllowedIPs
    PersistentKeepalive
    IP forwarding
    MTU

禁止把 192.0.2.0/24 同时作为两个 peer 的 AllowedIPs。

二、地址转换

必须在站点边界实现双向、确定性的 1:1 IPv4 prefix translation。

例如 lan1 主机：

    192.0.2.20

访问：

    10.92.0.50

应最终抵达：

    lan2 192.0.2.50

且 lan2 侧目标主机看到的源地址必须属于：

    10.91.0.0/24

理想情况下看到：

    10.91.0.20

而不能看到：

    192.0.2.20

否则 lan2 主机会误认为源地址属于自己的本地 /24，并直接 ARP，导致回程失败。

反方向同理：

    lan2 192.0.2.30
          ->
    10.91.0.3
          ->
    lan1 192.0.2.3

lan1 主机看到来源应为：

    10.92.0.30

要求保留 host octet，实现：

    192.0.2.X <=> 10.91.0.X
    192.0.2.X <=> 10.92.0.X

不要简单使用随机 masquerade 破坏一一对应关系，除非经过分析确认某方向只能使用 SNAT。

优先使用 nftables。

如果 OpenWrt fw4 无法直接表达要求，可以：
1. 使用 /etc/nftables.d/ include；
2. 使用 hotplug 脚本；
3. 或生成受 fw4 生命周期管理影响最小的 nftables 自定义链。

禁止依赖已经淘汰的 iptables 防火墙体系，除非作为兼容性备选方案单独说明。

三、路由

必须解决：

lan1 普通设备访问 10.92.0.0/24 时知道下一跳是 c。

如果 c 本身就是 lan1 默认网关，则直接由 c 路由。

lan2 同理：
    10.91.0.0/24 必须交给 lan2-gw。

如果 lan2-gw 不是 lan2 默认网关，应明确给出以下两种实现的差异：
1. 在真正的 lan2 默认网关增加静态路由；
2. 在各终端增加静态路由。

优先设计“只修改网关、不修改终端”的模式。

四、安全

默认禁止 VPN 两侧无限制访问网关管理平面。

至少区分：
    WireGuard transit
    LAN forwarding
    router INPUT

要求：
    允许 lan1 -> lan2 translated subnet
    允许 lan2 -> lan1 translated subnet
    允许 ESTABLISHED,RELATED
    限制访问 VPS 本身不必要的端口
    WireGuard UDP 仅开放所需端口

不得因为实现 VPN 而关闭整个防火墙。

五、转发

Linux：
    net.ipv4.ip_forward=1

确认 rp_filter 不会破坏经过 NAT/WireGuard 的非对称或特殊路由。

只有确有需要时才修改 rp_filter，并说明原因。

六、VPS

VPS 原则上只负责：
    WireGuard hub
    IPv4 forwarding

尽可能不要在 VPS 上完成两个站点的 192.0.2.0/24 地址翻译。

地址翻译应该放在 c 与 lan2-gw，使 VPS 看到的始终是：
    10.91.0.0/24
    10.92.0.0/24

这样 VPS 路由表不存在重叠地址问题。

七、输出要求

先检查本机环境，不要直接修改系统。

需要识别：
    Linux 发行版
    是否 OpenWrt
    OpenWrt 版本
    fw4/nftables 版本
    WireGuard 是否已经安装
    当前接口名称
    当前路由表
    当前 nftables ruleset
    当前防火墙 zone
    当前 WireGuard 配置
    sysctl forwarding/rp_filter 状态

然后生成：

    docs/network/topology.md
    docs/network/address-plan.md
    docs/network/packet-flow.md
    docs/operations/rollback.md

    vps/examples/wg0.conf.example
    vps/examples/nftables.conf.example

    routers/home-openwrt/
        network.example
        firewall.example
        nftables.d/*.nft
        apply.sh
        rollback.sh

    routers/company-openwrt/
        wg0.conf.example
        nftables.conf.example
        sysctl.conf.example
        apply.sh
        rollback.sh

如果当前机器就是其中某个节点，可以额外生成适配当前系统的配置，但：

    默认只 dry-run。
    未明确指定 APPLY=1 时不得修改网络配置。
    不得重启网络。
    不得删除现有规则。
    不得覆盖原配置文件。

所有 apply 脚本执行前必须：
    备份现有配置
    检查 WireGuard peer 可达性
    检查 nftables 语法
    检查目标路由是否会覆盖默认路由
    检查是否存在地址冲突

八、验收测试

必须提供自动测试脚本或命令。

至少覆盖：

Test 1：
lan1 设备 ping 10.92.0.X
必须抵达 lan2 192.0.2.X。

Test 2：
lan2 设备 ping 10.91.0.X
必须抵达 lan1 192.0.2.X。

Test 3：
两边同时存在真实的：
    192.0.2.3
仍可以分别访问：
    本地 192.0.2.3
    远端 translated .3

Test 4：
tcpdump 验证 lan2 主机收到 lan1 数据包时：
    源地址不是 192.0.2.X
    而是 10.91.0.X

Test 5：
反方向：
    lan1 收到来源为 10.92.0.X

Test 6：
VPS 路由表中不得出现两个冲突的 192.0.2.0/24。

Test 7：
VPN 中断后：
    lan1 本地网络正常
    lan2 本地网络正常
    两侧互联网访问不受影响

Test 8：
恢复 VPN 后无需重启 LAN 终端即可重新互通。

九、必须解释关键数据包路径

至少画出：

LAN1 -> LAN2：

    192.0.2.20
      ->
    10.92.0.50
      ->
    c prefix translation
      ->
    WireGuard
      ->
    VPS
      ->
    WireGuard
      ->
    lan2-gw
      ->
    192.0.2.50

以及反向路径。

十、原则

这是 production 网络配置任务。

优先：
    可回滚
    幂等
    不破坏现有网络
    最少修改
    nftables 原生实现
    OpenWrt fw4 兼容
    配置可版本管理

不要直接假定 eth0、br-lan、wan 等接口名称。
必须检测后用变量表达。

所有私钥不得写入 Git。
example 配置只允许 placeholder。
```

## Agent B：WireGuard + 1:1 NAT + Split DNS

这个方案建立在 Agent A 之上，目的是进一步解决“人需要记 `10.201`、`10.202`”的问题。

```text
你是一名 Linux/OpenWrt 网络与 DNS 工程 Agent。

在已有的 WireGuard + overlapping subnet 1:1 NAT 网络基础上，增加 Split DNS，使用户访问设备时不需要关心当前位于 lan1、lan2 或 VPN 客户端网络。

基础网络：

真实网络：

    lan1 = 192.0.2.0/24
    lan2 = 192.0.2.0/24

VPN 映射：

    lan1 = 10.91.0.0/24
    lan2 = 10.92.0.0/24

WireGuard transit：

    VPS      10.90.0.1
    c        10.90.0.2
    lan2-gw  10.90.0.3

已有的数据面必须保持：

    lan1 -> lan2 使用 10.92.0.0/24
    lan2 -> lan1 使用 10.91.0.0/24

现在增加 DNS abstraction。

目标：

用户不应日常直接记忆：

    192.0.2.3
    10.91.0.3
    10.92.0.3

而是使用稳定名称，例如：

    storage.home.test
    hypervisor.home.test
    device01.site.test
    switch01.site.test

要求根据查询者所在网络返回不同 IP。

示例：

设备：
    storage.home.test
    lan1 实际地址 = 192.0.2.3
    VPN 映射地址 = 10.91.0.3

查询来源在 lan1：
    storage.home.test -> 192.0.2.3

查询来源在 lan2：
    storage.home.test -> 10.91.0.3

查询来源是远程 WireGuard road-warrior：
    storage.home.test -> 10.91.0.3

公司设备：

    device01.site.test
    lan2 实际地址 = 192.0.2.50
    VPN 映射地址 = 10.92.0.50

查询来源在 lan2：
    device01.site.test -> 192.0.2.50

查询来源在 lan1：
    device01.site.test -> 10.92.0.50

查询来源是远程 VPN：
    device01.site.test -> 10.92.0.50

设计目标：

用户无论使用：
    a1 家里 Linux
    a2 公司 Linux
    a3 出差 Linux

都尽可能使用：

    ssh storage.home.test
    https://hypervisor.home.test
    ssh device01.site.test

而不是根据位置切换 IP。

一、DNS 技术方案

优先评估：

    dnsmasq
    unbound

OpenWrt 原生优先使用 dnsmasq。

如果简单静态 hosts 无法根据来源网络返回不同结果，则实现 split-horizon DNS。

可以选择：

方案 1：
不同站点运行不同 DNS 视图。

例如：

lan1 DNS：

    storage.home.test -> 192.0.2.3
    hypervisor.home.test -> 192.0.2.X

    device01.site.test -> 10.92.0.50
    switch01.site.test -> 10.92.0.X

lan2 DNS：

    storage.home.test -> 10.91.0.3
    hypervisor.home.test -> 10.91.0.X

    device01.site.test -> 192.0.2.50
    switch01.site.test -> 192.0.2.X

远程 VPN DNS：

    *.home.test -> 10.91.0.X
    *.site.test -> 10.92.0.X

优先采用这种设计，因为简单、明确、容易排障。

不要求为了“智能 DNS”搭建过度复杂的中心 DNS。

二、域名规范

使用私有命名空间。

优先：

    home.test

公司自管设备可使用：

    site.test

如果 site.test 的标准或兼容性存在问题，则检查相关 RFC 后选择更合理的内部子域。

禁止使用：
    .local

因为 .local 通常用于 mDNS，会产生解析冲突。

不得劫持真实公网域名，除非该域名归用户所有。

建议允许将内部名称集中定义在一个 inventory 文件：

    inventory/hosts.yaml

例如：

    sites:
      lan1:
        real_prefix: 192.0.2.0/24
        translated_prefix: 10.91.0.0/24

      lan2:
        real_prefix: 192.0.2.0/24
        translated_prefix: 10.92.0.0/24

    hosts:
      nas:
        site: lan1
        address: 192.0.2.3
        dns: storage.home.test

      pve:
        site: lan1
        address: 192.0.2.3
        dns: hypervisor.home.test

      plc01:
        site: lan2
        address: 192.0.2.50
        dns: device01.site.test

注意：
示例中的具体设备/IP只作为说明，最终配置必须从用户 inventory 生成。

三、自动生成 translated IP

不要让用户重复维护：

    real IP
    translated IP

程序根据：

    site
    real address
    translated prefix

自动计算。

例如：

    site=lan1
    real=192.0.2.37
    translated prefix=10.91.0.0/24

自动得到：

    10.91.0.37

必须验证真实地址属于该 site 的 real_prefix。

四、DNS 配置生成

编写生成器，例如：

    tools/generate.py

输入：

    inventory/hosts.yaml

输出：

    generated/lan1/dnsmasq.conf
    generated/lan2/dnsmasq.conf
    generated/vpn/dnsmasq.conf

或者对应的 OpenWrt UCI batch 配置。

生成内容必须可重复执行并保持确定性。

五、a1/a2/a3

为 Linux 客户端设计 DNS 策略。

a1：
    位于 lan1 时优先使用 lan1 DNS。

a2：
    位于 lan2 时优先使用 lan2 DNS。

a3：
    连接个人 vpn2 后使用 VPN DNS。

如果主力 Linux 使用 systemd-resolved，应给出对应配置。

如果使用 NetworkManager，应给出：
    nmcli
或 connection profile 配置方式。

不要强制修改 /etc/resolv.conf，除非系统确实以静态 resolv.conf 工作。

六、WireGuard Road Warrior

为 a1/a2/a3 增加可选 WireGuard 客户端设计：

    aX -> VPS

客户端访问：

    10.91.0.0/24
    10.92.0.0/24

这样出差时：

    storage.home.test -> 10.91.0.3
    device01.site.test -> 10.92.0.50

允许同时访问两个站点。

Road-warrior 客户端本身不需要知道两个站点真实网络均为 192.0.2.0/24。

其 AllowedIPs 应只包含：
    VPN transit/管理地址
    10.91.0.0/24
    10.92.0.0/24

除非明确需要全隧道，否则不要加入：

    0.0.0.0/0

七、连接场景

必须分析以下场景：

1.
a1 位于 lan1：
    storage.home.test
        -> 192.0.2.3

2.
a1 位于 lan1：
    device01.site.test
        -> 10.92.0.50
        -> VPN
        -> lan2 192.0.2.50

3.
a2 位于 lan2：
    device01.site.test
        -> 192.0.2.50

4.
a2 位于 lan2：
    storage.home.test
        -> 10.91.0.3
        -> VPN
        -> lan1 192.0.2.3

5.
a3 出差：
    storage.home.test
        -> 10.91.0.3

    device01.site.test
        -> 10.92.0.50

6.
a1 在家但同时连接 vpn2：
    DNS 不能因为 VPN 优先级设置错误，而把本地 home.test 强制解析到不必要的远程路径。

应设计明确的 DNS routing domain / priority。

八、重要边界

DNS 只能隐藏地址差异，不能解决底层 overlapping subnet。

因此必须首先确保 Agent A 的：
    WireGuard
    routing
    prefix NAT
已经正确。

DNS 服务故障不应破坏：
    lan1 本地互联网
    lan2 本地互联网
    WireGuard 本身

只影响名称解析。

九、服务发现

不要假定跨站点 mDNS、SSDP、NetBIOS broadcast 会自动工作。

本项目主要解决：
    单播 IP
    DNS
    TCP/UDP 服务访问

以下服务另行处理：

    mDNS
    SSDP
    WS-Discovery
    NetBIOS broadcast
    DHCP broadcast

如果确有需要，只在文档中列出可选：
    avahi reflector
    mdns repeater

不要默认开启二层广播转发。

十、TLS

如果内部 Web 服务使用 HTTPS，DNS 名称稳定后应考虑证书问题。

不得关闭 TLS 验证作为长期解决方案。

如果用户拥有公网域名，可以额外设计：

    nas.home.example.com
    plc01.work.example.com

配合：
    DNS-01 ACME

但作为 optional，不要成为基本方案依赖。

十一、项目输出

生成：

    README.md

    inventory/
        sites.yaml
        hosts.yaml.example

    tools/
        generate_dns.py
        validate_inventory.py

    generated/
        lan1/
        lan2/
        vpn/

    openwrt/
        lan1/
        lan2/

    linux/
        systemd-resolved/
        NetworkManager/

    wireguard/
        road-warrior.conf.example

    tests/
        test_translation.py
        test_dns.sh
        test_routes.sh

    docs/
        dns-design.md
        name-resolution-matrix.md
        troubleshooting.md
        rollback.md

十二、验证

至少验证：

    dig @LAN1_DNS storage.home.test
        = 192.0.2.3

    dig @LAN2_DNS storage.home.test
        = 10.91.0.3

    dig @VPN_DNS storage.home.test
        = 10.91.0.3

    dig @LAN1_DNS device01.site.test
        = 10.92.0.50

    dig @LAN2_DNS device01.site.test
        = 192.0.2.50

    dig @VPN_DNS device01.site.test
        = 10.92.0.50

然后进行：

    ping
    ssh
    curl
    nc

验证 DNS 返回地址和实际数据路径一致。

十三、安全和变更策略

默认 dry-run。

任何修改：
    WireGuard
    nftables
    OpenWrt UCI
    dnsmasq
    systemd-resolved
    NetworkManager

都必须先生成 diff。

不得覆盖当前配置。

必须保存 rollback 文件。

DNS reload 前先验证配置语法。

网络修改前必须保留当前 SSH 会话的回退路径。

如果检测到当前就是远程 SSH 环境，禁止执行可能立即断开 SSH 的配置，除非显式设置：

    ALLOW_REMOTE_NETWORK_CHANGE=1

十四、最终目标

用户日常应能够做到：

在家：
    ssh storage.home.test
    ssh device01.site.test

在公司：
    ssh storage.home.test
    ssh device01.site.test

出差并连接 vpn2：
    ssh storage.home.test
    ssh device01.site.test

命令完全相同。

底层根据当前位置自动选择：
    本地真实地址
或
    VPN translated address

用户无需记住当前网络属于 lan1、lan2 还是外部网络。
```

### 推荐给 Codex 的执行顺序

```text
Phase 1
只做网络探测和现状报告，不修改系统。

Phase 2
实现 WireGuard Hub + 10.91.0.0/24 / 10.92.0.0/24 的路由骨架。

Phase 3
实现两侧 1:1 prefix NAT。

Phase 4
完成 ping/tcpdump 双向验收。

Phase 5
加入 inventory + Split DNS。

Phase 6
加入 a1/a2/a3 road-warrior WireGuard。

Phase 7
编写 apply/rollback 和故障恢复脚本。
```

其中 **Agent A 是网络基础设施本体，Agent B 不应独立重做网络层，而应直接以 Agent A 产出的配置和 inventory 为输入。**
