
注意到 wireguard 也是一种 vpn, 肯定得拿出来和 openvpn 进行对比

## openvpn

架构

```mermaid


```


## wireguard

wireguard 主要基于 udp 实现, 

```mermaid


```

```bash
$ sudo apt update

$ sudo apt install -y wireguard resolvconf

$ sudo mkdir -p /etc/wireguard

$ sudo cp ./config/peer1/peer1.conf /etc/wireguard/wg0.conf

$ echo 'nameserver 8.8.8.8' > /etc/resolvconf/resolv.conf.d/base

$ sudo wg-quick up wg0

$ sudo resolvconf -u

```

### 网段冲突问题

注意在 wireguard-server 中, 配置 ALLOWEDIPS 为 10.192.9.0/24, 否则会出现: 客户端启动了 wg 后, ssh 流量进 wg 隧道 -> 隧道要连 vps -> 流量又进隧道 的死循环

有两种方式解决 "只想特定 ip 段走 wireguard 隧道" 的问题:

1. 在 wireguard-server 中, 配置 ALLOWEDIPS 为 10.192.9.0/24, 这样只有 10.192.9.0/24 的流量会走 wireguard 隧道
2. 在 wireguard-server 中, 配置 ALLOWEDIPS 为 0.0.0.0/0, 这样所有流量都会走 wireguard 隧道

但是第一种方式会导致其他 ip 段无法上网, 第二种方式会导致所有流量都会走 wireguard 隧道, 这样会导致性能问题

既需要保证特定 ip 段走 wireguard 隧道, 又需要保证其他 ip 段上网

### 路由问题

在 wireguard-server 生成的 peer 配置文件中, 需要 /32 来精确确定 peer 的 ip

但在客户端的 peer 配置文件中, 往往需要指定例如 /24 来表示同网段

即分发 peer.conf 配置文件时, 在 ip 后边加一个 /24 即可

## refer

1. https://www.cnblogs.com/ryanyangcs/p/14462269.html
2. 