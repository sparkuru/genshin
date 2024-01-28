# nginx

## basic

1. Nginx 默认在 ubuntu 源仓库可用 `sudo apt install nginx`，
2. `sudo systemctl start nginx`，还有 restart、stop、status、enable、disable
3. `sudo nginx -s reload`，`sudo nginx -t`
4. 进入到 `/etc/nginx/` 工作目录下（注意 root 权限），网站可用配置文件放在 `/etc/nginx/sites-available/` 文件夹下（这里的配置文件只是配置好但不应用），网站已应用配置文件放在 `/etc/nginx/sites-enabled/` 文件夹下（这里的文件由上面的创建一个软连接过来，只有这里的可以被应用）：`ln -s /etc/nginx/sites-available/default /etc/nginx/sites-enabled/`

## I'm the one who make the questions

### question 1

nginx 本身主要是代理 http 协议，为了使 nginx 可以支持代理各种其他协议，因此需要配置 nginx 的 stream 模块来实现这些非 http 协议的代理，我提出以下一种实际的问题模型，其可以应用到多种不依赖于 http 的环境中去

1. 假设网络拓扑为：

    1. A：一台家用高性能服务器主机
    2. B：一个 vps 服务商提供的 host，ip 是 123.123.123.123，域名是 example.com
    3. 许多玩家的客户端
2. 我在 A 上开了一个 minecraft 服务器在 127.0.0.1:5505，使用 frp 内网穿透将 127.0.0.1:5505 映射到 123.123.123.123:5505，以往其他客户端只需要输入：`123.123.123.123:5505` 即可通过 B 上的 frps 中转连接到 A 进行 server 的游玩
3. 如果不想暴露端口，而使用二级域名，即 B 上不再开放 5505 端口，客户端需要输入 `mc.example.com` 来替代含有端口的行为
4. 换种说法就是：能否让玩家输入 mc.example.com 时，在 client 看来是通过 123.123.123.123:80 的方式连接到 B，而在 B 上 nginx 根据请求的地址是 `mc.example.com` 智能地将这些来自 client、目的为 mc.example.com 的 tcp、udp 链接转发到 123.123.123.123:5505

Nginx 的 stream 模块就支持 TCP 和 UDP 的代理（以及负载均衡，尽管该模块一开始就是设计来用于负载均衡的），要配置 nginx 支持 tcp 和 udp 的代理，需要 nginx 在编译时添加上 `--with-stream` 的选项，但是就 ubuntu 22.04 源里默认安装的 nginx 是 1.18.0 的，默认不带 stream 模块，有两种解决方案：安装 1.24.0+ 的 nginx 的 binary（可以通过获取最新的包然后 dpkg 安装或其他）；或者自己编译，下面提供自己编译的流程：

1. 输入 `nginx -V` 查看自己的 nginx 编译时使用的选项：

    ```bash
    nginx version: nginx/1.18.0 (Ubuntu)
    built with OpenSSL 3.0.2 15 Mar 2022
    TLS SNI support enabled
    configure arguments: --with-cc-opt='-g -O2 -ffile-prefix-map=/build/nginx-zctdR4/nginx-1.18.0=. -flto=auto -ffat-lto-objects -flto=auto -ffat-lto-objects -fstack-protector-strong -Wformat -Werror=format-security -fPIC -Wdate-time -D_FORTIFY_SOURCE=2' --with-ld-opt='-Wl,-Bsymbolic-functions -flto=auto -ffat-lto-objects -flto=auto -Wl,-z,relro -Wl,-z,now -fPIC' --prefix=/usr/share/nginx --conf-path=/etc/nginx/nginx.conf --http-log-path=/var/log/nginx/access.log --error-log-path=/var/log/nginx/error.log --lock-path=/var/lock/nginx.lock --pid-path=/run/nginx.pid --modules-path=/usr/lib/nginx/modules --http-client-body-temp-path=/var/lib/nginx/body --http-fastcgi-temp-path=/var/lib/nginx/fastcgi --http-proxy-temp-path=/var/lib/nginx/proxy --http-scgi-temp-path=/var/lib/nginx/scgi --http-uwsgi-temp-path=/var/lib/nginx/uwsgi --with-compat --with-debug --with-pcre-jit --with-http_ssl_module --with-http_stub_status_module --with-http_realip_module --with-http_auth_request_module --with-http_v2_module --with-http_dav_module --with-http_slice_module --with-threads --add-dynamic-module=/build/nginx-zctdR4/nginx-1.18.0/debian/modules/http-geoip2 --with-http_addition_module --with-http_gunzip_module --with-http_gzip_static_module --with-http_sub_module
    ```
2. 删除 nginx ，[参考](https://cloud.tencent.com/developer/article/1752589)，但是先备份和删除 `/etc/nginx` 文件夹，重点是 `sites-*` 两个文件夹和 `nginx.conf` 文件，以便后续安装后重新配置 nginx 的设置
3. 获取 nginx 源码：`git clone https://github.com/nginx/nginx.git /tmp/tmp/nginx`
4. 进入工作目录，`cd /tmp/tmp`，创建一个 `touch /tmp/tmp/build.sh` 文件方便修改编译选项，根据前文 nginx 输出内容填入以下选项（复制编译选项，最后加上 stream 相关模块的选项）

    ```shell
    #!/bin/sh

    cd /tmp/tmp/nginx

    auto/configure \
    --with-cc-opt='-g -O2 -ffile-prefix-map=/build/reproducible-path/nginx-1.25.5=. -fstack-protector-strong -fstack-clash-protection -Wformat -Werror=format-security -fcf-protection -fPIC -Wdate-time -D_FORTIFY_SOURCE=2' --with-ld-opt='-Wl,-z,relro -Wl,-z,now -fPIC' --prefix=/usr/share/nginx --conf-path=/etc/nginx/nginx.conf --http-log-path=/var/log/nginx/access.log --error-log-path=stderr --lock-path=/var/lock/nginx.lock --pid-path=/run/nginx.pid --modules-path=/usr/lib/nginx/modules --http-client-body-temp-path=/var/lib/nginx/body --http-fastcgi-temp-path=/var/lib/nginx/fastcgi --http-proxy-temp-path=/var/lib/nginx/proxy --http-scgi-temp-path=/var/lib/nginx/scgi --http-uwsgi-temp-path=/var/lib/nginx/uwsgi --with-compat --with-debug --with-pcre-jit --with-http_ssl_module --with-http_stub_status_module --with-http_realip_module --with-http_auth_request_module --with-http_v2_module --with-http_dav_module --with-http_slice_module --with-threads --with-http_addition_module --with-http_flv_module --with-http_gunzip_module --with-http_gzip_static_module --with-http_mp4_module --with-http_random_index_module --with-http_secure_link_module --with-http_sub_module --with-mail_ssl_module --with-http_geoip_module=dynamic --with-http_image_filter_module=dynamic --with-http_xslt_module=dynamic --with-mail=dynamic --with-stream_geoip_module=dynamic \
    --with-stream_ssl_module --with-stream_ssl_preread_module --with-stream_realip_module --with-stream=dynamic --with-stream_geoip_module=dynamic

    # make
    # sudo make install
    ```
5. `chmod +x /tmp/tmp/build.sh && /tmp/tmp/build.sh`，尝试开始 configure，之后应该会报各种错，例如 *auto/configure: error: the HTTP XSLT module requires the libxml2/libxslt libraries.* ，根据报错安装必要组件即可：

    1. 这里给一个可能遇到的：`sudo apt install libpcre3-dev libssl-dev libxml2-dev libxslt-dev libgd-dev libgeoip-dev`
    2. 当然也有可能是已经安装了，但是仍然无法找到，这里使用 `sudo apt install apt-file`，然后使用 `sudo apt-file search libxml2` 来查找文件，这里查找到 `/usr/include/libxml2/*` 文件，因此需要在编译时将这个目录添加到当前目录下即可：`ln -s /usr/include/libxml2 /tmp/tmp`
    3. 再出问题，例如安装 `libgd-dev` 失败，则手动编译之：

        1. `git clone https://github.com/libgd/libgd.git -b GD-2.3 /tmp/tmp/libgd`
        2. `mkdir /tmp/tmp/libgd/build`，`cd /tmp/tmp/libgd/build`
        3. `cmake ..`，`make` 开始编译，编译完成后将其连接到目录 `ln -s /tmp/tmp/libgd/build/Bin /tmp/tmp`
6. 解决以上报错后，进入 `/tmp/tmp/nginx`，`make` 将各种源码编译成库和可执行文件，`sudo make install` 将库和可执行文件安装到对应的地方
7. 编写 stream 模块允许代理 tcp 流量，在 `nginx.conf` 中配置以下内容 **（这是一个** **<u>相对无效</u>**  **<u>的配置）</u>**​ **：**

    ```nginx
    ....

    http {
        ....

        server {
            listen 80;
            server_name blog.majo.im;

            root /home/www/typecho;
            index index.php;

            ...

        }
        ....
    }

    stream {

        resolver 223.5.5.5;
        map $ssl_preread_server_name $backend {
            mc.majo.im 127.0.0.1:5505;  # 假设服务器地址就是 127.0.0.1:5505，
        }

        server {
            listen 80;
            ssl_preread on;
            proxy_pass $backend;
        }

        include /etc/nginx/sites-enabled/*.stream.conf; # 如果有其他 stream 代理的话
    }
    ```

    1. 将以上配置填写完后，`sudo systemctl restart nginx` 来应用该配置
    2. 该项的逻辑是，当一个 request 来到 80 端口时，nginx 智能地根据 SNI（Server Name Indication）来分流这些 request，例如看到是 `CONNECT HTTP blog.majo.im` 就访问 `/home/www/typecho/index.php`；看到是 `CONNECT TCP mc.majo.im`，则被 stream 里的 `$backend` 给 proxy 到 127.0.0.1:5505 实现 tcp 的转发
    3. **理想是很美好的，但是这个想法从一开始就错了，执行** **​`sudo systemctl restart nginx`​** **时注定起不来，报错** ***port 80 already used***​ **，这是因为实际为 nginx 配置了两个不同的应用，他们都监听 80，这当然失败，于是乎这种仅一个端口再智能地分流的想法还没开始就破产了**；但是你又不能修改端口，因为通过 `mc.majo.im` 访问而不加端口时，他就是连接的 80 端口，如果你让给了 http，就不会再和 stream 有什么关系了
    4. **问为什么不把 http(s) 都开在 443，然后 tcp、udp 代理都放在 80？** 答案是为了可用性，别人输入 `blog.majo.im` 的时候，如果没有 http 的 `return 301 https://$host$requesturi`，这将大大减少博客被成功访问的几率，毕竟就一个 ssl/tls 都有 cs 科班自己的学生学不明白的，不太可能会指望其他用户通过手动添加 `https://` 来访问你的博客了

### question 2

是否有一种工具，能够实现：例如该工具绑定于 80 端口，对于来到的数据，首先检查其协议：

1. 如果是 http，则自动将其 301 重定向到 81 端口（假设 nginx 的 http 监听于 81，然后再根据具体情况提供 web 服务或 proxy 服务）
2. 如果检测到其他协议例如 tcp、udp 等，将其自动连接到对应开放的端口，例如使用 `mysql -p 80 -h sql.majo.im`访问 sql.majo.im（假设 ip 为 123.123.123.123），这个其实是 mysql 通过 tcp 访问了 123.123.123.123:80，则该工具自动将流量从 80 转到 3306

答案是有的（？），HAProxy 就可以实现，下面是一个可能的配置：

```ini
frontend all_traffic
    bind *:80
    mode tcp
    tcp-request inspect-delay 5s
    tcp-request content accept if HTTP

    use_backend http_traffic if HTTP
    default_backend tcp_traffic

backend http_traffic
    mode http
    server web1 localhost:81

backend tcp_traffic
    mode tcp
    server sql localhost:3306
```

其实这个配置文件很好读，haproxy 监听 80，如果到来的是 http，则转发到 `localhost:81`；如果到来的不是 http，则默认转发到 `localhost:3306`；

至此是不是就实现了一开始提出的问题？答案是半否定的，我们要回到应用的逻辑来，当用户输入 `sql.majo.im` 时，服务器不会一直都用这个域名，因为他是 tcp 连接，不需要 sni 请求，它只需要按照正常的 dns 询问历程获取服务器的 ip，然后后续都通过 ip:80 来访问服务器，因此可以实现分流，但是基本上这样还需要指定一个 80 端口，与直接指定 3306 其实没什么区别，这样还要多折腾一个 haproxy 其实不如通过 stream 直接全部代理，更好配置和管理

HAproxy 搭配 lua 脚本，实现根据请求的内容转发流量到特定端口，**可以但没必要**。如果感兴趣，可以自行尝试

### question 3

难道 nginx 的 stream 除了转发没有其他功能吗？答案是有的，而且在某些层面上有大用

1. stream 一个正常的 **负载均衡** 配置如下：

    ```nginx
    stream {
        upstream backend_servers {
            server 192.168.1.100:12345 weight=3;
            server 192.168.1.101:12345 weight=1;
        }

        server {
            listen 8080;
            proxy_pass backend_servers;
        }
    }
    ```

    这一块的逻辑是，连接到 8080 的请求，会被按照 1:3 的比例随机地负载均衡到 `192.168.1.100` 和 `192.168.1.101` 两台主机，这在大的业务场景中十分有用
2. **使用 stream 实现对 tcp 流量的加密**：假设自己开发的系统使用纯 tcp 通信（或者私有通信协议），但是又需要加密，则 stream 就可以帮助实现之；例如 client 和 server 之间的 tcp 连接要被加密，server 在服务器上开放在 5555 端口，对外的端口是 5556，则可以使用 nginx stream 将 client 与 5556 之间的通信使用 ssl/tls 来加密，然后再让 nginx 透明地将数据从 5556 传输给 5555 <u>（client -&gt; 5556 -&gt; nginx_stream -&gt; 5555 -&gt; server）</u>

    ```nginx
    stream {
        upstream backend_app {
            server 127.0.0.1:5555;
        }

        server {
            listen 5556 ssl;	# 监听并启用 ssl
            ssl_certificate /etc/nginx/cert/fullchain.cer;
            ssl_certificate_key /etc/nginx/cert/private.key;

            ssl_protocols TLSv1.2 TLSv1.3;
            ssl_ciphers HIGH:!aNULL:!MD5;

            proxy_pass backend_app;
        }
    }
    ```

    在 client 端需要搭配对应的 ssl 套件来实现这个加密通信

### question 4

假设我现在要做端口集成，具体场景如下：

1. 服务器 ip 是 123.123.123.123，域名是 example.com（二级域名有 mc，l4d2，都指向该 ip），开放集成端口于 2000
2. 有 3 个游戏服务器分别开放在：2001（mc）、2002（mc）、2003（l4d2）

    1. 玩家在 Minecraft 1.20.1 中输入 mc.example.com:2000，则 nginx stream 将其转发到 127.0.0.1:2001
    2. 玩家在 Minecraft 1.18.2 中输入 mc.example.com:2000，则 nginx stream 将其转发到 127.0.0.1:2002
    3. 玩家在 left 4 dead 2 中输入 l4d2.example.com:2000，则 nginx stream 将其转发到 127.0.0.1:2003
3. 问题是：可以在 nginx 的 stream 中根据请求报文的信息分辨出 tcp、udp、rtmp（只要不是 http(s)）要访问的游戏服务指纹（例如目标 sni、目标服务的类型、类似 http header 那样可以被具体识别）来做相应的转发处理吗？（例如 lua 脚本搭配 haproxy）

答案是，nginx 很难处理这么复杂的任务，nginx 本身并不支持像 http 请求头一样深入地内容检查，但是 nginx + lua 脚本可以实现以上的处理（这个想法本身是借鉴于 haproxy + lua 的）；假如能通过 wireshark 有效识别到了以上服务在发起 request 时指纹，去 fork 一份 nginx 的源码来编写相应的 module 也完全是有可能的

### question 5

工业互联网中，有些工业应用会使用到私有协议，结合了前文使用 nginx stream 来实现了 tcp、udp 的流量加密（类似于基于 tcp 通信的 http(s) 的原理），工业互联网的通信会和 nginx 擦出火花吗？当然是有可能的。

私有协议针对特定设备、特定环境、特定接口，其可以被设计为减少数据包的大小来减少网络延迟等；私有工业协议也可以被设计为基于 tcp 和 udp，未加密的 tcp、udp 通信在 CIA 三要素中存在可用性（ddos）、完整性（篡改）、保密性（mitm）的问题

1. nginx stream 本身可以代理 tcp 和 udp 流量，当数据要走网络时，nginx stream 还可以为他们进行加密：假如身处两地（物理）的工业设备，要通过互联网来进行通信（本身使用的是私有工业协议），如果想设计为基于 tcp、udp 包裹的通信，则使用 nginx stream + ssl/tls 来实现加密就是有可能的。**当然目前已经有了十分成熟的工业协议了，例如 Modbus TCP、MQTT、OPC UA，他们本身都是业界广泛接受的协议**，使用 nginx stream 来代理基于 tcp、udp 通信的私有协议本身也只是一种头脑风暴
2. 基于对私有协议的理解，开发者可以设计一个 nginx + lua 的模块，这个模块能够解析私有协议的数据流，例如识别数据包的边界、解析头部和负载、处理连接状态等

特别的，ipsec 协议的核心思想与该问题下的 nginx stream 加密方案是类似的，IPSec 工作在网络层，为 ip 包提供加密和身份验证，而 nginx stream 明显就是工作在应用层，只提供了端到端的加密。IPSec 适用于任何基于 IP 的协议，但 nginx 明显是被限制于应用层了。

经过多个应用的测试，这种操作实际上已经破产了。可以举一个例子简单来说明，假设我要在本地通过 mysql 连接到 mysql server<u>（虽然 mysql 本身就支持自己的 ssl 操作，但是其他纯 tcp、udp 的应用不一定支持，这里就把 mysql 假设成不支持自己的 ssl 来举例）</u>，mysql 本身没有指定 ssl 连接的情况下，就不会主动使用 ssl 套件来与 nginx stream 来进行 ssl handshake，自然无法被 nginx stream 承认为合法的连接，也就无法建立通信；但是假如 mysql 指定了使用 mysql 连接，虽然可以和 nginx stream 连接了，但是当一个带有 "请求 ssl 连接" 的 mysql request 被 nginx stream 转发给内网的 3306 时，内网的 3306 有没有开启 ssl 是一方面，更重要的是内网假如返回一个 ssl handshake 请求与本地的 mysql 连接，此时双方信息不同步，也无法建立连接。

## sub domain

配置二级域名很简单，只需要在 dns 控制台中，添加一条 A 类型记录，主机记录填二级域名以 blog 为例，记录值填 vps 的 ip 即可；然后在 nginx 的 server 块中按照如下配置：

```nginx
server {
	listen 80;
	listen [::]:80;

	server_name blog.majo.im;	# 以 blog 为例

	root /home/www/blog;
	index index.html;

	location / {
		try_files $uri $uri/ =404;
	}
}
```

当通过 `blog.majo.im` 访问时，dns 服务商告诉你的客户端访问这个 ip，然后该 ip 里的 nginx 自动按照 server_name 来分流你的请求

## dns

1. 我在 Dynadot 注册的域名，在使用 acme.sh 进行 dns 方式通过 api_token 注册时，没有发现官方提供的脚本，兜兜转转找到别人提出的 [issue](https://github.com/acmesh-official/acme.sh/pull/4510#issuecomment-1868287264)，因此决定将 majo.im 保留在 dynadot，但是 dns 服务商修改成 aliyun；如果读者的域名也没有相关支持，我也推荐转移到 aliyun、dnspod、cloudflare（如果主要面向海外用户的话）等，相关迁出过程网上很多，这里就不再重复了；**请注意，域名持有商和 dns 服务商不是一个概念，以上提到的是 dynadot 保留有 majo.im，续费也在 dynadot，但是配置 dns 解析的时候是在 aliyun**；以下内容会以 aliyun 上的 majo.im 为准
2. 为了方便后文可以检验 https 结果，需要先创建一个 web 服务测试连通性，使用 nginx、apache 之类的都可以，这里以 nginx 为例：

    1. 安装 nginx 服务：`sudo apt install nginx`，添加开机自启动：`sudo systemctl enable nginx`
    2. 在 dns 中，将域名解析到自己的 ip
    3. 配置服务，可以用以下临时配置文件来快速搭建：`/etc/nginx/sites-available/default`：

        ```bash
        server {
        	listen 80;
        	listen [::]:80;

        	server_name www.majo.im;	# 修改成自己的域名

        	root /home/www/typecho;
        	index index.html;

        	location / {
        		try_files $uri $uri/ =404;
        	}
        }
        ```

        然后创建一个主页文件用来验证：`echo "hello" > /home/www/typecho/index.html`，热重载 nginx：`sudo nginx -s reload`
    4. 访问 `http://www.majo.im` 即可看到结果
3. 自动更新证书服务：[acmesh-official/acme.sh](https://github.com/acmesh-official/acme.sh.git)，这里使用 dns 方式生成证书（下文内容客制化更改 domain 信息）

    1. `sudo mkdir -p /home/app/acme`，`sudo chown wkyuu:wkyuu -R /home/app`
    2. 获取以及安装：`curl https://get.acme.sh | sh -s email=my@example.com`，后面的 `email` 填自己注册的邮箱
    3. `cd /home/app/acme`，`mkdir cert`，`sudo ln -s /home/app/acme/cert /etc/nginx/cert`
    4. 正式签发，有两种方式

        1. **（完全自动，十分推荐）** 创建一个脚本文件：`touch /home/app/acme/scripts.sh`，填入以下内容（以下脚本需要按照具体情况来弄，但是如果你是按照我前文的配置，则基本只需要修改 `wkyuu` 为自己的用户名，以及 `majo.im` 修改成自己的域名）：

            ```shell
            #!/usr/bin/zsh
            cd /home/app/acme
            . "/home/wkyuu/.acme.sh/acme.sh.env"

            # ./scripts.sh > log 2>&1

            function color() {
                echo -e "\e[33m$1\e[0m"
            }

            DOMAIN='majo.im'
            # SUB_DOMAIN_LIST=(
            #     'www' 'ftp'
            # )
            SUB_DOMAIN_LIST=(
                '\*'
            )
            KEY_FILE_PATH="/home/app/acme/cert/majo.im.key"
            FULLCHAIN_FILE_PATH="/home/app/acme/cert/fullchain.cer"

            export Ali_Key="xxxxx"		# 参考这篇文章：https://blog.csdn.net/chen249191508/article/details/98088553
            export Ali_Secret="xxxxx"	# AccessKey ID 就是 Ali_Key，AccessKey Secret 就是 Ali_Secret

            if [[ $1 == 'issue' ]]; then
                base_cmd="acme.sh --issue --dns dns_ali -d $DOMAIN"
                for sub in "$SUB_DOMAIN_LIST[@]"; do
                    base_cmd+=" -d $sub.$DOMAIN"
                done
            fi

            if [[ $1 == 'install' ]]; then
                reloadcmd="sudo systemctl restart nginx"
                base_cmd="acme.sh --install-cert --key-file $KEY_FILE_PATH --fullchain-file $FULLCHAIN_FILE_PATH --reloadcmd '$reloadcmd' -d $DOMAIN"
                for sub in "${SUB_DOMAIN_LIST[@]}"; do
                    base_cmd+=" -d $sub.$DOMAIN"
                done
            fi

            if [[ $1 == 'info' ]]; then
                base_cmd="acme.sh --info -d $DOMAIN"
                for sub in "${SUB_DOMAIN_LIST[@]}"; do
                    base_cmd+=" -d $sub.$DOMAIN"
                done
            fi

            color "执行: $base_cmd"
            if [[ $2 == 'run' ]]; then
                if [[ $3 == 'debug' ]]; then
                    base_cmd+=" --debug"
                fi
                eval $base_cmd
            fi
            ```

            1. 后续操作，都是以该脚本为主；举例输入 `./scripts.sh issue`，则会输出将要执行的指令，输入 `./scripts.sh issue run`，则确认执行
            2. 在 `SUB_DOMAIN_LIST` 项中，填写自己想要签发的二级域名，例如这里目标生成了 `majo.im`（默认生成的）、`www.majo.im` 以及 `ftp.majo.im`；推荐使用 `\*` 生成 `*.majo.im` 泛域名，这样在新增二级域名时就不需要重新签发了
            3. 域名控制台相关内容如下（如果配置的是 `*.majo.im` 则随意添加二级域名的 A 记录）：

                | 记录 | 类型 | 值      |
                | ------ | ------ | --------- |
                | @    | A    | 你的 ip |
                | www  | A    | 你的 ip |
                | ftp  | A    | 你的 ip |
                | xxx  | A    | 你的 ip |
        2. **（到期了需要手动自己再添加）** 创建一个脚本文件：`touch /home/app/acme/scripts.sh`，填入以下内容（以下脚本需要按照具体情况来弄，但是如果你是按照我前文的配置，则基本只需要修改 `wkyuu` 为自己的用户名，以及 `majo.im` 修改成自己的域名）：

            ```shell
            #!/usr/bin/zsh
            cd /home/app/acme
            . "/home/wkyuu/.acme.sh/acme.sh.env"

            # ./scripts.sh > log 2>&1

            function color() {
                echo -e "\e[33m$1\e[0m"
            }

            DOMAIN='majo.im'
            SUB_DOMAIN_LIST=(
                'www' 'ftp'
            )
            KEY_FILE_PATH="/home/app/acme/cert/majo.im.key"
            FULLCHAIN_FILE_PATH="/home/app/acme/cert/fullchain.cer"

            if [[ $1 == 'issue' ]]; then
                base_cmd="acme.sh --issue --dns --yes-I-know-dns-manual-mode-enough-go-ahead-please -d $DOMAIN"
                for sub in "$SUB_DOMAIN_LIST[@]"; do
                    base_cmd+=" -d $sub.$DOMAIN"
                done
            fi

            if [[ $1 == 'renew' ]]; then
                base_cmd="acme.sh --renew --dns --yes-I-know-dns-manual-mode-enough-go-ahead-please -d $DOMAIN"
                for sub in "$SUB_DOMAIN_LIST[@]"; do
                    base_cmd+=" -d $sub.$DOMAIN"
                done
            fi

            if [[ $1 == 'install' ]]; then
                reloadcmd="sudo systemctl restart nginx"
                base_cmd="acme.sh --install-cert --key-file $KEY_FILE_PATH --fullchain-file $FULLCHAIN_FILE_PATH --reloadcmd '$reloadcmd' -d $DOMAIN"
                for sub in "${SUB_DOMAIN_LIST[@]}"; do
                    base_cmd+=" -d $sub.$DOMAIN"
                done
            fi

            if [[ $1 == 'info' ]]; then
                base_cmd="acme.sh --info -d $DOMAIN"
                for sub in "${SUB_DOMAIN_LIST[@]}"; do
                    base_cmd+=" -d $sub.$DOMAIN"
                done
            fi

            color "执行: $base_cmd"
            if [[ $2 == 'run' ]]; then
                if [[ $3 == 'debug' ]]; then
                    base_cmd+=" --debug"
                fi
                eval $base_cmd
            fi
            ```

            1. 执行 `/home/app/acme/scripts.sh issue run`，会返回好几条数据，参考以下输出：

                ```bash
                Domain: '_acme-challenge.majo.im'
                TXT value: '123456123456qweqweqwe'

                Domain: '_acme-challenge.www.majo.im'
                TXT value: 'qweqweqwe123456123456'

                Domain: '_acme-challenge.ftp.majo.im'
                TXT value: '654321654321654321'
                ```

                则到 dns 管理面板中，添加以下数据：

                | 记录                | 类型 | 值                    |
                | --------------------- | ------ | ----------------------- |
                | @                   | A    | 你的 ip               |
                | www                 | A    | 你的 ip               |
                | ftp                 | A    | 你的 ip               |
                | _acme-challenge     | TXT  | 123456123456qweqweqwe |
                | _acme-challenge.www | TXT  | qweqweqwe12345612345  |
                | _acme-challenge.ftp | TXT  | 654321654321654321    |

                根据具体情况来添加，添加完后等个几分钟再进行下一步
            2. 执行 `/home/app/acme/scripts.sh renew run`，签发和验证成功会输出相关提示，签发完成后，可以在 `/home/app/acme/.acme.sh/majo.im_ecc` 下找到相关 csr、cer、key 文件；
            3. 执行 `/home/app/acme/scripts.sh install run`，则会将相关文件安装到 `/home/app/acme/cert` 中，也会同时安装到 `/etc/nginx/cert` 中
            4. 其实前一种完全自动的方式，就是为你自动执行了下面这块的步骤，仅需要一个 dns api
    5. 检查 nginx 的配置文件，添加相关证书项

        ```nginx
        ssl_certificate      /etc/nginx/cert/fullchain.cer;
        ssl_certificate_key  /etc/nginx/cert/majo.im.key;
        ```
    6. 这里给一个参考重定向到 https 的配置文件：

        ```nginx
        server {
        	listen 80;
        	listen [::]:80;

        	server_name majo.im;
        	server_name www.majo.im;

        	return 301 https://$server_name$request_uri;
        }

        server {
            listen 443 ssl;
            listen [::]:443 ssl;

            ssl_certificate      /etc/nginx/cert/fullchain.cer;
            ssl_certificate_key  /etc/nginx/cert/majo.im.key;

            root /home/www/typecho;
        	server_name majo.im;
        	server_name www.majo.im;

            ...
        }
        ```

以上操作的主要目录如下：

```bash
.
├── etc
│   ├── apt
│   │   ├── sources.list
│   │   └── sources.list.backup
│   ├── nginx
│   │   ├── cert
│   │   └── sites-available
│   │       └── default
│   └── php
│       └── 8.1
│           └── fpm
│               └── php.ini
└── home
    ├── app
    │   ├── acme
    │   │   ├── acme.sh
    │   │   ├── cert
    │   │   │   ├── fullchain.cer
    │   │   │   └── majo.im.key
    │   │   └── scripts
    │   └── phpmyadmin
    │       └── index.php
    ├── wkyuu
    │   ├── .acme.sh
    │   │   ├── acme.sh
    │   │   └── majo.im_ecc
    │   │       ├── fullchain.cer
    │   │       └── majo.im.key
    │   ├── .ssh
    │   │   └── authorized_keys
    │   └── .zshrc
    └── www
        └── typecho
            └── index.html
```

## mail forward

搭建自己的邮箱匿名系统，即以后你可以留下邮箱 wkyuu@majo.im，别人发送后会自动中继转发到你的 @gmail.com；但是 nginx 本身被设计为 http 和 https，虽然有 mail 相关选项，但是本身支持很差，摘自 [github](https://github.com/ltcbuzy/Configuring-NGINX-as-a-Mail-Proxy-Server) 的回答如下：

> For mail proxy functionality, you would typically use a dedicated mail server software such as Postfix, Exim, or Microsoft Exchange. These mail servers are specifically designed to handle email traffic and implement protocols like SMTP and IMAP.

该 github 项目也只是实现了对 imap 邮件处理协议的 SSL 支持和负载均衡，与提出的仅转发邮件其实没什么关系，因此下面主要使用 postfix 来实现邮件主动中继

**搭建前先看：** 有些 vps 服务商默认封堵了 25 的出端口，如果确实封堵了，**需要主动去** **[申请解封](https://www.cnblogs.com/sueyyyy/p/16326691.html)**。以下是检测方法

1. 输入 `host -t mx gmail.com` 可以查看所有 gmail.com 提供的邮件服务器接口，这里以 *gmail-smtp-in.l.google.com* 为例
2. 输入 `telnet gmail-smtp-in.l.google.com 25 ` 尝试连接，如果迟迟没有回应，最终报错 *telnet: Unable to connect to remote host: Network is unreachable*，说明你的 vps 已经封堵了 25/tcp 的出端口
3. 封堵 25 端口的目的是为了防止垃圾邮件 ddos，通过下面的 postfix 配置可以发现，其可以自定义邮件的发件人，这就可以被利用来伪造和滥发，因此 vps 会要求使用受信任的 smtp 服务器来发件，这样就能有溯源的可能了
4. 题外话，分别使用 `nc -nvlp 1234` 和 `nc -e rootkit_addr 1234 -p 25` 是可以发现能正常通信的；但是 `nc -nvlp 25` 搭配 `nc -e rootkit_addr 25 -p 25` 的端口对端口就会被屏蔽了，可以用 `tcpdump -i eth0 port 25` 来观察通信过程
5. 除了自己搭建外，还可以选择第三方邮箱托管，例如 [zoho mail](https://www.zoho.com/mail/)，只需要一系列 dns 验证操作即可实现前文提到的自定义邮箱名，但是没必要再转发了

首先介绍一下三种主流的邮件协议：

1. Simple Mail Transfer Protocol（SMTP），**主要用于处理邮件的发送**，不涉及邮件的存储和管理，通常使用端口 25、587
2. Internet Message Access Protocol（IMAP），**主要用于从邮件服务器接收和管理邮件的协议**，是与邮件服务器之间的双向通信，允许用户从多个设备访问同一个邮箱，邮件保留在服务器上，用户可以在邮件客户端中查看邮件的同步状态（如未读、已读、标记等），通常使用端口 143、993
3. Post Office Protocol version 3（POP 3），**主要邮件接收协议**，用于从邮件服务器下载邮件到本地邮件客户端，通常使用端口 110、995

当网页通过邮箱的方式向你发送验证码时。首先是 SMTP 发送一封邮件，该邮件被互联网上一系列 SMTP 路由服务器转发，最终到达你的 @gmail.com 服务器，鉴权并存储；本地通过邮件客户端通过 IMAP 或 POP 3 协议访问 @gmail.com 服务器，下载或查看自己的邮件；当然现如今通过直接访问 gmail web 页面的方式称为 webmail，就是由厂商通过向你直接提供一个连接到自己服务器的方式来访问自己的邮件。

1. 首先在 dns 中添加一条 MX 记录，主机记录为 `@`，记录值为 `majo.im`；vps 防火墙开放 25/tcp 端口
2. 安装邮件服务器：`sudo apt install postfix`，对于 postfix configuration 第二项 system mail name 填写自己的域名，这里是 `majo.im`；为其配置开机自启动：`systemctl enable postfix`
3. 创建个人公私钥：

    1. 创建目录和文件：`mkdir /etc/postfix/cert`，`touch /etc/postfix/cert/mail.key`
    2. 生成私钥：`openssl genrsa -aes128 2048 > /etc/postfix/cert/mail.key`，输入一个密码作为 key
    3. 删除私钥中的密码：`openssl rsa -in /etc/postfix/cert/mail.key -out /etc/postfix/cert/mail.key`，再输入刚才的密码
    4. 生成证书签名请求：`openssl req -utf8 -new -key /etc/postfix/cert/mail.key -out /etc/postfix/cert/mail.csr`，以下内容是参考：

        ```bash
        You are about to be asked to enter information that will be incorporated
        into your certificate request.
        What you are about to enter is what is called a Distinguished Name or a DN.
        There are quite a few fields but you can leave some blank
        For some fields there will be a default value,
        If you enter '.', the field will be left blank.
        -----
        Country Name (2 letter code) [AU]:CN
        State or Province Name (full name) [Some-State]:Guangdong
        Locality Name (eg, city) []:Guangzhou
        Organization Name (eg, company) [Internet Widgits Pty Ltd]:majo
        Organizational Unit Name (eg, section) []:shell
        Common Name (e.g. server FQDN or YOUR name) []:mail.majo.im
        Email Address []:admin@majo.im

        Please enter the following 'extra' attributes
        to be sent with your certificate request
        A challenge password []:
        An optional company name []:
        ```
    5. 生成自签名证书文件：`openssl x509 -in /etc/postfix/cert/mail.csr -out /etc/postfix/cert/mail.crt -req -signkey /etc/postfix/cert/mail.key -days 3650`
    6. `/etc/postfix/cert/` 目录下应该有 mail.key、mail.csr 以及 mail.crt 三个文件
4. 配置 Postfix，编辑其配置文件 `vim /etc/postfix/main.cf` 参考如下，主要是最后几项：

    ```ini
    smtpd_relay_restrictions = permit_mynetworks permit_sasl_authenticated defer_unauth_destination
    alias_maps = hash:/etc/aliases
    alias_database = hash:/etc/aliases
    mailbox_size_limit = 0
    recipient_delimiter = +
    inet_interfaces = all
    inet_protocols = all
    virtual_alias_maps = hash:/etc/postfix/virtual

    # 中继目标, 也就是目标发送到哪个 SMTP 服务器
    relayhost = 
    # postfix 服务器的主机名 host, 在使用 mail -s 发送邮件时显示的 xxx@mail.majo.im 里的 mail.majo.im
    myhostname = mail.majo.im
    # postfix 服务器的域名
    mydomain = majo.im
    # 邮件在发送时的邮件地址, 即在发起转发时使用的 wkyuu@majo.im 里的 majo.im
    myorigin = majo.im
    # 邮件的目标地址
    mydestination = $myhostname, localhost.$mydomain, localhost, $mydomain, gmail.com
    mynetworks = 127.0.0.0/8 0.0.0.0/0
    ```
5. 配置邮件转发，`vim /etc/postfix/virtual`（可能需要创建），这将使得所有目标为 wkyuu@majo.im 的邮件都被转发到 wkyuu@gmail.com：

    ```ini
    wkyuu@majo.im wkyuu@gmail.com
    ```

    然后执行：`postmap /etc/postfix/virtual`，`systemctl restart postfix` 来应用更改
6. 测试：

    1. 输入 `echo "test" | mail -s "test mail" wkyuu@majo.im` 来向本地的 postfix 服务器发送一封邮件；如果不出意外的话在 @gmail.com 里就能看见自己的邮件了，如果迟迟不见邮件，那就是封堵了，这点在日志文件中可以看到 *Network is unreachable* 的字样
    2. 查看 postfix 的邮件日志 `/var/log/mail.log`
    3. 输入 `mailq` 可以查看当前 postfix 发送队列中的邮件，输入 `postsuper -d ALL` 删除这些邮件