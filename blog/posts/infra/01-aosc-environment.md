---
title: "init-my-aosc"
description: "nix 是真的能作为主力机系统来使用的。"
date: "2025-04-02T01:20:00.000Z"
updated: "2025-12-02T02:11:44.000Z"
tags: []
draft: false
layout: "post"
slug: "aosc-environment"
---

由于鸡哥的 windows 10/11 总是有各种问题（我们小组的几台鸡哥全寄了），~~这边选择装一个双系统~~，~~日常除了 office 三件套以外的工作~~，现在 linux in wps 全部解决了（由于市场还是太小了，没有广告、操作和 office 没什么差别，对我们这种写写简单报告的够用了，唯一良心），都将主要使用 linux

在众多发行版中，相中了国内社区主导的 [aosc](https://aosc.io/) 安同系统，一是安装比较简单，二是更新比较勤快 **（2025年06月05日记：oma 上游更新了个用不了的 zsh5.9-1，导致我一天没法正常干活，通过重装并改用 bash 解决；第二天 oma 紧急更新了 zsh5.9-2，目前是可用了；但是经此一事，这边又把系统换成 debian 13 了，至少推送这些不稳定的东西时，很快就会有人提出来然后整改）** ，三是现在常用的 wechat、qq 之类的已经对 unix 支持比较完善了，可以无痛迁移

进一步配置请参考 [init-my-unix](https://www.majo.im/index.php/wkyuu/356.html)

## 系统安装及设置

1. kde 主题
2. 设置配置

    1. 进系统再修改字体时区，防止 `~/download` 这种
    2. 修改 ~ 下的 Downloads -> download
    3. 拼音，pinyin
    4. 个性化

        1. KDE 密码库，kwallet
3. 开机启动小键盘：修改 `/etc/sddm.conf` 的 `Numlock = on`
4. 添加应用快捷方式：`/usr/share/applications`
5. 安装 vmware workstation：

    1. `wget -O vmware-workstation.bundle https://download3.vmware.com/software/WKST-1750-LX/VMware-Workstation-Full-17.5.0-22583795.x86_64.bundle`
    2. `chmod +x vmware-workstation.bundle`
    3. `./vmware-workstation.bundle`
    4. 如果报错 `[AppLoader] Fail to load the library. /usr/lib/libxcb-shm.so.0: undefined symbol: xcb_send_request_with_fds`，则

        ```bash
        $ file /usr/lib/libxcb-shm.so.0
        /usr/lib/libxcb-shm.so.0: symbolic link to libxcb-shm.so.0.0.0

        $ ll /usr/lib/libxcb-shm.so.0.0.0
        -rwxr-xr-x 1 root root 14K 12月16日 15:02 /usr/lib/libxcb-shm.so.0.0.0

        $ sudo mv /usr/lib/vmware/lib/libxcb.so.1/libxcb.so.1 /usr/lib/vmware/lib/libxcb.so.1/libxcb.so.1.backup

        $ sudo ln -s /usr/lib/libxcb-shm.so.0.0.0 /usr/lib/vmware/lib/libxcb.so.1/libxcb.so.1
        ```
    5. 手动安装网络模块：`sudo vmware-modconfig --console --install-all`
    6.

## bash

1. 安装时 locale 选择 us, 进去后再改成 cn
2. 修改字体

    ```bash
    # cjk 表示中日韩、mono 表示等宽、nerd 表示字体里额外带了很多图标
    oma install -y  noto-fonts noto-cjk-fonts wqy-microhei

    sudo echo "LANG=zh_CN.UTF-8" > /etc/locale.conf

    sudo mkdir -p /usr/share/fonts/{windows}
    # 1. 将 windows 下的 Fonts 文件夹内的所有内容，复制到这个 windows 下
    # 2. 获取一些字体 https://www.nerdfonts.com/font-downloads，同样放到上面的目录下
    sudo chmod -R +rx /usr/share/fonts && sudo chown -R root:root /usr/share/fonts

    # 修改以下文件（跟着用户走）
    wget -O ~/.config/fontconfig/fonts.conf \
    	https://raw.githubusercontent.com/shi9uma/genshin/refs/heads/main/mtf/fonts.conf

    # 查看系统中有什么可用字体
    fc-list

    fc-cache -fv
    ```
3. pinyin, zsh, wayland, kwallet
4. 基础组件安装

    ```bash
    oma install -y  ack antlr4 aria2 asciidoc autoconf
    oma install -y  automake binutils bison build-essential devel-base debug-base
    oma install -y  ccache cmake cpio dtc
    oma install -y  flex gettext gperf haveged help2man glibc libglibutil
    oma install -y  net-tools curl openvpn rsync jq fd btop tcpdump
    oma install -y  tmux scons upx git qemu nbd
    oma install -y  fzf ripgrep vim
    oma install -y  docker docker-compose
    oma install -y  lrzsz android-platform-tools ntfs-3g
    oma install -y  nodejs-22 picocom
    oma install -y  wine winetricks
    oma install -y  virt-manager 
    oma install -y  openjdk-8 openjdk-11 openjdk-17 openjdk-23 openjdk+latest
    oma install -y  git pandoc osdlyrics sshpass
    ```
5. 常用软件安装

    ```bash
    oma install -y  kwallet kwallet-pam kwalletmanager zsh mihomo-party
    oma install -y  google-chrome vscode telegram-desktop filezilla yesplaymusic

    npm install -g npm@latest --registry=https://registry.npmmirror.com
    npm install cnpm -g --registry=https://registry.npmmirror.com
    cnpm install -g pm2
    ln -s /usr/lib/node-22 /usr/lib/nodejs

    # 额外装：
    ghidra rizin radare2 hydra(vanhauser-thc/thc-hydra) john(openwall/john) ida linuxqq wechat
    siyuan typora cursor dingtalk 百度网盘 xmind
    vmware-workstation
    wps
    ```
6. sec

    ```bash
    oma install -y  binwalk cabextract patchelf nmap putty wireshark fscan okteta radare2 sqlmap
    ```
7. python, pip

    ```bash
    sudo rm /usr/bin/python && sudo ln -s /usr/bin/python3 /usr/bin/python
    pip install \
    	datetime argparse colorama cryptography getpass4 rich readchar mmh3 toml \
    	ipython \
    	ifaddr \
    	ropgadget pwntools \
    	scapy shodan \
    	ollama
    ```
8. git

    ```bash
    git config --global user.email wkyuu@majo.im
    git config --global user.name sparkle
    git config --global credential.helper store
    git config --global init.defaultbranch main
    git config --global core.editor vim
    git config --global pull.rebase true
    ```
9.
