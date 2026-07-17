# using hedgedoc-offline with mDNS

## hedgedoc

repo: [hedgedoc/hedgedoc](https://github.com/hedgedoc/hedgedoc)

一个在线协作 markdown 平台，是 HackMD 的开源版本，主要用途是在线协作；当然还集成了发布文章供他人访问，权限管理等内容。

旧版本名称为 codimd，现在官方开源更新的名称为 `hedgedoc/hedgedoc`，基本使用 docker-compose 的流程是相同的

### installation

1. 在 MySQL 建立供 HedgeDoc 使用的数据库，以下是基本要求
    1. 一个数据库，名为 `hedgedoc`：`CREATE DATABASE hedgedoc`
    2. 一个对上述数据库有完全权限的、使用密码的数据库内账户，名为 `hedgedoc`；`CREATE USER 'hedgedoc'@'%' IDENTIFIED BY 'password';`，`GRANT ALL ON hedgedoc.* TO 'hedgedoc'@'%';`
2. 安装 docker 以及 docker-compose，参阅本站文章 [app | docker-handbook](https://www.majo.im/index.php/wkyuu/17.html)
3. 使用 docker-compose 来部署 hedgedoc；贴一个自己用的配置文件，这里是根据上文自己创建的 MySQL 数据库来配置的，这样做的好处是今后 hedgedoc 源镜像在哪都能 pull 一份官方的，而数据库和图片信息都在本地，更好移植；配置更多内容，参考高级配置文件：[configuration](https://docs.hedgedoc.org/configuration/)
    ```yaml
    version: "3"

    services:
      hedgedoc:
        image: lscr.io/linuxserver/hedgedoc:latest
        container_name: hedgedoc
        environment:
          - PUID=1000
          - PGID=1000
          - TZ=Asia/Shanghai
          - CMD_DOMAIN=md.majo.im
          - CMD_PROTOCOL_USESSL=true
          - CMD_PORT=3000
          - CMD_ALLOW_ORIGIN=['localhost']
          - CMD_DB_URL=mysql://hedgedoc:password@localhost:3306/hedgedoc
          - UPLOADS_MODE=0744
          - CMD_HSTS_ENABLE=true
          - http_proxy=http://192.168.124.10:7890
          - https_proxy=http://192.168.124.10:7890
        volumes:
          - /home/www/hedgedoc/uploads:/hedgedoc/public/uploads
          - /home/www/hedgedoc/config:/config
        ports:
          - 2000:3000
        restart: always

    # sudo docker-compose -f /home/www/hedgedoc/hedgedoc.yml up -d
    ```
4. 配置 nginx 反向代理：

    ```nginx
    server {
        listen 80;
        server_name md.majo.im;
        return 301 https://$host$request_uri;
    }

    ssl_certificate /etc/nginx/cert/fullchain.cer;
    ssl_certificate_key /etc/nginx/cert/majo.im.key;

    server {
        listen 443 ssl http2;

        server_name md.majo.im ;

        location / {
            proxy_pass http://127.0.0.1:9420 ;
            proxy_redirect http://127.0.0.1:3000 https://md.majo.im;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location /socket.io/ {
            proxy_pass http://127.0.0.1:3000/socket.io/;
            proxy_redirect http://127.0.0.1:3000 https://md.majo.im;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection $connection_upgrade;
        }
    }
    ```

## problem

hedgedoc 这套系统涉及到的主要网络拓扑如下

```bash
URL
```

会遇到如下的问题：

### 动态 Host 与规范入口

HedgeDoc 会在登录重定向、页面资源和 Socket.IO 配置中使用启动时确定的 `CMD_DOMAIN`、协议和端口。若容器配置为 `localhost`，局域网客户端登录后会被重定向到客户端自己的 `localhost`，表现为“登录成功但仍未登录”。

Nginx 可以用 `proxy_redirect` 与 `sub_filter` 将响应内的 `localhost` 动态替换为请求 Host，使同一实例能从多个 mDNS 名称或 IP 入口访问；但这依赖文本替换，容易遗漏 CSP、认证回调和非文本响应。稳定部署应选择一个固定的 mDNS 名称或 LAN IP 作为规范入口，并让 HedgeDoc 的公开 URL 配置与该入口完全一致。

## solution

通过 mDNS 绑定 hedgedoc 通过 hostname.lan 访问，这样在切换 ip、更换网络环境时，就不会影响登录状态，而他人依旧可以通过 mDNS 访问该服务

