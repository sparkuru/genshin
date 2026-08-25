---
title: "init-my-dpkg"
description: "对 dpkg 初始化的可复用路径依赖"
date: "2024-09-06T15:04:00.000Z"
updated: "2026-07-16T01:39:14.000Z"
tags: []
draft: false
layout: "post"
slug: "debian-family-setup"
source: "online/13-init-my-dpkg.md"
---

## init-my-dpkg

选择 dpkg 系的 debian、ubuntu、kali 都可以，下文以 kali 为参考

1. 如果是使用 vmware 直接的镜像，需要改名
    1. `sudo passwd root`，然后使用 root 登录：`su`，关闭原 kali 用户所有进程 `pkill -9 kali`
    2. `sudo usermod -l wkyuu kali`，更新 `/home/kali` 名称为 `/home/wkyuu`：`usermod -d /home/wkyuu -m wkyuu`
    3. 修改组名：`sudo groupmod -n wkyuu kali`
2. 如果是新装系统，用户名和密码都在新装时设置过（地区选择新加坡），则按照正常流程就可以；如果没有新装设置非 root 用户，可以按照以下方式
    1. `export newuser="wkyuu"`
    2. 先尝试 `adduser $username`，这种方式更智能，可以自动设置下面大部分内容
    3. 手动新增：
        1. 创建新组：`groupadd $newuser`
        2. 新 home 目录：`mkdir -p /home/$newuser`，`chown -R newuser:newuser /home/$newuser`
        3. 新建用户，并指定默认 shell、新建同名组、添加到其他组、指定 home 目录：`useradd -s $(which zsh) -g $newuser -G adm,sudo,docker -d /home/$newuser $newuser`
        4. 修改密码：`passwd $newuser`
        5. 也可以使用 usermod 为用户配置各种用户信息：`usermod -s /usr/bin/zsh -d /home/$newuser -g another_group $newuser`
    4. 如果想删除用户：`userdel -fRrz $newuser`
3. （可选）修改 sudoers 文件配置免密 sudo：`sudo su`，`visudo`，在 `%sudo ALL=(ALL:ALL) ALL` 下方加入一行 `wkyuu ALL=(ALL:ALL) NOPASSWD:ALL`
4. 换源，`vim /etc/apt/sources.list`
    ```ini
    deb https://mirrors.ustc.edu.cn/kali kali-rolling main non-free non-free-firmware contrib
    deb-src https://mirrors.ustc.edu.cn/kali kali-rolling main non-free non-free-firmware contrib
    ```
    `sudo apt update`
5. 配置网络
    1. 安装网络管理器：`sudo apt install network-manager`
    2. `nmcli networking` 检查网络接管状态，如果是 `disabled`，则 `nmcli networking on`
    3. 输入 `nmcli connection show` 可以查看网卡情况

一键脚本，参考：`https://raw.githubusercontent.com/sparkuru/genshin/main/mtf/init-dpkg.sh`

## other

### 多系统设计

```bash
# fdisk -l
Disk /dev/nvme0n1：1.86 TiB，2048408248320 字节，4000797360 个扇区
磁盘型号：ZHITAI TiPlus7100 2TB
单元：扇区 / 1 * 512 = 512 字节
扇区大小(逻辑/物理)：512 字节 / 512 字节
I/O 大小(最小/最佳)：512 字节 / 512 字节
磁盘标签类型：gpt
磁盘标识符：C167EC97-3411-4B16-91FF-531D271EE25E

设备            起点       末尾       扇区  大小 类型
/dev/nvme0n1p1  2048 4000796671 4000794624  1.9T Linux home


Disk /dev/nvme1n1：1.82 TiB，2000398934016 字节，3907029168 个扇区
磁盘型号：Fanxiang P761 2TB
单元：扇区 / 1 * 512 = 512 字节
扇区大小(逻辑/物理)：512 字节 / 512 字节
I/O 大小(最小/最佳)：512 字节 / 512 字节
磁盘标签类型：gpt
磁盘标识符：F0BA6B44-5E54-954B-8791-D357D59C7847

设备              起点       末尾       扇区  大小 类型
/dev/nvme1n1p1    2048    1050623    1048576  512M EFI 系统
/dev/nvme1n1p2 1050624 3907028991 3905978368  1.8T Linux 文件系统

# df -h
文件系统        大小  已用  可用 已用% 挂载点
/dev/nvme1n1p2  1.8T  103G  1.6T    6% /
devtmpfs        4.0M     0  4.0M    0% /dev
tmpfs            16G  108M   16G    1% /dev/shm
efivarfs        128K   43K   81K   35% /sys/firmware/efi/efivars
tmpfs           6.2G  4.7M  6.2G    1% /run
tmpfs           1.0M     0  1.0M    0% /run/credentials/systemd-journald.service
tmpfs           1.0M     0  1.0M    0% /run/credentials/systemd-resolved.service
tmpfs            16G   34M   16G    1% /tmp
/dev/nvme1n1p1  511M  148K  511M    1% /boot/efi
/dev/nvme0n1p1  1.9T  342G  1.5T   20% /home
overlay         1.8T  103G  1.6T    6% /var/lib/docker/overlay2/95a236ea8c03744fb11b19a3755374bec05f21367e567cf0e6a4f0a20a8ee755/merged
overlay         1.8T  103G  1.6T    6% /var/lib/docker/overlay2/ac87c55c6d2b87363002a1c0822ad93f4caca55f32503d93185d00bac0964ca1/merged
overlay         1.8T  103G  1.6T    6% /var/lib/docker/overlay2/561941862c607ba7a286299f0fcb3fecbf85f55f52e896f91a4608f3cee73b7a/merged
overlay         1.8T  103G  1.6T    6% /var/lib/docker/overlay2/a01afb6e5e570d31c21cb8a39eb52b734c2c9e3cdfcf149a0ea599b306936e42/merged
tmpfs           3.1G  168K  3.1G    1% /run/user/1001
```

打算将 `/dev/nvme0` 做一个双系统：原本的 kali（主要），备用的 windows：

1. 主要是 linux，通过 grub 选择 kali、windows
2. linux 分 512G 大小，剩下全给 windows
3. `/dev/nvme1` 是 `/home`，做了双盘设计，这一块在 windows 下不要做任何操作

操作如下：

1. `sudo apt install parted`
2. 使用 parted 管理盘
    ```bash
    parted /dev/nvme1n1

    # 查看当前盘符信息
    (parted) print

    # 这里的 2 对应 /dev/nvme1n1p2
    (parted) resizepart 2 512GB
    (parted) quit

    # 确认调整
    sudo resize2fs /dev/nvme1n1p2
    ```
3. 此时通过 ventoy 等工具，将剩下的 1.8t - 512g = 1.3t 用作 windows 系统管理的盘符：
    1. 安装 windows，在盘符选择过程中，主动选择这多出来的空间
    2. 重启回到 kali，通过 grub 工具将 windows boot 选项添加到 efi：
        ```bash
        # os-prober                                   
        /dev/nvme1n1p1@/EFI/Microsoft/Boot/bootmgfw.efi:Windows Boot Manager:Windows:efi

        # sed "s/#GRUB_DISABLE_OS_PROBER/GRUB_DISABLE_OS_PROBER/i" /etc/default/grub > /etc/default/grub

        # update-grub
        Generating grub configuration file ...
        Found theme: /boot/grub/themes/kali/theme.txt
        Found linux image: /boot/vmlinuz-6.12.33+kali-amd64
        Found initrd image: /boot/initrd.img-6.12.33+kali-amd64
        Warning: os-prober will be executed to detect other bootable partitions.
        Its output will be used to detect bootable binaries on them and create new boot entries.
        Found Windows Boot Manager on /dev/nvme1n1p1@/EFI/Microsoft/Boot/bootmgfw.efi
        Adding boot menu entry for UEFI Firmware Settings ...
        done
        ```
    3. 重启后即可看到 windows 选项，正常安装 windows 即可，需要注意的是，安装 windows 期间会好几次重启，需要在每次进入到 boot menu 时选择 windows

## 双系统及 home 分离

由于 vmware in linux 已经很好用了，主力系统用的就是 debian 13，但是仍辅以双系统（windows 11） + `/home` 分离设计

```bash
$ sudo fdisk -l
Disk /dev/nvme1n1: 1.86 TiB, 2048408248320 bytes, 4000797360 sectors
Disk model: ZHITAI TiPlus7100 2TB                   
Units: sectors of 1 * 512 = 512 bytes
Sector size (logical/physical): 512 bytes / 512 bytes
I/O size (minimum/optimal): 512 bytes / 512 bytes
Disklabel type: gpt
Disk identifier: C167EC97-3411-4B16-91FF-531D271EE25E

Device         Start        End    Sectors  Size Type
/dev/nvme1n1p1  2048 4000796671 4000794624  1.9T Linux home


Disk /dev/nvme0n1: 1.82 TiB, 2000398934016 bytes, 3907029168 sectors
Disk model: Fanxiang P761 2TB                       
Units: sectors of 1 * 512 = 512 bytes
Sector size (logical/physical): 512 bytes / 512 bytes
I/O size (minimum/optimal): 512 bytes / 512 bytes
Disklabel type: gpt
Disk identifier: F0BA6B44-5E54-954B-8791-D357D59C7847

Device          Start        End   Sectors   Size Type
/dev/nvme0n1p1   2048     999423    997376   487M EFI System
/dev/nvme0n1p2 999424 1000998911 999999488 476.8G Linux filesystem
```

以上是原来的双系统设计，新的设计是：

1. 备份 nvme1 下，windows 重要内容
2. 备份 nvme0（也就是在用的 aosc）下的 `/home`
3. 在 nvme0 装 aosc，挂载在 `/`（如果已有 linux 系统，则不需要重装，配置一下硬盘即可，参考下文）；将 nvme1 挂载到 `/home`

在这种设计下，只需要确保 nvme1 不损坏，备份也只备份 nvme1（也就是 `/home`），而底层系统（挂载在 `/` 的可以随便换其他 linux），真正做到换系统不换系统配置

不需要重装 linux，当然是可以直接重新挂载的：

1. 首先确定分区的内容（注意每次开机都有可能会给不同的盘分不同的盘符标识，需要以当次为准）
    ```bash
    # fdisk -l
    Disk /dev/nvme1n1：1.86 TiB，2048408248320 字节，4000797360 个扇区
    磁盘型号：ZHITAI TiPlus7100 2TB
    单元：扇区 / 1 * 512 = 512 字节
    扇区大小(逻辑/物理)：512 字节 / 512 字节
    I/O 大小(最小/最佳)：512 字节 / 512 字节
    磁盘标签类型：gpt
    磁盘标识符：C167EC97-3411-4B16-91FF-531D271EE25E

    设备                 起点       末尾       扇区  大小 类型
    /dev/nvme1n1p1       2048    1050623    1048576  512M EFI 系统
    /dev/nvme1n1p2    1050624 1074794495 1073743872  512G Microsoft 基本数据
    /dev/nvme1n1p3 1074794496 4000795278 2926000783  1.4T Microsoft 基本数据


    Disk /dev/nvme0n1：1.82 TiB，2000398934016 字节，3907029168 个扇区
    磁盘型号：Fanxiang P761 2TB
    单元：扇区 / 1 * 512 = 512 字节
    扇区大小(逻辑/物理)：512 字节 / 512 字节
    I/O 大小(最小/最佳)：512 字节 / 512 字节
    磁盘标签类型：gpt
    磁盘标识符：3E1686CA-F7F2-421A-9746-B7FCAEB2B77A

    设备            起点       末尾       扇区  大小 类型
    /dev/nvme0n1p2  2048 3907028991 3907026944  1.8T Linux 文件系统
    ```
2. 然后清空 nvme1n1（注意对应 windows 的分区）：
    ```bash
    # 卸载可能挂载的分区
    sudo umount /dev/nvme1n1p1
    sudo umount /dev/nvme1n1p2
    sudo umount /dev/nvme1n1p3

    # 使用 fdisk 删除所有分区并创建新分区
    sudo fdisk /dev/nvme1n1

    # 在 fdisk 界面中，依次运行以下指令
    d 然后默认回车   # 删除分区（重复此步骤直到删除所有分区，这里是三个子分区，就是三次）
    n   # 新建分区
    1   # 分区号
    默认 # 起始扇区(按回车接受默认值)
    默认 # 结束扇区(按回车使用全部空间)
    t   # 更改分区类型，输入 L 可以查看可选的分区类型，拉到最下面可以看到 home 类型
    # 别名：
    #    linux          - 0FC63DAF-8483-4772-8E79-3D69D8477DE4
    #    swap           - 0657FD6D-A4AB-43C4-84E5-0933C84B4F4F
    #    home           - 933AC7E1-2EB4-4F13-B844-0E14E2AEF915
    #    uefi           - C12A7328-F81F-11D2-BA4B-00A0C93EC93B
    #    raid           - A19D880F-05FC-4D3B-A006-743F0F84911E
    #    lvm            - E6D6D379-F507-44C2-A23C-238F2A3DF928
    #    xbootldr       - BC13C2FF-59E6-4262-A352-B275FD6F7172
    home  # 这里也可以选择其他类型，例如 linux
    w   # 写入更改并退出
    ```
3. 创建文件系统
    ```bash
    # sudo mkfs.ext4 /dev/nvme1n1p1
    mke2fs 1.47.2 (1-Jan-2025)
    丢弃设备块：完成
    创建含有 500099328 个块（每块 4k）和 125026304 个 inode 的文件系统
    文件系统 UUID：2abe4876-24c7-467b-933b-45725c316473
    超级块的备份存储于下列块：
            32768, 98304, 163840, 229376, 294912, 819200, 884736, 1605632, 2654208,
            4096000, 7962624, 11239424, 20480000, 23887872, 71663616, 78675968,
            102400000, 214990848

    正在分配组表：完成
    正在写入 inode表：完成
    创建日志（262144 个块）：
    完成
    写入超级块和文件系统账户统计信息：已完成
    ```
4. 此时新的磁盘、分区内容应该如下
    ```bash
    # fdisk -l
    Disk /dev/nvme1n1：1.86 TiB，2048408248320 字节，4000797360 个扇区
    磁盘型号：ZHITAI TiPlus7100 2TB
    单元：扇区 / 1 * 512 = 512 字节
    扇区大小(逻辑/物理)：512 字节 / 512 字节
    I/O 大小(最小/最佳)：512 字节 / 512 字节
    磁盘标签类型：gpt
    磁盘标识符：C167EC97-3411-4B16-91FF-531D271EE25E

    设备            起点       末尾       扇区  大小 类型
    /dev/nvme1n1p1  2048 4000796671 4000794624  1.9T Linux home	# 已修改


    Disk /dev/nvme0n1：1.82 TiB，2000398934016 字节，3907029168 个扇区
    磁盘型号：Fanxiang P761 2TB
    单元：扇区 / 1 * 512 = 512 字节
    扇区大小(逻辑/物理)：512 字节 / 512 字节
    I/O 大小(最小/最佳)：512 字节 / 512 字节
    磁盘标签类型：gpt
    磁盘标识符：3E1686CA-F7F2-421A-9746-B7FCAEB2B77A

    设备            起点       末尾       扇区  大小 类型
    /dev/nvme0n1p2  2048 3907028991 3907026944  1.8T Linux 文件系统
    ```
5. 将 `/dev/nvme1n1p1` 挂载到 `/home` 并设置开机自动挂载
    1. 首先复制一份原有的 `/home`：
        1. 将 `/dev/nvme1n1p1` 挂载到 `/mnt/home`，用于 `/home`
        2. `sudo rsync -aAXv /home/ /mnt/home`
        3. 备份完成后 `umount /mnt/home`
    2. 挂载：`mount /dev/nvme1n1p1 /home`，然后进 `/home` 看看是否满足原有的 home 结构；这里 mount 时，不会覆盖原有 nvme0 的 `/home`，如果确定了新的迁移方案是满足需求的，需要取消挂载后，删除掉原来的 `/home`，建议是用纯 cli + root 登陆的方式删除 `/home`
    3. （可选）如果此时通过 arch-iso 等方式配置相关信息，需要手动挂载几个路径：
        ```bash
        mount /dev/nvme0n1p2 /mnt/rootfs --mkdir

        # 具体挂载的路径
        cd /mnt/rootfs

        mount -t proc /proc proc/
        mount -t sysfs /sys sys/
        mount --rbind /dev dev/

        mount /dev/neme0n1p1 boot/efi --mkdir
        ```
    4. 设置自动挂载，通过 `genfstab -U / >> /etc/fstab` 写入开机自动挂载表
        ```bash
        # /dev/nvme1n1p2
        UUID=16b28ae6-839d-4601-801b-c57ebc5b15ff       /               ext4            rw,relatime     0 1

        # /dev/nvme0n1p1
        UUID=2abe4876-24c7-467b-933b-45725c316473       /home           ext4            rw,relatime     0 2

        # /dev/nvme1n1p1
        UUID=351C-94D8          /boot/efi       vfat            rw,relatime,fmask=0022,dmask=0022,codepage=437,iocharset=ascii,shortname=mixed,utf8,errors=remount-ro 0 2

        /.swapfile              none            swap            defaults        0 0
        ```
    5. 重启后查看是否成功实现这种分盘的设计架构
        ```bash
        # df -hl
        文件系统        大小  已用  可用 已用% 挂载点
        /dev/nvme1n1p2  1.8T  129G  1.6T    8% /	# 单盘 nvme1 挂载
        devtmpfs        4.0M     0  4.0M    0% /dev
        tmpfs            16G  103M   16G    1% /dev/shm
        efivarfs        128K   43K   81K   35% /sys/firmware/efi/efivars
        tmpfs           6.2G  4.5M  6.2G    1% /run
        tmpfs           1.0M     0  1.0M    0% /run/credentials/systemd-journald.service
        tmpfs           1.0M     0  1.0M    0% /run/credentials/systemd-resolved.service
        tmpfs            16G   18M   16G    1% /tmp
        /dev/nvme1n1p1  511M  148K  511M    1% /boot/efi
        /dev/nvme0n1p1  1.9T  490G  1.3T   28% /home	# 单盘 nvme0 挂载
        tmpfs           3.1G  152K  3.1G    1% /run/user/1000
        ```
6. 去掉无效的 windows efi 引导
    ```bash
    # 查看当前 EFI 启动项
    sudo efibootmgr -v

    # 删除 windows 的启动项（假设启动项编号为 X）
    sudo efibootmgr -b X -B
    ```

## problem

### 重打包

1. `wget https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage`
2. `chmod +x appimagetool-x86_64.AppImage`
3. `./appimagetool-x86_64.AppImage squashfs-root app.AppImage`

squashfs-root 下至少要有 `xxx.desktop` 文件，参考如下：

```ini
$ cat qq.desktop
[Desktop Entry]
Name=QQ
Exec=env LD_PRELOAD=bstar-0.5.10.so AppRun --no-sandbox %U
Terminal=false
Type=Application
# 这里的 icon，是 squashfs-root 下的路径；且最后不需要 {.png, .jpg} 这些后缀
Icon=/usr/share/icons/hicolor/512x512/apps/qq
StartupWMClass=QQ
X-AppImage-Version=35341
Categories=Network;
Comment=QQ
```
