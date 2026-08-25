---
title: "app | minecraft_server_build_records"
description: "server build record for minecraft."
date: "2024-03-07T04:38:00.000Z"
updated: "2024-04-21T02:43:05.000Z"
tags: []
draft: false
layout: "post"
slug: "minecraft-server-build"
source: "online/43-minecraft-selfhost-server-build-up-record.md"
---

## minecraft-server-build-record

建议读者使用 unix like 环境进行 java edition 开服，以下文章环境以 **ubuntu 18.04** 为例；~~互通服、插件服~~ 等以后有空了更新

## main

主要思路如下：

1.   创建主文件夹，这里以 `~/minecraft` 为例，后续只写 `minecraft/`
2.   **初次运行，需要配置 java 环境**，为了适应不同的 minecraft server，有时需要使用不同的 java 版本，因此个人建议使用 binary 的 java 版本，通过 `update-alternatives` 更新 `/bin/java` 的动态链接，实现切换自由；通过 `java --version` 查看使用的版本
3.   创建一个文件夹作为 server 目录，下以 `minecraft/minecraft-v1201` 为例
4.   在 pc 上选择自己想要装载的 mod，打包成 zip，将其通过 filezilla 等 ftp 软件传输到服务器的 `minecraft/minecraft-v1201/mods` 目录下，解压之：`unzip mods.zip -d minecraft-v1201/mods`；
5.   使用 forge-installer 安装 forge 和 server
6.   启动服务器，修改配置文件，启动服务器

### java env

1.   可以在 [这里](https://adoptium.net/zh-CN/temurin/releases/) 获取 java 的不同 binary 版本，选择对应架构即可，注意选择 jdk 以减少出错

2.   创建一个用于存放 java binary 的文件夹：`mkdir minecraft/tools/openjdk-binaries`，`cd minecraft/tools/openjdk-binaries`

3.   将下载到的 tar.gz 包传到该目录下，以 `OpenJDK17U-jdk_x64_linux_hotspot_17.0.10_7.tar` 为例，并解压：`tar -zxvf OpenJDK17U-jdk_x64_linux_hotspot_17.0.10_7.tar`，得到 `minecraft/tools/openjdk-binaries/jdk-17.0.10+7`

4.   创建一个 shell 脚本：`touch minecraft/tools/openjdk-binaries/install-openjdk.sh`，`chmod +x minecraft/tools/openjdk-binaries/install-openjdk.sh`；写入以下内容：

     ```shell
     #!/bin/bash
     
     # update-alternatives --install [/usr/bin/目标下的bin] [系统注册名称] [bin实际地址] [优先级越大越优先]
     update-alternatives --install /usr/bin/java java ~/minecraft/tools/openjdk-binaries/jdk-17.0.10+7/bin/java 1
     update-alternatives --install /usr/bin/javac javac ~/minecraft/tools/openjdk-binaries/jdk-17.0.10+7/bin/javac 1
     update-alternatives --install /usr/bin/javadoc javadoc ~/minecraft/tools/openjdk-binaries/jdk-17.0.10+7/bin/javadoc 1
     update-alternatives --install /usr/bin/javap javap ~/minecraft/tools/openjdk-binaries/jdk-17.0.10+7/bin/javap 1
     
     sudo update-alternatives --config java
     ```

     注：ubuntu 自带 `update-alternatives`，其他分发版自行找相关指令

5.   执行 `minecraft/tools/openjdk-binaries/install-openjdk.sh`，此时会让选择 java 版本（如果装过多个的话），选择即可

6.   使用 `java --version` 查看 java 版本

### forge install

（可选）为了照顾网络不好的地区，推荐：`touch minecraft/tools/proxy.txt`，并写入以下内容（自行配置代理信息）：

```shell
-Dhttp.proxyHost=127.0.0.1
-Dhttp.proxyPort=7890
-Dhttps.proxyHost=127.0.0.1
-Dhttps.proxyPort=7890
```

#### new

特指 1.18.x 以上版本的 forge installer

1.   到 [minecraftforge](https://files.minecraftforge.net/net/minecraftforge/forge/) 获取对应 server 的 forge-installer.jar，这里以对应 minecraft 1.20.1 的 `foge-47.2.20-installer.jar` 为例
2.   将其上传到目标目录 `minecraft/minecraft-v1201`
3.   安装 forge-server：`java -jar forge-47.2.20-installer.jar --installServer`；或者：`java @minecraft/tools/proxy.txt -jar forge-x.xx.x-installer.jar --installServer`
4.   在命令行出现：**The server installed successfully**，则安装完成，可以删除 `forge-47.2.20-installer.jar` 了

如果是旧版本的，需要多加一步：到 [mcversions](https://mcversions.net/) 下载对应版本的 server 文件，传到同目录下，且安装指令修改成

### start

1.   修改 `minecraft/minecraft-v1201/user_jvm_args.txt`，以下是参考

     ```shell
     -Xms6G
     -Xmx6G
     -server
     -XX:+UseG1GC
     -XX:-UseAdaptiveSizePolicy
     -XX:-OmitStackTraceInFastThrow
     -Dfml.ignoreInvalidMinecraftCertificates=True
     -Dfml.ignorePatchDiscrepancies=True
     -Dfile.encoding=utf-8
     -Dhttp.proxyHost=127.0.0.1
     -Dhttp.proxyPort=7890
     -Dhttps.proxyHost=127.0.0.1
     -Dhttps.proxyPort=7890
     ```

2.   修改启动脚本：`minecraft/minecraft-v1201/run.sh`，以下是参考

     ```shell
     #!/usr/bin/env sh
     
     cd ~/minecraft/minecraft-v1201
     java @user_jvm_args.txt @libraries/net/minecraftforge/forge/1.20.1-47.2.20/unix_args.txt "$@" nogui
     ```

3.   然后启动脚本即可，`chmod +x minecraft/minecraft-v1201/run.sh`，`minecraft/minecraft-v1201/run.sh`；初次运行必定退出，阅读了 minecraft 的 [eula](https://aka.ms/MinecraftEULA) 文件后，将同目录下 `eula.txt` 文件中的 false 改成 true，再次启动，直到出现命令行

4.   如果服务器无法正常运行，从命令行中提取错误的 mod 来排错，例如 `[3D皮肤层] skinlayers3d.jar`，这是一个客户端渲染 mod，服务器无效，则需要手动将其删除，或者将后缀改成任意不是 `.jar` 的后缀

5.   按照上述操作完成后，目录拓扑结构应该如下：

     ```bash
     ~/minecraft/minecraft-v1201
     ├── ...
     ├── eula.txt	# 许可文件
     ├── libraries	# 核心文件
     ├── mods		# 上传的 mods 文件
     ├── server.properties	# 服务器配置文件
     ├── run.sh		# 启动脚本
     ├── world		# 服务器存档
     └── ...
     ```

     文末附上 `server.properties` 配置文件

## ex

### 配置外置登录

为了防止滥用登录，服务器一般都会添加正版验证，而为了没有购买 minecrat 正版的朋友能够进服，这里提出了一种外置 hook 登录的方法，即整个登录流程全部采用第三方认证服务器，这项技术的源码：[yushijinhun/authlib-injector](https://github.com/yushijinhun/authlib-injector.git)，比较大的服务器有 [littleskin](https://littleskin.cn/) 等；下面介绍外置登录的实现方式

1.   到 release 下载 `authlib-injector-1.2.5.jar` 文件，上传到 `minecraft/tools` 目录下
2.   到前文的启动脚本中 `minecraft/minecraft-v1201/user_jvm_args.txt` 添加一行内容 `-javaagent:~/minecraft/tools/authlib-injector-1.2.5.jar=https://littleskin.cn/api/yggdrasil`，后面的地址可以在 littleskin 的手册中找到
3.   正常启动脚本即可，注意：开启了第三方验证后，原正版 mc 账号将无法登录，需要都去 littleskin 上注册账号，并在各启动器（hmcl、pcl 等）启动时输入 littleskin 的账号才能进入服务器

### mods + plugin

新一代可兼容 forge/fabric mods 和 bukkit/spigot plugins 的服务器 [mohistMC](https://mohistmc.com/)，有兼容 forge + plugins 的 mohist 和 fabric + plugins 的 banner 两个版本





### 互通服

#### spigot

参考：[Spigot 架設多人遊玩的 Minecraft 伺服器-以 Ubuntu 環境中示範](https://www.kjnotes.com/freeware/93)

1.   获取 spigot 对应 build 文件，[spigot](https://www.spigotmc.org/)
2.   在目录下执行：`java -jar BuildTools.jar --rev 1.19.4`，后面是指定要安装的版本
3.   然后即可获得一个不加 mod 的 java edition 服务器

#### geyser

参考：[Minecraft Geyser 互通服开服指南](https://doc.natfrp.com/offtopic/mc-geyser.html)

1.   选择使用 geyser-spigot 版本，[geyser](https://ci.opencollab.dev//job/GeyserMC/job/Geyser/job/master/)

## server.properties

```properties
#Minecraft server properties
#[星期] [月份] [日期] [时间] CST [年份]
# 自动生成配置文件时附带的时间记录功能，可删除或忽略。

enable-jmx-monitoring = false
# 是否允许 JMX 监视
# 允许值:
#   是: true
#   否: false

rcon.port = 25575
# 远程控制端口
# 允许值: [1, 65535]

level-seed =
# 为世界定义一个种子
# 缺省值为随机

gamemode = survival
# 为新玩家设置游戏模式
# 允许值: 
#   生存: survival
#   创造: creative
#   冒险: adventure

enable-command-block = false
# 是否启用命令方块
# 允许值:
#   是: true
#   否: false

enable-query = false
# 是否启用查询功能
# 允许值:
#   是: true
#   否: false

generator-settings = {}
# 世界生成器设置

level-name = world
# 世界名称

motd = A Minecraft Server
# MOTD 时显示的服务器名称

query.port = 25565
# 查询端口
# 允许值: [1, 65535]

pvp = true
# 是否允许 PVP (玩家间攻击)

generate-structures = true
# 是否允许自然生成结构
# 允许值:
#   是: true
#   否: false

difficulty = easy
# 设定世界的难度
# 允许值: 
#   和平: peaceful
#   简单: easy
#   普通: normal
#   困难: hard

network-compression-threshold = 256
# 要压缩的原始网络有效负载的最小大小
# 允许值 : [0, 65535]

require-resource-pack = false
# 强制客户端加载服务端资源包
# 允许值:
#   是: true
#   否: false

max-tick-time = 60000
# 最长单个游戏刻时间。单个游戏刻加载超过此时长后，服务器将自动关闭。
# 允许值: [0, ∞]

use-native-transport = true
# 是否启用 Linux 的数据包优化功能
# 允许值:
#   是: true
#   否: false

max-players = 20
# 服务端上可以同时在线的最大玩家数。
# 允许值: [1, ∞]

online-mode = true
# 是否根据 Minecraft 账号数据库对玩家进行身份验证
# 启用后，仅正版账号玩家可加入游戏。
# 允许值: 
#   是: true
#   否: false

enable-status = true
# 是否允许在玩家的服务器列表界面中显示在线状态
# 允许值: 
#   是: true
#   否: false

allow-flight = false
# 在安装了可飞行的 mod 时，是否允许生存模式玩家飞行
# 若设置为否，则玩家悬空 5 秒后将被踢出游戏。
# 允许值: 
#   是: true
#   否: false

broadcast-rcon-to-ops = true
# 是否将远程控制台命令的输出发送给所有在线的管理员
# 允许值: 
#   是: true
#   否: false

view-distance = 10
# 设置服务端向客户端发送的区块数量半径，即视距。
# 允许值: [3, 32]

server-ip =
# 设置进入服务器的玩家是否仅限于指定的 IP 地址。
# 缺省值为不作限制

resource-pack-prompt =
# 设置在使用资源包时，在资源包提示符上显示的自定义文本。
# 仅在 require-resource-pack 启用时有效。
# 缺省值为不自定义文本

allow-nether = true
# 是否允许玩家前往下界
# 允许值: 
#   是: true
#   否: false

server-port = 25565
# 设置服务端监听的端口。
# 允许值: [1, 65535]

enable-rcon = false
# 是否允许服务器对控制台的远程访问
# 允许值: 
#   是: true
#   否: false

sync-chunk-writes = true
# 是否允许同步区块写入
# 允许值: 
#   是: true
#   否: false

op-permission-level = 4
# 设置管理员的权限级别。
# 允许值: [0, 4]

prevent-proxy-connections = false
# 是否禁止使用代理连接服务器
# 如果从服务器发送的 ISP/AS 与 Mojang 认证服务器发送的不同，则玩家将被踢出。
# 允许值: 
#   是: true
#   否: false

hide-online-players = false
# 是否在服务器列表中的状态信息中显示在线玩家列表
# 允许值: 
#   是: true
#   否: false

resource-pack =
# 资源包的 URL 地址。
# URL 中，: 及 = 需要在其前一个字符的位置添加 \ 以转义。
# 缺省值为不设置

entity-broadcast-range-percentage = 100
# 设置实体信息发送至客户端前，需离相应玩家有多近。
# 使用百分比表示，如 50 为正常值的一半。
# 允许值: [0, 100]

simulation-distance = 10
# 设置模拟距离半径。
# 若一个实体在该范围之外，则玩家不会看到该实体。
# 允许值: [1, ∞]

rcon.password =
# 设置远程控制的密码。
# 缺省值为不设置

player-idle-timeout = 0
# 设置玩家无操作后踢出的时间，单位为分钟。
# 在服务器收到如下数据包类型之一时，该计时将被重置：
#   单击窗口、附魔物品、更新签名、挖掘、放置方块、更改手持物品、
#   播放动画、与实体交互、客户端状态变化、发送消息、使用实体。
# 允许值: [1, ∞]

force-gamemode = false
# 设置游戏模式。
# 允许值: 
#   生存: survival
#   创造: creative
#   冒险: adventure

rate-limit = 0
# 设置用户被踢出前最多可发送的数据包量。
# 允许值: [1, ∞]

hardcore = false
# 是否启用极限模式
# 在设置为 "是" 后，服务器难度将被忽略并始终固定为困难。
# 玩家死亡后，其游戏模式将被切换为旁观者模式。
# 允许值: 
#   是: true
#   否: false

white-list = false
# 是否启用白名单模式
# 如果值为 true，则必须在 whitelist.json 文件中列出所有连接的玩家。
# 允许值:
#   是: true
#   否: false

broadcast-console-to-ops = true
# 是否将控制台输出发送至所有在线管理员
# 允许值:
#   是: true
#   否: false

spawn-npcs = true
# 是否允许生成村民
# 允许值:
#   是: true
#   否: false

spawn-animals = true
# 是否生成动物
# 允许值:
#   是: true
#   否: false

function-permission-level = 2
# 函数文件的默认权限等级
# 允许值: [0, 4]

level-type = default
# 设置世界类型
# 允许值:
#   标准: default
#   平坦: flat
#   巨型生物群系: largeBiomes
#   放大: amplified

text-filtering-config =
# (需要更多信息)

spawn-monsters = true
# 是否生成怪物
# 允许值:
#   是: true
#   否: false

enforce-whitelist = false
# 是否强制执行白名单
# 启用后，在 whitelist.json 文件重载后，不在白名单中的在线玩家将被踢出游戏。
# 允许值:
#   是: true
#   否: false

resource-pack-sha1 =
# 设置资源包的 SHA1 值，以验证资源包完整性。

spawn-protection = 16
# 设置出生保护区域的大小，0 为禁用该功能。
# 允许值: [0, ∞]

max-world-size = 29999984
# 设置最大的世界边界半径，单位为方块。
# 允许值: [1, 29999984]

# max-chained-neighbor-updates = 0
# 设置连锁更新 NC 的数量，超过此限制的 NC 更新会被跳过。若为负数则无限制。
# 仅在 1.19 及更高版本有效。
# 允许值: [∞, ∞]

# enforce-secure-profile = true
# 是否强制要求使用签名公钥
# 启用后，玩家必须具有由 Mojang 签名的公钥，才能进入服务器。
# 仅在 1.19 及更高版本有效，1.19 默认值为 false。
# 允许值:
#   是: true
#   否: false

# previews-chat = true
# 是否启用聊天预览功能
# 仅在 1.19 至 1.19.2 有效。
# 允许值:
#   是: true
#   否: false

initial-disabled-packs =
# 不会自动启用的数据包名称
# 仅在 1.19.3 及更高版本有效。

initial-enabled-packs = vanilla
# 在创建世界过程中，需要启用并加载的数据包名称
# 仅在 1.19.3 及更高版本有效。
```

## references

1.   minecraft server 对照信息，[MCVERSIONS](https://mcversions.net/)
2.   [MinecraftServerHostGuide](https://mhy278.github.io/MinecraftServerHostGuideHtml/)
3.   [Minecraft 开服：从入门到精通](https://blog.csdn.net/Markus_xu/article/details/117793415)
