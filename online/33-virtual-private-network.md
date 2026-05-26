# proxy architecture

## openvpn

注意到 wireguard 也是一种 vpn, 肯定得拿出来和 openvpn 进行对比

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

## vpn

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
      "remote_port": 510,	# fake port，detected  avoid of the
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
        "local_port": 9445,
        "remote_addr": "magic.majo.im",
        "remote_port": 9446,
        "password": [
            "WaxTnF7u35wVZIeQ29l6UJq0mNXAbycg"
        ],
        "ssl": {
            "cert": "/etc/trojan-go/cert/fullchain.cer",
            "key": "/etc/trojan-go/cert/majo.im.key",
            "sni": "magic.majo.im",
            "fallback_port": 443
        }
    }
    ```

    注意 cert 和 key 不要用动态链接 ln -s，且有可读权限

3.  nginx 配置参考 `/etc/nginx/site-enabled/trojan.http.nginx`：

    ```nginx
    server {
        listen 80;
        server_name magic.majo.im;
        return 301 https://$host$request_uri;
    }
    
    server {
        listen 9446 ;
        server_name magic.majo.im;
        location / {
            proxy_pass http://127.0.0.1:9421 ;
            proxy_redirect http://127.0.0.1:9421 http://magic.majo.im:9446;
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
    ssl_certificate_key /etc/nginx/cert/majo.im.key;
    
    server {
        listen 443 ssl ;
        server_name magic.majo.im ;
        location / {
            proxy_pass http://127.0.0.1:9421 ;
            proxy_redirect http://127.0.0.1:9421 https://magic.majo.im ;
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

4.  本地的 `clash.yml`：

    ```yaml
    proxies:
      - name: majo
        type: trojan
        server: magic.majo.im
        port: 9445
        password: "WaxTnF7u35wVZIeQ29l6UJq0mNXAbycg"
        sni: magic.majo.im
    ```

5.  与 9445 发起连接时

    1.  TLS 成功，但不是 trojan 协议，则重定向到 9446；访问 `http://magic.majo.im:9446` 和 `https://magic.majo.im:9445`，两个页面完全相同，但是后者为 https
    2.  TLS 失败，直接重定向到 443 ssl；
    3.  TLS 成功，是 trojan 协议，密码正确，正常代理

6.  检查是否配置正确，假设 fake page 开放在 9428 端口，配置的域名是 `test.majo.im` 和 `magic.majo.im`

    1.  访问 `https://test.majo.im`，fake
    2.  访问 `http://magic.majo.im` -> `https://magic.majo.im`，fake
    3.  访问 `http://magic.majo.im:9446`，fake
    4.  访问 `https://magic.majo.im:9445`，fake

### sing-box

repo: https://github.com/SagerNet/sing-box.git

类似 trojan-go，配置文件信息如下

`sing-box.yml`

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

结构如下

```bash
$ tree
.
├── data
│   ├── cert
│   │   ├── fullchain.cer	# 从 acme.sh ECC 复制
│   │   └── majo.im.key
│   └── config.json
└── sing-box.yml

3 directories, 5 files

```


## refer

1. https://www.cnblogs.com/ryanyangcs/p/14462269.html
2. 