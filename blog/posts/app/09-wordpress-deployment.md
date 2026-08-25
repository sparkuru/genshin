---
title: "app | Wordpress 折腾记录"
description: "wordpress 折腾记录，还包含了一些其他的建站(nginx，mysql，php，phpmyadmin)常见设置。"
date: "2022-03-16T11:14:00.000Z"
updated: "2024-02-21T12:08:36.000Z"
tags: []
draft: false
layout: "post"
slug: "wordpress-deployment"
---

## Wordpress 安装记录

做网站从wordpress开始。

## 前置

系统信息

> OS：Ubuntu 18.04.6 LTS

### Web容器

首先需要一个web容器 Nginx 和 Apache 都可以

这里我选择nginx

```bash
#apt源安装
sudo apt install nginx

#启动
sudo systemctl start nginx
```

#### 配置wordpress相关内容

1，在 **/home/** 目录下创建相关文件夹并且修改相关权限

```bash
#创建文件夹
sudo mkdir -p /srv/www/wordpress/

#修改合适的权限 这里用 www-data 来演示
sudo chown www-data:www-data -r /srv/www/wordpress/
```

2，配置 **/etc/nginx/** 文件夹中的内容

```bash
# 在 /etc/nginx/sites-available/ 文件夹下创建文件
sudo touch /etc/nginx/sites-available/wordpress

# 复制粘贴以下内容到 wordpress 文件中 并根据实际情况修改
## 从下行开始
server {
	listen 80 default_server;
	listen [::]:80 default_server;
  
    root /srv/www/wordpress;
	server_name xxx.com;# 这里放域名 没有域名放公网ip地址

	location / {
		try_files $uri $uri/ = 404;
		index index.php index.html;

        if (-f $request_filename/index.html) {
            rewrite (.*) $1/index.html break;
        }

        if (-f $request_filename/index.php) {
            rewrite (.*) $1/index.php;
        }

        if (!-f $request_filename) {
            rewrite (.*) /index.php;
        }

	}

    error_page 404 /404.html;
    error_page 500 502 503 504 /50x.html;
    location /50x.html {
        root /usr/share/nginx/html;
    }

	location ~ \.php$ {
		fastcgi_pass 127.0.0.1:9000;	# 设置监听端口
		fastcgi_param  SCRIPT_FILENAME  $document_root$fastcgi_script_name;	# 设置脚本文件请求的路径
		include fastcgi_params;	# 引入fastcgi的配置文件
	}

}
## 到上行结束

# 删除 /etc/nginx/sites-enabled/ 文件夹中的 defult 文件 并应用刚修改好的 wordpress 文件
sudo ln -s /etc/nginx/sites-available/wordpress /etc/nginx/sites-enabled/

# 重启nginx服务
sudo systemctl restart nginx
```

3，开启SSL服务并使用nginx强制https访问

```bash
# 修改相关配置即可
## 从下行开始
server {
	listen 80 default_server;
	listen [::]:80 default_server;

    server_name xxx.com;
	return 301 https://$server_name$request_uri;	# 端口转发服务 强制https访问
}

server {
    listen 443 ssl;
    listen [::]:443 ssl;

    root /srv/www/wordpress;
    server_name xxx.com;

	location / {
		try_files $uri $uri/ = 404;
		index index.php index.html;

        if (-f $request_filename/index.html) {
            rewrite (.*) $1/index.html break;
        }

        if (-f $request_filename/index.php) {
            rewrite (.*) $1/index.php;
        }

        if (!-f $request_filename) {
            rewrite (.*) /index.php;
        }

	}

    error_page 404 /404.html;
    error_page 500 502 503 504 /50x.html;
    location /50x.html {
        root /usr/share/nginx/html;
    }


    location ~ \.php$ {
		fastcgi_pass 127.0.0.1:9000;	# 设置监听端口
		fastcgi_param  SCRIPT_FILENAME  $document_root$fastcgi_script_name;	# 设置脚本文件请求的路径
		include fastcgi_params;	# 引入fastcgi的配置文件
	  }

    ssl on;
    ssl_certificate      /etc/nginx/cert/cert.pem;	# 这里填你的证书
    ssl_certificate_key  /etc/nginx/cert/cert.key;
    ssl_session_cache    shared:SSL:1m;
    ssl_session_timeout  10m;
    ssl_ciphers ECDHE-RSA-AES128-GCM-SHA256:ECDHE:ECDH:AES:HIGH:!NULL:!aNULL:!MD5:!ADH:!RC4;  
    ssl_protocols TLSv1 TLSv1.1 TLSv1.2;
    ssl_prefer_server_ciphers  on;    # 设置协商加密算法时 优先使用我们服务端的加密套件 而不是客户端浏览器的加密套件
}
### 到上行结束
```

### PHP脚本执行语言

#### 安装

在 apt-get 仓库自带 php7.2 版本

推荐用 **php7.4(运行phpmyadmin)** + **php8(运行wordpress主程序)** 共存的方式

```bash
#在这之前如果安装过php低版本 推荐先一路卸载

#添加php8仓库
##一路回车就行了
sudo apt-get install software-properties-common
sudo add-apt-repository ppa:ondrej/php
sudo apt-get update

#一键安装
sudo apt-get update 

sudo apt install php7.4 php7.4-common php7.4-cgi php7.4-cli php7.4-mysql php7.4-fpm php7.4-mbstring php7.4-gettext

sudo apt-get install php8.1 php8.1-fpm php8.1-cgi php8.1-cli php8.1-mbstring php8.1-gettext php8.1-common


#查看是否安装成功
##这里会显示 php版本为8.1 但是没关系
php -v

#这里安装完nginx和php以后 建议一键重启整个服务器以适配nginx和php
reboot

#tips：在安装php的时候会自动安装apache 可以用以下指令删除apache
sudo apt remove apache && sudo apt autoremove
```

#### 修改相关配置

在ubuntu下 nginx + php 需要修改相关配置

tips: 这里确保已经修改了nginx的配置

```bash
#进入 php8.1-fpm 工作目录
#php7.4的配置同理
cd /etc/php/8.1/fpm/

#修改 pool.d/www.conf 配置
vim /etc/php/8.1/fpm/pool.d/www.conf

##找到第36行 listen = /run/php/php8.1-fpm.sock 在前面加上 ; 注释掉
##在下一行添加 listen = 127.0.0.1:9000
##如果是 php7.4 就改成 listen = 127.0.0.1:9001

##找到第63行 ;listen.allowed_clients = 127.0.0.1 去掉前面的 ; 号
```

然后刷新修改的内容&&重启

> sudo service nginx restart && sudo service php8.1-fpm restart && sudo service php7.4-fpm restart

查看 php8.1-fpm 服务是否成功开启(php7.4-fpm同理)

> sudo service php8.1-fpm status
>
> netstat -anp | grep fpm	# 可以看见 127.0.0.1:9000 已经被监听了

设置开机自启动

> sudo systemctl enable php7.4-fpm
>
> sudo systemctl enable php8.1-fpm

### 数据库

这里用MySQL来当数据库

下面请按步骤来走

#### 安装MySQL数据库

```bash
#在apt仓库自带mysql
sudo apt install mysql-server
```

#### 初始化设置 step1

为之后wordpress使用提前配置好mysql服务

```bash
#打开初始化设置
sudo mysql_secure_installation

#1 VALIDATE PASSWORD PLUGIN 密码强度验证器 >选y或n都行
#2 输入有效密码 >选y确认
#3 Remove anonymous users? 移除匿名访问权限 这个先不要禁止 >选n
#4 Disallow root login remotely? 禁止高权限用户远程登录 >选y
#5 Remove test database and access to it? 移除test默认数据库 >选n
#6 Reload privilege tables now? 重新加载授权信息 >选y

#使用root用户登录以进行下一步操作
sudo mysql -uroot -p
```

#### 安装phpmyadmin管理数据库

apt源也是自带phpmyadmin的

```bash
#直接通过 apt 安装就可以
sudo apt-get install phpmyadmin
##第一个可视化界面选择 apache2 回车即可
##第二个可视化界面先按小键盘↓键拉到最低 然后按 TAB 键选择 OK 再回车
##第三个和第四个可视化界面用于设置初始密码 输入完了也是按 TAB 选择 OK

#设置软连接(快捷方式)
sudo ln -s /usr/share/phpmyadmin /srv/www/phpmyadmin
##这里如果想删除软链接就 rm -f /srv/www/phpmyadmin
##注意别在末尾加/ 也不要把 -f 变成 -rf
```

#### 配置phpmyadmin在nginx中的内容

为phpmyadmin也创建一个可供网页访问web容器

```bash
#进入工作目录
cd /etc/nginx/sites-available/ && touch phpmyadmin

#打开 phpmyadmin 文件并粘贴以下内容
##下一行开始
server {
	listen 81 default_server;
	listen [::]:81 default_server;
  
    root /srv/www/phpmyadmin;
	server_name xxx.com;

	location / {
		try_files $uri $uri/ = 404;
		index index.php index.html index.htm;
	}

	location ~ \.php$ {
		fastcgi_pass 127.0.0.1:9001;	# 设置监听端口 这里要对应php7.4的监听端口
		fastcgi_param  SCRIPT_FILENAME  $document_root$fastcgi_script_name;	# 设置脚本文件请求的路径
		include fastcgi_params;	# 引入fastcgi的配置文件
	}

}
##上一行结束

#开放81端口 记得也去安全面板打开81端口
sudo ufw allow 81

#设置软连接
sudo ln -s /etc/nginx/sites-available/phpmyadmin /etc/nginx/sites-enabled/

#应用修改
sudo service nginx restart

#此时访问服务器的81端口就可以正常弹出phpmyadmin的界面了
```

#### 初始化设置step2

安全起见 为phpmyadmin设置创建一个可以管理数据库的账号(非root)

```bash
#因为上一步安装了 phpmyadmin 会自动在数据库中创建了一个 phpmyadmin的账号
#需要我们设置相应的账号密码 权限

#首先使用root身份进入mysql
sudo mysql

#输入如下语句
##修改密码
update user set authentication_string=password("你的密码"),plugin='mysql_native_password' where user='phpmyadmin';
##授予权限
GRANT ALL ON *.* TO 'phpmyadmin'@'localhost' IDENTIFIED BY '密码' WITH GRANT OPTION;
GRANT ALL ON *.* TO 'phpmyadmin'@'%' IDENTIFIED BY '密码' WITH GRANT OPTION;
flush privileges;

#然后就可以在phpmyadmin界面中使用相应账户密码登录了
```

#### 初始化设置step3

为wordpress创建专用的数据库

> 1. 数据库名
> 2. 数据库用户名
> 3. 数据库密码
> 4. 数据库主机
> 5. 数据表前缀（table prefix，特别是当您要在一个数据库中安装多个WordPress时）

用phpmyadmin身份登录phpmyadmin页面

左侧新建数据库名为 wordpress 排序方式选 utf8_general_ci 就可以了

## 安装

### 获取wordpress

apt仓库源没有 wordpress 不过这也正常

```bash
#首先以普通用户权限(非root)进入到 /srv/www/ 目录 并获取 wordpress 源码
cd /hone/www/wordpress && wget https://cn.wordpress.org/latest-zh_CN.tar.gz
```

如果前置内容全部配置完毕

则可以直接访问服务器ip就能看见wordpress初始化安装页面

点击开始就可以自动化安装

> 数据库名字 - wordpress
>
> 数据库用户 - phpmyadmin
>
> 数据库密码 - 之前设置的密码
>
> 其他默认

之后可能会出现要手动创建 **wp-config.php** 文件的要求

> 进入工作目录
>
> cd /etc/www/wordpress
>
> 创建文件
>
> touch wp-config.php
>
> 复制粘贴wordpress页面的内容 保存

至此wordpress原生安装配置完毕

## 维护

### 更新wordpress

目前实测自动更新不是很好用

推荐手动更新

> 1，去官网下载最新的 wordpress 包
>
> 2，解压缩
>
> 3，上传 wp-admin 和 ap-includes 文件夹到 /srv/www/wordpress 文件夹中对应替换掉
>
> 4，更新完后再访问wordpress网页的时候可能会提示更新数据库 更新就好
>
