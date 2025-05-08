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