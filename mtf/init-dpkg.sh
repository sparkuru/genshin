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

curl -fLo /etc/ssh/sshd_config $GITHUB_URL_BASE/mtf/etc/sshd_config
systemctl start ssh && systemctl enable ssh

# software
# cat <<EOF >/etc/apt/sources.list
# deb https://mirrors.ustc.edu.cn/kali kali-rolling main non-free non-free-firmware contrib
# deb-src https://mirrors.ustc.edu.cn/kali kali-rolling main non-free non-free-firmware contrib
# EOF

apt update
apt install -y autoconf autopoint bison cmake gettext gperf help2man intltool libtool ninja-build scons texinfo uglifyjs clangd linux-headers-amd64
apt install -y g++-multilib gcc-multilib gdb-multiarch gdbserver ccache module-assistant
apt install -y libssl-dev libbz2-dev libelf-dev libglib2.0-dev libgmp3-dev libltdl-dev libmpc-dev libmpfr-dev libreadline-dev libc6-dbg libxml2
apt install -y zsh git asciidoc pandoc curl pkexec tree dkms aptitude
apt install -y ack fd-find fzf ripgrep
apt install -y btop iftop inotify-tools aria2 sshpass telnet network-manager-openvpn arch-install-scripts
apt install -y docker-compose virt-manager qemu-system qemu-user bridge-utils
apt install -y fonts-noto-cjk fonts-noto-color-emoji fonts-wqy-microhei
apt install -y fcitx5 fcitx5-table fcitx5-chinese-addons fcitx5-rime fcitx5-anthy fcitx5-frontend-all fcitx5-frontend-gtk* fcitx5-frontend-qt* kde-config-fcitx5
apt install -y filezilla okteta putty picocom glow mtools
apt install -y upx p7zip p7zip-full python3-pip python3-venv python-is-python3
apt install -y gnupg2 patchelf binwalk wireshark	
apt install -y docker.io docker-compose
apt install -y strace adb
apt install -y winetricks k3b gimp digikam krdc cups ffmpeg npm
apt install -y genisoimage device-tree-compiler
apt install -y antlr3 antlr4 swig
apt install -y debsums msmtp xxd
# apt install -y ibus ibus-gtk ibus-rime rime-data-emoji im-config

python_version=$(python3 --version | awk '{print $2}' | awk -F. '{print "python"$1"."$2}')
if [[ -f "/usr/lib/${python_version}/EXTERNALLY-MANAGED" ]]; then
	mv /usr/lib/${python_version}/EXTERNALLY-MANAGED /usr/lib/${python_version}/EXTERNALLY-MANAGED.backup
fi

# nodejs
# require_version="20.0.0"
# if [ $(echo -e "$require_version\n$(nodejs -v | grep -oE '[0-9]+\.[0-9]+\.[0-9]+')" | sort -V | head -1) != "$require_version" ]; then
# 	curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && apt-get install -y nodejs npm &&
# 		npm install -g npm@latest --registry=https://registry.npmmirror.com &&
# 		npm install -g --registry=https://registry.npmmirror.com cnpm pm2 @anthropic-ai/claude-code picgo
# fi

# for pkg in $(dpkg -l | grep fcitx | awk '{print $2}'); do apt purge -y $pkg; done
apt purge -y needrestart
apt autoremove -y

ln -s /usr/bin/fdfind /usr/bin/fd

# fonts
curl -fLo $HOME/.config/fontconfig/fonts.conf $GITHUB_URL_BASE/mtf/fonts.conf
fc-cache -f

# docker
mkdir /etc/systemd/system/docker.service.d
cat <<EOF >/etc/systemd/system/docker.service.d/proxy.conf
[Service]
Environment="HTTP_PROXY=http://198.18.0.1:1080"
Environment="HTTPS_PROXY=http://198.18.0.1:1080"
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
	ropgadget pwntools frida-tools \
	scapy shodan \
	ollama \
	watchdog psutil \
	legacy-cgi

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

# locale, or run `sudo dpkg-reconfigure locales` to config in terminal GUI
echo "en_SG.UTF-8 UTF-8\nen_US.UTF-8 UTF-8\nzh_CN.UTF-8 UTF-8\nzh_SG.UTF-8 UTF-8" >> /etc/locale.gen
# update-locale LANG=zh_CN.UTF-8 LANGUAGE=zh_CN.UTF-8 LC_ALL=zh_CN.UTF-8
locale-gen
locale

groups="adm,sudo,docker,netdev,libvirt,dialout,plugdev,wireshark"
usermod -aG $groups $USERNAME

chown -R $USERNAME:$USERNAME $HOME

# 其他需要安装的软件
# siyuan-note、百度网盘、wps（12.1.0.17881）、wechat、linuxqq、wemeet、vmware-workstation、mihomua

