---
title: "dev | linux-handbook"
description: "tips while using ubuntu and references for other debian like distribution."
date: "2022-03-17T11:41:00.000Z"
updated: "2024-03-28T12:21:48.000Z"
tags: []
draft: false
layout: "post"
slug: "linux-handbook"
---

## linux-handbook

>   本文章的内容基于 **ubuntu 18.04 LTS** 编写
>
>   记录自己接触 Linux 历程中的各类指令和问题

## 让系统跑起来

### install

**ubuntu 18.04** 系统到 [这里](https://releases.ubuntu.com/18.04/) 下载，进入页面后找到 `ubuntu-18.04.6-desktop-amd64.iso` 点击下载即可

这里使用的是 VMware Workstation 虚拟环境搭建系统，在物理机上安装的流程大致相同

### localization

>   update package sources，更新包管理器源

也可以理解为，为了更好地在国内使用而进行一些能明显提升个人在使用 ubuntu 时的幸福感的操作

这里的操作目的是，在使用 debian 系的 Linux 系统时，一般会使用自带的 apt-get 包管理器，这些包管理器会有专门的软件源，ubuntu 在默认安装时其 source.list 文件中源大多数是比较慢的，因此需要将其修改成国内的源

1.   备份 sources.list 文件：`sudo cp /etc/apt/sources.list /etc/apt/sources.list.bak`
2.   更新 sources.list 文件：`sudo gedit /etc/apt/sources.list`；具体的软件源可以通过搜索引擎获得，这里给出个人比较喜欢的一个国内源，[ustc](https://mirrors.ustc.edu.cn/help/ubuntu.html)，进入后按照所描述的更新方式来修改软件源内容即可
3.   `sudo apt-get update`

如果出现 **您使用的镜像正在同步中** 的字样，则删除 apt.conf.d 文件夹下所有文件：`sudo rm /etc/apt/apt.conf.d/*`，然后继续所进行的操作

>   change system language to Chinese，修改系统语言为中文

1.   使用图形化界面修改（推荐）：
     1.   输入 `sudo dpkg-reconfigure locales`，会出现一个图形框；
     2.   使用 **方向下键** 或者 **pagedown** 键，一直往下拉，直到找到 `zh_CN.UTF-8`，按下 **空格键（space）** 选中
     3.   最后按下 **tab** 将光标切换到下面的确认按钮，然后 **回车**
2.   手动修改语言：
     1.   安装中文语言包：`sudo apt install language-pack-zh-hans`
     2.   更新中文语言：`sudo update-locale LANG=zh_CN.UTF-8`

注意，在一些情况下，当修改了语言后重启系统，可能会出现是否要将 **英文名的文件夹** 重命名为 **中文名的文件夹** 的情况，建议是 **不要重命名**

## apt-get

>   作为 debian 的统一包管理器，下面会给出一些比较常用的与该命令相关的配置

在下文中 `xxx` 表示要操作的对象软件名

### installs

安装软件，其中 apt 和 apt-get 的关系大致上是可以不用很细致区分，大多数场景下 apt 和 apt-get 两个指令可以互相混合使用

1.   最基础的安装指令：`sudo apt-get install xxx`
2.   有时候会出现软件包不兼容的情况，这时候需要用到更高级的包管理器：`sudo aptitude install xxx`，这个包管理器可以帮助解决兼容性问题
3.   使用代理：`sudo apt-get -o Acquire::http::proxy="http://127.0.0.1:7890" install xxx`

### uninstalls

卸载一些不想要了的软件包，详细内容请参阅：[参考链接](https://blog.csdn.net/get_set/article/details/51276609)，以下给出一些比较常用的指令

1.   仅卸载软件：`sudo apt-get remove xxx`
2.   卸载软件及其配置文件：`sudo apt-get --purge remove xxx`
3.   删除一些冗余包，即使不需要这些包，已经安装好的软件也能正常运行：`sudo apt-get autoremove`
4.   删除下载软件时的安装包文件：`sudo apt-get autoclean`，这个操作会把 `/var/cache/apt/archives/` 目录下过期了的 `*.deb` 包文件给清理

### others

一些比较常用的软件

>   glibc-things

一些软件在使用时会要求需要 glibc 开发编译环境，可以通过 apt 来安装

`sudo apt-get install libc-dev`

>   docker

容器化技术 docker，docker-compose

`sudo apt-get install docker.io docker-compose`

>   nodejs

nodejs 是 javascript 语言的运行时；有时候一些环境会要求使用 npm 等工具安装，这里的 npm 就是 nodejs 的包管理器

1.   通过官方网站获取安装信息：`curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -`；由于 ubuntu 的 apt 包默认的 nodejs 版本较低，在碰到一些比较新的框架时，会有 nodejs 版本的要求，所以这里推荐安装 nodejs 18.x
2.   通过第一步更新了 apt 源后，再安装：`sudo apt-get install nodejs`，或者使用代理：`sudo apt-get -o Acquire::http::proxy="http://127.0.0.1:7890" install nodejs`
3.   镜像加速 cnpm：`npm install cnpm -g --registry=https://registry.npmmirror.com`，然后后续使用 cnpm 来代替 npm 命令，这是一个会优先使用国内镜像来加速下载的指令，基本功能与 npm 一致，在后续使用到 npm 时，都可以将其直接修改成 cnpm 来运行

>   python

默认情况下，ubuntu 自身就包含了比较新的 python 3.x 环境以及 python 2.7，并且其默认输入 python 时使用的是 python 3，这里提供一些在使用 python 时可能会遇到的问题

1.   修改 pip 默认源，其作用也是为了加速包下载速度：

     1.   创建 `~/.pip/pip.conf` 文件：`mkdir -p ~/.pip && touch ~/.pip/pip.conf`

     2.   修改 `~/.pip/pip.conf` 文件如下：

          ```ini
          [global]
          timeout = 60
          index-url = https://mirrors.ustc.edu.cn/pypi/web/simple
          [install]
          trusted-host = https://mirrors.ustc.edu.cn
          ```

2.   修改默认使用的 python 版本，参考于 [更改Ubuntu默认python版本的方法 - Fugui](https://www.cnblogs.com/yifugui/p/8649864.html)

     1.   查看默认 python 版本：`python --version`

     2.   列出当前系统中所有可用的 python 版本：`ls /usr/bin/python*`

     3.   使用 update-alternatives 来为整个系统更改 python 版本：`update-alternatives --list python`

          如果出现：*update-alternatives: error: no alternatives for python*，表明当前系统中的 python 版本尚未被识别到，需要更新替代列表，通过第 2 步的列出所有可用 python 版本，可以获取到当前系统中存在但并未被识别的可执行 python 指令，例如 `/usr/bin/python2.7`

          此时通过 

          `update-alternatives --install /usr/bin/python python /usr/bin/python2.7 1`

          `update-alternatives --install /usr/bin/python python /usr/bin/python3.8 2`

          来注册两个 python 指令

          `--install` 选项使用了多个参数用于创建符号链接，最后一个参数指定了此选项的优先级，如果没有手动来设置替代选项，那么具有最高优先级的选项就会被选中；

          在上述例子中为 `/usr/bin/python3.8` 设置的优先级为 2，所以 update-alternatives 命令会自动将它设置为默认 python 版本

3.   为 python 2 添加 pip 功能

     在当前使用的 ubuntu 版本中，并没有为 python 2.7 添加 pip 功能，需要自己手动添加，下面为 python 2.7 添加 pip 功能，然后使用 pip2 指令来调用专属于 python 2.7 的 pip 包管理器

     1.   获取官方脚本：`curl https://bootstrap.pypa.io/pip/2.7/get-pip.py -o get-pip.py`
     2.   使用 python 2 执行脚本：`python2 get-pip.py`
     3.   为 pip2 添加软链接：`sudo ln -s ~/.local/bin/pip2 /usr/local/bin/pip2`，后续就可以使用 `pip2 install xxx` 指令了；可以使用 `pip2 -V` 指令来查看是否成功安装，会提示是来自于 python 2.7
     4.   顺带更新 setuptools：`pip2 install --upgrade setuptools`；部分包安装时使用了较新的安装语句，这需要新版的 setuptools 支持
     5.   顺带安装开发环境：`sudo apt-get install python2.7-dev`；在通过 pip2 安装一些库时，会要求使用到 python 2.7 的开发环境来编译某些运行文件

>   占位符

...



## basic operations

>   以下是一些可能会用得到的操作

基本上与 Linux 系统进行交互时都应该在 shell 中完成（如果是 gui 界面，打开终端的时候，会自动进入一个 shell），列出一些最基本的操作方法

>   进程

1.   中断；`ctrl + c` 就是直接向当前运行的进程发送一个 SIGINT 信号并使之中断，退出；在有些交互式 shell 中 `ctrl + d` 还可以被用作退出当前的 shell

2.   挂起与恢复；

     1.   如果不想退出进程，而是暂时放到后台，并继续运行其他进程，则需要 `ctrl + z` 将进程挂起到后台，其显示如下：

          ```bash
          [任务号] [状态：+(表示在运行) or -(表示已关闭)] [PID] [当前状态] [进程信息\名字]
          
          # 例如
          [1] + 784024 suspended python
          ```

     2.   将后台进程恢复，则需要输入 `jobs` 会列出当前后台挂起的进程；然后输入 `fg %任务号` 即可将该进程调到前台来，例如：

          ```bash
          $jobs
          [1]  - 1696 suspended  cmd1
          [2]  + 1697 suspended  cmd2
          
          # 重新将 cmd1 调到前台
          $fg %1
          ```

>   用户

1.   用户身份的确定；

     1.   `whoami`，打印出当前用户的用户名，通常用于确认当前用户身份
     2.   `id`，打印出当前用户的用户组，以及所属组的 id

2.   用户切换；

     1.   `sudo`，用另一个用户的身份去执行某个命令，通常需要输入密码，详细用法可以参考 [这里](https://www.runoob.com/linux/linux-comm-sudo.html)，常用方法如下：

          ```bash
          # 查看当前用户的信息
          sudo -l
          
          # 切换到另一个用户
          sudo foobar
          
          # 切换到 superuser 用户
          sudo su
          sudo -i
          
          # 以其他用户的身份执行命令
          sudo [-u someone] command	# 配置通式
          sudo command	# 缺省 -u 的情况下, 以 superuser 的身份执行命令, 通常用于出现了 permission denied 的情况
          sudo -u foobar command
          ```

     2.   使用 `sudo` 要求当前用户有 `sudo` 权限，需要在 `/etc/sudoers` 中配置，配置参考如下：

          ```bash
          # 通式
          username	hostname=(group_name:username)	 command
          
          # 参考如下, 需要插入到 /etc/sudoers 文件中 root ALL=(ALL:ALL) ALL 一项的下方
          foobar ALL=(ALL:ALL)	ALL	# 解释为 foobar 用户可以在 ALL(任何主机) 下, 以 ALL:ALL(任何用户任何身份) 的方式执行 ALL(任意命令)
          
          # 下面还给出一个用于在 sudo command 时免密登录的配置, 当然一般都不建议直接配置 NOPASSWD
          foobar ALL=(ALL:ALL) NOPASSWD:ALL
          ```

     3.   `su foobar`；这个指令是直接切换到目标用户 foobar，如果直接输入 `su` 表示切换到 root 用户

3.   修改用户信息；

     1.   用户的改名，单纯修改用户名是无效的，需要对用户的 home 目录、uid、组名都修改；下列操作中，实现将用户名 `user1` 完全修改成用户名 `user2`，确保所有与之相关的信息都能得到更新，
          1.   将用户 user1 的登录名修改成新用户名 user2：`sudo usermod -l user2 user1`
          2.   确保从用户 user1 的账户中登出，可以使用 `sudo su` 切换成 root 账户，然后使用 `pkill -9 -u user1` 杀死所有 user1 的进程
          3.   将用户 user1 的 home 目录更改成新用户名 user2 对应的目录：`usermod -d /home/user2 -m user2`
          4.   为新用户设置其 uid：`usermod -u 1001 user2`
          5.   修改组用户名：`groupmod -n user2 user1`，即直接把原来组名为 user1 的修改成 user2

>   网络

查看网络相关设置需要使用工具集 net-tools 中的 `ifconfig` 指令：`sudo apt install net-tools`

1.   查看当前网卡相关信息：`ifconfig`，一个示例输出如下

     ```bash
     eth0: flags=4163&lt;UP,BROADCAST,RUNNING,MULTICAST&gt;  mtu 1500
             inet 192.168.4.11  netmask 255.255.255.0  broadcast 192.168.4.255
             inet6 fe80::200:ff:fe00:1  prefixlen 64  scopeid 0x20&lt;link&gt;
             ether 00:00:00:00:00:01  txqueuelen 1000  (Ethernet)
             RX packets 470584  bytes 209393190 (199.6 MiB)
             RX errors 0  dropped 0  overruns 0  frame 0
             TX packets 421366  bytes 184306566 (175.7 MiB)
             TX errors 0  dropped 0 overruns 0  carrier 0  collisions 0
     
     lo: flags=73&lt;UP,LOOPBACK,RUNNING&gt;  mtu 65536
             inet 127.0.0.1  netmask 255.0.0.0
             inet6 ::1  prefixlen 128  scopeid 0x10&lt;host&gt;
             loop  txqueuelen 1000  (Local Loopback)
             RX packets 676832  bytes 215381786 (205.4 MiB)
             RX errors 0  dropped 0  overruns 0  frame 0
             TX packets 676832  bytes 215381786 (205.4 MiB)
             TX errors 0  dropped 0 overruns 0  carrier 0  collisions 0
     ```

     在该示例中，eth0 是当前正在使用的有效网卡，inet 标识该网卡被分配给的 ipv4 地址信息

2.   配置网卡信息；如果发现网卡无法正常获取到 ip 地址，则需要进入到 `/etc/network` 目录，修改文件 `/etc/network/interfaces` 中的内容，示例如下：

     ```ini
     # This file describes the network interfaces available on your system
     # and how to activate them. For more information, see interfaces(5).
     
     source /etc/network/interfaces.d/*
     
     # The loopback network interface
     auto lo
     iface lo inet loopback
     
     auto eth0
     iface eth0 inet dhcp
     ```

     配置完成后，输入 `sudo systemctl restart networking.service` 重启网络配置信息

### 关机

```bash
shutdown -h 10	# 十分钟后安全的关机
shutdown -r now/10/12:00	# 立即/10分钟后/12:00 重启

halt	# 立即关机
= shutdown -h now
= poweroff

reboot	# 重启
```

### 创建&查看文件信息

```bash
# 创建:
touch file	# 创建单个文件
mkdir folder	# 创建文件夹

查看:
ls	# 列出当前目录下是文件 不包含隐藏文件
ls -a	# 包含隐藏文件
ls -l	# 列出文件的权限属性
ll = ls -al
```

### 删除

>   sudo rm -rf file	# -f表示强制删除 -r表示同时删除文件夹

### 关闭进程

```bash
# 首先确定要关闭的进程
ps -aux | grep '某个进程名字'

# 获取第二列，例如 12345
kill 12345	## 普通关闭
kill -9 12345	## 强制关闭

## 批量杀进程
ps -aux | grep '进程名' | grep -v grep | awk '{print $2}' | xargs  kill -9
## xargs 是传参的
## awk 是一种文本语言，在这里截取第二列pid
## grep -v xxx 指列出来的不显示 xxx ，只显示其他的
## grep -v grep 指不显示 grep，这里主要是因为grep的时候会把grep自身也列出来，然而我们并不需要关闭grep
```

## 系统手册

### 查看ubuntu系统版本

```bash
cat /proc/version
# Linux version 5.13.0-27-generic (buildd@lgw01-amd64-045)
# gcc (Ubuntu 9.3.0-17ubuntu1~20.04) 9.3.0, 
# GNU ld (GNU Binutils for Ubuntu) 2.3429~20.04.1-Ubuntu SMP

lsb_release -a
# Distributor ID: Ubuntu
# Description:    Ubuntu 20.04.3 LTS
# Release:        20.04
# Codename:       focal

# 一键查看系统信息
sudo wget -qO- bench.sh | bash
```

### 公私钥免密登录

```bash
# 生成公私钥对 一路回车
## 保护好 id_rsa 里的私钥 (BEGIN OPENSSH PRIVATE KEY 开头)
ssh-keygen

# 把 id_rsa.pub 里的内容复制到想要免密登录到的机器上
# 在目标机器上 某用户在 ~ 目录下创建一个 .ssh文件夹

chmod 600 -R ~/.ssh
cd ~/.ssh
## 写入 id_rsa.pub 的内容
vim authorized_keys
## 然后就可以免密登录了
ssh xxx@ip
```

### fail2ban

一个用于验证短时间内过量请求ssh登录等服务的脚本

```bash
# 安装
sudo apt install fail2ban

# 配置
## 配置最大登录次数，封禁时间等
vim /etc/fail2ban/jail.conf
### 下行开始 提到的可以自定义 其他的默认即可
[DEFAULT]
ignorecommand =
bantime  = 10m	# ban掉的ip的时间
maxretry = 7	# 最大登录失败尝试次数
### 上行结束

systemctl enable fail2ban.service	# 设置开机启动
cat /var/log/fail2ban.log	# 查看日志
fail2ban-client status sshd	# 查看ssh登录详细信息
fail2ban-client set sshd unbanip xxx.xxx.xxx.xxx	# 解封某个地址
```

### 测试服务器性能

```bash
# https://blog.ilemonrain.com/linux/LemonBench.html
curl -fsSL http://ilemonra.in/LemonBenchIntl | bash -s fast
```

### /etc/passwd

```bash
用于保存系统中所有用户的信息，该文件对所有用户都可见，在该文件中，每行信息代表一个用户。
修改密码的方式:
	sudo passwd xxx	# 修改xxx的密码
	sudo passwd root	# 修改root账户的密码
	echo "root:password" | chpasswd	# 非交互式改密
	
cat /etc/passwd	# 查看所有用户属性
    xxx:xxx:xxx:xxx:xxx:xxx:xxx
    用户名:口令:用户标识号:组标识号:注释性描述:用户主目录:命令解释程序
```

### Vim

```bash
vim file	# 打开/编辑时创建文件

1.进入vim时会先进入 "命令模式"
2.按 "i" 进入插入模式(按 "a" 则新开一行)
3.按 "esc" 退出插入模式
4.常用指令
	x	# 删除后一个字符
	dd	# 删除整行
	/text = ?text	# 意义为 Ctrl + f
	u	# 撤销操作
	yy	# 复制
	Ctrl + r	# 重做操作
	Ctrl + s	# 锁定终端输入
	Ctrl + q	# 恢复终端锁定状态
5.翻页
	Ctrl + B	# 往上
	Ctrl + F	# 往下
6.在命令行模式下键入 ":" 并输入
	"w"	# 保存
	"q"	# 退出
	"wq"	# 保存并退出
	"wq!"	# 强制保存并退出
7.批量修改字符串
	:1,$s/str1/str2/g	# 用str2替换全文的str1
8.更多操作见[./Ubuntu下Vim的常用操作命令]
```

### systemctl

自定义系统命令脚本

```bash
vim /usr/lib/systemd/system/xxx.service 
[Unit]   # 主要是服务说明
Description=test   # 简单描述服务
After=network.target    # 描述服务类别，表示本服务需要在network服务启动后在启动
Before=xxx.service      # 表示需要在某些服务启动之前启动，After和Before字段只涉及启动顺序，不涉及依赖关系。

[Service]  # 核心区域
Type=forking     # 表示后台运行模式。
User=user        # 设置服务运行的用户
Group=user       # 设置服务运行的用户组
KillMode=control-group   # 定义systemd如何停止服务
PIDFile=/usr/local/test/test.pid    # 存放PID的绝对路径
Restart=no        # 定义服务进程退出后，systemd的重启方式，默认是不重启
ExecStart=/usr/local/test/bin/startup.sh    # 服务启动命令，命令需要绝对路径
PrivateTmp=true                               # 表示给服务分配独立的临时空间
   
[Install]   
WantedBy=multi-user.target  # 多用户
```

#### 指令

```bash
systemctl daemon-reload    # 重载系统服务
systemctl enable *.service # 设置某服务开机启动      
systemctl start *.service  # 启动某服务  
systemctl stop *.service   # 停止某服务 
systemctl reload *.service # 重启某服务
```

### tcpdump

> 查看网络连接信息

1. 查看某个网卡的端口信息：`tcpdump -i <网卡名> -v port <端口号> -nn`，向某个端口发送 **udp** 协议包：`nc -vuz &lt;ip&gt; &lt;port&gt;`

### tar

Linux下的归档文件 tar只是合成一个文件 但是不压缩

#### tar格式

```bash
"-c" # create 创建
"-x" # extract 解包
"-v" # verbose 列出详细信息
"-f" # filename 后接文件名 这个f必须放最后一个
# 打包
tar -cvf file.tar(目标文件名) somefile(原文件名或目录)
# 解包
tar -xvf file.tar
```

#### tar.gz格式

这个就是tar的zip格式(gzip)

```bash
"-z" #以gzip方式压缩
# 直接压缩 .tar 文件
gzip file.tar

# 直接解压 .tar.gz 文件
gunzip file.tar.gz

# 打包并压缩文件
tar -zcvf file.tar.gz somefile

# 解压并解包
tar -zxvf file.tar.gz
```

### 账户信息相关

```bash
1.修改进入终端时的目录
	在/home/user下
	vim .bashrc
	在末尾添加 cd Desktop	# 意为每次进入bash都会自动先执行 cd Desktop
2.新增账户
	adduser new_account
    passwd new_account	# 为新账户指定密码
    usermod -s /bin/bash new_account	# 为新账户指定命令解释器
    usermod -d /home/new_account new_account	# 为新账户指定用户主目录

3.修改账户信息
	passwd user	# 修改user的密码 需要root
	vim hostname	# 修改主机名
	vim hosts	# 修改主机名	
	vim group	# 修改组
		使用正则 :%s/old_name/new_name/g
	mv /home/old_name /home/new_name	# 移动目录
```

### 权限相关

```bash
chmod chown(更改拥有者 用法相同)
# r：可读 w：可写 x：可执行
# chmod (u)User,(g)Group,(o)Other file..
# 指定一个 -R 可以递归授权

## e.g:
## 所有用户可读 a.conf
    chmod ugo+r a.conf	### user, group, other +一个 r(read) 的权限
    = chmod a+r a.conf	### allusers 都+上 r(read) 的权限

## 设置文件 a.conf 与 b.xml 权限为拥有者与其所属同一个群组 可读写，其它组可读不可写
    chmod a+r,ug+w,o-w a.conf b.xml

## 设置当前目录下的所有档案与子目录皆设为任何人可读写
    chmod -R a+rw *

## 所有人 可读可写可执行 a.conf
    chmod 777 a.conf
    = chmod u=rwx,g=rwx,o=rwx a.conf
    = chmod a=rwx a.conf

## 设置拥有者可读写 其他人不可读写执行 a.conf
    chmod 600 a.conf
    = chmod u=rw,g=---,o=--- a.conf
    = chmod u=rw,go-rwx a.conf

常用权限表
-rw------- (600)    只有拥有者有读写权限。
-rw-r--r-- (644)    只有拥有者有读写权限；而属组用户和其他用户只有读权限。
-rwx------ (700)    只有拥有者有读、写、执行权限。
-rwxr-xr-x (755)    拥有者有读、写、执行权限；而属组用户和其他用户只有读、执行权限。
-rwx--x--x (711)    拥有者有读、写、执行权限；而属组用户和其他用户只有执行权限。
-rw-rw-rw- (666)    所有用户都有文件读、写权限。
-rwxrwxrwx (777)    所有用户都有读、写、执行权限。
```

### 运维查看

```bash
# 查看cpu使用
top

# 查看文件运行进程
ps -aux

# 查看 当前使用了的句柄数 空闲的句柄数 最大可行句柄数
cat /proc/sys/fs/file-nr

# 查看硬盘使用率
df -h

# 查看当前文件夹大小的信息
ls -lh	# 简单查看
du -h -d 1	# 明确查看 --help可以显示帮助信息
```



## 安装各种环境



### PWN环境

安装最新版 **pwntools**：

1. `sudo apt install curl aptitude `，

2. `sudo aptitude install python3 python3-pip python3-dev git libssl-dev libffi-dev build-essential`，

3. `python3 -m pip install --upgrade pip`，

4. `pip install setuptools setuptools_rust`，

5. `python3 -m pip install --upgrade pwntools`

验证是否安装成功：

​	输入 `python -c "from pwn import *;print(asm('ret'))"`

​	然后会回显一个 `b'\xc3'` 则代表安装成功

#### peda 拓展

```bash
1.git clone https://github.com/gatieme/GdbPlugins.git ~/GdbPlugins
2.对应启动命令(注意具体路径)：
    echo "source ~/GdbPlugins/peda/peda.py" > ~/.gdbinit
    echo "source ~/GdbPlugins/gef/gef.py" > ~/.gdbinit 
    echo "source ~/GdbPlugins/gdbinit/gdbinit" > ~/.gdbinit
    
3.顺便再安装c库文件
	sudo apt-get install gcc-multilib
```

#### pwndbg 拓展

pwndbg 会比 peda 界面好用一点，见仁见智

安装：

 1.    `git clone https://github.com/pwndbg/pwndbg`

 2.    `cd pwndbg`

 3.    `./setup.sh`

       这里可能会有错误，一般是 `xxx1 requires xxx2，not installed.` 类型的

       使用 `sudo pip install xxx2 ` 以 **sudo** 的身份安装python包就行了

 4.    `vim ~/.gdbinit`

       执行完第3步，这里一般都会自动写上对应的 pwndbg 地址了

       如果没有，就手动写上 **source xxx目录/pwndbg/gdbinit.py**

#### ida远程调试

>   1.   在 ida 根目录 dbgsrv 文件夹 找到 linux_server 或 linux_server64
>   2.   拖到 linux 并且 chmod +x linux_server
>   3.   执行 ./linux_server 注意相应端口要能连通
>   4.   ida 远程连接

相关配置 假设要调试的目标程序为 ~/Desktop/pwn

```bash
# 应用程序 -> ~/Desktop/pwn
# 输入文件 -> ~/Desktop/pwn
# 目录 -> ~/Desktop/
# 参数 -> 根据具体情况，默认不填
# 主机名 -> linux的ip地址 端口填在linux上运行 ./linux_server 之后回显的端口
# 密码 -> 填你用的什么账户执行的 ./linux_server 的账户密码
```

## 简单实用工具

这块都是按照个人需求来自行选择

### 安装 ZSH shell

新kali的默认shell

```bash
1.apt先安装zsh服务
	sudo apt install zsh
	
2.获取oh my zsh用于配置个人zsh终端
	sudo git clone https://github.com/robbyrussell/oh-my-zsh.git ~/.oh-my-zsh
	sudo cp ~/.oh-my-zsh/templates/zshrc.zsh-template ~/.zshrc	# 应用到.zshrc中

3.修改账号的默认shell
	举例为user账户
	sudo vim /etc/passwd
	看到
		user:x:1000:1000:,,,:/home/user:/bin/bash
	修改成
		user:x:1000:1000:,,,:/home/user:/usr/bin/zsh
	保存
	
	或者 chsh user
	输入 /usr/bin/zsh
	
4.美化zsh shell
	cd ~
	vim .zshrc
	修改 ZSH_THEME 项，即为修改shell主题	# duellj
	保存
	
5.应用配置
	cd ~
	source .zshrc
```

### 安装 rlwrap

一个命令内的命令行记忆

```bash
sudo apt install rlwrap
```

### 美化工具

需要gui可视化界面

```bash
1.安装unity-tweak-tool美化工具
	sudo apt install unity-tweak-tool
	
2.安装plank Dock插件
	sudo apt install plank 
	sudo add-apt-repository ppa:noobslab/macbuntu
	sudo apt update
	sudo apt install macbuntu-os-plank-theme-lts-v7
	sudo ln -s /usr/share/applications/plank.desktop /etc/xdg/autostart/	# 设置开机自启动
		在docker上按ctrl+鼠标右键进入设置菜单
		
3.安装gnome-tweak-tool管理开机自动启动项
	sudo apt install gnome-tweak-tool

4.终端美化-guake
	sudo apt install guake
```

## 初始化 vps

从云服务商获取一台 vps，这里以 ubuntu 22.04，2c2g 30Mbps 为例；默认用户名是 admin，主机名是 `4RDyINeM1GQ6gaZj7VWuboXxwYLCJmH`；对应修改成 wkyuu 和 `vps`

1.   使用控制台登录系统，修改密码：`passwd root`，`passwd admin`

2.   修改用户名称、主机名称：

     1.   改名：`sudo usermod -l wkyuu admin`
     2.   关闭所有 admin 起的进程：`sudo su`，`pkill -9 -u admin`
     3.   更新 `/home/admin` 名称为 `/home/wkyuu`：`usermod -d /home/wkyuu -m wkyuu`
     4.   修改组名：`sudo groupmod -n wkyuu admin`，使用 `id` 查看结果：*uid=1000(wkyuu) gid=1000(wkyuu) groups=1000(wkyuu)*
     5.   修改主机名：`vim /etc/hostname`，将其中 `4RDyINeM1GQ6gaZj7VWuboXxwYLCJmH` 改成 `vps`，重启：`reboot`
     6.   修改 sudoers 文件：`sudo su`，`visudo`，找到所有 `admin` 选项修改成 `wkyuu`

3.   将个人公钥复制到对应文件中 `~/.ssh/authorized_keys`，root 和 wkyuu 都要

     1.   个人公钥文件：

          ```ini
          ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC0ReXz21jNw8//pENvBHaj/I1yetMj805awkLFAMavihPEw6ZdJfJssPKb5t8uc+hy7or+tvPEPq6oDj+aWLmmgNOXN4Wjo1r7l2IKwCIueuAztWz2pJZ1WwQJuqJiWuEuKQ+ysjHNEPGZW/2n/IZeHCg5n0OnSeEblhx3Z2t3Bhj7YcNmZgBrc2ZDNuRvgNNTebdFNUCCYDIf3PQVGqjNNDdXOTvrCN8e1g2O41AhGGvL0pRv91Y9/3tjjlxdeyGSI7wmfHlhTCiQmeEzOM+X7wNa08fnXI5RUu5+1SPoT4JwuYvPU9LZ0Ohh4wlvkUsxRJ4l+UVpvGddsmu4JO4nEGGIZXy4vHK+vQ7+SPDweRoIe73+afnQi4de5W3vc/BrAJEsfDlll+XRTaRUwbC0RLkslAlpD9vwHuUKIpwvGHY1vrM605IUUAWTlDaa5z+m0xKaQX8b1Vl+tX9DM+4dQjm3mWUYbct5NL7WWSiKiN//pxQQB0vtHmWt1GVlXgs= wkyuu\wkyuu@wkyuu
          ```

     2.   `/root/.ssh` 对应权限如下：

          ```bash
          drwx------  2 root root 4.0K Mar 28 01:06 .		# .ssh
          drwx------ 10 root root 4.0K Mar 28 10:03 ..
          -rw-------  1 root root  571 Mar 28 01:06 authorized_keys
          ```

          `chmod 700 /root/.ssh`，`chmod 600 /root/.ssh/authorized_keys`

     3.   `~/.ssh` 对应权限：

          ```bash
          drwxr-xr-x 2 wkyuu wkyuu 4.0K Mar 28 01:34 .	# .ssh
          drwxr-x--- 4 wkyuu wkyuu 4.0K Mar 28 09:57 ..
          -rw-r----- 1 wkyuu wkyuu  570 Mar 28 01:34 authorized_keys
          ```

          `chmod 655 ~/.ssh`，`chmod 640 ~/.ssh/authorized_keys`

     4.   检查 `/etc/ssh/sshd_config` 文件，主要是以下几项：

          ```ini
          KbdInteractiveAuthentication no
          
          UsePAM yes
          X11Forwarding yes
          
          PrintMotd no
          
          UseDNS no
          AddressFamily inet
          SyslogFacility AUTHPRIV
          PermitRootLogin yes
          PasswordAuthentication no	# 禁止密码登录
          ```

4.   安装 zsh：

     1.   首先换源，这里换 ubuntu 22.04 ustc 的源，其他自助，`cp /etc/apt/source.list /etc/apt/source.list.backup`，`vim /etc/apt/source.list`：

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

          `sudo apt update`

     2.   获取 zsh：`sudo apt install zsh`，找到具体位置：`which zsh`，这里是 */usr/bin/zsh*

     3.   配置默认 shell：`chsh -s /usr/bin/zsh`，root 和 wkyuu 都要

     4.   修改配置文件 `touch ~/.zshrc`，配置文件放在这里 `https://paste.majo.im/orihizulay.bash`，一键配置：`curl https://paste.majo.im/raw/orihizulay > ~/.zshrc`，root 和 wkyuu 都要
