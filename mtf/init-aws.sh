#!/bin/bash

# It’s been hard to tolerate the policies and service quality of Chinese cloud providers ever since I started using AWS.

if [ "$(id -u)" -ne 0 ]; then
	echo "\033[0;31m please rerun "$0" with root user permission \033[0m"
	exit 1
fi

GITHUB_URL_BASE="https://raw.githubusercontent.com/sparkuru/genshin/main"
VALID_USER_LIST=(
	"root"
	"wkyuu"
)

_curl() {
	curl -fLo $1 $2
}

_cp() {
	cp -rf $1 $2
}

fix_resolvconf_dns() {
	local dns_server="172.26.0.2"
	local conf_dir="/etc/resolvconf/resolv.conf.d"
	local head_file="$conf_dir/head"
	local backup_file="$conf_dir/head.backup.$(date +%Y%m%d-%H%M%S)"
	local tmp_file="/tmp/resolvconf-head.$$"

	if ! command -v resolvconf >/dev/null 2>&1; then
		return 0
	fi

	mkdir -p "$conf_dir"
	if [ -e "$head_file" ]; then
		cp -a "$head_file" "$backup_file"
	else
		: >"$backup_file"
	fi

	if [ -e "$head_file" ]; then
		sed '/^# BEGIN mtf-aws-dns-fix$/,/^# END mtf-aws-dns-fix$/d' "$head_file" >"$tmp_file"
	else
		: >"$tmp_file"
	fi

	cat >>"$tmp_file" <<EOF
# BEGIN mtf-aws-dns-fix
nameserver $dns_server
options timeout:2 attempts:3
# END mtf-aws-dns-fix
EOF
	install -m 0644 -o root -g root "$tmp_file" "$head_file"
	rm -f "$tmp_file"
	resolvconf -u
}

fix_resolvconf_dns

# init zsh
tmp_zshrc_path="/tmp/zshrc"
_curl $tmp_zshrc_path $GITHUB_URL_BASE/mtf/.zshrc
for user in "${VALID_USER_LIST[@]}"; do
	if [ $user = "root" ]; then
		_cp $tmp_zshrc_path /root/.zshrc
	else
		_cp $tmp_zshrc_path /home/$user/.zshrc
	fi
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

to_install_list=(
	autoconf autopoint bison cmake gettext gperf help2man intltool libtool ninja-build scons texinfo uglifyjs clangd linux-headers-amd64
	g++-multilib gcc-multilib gdb-multiarch gdbserver ccache module-assistant
	libssl-dev libbz2-dev libelf-dev libglib2.0-dev libgmp3-dev libltdl-dev libmpc-dev libmpfr-dev libreadline-dev libc6-dbg libxml2 libqt6help6 libguestfs-tools libyaml-cpp-dev libeigen3-dev libboost-all-dev libspdlog-dev libfmt-dev
	zsh git git-filter-repo asciidoc pandoc curl pkexec tree dkms aptitude
	ack fd-find fzf ripgrep
	glances iftop inotify-tools aria2 sshpass telnet network-manager-openvpn arch-install-scripts
	docker.io docker-compose virt-manager qemu-system qemu-user bridge-utils
	filezilla okteta putty picocom glow mtools epub-utils
	upx p7zip p7zip-full
	python3-pip python3-venv python-is-python3
	gnupg2 patchelf binwalk wireshark tcpdump
	strace
	ffmpeg npm tmux
	genisoimage device-tree-compiler
	antlr3 antlr4 swig
	debsums msmtp xxd ftp shfmt rlwrap pdfgrep
	wireguard resolvconf mariadb-client-compat
	sqlmap
	enca dos2unix
	davfs2
	webp libxdo-dev webkitgtk-webdriver
	rclone shellcheck
	v4l-utils v4l2loopback-dkms v4l2loopback-utils
	rsync nginx php-fpm php-mysql php-curl php-mbstring net-tools
)

apt update
apt install -y ${to_install_list[@]}
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

# docker
mkdir -p /etc/systemd/system/docker.service.d
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
)

for user in "${VALID_USER_LIST[@]}"; do
	sudo -u $user pip install ${pip_to_install_list[@]}
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

		sudo -u $user _curl "/home/$user/.gitignore_global" $GITHUB_URL_BASE/mtf/.gitignore_global
		sudo -u $user git config --global core.excludesfile "/home/$user/.gitignore_global"

		sudo -u $user git config --global --list
		ln -sfn "/home/$user/.gitconfig" "/root/.gitconfig"
	fi
done

# vim
_curl /tmp/tmp/unix-install-vim.sh $GITHUB_URL_BASE/mtf/unix-install-vim.sh
chmod +x /tmp/tmp/unix-install-vim.sh
for user in "${VALID_USER_LIST[@]}"; do
	sudo -u $user /tmp/tmp/unix-install-vim.sh install --force
done

# locale, or run `sudo dpkg-reconfigure locales` to config in terminal GUI
echo "en_SG.UTF-8 UTF-8\nen_US.UTF-8 UTF-8\nzh_CN.UTF-8 UTF-8\nzh_SG.UTF-8 UTF-8" >>/etc/locale.gen
# update-locale LANG=zh_CN.UTF-8 LANGUAGE=zh_CN.UTF-8 LC_ALL=zh_CN.UTF-8
locale-gen
locale

# timezone
timedatectl set-timezone Asia/Singapore

groups="adm,sudo,docker,netdev,dialout,plugdev,cdrom,floppy,tcpdump"
for user in "${VALID_USER_LIST[@]}"; do
	usermod -aG $groups $user
done

for user in "${VALID_USER_LIST[@]}"; do
	chown -R $user:$user /home/$user
done
