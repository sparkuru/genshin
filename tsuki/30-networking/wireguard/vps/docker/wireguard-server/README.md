# VPS WireGuard Docker runtime

这个目录是重叠 LAN VPN 的公开 Docker 运行时模板。它展示 host-network、peer 管理和 Prefix NAT 的边界；默认地址、endpoint 和密钥均为演示值，不代表任何生产部署：

- VPS：`10.90.0.1/24`，WireGuard 监听端口以运行中的 `wg0` 为准
- c：`10.90.0.2`，负责 `10.91.0.0/24` 家庭 translated 前缀
- g：`10.90.0.3`，负责 `10.92.0.0/24` 公司 translated 前缀
- road-warrior：`10.93.0.0/24`，示例外出设备使用 `.10/32`

## 为什么使用 host network

WireGuard 是 VPS 的三层路由数据面，不是普通 Web 应用。容器使用 host network 后：

- `wg0`、kernel route 和 `PostUp/PostDown` 的 iptables 规则仍在 VPS 宿主机网络命名空间；
- 云防火墙/安全组只需允许示例 UDP `51820`；Compose 不使用 `ports`；
- c、g、a3 的 endpoint、AllowedIPs、Prefix NAT 和返回路由无需改变；
- 其他 VPS 服务可以继续直接访问 VPN 路由；
- Docker 只负责 WireGuard 工具、入口进程和启动恢复。

容器需要 `NET_ADMIN`；`SYS_MODULE` 和 `/lib/modules` 用于让容器使用 VPS 内核的 WireGuard 模块。VPS 已有 `ip_forward=1` 和适合本方案的 `rp_filter` 设置，Compose 不在容器内重复接管这些宿主机级参数。

## 秘密和状态边界

生产配置不放在这个项目目录中。Compose 只挂载 VPS 上的：

- `/etc/wireguard`：root-only 的 `wg0.conf` 和 VPS 私钥；
- `/etc/overlap-vpn`：road-warrior 登记表；
- `/lib/modules`：只读内核模块目录。

`wg0.conf.example` 只有占位符。不要把真实 `wg0.conf`、客户端私钥或 peer 登记表复制回项目目录。

`wireguard-server.yml` 默认把客户端签发脚本指向 `vpn.example.invalid` 和 `10.90`–`10.93` 演示前缀。生产部署必须通过环境变量提供真实 endpoint 与地址规划，或使用目标机上已审查的生产配置；生产值不应写回公开仓库。

## 构建和运行

先确认原生服务已停止，再启动容器；不要让 systemd 和容器同时拥有 `wg0`：

```sh
./manage.sh validate
./manage.sh build
sudo systemctl stop wg-quick@wg0
sudo systemctl disable wg-quick@wg0
./manage.sh up
./manage.sh status
```

容器启动后，应该看到：

- `wg0` 地址 `10.90.0.1/24`；
- UDP `51820` 监听；
- `10.91.0.0/24`、`10.92.0.0/24` 和每个 road-warrior `/32` 路由；
- c/g/a3 peer handshake 恢复。

常用命令：

```sh
./manage.sh status
./manage.sh logs
./manage.sh road-list
./manage.sh road-add client-name 10.93.0.11/32 <CLIENT_PUBLIC_KEY>
umask 077
./manage.sh road-issue client-name > client-name.conf
./manage.sh road-issue laptop 10.93.0.12/32 --linux > laptop.conf
./manage.sh road-revoke client-name
./manage.sh road-revoke 10.93.0.12/32
```

`road-list` 输出当前登记的名称、地址和公钥。`road-issue` 在 VPS 内生成客户端密钥，默认自动选择下一个空闲地址，也可指定地址；名称或地址冲突时会退出。客户端配置从标准输出返回，私钥不会写入登记表或项目目录；Endpoint 端口从当前 `wg0` 自动读取。

`road-issue --linux` 会额外加入当前 a1 所需的 `table 2023` 策略路由；手机或普通客户端使用默认配置。`road-revoke` 接受 peer 名称或 `/32` 地址，会同时删除活动 peer、返回路由、`wg0.conf` 和登记表。

所有新增、签发和吊销操作都使用同一个运行时锁，并在 `/tmp/overlap-vpn-road-peer.*` 留下 owner-only 回滚备份。`road-add` 仍保留为手工提供已有客户端公钥的低级入口。

## 回滚

若容器验证失败：

```sh
./manage.sh down
sudo systemctl enable --now wg-quick@wg0
sudo systemctl is-active wg-quick@wg0
```

回滚不需要修改 c、g 或 a1。切换前还应保存 `/etc/wireguard/wg0.conf` 和 `/etc/overlap-vpn/road-warriors.tsv` 的备份。

## 与旧项目的关系

此前的自动生成 WireGuard 项目、地址池和 MASQUERADE 规则属于另一套旧 VPN。当前模板使用手工配置和自定义 road-warrior 工具，不能把旧项目的状态目录直接作为生产状态。
