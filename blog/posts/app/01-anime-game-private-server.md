---
title: "anime-game-private-server-build-records"
description: "gayshit, grasscutter, mitm"
date: "2024-02-21T12:58:00.000Z"
updated: "2024-08-20T02:37:46.000Z"
tags: []
draft: false
layout: "post"
slug: "anime-game-private-server"
---

## anime-game-private-server-build-records

>   使用 grasscutter 和 mitm proxy 架设 gayshit（下称 gs ） 私人服务器

敬告

尊重知识产权，请您支持正版软件，切勿使用盗版软件。本项目仅用于测试和学习 java 项目的构建，请任何读者在试用后 24 小时内删除。

这玩意也就图一乐，很多功能都是残疾的，顶多体验一下抽卡和命座，玩几个小时体验完爽感就无聊了，真体验还得是原游戏持续更新的剧情等内容

## 环境准备

1.   服务端：架设 grasscutter 服务器以及 mongodb 服务，以下文章为在 ubuntu 20.04 上构建为例
2.   客户端
     1.   pc 端，Windows
     2.   Android 端
     3.   ios 端
3.   软件依赖支持
     1.   python
     2.   java
     3.   grasscutter
     4.   mongodb
4.   确定连接地址
     1.   mongodb 数据库开放端口：17000/tcp
     2.   grasscutter 服务开放端口：17001/tcp
     3.   grasscutter-game 数据交互端口：17002/udp

## 详细步骤

### 确保 java 17+ 环境

安装 java 17+ 环境，使用 `java --version` 查看系统是否支持 java 17+ 依赖

或者，直接获取 jdk 17+ 可执行程序，以下步骤以该方式为主

### 安装 mongodb

推荐直接使用 binary 文件启动数据库，不需要再手动安装和配置相应文件，[下载地址](https://www.mongodb.com/try/download/community-kubernetes-operator)，选择合适自己的架构，这里以 ubuntu-20.04 为例，则最后获取到的下载地址为：`https://fastdl.mongodb.org/linux/mongodb-linux-x86_64-ubuntu2004-6.0.8.tgz`

解压后，其中应该有一个 bin 文件夹，里面包含 mongod 这个可执行文件

启动 mongodb 数据库：`mongod --dbpath ./db --port 17000`

### 安装 grasscutter

1.   直接从 [relaeses](https://github.com/Grasscutters/Grasscutter/releases) 获取 grasscutter-x.x.x.jar 文件；

2.   （可选）若想要自己编译，请参照以下步骤

     1.   获取源码：`git clone --recurse-submodules -b development https://github.com/Grasscutters/Grasscutter.git grasscutter`，注意使用的是 development 的 branch

     2.   编译

          1.   进入到源码目录

          2.   使用 gradlew 编译 jar 包：

               1.   如果使用的 windows 架设，可以直接执行目录下的 `gradlew.bat` 自动编译，这里主要讨论 Linux 下架设

               2.   使用以下脚本文件：

                    ```shell
                    #!/bin/bash
                    
                    # 进入工作目录
                    cd /srv/www/genshin/grasscutter/repo
                    
                    # 设置 grasscutter 和 java 可执行程序的文件夹路径
                    APP_BASE_NAME=grasscutter
                    GRASSCUTTER_DIR=/srv/www/genshin/grasscutter/repo
                    JAVA_BINARY_DIR=/srv/www/genshin/jdk-17.0.5
                    JAVA_BINARY="$JAVA_BINARY_DIR/bin/java"
                    
                    # 检测 GRASSCUTTER_DIR 是否设置正确
                    if [ ! -d "$GRASSCUTTER_DIR" ]; then
                      echo "ERROR: GRASSCUTTER_DIR is not set or the directory does not exist: $GRASSCUTTER_DIR"
                      exit 1
                    fi
                    
                    # 检测 JAVA_BINARY_DIR 是否设置正确
                    if [ ! -d "$JAVA_BINARY_DIR" ]; then
                      echo "ERROR: JAVA_BINARY_DIR is not set or the directory does not exist: $JAVA_BINARY_DIR"
                      exit 1
                    fi
                    
                    # Add default JVM options here. You can also use JAVA_OPTS and GRADLE_OPTS to pass JVM options to this script.
                    DEFAULT_JVM_OPTS="-Xmx2048m -Xms1024m"
                    
                    # Check if Java is installed and executable
                    if ! "$JAVA_BINARY" -version > /dev/null 2>&1; then
                        echo "ERROR: JAVA_BINARY_DIR is not set or Java is not executable."
                        echo "Please set the JAVA_BINARY_DIR variable in your environment to match the"
                        echo "location of your Java installation."
                        exit 1
                    fi
                    
                    # Setup the classpath
                    CLASSPATH="$GRASSCUTTER_DIR/gradle/wrapper/gradle-wrapper.jar"
                    
                    # Execute Gradle
                    # echo "$JAVA_BINARY" $DEFAULT_JVM_OPTS "-Dorg.gradle.appname=$APP_BASE_NAME" -classpath "$CLASSPATH" org.gradle.wrapper.GradleWrapperMain "$@"
                    
                    CMD="$JAVA_BINARY \
                         $DEFAULT_JVM_OPTS \
                         -Dhttp.proxyHost=127.0.0.1 \
                         -Dhttp.proxyPort=7890 \
                         -Dhttps.proxyHost=127.0.0.1 \
                         -Dhttps.proxyPort=7890 \
                         -Dorg.gradle.appname=$APP_BASE_NAME \
                         -classpath $CLASSPATH \
                         org.gradle.wrapper.GradleWrapperMain \
                         $@"
                    
                    exec $CMD
                    
                    exit 0
                    ```
               
               3.   填写以上脚本文件中的 `GRASSCUTTER_DIR` 和 `JAVA_BINARY_DIR` 项，然后执行，等待自动编译完成（注意这里需要到 7890 代理工具下载一些过程中使用到的组件）

3.   拿到对应的 jar 包后，将其移动到一个干净的工作目录，执行 `java -jar grasscutter-x.x.x.jar`，会在相同目录下生成 resources 等文件夹，其中目录结构应该如下：

     ```bash
     ├── config.json
     ├── data
     ├── grasscutter-x.x.x.jar
     ├── logs
     └── resources
         ├── BinOutput
         ├── ExcelBinOutput
         ├── Scripts
         ├── ScriptSceneData
         ├── Server
         └── TextMap
     ```

4.   配置 config.json 文件，其中，主要修改以下内容

     1.   `databaseInfo` 项，修改 mongodb 的端口为上述 17000 相同
     2.   `server.http.accessAddress` 项，修改成想要客户端连接的端口
     3.   `game.bindPort` 项，修改成游戏正式启动的端口

5.   从 [Resources](https://gitlab.com/YuukiPS/GC-Resources) 处获取 **相应的版本** 资源放到对应目录下

#### plugins

1.   https://github.com/NotThorny/AttackModifier
2.   https://github.com/snoobi-seggs/FuckPaimonPlugin
3.   https://github.com/snoobi-seggs/AttackInfusedWithItem
4.   https://github.com/jie65535/gc-opencommand-plugin
5.   https://github.com/liujiaqi7998/GrasscuttersWebDashboard
6.   https://github.com/jie65535/gc-opencommand-plugin
7.   https://github.com/NotThorny/setLevel
8.   https://github.com/Penelopeep/SwitchElementTraveller
9.   https://github.com/Penelopeep/TeamMerge

## 配置客户端

1.   下载游戏本体文件，这里选择国服或国际服均可
2.   下载 patch 文件：[34736384/RSAPatch](https://github.com/34736384/RSAPatch)，从 release 获取最新版，然后将其更名为 `mhypbase.dll`，放到和启动游戏的程序同目录下

## 参考

1.   [grasscutter 使用指南——Android/Windows/IOS端均已支持](https://juejin.cn/post/7124213726730797063)
2.   [Grasscutters/Grasscutter](https://github.com/Grasscutters/Grasscutter)
3.   [GrassCutter使用教程](https://blog.csdn.net/qq_41242689/article/details/125828156)
4.   [grasscutter 资源文件](https://gitlab.com/YuukiPS/GC-Resources)
5.   [面向萌新的连接 grasscutter 服务器教程](https://fudaoyuan.icu/2022/05/16/面向萌新的连接grasscutter服务器教程/)
6.   [Genshin PS-Grasscutter](https://blog.btjawa.top/?p=244)
7.   真端 3.4 公益服，https://nas.sxww.run:8000/
8.   真端 3.2，https://www.youtube.com/watch?v=PGKV6nzJ0o0
