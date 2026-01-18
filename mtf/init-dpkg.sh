#!/bin/bash

if [ "$(id -u)" -ne 0 ]; then
	echo "\033[0;31m please rerun "$0" with root user permission \033[0m"
	exit 1
fi

PROXY_POINT="http://198.18.0.1:1080"
GITHUB_URL_BASE="https://raw.githubusercontent.com/sparkuru/genshin/main"
export all_proxy="$PROXY_POINT"

VALID_USER_LIST=("root")
while read -r line; do
	if [[ -d "/home/$line" ]]; then
		VALID_USER_LIST+=("$line")
	fi
done < <(getent passwd | awk -F: '$3 >= 1000 && $3 < 65534 {print $1}')

_curl() {
	curl -fLo $1 $2
}

_cp() {
	cp -f $1 $2
}

# init zsh
tmp_zshrc_path="/tmp/zshrc"
_curl $tmp_zshrc_path $GITHUB_URL_BASE/mtf/.zshrc
for user in "${VALID_USER_LIST[@]}"; do
	mkdir -p /home/$user/.zsh
	_cp $tmp_zshrc_path /home/$user/.zshrc
done
rm -f $tmp_zshrc_path

# ssh
tmp_ssh_authorized_keys_path="/tmp/ssh_authorized_keys"
_curl $tmp_ssh_authorized_keys_path $GITHUB_URL_BASE/mtf/authorized_keys
for user in "${VALID_USER_LIST[@]}"; do
	mkdir -p /home/$user/.ssh
	_cp $tmp_ssh_authorized_keys_path /home/$user/.ssh/authorized_keys
	chmod 700 -R /home/$user/.ssh
done
rm -f $tmp_ssh_authorized_keys_path

_curl /etc/ssh/sshd_config $GITHUB_URL_BASE/mtf/etc/sshd_config
systemctl start ssh && systemctl enable ssh

# software
# cat <<EOF >/etc/apt/sources.list
# deb https://mirrors.ustc.edu.cn/kali kali-rolling main non-free non-free-firmware contrib
# deb-src https://mirrors.ustc.edu.cn/kali kali-rolling main non-free non-free-firmware contrib
# EOF

to_install_list=(
  autoconf autopoint bison cmake gettext gperf help2man intltool libtool ninja-build scons texinfo uglifyjs clangd linux-headers-amd64
  g++-multilib gcc-multilib gdb-multiarch gdbserver ccache module-assistant
  libssl-dev libbz2-dev libelf-dev libglib2.0-dev libgmp3-dev libltdl-dev libmpc-dev libmpfr-dev libreadline-dev libc6-dbg libxml2 libguestfs-tools
  zsh git asciidoc pandoc curl pkexec tree dkms aptitude
  ack fd-find fzf ripgrep
  glances iftop inotify-tools aria2 sshpass telnet network-manager-openvpn arch-install-scripts
  docker-compose virt-manager qemu-system qemu-user bridge-utils
  fonts-noto-cjk fonts-noto-color-emoji fonts-wqy-microhei
  fcitx5 fcitx5-table fcitx5-chinese-addons fcitx5-rime fcitx5-anthy fcitx5-frontend-all fcitx5-frontend-gtk* fcitx5-frontend-qt* kde-config-fcitx5
  filezilla okteta putty picocom glow mtools epub-utils
  upx p7zip p7zip-full python3-pip python3-venv python-is-python3
  gnupg2 patchelf binwalk wireshark tcpdump
  docker.io docker-compose
  strace android-sdk-platform-tools
  winetricks k3b gimp digikam krdc cups ffmpeg npm
  genisoimage device-tree-compiler
  antlr3 antlr4 swig
  debsums msmtp xxd ftp shfmt rlwrap pdfgrep
  wireguard resolvconf mariadb-client-compat
  unrar
)

apt update
apt install -y ${to_install_list[@]}
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

update-alternatives --install /usr/bin/fd fd /usr/bin/fdfind 1

# fonts
tmp_fonts_conf_path="/tmp/fonts.conf"
_curl $tmp_fonts_conf_path $GITHUB_URL_BASE/mtf/fonts.conf
for user in "${VALID_USER_LIST[@]}"; do
	mkdir -p /home/$user/.config/fontconfig
	_cp $tmp_fonts_conf_path /home/$user/.config/fontconfig/fonts.conf
done
fc-cache -f
rm -f $tmp_fonts_conf_path

# rime
tmp_oh_my_rime_path="/tmp/oh_my_rime"
git clone https://github.com/Mintimate/oh-my-rime.git $tmp_oh_my_rime_path
for user in "${VALID_USER_LIST[@]}"; do
	if [ $user = "root" ]; then
		user_rime_path="/root/.config/fcitx5/rime"
	else
		user_rime_path="/home/$user/.config/fcitx5/rime"
	fi
	sudo -u $user mkdir -p $user_rime_path
	sudo -u $user cp -f $tmp_oh_my_rime_path $user_rime_path
done
rm -f $tmp_oh_my_rime_path

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

for user in "${VALID_USER_LIST[@]}"; do
	sudo -u $user pip install \
		datetime argparse colorama cryptography getpass4 rich bs4 readchar mmh3 toml \
		ipython \
		ifaddr \
		ropgadget pwntools frida-tools \
		scapy shodan \
		ollama \
		watchdog psutil \
		legacy-cgi \
		pyinstaller staticx
done

# git
for user in "${VALID_USER_LIST[@]}"; do
	if [ $user = "wkyuu" ]; then
		sudo -u $user git config --global user.email wkyuu@majo.im
		sudo -u $user git config --global user.name sparkuru
		sudo -u $user git config --global credential.helper store
		sudo -u $user git config --global init.defaultbranch main
		sudo -u $user git config --global core.editor vim
		sudo -u $user git config --global core.autocrlf false
		sudo -u $user git config --global pull.rebase true

		sudo -u $user _curl "/home/$user/.gitignore_global" $GITHUB_URL_BASE/mtf/.gitignore_global
		sudo -u $user git config --global include.path "/home/$user/.gitignore_global"

		sudo -u $user git config --global --list
		ln -s "/home/$user/.gitconfig" "/root/.gitconfig"
	fi
done

# vim
curl -fLo /tmp/tmp/unix-install-vim.sh $GITHUB_URL_BASE/mtf/unix-install-vim.sh
chmod +x /tmp/tmp/unix-install-vim.sh
for user in "${VALID_USER_LIST[@]}"; do
	sudo -u $user /tmp/tmp/unix-install-vim.sh
done

# locale, or run `sudo dpkg-reconfigure locales` to config in terminal GUI
echo "en_SG.UTF-8 UTF-8\nen_US.UTF-8 UTF-8\nzh_CN.UTF-8 UTF-8\nzh_SG.UTF-8 UTF-8" >>/etc/locale.gen
# update-locale LANG=zh_CN.UTF-8 LANGUAGE=zh_CN.UTF-8 LC_ALL=zh_CN.UTF-8
locale-gen
locale

groups="adm,sudo,docker,netdev,libvirt,dialout,plugdev,wireshark"
for user in "${VALID_USER_LIST[@]}"; do
	usermod -aG $groups $user
done

for user in "${VALID_USER_LIST[@]}"; do
	chown -R $user:$user /home/$user
done

# 其他需要安装的软件
# siyuan-note、百度网盘、wps（12.1.0.17881）、wechat、linuxqq、wemeet、vmware-workstation、mihomua
