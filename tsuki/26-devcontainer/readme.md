# devcontainer

基础测试用 container 集合，每个一个子目录：`<name>.yml`（docker compose）+ `init-<name>.sh`（建映射目录并按需拉取 yml）+ 映射文件夹。

| dir | image | port | note |
| --- | --- | --- | --- |
| 01-telnet | alpine + busybox-extras | 2323:23 | `telnet 127.0.0.1 2323` 直接进 /bin/sh，无认证 |
| 02-nginx | nginx:alpine | 8080:80 | 静态站点根 `./html`，可选 `./conf/default.conf` |
| 03-python | python:3.12-slim | 8000:8000 | `http.server` 托管 `./app`，可改为 `python main.py` |
| 04-ssh | linuxserver/openssh-server | 2222:2222 | `ssh user@127.0.0.1 -p 2222`，口令 password |
| 05-redis | redis:alpine | 6379:6379 | `--protected-mode no`，未授权靶；改密见 yml 注释 |
| 06-postgres | postgres:alpine | 5432:5432 | postgres/postgres，库 test；18+ 挂载点为 `/var/lib/postgresql` |
| 07-mongo | mongo | 27017:27017 | 默认不设账号 = 未授权靶 |
| 08-php | php:apache | 8081:80 | `./www` 映射 `/var/www/html`，含 phpinfo |
| 09-tomcat | tomcat:9-jdk11 | 8082:8080 | war 放 `./webapps`；默认应用在镜像 webapps.dist |
| 10-httpd | httpd:alpine | 8083:80 | Apache，静态根 `./htdocs` |
| 11-samba | dperson/samba | 139/445 | 共享 share，账号 user/password |
| 12-dns | coredns/coredns | 53/udp+tcp | 记录在 `./conf/hosts`，转发在 `./conf/Corefile` |
| 13-smtp | mailhog/mailhog | 1025 / 8025 | SMTP 捕获，web UI `:8025` |
| 14-openwrt | openwrtorg/rootfs | 8084:80 | privileged 软路由；LuCI 需自行 opkg 安装 |

> 端口互不冲突。redis/mongo 默认无认证（练习用途），生产勿直接暴露。

## usage

```bash
cd 01-telnet
sh init-telnet.sh                       # 建映射目录，缺 yml 时拉取
docker compose -f telnet.yml up -d      # 启动
docker compose -f telnet.yml down       # 停止
```

nginx、python 同理，替换目录与文件名。
