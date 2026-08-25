---
title: "app-synctv"
description: "SyncTV，一个用于在线一起看、一起聊天、发送弹幕、自动挂载主流媒体源的项目"
date: "2024-02-03T05:55:00.000Z"
updated: "2024-11-25T05:32:10.000Z"
tags: []
draft: false
layout: "post"
slug: "synctv"
---

## SyncTV

>   一个用于在线一起看，一起聊天，发送弹幕，自动挂载主流媒体源的项目

项目源码，[synctv-org/synctv](https://github.com/synctv-org/synctv.git)，[文档](https://synctv.wiki/)

![实现效果](https://wkyuu.oss-cn-shenzhen.aliyuncs.com/markdown/image-20240203121531508.png)

## install

建议使用 docker-compose 快速容器化搭建 synctv，下面是参考配置文件：

```yaml
version: '3'

services:
  synctv:
    image: 'synctvorg/synctv:latest'
    container_name: synctv
    restart: unless-stopped
    ports:
      - '8001:8080'	# host:container
    volumes:
      - /srv/www/synctv/data:/root/.synctv
    environment:
      - PUID=0
      - PGID=0
      - UMASK=022
      - TZ=Asia/Shanghai

# sudo docker-compose -f /srv/www/synctv/synctv.yml up -d
```

访问 `http://ip:8001` 即可访问页面；通过 docker 查看日志可以发现，其内置一个 root/root 的账号，使用其登录之，后续可以进行一系列配置，包括创建新的 root 账号，新建其他 guest 账号等

## online

为了减少 vps 的资源压力，使用本地主机 itx 搭建，需要搭配 nginx（vps） + frps（vps） + frpc（itx）做成在线的站点供朋友分享

### frp

vps 上的 frps 配置参考文件如下，并且还要在 vps 的安全组中开启 8000、8001（tcp/udp）、8002 的端口准入

```ini
[common]
bind_port = 8000
authentication_method = token
token = "xxxxxxx"
log_file = ./frps.log
log_max_days = 3
```

itx 上的 frpc 配置参考文件如下

```ini
[common]
server_addr = xxx.xxx.xxx.xxx	# 这里写 vps 的公网 ip
server_port = 8000
authentication_method = token
token = "xxxxxxx"

[synctv_tcp]
type = tcp
local_ip = 127.0.0.1
local_port = 8001
remote_port = 8001

[synctv_udp]
type = udp
local_ip = 127.0.0.1
local_port = 8001
remote_port = 8001

[alist]
type = tcp
local_ip = 127.0.0.1
local_port = 8002
remote_port = 8002
```

### nginx

在 vps 中使用 nginx 配置反向代理，server 参考配置如下

```nginx
server {
	listen 443 ssl      ;
	server_name sync.domain.com ;	# 实际的域名

    ssl_certificate fullchain.cer ;	# 可以选择是否启用 ssl
	ssl_certificate_key cert.key  ;

	location / {
		proxy_pass http://127.0.0.1:8001;	# 看 docker-compose 里的 host
		proxy_set_header Host $host;
		proxy_set_header X-Real-IP $remote_addr;
		proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
		proxy_set_header X-Forwarded-Proto $scheme;
		proxy_set_header X-Forwarded-Protocol $scheme;
		proxy_set_header X-Forwarded-Host $http_host;
		proxy_set_header REMOTE-HOST $remote_addr;
		proxy_set_header Upgrade $http_upgrade;
		proxy_set_header Connection $connection_upgrade;
		proxy_set_header Range $http_range;
		proxy_set_header If-Range $http_if_range;
		client_max_body_size 20m;
		proxy_http_version 1.1;
	}
}
```

然后访问 `sync.domain.com` 即可；

注意，在测试环境 ubuntu 18.04 使用 `apt install nginx` 所得 `nginx -v` 版本为 nginx/1.18.0，默认没有支持 `http_upgrade` 和 `connection_upgrade` 两个定义（官方推荐自定义这两个映射），会导致项目的 wss 在升级协议时失败，因此需要到 nginx.conf 内的 http 域内添加以下内容：

```nginx
http {

    ...

	map $http_upgrade $connection_upgrade {
		default upgrade;
		'' close;
	}
    ...
}

```

### OAuth

为了方便管理和注册，建议直接使用 QQ、gitee 等的 OAuth2 调用直接登录，在 **管理后台 - OAuth2 管理** 中可以配置，具体各项可以参考官方文档，下面给出一个 gitee 的参考

![](https://tataramoriko-oss.oss-cn-shenzhen.aliyuncs.com/markdown/image-20240203134812464.png)

---

![](https://tataramoriko-oss.oss-cn-shenzhen.aliyuncs.com/markdown/image-20240203134933763.png)

## alist

>   一个快速管理各网盘的开源项目，其可以作为中间人挂载各主流网盘供访问，搭配 synctv 可以播放网盘中的内容，减少一些不必要的鉴权行为

使用 docker-compose 安装，参考文件如下

```yaml
version: '3'

services:
    alist:
        image: 'xhofe/alist:latest'
        container_name: alist
        volumes:
            - '/srv/www/alist/data:/opt/alist/data'
        ports:
            - '8002:5244'
        environment:
            - PUID=0
            - PGID=0
            - UMASK=022
        restart: unless-stopped

# sudo docker-compose -f /srv/www/alist/alist.yml up -d
```

成功启动后，访问 `http://ip:8002`，通过 docker 日志可以找到 `INFO[xxx] Successfully created the admin user and the initial password is: xxxxx`，则账号密码就是 admin/xxxxx，然后到用户中心修改管理员账号相应内容

将 alist 穿透到 vps，可以在 vps 中采用以下 nginx 设置

```ini
server {
	listen 443 ssl      ;
	server_name alist.domain.com ;

	location / {
		proxy_pass http://127.0.0.1:8002 ;

		proxy_redirect http://127.0.0.1:8002 https://alist.domain.com;	# 必须要重写，不然无法播放
		proxy_set_header Host $host;
		proxy_set_header X-Real-IP $remote_addr;
		proxy_set_header X-Forwarded-Proto https;
	}
}
```

挂载百度网盘，可以参考 [官方文档](https://alist-doc.nn.ci/docs/driver/baidu/)
