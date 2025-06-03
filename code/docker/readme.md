# cmd

## 常用

1. 运行：
    1. 运行一个 docker 镜像并绑定 80 端口：`docker run -d -p 80(主机端口):80(镜像端口) docker_id`
    2. 运行一个 docker 镜像，并进入其交互的 shell：`docker run -it --rm -p 8080:80 docker_id`
    3. 运行一个 docker 镜像，挂载目录映射：`docker run -it -v "/tmp/tmp:/tmp/tmp" -p 8080:80 docker_id`
2. 停止某个 docker 镜像：`docker stop docker_id`
3. 复制文件到 docker 镜像中：`docker cp src-path docker_id:dst-path`
4. 查看正在运行的 docker 列表：`docker ps`
5. 查看所有的镜像：`docker images`
6. 删除某个 docker 镜像：`docker rmi docker_id`
7. 创建一个 docker 备份（快照）：`docker commit -p CONTAINER_ID NEW_CONTAINER_BACKUP`
8. 将 docker 保存为 tar 格式（用于迁移）：`docker save -o ~/CONTAINER_BAK.tar(保存目标) CONTAINER_ID(保存原镜像)`
9. 加载 tar 格式的镜像（用于迁移）：`docker load -i ~/CONTAINER_BAK.tar`
10. 修改 docker 的 TAG 和 REPOSITORY：`docker tag CONTAINER_ID REPOSITORY:TAG`
11. 查看日志：`docker logs -f -t --tail 502 CONTAINER_ID`
12. 修改 docker 名称：`docker tag old_repository:tag new_repository:tag`

## 进入

```bash
docker container
docker ps
sudo docker exec -u root -it CONTAINER_ID /bin/bash
```

## 删除

```bash
docker rmi CONTAINER_ID
docker image prune -a	# 删除所有废弃的镜像
docker rm `docker ps -a | grep Exited | awk '{print $1}'` # 列出所有已停止镜像并删除
docker rm `docker ps -a | grep <none> | awk '{print $1}'`	# 列出所有已停止的镜像并删除
```

## 获取信息

```bash
sudo docker exec CONTAINER_ID hostname # 直接获取信息
docker inspect CONTAINER_ID

docker cp CONTAINER_ID:/config /tmp/config	# 获取文件
docker system df    # 查看 docker 磁盘使用情况
```

## 安装

```bash
sudo apt-get install apt-transport-https ca-certificates curl gnupg-agent software-properties-common
sudo apt-get install docker-ce	# 注：在ubuntu20 下 直接 apt install docker.io

# 设置开机自启动
sudo systemctl enable docker
sudo systemctl start docker
```

## 卸载

```bash
sudo apt-get remove docker docker-engine docker.io containerd runc
sudo apt-get update
```

## 数据迁移

如果没有映射 docker 到本机，有两种方法来做数据迁移：

1. 手动复制出 docker 中的数据，在新机器上再挂载上
2. 直接打包 docker 及其 volume

## docker-compose

`dockerfile` 模板：

```dockerfile
FROM mcr.microsoft.com/vscode/devcontainers/python:3.10-bookworm

ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

ENV WORKDIR="/opt/test"

RUN sed -i 's|http://archive.ubuntu.com/ubuntu/|http://mirrors.ustc.edu.cn/ubuntu/|g' /etc/apt/sources.list && \
    sed -i 's|http://security.ubuntu.com/ubuntu/|http://mirrors.ustc.edu.cn/ubuntu/|g' /etc/apt/sources.list

RUN apt-get update && apt-get install -y \
    net-tools curl wget \
    gnupg2 \
    software-properties-common \
    build-essential \
    vim

RUN add-apt-repository ppa:deadsnakes/ppa && \
    apt-get update && \
    apt-get install -y python3.10 python3.10-dev python3.10-distutils python3.10-venv && \
    curl https://bootstrap.pypa.io/get-pip.py | python3.10

RUN rm -rf /var/lib/apt/lists/*

RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.10 1
RUN ln -s /usr/bin/python3.10 /usr/bin/python

RUN pip install --ignore-installed pyserial flask eventlet flask_socketio

RUN mkdir -p $WORKDIR/log $WORKDIR/server $WORKDIR/client
```

`docker-compose.yml` 模板：

```yaml
version: "3"
services:
  container_name:
    image: owner/dockername:latest
    container_name: container_name
    environment:
      - UID=1000
      - GID=1000
      - CONTAINER_TIMEZONE=Asia/Shanghai
    tty: true
    stdin_open: true
    volumes:
      - /host:/docker
    ports:
      - 80:80	# host:docker
    restart: always

# sudo docker-compose -f docker-compose.yml up -d
```

## create-docker

在 [这里](https://mcr.microsoft.com/en-us/) 找一些好用的基础镜像：

1. ubuntu 22.04 docker 镜像：`docker pull mcr.microsoft.com/devcontainers/base:jammy`
2. python 开发镜像：`docker pull mcr.microsoft.com/devcontainers/python:dev-3.10-buster`
3. arm 环境镜像：`docker pull mcr.microsoft.com/deployment-environments/runners/arm:latest`

也可以自己搭建一个好用的镜像：

1. 有以下 [常见操作](https://www.majo.im/index.php/wkyuu/342.html)：
2. 将构建好后的 docker 镜像进行脱敏并打包
    1. `rm -rf /var/log `
    2. `docker ps`、`docker stop container_id`、`docker commit container_id my_container:tag`、`docker save -o my_container.tar my_container:tag`

以下是自己构建的一些镜像，直接下载并 `docker -i xxx.tar` 即可

## devcontainer

microsoft 的 vscode 自带一套很好用的自动化起 docker 流程

1. 创建一个空文件夹

2. 在空文件夹下，创建对应文件：`mkdir .devcontainer`，`touch .devcontainer/devcontainer.json`，写入以下内容（参考）

	```json
	// For format details, see https://aka.ms/devcontainer.json.
	{
	    "name": "dev-ubuntu",
	    "image": "mcr.microsoft.com/devcontainers/base:jammy",
	    "runArgs": ["--privileged"],
	    "mounts": [
	            "source=/dev,target=/dev,type=bind"
	    ],
	    "postCreateCommand": "sudo apt-get update && sudo apt-get install -y git wget flex bison gperf python3 python3-pip python3-venv cmake ninja-build ccache libffi-dev libssl-dev dfu-util libusb-1.0-0",
	    "customizations": {
	            "vscode": {
	                    "extensions": [
	                            "ms-vscode.cpptools"
	                    ]
	            }
	    },
	    "remoteUser": "root"
	}
	```

3. 在 vscode 的拓展商店里安装 devcontainer 插件

4. 左下角 "在容器中重新打开"

## sth

1. 添加用户组，目的是不再需要 `sudo` 去管理 docker：`sudo usermod -aG docker user`

2. docker 换源
    1. 新建配置文件：`sudo vim /etc/docker/daemon.json`
    2. 修改内容参考：
        ```json
        {
        	"registry-mirrors": [
        		"https://docker.m.daocloud.io",
        		"https://noohub.ru",
        		"https://huecker.io",
        		"https://dockerhub.timeweb.cloud"
        	]
        }
        ```
    3. 重启 docker：`sudo systemctl restart docker`
    4. 使用 `docker info | grep Mirrors -A 3` 查看换源情况

3. docker 修改默认网段，主要是别和一些公司的内网默认 172 段撞了，

    1. `sudo vim /etc/docker/daemon.json`：

        ```json
        {
            "default-address-pools" : [
                {
                  "base" : "10.172.0.0/12",
                  "size" : 20
                },
                {
                  "base" : "10.168.0.0/16",
                  "size" : 24
                }
            ]
        }
        ```

    2. 如果已经启动了 docker，且出现了其他遗留的网段，需要依次停止、删除默认网络：

        ```bash
        $ for i in `docker ps -q`; do docker stop $i; done
        $ docker network prune
        ```

    3. 重启 docker daemon：`sudo systemctl restart docker`，和各 docker 镜像即可

4. 配置 docker 使用代理，[参考](https://www.lfhacks.com/tech/pull-docker-images-behind-proxy/)
    1. docker pull 的代理：`sudo mkdir /etc/systemd/system/docker.service.d`，创建文件：`sudo vim /etc/systemd/system/docker.service.d/proxy.conf`，编写以下内容：
        ```ini
        [Service]
        Environment="HTTP_PROXY=http://198.18.0.1:1080"
        Environment="HTTPS_PROXY=http://198.18.0.1:1080"
        Environment="NO_PROXY=localhost,127.0.0.1"
        ```

        适当修改对应代理信息，修改完成后
        1. `sudo systemctl daemon-reload`，
        2. 重启 docker：`sudo systemctl restart docker.service`
    2. 容器想要使用代理：`mkdir -p ~/.docker`，`touch ~/.docker/config.json`，内容如下：
        ```json
        {
            "proxies": {
                "default": {
                    "httpProxy": "http://198.18.0.1:1080",
                    "httpsProxy": "http://198.18.0.1:1080",
                    "noProxy": "localhost,127.0.0.1"
                }
            }
        }
        ```

## refer

1. docker 网络模式详解，https://www.cnblogs.com/davis12/p/14392125.html