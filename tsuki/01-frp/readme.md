## desc

使用 frp 内网穿透实现异地组建局域网

举个例子来说，某些游戏支持局域网联机（通俗点就是指连接了家里面同一个“路由器”的情况下两台机子就算组成了一个局域网了），但是如果想要和在异地的朋友一起进行局域网联机的话，就可以使用 frp 技术来实现这个异地组网过程。

## install

### pre

1. 部署：需要一个能连接得上的公网 IP 地址，对于大多数人来说，选购一台新人优惠下的云服务器会是不错的选择，并且云服务器在服务器提供商的管理下可以不关机运行，本文中使用的云服务器是 Linux 系统的，这里顺便贴一个选择带宽时的参考

   ```
   8Mbps
   = 8,000,000 bits per second
   = 8,000,000 / 8 = 1,000,000 bytes (1字节等于8位)
   = 1,000,000 / 1,000 = 1,000 kilo bytes per second = 1,000 kb/s
   ≈ 1mb/s (1024kb/s = 1mb/s)
   ```

   本人不仅用来搭建过 Minecraft 服务器，还有其他各种服务，这个带宽对于 Minecraft 开服人数较少时是够用的

2. 连接：两台 Windows 系统的主机，（这里的客户端不限，Linux、Windows、Mac等都可以，本人用的是两台 Windows）

### deploy

1. 获取安装包：到项目的 [fatedier/frp](https://github.com/fatedier/frp/releases) 上下载对应版本的项目 release 版本（[备选链接](https://mirrors.nju.edu.cn/github-release/fatedier/frp/)），这里要下两个，`frp_版本号_linux_指令架构.tar.gz` 和 `frp_版本号_windows_指令架构.tar.gz`

2. 将 `frp_linux.tar.gz` 通过 [ftp](https://www.majo.im/index.php/wkyuu/15.html) 服务传到 Linux 云服务器去（假设放在 `/root/` 目录下）

   ```bash
   sudo su
   
   # 找到刚刚上传的 tar.gz 文件，将其转到 /etc/frp/ 目录下（先创建）
   mkdir /etc/frp
   cp /root/frp_xxx_linux_xxx.tar.gz /etc/frp/
   
   cd /etc/frp
   tar -xvf frp_xxx_linux_xxx.tar.gz
   ```

3. 解压出来的一众文件，只需要关注 frp 服务端 `frps` 和服务端配置 `frps.ini` 两个文件即可。向 `frps.ini` 中填入以下内容（注意 `#` 是注释符号，便于解释记得删掉）

   ```ini
   [common]
   bind_port = 7000	# frp 服务的绑定端口
   # 上一行单独一行即可提供完整服务，从下一行开始是为了方便运维，查bug，可以不用加
   log_file = ./frps.log
   log_level = info
   log_max_days = 3
   ```

4. 修改并保存好内容后，只需要执行 `/etc/frp/frps -c /etc/frp/frps.ini` 即可，每次想要使用 frp 服务时，都要确保执行了 frps 进程，并且保证该进程不被 kill 掉

5. （可选内容，否则直接跳到 6）如果想将 frp 服务写入到系统进程，像执行 nginx 一样由 systemctl 来管理，则执行以下步骤：

   1. 在 `/etc/frp/` 文件夹下创建一个 `frp.service` 文件：`touch /etc/frp/frp.service`，并写入以下内容

      ```ini
      [Unit]
      Description=Frp Server
      Documentation=https://github.com/fatedier/frp
      After=network.target
      
      [Service]
      Type=simple
      User=root
      WorkingDirectory=/etc/frp/
      ExecStart=/etc/frp/frps -c /etc/frp/frps.ini
      ExecReload=/bin/kill -HUP
      ExecStop=ps aux |grep frps |grep -v grep |awk '{print $2}'|xargs  kill -9
      Restart=on-failure
      RestartPreventExitStatus=23
      
      [Install]
      WantedBy=multi-user.target
      ```

   2. 保存文件，并创建软链接：`ln -s /etc/frp/frp.service /usr/lib/systemd/system/frp.service`，刷新配置 `systemctl daemon-reload`，之后便可以使用 `systemctl` 来管理 frp 服务了

   3. 设置开机自启动：`systemctl enable frp`

   4. 启动、关闭、查看状态 frp 服务：`systemctl start/stop/status frp`

6. 由于云服务器安全组设置，需要到相应的安全面板开启对应的端口（可以在网上找怎么开），这里需要开启 `7000，7001，7002` 三个端口（根据实际情况），协议根据具体情况定，同时如果在本地还开了防火墙，也需要[放行相关端口](https://cloud.tencent.com/document/product/213/2502)

### usage

1. 将 `FRP_windows.tar.gz` 解压到 Windows 本地（这里是客户端 A）某个文件夹，得到众多文件，其中只需要关注 `frpc` 和 `frpc.ini` 两个文件
2. 修改 `frpc.ini` 文件

    ```ini
    [common]
    server_addr = 123.123.123.123	# 这里填公网IP，也可以填域名
    server_port = 7000	# 要和 frps.ini 的 bind_port 一致
    
    [server_1]	# 名字自己确定，要保证名字唯一
    type = tcp	# 单纯的局域网联机一般都是 tcp 和 udp，如果是访问网页就填 http，如果还不确定请网上搜索具体的
    local_ip = 127.0.0.1
    local_port = 25565	# 填具体想要开的端口，例如在 Minecraft 中单人游戏向局域网开启后，会显示“游戏已在 xxx 端口开放”，这里就填那个 xxx
    remote_port = 7001	# 代表 客户端A 通过 7001 端口与 云服务器，客户端B 共同形成了一个局域网。保证端口唯一
    
    [server_2]	# 可以自定义其他内容，确保 服务名字、端口 不被占用就行了
    ...
    ```
3. 同理，修改 客户端B 的 `frpc.ini` 设置（基本和 客户端A 一样，只修改了部分信息）

    ```ini
    [common]
    server_addr = 123.123.123.123
    server_port = 7000
    
    [server_x]	# 不能和 客户端A 中的任意一个服务名相同
    type = tcp
    local_ip = 127.0.0.1
    local_port = 123	# 这里任意填写
    remote_port = 7002	# 代表 客户端B 通过 7002 端口与 云服务器，客户端A 共同形成了一个局域网。
    
    [server_y]	# 可以自定义其他内容，确保 服务名字、端口 不被占用就行了
    ...
    ```
4. 修改完对应的 `frpc.ini` 文件并保存，`./frpc -c ./frpc.ini` 即可运行
5. 这里在使用 frp 进行组网时，要保证云服务器 frps、客户端 A frpc、客户端 B frpc 都打开着

## example

1. 想要通过内网穿透的方法实现 Minecraft 联机：就拿安装过程中各项设置，实现 Minecraft 联机为例子

   1. 局域网联机，云服务器（ ip 为 `123.123.123.123`）搭建好了 `frps服务（放在7000端口，这个是服务的端口，是必要的）`，并开放了供客户端连接的端口 `7001、7002`
   2. 客户端 A 打开了 Minecraft 游戏，向局域网开放在了 25565 端口，其 `frpc.ini` 中的 `local_port = 25565；remote_port = 7001`。表示 客户端 A 通过 `客户端A的 25565 端口` 连接到了 `云服务器的 7001 端口`，它们之间形成了一个局域网，服务器想要访问客户端A 就通过服务器自己的 7001 端口到达客户端A的 25565 端口，即可访问 客户端A 提供的 Minecraft 局域网联机服务（类似于隧道）
   3. 客户端 B 通过多人游戏中的直接连接，填入 `123.123.123.123:7001`。接下来首先 客户端 B 通过 `客户端B的 123 端口` 与 `云服务器的 7002 端口` 绑定。当 客户端B 想要访问 客户端A 就发生 `客户端B的 123 端口 -> 云服务器的 7002 端口 -> 云服务器的 7001 端口 -> 客户端A的 25565 端口`，这样通过切换这几种 隧道，就能实现虚拟局域网了（反过来也同理）
   4. 本地主机作服务器
      1. 基本配置同理，这里用 客户端A 当作 server（体现在使用的 Minecraft 端是名为 server.jar 的），使用的启动指令是 `java -Xmx1G -jar server.jar --port 1234 --nogui`，这表明服务器开在了 1234端口
      2. 按照上一步的原理展示，你大概能明白只需要在 客户端A 的 `frpc.ini` 中将某一 `local_port = 1234; remote_port = 7001` 即可
      3. 对于其他的 客户端BCDEF，都是确保 `frpc.ini 占用不同 remote_port，不同服务名`，`云服务器相应的 remote_port 保证正常可用`，`客户端A在开服的时候，不关闭那个启动 frpc.exe 的 命令行端口，以及执行 java server.jar ... 的 命令行端口`，这样基本就没有什么问题了

2. 想要通过 frp 内网穿透来传文件

   一个简单的场景就是，本人在办公室放置了一台较大存储空间的不断电 `Linux 主机 A`，利用 `任意想访问 A 的机器 B`，`作为 frps 部署服务的云服务器 C`，实现了"在家也能访问办公室里的文件"。（也可以通过这个方式访问本地的 NAS）

   1. 开启 `Linux 主机A` 上的 `frpc` 服务，`frpc.ini` 文件内容如下

      ```ini
      [common]
      server_addr = 123.123.123.123
      server_port = 7000
      
      [Linux_A]
      type = tcp
      local_ip = 127.0.0.1
      local_port = 11451	# 一定要保证端口一一对应
      remote_port = 7001
      ```

      使用 `/etc/frp/frpc /etc/frp/frpc.ini` 来开启 frpc 服务，同时还要确保开启了这个 frpc 的 shell 不要被关掉（可以写到 systemctl 中）

   2. 将 `Linux 主机A` 上某个想要开放访问的文件夹通过 SMB/WebDav/FTP 等类型服务开启映射

   3. `云服务器 C` 部署 `frps` 服务并且保证 全部涉及到的端口正常使用，部署方法略

   4. `某机器 B` 通过支持 webdav 的应用访问 `123.123.123.123:7001` 即可；或者在浏览器中访问 `http://123.123.123.123:7001`，也可以看到相应的文件夹映射

## refer

1. [frp 项目的 github](https://github.com/fatedier/frp)
2. [南京大学镜像站](https://mirrors.nju.edu.cn/github-release/fatedier/frp/)