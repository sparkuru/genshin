---
title: "dev | 一次简单的误操作恢复过程"
description: "一定要经常备份！！！"
date: "2022-03-18T06:26:00.000Z"
updated: "2024-02-21T12:13:05.000Z"
tags: []
draft: false
layout: "post"
slug: "typecho-database-recovery"
---

## 记一次关于网站运维操作失误而引起的数据恢复

框架：ubuntu18.04 + 宝塔Linux面板 + mysql 5.6 + typecho

## 关于数据库的安装

个人推荐在Linux上还是用mysql。 关于怎么安装 mysql 百度很多教程。 本文只针对宝塔面板的MySQL一键安装。

安装MySQL的方法：宝塔面板的软件商店 -> 搜索MySQL -> 选择版本 极速安装

实际上 在刚刚安装完宝塔 进入面板的时候 面板就会推荐你一键全部安装 简称懒人包

## 关于如何设置 数据库 架设网站

成熟的框架都有一键部署 通常你只需要在宝塔里面创建一个数据库即可 跳过

## 网站恢复

适用情况：无意中修改了配置 例如 在linux系统里修改了本机的名称 或者 因为其他应用而重新安装了mysql 等

### 第一步：备份数据库(很重要)

```
    1.找到你的mysql数据库所在地
        宝塔面板在 /www/server/data
        或者你可以 vim /etc/my.cnf 查看 datadir 行

    2.备份(root权限)
        mkdir /home/backup    在 /home 创建一个 backup 文件夹
        cd /www/server
        cp -r data/ /home/backup  备份 data/ 到 /home/backup
```

### 第二步：尝试重启

#### 1.service mysqld restart

```
        如果出现 See "systemctl status vsftpd.service" and "journalctl -xe" for details.
        八成就是出错了
        此时输入 systemctl status vsftpd.service 查看错误情况

        1.ERROR 2002 (HY000): Can't connect to local MySQL server through socket '/tmp/mysql.sock' (2)
            这个问题的本质是没法查找到 /tmp/mysql.sock 这个文件
            但是 宝塔面板的 mysql 是找不到这个文件的
            对于宝塔面板 出错后可以直接跳过该错误 参考其他方案

            附一个常规的解决方法(宝塔下不可用)：
                vim /etc/my.cnf
                -> 修改两个 socket 后的地址 这里我建议是将原来的注释掉 新写一行 目的是用于生成新的 mysql.sock 文件
                -> service mysqld restart
                -> 找到那个 mysql.sock 文件 替换到原来的 /tmp/ 目录下 (注意权限问题 关于权限修改 见文末)
            思路就是 启动MySQL时会生成这个 mysql.sock 但是 /tmp 是一个临时文件夹 有时候会被删掉
            只要把生成的 'mysql.sock' 替换回去就行了

        2.Warning: World-writable config file /etc/my.cnf is ignored 类型
            这个问题是因为 在MySQL安全策略中 不允许它的文件可以被其他人获得太高权限
            而出错的原因 可能是因为 在测试时不小心更改了 /etc/mysql/ 文件夹下的文件权限
            解决方法是 按照正常的权限去修改回来(注意拥有者也要修改 而且不要像网上一样的 644!) 如图
                ![cd /etc/mysql && ll *]
          
        3.mysqld_safe Directory '/var/run/mysqld' for UNIX socket file don't exists.
            这个问题就 创建一个 mysqld 文件夹就行了
            mkdir /var/run/mysqld
```

#### 2.直接输入 mysql 出现 'ERROR 2002 (HY000): Can't connect to local MySQL server through socket '/tmp/mysql.sock' (2)'

没办法 删库吧 (凡事先备份)

### 第三步：删库(删除MySQL服务)

再三确保已经备份数据库！！！

```
            sudo su
            ->apt-get autoremove --purge mysql-server-xxxx      这里需要自动补全
            ->apt-get remove mysql-server
            ->apt-get autoremove mysql-server
            ->apt-get remove mysql-common

            清理残留
            ->dpkg -l |grep ^rc|awk '{print $2}' |sudo xargs dpkg -P
            ->find /etc -name "*mysql*" |xargs rm -rf           这里要求没有回显 但是宝塔会有 不用管
            ->rm -rf /www/server/mysql                  这是宝塔的MySQL安装目录 这一步完成后还要去 宝塔面板里点击卸载MySQL
```

### 第四步：重新安装MySQL

只需要到宝塔面板里面 一键安装MySQL即可 请确保和卸载之前的版本一致 在上一步卸载前可以看到版本

安装完成后 可以使用 systemctl status mysqld 查看运行情况

### 第五步：配置 + 修改权限

这一步的思路是将备份的mysql数据库数据复制回原文件夹 同时正确配置权限(在备份时 文件拥有者会变成 root 而不再是 mysql 导致后续面板无法读取到数据库的数据)

```
        sudo su
        ->在 /home/backup 文件夹(即你的备份目录)里面 找到除了 mysql 以外你要复原的数据库。(下文以 typecho 数据库为例)
        ->如果想知道这个数据库有没有数据 只要看其目录(与数据库同名)下有没有文件就行
        ->cp -r typecho /www/server/data
        ->cd /www/server/data               然后进入 /www/server/data 修改权限
        ->chown mysql typecho/
        ->cd typecho/
        ->chown mysql *
        ->重复到 cp 部分(这里在第一步就可以把所有想要复原的数据库一次性先移过去 注意 cp 要一步一动最保险)
        ->在宝塔面板 同步数据库 这个时候就可以正常读取到原数据库的文件了
```

## 如何修改权限

```
更改权限 chmod	chown(更改拥有者 用法相同)
r：可读 w：可写 x：可执行
chmod (u)User,(g)Group,(o)Other file..

	范例：
		所有用户可读 a.conf
			chmod ugo+r a.conf
			= chmod a+r a.conf

		设置文件 a.conf 与 b.xml 权限为拥有者与其所属同一个群组 可读写，其它组可读不可写
			chmod a+r,ug+w,o-w a.conf b.xml

		设置当前目录下的所有档案与子目录皆设为任何人可读写
			chmod -R a+rw *

		所有人 可读可写可执行 a.conf
			chmod 777 a.conf
			= chmod u=rwx,g=rwx,o=rwx a.conf
			= chmod a=rwx a.conf

		设置拥有者可读写 其他人不可读写执行 a.conf
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

## 关于宝塔面板的卸载

用腻了怎么办呢 现在为你提供几种卸载宝塔面板的方法

```
    方法一：首先进入宝塔Linux面板 -> 在软件商店的'已安装'中 卸载完所有已安装服务
    -> 输入 '/etc/init.d/bt stop && rm -f /etc/init.d/bt && rm -rf /www/server/panel'

    方法二：使用脚本卸载
    -> 'wget http://download.bt.cn/install/bt-uninstall.sh'
    -> 'sh bt-uninstall.sh'

    后续操作：由于卸载后会剩余残留文件等
    -> 'rm –rf /www'

    出现 'rm: cannot remove ‘/www/swap’: Operation not permitted'
    -> 输入 'swapoff /www/swap' 用于停止临时交换内存
    -> rm -rf swap
  
    出现 'rm: cannot remove 'wwwroot/xxx/.user.ini': Operation not permitted'
    -> cd /www/wwwroot/xxx	注意修改 xxx
    -> lsattr -a						这个操作是列出隐藏权限
    -> chattr -i .user.ini	这个操作是去除掉 .user.ini 的 i 属性
```
