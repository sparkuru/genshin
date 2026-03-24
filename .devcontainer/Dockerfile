FROM debian:trixie

ARG DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y --no-install-recommends \
    ca-certificates curl wget gnupg lsb-release apt-transport-https \
    zsh git vim tree ripgrep fd-find fzf less unzip xz-utils \
    build-essential gcc g++ make pkg-config \
    python3 python3-pip python3-venv python-is-python3 \
    golang-go rustup cargo \
    php php-cli php-fpm \
    openssh-server vsftpd xinetd inetutils-telnetd \
    nginx \
    && rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://deb.nodesource.com/setup_lts.x | bash - \
    && apt-get update \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

RUN update-alternatives --install /usr/bin/fd fd /usr/bin/fdfind 1

RUN mkdir -p /var/run/sshd /var/log/xinetd /var/run/vsftpd/empty

COPY ./mtf/etc/sshd_config /etc/ssh/sshd_config
COPY ./.devcontainer/conf/vsftpd.conf /etc/vsftpd.conf
COPY ./.devcontainer/conf/telnet /etc/xinetd.d/telnet
COPY ./.devcontainer/scripts/start-services.sh /usr/local/share/devcontainer/start-services.sh
COPY ./.devcontainer/scripts/bootstrap-user.sh /usr/local/share/devcontainer/bootstrap-user.sh

RUN chmod +x /usr/local/share/devcontainer/start-services.sh /usr/local/share/devcontainer/bootstrap-user.sh

EXPOSE 21 22 23 80 8080
