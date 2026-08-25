---
title: "app | ftp-server-in-linux"
description: "几种使用 Linux 来当 ftp 中转站的方法"
date: "2022-03-18T04:36:00.000Z"
updated: "2024-07-02T03:01:00.000Z"
tags: []
draft: false
layout: "post"
slug: "ftp-server-linux"
---

## ftp server in linux

测试环境：Kali（debian linux）

## lrzsz

Linux 与 other os 互传好工具，直接代替右键的上传与下载：`sudo apt-get install lrzsz`

## filezilla

1.   linux：

     1.   `sudo apt-get install filezilla`

     2.   `vim /etc/ssh/sshd_config`，末尾添加以下内容：

          ```ini
          PermitRootLogin yes
          StrictModes no
          PasswordAuthentication yes
          ```

     3.   开启 ssh 服务并配置开机自启动：`sudo systemctl enable ssh`、`sudo systemctl start ssh`

2.   Windows or 其他 os：

     1.   安装 FileZilla
     2.   左上角 - 文件 - 站点管理器 - 新建站点 - 右侧协议改成 SFTP
     3.   按照配置输入 用户 密码等

### 方式二 vsftpd(Very Safe ftp Daemon)

```bash
ubuntu:
1.先在 home 下 创建 'ftp' 文件夹
	cd /home
	mkdir ftp
2.sudo apt install vsftpd	# 安装vsftpd
3.修改配置文件
	vim /etc/vsftpd.conf	# 详见文末 注意文档里面不能有空格
4.在终端输入 "ifconfig -a" 查看到的 inet 即为 linux地址
5.启动
	sudo /etc/init.d/vsftpd restart
	或 service vsftpd restart
6.查看开启状态
	service vsftpd status
	或 systemctl status vsftpd
7.查看端口
	netstat -anp|grep 21

windows\phone:
1.访问：ftp://linux机地址
	例：ftp://192.168.6.176
2.在打开的文件夹 右键-登录-输入账户密码-连接
	这里的账户密码是Linux那边的账户
```

#### vsftpd 配置过程疑难杂症

##### 550 Permission denied.

```bash
1.没有可写 权限
    vim /etc/vsftpd.conf
    line 31 : write_enable=YES 把前面的 # 去掉
2.在连接ftp成功后 如果不能创建文件夹 首先检查是否有可写权限
    sudo chmod 777 文件夹
```

##### exit=exit0,status=2

```bash
sudo 打开 /etc/vsftpd.conf
首先文件里面不能有空格
在 listen_ipv6=YES 这行 注释掉 或者 listen_ipv6=NO
```

#### vsftpd相关的配置详解

```bash
使用方法：sudo vim /etc/vsftpd.conf 添加到末尾
anonymous_enable=YES		允许匿名登录
#anonymous_enable=NO

non_mkdir_write_enable=YES	允许匿名用户创建目录
non_upload_enalbe=YES		允许匿名用户上传文件
anon_world_readable_only=YES	允许匿名用户下载 默认是禁止的 自行添加即可
anon_other_write_enable=YES	允许匿名用户对文件拥有 可读 可写权限

listen_port=233				指定命令通道为233,默认为21
listen_data_port=234			指定数据通道为234,默认为20

listen_address=192.168.6.176	指定本机IP地址
```

## 如何添加一个 Linux 账户

```bash
1.sudo su
2.adduser new_account
3.passwd new_account	#为新账户指定密码
4.cat /etc/passwd	#查看所有用户属性
	xxx:xxx:xxx:xxx:xxx:xxx:xxx
	用户名:口令:用户标识号:组标识号:注释性描述:用户主目录:命令解释程序
```

## 如何修改权限

主要是因为ftp文件夹可能存在无法访问/读/写 等情况

```bash
1.chmod chown(更改拥有者 用法相同)
	r：可读 w：可写 x：可执行
	chmod (u)User,(g)Group,(o)Other file..
		范例：
		所有用户可读 a.conf
		chmod ugo+r a.conf
		= chmod a+r a.conf

2.设置文件 a.conf 与 b.xml 权限为拥有者与其所属同一个群组 可读写，其它组可读不可写
	chmod a+r,ug+w,o-w a.conf b.xml

3.设置当前目录下的所有档案与子目录皆设为任何人可读写
	chmod -R a+rw *

4.所有人 可读可写可执行 a.conf
	chmod 777 a.conf
	= chmod u=rwx,g=rwx,o=rwx a.conf
	= chmod a=rwx a.conf

5.设置拥有者可读写 其他人不可读写执行 a.conf
	chmod 600 a.conf
	= chmod u=rw,g=---,o=--- a.conf
	= chmod u=rw,go-rwx a.conf

6.常用权限表
    -rw------- (600)    只有拥有者有读写权限。
    -rw-r--r-- (644)    只有拥有者有读写权限；而属组用户和其他用户只有读权限。
    -rwx------ (700)    只有拥有者有读、写、执行权限。
    -rwxr-xr-x (755)    拥有者有读、写、执行权限；而属组用户和其他用户只有读、执行权限。
    -rwx--x--x (711)    拥有者有读、写、执行权限；而属组用户和其他用户只有执行权限。
    -rw-rw-rw- (666)    所有用户都有文件读、写权限。
    -rwxrwxrwx (777)    所有用户都有读、写、执行权限。
```
