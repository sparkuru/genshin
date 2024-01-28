# 01 iot-introduction

sth useful while learning how to bug the iot

## article

1.   各类安全文章集合，[看雪知识库](https://www.kanxue.com/chm.htm)
2.   iot 安全文章集合，[先知社区，iot 板](https://xz.aliyun.com/node/18)
3.   配置固件分析环境（1），[一步一步PWN路由器之环境搭建](https://xz.aliyun.com/t/1508)
4.   配置固件分析环境（2），[路由器固件模拟环境搭建](https://xz.aliyun.com/t/5697)
5.   配置固件分析环境（3），[固件模拟调试环境搭建](http://zeroisone.cc/2018/03/20/固件模拟调试环境搭建)
6.   iot 文章（1），[路由器通用 0day 漏洞挖掘及 RCE 思路](https://xz.aliyun.com/t/13506)
7.   ctf（1），[[原创]CTF-PWN常规题个人实战笔记（持续更新）](https://bbs.kanxue.com/thread-266142.htm)
8.   linux（1），程序是怎样运行的，[How programs get run: ELF binaries](https://lwn.net/Articles/631631/)

## tool

1.   SecureCRT，分析串口信息
2.   binwalk，用于识别和提取嵌入在 rom 中的文件系统、压缩文件、嵌入式固件等
3.   firmadyne，固件模拟工具，[firmadyne/firmadyne](https://github.com/firmadyne/firmadyne.git)
4.   iot 类的在线云沙箱，[bugprove](https://bugprove.com/)
5.   固件下载网址，[drivers.softpedia](https://drivers.softpedia.com)
6.   网络测绘引擎（1），[shodan](https://shodan.io)
7.   网络测绘引擎（2），[fofa](https://en.fofa.info/)

## binary-tool

1.  static
    1.  **ida**，[IDA Pro](https://hex-rays.com/ida-pro/)；对二进制文件进行反汇编和静态分析，提供直观的图形界面和强大的反汇编功能，用于理解程序的结构和逻辑
    2.  **ghidra**，[NationalSecurityAgency/ghidra](https://github.com/NationalSecurityAgency/ghidra.git)；ida 平替
    3.  **jadx**，[skylot/jadx](https://github.com/skylot/jadx.git)；用于将 Android 应用程序的 DEX 文件反编译成可读的 Java 源代码，有助于理解和修改 Android 应用程序
    4.  **dnspy**，[dnSpy/dnSpy](https://github.com/dnSpy/dnSpy.git)；用于 .NET 程序的反编译器和调试器，允许逆向工程 .NET 应用程序，查看和修改源代码
    5.  **apktool**，[iBotPeaches/Apktool](https://github.com/iBotPeaches/Apktool.git)；反编译和重新编译 apk 文件，查看 java smail 源码
    6.  **jd-gui**，[java-decompiler/jd-gui](https://github.com/java-decompiler/jd-gui.git)；可以看 jar 包的源码，`apt install jd-gui`
    7.  **dex2jar**，[pxb1988/dex2jar](https://github.com/pxb1988/dex2jar.git)；将 dex 文件转为 jar 包，`apt install dex2jar`
2.  dynamic
    1.  **gdb**，[official](https://www.sourceware.org/gdb/)；用于调试程序，支持多种编程语言，可用于跟踪程序的执行过程、检查内存和寄存器状态等，一般不会只使用 gdb，更多要配合插件
    2.  **ollydbg**，[OllyDbg](https://www.ollydbg.de/)；Windows，动态调试器，用于分析和修改程序的运行时行为，主要用于反汇编和跟踪
    3.  **x64dbg/x32dbg**，[x64dbg/x64dbg](https://github.com/x64dbg/x64dbg.git)；开源，支持多种指令集，和 ollydbg 像
    4.  **windbg**，[official](http://www.windbg.org/)；分析 Windows 系统和应用程序
    5.  **cheat engine**，[official](https://www.cheatengine.org/)；改游戏挺常用的
    6.  **frida**，[frida/frida](https://github.com/frida/frida.git)；动态插桩
3.  other
    1.  **z3**，[Z3Prover/z3](https://github.com/Z3Prover/z3.git)；用于自动推理和解决数学问题的定理证明器，可用于逆向工程中的符号执行、模型检测等约束求解问题
    2.  **angr**，[angr/angr](https://github.com/angr/angr.git)；开源的二进制分析框架，用于自动化逆向工程任务，包括符号执行、路径探索和程序分析
    3.  **binwalk**，[ReFirmLabs/binwalk](https://github.com/ReFirmLabs/binwalk.git)；固件提取工具
    4.  **easy apk tool**，[APK Easy Tool v1.59.2 - Windows 下使用的安卓逆向工具](https://www.52pojie.cn/thread-1411747-1-1.html)；各种安卓逆向工具的封装，有民间汉化版本，一键反编译、回编译、签名
    5.  **MT 修改器**，[Android 平台文件管理 & 逆向修改神器](https://mt2.cn/)；安卓平台的，能很大程度地看 apk 的各种信息并修改

# 02 iot-environment-configuration

简要配置一下固件分析环境，个人使用的是 Kali in wsl2，属于是残疾版，很多常用的命令都没有自带，除此之外还需要配置网络，相关安装配置可以参考我的另一篇文章 [app | windows-terminal](https://www.majo.im/index.php/wkyuu/36.html) 中的 wsl 小标题下的内容

## qemu

debian 系使用 apt 安装：`apt-get install qemu-user-static qemu-system uml-utilities bridge-utils`

### usage

有两种使用 qemu 运行应用的模式，user mode 和 system mode，前者模拟单个应用，后者模拟一整个 os

1.   user mode；需要使用 `chroot` 进行环境切换，在新的环境中运行一个 qemu-mips 模拟器来执行指定的二进制文件（例如 busybox）：

     ```bash
     # 将 qemu-mips-static 复制到 提取出的固件的根目录下
     $ sudo cp $(which qemu-mips-static) squashfs-root
     $ cd squashfs-root
     
     # 修改 root 并执行固件自带的 ash shell
     $ sudo chroot . ./qemu-mips-static bin/busybox ash
     ```

2.   system mode；主要思路为使用 [现成的](https://people.debian.org/~aurel32/qemu/mips/) kernel 和 img 创建空环境，然后将解压出来的固件挂载上去，方便查看各类性能指标、内存监控、远程调试等

     1.   为 qemu 配置网络，方便后续 gdb attach 和网络测试等行为；主要思路为，先在宿主机创建虚拟网桥 br0，然后为该虚拟网桥添加接口 tap0，最后在 qemu 启动时使用该接口，则 qemu 中模拟的系统就可以通过 tap0 与宿主机通信

          1.   传统派（推荐），wsl user 可用，单次开机可用，重启消失，可以写脚本自动执行

               1.   宿主机创建网桥；注意，不同的分发版本使用的网卡名不同，以下以 ens33 为例，其他的有 eth0 之类的，具体情况具体分析

                    ```bash
                    $ sudo brctl addbr br0
                    $ sudo ip addr add 192.168.0.1/24 dev br0
                    $ sudo ip link set br0 up
                    ```
     
               2.   宿主机创建 tap0 接口；
     
                    ```bash
                    $ sudo ip tuntap add mode tap dev tap0
                    $ sudo ip addr add 192.168.0.2/24 dev tap0
                    $ sudo ip link set tap0 up
                    $ sudo brctl addif br0 tap0
                    $ sudo brctl show # 可以看到网桥 br0 拥有了 tap0 接口
                    ```

                    此时输入 `ifconfig` 应当至少可以看到 tap0、br0、lo、ens33 几个网络接口；此时记住 br0 的 inet 地址，这里以 `192.168.0.1` 为例

               3.   宿主机启动 qemu system mode，并指定其使用 tap0 用于与宿主机通信：
     
                    ```bash
                    $ sudo qemu-system-mips \
                    -M malta \	# 指定使用的 mips 开发板模型, 输入 -M ? 可以查看其他类型
                    -kernel vmlinux-3.2.0-4-4kc-malta \	# 指定要使用的 mips 内核
                    -append "root=/dev/sda1 console=tty0" \		# 内核启动命令, 这里指定了 qemu 启动时挂载在模拟环境硬盘中哪个位置, 指定使用的控制台
                    -net nic \	# 指定使用默认网络接口配置
                    -net tap,ifname=tap0,script=no,downscript=no \	# 创建和配置一个基于 tap 设备的网络设备, 设备名为 tap0, 设备名必须与创建的 tap 接口相同
                    -hda debian_squeeze_mips_standard.qcow2	# 指定目标的镜像文件目录
                    
                    # 完整指令如下
                    $ sudo qemu-system-mips -M malta -kernel vmlinux-3.2.0-4-4kc-malta -append "root=/dev/sda1 console=tty0" -net nic -net tap,ifname=tap0,script=no,downscript=no -hda debian_squeeze_mips_standard.qcow2
                    ```

               4.   最后在虚拟环境中配置 ip：`sudo ifconfig eth0 192.168.0.3/24 up` 或者 `sudo ip addr add 192.168.0.3/24 dev eth0`，这里的 ip 地址参考上文 ens33 的 ip，要求同一子网

               5.   如果要连通外网，需要配置路由和 dns 服务器

                    目前已知宿主机 br0 为 `192.168.0.1`，tap0 为 `192.168.0.2`，qemu 系统为 `192.168.0.3`；br0 可以上网

                    1.   `ip route add 192.168.9.1 via 192.168.0.1`（这里的 `192.168.9.1` 是网关）

          2.   维新派

               1.   使用 docker 提供的网桥直接通信，首先安装 docker：`sudo apt-get install docker.io`
     
               2.   启动 docker：`sudo systemctl start docker.service`，为 docker 添加开机自启动：`sudo systemctl enable docker.service`；注意，使用 wsl 时，开机自启 docker 容易导致通过 terminal 启动 wsl 时增加冗余，私以为而这种行为明显不符合 wsl 即开即用的逻辑
     
               3.   输入 `ifconfig` 可以至少看到 lo、eth0、docker0 几个接口，记住 docker0 的 inet 地址，这里以 `172.17.0.1` 为例
     
               4.   创建 tap0 设备，并连接到 docker0：
     
                    ```bash
                    $ sudo ip tuntap add mode tap dev tap0
                    $ sudo ip addr add 172.17.0.2/16 dev tap0
                    $ sudo ip link set tap0 up
                    $ brctl addif docker0 tap0
                    $ brctl show	# 此时可以看到 docker0 有了 tap0 接口
                    ```
     
               5.   宿主机启动 qemu system mode，指令与上一步骤相同
     
               6.   在 qemu 中，需要手动配置网络信息：
     
                    ```bash
                    $ ifconfig eth0 172.17.0.3/16	# 如果地址冲突了就换一个
                    $ ip route add default gw 172.17.0.1	# 配置默认网关为 docker0, 可以由此连通外网
                    $ echo "nameserver 172.17.0.1" > /etc/resolv.conf	# 配置 dns
                    ```
     
          3.   永久修改网络配置，成功率较低，wsl 用户不可用，不推荐；主要思路是在 `/etc/network/interfaces` 中配置好 ens33 和 br0（网桥），用 br0 取代 ens33，然后创建 tap0 连接到 br0，再使用 tap0 为 qemu 提供网络，由于涉及到 `ifdown eth0` 和 `ifup br0`，而 wsl 的 dhcp 不会自动为 br0 提供 ip，就会导致 wsl 无 ip 可用，直接无网络。因此，私以为使用前两种生命周期为单次开机的方法更值得使用。
     
     2.   挂载提取出来的固件
     
          1.   按照上文配置好网络并启动 qemu 模拟环境，通过 `ping 172.17.0.2` 可以 ping 通；由于在一些老版本的镜像中 ssh 版本较低，而新版本的 ssh 默认禁用了 `ssh-dss` 算法，可以通过 `ssh -o HostKeyAlgorithms=+ssh-dss -o PubkeyAcceptedKeyTypes=+ssh-dss  user@172.17.0.2` 指定新增算法选项来解决，如果想一劳永逸，还可以修改配置文件 `~/.ssh/config`（没有就创建）：
     
               ```ini
               # 方法 1, 对特定 ip 添加配置
               Host 172.17.0.2
               HostKeyAlgorithms +ssh-dss
               PubkeyAcceptedKeyTypes +ssh-dss
               
               # 方法 2, 对所有 ip 都添加配置
               Host *
               HostKeyAlgorithms +ssh-dss
               PubkeyAcceptedKeyTypes +ssh-dss
               ```
     
          2.    将提取出来的系统传输到 qemu 中
     
                1.   首先需要将整个 squashfs-root 文件夹打包成 tar：`tar -cvf sqfs.tar squashfs-root`
                2.   传输到 qemu 里：`scp -r sqfs.tar root@172.17.0.2:/root/`（scp 需要用到 ssh，遇到 ssh-dss 算法问题就参考上一步添加对应选项）
                3.   在 qemu 中解压：`tar -xvf sqfs.tar`
                4.   运行固件的 shell：`cd /root/squashfs-root`，`chroot . bin/ash`
                5.   按照上述步骤制作完固件的虚拟环境后，可以将启动时指定的 `debian_squeeze_mips_standard.qcow2`，当然，后续只需要 cp 一份该文件就能分发着去用了，不同的 iot 固件需要更换不同 kernel 和 img，可以自己编译也可以去下载，各凭本事

### imgs

index here：[aurel32/qemu](https://people.debian.org/~aurel32/qemu/)；squeeze 对应 debian 6.x，wheezy 对应 debian 7.x，尽可能选择较新的；

```shell
#/bin/bash

workdir=/home/app/qemu-imgs

download() {
    local url=$1
    local output_file=$2
    local dir=$workdir/$3
    if [ ! -f "$dir/$output_file" ]; then
        wget -e use_proxy=yes -e https_proxy=http://172.28.240.1:7890 -O $dir/$output_file $url
    fi
}

# i386
download https://people.debian.org/~aurel32/qemu/i386/debian_wheezy_i386_standard.qcow2 debian-i386-wheezy-standard.qcow2 i386

# amd64
download https://people.debian.org/~aurel32/qemu/amd64/debian_wheezy_amd64_standard.qcow2 debian-amd64-wheezy-standard.qcow2 amd64

# mips
download https://people.debian.org/~aurel32/qemu/mips/debian_wheezy_mips_standard.qcow2 debian-mips-wheezy-standard.qcow2 mips
download https://people.debian.org/~aurel32/qemu/mips/vmlinux-2.6.32-5-4kc-malta vmlinux-2.6.32-5-4kc-malta mips
download https://people.debian.org/~aurel32/qemu/mips/vmlinux-2.6.32-5-5kc-malta vmlinux-2.6.32-5-5kc-malta mips
download https://people.debian.org/~aurel32/qemu/mips/vmlinux-3.2.0-4-4kc-malta vmlinux-3.2.0-4-4kc-malta mips
download https://people.debian.org/~aurel32/qemu/mips/vmlinux-3.2.0-4-5kc-malta vmlinux-3.2.0-4-5kc-malta mips

# mipsel
download https://people.debian.org/~aurel32/qemu/mipsel/debian_wheezy_mipsel_standard.qcow2 debian-mipsel-wheezy-standard.qcow2 mipsel
download https://people.debian.org/~aurel32/qemu/mipsel/vmlinux-2.6.32-5-4kc-malta vmlinux-2.6.32-5-4kc-malta mipsel
download https://people.debian.org/~aurel32/qemu/mipsel/vmlinux-2.6.32-5-5kc-malta vmlinux-2.6.32-5-5kc-malta mipsel
download https://people.debian.org/~aurel32/qemu/mipsel/vmlinux-3.2.0-4-4kc-malta vmlinux-3.2.0-4-4kc-malta mipsel
download https://people.debian.org/~aurel32/qemu/mipsel/vmlinux-3.2.0-4-5kc-malta vmlinux-3.2.0-4-5kc-malta mipsel

# armel 较老, armhf 更新(armv7+)
download https://people.debian.org/~aurel32/qemu/armel/debian_wheezy_armel_standard.qcow2 debian-armel-wheezy-standard.qcow2 armel
download https://people.debian.org/~aurel32/qemu/armel/initrd.img-2.6.32-5-versatile initrd.img-2.6.32-5-versatile armel
download https://people.debian.org/~aurel32/qemu/armel/initrd.img-3.2.0-4-versatile initrd.img-3.2.0-4-versatile armel
download https://people.debian.org/~aurel32/qemu/armel/vmlinuz-2.6.32-5-versatile vmlinuz-2.6.32-5-versatile armel
download https://people.debian.org/~aurel32/qemu/armel/vmlinuz-3.2.0-4-versatile vmlinuz-3.2.0-4-versatile armel

download https://people.debian.org/~aurel32/qemu/armhf/debian_wheezy_armhf_standard.qcow2 debian-armhf-wheezy-standard.qcow2 armhf
download https://people.debian.org/~aurel32/qemu/armhf/initrd.img-3.2.0-4-vexpress initrd.img-3.2.0-4-vexpress armhf
download https://people.debian.org/~aurel32/qemu/armhf/vmlinuz-3.2.0-4-vexpress vmlinuz-3.2.0-4-vexpress armhf
```

### other architecture

mips64，注意是 5kc

```bash
sudo qemu-system-mips64 \
-M malta \
-append "root=/dev/sda1 console=tty0" \
-net nic \
-net tap,ifname=tap0,script=no,downscript=no \
-kernel vmlinux-3.2.0-4-5kc-malta \
-hda debian-mips-wheezy-standard.qcow2
```

mipsel

```bash
sudo qemu-system-mipsel \
-M malta \
-append "root=/dev/sda1 console=tty0" \
-net nic \
-net tap,ifname=tap0,script=no,downscript=no \
-kernel vmlinux-3.2.0-4-4kc-malta \
-hda debian-mipsel-wheezy-standard.qcow2
```

mips64el

```bash
sudo qemu-system-mips64el \
-M malta \
-append "root=/dev/sda1 console=tty0" \
-net nic \
-net tap,ifname=tap0,script=no,downscript=no \
-kernel vmlinux-3.2.0-4-5kc-malta \
-hda debian-mipsel-wheezy-standard.qcow2
```

armel

```bash
sudo qemu-system-armel \
-M versatileab \
-append "root=/dev/sda1 console=tty0" \
-net nic \
-net tap,ifname=tap0,script=no,downscript=no \
-kernel initrd.img-3.2.0-4-versatile \
-hda debian-armel-wheezy-standard.qcow2
```

armhf，arm 架构倾向于 sd 卡等小型存储，因此用的 `-drive if=sd,debian-armhf-wheezy-standard.qcow2`

```bash
sudo qemu-system-armhf \
-M vexpress-a9 \
-append "root=/dev/sda1 console=tty0" \
-net nic \
-net tap,ifname=tap0,script=no,downscript=no \
-kernel vmlinuz-3.2.0-4-vexpress \
-initrd initrd.img-3.2.0-4-vexpress \
-drive if=sd,debian-armhf-wheezy-standard.qcow2
```

## binwalk

1.   包管理器安装（推荐）：`sudo apt-get install binwalk`
2.   或者源码安装：
     1.   `git clone https://github.com/ReFirmLabs/binwalk.git`
     2.   `cd binwalk`
     3.   `sudo ./deps.sh`
     4.   `sudo python ./setup.py install`
3.   其他依赖：`sudo apt install unsquashfs sasquatch`

## firmadyne

get src here：[firmadyne/firmadyne](https://github.com/firmadyne/firmadyne.git)；这边直接使用脚本一把梭，[attify/firmware-analysis-toolkit](https://github.com/attify/firmware-analysis-toolkit.git)

### installation

1.   `git clone https://github.com/attify/firmware-analysis-toolkit fat`

2.   `cd fat`，`chmod +x ./setup.sh`

3.   如果是 kali 用户，等待报错就行，因为会安装 binwalk，但是 binwalk 的安装脚本 `binwalk/deps.sh` 中有一项 `qt5base-dev`，需要将其修改成 `qtbase5-dev`，然后回到 `./setup.sh` 中注释掉第 13 行的 binwalk.git 的获取，然后重新运行脚本完成剩下的安装

4.   还是 binwalk 的问题，会自动 pip 安装 package，速度十分慢，可以到 `binwalk/deps.sh` 的 126 行左右，为 pip 命令添加 `--proxy=http://127.0.0.1:7890`

5.   firmadyne 的问题，当开始下载 firmadyne 的部分时，需要到 `firmadyne/download.sh` 中第 6 行左右的 wget 处，修改成 `wget -e https_proxy=http://127.0.0.1:7890 -N --continue -P./binaries/ $*`；同时原 `setup.sh` 后半部分也有 wget 指令，都要手动配置代理

6.   期间还可能遇到各种 fatal，基本逻辑就是要去看 shell 脚本对应的地方修改，例如多次使用 git clone，但是中断再运行后就会因为 git clone 剩下来的文件夹没删掉导致中断，手动删掉即可；还有不需要重复安装一些应用，手动注释掉关键命令即可

7.   分别输入以下命令看是否有回显来确认是否完成安装：`sasquatch`、`yaffshiv`、`jefferson`

8.   安装完成后，到 `fat.config` 中修改默认内容，参考：

     ```ini
     [DEFAULT]
     sudo_password=root
     firmadyne_path=/home/app/fat/firmadyne
     ```

### usage

安装完成后，直接通过 `/home/app/fat/fat.py firmware.bin` 来解析固件

## frida

get src here：[frida/frida](https://github.com/frida/frida.git)；Android、Linux、Windows 等平台上的动态插桩工具，拦截应用程序的函数调用、监视数据传输以及修改应用程序的行为，从而进行各种各样的分析和测试操作；`pip install frida-tools`，安装完成后将其添加到环境变量：`export PATH=$PATH:/home/user/.local/bin`，也可以写到 `~/.bashrc` 中

要解析固件时，需要到 [release](https://github.com/frida/frida/releases/) 中下载 frida-server 对应的 platform 和 structure；例如要解析是 mips linux 固件，则下载 `frida-server-x.x.x-linux-mips.xz`，解压得到 `frida-server` 将其复制到固件中，后台运行之 `sudo /tmp/frida-server &`（需要 root 权限）

具体使用方式参考另一篇文章 [app | frida-handbook]()；

## reference

1.   配置固件分析环境（1），[一步一步PWN路由器之环境搭建](https://xz.aliyun.com/t/1508)
2.   配置固件分析环境（2），[路由器固件模拟环境搭建](https://xz.aliyun.com/t/5697)
3.   配置固件分析环境（3），[固件模拟调试环境搭建](http://zeroisone.cc/2018/03/20/固件模拟调试环境搭建)
4.   配置 qemu 环境（1），[QEMU Intro and Network Configuration](https://tyeyeah.github.io/2020/01/11/2020-01-11-QEMU-Intro-and-Network-Configuration/)
5.   配置 qemu 环境（2），[Qemu 模拟环境](https://ctf-wiki.org/pwn/linux/kernel-mode/environment/qemu-emulate/)
6.   配置 qemu 环境（3），[IoT（七）通过qemu调试IoT固件和程序](https://www.gandalf.site/2018/12/iotqemuiot.html)

# 04 router-device-introduction

写这些理论的东西感觉不如直接上手样本来得实在，慢慢补充吧

## introduction

路由器，是比较容易接触到的智能设备，路由器的挖掘有：

-   从路由器的 web 管理界面下手，从登录界面开始就找什么弱口令、注入之类的，进去后还有命令执行、越权之类的，比起要用到逆向的知识，这更像是渗透或者 web 手做的事情
-   通过 binwalk 对 flash rom 处理提取出固件，再对固件展开逆向分析

## component

简单的路由器组成主要是 cpu、ram、flash rom、uart / jtag 串口

-   cpu：在一些嵌入式微控制器里也叫 MCU（Microcontroller Unit，微控制单元）
-   uart：Universal Asynchronous Receiver/Transmitter，通用异步收发器/发送器。常见的串行通信接口标准，用于在计算机系统和外部设备之间进行数据传输，通过 uart 调试口，开发人员可以发送和接受调试信息、日志、配置等，可以使用 SecureCRT 来获取和分析串口的信息
-   Flash Rom：用于 iot 设备存储文件系统、内核信息、boot 信息、配置信息。不同的 flash rom 有不同的存储结构，需要主动识别和区分这些 rom，最常见的方式是通过芯片上厂商的首字母缩写、不规则数字等信息区分 rom，然后使用编程器软件提取信息，不同的厂商可能会有不同的编程器软件

## firmware

固件（firmware）就是存储于设备的 flash 芯片中，一般担任着一个数码产品最基础、底层的工作

获取固件的方法有以下方式：

-   从官网技术支持获取固件升级包；从第三方网站获取固件包
-   本地 OTA（over the air，无线传输方式升级）升级时进行抓包；也可以破解掉用于升级的软件，获取其通讯算法，直接下载
-   通过编程器、binwalk 直接从路由器的 flash rom 中获取
-   获取硬件系统的系统权限后，使用 tar、dd 等指令提取固件
-   ......

## boot

boot 引导进入系统，修改 boot 启动脚本进入有密码保护的登陆系统的思路（也可以用于其他 iot 设备的引导程序）：

1.   进入 uboot 后，通过 `tftpboot ${loadaddr} filesystem.img` 来引导魔改过的系统，简单文件传输协议（Trivial File Transfer Protocol，TFTP），在系统运行后再提取固件
2.   使用第三方 Linux 挂载 rom，然后修改 `passwd`，`shadow`，`shadow-` 文件中的 root 相关内容
3.   对于使用 x86 系统的固件，使用类似 WinPE 系统的方式，挂载一个 u 盘版本的 LinuxPE，然后提取固件
4.   类似 Linux 系统忘记密码的解决方案，在启动选项中添加 `single` 或 `init=/bin/sh`，即进入单用户模式，然后修改密码
5.   让系统在启动时执行删除密码的命令，`init=passwd root -d`，一般删除后，使用 root 登录将不再需要密码

## reference

1.   [智能设备漏洞挖掘中几个突破点](https://bbs.kanxue.com/thread-230095.html)