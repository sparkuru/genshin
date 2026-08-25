---
title: "windows-terminal"
description: "use windows terminal like terminal in linux."
date: "2022-04-16T06:28:00.000Z"
updated: "2024-11-11T06:07:06.000Z"
tags: []
draft: false
layout: "post"
slug: "windows-terminal"
---

> 欢迎使用 Windows Terminal

## installation

主要有 2 种方法安装：

* 在 Microsoft Store 直接搜索 **终端** 或者搜索 **Windows Terminal** 下载
* 非商店安装，主要是直接到官方 repo 下载和通过第三方例如 chocolate 安装，[参考](https://www.sysadm.cc/index.php/xitongyunwei/784-windows-10-ltsc-windows-terminal)

> 初始化

win10 自带的 Windows Terminal，使用 `host` 指令可以查看当前使用的 Windows Terminal 版本信息等

```powershell
PS %USERPROFILE%\wkyuu\Desktop> host

Name             : ConsoleHost
Version          : 5.1.19041.3930
InstanceId       : xxx
UI               : System.Management.Automation.Internal.Host.InternalHostUserInterface
CurrentCulture   : zh-CN
CurrentUICulture : zh-CN
PrivateData      : Microsoft.PowerShell.ConsoleHost+ConsoleColorProxy
DebuggerEnabled  : True
IsRunspacePushed : False
Runspace         : System.Management.Automation.Runspaces.LocalRunspace
```

> 创建自己的配置文件

这里默认是添加到默认 Documents 文件夹的，我修改过这个默认文档文件夹的位置，根据具体情况来找，也可以通过 Windows Terminal 直接修改：`new-item -path $profile -itemtype file -force`，然后修改文件 `notepad $profile`，个人配置文件 [参考](https://raw.githubusercontent.com/shi9uma/genshin/refs/heads/main/script/05-initial/powershell_profile.ps1)

配置完后打开一个新的终端，若出现 *无法打开 ...，因为在此系统上禁止运行脚本*，需要以管理员身份启动终端（按住 ctrl 点击选项卡里的 + 号），然后输入 `set-executionpolicy remotesigned` 选择 `Y`

## hint

> 快速计算文件 hash

在想要计算的文件的目录下输入：`certutil.exe -hashfile filename MD5`，就可以计算文件的 MD5 了

> 配置快捷键

使用快捷键查看以及绑定的 key：`Ctrl + Alt + ?`，或者输入：`Get-PSReadLineKeyHandler -bound`，也可以查看未绑定的键：`Get-PSReadLineKeyHandler -Unbound`

> 将快捷启动方式添加到右键菜单

文章头图是在正常的情况下更新好 windows terminal 后，会自动将 `Open in Windows Terminal` 添加到右键菜单，其作用是直接在当前目录下直接打开 terminal

有的时候修改了系统右键菜单相关注册表信息后，会有可能把这个快捷启动方式给注销掉，这里参考 [github](https://github.com/microsoft/terminal/issues/1060) 上提供的解决方案，这里提供手动将快捷启动方式添加到右键菜单的过程（注：下述操作中请自行替换 `[username]` 为 **自己的用户名**）

1. 挑选一个喜欢的 ico 图案，也可以从 [官方仓库](https://github.com/yanglr/WindowsDevTools/tree/master/awosomeTerminal/icons) 挑选他们提供的 ico 图标，这里以他们仓库中的 `wt_32.ico` 为例。将 ico 文件下载下来，挑选一个自己喜欢的目录，这里选择 `C:\users\[username]\pictures\ico` 目录为例，即最后目标 ico 图案的位置为 `C:\users\[username]\pictures\ico\wt_32.ico`
2. 创建一个注册表文件。打开 cmd，进入到桌面 `cd %USERPROFILE%\[username]\Desktop\`，创建一个注册表文件 `New-Item terminal.reg`
3. 使用 notepad 等文本编辑工具打开该 `terminal.reg`，将下述内容添加进去并保存（注意修改 `[username]` 项）

    ```ini
    Windows Registry Editor Version 5.00

    [HKEY_CLASSES_ROOT\Directory\Background\shell\wt]
    @="Open in Windows Terminal"
    "Icon"="C:\\users\\[username]\\pictures\\ico\\wt_32.ico"

    [HKEY_CLASSES_ROOT\Directory\Background\shell\wt\command]
    @="C:\\Users\\[username]\\AppData\\Local\\Microsoft\\WindowsApps\\wt.exe -d ."
    ```
4. 在桌面运行该 `terminal.reg` 文件，此时再查看右键菜单则可以发现 `Open in Windows Terminal` 项了

## wsl

WSL（Windows Subsystem for Linux），通过 windows terminal 直接打开一个 linux 子系统；如无特别说明，以下的 wsl 都是指 wsl2

**重要**：在启动了 hyper-v 之后，会导致旧版本的 vmware workstation 无法兼容使用，在 15.5.5 版本之后这个问题得到了解决。目前市面上的 安卓模拟器 基本都和 hyper-v 不兼容，启用将导致安卓模拟器无法启动

> wsl 具体安装流程如下

1. 启用电脑虚拟化

    1. 启用子系统：在 windows terminal 中输入 `dism.exe /online /enable-feature /featurename:Microsoft-Windows-Subsystem-Linux /all /norestart`
    2. 启用电脑虚拟化：`dism.exe /online /enable-feature /featurename:VirtualMachinePlatform /all /norestart`
    3. 修改 boot 信息：`bcdedit /set hypervisorlaunchtype auto`
    4. 重启 windows，并按住 F2 进入机器的 bios（不同的机子进入 bios 的方式可能不同），在 `Advanced - SVM mode - enable` 启动机器的虚拟化
    5. 在控制面板，找到 **启用或关闭 windows 功能**，勾选 **Hyper-V（也叫 Windows 虚拟机监控程序平台）** 、**适用于 Linux 的 Windows 子系统**、**虚拟机平台** 三个选项
    6. 重启电脑
    7. 启用 wsl2：`wsl --set-default-version 2`
2. 获取并安装 wsl 系统，这里使用 kali-linux 来演示，其他的例如 ubuntu-20.04 的安装方法网上也有，基本流程大致相同

    1. 列出目前支持的 wsl 系统：`wsl --list --online`
3. 获取对应的 wsl 系统：`wsl --install -d kali-linux`，-d 表示指定 distribution，操作可能需要代理；
    1. 如果出现 *WslRegisterDistribution failed with error: 0x800701bc* 报错，需要下载 wsl2 [更新包](https://wslstorestorage.blob.core.windows.net/wslblob/wsl_update_x64.msi) 并安装
    2. 出现 *WslRegisterDistribution failed with error: 0x80004005* 报错，[参考](https://blog.csdn.net/weixin_43891732/article/details/133672607)，打开 `计算机\HKEY_LOCAL_MACHINE\SYSTEM\CurrentControlSet\Services\LxssManager` 注册表，修改 `start` 项为 2，然后在 terminal 中 `wsl --update`
    3. 安装完成后，输入 wsl 即可进入系统，初次启动会提示创建一个普通账户和输入密码，创建完成后，每次登录 wsl，只需要输入 `wsl` 即可。如果安装了多个 wsl 的分发版，输入 `wsl -l --all` 可以查看所有分发版的信息，输入 `wsl -d <第一列的名字>` 即可登录对应分发版
4. （可选）修改 wsl 默认安装路径，通过以上流程安装 wsl 后，wsl 的默认位置是在 c 盘下的，为了防止过于占用 c 盘空间，可以自定义修改这个位置

    1. 首先将已经安装好的 wsl 系统导出（以  kali-linux 为例）：`wsl --export kali-linux d:/bin/wsl/kali.tar`，可以在 **d:/bin/wsl** 目录下看到一个 **kali.tar** 文件
    2. 注销装载在 C 盘的 wsl 系统：`wsl --unregister kali-linux`
    3. 重新导入装载在其他盘符的 wsl 系统：`wsl --import kali-wsl(想要给新的 wsl 命名的名字) d:/bin/wsl/kali(想要把这个 wsl 放在哪个具体的地方) d:/bin/wsl/kali.tar(第 1 步导出的 tar 包) --version 2`
    4. 操作完成后查看刚才导入的 wsl 系统：`wsl -l --all`，这里第一列显示的就是刚刚保存的 wsl 的名字
    5. 登录系统：`wsl -d kali-wsl`，这个看第 4 步给出的具体名字
    6. （可选）由于通过以上的方式默认会以 **root** 登录到 wsl，可以在 wsl 系统中更改默认启动名，通过 `vim /etc/wsl.conf`，该文件不止修改默认登录用户名，还用于修改启动 wsl 时一些默认设置，下面给出一些常用的配置信息；

        ```ini
        [user]	# 修改默认用户名
        default = someone

        [boot]	# 启用 systemd, 为了后续使用 containerd 等提供方便
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

        配置完成后，退出 wsl：`wsl --shutdown kali-linux`，然后重新进入 wsl 即可
5. （可选）安装 Hyper-V 管理器

    Windows 10 家庭普通版有可能没有 Hyper-V 管理器，需要手动添加，方法如下

    1. 打开终端进入桌面，创建一个批处理文件：`New-Item hyper.cmd`，并将以下内容复制到其中

        ```cmd
        pushd "%~dp0"
        dir /b %SystemRoot%\servicing\Packages\*Hyper-V*.mum >hyper-v.txt
        for /f %%i in ('findstr /i . hyper-v.txt 2^>nul') do dism /online /norestart /add-package:"%SystemRoot%\servicing\Packages\%%i"
        del hyper-v.txt
        Dism /online /enable-feature /featurename:Microsoft-Hyper-V-All /LimitAccess /ALL
        ```
    2. 右键管理员运行该脚本，会跳出一个 cmd 自动安装，安装完成后提示按 Y 重启即可
    3. 重启完成后，打开控制面板，搜索 **启用或关闭 Windows 功能** 并进入，此时可以发现已经出现了 Hyper V 的功能，将其勾选上即可
    4. 再按 `Win + S` 可以打开搜索框，在搜索框中输入 hyper，就会给出搜索结果，点击打开 Hyper-V 管理器即可

> 解决 wsl 无法与宿主机共用代理

这个原因是由于 **wsl 和主机的 ip 不同**，导致被 Windows Defender 当作公网链接屏蔽，在 wsl 上配置代理接口后，仍然无法连接主机的 clash 代理，因此需要手动配置防火墙规则，操作流程如下

* 原理

  1. 在 wsl 中，输入 `cat /etc/resolv.conf` 找到 nameserver 项即为主机相对于 wsl 的 ip 地址，例如 172.28.240.1；输入 `hostname -I` 返回地址即为 wsl 内主机的 ip 地址，例如 172.28.255.219
  2. 在 clash 的 dashboard 中，勾选 `Allow LAN`，可以点一下后面的 network interfaces 选项查看相关网络，找到 `vEthernet (WSL)` 项，看看 Address 是否与上一步 nameserver 的 ip 相同
  3. 在 wsl 内正常配置代理： `export all_proxy=http://ip:port`，例如这里为 `http://172.28.240.1:7890`
  4. 使用管理员打开 terminal（按住 ctrl + 鼠标左键点击新建选项卡），输入以下防火墙规则：`New-NetFirewallRule -DisplayName "WSL" -Direction Inbound -InterfaceAlias "vEthernet (WSL)" -Action Allow`，此时 wsl 中应该能够正常使用主机的代理
* 进阶版，**该方法在 Windows 10 不可用，至少需要升级到 Windows 11 22H2**，由于每次关机 hyper-V 都会删除掉 wsl 的网卡 vEthernet（WSL），上述方法需要每次开机都重新添加一次防火墙规则，于是可以采用下面的方案来实现一劳永逸，其原理是手动创建一张虚拟网卡并为其添加入站规则，并在 wsl 的配置文件中指定该网卡；[参考 1](https://learn.microsoft.com/zh-cn/windows/wsl/networking#accessing-a-wsl-2-distribution-from-your-local-area-network-lan)，[参考 2](https://zhuanlan.zhihu.com/p/593263088)，[参考 3](https://learn.microsoft.com/zh-cn/virtualization/hyper-v-on-windows/quick-start/connect-to-network)，[参考 4](https://cloud.tencent.com/developer/article/1352777)，[参考 5](https://blog.xzr.moe/archives/273/)
* **暗度陈仓（推荐）** ：由于主要矛盾就是 wsl 的网络流量被宿主机的防火墙挡住，则可以采用 **不指定网卡来创建防火墙入站规则，而是根据 ip 网段来制定入站规则的方式** 来回避网卡自动删除的问题。基本流程与前文原理相同，就是最后的入站规则修改成 `New-NetFirewallRule -DisplayName "wsl" -Direction Inbound -LocalPort Any -Protocol Any -RemoteAddress 172.28.240.1/20 -Action Allow`，这里的 `172.28.240.1/20` 来自于 `nameserver 172.28.240.1` 和 `mask 172.28.240.0`
* 宿主机使用 Tun 模式：常见的 clash core 或 clash like 的发行版都带有 "虚拟网卡" 模式（或 Tun 模式），开启该模式后，相当于 clash 模拟出一张网卡，然后让主机内所有流量都走这个网卡，在 "路由" 层面解决代理的问题

> 让 wsl 常驻在后台

一般启动 wsl 时就是通过 terminal，在工作时会不小心关闭所有 terminal 导致 wsl 实例关闭，因此对于计算机资源富足的用户，推荐使用启动脚本的方式让 wsl 在后台永远运行，即使关闭了 console 也不必担心 wsl 失效；[参考 1](https://askubuntu.com/questions/1435938/is-it-possible-to-run-a-wsl-app-in-the-background)，[参考 2](https://github.com/microsoft/WSL/issues/8854#issuecomment-1421910739)

1. 修改 powershell 配置文件，添加以下函数：

    ```powershell
    function kali {
        $shell = New-Object -ComObject WScript.Shell
        $running = Get-WmiObject Win32_Process | Where-Object { $_.Name -eq "wsl.exe" } | Select-Object -ExpandProperty CommandLine
        if ($running -like "*kali*") {
            wsl --distribution kali
        } else {
            $shell.Run("wsl --distribution kali", 0)
            Write-Host "Starting Kali WSL instance in background." -ForegroundColor Yellow
        }
    }

    function kalidown {
        $running = Get-WmiObject Win32_Process | Where-Object { $_.Name -eq "wsl.exe" } | Select-Object -ExpandProperty CommandLine
        if ($running -like "*kali*") {
    		wsl --shutdown kali
    		Write-Host "Shutting down Kali WSL instance." -ForegroundColor Yellow
        } else {
    		Write-Host "no kali wsl instance running, type kali to start one." -ForegroundColor Yellow
        }
    }
    ```
2. 第一次打开 terminal 时，输入 `kali` 即可在后台注册一个 wsl 实例；输入 `kalidown` 注销所有 kali for wsl 实例；再也不用担心关闭 console 即关闭所有 wsl 的情况了

> 让 wsl 访问 usb 设备

wsl 本质是虚拟机，不像 vmware 一样有专门适配的 usb 连接媒介选择；wsl 默认内核中没有添加 usb 存储设备的相关支持驱动；

因此主要解决以上两个问题：

* 允许 wsl 访问宿主机的 usb 设备

  usbipd-win 是一个用于将 usb i/o 信息封装到 tcp/ip 数据包中，通过网络传输实现 usb 信息共享的项目

  1. 在 terminal 中安装 usbipd：`winget install --interactive --exact dorssel.usbipd-win`，按照要求完成安装
  2. 在 wsl 中安装 usbipd：`sudo apt install usbip hwdata usbutils`
* 为 wsl 添加 usb 存储设备驱动支持

  只能自己编译一份 wsl kernel，在启动时指定 kernel

  1. 获取 wsl 源码：`git clone https://github.com/microsoft/WSL2-Linux-Kernel.git`，当然由于通过 git 下载体验不好，建议直接去下载 zip 包 [release](https://github.com/microsoft/WSL2-Linux-Kernel/releases/)；复制到 wsl 里，并解压：`unzip WSL2-Linux-Kernel-linux-msft-wsl-xxxx.zip`
  2. 安装编译环境：`sudo apt install libncurses-dev flex bison build-essential libssl-dev libelf-dev dwarves bc`
  3. 进入解压出来的目录，编辑内核配置文件：`make menuconfig KCONFIG_CONFIG=Microsoft/config-wsl`，会弹出一个列表界面，按照以下路径：**Device Drives - USB Support - Support for Host-side USB - 往下拉找到 USB Mass Storage support**，按 `Y` 会选中，并在下方弹出更多选择，一路选择下去，直到 **USB Imaging devices** 之前；选择完成后，按左右移动到  **&lt;Save&gt;**  并回车保存，然后一路  **&lt;Exit&gt;**  退出
  4. 确保在项目目录下，开始编译内核：`make -j$(nproc) bzImage KCONFIG_CONFIG=Microsoft/config-wsl`，编译过程缺什么用 apt-get 补什么；编译时长大约在 10 分钟左右（Ryzen 7 4800H）
  5. 编译完成后，在 `arch/x86/boot` 目录下获取 bzImage：`file arch/x86/boot/bzImage`，*arch/x86/boot/bzImage: Linux kernel x86 boot executable bzImage, version 5.15.146.1-microsoft-standard-WSL2 (wkyuu@kali)* ；将其移动到宿主机中
  6. 在宿主机的用户目录下创建一个 `.wslconfig` 文件，在其中指定 kernel：

      ```ini
      [wsl2]
      kernel=path/to/bzImage
      ```

      重启 wsl 即可：`wsl --shutdown`，重启后使用 `uname -r` 查看内核版本是否和上边的 5.15.146.1 一致
  7. 在宿主机首先 `ctrl + 鼠标左键点击"+"号` 打开管理员终端，输入 `usbipd list` 查看已接入 usb 设备，记录其 BUSID（以 2-2 为例），然后绑定：`usbipd bind -b 2-2`，`usbipd attach -b 2-2 --wsl`，如果出现 *usbipd: error: Mounting 'C:\Program Files\usbipd-win\WSL' within WSL failed.*  的报错，则在 wsl 中执行以下指令：

      ```bash
      sudo su -c '[ ! -d /var/run/usbipd-win ] && mkdir /var/run/usbipd-win'
      sudo mount -t drvfs -o "ro,umask=222" "C:\Program Files\usbipd-win\WSL" "/var/run/usbipd-win"
      ```

      然后重启 wsl，在 wsl 中执行：`lsusb` 即可看到 usb 设备；注意，使用 usbipd bind 设备后，如果不主动：`usbipd unbind -b 2-2`，会导致宿主机无法识别设备
  8. [参考](https://www.cnblogs.com/feiquan/p/12806081.html)，如果使用 adb 调试安卓设备时出现：*missing udev rules? user is in the plugdev group* 的提示，则在 `~/.zshrc` 中写入以下内容：

      ```bash
      update_adb() {
          adb_result=$(adb devices 2>&1)
          if echo "$adb_result" | grep -q 'missing udev rules'; then
              lsusb_output=$(lsusb)

              while read -r line; do
                  idVendor=$(echo $line | awk '{print $6}' | cut -d ':' -f1)
                  idProduct=$(echo $line | awk '{print $6}' | cut -d ':' -f2)

                  if [[ $line == *'ADB'* ]] && [[ ! -z $idVendor ]] && [[ ! -z $idProduct ]]; then
                      echo "Creating /etc/udev/rules.d/90-android.rules file. Please run with sudo permissions."
                      rule='SUBSYSTEM=="usb",ATTRS{idVendor}=="'$idVendor'",ATTRS{idProduct}=="'$idProduct'",MODE="0666",GROUP="plugdev",SYMLINK+="android",SYMLINK+="android_adb"'
      		        rule_path='/etc/udev/rules.d/90-android.rules'
      		        sudo sh -c "echo $rule > $rule_path"
                      if [ $? -eq 0 ]; then
                          sudo udevadm control --reload-rules
                          sudo service udev restart
                          sudo udevadm trigger
                          adb kill-server
                          echo "Updated Android adb permissions successfully."
                      else
                          echo "Error: Permission denied. Please run with sudo permissions."
                      fi
                      break
                      echo "Updated Android adb permissions."
                      break
                  fi
              done <<< "$lsusb_output"
          fi
      }
      ```

      完成后更新 shell：`source ~/.zshrc`，之后每次连接设备如果再出现错误，输入 `update_adb` 来刷新权限问题

## fault

> 解决中文乱码问题

powershell 默认使用系统默认文字编码格式，家庭简体中文版是 GBK，打上中文容易乱码，

1. 解决方法是修改 `$profile` 文件，输入以下内容

    ```ini
    $OutputEncoding = [console]::InputEncoding = [console]::OutputEncoding = New-Object System.Text.UTF8Encoding
    ```
2. 使用 `win + x` 键打开菜单，用管理员身份运行 cmd
3. 在打开的cmd里输入 `powershell` 打开一个新终端
4. 然后在 powershell 中输入 `Set-ExecutionPolicy Unrestricted`

> 启动 wsl 时出现 "参考的对象类型不支持尝试的操作"

这是由于系统代理起了冲突，输入 `netsh winsock reset` 即可解决

## reference

1. [将 powershell 的编码默认改为 UTF-8](https://blog.csdn.net/qq_39494169/article/details/122561317)
2. [史上最全的 WSL 安装教程](https://zhuanlan.zhihu.com/p/386590591)
3. [wsl 官方配置](https://learn.microsoft.com/zh-cn/windows/wsl/wsl-config)
4. [WSL2 中的高级设置配置 wsl.conf 和 .wslconfig](https://cloud.tencent.com/developer/article/2154076)
5. [Win10 WSL2 链接主机代理](https://zhuanlan.zhihu.com/p/592620059)
6. [WSL2 的一些网络访问问题](https://cat.ms/wsl2-network-tricks)
7. [WSL2 连接 USB 存储设备](https://zhuanlan.zhihu.com/p/661175117)
8. [使用 WSL2 解决在 Windows 中读写 Btrfs、Ext4 等 Linux 文件系统的 USB 存储设备](https://blog.csdn.net/m0_72123696/article/details/136288493)
