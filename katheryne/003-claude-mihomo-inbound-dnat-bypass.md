# mihomo TUN auto-route 劫持 WAN→Docker 入向连接的回包，用 CONNMARK 旁路修复并装入 compose 项目

- 领域标签：networking / iptables / docker-compose / proxy / debugging
- 难度：困难
- TL;DR：诊断出虚拟化宿主上 `MIHOMO-CONTAINER` 容器的 mihomo `auto-route` 把 Docker 容器响应 WAN 客户端的回包发往 `TUN-IFACE` TUN，导致 `EXAMPLE-SERVICE` 等 host-published 服务对外不可达；用 mangle 表 CONNMARK + `fwmark 0x100` + `ip rule pref 8500 lookup main` 旁路修复，并把整套规则封装为同 compose 项目下的 `BYPASS-SIDECAR` sidecar（Debian + iptables-legacy + SIGTERM trap 清理），生命周期跟随 `docker-compose up/down`。

## 2. 目标与起点

- **原始诉求**：用户反映虚拟化宿主上配置 mihomo 后主机自身可正常上网，但 host-published Docker 服务"无法正常响应外部连接"；后续要求把 fix"尽可能限制在单个项目里，确保通用可复用"。
- **已知约束**：
  - 目标主机：Proxmox VE / Debian 系虚拟化宿主，SSH 别名 `SSH-HOST`，登录用户 `USERNAME`（docker+sudo 组）。
  - 接入方式：用户从 `WAN-CLIENT-IP` 经路由器端口转发访问宿主，host-published 服务也走同样路径。
  - mihomo 在 docker 容器 `MIHOMO-CONTAINER`（`MIHOMO-IMAGE`）内，`network_mode: host` + `cap_add: NET_ADMIN/NET_RAW` + `/dev/net/tun`；compose 文件 `PROJECT-PATH/COMPOSE-FILE.yml`，配置 bind-mount `./config:/root/.config/mihomo`。
  - mihomo 配置：`auto-route: true`，`device: TUN-IFACE`（TUN-CIDR），`stack: mixed`，`route-exclude-address` 已含 `LAN-CIDR`、`EXCLUDED-CIDR`。
  - 多个 docker-compose 服务栈分布在 `DOCKER-BRIDGE-CIDR` 自定义 bridge 上。
  - `iptables-legacy` 是当前 alternative，`nftables` 链路空。
- **最初假设**：以为是 TPROXY/REDIRECT iptables 规则把 docker 端口劫持了——错。mihomo 实际仅用纯 TUN + 策略路由，iptables 全空。

## 3. 最终成果

- **交付物**：
  - `PROJECT-PATH/COMPOSE-FILE.yml` — 新增 `BYPASS-SIDECAR` 服务（原 mihomo 服务定义零改动，避免重建）。
  - `PROJECT-PATH/bypass/Dockerfile` — `debian:bookworm-slim` + `apt install iptables iproute2` + `update-alternatives --set iptables iptables-legacy`。
  - `PROJECT-PATH/bypass/apply.sh` — 启动时幂等下规则、`trap cleanup INT TERM` 在 SIGTERM 时拆除规则，最后 `while sleep 86400 & wait` 保活以让 trap 有机会触发。
  - 镜像 `BYPASS-IMAGE`、容器 `BYPASS-SIDECAR`，sidecar 间接通过 `network_mode: host` + `cap_add: NET_ADMIN` 操作宿主 netns。
  - 删除：宿主机 `/etc/systemd/system/mihomo-inbound-bypass.service`、`/usr/local/sbin/mihomo-inbound-bypass.sh`（旧的过渡方案，已不需要）。
  - 本地 agent memory：`AGENT-MEMORY-PATH` + `MEMORY.md` 索引。
- **验证方式与结果**：
  - `ip route get WAN-CLIENT-IP from CONTAINER-IP iif DOCKER-BRIDGE mark 0x100` → `via LAN-GATEWAY dev WAN-IFACE`（修复后）；同命令不带 `mark` 仍走 `TUN-IFACE`（容器主动出网走代理的能力被保留）。
  - 用户从 WAN 实测访问 `EXAMPLE-SERVICE` 成功。
  - `docker-compose stop BYPASS-SIDECAR` → trap 触发 → `iptables-legacy -t mangle -S PREROUTING` 与 `ip rule` 全部干净；`start` → 三条 mangle 规则 + 一条 ip rule 全部恢复。
- **与原始目标的差距**：无。诊断、修复、容器化封装、生命周期校验、宿主清理、记忆沉淀全部完成。

## 4. 关键决策与权衡

- **保留容器出网走 mihomo vs. 全部直连**：选了"保留代理 + CONNMARK 仅旁路入向"，否决了"`from DOCKER-BRIDGE-CIDR lookup main` 让所有容器直连"。
  - 原因：用户在 AskUserQuestion 中明确"Yes, keep proxying containers"。
  - 性质：偏好驱动。
- **持久化方式**：先临时用宿主机 systemd oneshot（`/usr/local/sbin/mihomo-inbound-bypass.sh`），后改为 compose 内 sidecar。
  - 原因：用户后续要求"限制在单个项目里、通用可复用"——sidecar 跟随项目移动，systemd 单元留在宿主机不可移植。
  - 性质：偏好驱动（用户主动追加约束）。
- **基础镜像 alpine vs. debian**：选 `debian:bookworm-slim`，否决 `alpine:3.19`。
  - 原因：alpine 的 `iptables` 只装 nft 变体；`iptables-legacy` 单装包不带 `libxt_CONNMARK` 用户态扩展，导致 `--restore-mark` 报 `unknown option`。debian 版本与宿主一致，`update-alternatives --set iptables iptables-legacy` 直接对齐。
  - 性质：事实驱动（实测 alpine `iptables-legacy` 不识别 `--restore-mark`）。
- **sidecar 重启策略**：`restart: unless-stopped` + 长驻 `sleep` 循环 + SIGTERM trap，否决 `restart: no` 一次性 oneshot。
  - 原因：要让 `docker-compose down` 触发清理 trap，恢复宿主 netns 干净。oneshot 无法在 down 时执行清理。
  - 性质：事实驱动。
- **fwmark 选择**：`0x100/0x100`（位 8）+ `ip rule pref 8500`（< mihomo 的 9002）。
  - 原因：mark 用单 bit 不与未来其它 mark 冲突，pref 必须早于 mihomo 的 9002 才能短路。
  - 性质：事实驱动。
- **不修改 mihomo 主服务定义**：sidecar 仅用 `depends_on: [MIHOMO-SERVICE]`，主服务 block 一字未动。
  - 原因：避免 `docker-compose up -d` 因 spec 变化把 mihomo 主服务也 recreate 一遍，造成上网中断。
  - 性质：事实驱动。

## 5. 踩坑记录

- **现象**：在 `/srv` 找 mihomo 配置文件，`ls /srv` 是空的，但 `/proc/<mihomo_pid>/cwd → /srv` 又能列出 `mihomo` 二进制和 caddy 文件。
  - 根因：mihomo 跑在 `MIHOMO-CONTAINER` 容器内，`/proc/<pid>/cwd` 解析的是容器 mount namespace 下的 `/srv`，宿主机 `/srv` 是真空。`docker top MIHOMO-CONTAINER` 才暴露容器内进程树，进而 `docker inspect MIHOMO-CONTAINER` 看到 `--network=host` 与 bind-mount 才定位真正配置 `PROJECT-PATH/config/config.yaml`。
  - 触发条件：进程是 `--network=host` 的容器化部署，但宿主 `ps -ef` 仍能看见进程（因为 PID 命名空间未隔离/无 `--pid=host` 但容器进程的宿主 PID 仍可见）。
  - 规避：碰到"宿主能看见进程但宿主文件系统找不到配置"，先 `docker ps`、`docker top <container>`、`docker inspect <container> --format '{{.HostConfig.NetworkMode}}'` 确认是不是容器化的，再读 bind-mount。

- **现象**：`alpine:3.19` + `apk add iptables-legacy` 后，sidecar 容器 restart loop，日志反复 `iptables v1.8.10 (legacy): unknown option "--restore-mark"`。
  - 根因：alpine 的 `iptables-legacy` 包只装 `xtables-legacy-multi` 二进制和 legacy 符号链接，**不包含 `libxt_CONNMARK.so` 用户态扩展**；扩展由完整的 `iptables` 包提供（但那个包又只有 nft 默认）。错误把"target/option 未识别"看成是 kernel 模块缺失，但其实是用户态共享库没有被装出来。
  - 触发条件：在 alpine 上需要 iptables 高级 target（CONNMARK/MARK/TPROXY 的 `--restore-mark`/`--save-mark`/`--mask` 选项）时。
  - 规避：要么换 debian/ubuntu 系（包结构完整），要么在 alpine 显式同时 `apk add iptables iptables-legacy` 并验证 `iptables-legacy -j CONNMARK -h` 是否打印 mask 相关帮助。

- **现象**：第一次写 alpine Dockerfile 时 `apply.sh` 直接 `IPT="iptables-legacy"`，报 `iptables-legacy: not found`。
  - 根因：alpine 的 `iptables` 包默认只安装 nft 变体，没有 `iptables-legacy` 这个名字的可执行；需要单独装 `iptables-legacy` 包才出现该名字。
  - 触发条件：跨发行版假设二进制名字相同。
  - 规避：脚本里用 `command -v iptables-legacy || command -v iptables` 探测；或在镜像里 `update-alternatives --set` 把 `iptables` 显式指向 legacy，脚本直接调 `iptables`。

- **现象**：第一次"测试 cleanup"时显示 `STILL PRESENT (bad)`。
  - 根因：那时宿主 systemd unit 仍 enable+running（持久化的过渡方案），每次 cleanup 后实际 trap 没运行（sidecar 因 iptables 错误已挂在 restart loop 里），看到的"残留规则"其实是 systemd unit 装的。
  - 触发条件：临时方案与最终方案并存测试时容易误判生效来源。
  - 规避：测试新机制前，先把旧机制 disable（不删，留作回退），证明新机制能独立生效，再清理旧文件。

- **现象**：`docker compose -f COMPOSE-FILE.yml up -d` 报 docker 帮助。
  - 根因：宿主机只装了 `docker-compose` v1.29（独立二进制），未装 `docker compose` v2 plugin。
  - 触发条件：默认 Debian apt 仓库或老版 docker。
  - 规避：先 `command -v docker-compose docker; docker compose version 2>&1 || docker-compose --version`，再决定语法。

- **现象**：`sysctl: command not found`、`conntrack: 找不到命令`。
  - 根因：非交互 SSH 进来 PATH 不含 `/sbin`、`/usr/sbin`，且 `conntrack-tools` 包未装（只有 `libnetfilter-conntrack3`）。
  - 触发条件：远程 `ssh host '<cmd>'` 形式跑系统管理命令时。
  - 规避：直接读 `/proc/sys/net/ipv4/...`、`/proc/net/nf_conntrack`，不依赖管理工具。

- **现象**：`docker inspect EXAMPLE-SERVICE --format "...{{range $k,$v := ...}}..."` 报 `template parsing error: template: :1: unexpected "," in range`。
  - 根因：双引号被 shell 吞掉了，template 里的 `$k,$v` 在 zsh 下被解析成位置参数。
  - 触发条件：Go template 写在 zsh 里又有 `$`、`,`、`{}`。
  - 规避：用 `--format '{{json .NetworkSettings.Networks}}'` 输出原始 JSON 自己解析，省心。

## 6. 可复用经验

- **诊断"上代理后入向 Docker 服务断"的固定套路**
  - 内容：
    ```
    1) ip rule show; ip route show table all; ip route show table <代理表>
    2) iptables-legacy -t mangle -S PREROUTING / nft list ruleset    # 排除 TPROXY/REDIRECT
    3) ip route get <client_ip> from <docker_container_ip> iif <docker_bridge>
       # 这一步直接显示回包走哪个出接口，是定位"代理吞回包"的银弹
    4) 同样 ip route get 但加 mark 0x?，验证 fwmark 旁路是否生效
    ```
  - 适用：任何 TUN 模式（mihomo / sing-box / clash-meta / xray TUN）配 `auto-route` 后，Docker host-published 服务从外部不通。
  - 反例：纯 TPROXY/REDIRECT 模式（rule/iptables 介入）时 `ip route get` 看不到完整真相，需要配合 `iptables -nvL -t mangle/nat` 看 hit 计数。

- **CONNMARK 入向旁路三件套（`iptables-legacy`）**
  - 内容：
    ```bash
    iptables -t mangle -I PREROUTING 1 -j CONNMARK --restore-mark --nfmask 0x100 --ctmask 0x100
    iptables -t mangle -A PREROUTING -i <wan_iface> -m conntrack --ctstate NEW -m addrtype ! --src-type LOCAL -j MARK --set-xmark 0x100/0x100
    iptables -t mangle -A PREROUTING -i <wan_iface> -m conntrack --ctstate NEW -m addrtype ! --src-type LOCAL -j CONNMARK --save-mark --nfmask 0x100 --ctmask 0x100
    ip rule add pref 8500 fwmark 0x100/0x100 lookup main
    ```
  - 适用：代理 TUN auto-route 把所有非 lo ingress 推进代理表，但需要保留代理出网能力的场景。
  - 反例：如果代理本身用 fwmark 路由（如 sing-box `tproxy_mark`），需要避开冲突的位段；选 `0x100` 是因为大多数代理默认用 `0x6669`/`0x80ff` 等，互不重叠。

- **想让 sidecar 用 `docker-compose down` 触发清理**
  - 内容：
    ```bash
    trap cleanup INT TERM
    apply
    while :; do sleep 86400 & wait $!; done   # 必须 & + wait，否则 sleep 不响应信号
    ```
  - 适用：oneshot 性质的 sidecar 想要 down 时回滚宿主状态。
  - 反例：用 `restart: no` + `exit 0` 退出，trap 在前台 sleep 时收不到 SIGTERM，down 时不会跑清理。

- **bake-in iptables 变体匹配宿主**
  - 内容：debian 系 sidecar 镜像里加：
    ```dockerfile
    RUN apt-get install -y iptables iproute2 \
     && update-alternatives --set iptables /usr/sbin/iptables-legacy
    ```
  - 适用：宿主用 legacy（`update-alternatives --display iptables` 确认），需要容器写入同一张表才能被宿主 `iptables -S` 看到。
  - 反例：宿主已用 nft（`iptables-nft`），别强切 legacy，否则双写两套表混乱。

- **不重建主服务的扩容方式**
  - 内容：在 compose 里只新增独立 service 块，不动既有 service 的 spec，再 `docker-compose up -d <new_service>` 仅创建新容器。`depends_on` 只引向已有服务即可。
  - 适用：给运行中、不能中断的服务（代理/数据库）加 sidecar。
  - 反例：在已有 service 的 spec 上加任何字段（label/depends_on/env）都会触发 recreate，要么手动 `docker-compose up -d --no-recreate`、要么接受短暂中断。

## 7. 环境上下文

- 宿主：Proxmox VE / Debian 系虚拟化宿主，kernel `KERNEL-VERSION`。
- iptables：`iptables-legacy`（`update-alternatives --display iptables` 显示当前指向 `/usr/sbin/iptables-legacy`），nftables 链路空。
- docker：仅装了 `docker-compose` v1.29.2，**没有 `docker compose` v2 plugin**。
- mihomo：`MIHOMO-IMAGE`（自构建）镜像内 `/srv/mihomo`，TUN device `TUN-IFACE`，`stack: mixed`，`auto-route: true`，`route-exclude-address` 已含 `LAN-CIDR` 与 `EXCLUDED-CIDR`。
- 网络拓扑：`WAN-IFACE` 是唯一对 LAN/WAN 的接口（`LAN-IP/LAN-CIDR`），路由器在 `LAN-GATEWAY`，WAN 端口转发到宿主；众多 docker bridge 在 `DOCKER-BRIDGE-CIDR`。
- alpine 3.19 的 `iptables` 包只含 nft 变体；`iptables-legacy` 包不含 `libxt_CONNMARK.so`——本次切到 debian 镜像就是因为这个。
- 非交互 SSH 不读 `/etc/profile`，PATH 不含 `/sbin`、`/usr/sbin`，要么 `sudo`、要么走 `/proc`。

## 8. 未尽事项

- **TODO**：无显式遗留。
- **已知限制**：
  - sidecar 的 mark 选 `0x100/0x100`，未与宿主已有 mark 做协商。当前宿主无其它 mark 使用方，未来若引入 sing-box / wireguard 等也用 fwmark 的工具，需检查位段冲突。
  - `apply.sh` 的清理路径 `iptables ... -D ...` 串行删 3 条 + 1 条 ip rule，假设格式与 `apply` 时完全一致；若中途有外部修改导致 `-C` 命中而 `-D` 失败，会留少量残规则——风险低但未做幂等校验。
  - sidecar `apply.sh` 等待 `TUN-IFACE` 60s 超时后会"无论如何 apply"——如果用户禁用了 mihomo 但仍启了 sidecar，会留下无意义但无害的规则。
- **故意延后**：
  - **未做 IPv6 旁路**：mihomo 配置 `ipv6: false` + 宿主 IPv6 ip rule 链路非常简单（只有 0/local 与 32766/main），现状 IPv6 入向不会被代理劫持。如果未来开启 IPv6 代理，需要镜像安装 `ip6tables` 并加同构 ip6tables 规则——本次因无对应症状，没做。
  - **未把 mark/pref 抽成更通用模板**：当前环境变量只暴露了 `WAN_IFACE/TUN_IFACE/MARK/RULE_PREF`。`addrtype ! --src-type LOCAL` 的判定写死，跨宿主迁移到有多接入接口的环境时需要手动改条件——但当前需求"单机+单 WAN 接口"已覆盖，没做泛化。

## 9. 后续行动

- **加入第二个走 fwmark 的工具时，重新评估位段**
  - 触发条件：用户在宿主上引入新的 TUN/代理（sing-box、wireguard、ZeroTier 等），或注意到 `iptables -t mangle -L -nv` 出现 0x100 之外的 MARK 规则。
  - 预期影响：如果有冲突，`MARK --set-xmark` 会覆盖既有位；改用与新工具不同的位（如 `0x200`）即可。
- **若 host-published 服务偶发"突然不通"**
  - 触发条件：用户报告 `EXAMPLE-SERVICE` 等任一 host-published docker 服务对外不通，且当时 mihomo 仍在工作。
  - 预期影响：`docker ps | grep BYPASS-SIDECAR` 检查 sidecar 是否在跑；若挂了 `docker-compose -f PROJECT-PATH/COMPOSE-FILE.yml up -d` 重新拉起即可恢复。
- **mihomo 升级或换分发后**
  - 触发条件：用户重建 `MIHOMO-IMAGE` 或换底镜像。
  - 预期影响：需验证新版本的 `auto-route` 仍创建预期的 `TUN-IFACE` + 同样的 ip rule 优先级（不同分发可能换 device 名/pref），若改了，调整 sidecar `TUN_IFACE` env 与 `RULE_PREF` 即可。
