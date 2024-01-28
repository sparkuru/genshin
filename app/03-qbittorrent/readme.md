# qbittorrent

## qBittorrent

源 repo：https://github.com/qbittorrent/qBittorrent.git

1. `sudo docker-compose -p 03-qbittorrent -f /home/server/03-qbittorrent/qbittorrent.yml up -d` 启动后，在 log 里看 webui 默认账密 `admin / xxxxxxx`
2. 登陆成功后
   1. 设置改中文
   2. `设置 / Web UI / 验证`，修改用户名和密码
   3. `设置 / 下载 / 默认保存路径` 为 `/downloads` 不要修改
3. 限制恶意刷 pt，[参考](https://www.bilibili.com/read/cv36727219/?from=articleDetail&spm_id_from=333.976.0.0)

## qBittorrent-Enhanced-Edition（推荐）

增强版 repo（反吸血）：https://github.com/c0re100/qBittorrent-Enhanced-Edition.git

1. 自己编译一个 docker 镜像

   1. `mkdir -p /home/server/03-qbittorrent/qbee-repo`

   2. `git clone https://github.com/linuxserver/docker-qbittorrent.git /home/server/03-qbittorrent/docker-repo`

   3. `touch /home/server/03-qbittorrent/Dockerfile`，写入以下内容

      ```dockerfile
      FROM ghcr.io/linuxserver/unrar:latest AS unrar
      FROM ghcr.io/linuxserver/baseimage-alpine:edge
      
      # set version label
      ARG BUILD_DATE
      ARG VERSION
      ARG QBT_CLI_VERSION
      ARG REPO_OWNER="c0re100"
      ARG REPO_NAME="qBittorrent-Enhanced-Edition"
      LABEL build_version="Linuxserver.io version:- ${VERSION} Build-date:- ${BUILD_DATE}"
      LABEL maintainer="thespad"
      LABEL notice="modified from linuxserver/qbittorrent"
      LABEL git_repo="https://github.com/c0re100/qBittorrent-Enhanced-Edition.git"
      LABEL description="qBittorrent Enhanced is based on qBittorrent, it's aimed at blocking leeching clients automatically."
      LABEL warning="Please do not use this modified BitTorrent client on Private Trackers. unless qBittorrent Enhanced Edition is allowed on the Private Tracker(Depend on which PT you're using.)."
      
      # environment settings
      ENV HOME="/config" \
      XDG_CONFIG_HOME="/config" \
      XDG_DATA_HOME="/config"
      
      # install runtime packages and qbitorrent-cli
      RUN apk add --no-cache icu-libs p7zip python3 qt6-qtbase-sqlite
      
      RUN LATEST_TAG=$(curl -s "https://api.github.com/repos/$REPO_OWNER/$REPO_NAME/releases/latest" | awk -F '"' '/"tag_name":/ {print $4}')
      RUN DOWNLOAD_URL="https://github.com/$REPO_OWNER/$REPO_NAME/releases/download/$LATEST_TAG/qbittorrent-enhanced-nox_x86_64-linux-musl_static.zip"
      RUN curl -o /tmp/qbittorrent-enhanced-nox.zip -sL $DOWNLOAD_URL
      RUN 7z x /tmp/qbittorrent-enhanced-nox.zip -o /usr/bin
      
      RUN mkdir /qbt
      RUN if [ -z ${QBT_CLI_VERSION+x} ]; then \
              QBT_CLI_VERSION=$(curl -sL "https://api.github.com/repos/fedarovich/qbittorrent-cli/releases/latest" \
              jq -r '. | .tag_name'); \
          fi
      RUN curl -o /tmp/qbt.tar.gz -L \
          "https://github.com/fedarovich/qbittorrent-cli/releases/download/${QBT_CLI_VERSION}/qbt-linux-alpine-x64-net6-${QBT_CLI_VERSION#v}.tar.gz"
      RUN tar xf /tmp/qbt.tar.gz -C /qbt
      RUN rm -rf /root/.cache /tmp/*
      
      # add local files
      COPY root/ /
      COPY --from=unrar /usr/bin/unrar-alpine /usr/bin/unrar
      EXPOSE 8080 6881 6881/udp
      
      VOLUME /config
      ```
      
      以上 dockerfile 是参考 [linuxserver/docker-qbittorrent/Dockerfile](https://github.com/linuxserver/docker-qbittorrent/blob/master/Dockerfile) 写出来的，尽可能让在编写 qbee.yml 时更接近原版的 qbittorrent.yml
