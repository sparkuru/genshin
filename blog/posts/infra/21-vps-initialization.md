---
title: "init-a-new-vps-host"
description: "goodbye, my old friend."
date: "2024-03-28T12:22:00.000Z"
updated: "2024-11-26T06:54:24.000Z"
tags: []
draft: false
layout: "post"
slug: "vps-initialization"
---

我的阿里云新人优惠 99rmb/year 的服务器在续费了三年以后，终于要迎来了到期的日子，感谢阿里云为学生、个人开发者们提供的上云机会，这几年以来我本人也因此变得越来越具备独立思考和信息检索的能力，这对于一名 cs 专业的学生来说真的太重要了。折腾在阿里云这里的主机的这段日子，我还尝试了阿里云提供的各种服务，类似 OSS 对象存储、dns 服务等，他们处理事务准确高效，态势感知做的很棒。今后我也仍会继续选择阿里云，并且积极向学弟学妹们推荐阿里云。

当前使用的 host 配置为 2c2g、1Mbps，这样的配置对于有了几年服务器折腾经验的我来说显得捉襟见肘了些，因此也是借着这个更新换代的机会将服务器迁移到阿里云的香港区，就凭他价格亲民，配置合适。

本文介绍初始化 & 迁移历程，也算是对过去的承上和对新未来的启下了。也可以为想要配置新 Linux 系统的人们提供一个参考。

## init

这里以 ubuntu 22.04，2c2g、30Mbps 为例；默认用户名是 admin，主机名是 `4RDyINeM1GQ6gaZj7VWuboXxwYLCJmH`，对应修改成 wkyuu 和 `vps`；并且添加一些个人用起来比较舒服的应用。

1. 使用控制台登录系统，修改密码：`passwd root`，`passwd admin`
2. 修改用户名称、主机名称：

    1. 使用 root 登录，关闭所有 admin 起的进程：`sudo su`，`pkill -9 -u admin`
    2. 改名：`sudo usermod -l wkyuu admin`
    3. 更新 `/home/admin` 名称为 `/home/wkyuu`：`usermod -d /home/wkyuu -m wkyuu`
    4. 修改组名：`sudo groupmod -n wkyuu admin`，使用 `id` 查看结果：
    5. 修改 sudoers 文件：`sudo su`，`visudo`，找到所有 `admin` 选项修改成 `wkyuu`；（可选）配置免密登录：在 `%sudo ALL=(ALL:ALL) ALL` 下方加入一行 `wkyuu ALL=(ALL:ALL) NOPASSWD:ALL`
    6. 修改主机名：修改 `/etc/hostname`、`/etc/hosts` 中旧主机名的部分为 `vps`
3. （可选）也可以新增用户：

    1. 先创建组：`groupadd -g 1001 wkyuu`
    2. `useradd -s /usr/bin/zsh -g wkyuu -G adm,cdrom,users,sudo -u 1001 -d /home/wkyuu -m wkyuu`，新增用户，指定 shell 解释器、组名、添加到的其他组名、uid、home 目录，（这里在添加组权限时，可能遇到不存在 sudo 组的问题，具体情况具体分析，可以改成 wheel 组，具体以 `cat /etc/group` 为准）
    3. `passwd`，改密码
4. 将个人公钥复制到对应文件中 `~/.ssh/authorized_keys`，root 和 wkyuu 都要

    1. 个人公钥文件：`wget -O ~/.ssh/autohrized_keys https://paste.majo.im/raw/efolavulal`
    2. `/root/.ssh` 对应权限如下：

        ```bash
        drwx------  2 root root 4.0K Mar 28 01:06 .	# .ssh
        drwx------ 10 root root 4.0K Mar 28 10:03 ..
        -rw-------  1 root root  571 Mar 28 01:06 authorized_keys
        ```

        `chmod -R 700 /root/.ssh`
    3. `~/.ssh` 对应权限：

        ```bash
        drwx------ 2 wkyuu wkyuu 4.0K Mar 28 01:34 .	# .ssh
        drwxr-x--- 4 wkyuu wkyuu 4.0K Mar 28 09:57 ..
        -rw------- 1 wkyuu wkyuu  570 Mar 28 01:34 authorized_keys
        ```

        `chmod -R 700 ~/.ssh`
    4. 检查 `/etc/ssh/sshd_config` 文件，主要是以下几项，可以直接替换该文件：

        ```ini
        # Port 22
        # AddressFamily any
        # ListenAddress 0.0.0.0
        # ListenAddress ::

        Include /etc/ssh/sshd_config.d/*.conf

        AddressFamily inet
        X11Forwarding yes
        UsePAM yes
        UseDNS no

        SyslogFacility AUTHPRIV
        PermitRootLogin yes	# 允许 root 登录
        PasswordAuthentication no	# 禁止密码登录
        KbdInteractiveAuthentication no

        PrintMotd no
        AcceptEnv LANG LC_*
        Subsystem sftp /usr/lib/openssh/sftp-server
        ```

        `systemctl start sshd && systemctl enable sshd`
5. 安装 zsh：

    1. 首先换源，这里换 ubuntu 22.04 ustc 的源，其他自助，`cp /etc/apt/source.list /etc/apt/source.list.backup`，`vim /etc/apt/source.list`：

        ```ini
        deb https://mirrors.ustc.edu.cn/ubuntu/ jammy main restricted universe multiverse
        deb-src https://mirrors.ustc.edu.cn/ubuntu/ jammy main restricted universe multiverse

        deb https://mirrors.ustc.edu.cn/ubuntu/ jammy-security main restricted universe multiverse
        deb-src https://mirrors.ustc.edu.cn/ubuntu/ jammy-security main restricted universe multiverse

        deb https://mirrors.ustc.edu.cn/ubuntu/ jammy-updates main restricted universe multiverse
        deb-src https://mirrors.ustc.edu.cn/ubuntu/ jammy-updates main restricted universe multiverse

        deb https://mirrors.ustc.edu.cn/ubuntu/ jammy-backports main restricted universe multiverse
        deb-src https://mirrors.ustc.edu.cn/ubuntu/ jammy-backports main restricted universe multiverse
        ```

        当然也可以快速换源：`sed -i 's|http://archive.ubuntu.com/ubuntu/|http://mirrors.ustc.edu.cn/ubuntu/|g' /etc/apt/sources.list && sed -i 's|http://security.ubuntu.com/ubuntu/|http://mirrors.ustc.edu.cn/ubuntu/|g' /etc/apt/sources.list`
    2. 更新：`sudo apt update`
    3. 获取 zsh：`sudo apt install zsh`，找到具体位置：`which zsh`
    4. 配置默认 shell：`chsh -s /usr/bin/zsh`，root 和 wkyuu 都要
    5. 修改配置文件 `touch ~/.zshrc`，配置文件放在这里 `https://paste.majo.im/orihizulay.bash`，一键配置：`curl https://paste.majo.im/raw/orihizulay > ~/.zshrc`，root 和 wkyuu 都要
6. 配置 python 3.12 +，杀软 python 3.12，喜欢教用户怎么用 pip 安装包文件，不是给用户选择，而是粗暴的一刀切，去你妈的一个脚本语言搞一大堆虚拟环境。强制去掉  *× This environment is externally managed* 的提示的方法：`sudo mv /usr/lib/python3.12/EXTERNALLY-MANAGED /usr/lib/python3.12/EXTERNALLY-MANAGED.backup`
7. 配置 git

    1. 查看 git 默认配置：`git config -l`
    2. 设置常用内容：

        ```bash
        git config --global user.email wkyuu@majo.im
        git config --global user.name shiguma
        git config --global credential.helper store
        git config --global init.defaultbranch main
        git config --global core.editor vim
        ```
    3. 如果设置错了，输入 `git config --global --unset xxx` 来解除
8. 其他可选的 apt 安装内容：`apt install -y curl vim docker.io docker-compose python3-venv python3-shodan gnupg2 software-properties-common build-essential net-tools binutils file xxd nmap fd-find openvpn fzf ripgrep`

    1. 安装 nodejs：`curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && apt-get install -y nodejs`，`npm install -g npm@latest`，`npm install cnpm -g --registry=https://registry.npmmirror.com`，然后安装 pm2：`cnpm install -g pm2`
    2. `
9. （可选）DNS 配套设施

    1. 我在 Dynadot 注册的域名，在使用 acme.sh 进行 dns 方式通过 api_token 注册时，没有发现官方提供的脚本，兜兜转转找到别人提出的 [issue](https://github.com/acmesh-official/acme.sh/pull/4510#issuecomment-1868287264)，因此决定将 majo.im 保留在 dynadot，但是 dns 服务商修改成 aliyun；如果读者的域名也没有相关支持，我也推荐转移到 aliyun、dnspod、cloudflare（如果主要面向海外用户的话）等，相关迁出过程网上很多，这里就不再重复了；**请注意，dns 服务商和域名持有商不是一个概念，以上提到的是 dynadot 保留有 majo.im，续费也在 dynadot，但是配置 dns 解析的时候是在 aliyun；** 以下内容会以 aliyun 上的 majo.im 为准
    2. 为了方便后文可以检验 SSL 添加结果，需要先创建一个 web 服务，使用 nginx、apache 之类的都可以，这里以 nginx 为例：

        1. 安装 nginx 服务：`sudo apt install nginx`，添加开机自启动：`sudo systemctl enable nginx`
        2. 在 dns 中，将域名解析到自己的 ip
        3. 配置服务，可以用以下临时配置文件来快速搭建：`/etc/nginx/sites-available/default`：

            ```bash
            server {
            	listen 80;
            	listen [::]:80;

            	server_name www.majo.im;	# 修改成自己的域名

            	root /srv/www/typecho;
            	index index.html;

            	location / {
            		try_files $uri $uri/ =404;
            	}
            }
            ```

            然后创建一个主页文件用来验证：`echo "hello" > /srv/www/typecho/index.html`，热重载 nginx：`sudo nginx -s reload`
        4. 访问 `http://www.majo.im` 即可看到结果
    3. 自动更新证书服务：[acmesh-official/acme.sh](https://github.com/acmesh-official/acme.sh.git)，这里使用 dns 方式生成证书（下文内容客制化更改 domain 信息）

        1. `sudo mkdir -p /opt/workspace/acme`，`sudo chown wkyuu:wkyuu -R /home/app`
        2. 获取以及安装：`curl https://get.acme.sh | sh -s email=my@example.com`，后面的 `email` 填自己注册的邮箱
        3. `cd /opt/workspace/acme`，`mkdir cert`，`sudo ln -s /opt/workspace/acme/cert /etc/nginx/cert`
        4. 正式签发，有两种方式

            1. **（完全自动，十分推荐）** 创建一个脚本文件：`touch /opt/workspace/acme/script.sh`，填入以下内容（以下脚本需要按照具体情况来弄，但是如果你是按照我前文的配置，则基本只需要修改 `wkyuu` 为自己的用户名，以及 `majo.im` 修改成自己的域名），注意要修改其中的 api 相关信息（检索关键词 acme dns + 注册商）：

                ```shell
                #!/bin/sh

                function color() {
                    echo -e "\e[33m$1\e[0m"
                }

                workdir="/opt/acme"
                home_acme_dir="$HOME/.acme.sh"
                DOMAIN='domain.top'
                SUB_DOMAIN_LIST=(   # 泛域名
                    '\*'
                )
                KEY_FILE_PATH="$workdir/cert/$DOMAIN.key"
                CERT_FILE_PATH="$workdir/cert/$DOMAIN.cer"
                FULLCHAIN_FILE_PATH="$workdir/cert/fullchain.cer"

                if [ ! -d "$home_acme_dir" ]; then
                    cmd="curl https://get.acme.sh | sh -s email=my@example.com"
                    color "no $home_acme_dir found, run $cmd first."
                    exit
                fi

                if [ ! -d $workdir ]; then
                    mkdir -p $workdir
                fi

                cd $workdir
                . "$home_acme_dir/acme.sh.env"

                export Ali_Key="xxxxx"   # 参考这篇文章：https://blog.csdn.net/chen249191508/article/details/98088553
                export Ali_Secret="xxxxx"  # AccessKey ID 就是 Ali_Key，AccessKey Secret 就是 Ali_Secret

                if [[ $1 == 'issue' ]]; then
                    base_cmd="acme.sh --issue --dns dns_ali -d $DOMAIN --force"
                    for sub in "$SUB_DOMAIN_LIST[@]"; do
                        base_cmd+=" -d $sub.$DOMAIN"
                    done
                fi

                # $DOMAIN.cer 是证书文件, $DOMAIN.key 是密钥文件, fullchain.cer 是全链接文件
                if [[ $1 == 'install' ]]; then
                    reloadcmd="sudo systemctl restart nginx"
                    base_cmd="acme.sh --install-cert --key-file $KEY_FILE_PATH --cert-file $CERT_FILE_PATH --fullchain-file $FULLCHAIN_FILE_PATH --reloadcmd '$reloadcmd' -d $DOMAIN"
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

                1. 后续操作，都是以该脚本为主；举例输入 `./script.sh issue`，则会输出将要执行的指令，输入 `./script.sh issue run`，则确认执行
                2. 在 `SUB_DOMAIN_LIST` 项中，填写自己想要签发的二级域名，例如这里目标生成了 `majo.im`（默认生成的）、`www.majo.im` 以及 `ftp.majo.im`；推荐使用 `\*` 生成 `*.majo.im` 泛域名，这样在新增二级域名时就不需要重新签发了
                3. 域名控制台相关内容如下（如果配置的是 `*.majo.im` 则随意添加二级域名的 A 记录）：

                    | 记录 | 类型 | 值      |
                    | ------ | ------ | --------- |
                    | @    | A    | 你的 ip |
                    | www  | A    | 你的 ip |
                    | ftp  | A    | 你的 ip |
                    | xxx  | A    | 你的 ip |
            2. **（到期了需要手动自己再添加）** 创建一个脚本文件：`touch /opt/workspace/acme/scripts.sh`，填入以下内容（以下脚本需要按照具体情况来弄，但是如果你是按照我前文的配置，则基本只需要修改 `wkyuu` 为自己的用户名，以及 `majo.im` 修改成自己的域名）：

                ```shell
                #!/usr/bin/zsh
                cd /opt/workspace/acme
                . "~/.acme.sh/acme.sh.env"

                # ./scripts.sh > log 2>&1

                function color() {
                    echo -e "\e[33m$1\e[0m"
                }

                DOMAIN='majo.im'
                SUB_DOMAIN_LIST=(
                    'www' 'ftp'
                )
                KEY_FILE_PATH="/opt/workspace/acme/cert/majo.im.key"
                FULLCHAIN_FILE_PATH="/opt/workspace/acme/cert/fullchain.cer"

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

                1. 执行 `/opt/workspace/acme/scripts.sh issue run`，会返回好几条数据，参考以下输出：

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
                2. 执行 `/opt/workspace/acme/scripts.sh renew run`，签发和验证成功会输出相关提示，签发完成后，可以在 `/opt/workspace/acme/.acme.sh/majo.im_ecc` 下找到相关 csr、cer、key 文件；
                3. 执行 `/opt/workspace/acme/scripts.sh install run`，则会将相关文件安装到 `/opt/workspace/acme/cert` 中，也会同时安装到 `/etc/nginx/cert` 中
                4. 其实前一种完全自动的方式，就是为你自动执行了下面这块的步骤，仅需要一个 dns api
            3. 手动更新 acme：如果发现上面的自动更新签发的行为没生效，还是需要手动进行更新 `./script.sh issue`
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

                root /srv/www/typecho;
            	server_name majo.im;
            	server_name www.majo.im;

                ...
            }
            ```
