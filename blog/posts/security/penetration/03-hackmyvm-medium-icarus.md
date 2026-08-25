---
title: "penetration | 03_hackmyvm-medium-Icarus"
description: "bash编程，LD PRELOAD劫持"
date: "2022-04-02T02:24:00.000Z"
updated: "2024-03-01T05:17:12.000Z"
tags: ["penetration"]
draft: false
layout: "post"
slug: "hackmyvm-medium-icarus"
---

## Medium Icarus

## 实践环境

### 攻击机

---

kali - VirtualBox_amd64 | 192.168.6.188

ubuntu - Desktop_amd64 | 192.168.6.223

Windows 10 | 192.168.6.107

### 靶机

---

[Icarus - Debian 10 from HackMyVM.eu](https://hackmyvm.eu/machines/machine.php?vm=Icarus) - 192.168.6.145

## 前期探测

开机 没有ip地址

![image-20220401122317381](https://tataramoriko-oss.oss-cn-shenzhen.aliyuncs.com/markdown/image-20220401122317381.png)

### netdiscoer

---

![image-20220401122301410](https://tataramoriko-oss.oss-cn-shenzhen.aliyuncs.com/markdown/image-20220401122301410.png)

```bash
## -r 指定范围; -i 指定网卡
netdiscover -r 192.168.6.0/24 -i eth0
```

![image-20220401122814213](https://tataramoriko-oss.oss-cn-shenzhen.aliyuncs.com/markdown/image-20220401122814213.png)

### nmap

---

```bash
# -sC 指定脚本，不选是默认; -sV 探测打开端口对应服务的版本信息; -v 显示详细信息，不加直接显示结果; -p- 指定要扫描多少个端口,-p默认1000,-p-就65536
nmap -sC -sV -v -p- 192.168.6.145
```

![image-20220401123219935](https://tataramoriko-oss.oss-cn-shenzhen.aliyuncs.com/markdown/image-20220401123219935.png)

开放ssh和80网页端口

### gobuster

---

```bash
gobuster dir -u http://192.168.6.145/ -w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt -x html,txt,php -e -o dir_192.168.6.145 -t 30 -q
```

![image-20220401125217096](https://tataramoriko-oss.oss-cn-shenzhen.aliyuncs.com/markdown/image-20220401125217096.png)

扫出很多东西，点开了看每个文件里面都只有一个字符。

其中 index.php和check.php 里面是一个php表单登录 似乎只能走爆破的路子

然后 **/a** 文件里面似乎是花名册，写个脚本把这些分别打开看一下里面的信息

![image-20220401125330095](https://tataramoriko-oss.oss-cn-shenzhen.aliyuncs.com/markdown/image-20220401125330095.png)

看一下这些东西都是啥

```bash
curl http://192.168.6.145/xxa
```

![image-20220401175410972](https://tataramoriko-oss.oss-cn-shenzhen.aliyuncs.com/markdown/image-20220401175410972.png)

一眼就是要让我按照顺序拼出某些东西

编写一个shell.sh脚本

```shell
#!/bin/bash
for i in $(cat url);
do
curl -s http://192.168.6.145/$i >> id_rsa;
done
echo "done"
```

然后 chmod +x shell.sh

![image-20220401180052472](https://tataramoriko-oss.oss-cn-shenzhen.aliyuncs.com/markdown/image-20220401180052472.png)

查看写入的文件

![image-20220401180128171](https://tataramoriko-oss.oss-cn-shenzhen.aliyuncs.com/markdown/image-20220401180128171.png)

有个私钥，看来可以直接用ssh登录靶机

### ssh免密登录

---

进入目录 **~/.ssh** 然后打开 id_rsa 文件 把这串私钥放进去保存

![image-20220401190617265](https://tataramoriko-oss.oss-cn-shenzhen.aliyuncs.com/markdown/image-20220401190617265.png)

然后尝试ssh登录目标靶机

```bash
# 这里我试了 root Icarus Man man 的用户名都不对
ssh icarus@192.168.6.145
```

![image-20220401190727517](https://tataramoriko-oss.oss-cn-shenzhen.aliyuncs.com/markdown/image-20220401190727517.png)

登陆成功 开始想办法提权

## 靶机渗透

---

首先查看自己有的权限 **sudo -l**

![image-20220401190932623](https://tataramoriko-oss.oss-cn-shenzhen.aliyuncs.com/markdown/image-20220401190932623.png)

进入home目录看看 **cd ~**

目录下有一个 flag.sh

![image-20220401192900155](https://tataramoriko-oss.oss-cn-shenzhen.aliyuncs.com/markdown/image-20220401192900155.png)

没啥用，就是告诉你要提权

### LD_PRELOAD

---

无意中逛 sudo -l 发现这里多了一个东西。联想到 [利用 LD_PRELOAD 来提权](https://www.hackingarticles.in/linux-privilege-escalation-using-ld_preload/)

![image-20220402085718171](https://tataramoriko-oss.oss-cn-shenzhen.aliyuncs.com/markdown/image-20220402085718171.png)

这是一种动态共享库劫持的方式(存疑)

按照文章步骤来走就是

在当前目录创建一个 劫持的共享库，里面写入提权语句，利用系统的加载来提权。

这里需要满足两个前提：

- 1，在 /etc/sudoers 里写入 env_keep += LD_PRELOAD
- 2，在 /etc/sudoers 里为某一用户添加 NOPASSWD 且 权限波及到 root 的 免密执行程序

![image-20220402092713519](https://tataramoriko-oss.oss-cn-shenzhen.aliyuncs.com/markdown/image-20220402092713519.png)

然后输入 sudo -l

![image-20220402092734158](https://tataramoriko-oss.oss-cn-shenzhen.aliyuncs.com/markdown/image-20220402092734158.png)

使用 sudo LD_PRELOAD 以运行 /usr/bin/id

![image-20220402092819534](https://tataramoriko-oss.oss-cn-shenzhen.aliyuncs.com/markdown/image-20220402092819534.png)

于是我们可以在靶机上创建一个 shell.so，以至于以root身份在运行id加载动态库的时候改变一些系统设置，其中就包括改变自身的id

#### 创建 shell.so

---

在/tmp下 创建一个 shell.c 文件

这里必须要把shell.so移动到/tmp目录下

![image-20220402093231386](https://tataramoriko-oss.oss-cn-shenzhen.aliyuncs.com/markdown/image-20220402093231386.png)

刷新_init并修改成 setuid(0)，并且打开一个shell来达到提权的目的

使用 **gcc -fPIC -shared -o shell.so shell.c -nostartfiles** 来创建 .so 文件

![image-20220402093646813](https://tataramoriko-oss.oss-cn-shenzhen.aliyuncs.com/markdown/image-20220402093646813.png)

**sudo LD_PRELOAD=/tmp/shell.so id**

![image-20220402101603287](https://tataramoriko-oss.oss-cn-shenzhen.aliyuncs.com/markdown/image-20220402101603287.png)

以root身份执行了id，并且使用system函数打开了一个shell。

## 参考链接

1，[arp-scan列出局域网内主机](https://blog.csdn.net/lixiangminghate/article/details/84343878)

2，[多线程爬虫入门及问题解决（爬取表情包）](https://cloud.tencent.com/developer/article/1671953)

3，[shell 中 &#39;&gt;&#39; 与‘&gt;&gt;’ 的区别](https://blog.csdn.net/nahanai/article/details/83861449)

4，[2&gt;/dev/null和&gt;/dev/null 2&gt;&amp;1和2&gt;&amp;1&gt;/dev/null](https://www.cnblogs.com/missmeng/p/10365044.html)

5，[Linux下去掉^M的四种方法](https://www.jb51.net/article/142224.htm)

6，[简谈SUID提权](https://www.freebuf.com/articles/web/272617.html)

7，[Linux Privilege Escalation using LD_Preload](https://www.hackingarticles.in/linux-privilege-escalation-using-ld_preload/)

8，[linux下动态库soname简介](https://blog.csdn.net/guotianqing/article/details/94304193)

9，
