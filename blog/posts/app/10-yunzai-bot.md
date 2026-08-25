---
title: "yunzai-bot"
description: "Yunzai Bot 框架搭建，以及相关开发。"
date: "2022-09-05T04:08:00.000Z"
updated: "2024-12-24T05:50:56.000Z"
tags: []
draft: false
layout: "post"
slug: "yunzai-bot"
---

## Yunzai-Bot 机器人框架

> Yunzai-Bot 框架搭建，以及相关开发

## 介绍

一个很容易上手的 oicq 机器人框架，部署完成后，只需要编写插件即可完成大部分工作

可以在 [项目源地址](https://github.com/Le-niao/Yunzai-Bot)（[备用链接](https://gitee.com/Le-niao/Yunzai-Bot.git)） 找到更详细的介绍

也可以在部署完成后在 [项目插件索引](https://github.com/yhArcadia/Yunzai-Bot-plugins-index) 挑选插件组合成属于自己的 Yunzai-Bot

## 部署服务

### 前提准备

1. 如果想要保持长时间运行，就需要一台不轻易关机的机子，这里推荐使用云服务器（Linux，Windows Server系统均可。个人推荐 Linux，且下文以 Linux 为主）

2. 可以直接获取项目后使用 npm 部署，也可以使用 docker 部署，个人推荐后者。

  npm：需要安装 nodejs，npm 到最新版

  docker：需要安装 docker，docker-compose

3. Redis 数据库

4. 一个 QQ 小号

5. 会查资料

### 获取项目

1. 创建工作目录，这里使用 **~/yunzaibot** 作为主要工作目录**（这里包括下文都要自行替换 user）**

	创建：`mkdir ~/yunzaibot`，并进入工作目录：`cd ~/yunzaibot`

2. 获取项目框架：`git clone --depth=1 -b main https://gitee.com/Le-niao/Yunzai-Bot.git`，进入目录：`cd Yunzai-Bot`

	*当然，如果你的下载网速很慢，也可以直接到项目地址下载项目源码 zip 包，上传到相应目录中解压，注意要能明确自己的路径*

3. 选择使用 npm 或者 docker-compose 部署

### 使用 npm 部署

1. 安装 nodejs：`sudo apt install nodejs`

  安装 redis：`sudo apt install redis`

  安装 pnpm：`npm install pnpm -g`

  安装相关依赖（注意一定要在 **Yunzai-Bot** 目录下）：`pnpm install -P`

  *如果之前安装过相关内容，也会自动提示并跳过；如果之前使用 redis 时设置了密码，需要到后面设置相关内容，请自动跳转*

2. 在 **~/yunzaibot/Yunzai-Bot** 目录下运行程序：`node app`

	如果前面没问题，那这里就可以正常运行提示输入账号密码了

### 使用 docker-compose 部署

1. 安装 docker，[参考链接](https://www.runoob.com/docker/ubuntu-docker-install.html)

2. 安装 docker-compose，这里注意需要安装最新版的 docker-compose，部分旧版本的 ubuntu 系统默认 apt 源只有 **docker-compose 1.25.x** 版本的，**而最新版 1.29.x 需要到 [github](https://github.com/docker/compose/releases) 手动安装**

  安装 docker-compose 1.29.x

```bash
  # 使用 pip 安装（推荐）
  pip install docker-compose==1.29.2
  
  # 使用 bash 安装
  sudo curl -L "https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
  sudo chmod +x /usr/local/bin/docker-compose
  
  # 查看版本
  docker-compose --version
  	docker-compose version 1.29.2, build xxxxxxx
```

3. 以上两项安装完成后，在当前目录 **~/yunzaibot/Yunzai-bot** 下，只需要关注 **docker 文件夹** 以及 **docker-compose.yaml**，可以删除除了 **这两项** 之外其他的文件

4. 修改 docker-compose.yaml 文件，请参考注释信息（映射会自动创建文件夹）

```yaml
  version: "3.9"
  services:
    yunzai-bot:
      container_name: yunzai-bot
      # build: ./docker # 使用 Dockerfile 本地构建
      # image: swr.cn-south-1.myhuaweicloud.com/sirly/yunzai-bot:v3         # 使用云端精简镜像
      image: swr.cn-south-1.myhuaweicloud.com/sirly/yunzai-bot:v3plus   # 推荐使用。扩展镜像，包含 ffmpeg 和 python，这个较大，但是里面的 ffmpeg 和 python 在后续插件开发的时候很有用，特别是 ffmpeg，部分插件需要语音转 amr 需要用到
      # image: sirly/yunzai-bot:v3                                        # Docker Hub源
      # image: sirly/yunzai-bot:v3plus 
      restart: always
      volumes:	# 请注重修改下面的内容中的 user，配置映射目录的目的是方便后续修改相关设置，包括插件（插件必须单一对应映射，js 插件放到 /plugins/example/ 目录下）
        - ~/yunzaibot/config/:/opt/container/Yunzai-Bot/config/config/                 # Bot基础配置文件
        - ~/yunzaibot/genshin_config:/opt/container/Yunzai-Bot/plugins/genshin/config  # 公共Cookie，云崽功能配置文件
        - ~/yunzaibot/logs:/opt/container/Yunzai-Bot/logs                              # 日志文件
        - ~/yunzaibot/data:/opt/container/Yunzai-Bot/data                              # 数据文件
        # 以下目录是插件目录，安装完插件后需要手动添加映射，即修改这个 yaml 文件对应映射目录后，重新执行 docker-compose up
        # - ~/yunzaibot/plugins/miao-plugin:/opt/container/Yunzai-Bot/plugins/miao-plugin                  # 喵喵插件
        # - ~/yunzaibot/plugins/py-plugin:/opt/container/Yunzai-Bot/plugins/py-plugin                      # 新py插件
        # - ~/yunzaibot/plugins/xiaoyao-cvs-plugin:/opt/container/Yunzai-Bot/plugins/xiaoyao-cvs-plugin    # 图鉴插件
      depends_on:
        redis: { condition: service_healthy }
  
    redis:
      container_name: yunzai-redis
      image: redis:alpine
      restart: always
      volumes:	# 这里也要修改
        - ~/yunzaibot/redis/data:/data
        - ~/yunzaibot/redis/logs:/logs
      healthcheck:
        test: [ "CMD", "redis-cli", "PING" ]
        start_period: 10s
        interval: 5s
        timeout: 1s
```

5. 部署：`sudo docker-compose -f ~/yunzaibot/Yunzai-bot/docker-compose.yaml up -d`

6. 等待部署完成后，进入 docker 镜像管理账号信息：`docker exec -it docker的id(如何获取请自查) sh`，登录账号：`npm run login`，然后按照提示操作即可

### 相关设置

如果是按照前文中的 docker-compose 来部署服务的，就会在这里找到对应的文件夹信息（使用 npm 部署，则也可以在 Yunzai-Bot 文件夹中找到相应信息）

```ini
yunzaibot
	Yunzai-bot	# docker-compose 必要文件
	config	# 框架总体配置
	data	# 框架配置信息
	logs	# 日志文件
	plugins	# 插件，后续插件信息都在这里
	redis	# 数据库信息，一般不用改
```

其本身写的很清楚了，一般按照给的去修改不会有啥问题，修改完如果没生效，就执行：`sudo docker-compose -f ~/yunzaibot/Yunzai-bot/docker-compose.yaml up -d`，重新部署服务（重启）

## 插件

占位符

## 参考&致谢

1. [项目 github](https://github.com/Le-niao/Yunzai-Bot)
2. [插件目录](https://github.com/yhArcadia/Yunzai-Bot-plugins-index)
3. [docker 安装](https://www.runoob.com/docker/ubuntu-docker-install.html)
4.
