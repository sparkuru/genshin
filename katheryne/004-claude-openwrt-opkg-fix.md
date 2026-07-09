# 修复 ImmortalWrt 路由器 opkg 源并安装 tcpdump

- 领域标签：infra / openwrt / networking
- 难度：中等
- TL;DR：`opkg update` 全部报 HTTP 404/8，根因是固件实为 ImmortalWrt R24.1.1 而非标准 OpenWrt，且腾讯镜像不含 SNAPSHOT 包；切换至 ImmortalWrt 23.05.4 官方源后，`opkg update` 全部成功，tcpdump 4.99.4 装好可用。

## 2. 目标与起点

- **原始诉求**：SSH 进 `root@ROUTER-IP`，执行 `opkg update`，然后 `opkg install tcpdump`
- **已知约束**：仅提供主机地址，无需额外认证（root 免密直连）
- **最初假设**：这是标准 OpenWrt 路由器，opkg 源配好了、网络通，只需跑两条命令

## 3. 最终成果

- **交付物**：
  - `/etc/opkg/distfeeds.conf`：已替换为 ImmortalWrt 23.05.4 官方源（原文件备份在 `/etc/opkg/distfeeds.conf.bak`）
  - `tcpdump 4.99.4` + `libpcap 1.10.4` 安装到系统
- **验证方式与结果**：`tcpdump --version` 输出 `tcpdump version 4.99.4 / libpcap version 1.10.4 (with TPACKET_V3)`，验证通过
- **与原始目标的差距**：无；顺带修复了原本损坏的包源配置

## 4. 关键决策与权衡

- **选用哪个包源替代腾讯镜像**：选了 ImmortalWrt 官方 `downloads.immortalwrt.org/releases/23.05.4`，否决了官方 OpenWrt `downloads.openwrt.org/snapshots`（该路径已迁移到 .apk 格式，本机 opkg 只支持 .ipk）以及 USTC 镜像（`/openwrt/snapshots/` 路径对 aarch64_cortex-a53 返回 exit=4）。
  - 原因：23.05.4 base 包含 `Packages.gz`（ipk 格式）且包含 tcpdump 4.99.4，路径可访问
  - 性质：事实驱动

- **保留还是删除 helloworld feed**：新 distfeeds.conf 未保留原 `helloworld` 源（该源在腾讯镜像上同样不可用）
  - 原因：没有对应可访问的 ImmortalWrt 版本 helloworld feed，不强行填充
  - 性质：事实驱动

- **用 23.05.4 而不是 24.10.x**：内核编译时间 2023-12-09 与 23.05.x 发布周期吻合；R24.1.1 命名虽含"24"但是固件自定义版本号，不对应 ImmortalWrt 24.10
  - 原因：时间吻合 + 实测 23.05.4 包可下载安装无报错
  - 性质：事实驱动（但有不确定性，见未尽事项）

## 5. 踩坑记录

- **现象**：`opkg update` 全部失败，错误 "wget returned 8"（HTTP 服务端错误），唯独 luci 一条成功
- **根因**：腾讯镜像（`mirrors.cloud.tencent.com/lede/snapshots/`）不含 SNAPSHOT 固件对应的包列表；luci 成功是因为它指向 `lede/releases/18.06.9`（releases 路径存在）。固件是 ImmortalWrt 私有构建而非官方 OpenWrt，distfeeds.conf 源从一开始就是错的
- **触发条件**：任何使用预装腾讯源但固件为 ImmortalWrt SNAPSHOT 构建的路由器重装或首次配置
- **规避**：拿到设备后先看 `DISTRIB_REVISION`，若含 `R2x.x.x` 格式则为 ImmortalWrt，应去 `downloads.immortalwrt.org/releases/` 找对应版本源

---

- **现象**：尝试官方 OpenWrt snapshot 源也失败（exit=8 / HTTP 404）
- **根因**：OpenWrt snapshots 在 2024 年前后已迁移至 APK 包格式（目录内只有 `.apk` 文件），不再提供 `Packages.gz`（ipk）；而本机只有 opkg，无法处理 apk
- **触发条件**：任何用 opkg 访问官方 OpenWrt snapshots 最新路径的操作
- **规避**：检查目录是否只含 `.apk`；如果是，只能用 releases 路径或换 apk 包管理器

## 6. 可复用经验

- **判断固件是否为 ImmortalWrt**
  - 内容：`cat /etc/openwrt_release | grep REVISION`，若输出格式为 `R2x.x.x`（如 R24.1.1）则为 ImmortalWrt
  - 适用：任何需要选包源的 OpenWrt-based 路由器
  - 反例：官方 OpenWrt 的 REVISION 格式为 `r12345-xxxxxxx`，不适用此规则

- **临时验证某 opkg 源里是否含目标包**
  - 内容：
    ```bash
    wget -q -O /tmp/pkglist.gz "<源URL>/Packages.gz" && \
    zcat /tmp/pkglist.gz | grep -A3 "^Package: <包名>" && \
    rm -f /tmp/pkglist.gz
    ```
  - 适用：修改 distfeeds.conf 前先确认包和版本存在，避免白改
  - 反例：包存在不代表依赖在同源可满足，安装时仍需观察依赖报错

- **ImmortalWrt 23.05.4 标准包源配置（aarch64_cortex-a53 / mediatek/filogic）**
  - 内容：
    ```
    src/gz immortalwrt_core https://downloads.immortalwrt.org/releases/23.05.4/targets/mediatek/filogic/packages
    src/gz immortalwrt_base https://downloads.immortalwrt.org/releases/23.05.4/packages/aarch64_cortex-a53/base
    src/gz immortalwrt_luci https://downloads.immortalwrt.org/releases/23.05.4/packages/aarch64_cortex-a53/luci
    src/gz immortalwrt_packages https://downloads.immortalwrt.org/releases/23.05.4/packages/aarch64_cortex-a53/packages
    src/gz immortalwrt_routing https://downloads.immortalwrt.org/releases/23.05.4/packages/aarch64_cortex-a53/routing
    src/gz immortalwrt_telephony https://downloads.immortalwrt.org/releases/23.05.4/packages/aarch64_cortex-a53/telephony
    ```
  - 适用：ImmortalWrt R24.x.x 基于 23.05 分支的固件，目标 mediatek/filogic
  - 反例：若固件是 ImmortalWrt 24.10.x 或 25.12.x 构建，需换对应 release 路径；24.10+ 的某些包与 23.05 ABI 不兼容

- **探测路由器外网可达性**
  - 内容：`wget -q --spider --timeout=8 <URL> 2>&1; echo "exit=$?"`，exit=0 表示可达，exit=8 表示 HTTP 服务端错误（404/403），exit=4 表示网络不通
  - 适用：ssh 进路由器后快速验证某个镜像源路径是否存在且可达
  - 反例：exit=0 只代表 HTTP HEAD 成功，不等于 Packages.gz 内容格式正确

## 7. 环境上下文

- 路由器：`root@ROUTER-IP`，aarch64 GNU/Linux
- 内核：5.15.138，编译于 2023-12-09
- 固件：ImmortalWrt SNAPSHOT R24.1.1，目标平台 `mediatek/filogic`（MT7986 Filogic 系列）
- 包管理器：opkg（ipk 格式），无 apk
- /overlay 可用空间：59.6 MB（足够常规包安装）
- 外网访问：可直连 `downloads.immortalwrt.org`、`downloads.openwrt.org`；USTC 镜像的 openwrt snapshots 路径不可用（exit=4）

## 8. 未尽事项

- **TODO**：无
- **已知限制**：23.05.4 包源与 R24.1.1 固件的 ABI 兼容性未系统验证，tcpdump 这次正常安装，但复杂包（如带 Lua 扩展的）可能出现库版本冲突
- **故意延后**：未恢复/配置 `helloworld` 第三方包源，因为没有可用的对应镜像路径；如有需要应单独查 ImmortalWrt 社区对应版本的 helloworld feed URL

## 9. 后续行动

- **确认 23.05.4 与 R24.1.1 的版本对应关系**
  - 触发条件：下次需要安装与系统库深度耦合的包（如 kmod-*、带 openssl 依赖的包）时，出现 `satisfies dependencies` 失败
  - 预期影响：如果不匹配，需切换至正确的 ImmortalWrt 版本源（24.10.x）
- **补充 helloworld / 代理相关包源**
  - 触发条件：需要在路由器上安装 mihomo、sing-box 等代理软件时
  - 预期影响：需手动找 ImmortalWrt R24.x.x 对应的第三方 feed URL 并写入 customfeeds.conf
