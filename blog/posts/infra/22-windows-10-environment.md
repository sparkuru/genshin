---
title: "init-my-windows-10"
description: "到头来还是 windows 10（划掉）"
date: "2024-09-05T17:19:00.000Z"
updated: "2025-05-08T08:14:43.000Z"
tags: []
draft: false
layout: "post"
slug: "windows-10-environment"
---

## init my windows 10

windows 10 + 各种常用软件（快捷键） + wsl + vscode

## 01

1. 制作系统盘：
   1. 一个不用的 U 盘，8G 以上
   2. 一个 windows 10 镜像，到这下载：
   3. 使用工具 rufus 制作系统盘，根据具体情况进行客制化
2. 可以用于文件中转的设备，例如文件分享平台、内网主机，下载以下 [链接](#) 中的东西放到中转平台以备用

## 02

1. 地区选新加坡，语言选新加坡简中，登陆微软账号，关闭各类隐私跟踪，关闭位置等
2. 进入到系统

   1. 配置任务栏右键

   2. 配置文件管理器的文件夹选项

   3. 配置语言输入法

   4. 关闭 windows 提示音
3. （安装完后）使用 dism++、content-manager 配置系统，使用 geek 卸载 microsoft onedrive
4. 更改鼠标图标
5. 备份一份注册表文件


## 03

1. 将系统分为三个（如果只有 1t，就两个）盘：c 盘名称 os，d 盘名称 app，e 盘名称 e。容量按照实际需求来，一般是 300g、633g、1t
2. 将 `x:/dir` 文件夹下的文件夹路径直接复制到对应盘符，也可以手动：
   1. `python -c "import os;print('mkdir ',end='');[ print(f'\'{x}\'',end=' ') for x in os.listdir() if os.path.isdir(x) and x not in ('\$RECYCLE.BIN', 'System Volume Information')]"`
   2. 在 d 盘创建目录：`mkdir driver lang project sec software bin`
   3. 在 e 盘创建目录：`mkdir game virtual-machine tmp`

3. 到 `c:/users/user` 下，将对应的文件目录修改到相应的位置，迁移 home 目录中的内容
   1. 将 `document` 移动到 `d:/`
   2. 将 `3d-object`、`saved-game`、`contact`、`link`、`favorite`、`search` 移动到 `d:/home/`
   3. 将 `picture`、`video`、`music`、`download` 移动到 `e:/`；然后将 `picture/Saved Picture` 移动到 `picture/picture/saved-picture`； `picture/Camera Roll` 移动到 `picture/picture/camera-roll`
4. 获取完整压缩包，包含 `core`、`extra`、`link` 三个文件夹
   1. `extra` 文件夹
      1. 先创建 `d:/software/bandizip` 文件夹，然后安装 bandizip 到 `d:/software`，会自动识别并安装
      2. 由于 windows 自带的 microsoft defender 会误杀，先创建 `d:/software/huorong`，然后安装火绒到该位置；打开火绒，右上角设置 - 常规设置 / 病毒防护，将自动处理全部改成询问我
      3. 激活时，选择 `智能激活/数字许可证激活`

   2. `core` 文件夹，复制粘贴、有 exe 的直接安装
   3. `link` 文件夹，直接复制到 `C:/ProgramData/Microsoft/Windows/Start Menu/Programs` 目录下

## other

1. Bandizip-Professional-7.36-x64-Repack.exe
2. ChromeSetup.exe
3. disk-genius.exe
4. geek.exe
5. Microsoft.WindowsTerminal.msixbundle
6. office-365.img
7. sysdiag-all-5.0.75.10-2024.08.24.1.exe
8. terminal-settings.json
9. uTools-5.2.1.exe
10. Windows-11-Cursors-Concept-HD-v2.zip

## d

### software

1.   anlink
2.   archive
3.   baidu-netdisk
4.   bandizip
5.   bitcomet
6.   clash
7.   context-menu-manager
8.   dandanplay
9.   dingding
10.   dism-pp
11.   everything
12.   filezilla
13.   glary-utilities
14.   huorong
15.   livehime
16.   netease-cloud-music
17.   netease-sirius-desktop
18.   netease-uu
19.   obs-studio
20.   picgo
21.   pikpak
22.   potplayer
23.   sublime-text
24.   sumatra-pdf
25.   telegram-desktop
26.   tencent-qq-music
27.   tencent-qq-nt
28.   tencent-wechat
29.   tencent-wemeet
30.   thunder
31.   tor-browser
32.   typora
33.   visual-studio-code
34.   vmware-workstation
35.   xmind
36.   xnview

### bin

1.   archive
2.   btop4win
3.   deskpins
4.   fd
5.   ffmpeg
6.   frp
7.   fzf
8.   git
9.   licecap
10.   nginx
11.   opendhcp-server
12.   pandoc
13.   ripgrep
14.   snipaste
15.   sysinternals
16.   tftpd
17.   tree
18.   vim
19.   wsl
20.   disk-genius.exe
21.   geek.exe
22.   draw.io.exe
23.   rufus.exe
24.   space-sniffer.exe

### sec

1. android
   1. android-platform-tool
   2. apk-easy-tool-portable
   3. miflash
   4. mppg-qualcomm-premium-tool
   5. payload-dumper-go
2. archive
3. burpsuite
4. caidao
5. cheat-engine
6. dnspy
7. fiddler
8. fofa-viewer
9. frida
10. ghidra
11. ida
12. jadx
13. last-activity-view
14. ollydbg
15. packet-sender-portable
16. peditor
17. peid
18. process-monitor
19. putty
20. serial-port-utility
21. uni-extract
22. upx
23. winhex
24. wireshark
25. x64dbg
26. xftp
27. xshell

### driver

1. android
2. directx
3. driver
4. 系统测试
   1. super_pi_mod.exe
   2. tulading，图吧工具箱

5. 系统激活
   1. HEU_KMS_Activator_42.0.0.exe
   2. XP系统激活工具


## e

### game

1. butter
2. electronic-arts
3. epic
4. game-software
   1. game-cheats-manager
   1. gcfscape
5. miHoYo
   1. 01-miHoYo-launcher
   2. 02-genshin
   3. 03-honkai-starrail
6. minecraft
   1. markdown
   2. mine
      1. 01-hmcl
      2. 02-pcl2
   3. package
   4. tool
7. other，放独立游戏
8. rockstar
9. steam
10. ubisoft

### picture

1. markdown
2. other
   1. emoji
   2. icon
   3. meme
   4. oicq
      1. ecchi
      2. ero
   5. pretty
   6. profile
   7. wallpaper
3. picture
   1. camera
   2. camera-roll
   3. saved-picture

4. snipaste

### video

1. comic
2. movie
3. other
   1. oicq
4. capture
   1. gacha
   1. genshin

### virtual-machine

1. 01-debian-kali
2. 02-windowsnt-10
3. 03-windowsnt-7
4. 04-debian-ubuntu-22.04

## link

将 `link` 目录下的快捷方式文件，直接清空替换 `C:/ProgramData/Microsoft/Windows/Start Menu/Programs` 文件夹即可

顺便清空 `c:/users/wkyuu/AppData/Roaming/Microsoft/Windows/Start Menu/Programs` 目录

## further

1. 配置环境变量：`wget -O init-windows-10-env.ps1 https://raw.githubusercontent.com/shi9uma/genshin/main/script/05-initial/init-windows-10-env.ps1`，然后允许 powershell 使用脚本：`Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

2. 配置 terminal：将 `extra/terminal-settings.json` 覆盖掉 terminal 的默认配置

3. 配置 wsl

   1. 安装 `d:/driver/driver/wsl_update_x64`、`dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart`、`dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart`、`bcdedit /set hypervisorlaunchtype auto`

   2. 重启

   3. `wsl --set-default-version 2`

   4. 在 `计算机\HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\LxssManager` 中，将 `start` 改成 2，然后 `wsl --update`

   5. `wsl --install -d kali-linux`、`wsl --export kali-linux d:/bin/wsl/kali.tar`

   6. `wsl --import kali d:/bin/wsl/kali d:/bin/wsl/kali.tar --version 2`（先试试这一步，如果不行再正常导入导出）

   7. `wsl --unregister kali-linux`

   8. `vim /etc/wsl.conf`：

      ```ini
      [user]	# 修改默认用户名
      default = wkyuu
      
      [boot]	# 启用 systemd, 为了后续使用 mysqld 等提供方便
      systemd = true
      
      [interop]	# wsl 在启动时会自动拓展 windows 的 path, 在此设置为 false 关闭
      appendWindowsPath = false
      
      [automount]	# 自动挂载文件系统, 注意只有挂载后, 才能从宿主机直接访问文件系统
      enabled = true
      root = /
      options = "metadata,umask=22,fmask=111"
      mountFsTab = true
      
      [network]	# 为主机配置主机名
      hostname = kali
      ```

      `wsl --shutdown kali`

   9. `chsh -s /usr/bin/zsh`

   10. 剩下的参考 [init-my-unix](https://www.majo.im/index.php/wkyuu/356.html)

4. 配置 python 环境

   1. `touch ~/pip/pip.ini`：

      ```ini
      [global]
      index-url = https://mirrors.ustc.edu.cn/pypi/simple
      [install]
      trusted-host = https://mirrors.ustc.edu.cn
      ```

   2. `pip install argparse cryptography scapy netifaces wsgidav shodan datetime colorama ipython getpass4`

5. 配置 git 环境：`touch git.ps1`

```powershell
   git config --global user.email wkyuu@majo.im
   git config --global user.name shiguma
   git config --global credential.helper store
   git config --global init.defaultbranch main
   git config --global core.editor vim
   
   git config -l
```

## install sw

1. `d:/lang/python`
2. `d:/sec/x`
   1. `d:/sec/ida`
   2. `d:/sec/xftp`
   3. `d:/sec/xshell`
3. `d:/software`
   1. `d:/software/anlink`
   2. `d:/software/baidu-netdisk`，绿化处理
   3. `d:/software/bandizip`，目录选择 `d:/software`
   4. `d:/software/dingding`，目录选择 `d:/software`
   5. `d:/software/everything`，安装文件夹、安装服务
   6. `d:/software/livehime`
   7. `d:/software/netease-sirius-desktop`
   8. `d:/software/netease-uu`
   9. `d:/software/picgo`
   10. `d:/software/pikpak`，目录选择 `d:/software`
   11. `d:/software/tencent-qq-music`，绿化处理
   12. `d:/software/tencent-qq-nt`，然后将 `bstar` 里改成 `version.dll` 并放到当前目录
   13. `d:/software/tencent-wechat`，
   14. `d:/software/tencent-wemeet`，
   15. `d:/software/thunder`
   16. `d:/software/typora`，选择仅为自己安装，目录选择 `d:/software`，安装完成后把 `theme.typora.iWonder-v3.0.0.zip` 里的内容复制到 `c:/users/wkyuu/AppData/Roaming/Typora/themes`
   17. `d:/software/vmware-workstation`，增强型键盘驱动程序、不要将控制台添加到系统 PATH，
   18. `d:/software/typora`
   19. `d:/software/typora`
   20. `d:/software/typora`

## important

如果要做数据迁移、销毁、出借，需要将主用的机子的以下几个位置进行备份，在完成前文的初始化后，再将以下内容复制到对应的文件夹：

1. `c:/users/wkyuu`，需要手动全选，注意不要选到 `appdata` 目录（隐藏的）
2. `d`
   1. `d:/project`
   2. `d:/document`
3. `e`
   1. `e:/game/minecraft`
   2. `e:/video`
   3. `e:/picture`
   4. `e:/music`

同时也建议以月度为单位，将以上目录进行冷备份
