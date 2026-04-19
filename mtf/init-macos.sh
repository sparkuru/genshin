
_curl() {
	curl -fLo $1 $2
}

PROXY_POINT="http://198.18.0.1:1080"
GITHUB_URL_BASE="https://raw.githubusercontent.com/sparkuru/genshin/main"
export all_proxy="$PROXY_POINT"

# git
git config --global user.email wkyuu@majo.im
git config --global user.name sparkuru
git config --global credential.helper store
git config --global init.defaultbranch main
git config --global core.editor vim
git config --global core.autocrlf false
git config --global core.quotepath false
git config --global pull.rebase true

_curl "$HOME/.gitignore_global" $GITHUB_URL_BASE/mtf/.gitignore_global
git config --global core.excludesfile "$HOME/.gitignore_global"
git config --global --list


# python
mkdir $HOME/.config/pip/pip.conf

cat <<EOF >$HOME/.config/pip/pip.conf
[global]
index-url = https://mirrors.ustc.edu.cn/pypi/simple
break-system-packages = true
user = true
[install]
trusted-host = https://mirrors.ustc.edu.cn
EOF

brew install curl net-tools openvpn rsync proxychains-ng jq tcp-traceroute iproute2mac \
	gnupg2 binutils file fd-find btop tmux strace coreutils \
	scons squashfs subversion swig texinfo upx unzip 7z-zip git \
	python \
    qemu \
	fzf ripgrep vim \
	docker docker-compose colima \
	ghidra rizin radare2 patchelf \
	nmap hydra john telnet \
	scroll-reverser \
	nmap hydra john telnet fd scroll-reverser android-platform-tools tree glow btop pidof \
	toml

pip install setuptools setuptools_rust datetime argparse ipython getpass4 colorama cryptography ifaddr \
  virtualenv ropgadget pwntools shodan \
  ollama readchar rich watchdog psutil faker python-docx

# vim
_curl /tmp/tmp/unix-install-vim.sh $GITHUB_URL_BASE/mtf/unix-install-vim.sh
chmod +x /tmp/tmp/unix-install-vim.sh
/tmp/tmp/unix-install-vim.sh install

# 到 System Settings → General → Sharing → Remote Login 启用 ssh 登录

# homebrew 意为家酿啤酒（homebrew 安装，会自己制作、编译软件），cask 意为桶装酒（直接下载 .app 文件，即成品下载）；
