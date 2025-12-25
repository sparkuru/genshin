# bitcomet in docker for linux

docker 配置文件修改参考, bitcomet for Linux 安装 [参考](http://wiki-zh.bitcomet.com/linux版bitcomet安装指南)，在 docker 化需求下，我使用 docker-compose 将其启动，下面是我的配置文件参考：

```yaml
version: "3"

services:
  bitcomet:
    container_name: bitcomet
    image: wxhere/bitcomet:latest
    volumes:
      # mounts a host directory into the container to store config files
      - /home/app/bitcomet/appdata:/home/sandbox/.config/BitComet:rw
      # mounts a host directory into the container to store downloaded files
      - /home/app/bitcomet/downloads:/home/sandbox/Downloads:rw
    ports:
      - 9448:5900 # VNC GUI port
      - 9449:80 # Web GUI port
      - 9450:6082 # BitTorrent ports
      - 9450:6082/udp
    environment:
      - VNC_PASSWORD=lYR6Bm3iKm2FDxB
      - HTTP_PASSWORD=o3DdVD6quQ76S34
      - USER=sandbox
      - PASSWORD=o3DdVD6quQ76S34

# sudo docker-compose -f /home/app/bitcomet/bitcomet.yml up -d
```

配置文件中指定了几个端口映射，但是由于其本身使用到了 novnc，且指定启动于其内部的 5900 端口，在尝试通过 9449 连接到其 http gui 服务时，出现了 5900 不可达的情况，http 本身并不会通过指定的 9448 去转接到 5900，另外查阅了其官方资料后也没有找到可以指定 `VNC_PORT` 的配置，因此需要手动修改其配置文件，以下是参考思路，理论上可以应用于所有无法在 docker 启动时自动指定的情况。

1. 首先正常启动该 docker 镜像：`sudo docker-compose -f /home/app/bitcomet/bitcomet.yml up`
2. 连接到 docker 的 shell：`sudo docker exec -u root -it docker_id /bin/bash`，这里的 docker_id 通过 `docker ps` 查看
3. 查看所有运行的进程 `ps -aux`，输出如下：

    ```bash
    root@1c35c2ccef22:~# ps -aux
    USER         PID %CPU %MEM    VSZ   RSS TTY      STAT START   TIME COMMAND
    root           1  0.0  0.0   2500   588 ?        Ss   08:49   0:00 /bin/tini -- supervisord -n -c /etc/supervisor/supervisord.conf
    root          22  0.1  0.5  28400 23568 ?        S    08:49   0:00 /usr/bin/python3 /usr/bin/supervisord -n -c /etc/supervisor/supervisord.conf
    root          24  0.0  0.2  57316 11316 ?        S    08:49   0:00 nginx: master process nginx -c /etc/nginx/nginx.conf -g daemon off;
    root          25  0.0  0.7 112012 29440 ?        Sl   08:49   0:00 python3 /usr/local/lib/web/backend/run.py
    root          26  9.3  1.3 720768 55576 ?        Sl   08:49   0:34 /usr/bin/Xvfb :1 -screen 0 1536x738x16
    sandbox       27  0.0  0.7 233752 30120 ?        Sl   08:49   0:00 lxqt-session
    root          28  0.2  0.2  34440 11936 ?        S    08:49   0:00 x11vnc -display :1 -xkb -forever -shared -repeat -capslock -rfbauth /.password2 -rfbauth /.password2
    root          29  0.0  0.0   4132  2936 ?        S    08:49   0:00 bash /usr/local/lib/web/frontend/static/novnc/utils/launch.sh --listen 6081
    www-data      33  0.0  0.0  57676  3320 ?        S    08:49   0:00 nginx: worker process
    root          50  0.0  0.4  22028 17004 ?        S    08:49   0:00 python /usr/local/lib/web/frontend/static/novnc/utils/websockify/run --web /usr/local/lib/web/frontend/static/novnc 6081 localhost:5900
    sandbox       56  0.0  0.0   7024  2340 ?        S    08:49   0:00 dbus-launch --sh-syntax --exit-with-session
    sandbox       57  0.0  0.0   6984  3096 ?        Ss   08:49   0:00 /usr/bin/dbus-daemon --syslog --fork --print-pid 5 --print-address 7 --session
    sandbox       67  0.0  0.4  66400 18260 ?        S    08:49   0:00 /usr/bin/openbox --config-file /home/sandbox/.config/openbox/lxqt-rc.xml
    sandbox       70 23.9  5.1 104551672 206556 ?    Sl   08:49   1:27 /home/sandbox/BitCometApp/usr/bin/BitComet
    sandbox       71  0.0  1.6 1226728 67592 ?       Sl   08:49   0:00 /usr/bin/pcmanfm-qt --desktop --profile=lxqt
    sandbox       72  0.0  0.6 307252 26604 ?        Sl   08:49   0:00 /usr/bin/lxqt-globalkeysd
    sandbox       73  0.0  0.6 233260 27036 ?        Sl   08:49   0:00 /usr/bin/lxqt-notificationd
    sandbox       74  0.0  1.6 925992 65500 ?        Sl   08:49   0:00 /usr/bin/lxqt-panel
    sandbox       75  0.0  0.7 233512 28060 ?        Sl   08:49   0:00 /usr/bin/lxqt-policykit-agent
    sandbox       76  0.0  0.8 236532 32976 ?        Sl   08:49   0:00 /usr/bin/lxqt-runner
    sandbox      158  0.2  3.9 103279868 156560 ?    SLl  08:49   0:00 /usr/lib/x86_64-linux-gnu/webkit2gtk-4.0/WebKitWebProcess 7 39
    sandbox      159  0.0  1.4 86442332 56300 ?      SLl  08:49   0:00 /usr/lib/x86_64-linux-gnu/webkit2gtk-4.0/WebKitNetworkProcess 8 39
    sandbox      185  0.2  2.5 85747048 103104 ?     SLl  08:49   0:00 /usr/lib/x86_64-linux-gnu/webkit2gtk-4.0/WebKitWebProcess 16 45
    sandbox      197  0.0  2.0 85700328 82104 ?      SLl  08:49   0:00 /usr/lib/x86_64-linux-gnu/webkit2gtk-4.0/WebKitWebProcess 23 52
    sandbox      200  0.0  1.7 102476820 68276 ?     SLl  08:49   0:00 /usr/lib/x86_64-linux-gnu/webkit2gtk-4.0/WebKitWebProcess 29 55
    sandbox      267  0.0  0.6 234496 26740 ?        Sl   08:50   0:00 /usr/bin/lxqt-powermanagement
    sandbox      269  0.0  0.6 230436 27812 ?        Sl   08:50   0:00 /usr/bin/qlipper
    root         368  0.0  0.0   4248  3496 pts/0    Ss   08:54   0:00 /bin/bash
    root         402  0.0  0.0   5888  2744 pts/0    R+   08:55   0:00 ps -aux
    ```
4. 通过以上输出，大概可以了解到几个点，和追踪到启动链

    1. `/bin/tini` 和 `supervisord`，用于在启动 docker 时执行的一系列脚本，相当于 rc
    2. `nginx`，`python3`，`lxqt`，`x11vnc`，`xvfb`，`webkit` 就是 bitcomet 通过 http 管理的一套工具链
    3. 根据 `python /usr/local/lib/web/frontend/static/novnc/utils/websockify/run --web /usr/local/lib/web/frontend/static/novnc 6081 localhost:5900` 可以得知 novnc 监听着 5900 上的 vnc 服务，而通过 `netstat -anp | grep 5900` 可以观察到该端口被 28/x11vnc 占用，因此目的就是修改 x11vnc 的启动指令
5. 观测 `cat /etc/supervisor/supervisord.conf` 文件可以得知，其引入了 `/etc/supervisor/conf.d/*.conf` 下的文件，进一步获取 `cat /etc/supervisor/conf.d` 得到以下配置文件，现在将其下载到主机里：`docker cp docker_id:/etc/supervisor /home/app/bitcomet/supervisor`，后续可以直接在外部修改这个文件来控制 docker 内部关键参数。**之所以先启动后再获取内部配置文件，是因为防止后续再次启动时如果挂载了一个空文件（夹）会导致内部文件丢失**
6. 参考 x11vnc 的 [配置](https://linux.die.net/man/1/x11vnc)，需要在原配置的情况下新增 `-autoport` 来指定新的 port，最终完整配置文件 `/home/app/bitcomet/supervisor/conf.d/supervisord.conf` 如下：

    ```ini
    [supervisord]
    redirect_stderr=true
    stopsignal=QUIT
    autorestart=true
    directory=/root

    [program:nginx]
    priority=10
    command=nginx -c /etc/nginx/nginx.conf -g 'daemon off;'

    [program:web]
    priority=10
    directory=/usr/local/lib/web/backend
    command=/usr/local/lib/web/backend/run.py
    stdout_logfile=/dev/fd/1
    stdout_logfile_maxbytes=0
    stderr_logfile=/dev/fd/1
    stderr_logfile_maxbytes=0


    [group:x]
    # programs=xvfb,wm,lxpanel,pcmanfm,x11vnc,novnc
    programs=xvfb,lxpanel,x11vnc,novnc

    # [program:wm]
    # priority=15
    # command=/usr/bin/openbox
    # environment=DISPLAY=":1",HOME="/root",USER="root"

    [program:lxpanel]
    priority=15
    directory=/home/sandbox
    command=/usr/bin/startlxqt
    user=sandbox
    environment=DISPLAY=":1",HOME="/home/sandbox",USER="sandbox"

    # [program:pcmanfm]
    # priority=15
    # directory=/home/sandbox
    # command=/usr/bin/pcmanfm --desktop --profile LXDE
    # user=sandbox
    # environment=DISPLAY=":1",HOME="/home/sandbox",USER="sandbox"

    [program:xvfb]
    priority=10
    command=/usr/local/bin/xvfb.sh
    stopsignal=KILL

    [program:x11vnc]
    priority=20
    command=x11vnc -display :1 -xkb -forever -shared -repeat -capslock -rfbauth /.password2 -rfbauth /.password2 -autoport 9448

    [program:novnc]
    priority=25
    directory=/usr/local/lib/web/frontend/static/novnc
    command=bash /usr/local/lib/web/frontend/static/novnc/utils/launch.sh --listen 6081 --vnc localhost:9448
    stopasgroup=true

    ```

    主要修改了 `[program:x11vnc]` 和 `[program:novnc]` 下的 command
7. 新的 docker-compose.yml 配置文件如下：

    ```yaml
    version: "3"

    services:
      bitcomet:
        container_name: bitcomet
        image: wxhere/bitcomet:latest
        volumes:
          - /home/app/bitcomet/appdata:/home/sandbox/.config/BitComet:rw
          - /home/app/bitcomet/downloads:/home/sandbox/Downloads:rw
          - /home/app/bitcomet/supervisor:/etc/supervisor
        ports:
          - 9448:9448 # VNC GUI port
          - 9449:80 # Web GUI port
          - 9450:6082 # BitTorrent ports
          - 9450:6082/udp
        environment:
          - VNC_PASSWORD=lYR6Bm3iKm2FDxB
          - HTTP_PASSWORD=o3DdVD6quQ76S34
          - UID=1000
          - GID=1000
          - USER=sandbox
          - PASSWORD=o3DdVD6quQ76S34

    # sudo docker-compose -f /home/app/bitcomet/bitcomet.yml up -d
    ```
8. 此时再重新启动之即可通过 `http://localhost:9449` 访问到 bitcomet in docker for linux 了

## ssl

通过 nginx 反代的方式访问 docker，并且搭配 ssl，可以按照以下配置：

```nginx
server {
    listen 443 ssl ;
    server_name bit.example.com ;
    client_max_body_size 500M;
    location / {
        proxy_pass http://127.0.0.1:9449 ;
        proxy_redirect http://127.0.0.1:9449 https://bit.example.com ;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection $connection_upgrade;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Protocol $scheme;
        proxy_set_header X-Forwarded-Host $http_host;
        proxy_set_header REMOTE-HOST $remote_addr;
    }
}
```

可以发现需要 websocker 升级，添加即可