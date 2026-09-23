---
title: "Virtual Private Network"
description: "VPN, WireGuard, OpenVPN, and proxy networking notes."
date: "2026-07-03T10:58:34+08:00"
tags: []
draft: false
layout: "post"
slug: "baacharu-puraibeeto-nettowaaku"
---

# baacharu puraibeeto nettowaaku

## openvpn

注意到 wireguard 也是一种 vpn, 肯定得拿出来和 openvpn 进行对比

架构如下

```mermaid


```


## wireguard

wireguard 主要基于 udp 实现, 

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

注意在 wireguard-server 中, 配置 ALLOWEDIPS 为 `10.192.9.0/24`, 否则会出现: *客户端启动了 wg 后, ssh 流量进 wg 隧道 -> 隧道要连 vps -> 流量又进隧道* 的死循环

有两种方式解决 "只想特定 ip 段走 wireguard 隧道" 的问题:

1. 在 wireguard-server 中, 配置 ALLOWEDIPS 为 `10.192.9.0/24`, 这样只有 `10.192.9.0/24` 的流量会走 wireguard 隧道
2. 在 wireguard-server 中, 配置 ALLOWEDIPS 为 `0.0.0.0/0`, 这样所有流量都会走 wireguard 隧道

但是第一种方式会导致其他 ip 段无法上网, 第二种方式会导致所有流量都会走 wireguard 隧道, 这样会导致性能问题

既需要保证特定 ip 段走 wireguard 隧道, 又需要保证其他 ip 段上网

### 路由问题

在 wireguard-server 生成的 peer 配置文件中, 需要 `/32` 来精确确定 peer 的 ip

但在客户端的 peer 配置文件中, 往往需要指定例如 `/24` 来表示同网段

即分发 `peer.conf` 配置文件时, 在 ip 后边加一个 `/24` 即可

## virtual private network

基于 trojan-go / sing-box 网络拓扑结构如下

```
# 正常情况下
公网用户 或 Trojan 客户端
        |
        | 443
        v
      nginx
        |
        +-- example.com / www.example.com -> 静态站点
        +-- magic.example.com -> 127.0.0.1:9001 nginx iso Web fallback
        +-- iso.example.com -> 127.0.0.1:9001 nginx iso Web fallback
        +-- ftp.example.com -> 127.0.0.1:9002
        +-- support / image / ... 等子域 -> 各自本地端口

# 代理情况下
公网用户 或 Trojan 客户端
        |
        | 8081
        v
    sing-box Trojan
        |
        +-- SNI = magic.example.com 且 密码正确 -> 代理出站 direct
        +-- 非 Trojan / 探测 -> 127.0.0.1:8080 nginx fallback
                                  |
                                  +-- 当前回到 127.0.0.1:9001 nginx iso Web fallback
```

### trojan-go

repo: https://github.com/p4gefau1t/trojan-go.git

1.  `/opt/trojan-go/trojan-go.yml`：

    ```yaml
    version: "3"
    services:
      trojan_go:
        image: teddysun/trojan-go:latest
        container_name: trojan_go
        network_mode: host
        volumes:
          - /opt/trojan-go/data:/etc/trojan-go
        restart: always
    
    # sudo docker-compose -f /opt/trojan-go/trojan-go.yml up -d
    ```

2.  [参考](https://p4gefau1t.github.io/trojan-go/basic/config/)，`/opt/trojan-go/data/config.json`：

    ```json
    {
      "run_type": "server",
      "local_addr": "0.0.0.0",
      "local_port": 509,	# 真正的代理连接端口
      "remote_addr": "xxx.pangolin.com",	# 代理连接的主机地址
      "remote_port": 510,	# fake port
      "password": [
        "password"	# 建议长点
      ],
      "ssl": {
        "cert": "/etc/trojan-go/cert/xxx.pem",	# 需要域名以及 cert 文件，公钥，这个 trojan-go 文件夹指的是 docker 里的，宿主机里 /etc/trojan 映射到这里就行
        "key": "/etc/trojan-go/cert/xxx.key",	# 私钥
        "sni": "xxx.pangolin.com",	# 主机地址
        "fallback_port": 443	# 如果检测到非 trojan 协议连接，就转到这个端口
      }
    }
    ```

    一个配置好的参考：

    ```json
    {
        "run_type": "server",
        "local_addr": "0.0.0.0",
        "local_port": 8081,
        "remote_addr": "magic.example.com",
        "remote_port": 8080,
        "password": [
            "WaxTnF7u35wVZIeQ29l6UJq0mNXAbycg"
        ],
        "ssl": {
            "cert": "/etc/trojan-go/cert/fullchain.cer",
            "key": "/etc/trojan-go/cert/example.com.key",
            "sni": "magic.example.com",
            "fallback_port": 443
        }
    }
    ```

    注意 cert 和 key 不要用动态链接 ln -s，且有可读权限

3.  nginx 配置参考 `/etc/nginx/site-enabled/trojan.http.nginx`：

    ```nginx
    server {
        listen 80;
        server_name magic.example.com;
        return 301 https://$host$request_uri;
    }
    
    server {
        listen 8080 ;
        server_name magic.example.com;
        location / {
            proxy_pass http://127.0.0.1:9001 ;
            proxy_redirect http://127.0.0.1:9001 http://magic.example.com:8080;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_set_header X-Forwarded-Protocol $scheme;
            proxy_set_header X-Forwarded-Host $http_host;
            proxy_set_header REMOTE-HOST $remote_addr;
        }
    }
    
    ssl_certificate /etc/nginx/cert/fullchain.cer;
    ssl_certificate_key /etc/nginx/cert/example.com.key;
    
    server {
        listen 443 ssl ;
        server_name magic.example.com ;
        location / {
            proxy_pass http://127.0.0.1:9001 ;
            proxy_redirect http://127.0.0.1:9001 https://magic.example.com ;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_set_header X-Forwarded-Protocol $scheme;
            proxy_set_header X-Forwarded-Host $http_host;
            proxy_set_header REMOTE-HOST $remote_addr;
        }
    }
    ```

4.  本地的 `config.yml`：

    ```yaml
    proxies:
      - name: majo
        type: trojan
        server: magic.example.com
        port: 8081
        password: "WaxTnF7u35wVZIeQ29l6UJq0mNXAbycg"
        sni: magic.example.com
    ```

5.  与 8081 发起连接时

    1.  TLS 成功，但不是 trojan 协议，则重定向到 8080；访问 `http://magic.example.com:8080` 和 `https://magic.example.com:8081`，两个页面完全相同，但是后者为 https
    2.  TLS 失败，直接重定向到 443 ssl；
    3.  TLS 成功，是 trojan 协议，密码正确，正常代理

6.  检查是否配置正确，假设 fake page 开放在 9428 端口，配置的域名是 `test.example.com` 和 `magic.example.com`

    1.  访问 `https://test.example.com`，fake
    2.  访问 `http://magic.example.com` -> `https://magic.example.com`，fake
    3.  访问 `http://magic.example.com:8080`，fake
    4.  访问 `https://magic.example.com:8081`，fake

### sing-box

repo: https://github.com/SagerNet/sing-box.git

类似 trojan-go，配置文件信息如下 `sing-box.yml`

```yaml
services:
  sing-box:
    image: ghcr.io/sagernet/sing-box:latest
    container_name: sing-box
    network_mode: host
    volumes:
      - ./data:/etc/sing-box
    command: ["run", "-c", "/etc/sing-box/config.json"]
    restart: unless-stopped

# sudo docker compose -f $PWD/sing-box.yml up -d
```

config 配置如下（允许多用户访问控制，服务监听 8081，探测流量会被 fallback 到 8080 上的服务）；具体的实现可以参考 [角色分流](https://sing-box.sagernet.org/configuration/route/rule/)

```json
{
  "log": {
    "level": "info",
    "timestamp": true
  },
  "inbounds": [
    {
      "type": "trojan",
      "tag": "trojan-in",
      "listen": "::",
      "listen_port": 8081,
      "users": [
        {
          "name": "full-access",
          "password": "<full-access-password>"
        },
        {
          "name": "guest",
          "password": "<guest-password>"
        }
      ],
      "tls": {
        "enabled": true,
        "server_name": "example.com",
        "certificate_path": "./cert/fullchain.cer",
        "key_path": "./cert/example.com.key"
      },
      "fallback": {
        "server": "127.0.0.1",
        "server_port": 8080
      }
    }
  ],
  "outbounds": [
    {
      "type": "direct",
      "tag": "direct"
    }
  ],
  "route": {
    "rules": [
      {
        "auth_user": [
          "guest"
        ],
        "action": "sniff",
        "timeout": "300ms"
      },
      {
        "auth_user": [
          "guest"
        ],
        "domain_suffix": [
          "chatgpt.com"
        ],
        "action": "route",
        "outbound": "direct"
      },
      {
        "auth_user": [
          "guest"
        ],
        "domain": [
          "copilot-proxy.githubusercontent.com",
          "origin-tracker.githubusercontent.com"
        ],
        "action": "route",
        "outbound": "direct"
      },
      {
        "auth_user": [
          "guest"
        ],
        "action": "reject",
        "method": "default"
      }
    ]
  }
}

```

整体结构如下

```bash
$ tree
.
├── data
│   ├── cert
│   │   ├── fullchain.cer	# 从 acme.sh ECC 复制
│   │   └── example.com.key
│   └── config.json
└── sing-box.yml

3 directories, 5 files
```

#### nice try，不用看

通过对前面网络拓扑结构的描述，可以很明显的发现 sing-box + trojan 架构的规律：

1.   客户端长期访问某个很特殊的端口 8081
2.   手动访问 8081 时，发现其和 8080 端口对应的服务是一样的：提供一个 web 服务，但是这个服务是偏静态的，需要长期建立连接且流量很大

长期观察下来就知道有猫腻，如果尝试将这个域名伪装成 mirror.example.com，就可以在一定程度上让人以为在下载镜像。但是端口很特殊，依旧不是理想的选择

如果要做的更稳一些，就该考虑让 singbox 监听 `80/443`，这样更符合 http 网络流量的叙事效果

于是灵机一动设计了下面这样的架构：

```
公网用户 或 Trojan 客户端
        |
        | 443
        v
    sing-box Trojan
        |
        +-- SNI=iso.example.com 且 Trojan 密码正确
        |       -> 代理出站 direct
        |
        +-- 其他普通 HTTPS / 密码错误 / 主动探测
                -> 127.0.0.1:8080 nginx 内部入口
                       |
                       +-- example.com / www.example.com -> Typecho / 静态站点
                       +-- iso.example.com -> 127.0.0.1:9001 nginx iso Web fallback
                       +-- ftp.example.com -> 127.0.0.1:9001 nginx iso Web fallback
                       +-- support / image / ... -> 原本各反代服务
```

即让 sing-box 直接面对来到服务器的任意流量，若 SNI 正确 + 密码正确，则代理；否则将流量再 fallback 给 nginx（监听在 8443 端口）做处理，仍然负责原来的多子域名反代、静态站点、WebSocket、上传、跳转等 Web 逻辑

但是带来的后果是很繁琐的：

- `443` 只能一个进程监听，所以 nginx 不能再直接监听公网 `443`

- nginx 需要退到内部端口 `127.0.0.1:8443`，真实客户端 IP 会消失，从 nginx 看到的来源都将是 127.0.0.1，后果是

    ```
    访问日志失真
    限速失效
    fail2ban 失效
    按 IP 封禁失效
    后台审计失真
    应用层安全策略失效
    GeoIP 判断失效
    ```

- 原本所有 `listen 443 ssl` 的 server block 都要重新适配成内部 fallback 入口

- TLS 终止点会从 nginx 变成 sing-box，证书、SNI、ALPN、HTTP/2 行为都要重新确认

- nginx 后面看到的连接可能变成来自本机的 HTTP，需要正确补 `Host`、`X-Forwarded-Proto: https`、真实 IP 等头；依赖 HTTPS scheme 的应用可能会出现跳转错误、回调 URL 错误、混合内容、`Secure` Cookie 判断异常；WebSocket、长连接、大文件上传、Range 下载、HTTP/2 等行为都要重新测试。特别是再反代一些 docker 暴露出来的服务时会更麻烦。

    ```
    http:// 回跳
    登录后无限重定向
    OAuth / 回调 URL 错误
    Secure Cookie 不下发
    SameSite / HTTPS 判断异常
    混合内容警告
    WebDAV / API 生成错误外链
    Typecho 后台地址异常
    ```

    一些大文件的上传和 Range 下载时可能遇到以下问题

    ```
    上传中断
    大文件 413 / 502 / 504
    下载不能断点续传
    Range 头被异常处理
    空闲超时提前触发
    nginx client_max_body_size 配置还在，但入口层可能先断
    ```

- 所有现有子域名都会经过 sing-box fallback，所以一次入口配置错误可能影响整个 `example.com` 站点群

- 回滚必须提前准备好：能快速让 nginx 重新接回公网 `443`

总结后果就是

1. 443 整体不可用，所有 example.com 子域挂掉
2. Trojan 可用但 Web 全挂
3. Web 可用但登录、回调、Cookie、跳转异常
4. WebSocket / 长连接异常
5. 大文件上传下载异常
6. 日志全是 127.0.0.1，安全审计失效
7. 证书续期失败，到期后全站 TLS 失败
8. ALPN / HTTP/2 行为异常，部分客户端无法访问
9. 回滚不干净，nginx 和 sing-box 抢 443

如果换个思路，用 nginx 的 stream 模式，检查 SNI 为 magic.example.com 时，转发给 singbox，其他的再走 nginx 自己的分发逻辑呢？

这个版本是让客户端访问 `magic.example.com:443`；对比原本 `magic.example.com:8081`，实际上 `magic.example.com` 的作用只是用于 dns 找到 ip，最终客户端访问的是 `ip:8081`

```
公网用户 或 Trojan 客户端
        |
        | 443
        v
    nginx stream
        |
        +-- SNI = iso.example.com
        |       |
        |       v
        |   sing-box 127.0.0.1:8081
        |       |
        |       +-- Trojan 密码正确 -> direct 出站
        |       +-- 普通 HTTPS / 错误密码 -> nginx iso Web fallback
        |
        +-- 其他 SNI
                |
                v
            nginx HTTPS 内部入口 127.0.0.1:8080
                |
                +-- example.com / www.example.com
                +-- magic.example.com -> 127.0.0.1:9001 nginx iso Web fallback
                +-- iso.example.com -> 127.0.0.1:9001 nginx iso Web fallback
                +-- support / image / ...
```

首先明确 nginx 的 http 不能实现流量转发到 singbox，而 nginx stream 相较于 http，可以代理 raw 的 tcp / udp 流量，但是代价是得把原来的 http / tls 回退到内部网络，这样要比前面 nginx 在 singbox 后的处理方式要温和的多，不过来源变成 127.0.0.1 这件事没辙

## behind the mTLS

参考 mTLS 常用于企业级 API、零信任系统的最外层防护机制：为开放在公网的服务提供按特定证书实现访问控制

### what is mTLS

设计一套 mTLS + PROXY PROTOCOL 的架构解决方案如下：

涉及到 3 个对象

- CA；可以是自建 CA、也可以是付费/公益 CA
- SERVER；提供 singbox 的服务器
- CLIENT；各访问终端

这里简单说明 mTLS 的作用

> TLS

解决客户端想要确认：我连接的是不是正确的服务器

1. client 连接 server；
2. server 提供服务器证书 cert；该 cert 由受信任的 CA 签发，而每台终端基本都有这些 CA 根证书；
3. client 验证 cert 可信；
4. client 建立 TLS 加密连接；

```
client
   |
   | 验证 cert-server
   | 信任依据：公共 CA / 自建 CA
   v
server
```

server 通常不需要验证 client 身份

> mTLS

解决服务端、客户端互认身份的需求

1. client 连接 server；
2. server 提供 cert-server；该 cert-server 可以由受信任的 CA 签发，也可以由自建 CA 签发；
3. client 验证 server 合法身份；
4. server 要求 client 提供 cert-client；但是该 cert-client 一般由自建 CA 签发（可以与签发 server 证书的是同一个）；
5. server 验证 client 合法身份；
6. 双方建立 TLS 加密连接

```
client
   |
   | 验证 cert-server
   | 信任依据：公共 CA / 自建 CA
   v
server
   |
   | 验证 cert-client
   | 信任依据：通常为自建 CA
   v
client
```

显然，mTLS 的流程对比 TLS 就是多了一个 「server 验证 client 身份」 的流程

这里有一个倾向，即一般 「使用自建 CA 签发 client 的证书」 以及 「使用公共 CA 签发 server 的证书」，因为

- client 连接 server，是希望确认 server 可信，可以使用公共 CA 证书证明 server 身份
- server 允许 client 连接，则需要 client 证明自己拥有接入的权限，所以需要自建 CA 服务器

本质上来讲，自建 CA 实际上定义了一个 「私有的信任域」，即只有架构自己签发、认可的身份，才允许存在于架构中

因此，设计出的架构如下：

```
                     公共 CA
                        |
                        v
                  cert-server
                        |
                        v
client  ----------->  server
   ^                    |
   |                    |
   |                    | 验证 client 身份
   |                    v
   |                 自建 CA
   |                    |
   |                    +--> cert-client-A
   |                    +--> cert-client-B
   |                    +--> cert-client-C
   |                         ...
   |
   +------ 验证 server 身份
```

整个信任关系可以归结为：

```
公共 CA
   |
   +--> 解决「这个 server 是不是可信 server」


自建 CA
   |
   +--> 解决「这个 client 是不是我允许的 client」


mTLS
   |
   +--> TLS server 身份验证
   |
   +--> client 身份验证
   |
   +--> 双方验证通过
            |
            v
       建立加密连接
```

### sing-box with mTLS

设计这个结构，主要还是

## refer

1. https://www.cnblogs.com/ryanyangcs/p/14462269.html
2. 
