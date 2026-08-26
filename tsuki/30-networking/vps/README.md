# WireGuard road-warrior 签发包

这个目录是公开的 VPS 签发参考，不包含 VPS、示例外出设备或任何客户端私钥。真实 VPS 状态应留在目标机的 owner-only 路径；公开副本中的地址、endpoint 和路径均不是生产事实：

- Docker 项目：由部署环境的 `WIREGUARD_PROJECT_DIR` 指定（示例：`/opt/wireguard-server`）
- 工具：容器内 `/usr/local/sbin/overlap-vpn-road-peer`；宿主机仍保留同路径的回滚/兼容工具
- WireGuard 配置：`/etc/wireguard/wg0.conf`（root-only，不复制到这里）
- peer 登记表：`/etc/overlap-vpn/road-warriors.tsv`

## 签发原理

WireGuard 没有 CA 式的“签名证书”。签发一个设备就是：

1. 在 VPS 内生成独立私钥和公钥。
2. 在 VPS 登记设备公钥与一个未占用的 `10.93.0.X/32`。
3. 由 VPS 输出完整客户端配置，用户通过 SSH 重定向或安全文件传输取得。

VPS 被视为可信签发源，但客户端私钥只在签发期间位于 VPS 的 owner-only 临时目录；命令结束后会删除。VPS 的 peer 登记表仍只保存公钥、地址和名称。

## 新设备签发

Docker 运行时的签发命令如下。默认自动选择下一个未占用的演示地址：

```sh
umask 077
WIREGUARD_PROJECT_DIR=${WIREGUARD_PROJECT_DIR:-/opt/wireguard-server}
cd "$WIREGUARD_PROJECT_DIR"
./manage.sh road-issue client-name > client-name.conf
chmod 600 client-name.conf
```

`client-name.conf` 的标准输出只有客户端配置；签发状态和回滚备份路径写到标准错误。配置包含客户端私钥，不要提交 Git 或粘贴到聊天记录。

签发前查询已经分配的地址：

```sh
./manage.sh road-list
```

也可以指定地址；如果名称或地址已存在，命令会报错并退出，不会生成或登记新 peer：

```sh
./manage.sh road-issue client-name 10.93.0.11/32 > client-name.conf
```

如果客户端是需要当前 a1 策略路由的 Linux 主机，加 `--linux`：

```sh
./manage.sh road-issue laptop 10.93.0.12/32 --linux > laptop.conf
```

旧的低级手工入口仍可用，但不负责生成客户端私钥：

```sh
./manage.sh road-add client-name 10.93.0.11/32 <CLIENT_PUBLIC_KEY>
```

## 查询和吊销

```sh
./manage.sh road-list
./manage.sh road-revoke client-name
./manage.sh road-revoke 10.93.0.11/32
```

`road-revoke` 会同时删除活动 peer、VPS `/32` 返回路由、`wg0.conf` 和登记表，并留下回滚备份路径。吊销后客户端配置和私钥应一并删除。

公开模板默认使用 `10.90`–`10.93` 演示前缀和 `vpn.example.invalid`。生产部署时，在受控环境中设置 `OVERLAP_VPN_ENDPOINT_HOST`、`OVERLAP_VPN_WG_HUB_ADDRESS`、`OVERLAP_VPN_HOME_TRANSLATED_CIDR`、`OVERLAP_VPN_COMPANY_TRANSLATED_CIDR`、`OVERLAP_VPN_ROAD_WARRIOR_PREFIX`，或直接使用目标机上已审查的生产配置；不要把生产值回填到公开副本。

## 客户端配置

`road-issue` 已自动填入客户端地址、私钥、VPS 公钥、当前 `wg0` 监听端口、Endpoint 和 `AllowedIPs`；不需要再手工替换模板。监听端口以 `wg show wg0 listen-port` 为准。

默认输出为通用/移动端配置。Linux 主机如需现有 TUN/代理专用策略路由，使用上面的 `--linux`；手机或普通客户端使用默认配置。

所有配置默认只访问：

```text
AllowedIPs = 10.90.0.1/32, 10.91.0.0/24, 10.92.0.0/24
```

不要填写 `0.0.0.0/0`，除非明确要做全隧道。

## a3 特殊说明

某台 Linux 客户端若需要专用策略路由，可在自己的 root-only WireGuard 配置中使用 `--linux` 输出；不要用公开模板覆盖已有生产配置。启用时：

```sh
sudo wg-quick up <CLIENT_INTERFACE>
```
