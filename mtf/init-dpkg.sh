#!/bin/bash

DEFAULT_PROXY_POINT="http://198.18.0.1:1080"
PROXY_POINT="${PROXY_POINT:-$DEFAULT_PROXY_POINT}"

usage() {
	printf 'Usage: %s [--proxy URL]\n' "$0"
	printf 'Default proxy: %s\n' "$DEFAULT_PROXY_POINT"
}

die() {
	printf 'Error: %s\n' "$*" >&2
	exit 1
}

while [[ $# -gt 0 ]]; do
	case "$1" in
	--proxy)
		[[ $# -ge 2 ]] || die "--proxy requires a URL"
		PROXY_POINT="$2"
		shift 2
		;;
	--help | -h)
		usage
		exit 0
		;;
	*)
		die "unknown option: $1"
		;;
	esac
done

# change it if you don't proxy via http proxies like mihomo.
[[ "$PROXY_POINT" =~ ^https?://[^[:space:]\"/]+(:[0-9]+)?/?$ ]] || die "proxy URL must be http://host:port or https://host:port"
PROXY_HOST="${PROXY_POINT#*://}"
PROXY_HOST="${PROXY_HOST%%:*}"
export ALL_PROXY="$PROXY_POINT"
export HTTP_PROXY="$PROXY_POINT"
export HTTPS_PROXY="$PROXY_POINT"
export all_proxy="$PROXY_POINT"
export http_proxy="$PROXY_POINT"
export https_proxy="$PROXY_POINT"

if [ "$(id -u)" -ne 0 ]; then
	echo "\033[0;31m please rerun "$0" with root user permission \033[0m"
	exit 1
fi

GITHUB_URL_BASE="https://raw.githubusercontent.com/sparkuru/genshin/main"
DEFAULT_DNS_SERVER="223.5.5.5"

VALID_USER_LIST=("root")
while read -r line; do
	if [[ -d "/home/$line" ]]; then
		VALID_USER_LIST+=("$line")
	fi
done < <(getent passwd | awk -F: '$3 >= 1000 && $3 < 65534 {print $1}')

_curl() {
	curl -fLo "$1" "$2"
}

_cp() {
	cp -rf "$1" "$2"
}

configure_resolvconf_dns() {
	local config_dir="/etc/resolvconf/resolv.conf.d"
	local head_file="$config_dir/head"
	local tmp_file

	command -v resolvconf >/dev/null 2>&1 || return 0
	mkdir -p "$config_dir"
	tmp_file=$(mktemp)

	if [[ -f "$head_file" ]]; then
		sed '/^# BEGIN default-dns$/,/^# END default-dns$/d' "$head_file" >"$tmp_file"
	fi

	cat >>"$tmp_file" <<EOF
# BEGIN default-dns
nameserver $DEFAULT_DNS_SERVER
options timeout:2 attempts:3
# END default-dns
EOF
	install -m 0644 -o root -g root "$tmp_file" "$head_file"
	rm -f "$tmp_file"
	resolvconf -u
}

# init zsh
tmp_zshrc_path="/tmp/zshrc"
_curl $tmp_zshrc_path $GITHUB_URL_BASE/mtf/.zshrc
for user in "${VALID_USER_LIST[@]}"; do
	if [ $user = "root" ]; then
		target_dir_path="/root/.zshrc"
	else

		target_dir_path=/home/$user/.zshrc
	fi
	_cp $tmp_zshrc_path $target_dir_path
done
rm -f $tmp_zshrc_path

# ssh
tmp_ssh_authorized_keys_path="/tmp/ssh_authorized_keys"
_curl $tmp_ssh_authorized_keys_path $GITHUB_URL_BASE/mtf/authorized_keys
for user in "${VALID_USER_LIST[@]}"; do
	if [ $user = "root" ]; then
		target_dir_path="/root/.ssh"
	else
		target_dir_path="/home/$user/.ssh"
	fi
	mkdir -p $target_dir_path
	_cp $tmp_ssh_authorized_keys_path "${target_dir_path}/authorized_keys"
	chmod 700 -R $target_dir_path
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
	libssl-dev libbz2-dev libelf-dev libglib2.0-dev libgmp3-dev libltdl-dev libmpc-dev libmpfr-dev libreadline-dev libc6-dbg libxml2 libqt6help6 libguestfs-tools libyaml-cpp-dev libeigen3-dev libboost-all-dev libspdlog-dev libfmt-dev
	zsh git git-filter-repo asciidoc pandoc curl pkexec tree dkms aptitude
	ack fd-find fzf ripgrep
	glances iftop inotify-tools aria2 sshpass telnet network-manager-openvpn arch-install-scripts
	docker.io docker-compose virt-manager qemu-system qemu-user bridge-utils
	fonts-noto-cjk fonts-noto-color-emoji fonts-wqy-microhei
	fcitx5 fcitx5-table fcitx5-chinese-addons fcitx5-rime fcitx5-anthy fcitx5-frontend-all fcitx5-frontend-gtk* fcitx5-frontend-qt* kde-config-fcitx5
	filezilla okteta putty picocom glow mtools epub-utils
	upx p7zip p7zip-full
	python3-pip python3-venv python-is-python3
	gnupg2 patchelf binwalk wireshark tcpdump
	strace android-sdk-platform-tools
	winetricks k3b gimp digikam krdc cups ffmpeg npm kdenlive tmux
	genisoimage device-tree-compiler
	antlr3 antlr4 swig
	debsums msmtp xxd ftp shfmt rlwrap pdfgrep
	wireguard resolvconf mariadb-client-compat
	unrar snmp snmp-mibs-downloader sqlmap sqlitebrowser
	enca dos2unix
	kile kile-l10n
	obs-studio simplescreenrecorder
	davfs2
	webp libxdo-dev webkitgtk-webdriver
	rclone shellcheck
	v4l-utils v4l2loopback-dkms v4l2loopback-utils
	rsync nginx net-tools dnsutils whois
	freecad
)

apt update
apt install -y "${to_install_list[@]}"
configure_resolvconf_dns
# apt install -y ibus ibus-gtk ibus-rime rime-data-emoji im-config

python_version=$(python3 --version | awk '{print $2}' | awk -F. '{print "python"$1"."$2}')
if [[ -f "/usr/lib/${python_version}/EXTERNALLY-MANAGED" ]]; then
	mv /usr/lib/${python_version}/EXTERNALLY-MANAGED /usr/lib/${python_version}/EXTERNALLY-MANAGED.backup
fi
# python_version=$(python3 --version | awk '{print $2}' | awk -F. '{print "python"$1"."$2}'); sudo mv /usr/lib/${python_version}/EXTERNALLY-MANAGED /usr/lib/${python_version}/EXTERNALLY-MANAGED.backup

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
apt autoclean -y

update-alternatives --install /usr/bin/fd fd /usr/bin/fdfind 1

# fonts
tmp_fonts_conf_path="/tmp/fonts.conf"
_curl $tmp_fonts_conf_path $GITHUB_URL_BASE/mtf/etc/fonts.conf
for user in "${VALID_USER_LIST[@]}"; do
	mkdir -p /home/$user/.config/fontconfig
	_cp $tmp_fonts_conf_path /home/$user/.config/fontconfig/fonts.conf
done
fc-cache -f
rm -f $tmp_fonts_conf_path

# rime
tmp_oh_my_rime_path="/tmp/oh_my_rime"
rm -rf "$tmp_oh_my_rime_path"
git clone https://github.com/Mintimate/oh-my-rime.git $tmp_oh_my_rime_path
for user in "${VALID_USER_LIST[@]}"; do
	if [ $user = "root" ]; then
		user_rime_path="/root/.config/fcitx5/rime"
	else
		user_rime_path="/home/$user/.config/fcitx5/rime"
	fi
	sudo -u $user mkdir -p $user_rime_path
	sudo -u "$user" cp -a "$tmp_oh_my_rime_path/." "$user_rime_path/"
done
rm -rf "$tmp_oh_my_rime_path"

# docker
mkdir -p /etc/systemd/system/docker.service.d
cat <<EOF >/etc/systemd/system/docker.service.d/proxy.conf
[Service]
Environment="HTTP_PROXY=$PROXY_POINT"
Environment="HTTPS_PROXY=$PROXY_POINT"
Environment="NO_PROXY=localhost,127.0.0.1,::1,$PROXY_HOST"
EOF
mkdir -p /etc/docker/
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
break-system-packages = true
user = true
[install]
trusted-host = https://mirrors.ustc.edu.cn
EOF

pip_to_install_list=(
	datetime argparse colorama cryptography getpass4 rich bs4 readchar mmh3 toml
	ipython
	ifaddr
	ropgadget pwntools frida-tools
	scapy shodan
	ollama
	watchdog psutil
	legacy-cgi
	pyinstaller staticx
	faker python-docx openpyxl
	pillow markdown pygments playwright
)

for user in "${VALID_USER_LIST[@]}"; do
	sudo -u "$user" pip install "${pip_to_install_list[@]}"
done

# git
for user in "${VALID_USER_LIST[@]}"; do
	if [ $user = "wkyuu" ]; then
		sudo -u $user git config --global user.email i@majo.im
		sudo -u $user git config --global user.name wkyuu
		sudo -u $user git config --global credential.helper store
		sudo -u $user git config --global init.defaultbranch main
		sudo -u $user git config --global core.editor vim
		sudo -u $user git config --global core.autocrlf false
		sudo -u $user git config --global core.quotepath false
		sudo -u $user git config --global pull.rebase true

		sudo -u "$user" env all_proxy="$all_proxy" curl -fLo "/home/$user/.gitignore_global" "$GITHUB_URL_BASE/mtf/.gitignore_global"
		sudo -u $user git config --global core.excludesfile "/home/$user/.gitignore_global"

		sudo -u $user git config --global --list
		ln -sfn "/home/$user/.gitconfig" "/root/.gitconfig"
	fi
done

# vim
mkdir -p /tmp/tmp
_curl /tmp/tmp/unix-install-vim.sh $GITHUB_URL_BASE/mtf/unix-install-vim.sh
chmod +x /tmp/tmp/unix-install-vim.sh
for user in "${VALID_USER_LIST[@]}"; do
	sudo -u "$user" env \
		all_proxy="$all_proxy" \
		http_proxy="$http_proxy" \
		https_proxy="$https_proxy" \
		/tmp/tmp/unix-install-vim.sh install --force
done

# locale, or run `sudo dpkg-reconfigure locales` to config in terminal GUI
sed -i '/\\n/d' /etc/locale.gen
locale_entries=(
	"en_SG.UTF-8 UTF-8"
	"en_US.UTF-8 UTF-8"
	"zh_CN.UTF-8 UTF-8"
	"zh_SG.UTF-8 UTF-8"
)
for locale_entry in "${locale_entries[@]}"; do
	if grep -Eq "^[#[:space:]]*${locale_entry}[[:space:]]*$" /etc/locale.gen; then
		sed -i -E "s|^[#[:space:]]*(${locale_entry})[[:space:]]*$|\\1|" /etc/locale.gen
	elif ! grep -qxF "$locale_entry" /etc/locale.gen; then
		printf '%s\n' "$locale_entry" >>/etc/locale.gen
	fi
done
# update-locale LANG=zh_CN.UTF-8 LANGUAGE=zh_CN.UTF-8 LC_ALL=zh_CN.UTF-8
locale-gen
locale

# timezone
timedatectl set-timezone Asia/Singapore

groups="adm,sudo,docker,netdev,libvirt,dialout,plugdev,wireshark"
for user in "${VALID_USER_LIST[@]}"; do
	usermod -aG $groups $user
done

for user in "${VALID_USER_LIST[@]}"; do
	chown -R $user:$user /home/$user
done

# 其他需要安装的软件
# siyuan-note、百度网盘、wps（12.1.0.17881）、wechat、linuxqq、wemeet、vmware-workstation、virtualbox、mihomua
