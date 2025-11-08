#!/bin/bash

if [ "$(id -u)" -ne 0 ]; then
	echo "\033[0;31mrerun "$0" with sudo\033[0m"
	exit 1
fi

USERNAME="${SUDO_USER:-$USER}"
PROXY_POINT="http://198.18.0.1:1080"
GITHUB_URL_BASE="https://raw.githubusercontent.com/sparkuru/genshin/main"
export all_proxy="$PROXY_POINT"

# init zsh
curl -fLo $HOME/.zshrc $GITHUB_URL_BASE/mtf/.zshrc
curl -fLo /root/.zshrc $GITHUB_URL_BASE/mtf/.zshrc

# ssh
mkdir -p $HOME/.ssh
curl -fLo $HOME/.ssh/authorized_keys $GITHUB_URL_BASE/mtf/authorized_keys
chmod 700 -R $HOME/.ssh

mkdir -p /root/.ssh
curl -fLo /root/.ssh/authorized_keys $GITHUB_URL_BASE/mtf/authorized_keys
chmod 700 -R /root/.ssh

curl -fLo /etc/ssh/sshd_config $GITHUB_URL_BASE/mtf/sshd_config
systemctl start ssh && systemctl enable ssh

# software
cat <<EOF >/etc/apt/sources.list
deb https://mirrors.ustc.edu.cn/kali kali-rolling main non-free non-free-firmware contrib
deb-src https://mirrors.ustc.edu.cn/kali kali-rolling main non-free non-free-firmware contrib
EOF

apt update
apt install -y autoconf autopoint bison cmake gettext gperf help2man intltool libtool ninja-build scons texinfo uglifyjs clangd linux-headers-amd64
apt install -y g++-multilib gcc-multilib gdb-multiarch gdbserver ccache module-assistant
apt install -y libssl-dev libbz2-dev libelf-dev libglib2.0-dev libgmp3-dev libltdl-dev libmpc-dev libmpfr-dev libreadline-dev libc6-dbg libxml2
apt install -y git asciidoc pandoc
apt install -y ack fd-find fzf ripgrep
apt install -y btop iftop inotify-tools aria2 sshpass telnet network-manager-openvpn arch-install-scripts
apt install -y docker-compose virt-manager qemu-system qemu-user bridge-utils
apt install -y fcitx5 fcitx5-chinese-addons fonts-noto-cjk fonts-noto-color-emoji fonts-wqy-microhei
apt install -y filezilla okteta putty picocom glow mtools
apt install -y upx p7zip p7zip-full
apt install -y gnupg2 patchelf
apt install -y python3-ropgadget strace adb
apt install -y osdlyrics winetricks k3b gimp digikam krdc cups
apt install -y genisoimage device-tree-compiler
apt install -y antlr3 antlr4 swig
apt install -y debsums msmtp

python_version=$(python3 --version | awk '{print $2}' | awk -F. '{print "python"$1"."$2}')
if [[ -f "/usr/lib/${python_version}/EXTERNALLY-MANAGED" ]]; then
	mv /usr/lib/${python_version}/EXTERNALLY-MANAGED /usr/lib/${python_version}/EXTERNALLY-MANAGED.backup
fi

# nodejs
require_version="20.0.0"
if [ $(echo -e "$require_version\n$(nodejs -v | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')" | sort -V | head -1) != "$require_version" ]; then
	curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && apt-get install -y nodejs npm &&
		npm install -g npm@latest --registry=https://registry.npmmirror.com &&
		npm install -g --registry=https://registry.npmmirror.com cnpm pm2 @anthropic-ai/claude-code @google/gemini-cli
fi

apt purge needrestart -y
apt autoremove -y

ln -s /usr/bin/fdfind /usr/bin/fd

# fonts
curl -fLo $HOME/.config/fontconfig/fonts.conf $GITHUB_URL_BASE/mtf/fonts.conf
fc-cache -f

# docker
groups="docker,netdev,libvirt,dialout,plugdev"
usermod -aG $groups $USERNAME

mkdir /etc/systemd/system/docker.service.d
cat <<EOF >/etc/systemd/system/docker.service.d/proxy.conf
[Service]
Environment="HTTP_PROXY=http://198.18.0.1:7890"
Environment="HTTPS_PROXY=http://198.18.0.1:7890"
Environment="NO_PROXY=localhost,198.18.0.1"
EOF
mkdir /etc/docker/
cat <<EOF >/etc/docker/daemon.json
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
EOF

# python
cat <<EOF >/etc/pip.conf
[global]
index-url = https://mirrors.ustc.edu.cn/pypi/simple
[install]
trusted-host = https://mirrors.ustc.edu.cn
EOF

sudo -u $USERNAME pip install \
	datetime argparse colorama cryptography getpass4 rich bs4 readchar mmh3 toml \
	ipython \
	ifaddr \
	ropgadget pwntools \
	scapy shodan \
	ollama \
	watchdog psutil

# git
if [ $USERNAME = "wkyuu" ]; then
	git config --global user.email wkyuu@majo.im
	git config --global user.name shiguma
	git config --global credential.helper store
	git config --global init.defaultbranch main
	git config --global core.editor vim
	git config --global core.autocrlf false
	git config --global pull.rebase true

	git config -l
fi

# vim
curl -fLo /tmp/tmp/unix-install-vim.sh $GITHUB_URL_BASE/mtf/unix-install-vim.sh
chmod +x /tmp/tmp/unix-install-vim.sh
/tmp/tmp/unix-install-vim.sh

chown -R $USERNAME:$USERNAME $HOME

# 其他需要安装的软件
# siyuan-note、百度网盘、wps（12.1.0.17881）、wechat、linuxqq、wemeet、vmware-workstation、mihomua
