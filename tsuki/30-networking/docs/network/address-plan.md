# Address plan（公开演示）

状态：本文使用 `10.90`–`10.93` 演示数据面和 road-warrior 地址池；生产地址不从公开文档推导。

## 规划

| 网络 | 用途 | 地址 |
| --- | --- | --- |
| WG transit | VPS、c、g 的基础隧道地址 | `10.90.0.0/24` |
| 家庭 translated | lan1 对其他站点暴露的地址 | `10.91.0.0/24` |
| 公司 translated | lan2 对其他站点暴露的地址 | `10.92.0.0/24` |
| road-warrior | 出差客户端地址池 | `10.93.0.0/24` |

演示分配：

```text
VPS  = 10.90.0.1/24
c    = 10.90.0.2/24
g    = 10.90.0.3/24
a3   = 10.93.0.10/32
```

`10.90.0.0/24` 保持完整，不预先划分地址用途；目前只使用 VPS、c、g 的 `.1/.2/.3`。

road-warrior 地址从 `10.93.0.10/32` 起顺序分配；`.11`、`.12` 等留给后续设备。
一个设备一个 WireGuard peer、一个 `/32` 和一对独立密钥；地址不得在登记表中重复使用。

## Host-octet 映射

```text
lan1 192.0.2.X  <=>  10.91.0.X
lan2 192.0.2.X  <=>  10.92.0.X
```

例如：

```text
家庭 192.0.2.3  <=>  10.91.0.3
公司 192.0.2.3  <=>  10.92.0.3
```

两个逻辑 LAN 都以 `192.0.2.0/24` 作为文档示例；`10.91` 与 `10.92` 是站点边界上的虚拟身份，不是额外的二层 LAN。

## WireGuard peer 路由意图

| 节点 | 对端 | 该对端的 `AllowedIPs` 意图 |
| --- | --- | --- |
| VPS | c | `10.90.0.2/32`, `10.91.0.0/24` |
| VPS | g | `10.90.0.3/32`, `10.92.0.0/24` |
| VPS | a3 | `10.93.0.10/32` |
| c | VPS | `10.90.0.1/32`, `10.92.0.0/24`, `10.93.0.0/24` |
| g | VPS | `10.90.0.1/32`, `10.91.0.0/24`, `10.93.0.0/24` |
| a3 | VPS | `10.90.0.1/32`, `10.91.0.0/24`, `10.92.0.0/24` |

VPS 不直接路由任何真实的 `192.0.2.0/24`。

## 路由归属

- c 的本地 `192.0.2.0/24` 继续走家庭 LAN；`10.92.0.0/24` 交给 WG/VPS/g。
- g 的本地 `192.0.2.0/24` 继续走公司 LAN；`10.91.0.0/24` 交给 WG/VPS/c。
- VPS 只把 `10.91.0.0/24` 送给 c，把 `10.92.0.0/24` 送给 g，把每个 `10.93.0.X/32` 送给对应出差客户端。
- 出差客户端不加入 `0.0.0.0/0`，默认互联网仍走当地网络。

## WireGuard 端口

```text
VPS listen port = 51820/udp (demo; verify the deployed value with `wg show wg0 listen-port`)
```

TCP `51820` 可以继续开放，但 WireGuard 不使用 TCP。实际部署前仍需做 UDP 握手验证。

## 可验证的参考行为

- c/g 的 WireGuard 用户态工具、内核模块和原生服务可用；VPS 的 host-network Docker WireGuard 容器已构建并运行。
- c 的 fw3/legacy `NETMAP` 与 g 的 fw4/nft Prefix NAT 均已做语法及数据面验证。
- Compose 演示中的 UDP `51820`、peer handshake、translated 路由、外出客户端的双站点访问和客户端策略路由可按 `compose.yaml` 验证。

## 未完成

- Split DNS 尚未部署。

## Road-warrior 管理

- 客户端配置：`/etc/wireguard/<client>.conf`，默认不设为开机自动启动；需要时执行 `sudo wg-quick up <client>`。
- VPS peer 登记表：`/etc/overlap-vpn/road-warriors.tsv`，只保存名称、`/32` 和公钥。
- VPS 添加工具：`/usr/local/sbin/overlap-vpn-road-peer add <name> <address> <public-key>`。
- 客户端模板：`vps/examples/road-warrior.conf.example`。移动端或简单 Linux 客户端可保留 `AllowedIPs`，去掉 Linux 专用的 `Table/PostUp/PostDown`。
- road-warrior 默认只访问 `10.91.0.0/24`、`10.92.0.0/24` 和 VPS `10.90.0.1/32`，不使用 `0.0.0.0/0`，也不允许客户端之间默认互访。

新增设备的最小流程：

```sh
# 在新设备上生成并保管私钥，只把公钥交给 VPS
umask 077
wg genkey > client-privatekey
wg pubkey < client-privatekey

# 在 VPS 上分配下一个未占用地址，例如 10.93.0.11/32
sudo /usr/local/sbin/overlap-vpn-road-peer add client-name 10.93.0.11/32 <CLIENT_PUBLIC_KEY>
```

然后把 `vps/examples/road-warrior.conf.example` 中的地址、客户端私钥和 VPS 公钥填入新设备；私钥不上传 VPS，也不写入本项目。
