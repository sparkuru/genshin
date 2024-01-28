#/usr/bin/env zsh

if [ "$(id -u)" -ne 0 ]; then
	echo "\033[0;31mrerun "$0" with sudo\033[0m"
	exit 1
fi

PROXY_POINT="http://198.18.0.1:1080"
GITHUB_URL_BASE="https://raw.githubusercontent.com/shi9uma/genshin/main"
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
cat << EOF > /etc/apt/sources.list
deb https://mirrors.ustc.edu.cn/kali kali-rolling main non-free non-free-firmware contrib
deb-src https://mirrors.ustc.edu.cn/kali kali-rolling main non-free non-free-firmware contrib
EOF

apt update
# apt remove -y libpython3.11-minimal libpython3.11-stdlib python3.11 python3.11-minimal
apt install -y \
    ack usbtils antlr3 aria2 asciidoc autoconf automake autopoint \
	binutils bison build-essential bzip2 \
	ccache cmake cpio curl \
	device-tree-compiler \
	fastjar flex \
	gawk gettext gcc-multilib g++-multilib gdb-multiarch gperf \
	haveged help2man \
	gnupg2 intltool \
	libc6-dev-i386 libelf-dev libglib2.0-dev libgmp3-dev libltdl-dev libmpc-dev libncurses-dev libpython3-dev \
	libmpfr-dev libc6-dbg libncurses5-dev libncursesw5-dev libreadline-dev libssl-dev libffi-dev libtool lrzsz \
    make module-assistant mkisofs msmtp \
	ninja-build \
	p7zip p7zip-full \
	patch pkgconf python2.7 python3-pip \
    software-properties-common zlib1g-dev

if [[ -f "/usr/lib/python3.12/EXTERNALLY-MANAGED" ]]; then
	mv /usr/lib/python3.12/EXTERNALLY-MANAGED /usr/lib/python3.12/EXTERNALLY-MANAGED.backup
fi

apt install -y \
	aptitude \
	locales iproute2 net-tools iftop curl openvpn rsync proxychains4 jq traceroute \
	file fd-find xxd btop tmux strace last coreutils \
	scons squashfs-tools subversion swig texinfo uglifyjs upx-ucl unzip git ntfs-3g \
	qemu-user-static qemu-system qemu-utils bridge-utils \
	python3-pip python3-venv python3-shodan python3-ropgadget \
	fzf ripgrep vim \
	docker.io docker-compose \
	gdb gdbserver ghidra rizin radare2 patchelf \
	nmap hydra john telnet \
	rkhunter chkrootkit debsums

curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && apt-get install -y nodejs npm && \
npm install -g npm@latest --registry=https://registry.npmmirror.com && \
npm install cnpm -g --registry=https://registry.npmmirror.com && \
cnpm install -g pm2

apt purge needrestart -y
apt autoremove -y

ln -s /usr/bin/fdfind /usr/bin/fd
ln -s /usr/bin/python3 /usr/bin/python

# docker
usermod -aG docker wkyuu
mkdir /etc/systemd/system/docker.service.d
cat << EOF > /etc/systemd/system/docker.service.d/proxy.conf
[Service]
Environment="HTTP_PROXY=http://127.0.0.1:7890"
Environment="HTTPS_PROXY=http://127.0.0.1:7890"
Environment="NO_PROXY=localhost,127.0.0.1"
EOF

# python
cat << EOF > /etc/pip.conf
[global]
index-url = https://mirrors.ustc.edu.cn/pypi/simple
[install]
trusted-host = https://mirrors.ustc.edu.cn
EOF

sudo -u wkyuu pip install \
	datetime argparse colorama cryptography getpass4 rich readchar \
	ipython \
	netifaces wsgidav \
	ropgadget pwntools \
	scapy shodan \
	ollama

# git
git config --global user.email wkyuu@majo.im
git config --global user.name shiguma
git config --global credential.helper store
git config --global init.defaultbranch main
git config --global core.editor vim
git config --global core.autocrlf false
git config --global pull.rebase true

git config -l

# vim
curl -fLo /tmp/tmp/unix-install-vim.sh https://raw.githubusercontent.com/shi9uma/vim/main/diy/unix-install-vim.sh
chmod +x /tmp/tmp/unix-install-vim.sh
/tmp/tmp/unix-install-vim.sh

# dir
USER="wkyuu"

HOME_DIR_PATH="/home"
APP_DIR_PATH="$HOME_DIR_PATH/app"
# GAME_DIR_PATH="$HOME_DIR_PATH/game"
REPO_DIR_PATH="$HOME_DIR_PATH/repo"
SERVER_DIR_PATH="$HOME_DIR_PATH/server"

mkdir -p $APP_DIR_PATH $GAME_DIR_PATH $REPO_DIR_PATH $SERVER_DIR_PATH

## app
mkdir -p \
	$APP_DIR_PATH/carbonyl \
	$APP_DIR_PATH/frp \
	$APP_DIR_PATH/java

# pwn
PWN_DIR_PATH="$APP_DIR_PATH/pwn"
PWNDBG_DIR_PATH="$PWN_DIR_PATH/pwndbg"
PWNDBG_REPO_DIR_PATH="$PWNDBG_REPO_DIR_PATH/repo"

mkdir -p $PWN_DIR_PATH $PWNDBG_DIR_PATH $PWNDBG_REPO_DIR_PATH

git clone https://github.com/pwndbg/pwndbg.git $PWNDBG_REPO_DIR_PATH
cd $PWNDBG_REPO_DIR_PATH && chmod +x ./setup.sh && all_proxy="$PROXY_POINT" ./setup.sh

chown -R $USER:$USER $HOME_DIR_PATH