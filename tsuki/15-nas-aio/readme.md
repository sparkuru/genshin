# NAS | ALL IN ONE

| 组件           | 产品                                                          | 价格，渠道       | 备注 |
| ---------------- | --------------------------------------------------------------- | ------------------ | ------ |
| cpu            | AMD；R9 7950x 盒装（板 u 套装）                               | 4619，pdd        | [jd](https://item.jd.com/100039537667.html)     |
| 主板           | 技嘉；电竞雕 WIFI B650M AORUS PRO AX                          | 0                | [jd](https://item.jd.com/100042368439.html)     |
|                |                                                               |                  |      |
| 显卡           | 盈通；樱瞳花嫁 4070 super oc 12g                              | 4469，tb         |      |
| 内存           | 金百达；银爵，32GB x 2 套装，DDR5 6400 C32，海力士 A-die 颗粒 | 1284，pdd        | [jd](https://item.jd.com/100046655844.html)     |
| 固态存储       | 致态；Tiplus 7100，1t，长江原厂颗粒                           | 492，pdd         | [jd](https://item.jd.com/10079976018181.html)     |
|                | 梵想；铝片高速固态 QLC，PCIe 4.0 7200MB/s，2t                 | 806，pdd         |      |
| 电源           | 海韵；focus gx650w，全日系金牌全模，14 cm                     | 596，jd          | [jd](https://item.jd.com/100007186422.html)     |
|                |                                                               |                  |      |
| 散热（cpu）    | COOLLEO 酷里奥；倚天 P60T V3，黑色性能版，双塔 6 热管         | 261，pdd         | [jd](https://item.jd.com/10099761123199.html)     |
| 散热，机箱风扇 | 伊科贝拉；玄冥普 1800 转，FBD（无光）黑色正叶                 | 17 x 3 = 51，pdd | [pdd](https://mobile.yangkeduo.com/goods1.html?goods_id=593177321830&page_from=23)     |
|                |                                                               |                  |      |
| 机箱           | 未知玩家；X200 手提小机箱 MATX ，jojo 定制图                  | 268，pdd         | [jd](https://item.jd.com/100070489290.html)     |
|                |                                                               | 12846            |      |
|                |                                                               |                  |      |
| ~~机械存储~~               | ~~西部数据；WUH721414ALE6L4 14T 7200 SATA3 企业级氦气硬盘~~                                                              | ~~1298，tb~~                 | [tb](https://item.taobao.com/item.htm?abbucket=17&id=624523855339&ns=1)     |
|                |                                                               | ~~12846 + 1298 = 14135~~                 |      |
|                |                                                               |                  |      |
| 其他耗材       | 扎带 宽 2.5mm 长 15cm 100 条                                  | 5.9，pdd         |      |
|                | miku chibi 角色贴纸 65 张不重复                               | 4.9，pdd         |      |
|                | 像素 miku 机箱贴纸 53 张不重复                                | 6，pdd           |      |
|                | 螺丝刀套装，合金                                              | 5.8，pdd         |      |

![更新后](https://md.majo.im/uploads/c2b03e1c-3ff9-499b-a4c0-a65a78f6b819.png)

## network

网络拓扑信息如下，需要到 192.168.9.1 路由器里配置相关静态 ip 地址

| ip   | dev             |
| ------ | ----------------- |
| 9.1  | main router     |
|      |                 |
| 9.2  | matx            |
| 9.3  | pve             |
| 9.4  | pve / wrt / wan |
| 9.5  | pve / wrt / lan |
| 9.6  | pve / linux-nas |
|      |                 |
| 9.7  |                 |
| 9.8  | phone           |
| 9.9  | ipad            |
| 9.10 | ppkvm           |

![网络拓扑](https://md.majo.im/uploads/abcf7564-d819-444c-b819-927e8cde35b5.png)

## pve

### 环境介绍

主路由器小米 ax6000（wifi6）是 192.168.9.1（从光猫桥接进来拨号，有公网 ipv4、ipv6）、主板板载 2.5g 网口（enp1s0）、8 块 hdd 机械硬盘、bcm 5720 2 千兆口 pcie 网卡（enp2s0、enp3s0）、sata 3.0 pcie 拓展卡、整机运存是 64G，规划如下：

1. 装一个 pve 作为主系统（），通过 enp2s0 管理 pve（192.168.9.3）
2. 使用 pve 自带的 ZFS 系统管理硬盘，其中 7 块 4t 组  RAIDZ1，1 块 6t 单独组，使用 alist 进行磁盘的共享
3. 虚拟机装一个 immortalwrt 做旁路由（2c2g）

    1. 将 enp3s0 直通给旁路由（192.168.9.4，作 WAN 口，设置网关为 192.168.9.1）；
    2. pve 再添加一个 VirtIO 给旁路由（192.168.9.5，做 LAN 口，子网的网关为 192.168.9.5）；
    3. 按照以上设计，局域网内（192.168.9.0/24）设备在上网时有两种选择：

        1. 设置 gateway 为 192.168.9.1，则直接走主路由连接互联网
        2. 设置 gateway 为 192.168.9.5，则其路由为：*局域网设备 -&gt; pve -&gt; VirtIO -&gt; wrt lan -&gt; vSwitch -&gt; pcie -&gt; wrt wan -&gt; enp3s0 -&gt; 主路由*

        在主路由和 wrt 上，都把局域网内常用设备的 ip 和 mac 进行绑定，即切换网关的时候都使用同一个 ip

        ![ff82e1c87be68b8afd757ebfd4022fb4](assets/ff82e1c87be68b8afd757ebfd4022fb4-20250305005152-ioq42gx.png)
    4. 当设备加入局域网时，只需要将网关切换成 192.168.9.5，即可实现旁路由上网；若不需要旁路由，则会默认使用主路由 192.168.9.1 网关
4. ~~虚拟机装一个 ubuntu server lts 作为主要的 nas 机~~

### pve 基本设置

1. 修改 pcie 设备的时候，可能会导致网卡的装载顺序发生变化，可能会出现因为 ip 不对的问题无法访问 pve 的 web 界面，需要手动修改网络信息（需要连接到 pve 系统的 shell，例如通过图形界面）：

    1. `ip a` 查看网卡信息，这里是一个网口 `enp5s0` 和一个 wlan 网口 `wlp4s0`
    2. 然后修改网卡信息：`nano /etc/network/interfaces`

        ```ini
        auto lo
        iface lo inet loopback

        iface enp5s0 inet manual
        iface wlp4s0 inet manual

        auto vmbr0
        iface vmbr0 inet static
                address 192.168.9.3/24
                gateway 192.168.9.1
                bridge-ports enp5s0
                bridge-stp off
                bridge-fd 0

        source /etc/network/interfaces.d/*
        ```
    3. 重启网络：`systemctl restart networking.service`
2. 在 pve 安装常用的工具

    1. 先配置 <span data-type="text" style="font-size: 13.6px; font-variant-ligatures: none; white-space-collapse: preserve; background-color: rgba(27, 31, 35, 0.05);"> </span>，使用 ustc 的 debian 源，参考如下

        ```ini
        deb http://mirrors.ustc.edu.cn/debian bookworm main contrib non-free non-free-firmware
        deb http://mirrors.ustc.edu.cn/debian bookworm-updates main contrib non-free non-free-firmware
        ```

        1. 同时可以将 `/etc/apt/sources.list.d/pve-enterprise.list` 中的内容注释掉（如果没有订阅企业版 pve 的话）
        2. 然后配置 ustc 的 pve 源：`echo "deb https://mirrors.ustc.edu.cn/proxmox/debian/pve bookworm pve-no-subscription" > /etc/apt/sources.list.d/pve-no-subscription.list`
        3. ustc 的 ceph 源：`source /etc/os-release`，`echo "deb https://mirrors.ustc.edu.cn/proxmox/debian/ceph-$(ceph -v | grep ceph | awk '{print $(NF-1)}') $VERSION_CODENAME no-subscription" > /etc/apt/sources.list.d/ceph.list`
        4. 替换 pve 的 gpg 验证：`cp /etc/apt/trusted.gpg.d/proxmox-release-bookworm.gpg /etc/apt/trusted.gpg.d/proxmox-release-bookworm.gpg.backup`，`wget http://mirrors.ustc.edu.cn/proxmox/debian/proxmox-release-bookworm.gpg -O /etc/apt/trusted.gpg.d/proxmox-release-bookworm.gpg`
    2. 更新 `apt update`
    3. 安装工具 `apt install sudo zsh vim git iperf3 net-tools iftop openvpn ntfs-3g samba`
3. 配置 pve 的访问控制权限，这里是设计成分角色的方案：root 用户可以进行所有操作，而平常使用一个普通用户，只进行简单的虚拟机开关机、虚拟机创建销毁、状态查看等

    1. 定位到 *数据中心 - 权限 - 群组，* 在这里创建一个名为 wheel 的群组
    2. 定位到 *数据中心 - 权限 - 角色*，在这里创建一个角色名为 wheel，特权可以多选，建议如下（参考 [PVE 权限管理](https://www.cnblogs.com/varden/p/15246180.html)，只列出了必须的，未列出的自行检索）

        | 特权名称          | 作用                     | 建议 |
        | ------------------- | -------------------------- | ------ |
        | Datastore.*       | 磁盘管理相关             | 全选 |
        |                   |                          |      |
        | SDN.*             | 网络相关                 | 全选 |
        |                   |                          |      |
        | Sys.AccessNetwork | 可以用于配置虚拟机的网络 | 选   |
        | Sys.Audit         | 审计                     | 选   |
        | Sys.PowerMgmt     | pve 开关机               | 选   |
        |                   |                          |      |
        | VM.*              | 虚拟机相关               | 全选 |
    3. 创建完成后，到 *数据中心 - 权限 - 用户*，添加一个新用户：领域选择 Proxmox VE authentication，群组选择上面创建的
    4. 定位到 *数据中心 - 权限*，选择 *添加 - 群组权限*，路径为 `/`，群组为 `wheel`，角色选择刚才创建的 `wheel`，创建
    5. 此时退出再登录 pve，账密为刚才创建的，领域选择 `Proxmox VE authentication server`，登陆即可
4. 其他设置

    1. PVE 上传的 iso 镜像位置为：`/var/lib/vz/template/iso/`
    2. pve 的存储中，有个 `local` 和 `local-lvm`

        1. `local`，就是 PVE 的根目录，同时还可以用于存储 iso 镜像
        2. `local-lvm`，专门特化用于存储虚拟镜像，也就是 pve 的节点存放的地方，由于在初始化时一般没有挂载其他盘，则 pve 默认将当前的盘分开成两种系统，当新建虚拟机时，一般放入到这个逻辑卷中

        如果像我一样，将 pve 直接作为主系统，那么其实可以 local 和 local-lvm 容量对半开着去做，有两种方法，一是直接将 local-lvm 部分容量挂载到 pve-root 下（对应 local），第二种是直接调整这两个部分的大小：

        ```bash
        # 首先删除掉 local-lvm 分区
        $ lvremove pve/data
        Removing pool pve/data will remove 1 dependent volume(s). Proceed? [y/n]: y
        Do you really want to remove active logical volume pve/vm-100-disk-0? [y/n]: y
          Logical volume "vm-100-disk-0" successfully removed.
        Do you really want to remove active logical volume pve/data? [y/n]: y
          Logical volume "data" successfully removed.

        # 此时可以看到还剩多少容量
        $ vgdisplay pve
          --- Volume group ---
          VG Name               pve
          System ID
          Format                lvm2
          Metadata Areas        1
          Metadata Sequence No  23
          VG Access             read/write
          VG Status             resizable
          MAX LV                0
          Cur LV                2
          Open LV               2
          Max PV                0
          Cur PV                1
          Act PV                1
          VG Size               <930.51 GiB
          PE Size               4.00 MiB
          Total PE              238210
          Alloc PE / Size       26624 / 104.00 GiB
          Free  PE / Size       211586 / <826.51 GiB
          VG UUID               qIsK3c-SnNP-hiQ8-7p63-Au2Y-x3KT-Q7UZkh

        # 开始为 local 增加容量
        $ lvextend -L +416G /dev/mapper/pve-root
          Size of logical volume pve/root changed from 96.00 GiB (24576 extents) to 512.00 GiB (131072 extents).
          Logical volume pve/root successfully resized.

        # 应用变更
        $ resize2fs /dev/mapper/pve-root
        resize2fs 1.47.0 (5-Feb-2023)
        Filesystem at /dev/mapper/pve-root is mounted on /; on-line resizing required
        old_desc_blocks = 12, new_desc_blocks = 64
        The filesystem on /dev/mapper/pve-root is now 134217728 (4k) blocks long.

        ```

        扩容完，还得把 local-lvm 给加回来：

        ```bash
        # 查看剩余空间
        $ vgs pve
          VG  #PV #LV #SN Attr   VSize    VFree
          pve   1   2   0 wz--n- <930.51g <410.51g

        # 创建 local-lvm
        $ lvcreate -L 400G -n data pve
          Logical volume "data" created.

        # 创建 thin-poll 池
        $ lvconvert --type thin-pool pve/data
          Thin pool volume with chunk size 256.00 KiB can address at most 63.50 TiB of data.
          WARNING: Converting pve/data to thin pool's data volume with metadata wiping.
          THIS WILL DESTROY CONTENT OF LOGICAL VOLUME (filesystem etc.)
        Do you really want to convert pve/data? [y/n]: y
          Converted pve/data to thin pool.

        ```

        然后回 *pve - 数据中心 - 存储 - 添加* 将 local-lvm 加回来即可
    3. 为 pve 启动 wake on lan，修改 `/etc/network/interfaces` 文件，支持网卡 wol，核心逻辑是命令 `/usr/sbin/ethtool -s <interface-name> wol g`：

        ```ini
        auto lo
        iface lo inet loopback

        iface enp4s0f0 inet manual
          post-up /usr/sbin/ethtool -s enp4s0f0 wol g
        iface wlp6s0 inet manual
        iface enp7s0 inet manual
          post-up /usr/sbin/ethtool -s enp7s0 wol g

        # 和正常配置一样
        ...
        ```
    4.

## ZFS 文件系统

ZFS 使用 设备 id、事务 id 等机制确保它不依赖于磁盘的物理插槽顺序，ZFS 池可以在磁盘顺序完全不同的情况下成功导入机械硬盘（前提是硬盘没有损坏）。除了前文直接挂载机械硬盘，然后让虚拟机管理软 raid 的情况外，还可以在 pve 上直接配置 ZFS 系统来管理这些机械硬盘

类似 raid 阵列，zfs 也有以下的阵列解决方案

| 类型    | 磁盘利用率           | 原理                                                                                       | 缺点                                             |
| --------- | ---------------------- | -------------------------------------------------------------------------------------------- | -------------------------------------------------- |
| Stripe  | 100%                 | 类似 RAID 0，数据被分散存储在所有磁盘上，提供最大存储空间和性能                            | 无冗余，一块盘故障会导致所有数据丢失             |
| Mirror  | 50% (双向镜像)       | 类似 RAID 1，数据被完全复制到每个镜像盘，可支持多路镜像(2 路、3 路等)                      | 磁盘利用率低，n 块盘只能使用 1 块的容量          |
| RAIDZ1  | n-1 块盘的容量       | 类似 RAID 5，单奇偶校验，可承受 1 块盘故障。数据以可变大小的条带分布，避免 RAID 5 写入放大 | 重建时间长且有额外负载，影响系统性能；风险窗口长 |
| RAIDZ2  | n-2 块盘的容量       | 类似 RAID 6，双奇偶校验，可承受 2 块盘同时故障。避免了 RAID 6 的写入放大                   | 写性能比 RAIDZ1 略差，重建过程长                 |
| RAIDZ3  | n-3 块盘的容量       | ZFS 特有，三重奇偶校验，可承受 3 块盘同时故障                                              | 写性能进一步降低，适合大型存储阵列               |
| RAID-Z+ | n-P 块盘的容量(可配) | ZFS 2.0 新增，允许用户配置更高的奇偶校验盘数                                               | 写性能随奇偶校验盘数量的增加而降低               |
| DRAID   | 可配置               | 分布式备用盘，在传统 RAID-Z 基础上增加了分布式热备功能，重建速度更快                       | 较为复杂，需更高版本 ZFS 支持                    |
| RAID 10 | 50%                  | 在 ZFS 中通过结合 Mirror 和 Stripe 实现，先镜像后条带化                                    | 磁盘利用率低，但比单纯 Mirror 阵列提供更好性能   |

这里有 pool 和 filesystem 的概念，使用 `zpool` 创建的是池，参考于根目录，而使用 `zfs create pool/dir` 的方式是在 pool 下创建子文件系统，一般来说用这种方式来创建 `pool/video`、`pool/music` 这样分离的方式会更好管理

选择 ZFS 的 RAIDZ1，总共是 `4t * (7 - 1) + 6t = 30t`（会有缩水），其中 6t 单独拿出来不做 raid，步骤如下：

1. ZFS 在创建池时会在每个磁盘上记录唯一的元数据信息，为了确保 raid 阵列在今后迁移时能够保证磁盘顺序不变，且与所插入的物理插槽无关，通过 by-id 的方式来组件 zfs 阵列：

    1. 首先为 7 块 4t 盘组建 RAIDZ1 存储池：

        ```bash
        # 确定要使用的磁盘
        $ ls -al /dev/disk/by-id/
        lrwxrwxrwx 1 root root  9 Mar  1 00:18 /dev/disk/by-id/ata-ST4000NM0035-1V4107_ZC18HJPF -> ../../sdc
        lrwxrwxrwx 1 root root 10 Mar  1 00:18 /dev/disk/by-id/ata-ST4000NM0035-1V4107_ZC18HJPF-part1 -> ../../sdc1
        lrwxrwxrwx 1 root root  9 Mar  1 00:18 /dev/disk/by-id/ata-ST4000VX007-2DT166_ZGY27TNF -> ../../sdf
        lrwxrwxrwx 1 root root 10 Mar  1 00:18 /dev/disk/by-id/ata-ST4000VX007-2DT166_ZGY27TNF-part1 -> ../../sdf1
        lrwxrwxrwx 1 root root  9 Mar  1 00:18 /dev/disk/by-id/ata-ST4000VX007-2DT166_ZGY2JM4H -> ../../sdb
        lrwxrwxrwx 1 root root 10 Mar  1 00:18 /dev/disk/by-id/ata-ST4000VX007-2DT166_ZGY2JM4H-part1 -> ../../sdb1
        lrwxrwxrwx 1 root root  9 Mar  1 00:18 /dev/disk/by-id/ata-ST4000VX007-2DT166_ZGY2JMC0 -> ../../sdh
        lrwxrwxrwx 1 root root 10 Mar  1 00:18 /dev/disk/by-id/ata-ST4000VX007-2DT166_ZGY2JMC0-part1 -> ../../sdh1
        lrwxrwxrwx 1 root root  9 Mar  1 00:18 /dev/disk/by-id/ata-ST4000VX007-2DT166_ZGY2JMJJ -> ../../sdg
        lrwxrwxrwx 1 root root 10 Mar  1 00:18 /dev/disk/by-id/ata-ST4000VX007-2DT166_ZGY2JMJJ-part1 -> ../../sdg1
        lrwxrwxrwx 1 root root  9 Mar  1 00:18 /dev/disk/by-id/ata-ST4000VX007-2DT166_ZGY2JN49 -> ../../sdd
        lrwxrwxrwx 1 root root 10 Mar  1 00:18 /dev/disk/by-id/ata-ST4000VX007-2DT166_ZGY2JN49-part1 -> ../../sdd1
        lrwxrwxrwx 1 root root  9 Mar  1 00:18 /dev/disk/by-id/ata-ST4000VX007-2DT166_ZGY2JN7W -> ../../sda
        lrwxrwxrwx 1 root root 10 Mar  1 00:18 /dev/disk/by-id/ata-ST4000VX007-2DT166_ZGY2JN7W-part1 -> ../../sda1
        lrwxrwxrwx 1 root root  9 Mar  1 00:18 /dev/disk/by-id/ata-WDC_WD60EJRX-89MP9Y1_WD-WX11D19511DC -> ../../sde
        lrwxrwxrwx 1 root root 10 Mar  1 00:18 /dev/disk/by-id/ata-WDC_WD60EJRX-89MP9Y1_WD-WX11D19511DC-part1 -> ../../sde1

        ```

        这里的不带 `-part1` 的值就是磁盘的 guid（全局唯一标识符），然后根据具体情况创建 RAIDZ1 存储池

        ```bash
        # zpool create -f <pool_name> <raid_type> guid1 guid2 ...
        $ zpool create -f raid4t raidz1 \
        	/dev/disk/by-id/ata-ST4000NM0035-1V4107_ZC18HJPF \
        	/dev/disk/by-id/ata-ST4000VX007-2DT166_ZGY27TNF \
        	/dev/disk/by-id/ata-ST4000VX007-2DT166_ZGY2JM4H \
        	/dev/disk/by-id/ata-ST4000VX007-2DT166_ZGY2JMC0 \
        	/dev/disk/by-id/ata-ST4000VX007-2DT166_ZGY2JMJJ \
        	/dev/disk/by-id/ata-ST4000VX007-2DT166_ZGY2JN49 \
        	/dev/disk/by-id/ata-ST4000VX007-2DT166_ZGY2JN7W
        ```
    2. 然后创建单独的 6t 盘存储池：`zpool create -f single6t /dev/disk/by-id/ata-WDC_WD60EJRX-89MP9Y1_WD-WX11D19511DC`
2. 然后创建并配置 ZFS 文件系统：

    1. 在 RAIDZ1 存储池 data4t 和独立存储池 single6t 上创建文件系统：`zfs create raid4t/nas`、`zfs create single6t/data`
    2. 设置 ZFS 数据压缩，可以提高机械硬盘的 IO 瓶颈，同时减少写入量，提高硬盘寿命：`zfs set compression=lz4 raid4t/nas`、`zfs set compression=lz4 single6t/data`
    3. 禁用 atime，提高性能：`zfs set atime=off raid4t/nas`、`zfs set atime=off single6t/data`
3. 配置 ZFS 系统内存参数，ARC 是 ZFS 的内存缓存机制，用作缓存数据的缓冲区，由于 pve 还需要分配 14 - 16g 的内存给其他应用，因此这边将 ARC 缓冲区的大小设置为 12G（`pow(2, 10) * 12 * 1024 * 1024 = 12884901888`）：`echo "options zfs zfs_arc_max=12884901888" > /etc/modprobe.d/zfs.conf`
4. 配置完成后查看相关回显：

    ```bash
    $ zpool status
      pool:raid4t
     state: ONLINE
    config:

            NAME                                  STATE     READ WRITE CKSUM
            data4t                                ONLINE       0     0     0
              raidz1-0                            ONLINE       0     0     0
                ata-ST4000NM0035-1V4107_ZC18HJPF  ONLINE       0     0     0
                ata-ST4000VX007-2DT166_ZGY27TNF   ONLINE       0     0     0
                ata-ST4000VX007-2DT166_ZGY2JM4H   ONLINE       0     0     0
                ata-ST4000VX007-2DT166_ZGY2JMC0   ONLINE       0     0     0
                ata-ST4000VX007-2DT166_ZGY2JMJJ   ONLINE       0     0     0
                ata-ST4000VX007-2DT166_ZGY2JN49   ONLINE       0     0     0
                ata-ST4000VX007-2DT166_ZGY2JN7W   ONLINE       0     0     0

    errors: No known data errors

      pool: single6t
     state: ONLINE
    config:

            NAME                                        STATE     READ WRITE CKSUM
            single6t                                      ONLINE       0     0     0
              ata-WDC_WD60EJRX-89MP9Y1_WD-WX11D19511DC  ONLINE       0     0     0

    errors: No known data errors

    $ zpool list
    NAME       SIZE  ALLOC   FREE  CKPOINT  EXPANDSZ   FRAG    CAP  DEDUP    HEALTH  ALTROOT
    raid4t    25.5T  1.43M  25.5T        -         -     0%     0%  1.00x    ONLINE  -
    single6t  5.45T   708K  5.45T        -         -     0%     0%  1.00x    ONLINE  -

    $ df -h
    Filesystem            Size  Used Avail Use% Mounted on
    udev                   16G     0   16G   0% /dev
    tmpfs                 3.1G  2.4M  3.1G   1% /run
    /dev/mapper/pve-root   94G  8.1G   82G  10% /
    tmpfs                  16G   46M   16G   1% /dev/shm
    tmpfs                 5.0M     0  5.0M   0% /run/lock
    efivarfs              128K   36K   88K  29% /sys/firmware/efi/efivars
    /dev/nvme0n1p2       1022M   12M 1011M   2% /boot/efi
    /dev/fuse             128M   20K  128M   1% /etc/pve
    tmpfs                 3.1G     0  3.1G   0% /run/user/0
    raid4t                 22T  256K   22T   1% /raid4t
    single6t              5.4T  128K  5.4T   1% /single6t
    raid4t/nas             22T  256K   22T   1% /raid4t/nas
    single6t/data         5.4T  128K  5.4T   1% /single6t/data
    ```

    由此 ZFS 文件系统就已经创建完毕

    1. 想删除某个 zfs 系统：`zfs destory raid4t/nas`
    2. 想删除某个 pool：`zfs destory raid4t`
    3. 重命名 zfs 系统：`zfs rename raid4t/nas raid4t/new`
5. 此时有两种方式来使用 ZFS 管理的磁盘：

    1. 直接挂载到 pve：`zfs set mountpoint=/mnt/nas raid4t/nas` 和 `zfs set mountpoint=/mnt/data single6t/data`，如果要解除挂载：`zfs unmount -f raid4t/nas`；当然创建 pool 时会默认把 raid4t 和 single6t 挂载到 `/`，所以需要将他们手动解除挂载 `zfs mountpoint=none raid4t`、`zfs set mountpoint=none single6t`
    2. （可选）由于是直接在 pve 中当作文件系统来使用，因此不再需要到 pve 的管理界面中再添加。如果需要用作它途，例如映射给虚拟机使用，那么需要到 *pve - 数据中心 - 存储 - 添加 - ZFS* 添加 ZFS 池，id 可以随意指定，ZFS 池选择 `raid4t/nas`，内容根据情况来选，例如 `Disk image` 是传统的 qcow2 虚拟机磁盘文件、`Container` 是 linux container 格式的文件系统（常用于 docker）等

### 功耗问题

按照上面的设置来看，5600G（低功耗常驻 25w） + 8 块 HDD（5 - 6w 一块，共 48w）低负载下总计 70w 左右，换算下来每个月共 `70 * 24 * 30 / 1000 = 50.4 KWh` 即每个月约 50 度

hdd 本身有休眠低功耗模式，但是 ZFS 天生默认会周期性把事务组（txg）刷到盘上，频率按秒级走，哪怕没有明显业务，也会写元数据。另外如果 ZFS dataset 开着 atime，每次 "读" 也可能变成 "读+写"，进一步拉起 hdd，有两个调优方式：

1. 把 zfs 上所有 dataset 的 atime 关掉：`zfs set atime=off raid4t`、`zfs set atime=off single6t`，
2. 适度拉长 txg 提交间隔，让 "每几秒一小写" 变成 "几十秒一次成批写"，减少无意义唤醒窗口：

    1. 查看默认设置：`cat /sys/module/zfs/parameters/zfs_txg_timeout`，一般是 5s
    2. 修改成 30s：`echo 30 > /sys/module/zfs/parameters/zfs_txg_timeout`
3. 将热写入搬走，确定除了 zfs 本身，不要让其他应用热写入到 hdd 阵列里（除了例如 alist 等应用访问时唤起 hdd 阵列），默认情况下都不会写入到 zfs 的 hdd 阵列，除非特地指定过

## samba 访问

1. `apt install samba`，然后修改配置文件 `vim /etc/samba/smb.conf`，主要是参考着添加以下作用域内容：

    ```ini
    [global]
    	interfaces = 192.168.9.3 vmbr0
    	bind interfaces only = yes

    [nas]
        path = /mnt/nas	# 注意下面指定的用户，必须有对应 path 的权限
        browseable = yes
        read only = no
        create mask = 0755
        directory mask = 0755
        valid users = @users	# 这里有两种方式，一是 valid users = USERNAME 填一个特定的用户名，或者 @GROUPNAME，则这个组里所有用户都能访问
        writable = yes

    [nas2]
        path = /mnt/nas2	# 注意下面指定的用户，必须有对应 path 的权限
    	...
    ```

    可以通过 `testparm` 命令来查看配置是否正确，以及打印出配置文件内容
2. 然后创建一个 samba 账户：`smbpasswd -a username`，这里的用户名得是自己系统里有的用户，根据命令行提示完成创建
3. 重启服务：`systemctl restart smbd nmbd`
4. 回到 windows 上，资源管理器添加网络磁盘映射，服务器是 `\\ip\nas`，账密就是刚才设置的

## 旁路由解决方案

旁路由有两种解决方案：

1. 使用 iStoreOS 处理 nas + 旁路由，这种是典型的在旁路由上添加 nas 功能的方案，一般会将硬盘通过直通或映射的方式给 iStoreOS 去管理
2. 使用 immortalwrt 单独管理旁路由

### iStoreOS

安装 [iStoreOS](https://www.istoreos.com/)，用于管理软路由以及 nas 存储，[安装参考](https://post.smzdm.com/p/a7nd00ql/)，给的是 2c2g10G 的配置，如果想要路由和 nas 分离，参看 immortalwrt 部分

1. 下载 [镜像文件](https://fw0.koolcenter.com/iStoreOS/x86_64/istoreos-22.03.7-2024080210-x86-64-squashfs-combined.img.gz)，由于 qemu 无法识别 img 格式的文件，直接选择下载 `squashfs.iso.gz` 格式的就好，然后将文件解压缩后主动将其挂载到硬盘
2. pve web 里

    1. 创建虚拟机，名称 `iStoreOS`，VM ID 为 100，高级里的开机自启动勾上
    2. 操作系统处选择不使用任何介质
    3. 磁盘删除掉
    4. cpu 1 插槽 2 核心，cpu type 选 host，这是独占两个逻辑核心
    5. 内存 2048MiB
    6. 网络桥接到 vmbr0，模型选 VirtIO
3. 然后将下载好的 gz 文件上传到 pve 的 `/tmp`

    1. 解压：`gunzip istore-squashfs.iso.gz`
    2. 挂载镜像：`qm importdisk 100 /tmp/istoreos-squashfs.img local-lvm`，挂载完成会显示 *Successfully imported disk as 'unused0:local-lvm:vm-100-disk-1'*
    3. 然后回到 `web/数据中心/pve/100`

        1. 硬件，将未使用的硬盘绑定到 scsi0，这里可以顺便增加 scsi0 的容量，我加了 58g
        2. 硬件，添加硬盘，SCSI，存储就选择之前挂载的机械硬盘，磁盘大小是 GiB 需要换算（使用微软计算器），5.5TiB 填入 5680GB 即可，3.6TiB 的就填 3725GB，格式选择 raw（为了在 pve、或其他设备可以直接共享访问该硬盘数据）；多块机械硬盘就添加多次
        3. 选项，引导顺序将 scsi0 移到第一位
        4. 开机（如果报错 *TASK ERROR: KVM virtualisation configured, but not available. Either disable in VM configuration or enable in BIOS.* ，则需要在主机的 bios 里开启虚拟化）
4. 见到 *iStoreOS is ready* 成功开机，按回车开始配置 iStoreOS，输入 `quickstart` 开始进行配置

    1. 第一项 `Show Interfaces` 可以发现网络 ip 被 dhcp 自动配置到 `192.168.9.x` 了
    2. 选择 `Change LAN IP`，修改如下：`192.168.9.4`、`255.255.255.0`
    3. 修改完成后，在网段内输入 `http://192.168.9.4` 进入 iStoreOS 的配置界面，预设账密是 `root/password`
    4. 然后到路由器里配置静态 ip 绑定 `iStoreOS` 的 mac 到 192.168.9.4
5. 使用 ssh 连接到终端，默认登录账密也是 `root / password`，然后参照 [init-a-new-vps-host](https://www.majo.im/index.php/wkyuu/342.html) 配置 iStoreOS

    1. 新建用户 wkyuu：`groupadd -g 1000 wkyuu`、`useradd -s /bin/ash -g wkyuu -G adm,users,docker -u 1000 -d /home/wkyuu -m wkyuu`、`passwd wkyuu`
    2. 为 root 和 wkyuu 配置 ssh 免密登录，这里由于 iStoreOS 使用的是 dropbear ssh，在本地创建一个文件，输入 `authorized_keys` 里的内容，然后在 `web/系统/管理权/SSH密钥` 里将其上传，该文件会被放置到 `/etc/dropbear/authorized_keys`
    3. 将 wkyuu 添加到 docker 组：`usermod add -aG docker wkyuu`
6. （可选）为 iStoreOS 系统目录扩容，如果是后续调整加盘，但是系统里没有自动将其挂载，则需要手动分区

    1. 输入 `lsblk` 查看未利用情况

        ```bash
        root@nas:~# lsblk
        NAME   MAJ:MIN RM  SIZE RO TYPE MOUNTPOINTS
        sda      8:0    0 60.4G  0 disk
        ├─sda1   8:1    0  128M  0 part /boot
        │                               /boot
        ├─sda2   8:2    0  256M  0 part /rom
        └─sda3   8:3    0    2G  0 part /overlay/upper/opt/docker
                                        /overlay
        ```
    2. 使用 `fdisk /dev/sda` 操作磁盘信息

        1. 删除分区：一进去就输入 `d`，然后选择分区 `3`
        2. 创建分区：然后输入 `n`，选择分区类型为主分区 `p`，分区号 `3`，起始和结束扇区都默认即可
        3. 完成修改：输入 `w` 即可
    3. 然后重启 `reboot` 即可看到更改
7. 网络附加存储（nas）

    1. 在 `web/系统/磁盘管理` 中可以看到已经成功挂载的机械硬盘及其容量
    2. 进入 `web/网络存储/磁盘阵列`，创建磁盘阵列

        1. 各种 raid 的区别：

            | 类型    | 磁盘利用率  | 原理                                                                                                     | 缺点                       |
            | --------- | ------------- | ---------------------------------------------------------------------------------------------------------- | ---------------------------- |
            | raid 0  | 100%        | 数据被分割并同时写入多块硬盘，使得读写速度提升                                                           | 一块盘坏，全部坏           |
            | raid 1  | 50%         | 平均分成两组，当数据被存到其中一组时，也会被完全复制到另一组硬盘上，一块硬盘损坏，数据可以从镜像盘中恢复 | 吃空间                     |
            | raid 5  | 减去 1 块盘 | 数据分布在所有硬盘上，使用奇偶校验信息来在 1 块硬盘损坏的情况下恢复数据                                  | 写入速度较慢，特别是小文件 |
            | raid 6  | 减去 2 块盘 | 数据分布在所有硬盘上，使用奇偶校验信息来在 2 块硬盘损坏的情况下恢复数据                                  | 写入性能更差，配置起来复杂 |
            | raid 10 | 50%         | 结合 raid 0 和 raid 1，先将数据镜像到两组硬盘，然后对镜像盘进行条带化                                    | 吃空间                     |
        2. 确定 raid 后，选择硬盘来创建，我这里选择了 raid 5，但是由于既有 5.5t 又有 3.6t，会导致全部按照 3.6t 的大小来组建 raid 5，会浪费 6t 左右的空间，因此还可以分开组 raid：7 块 3.6t 的盘组 raid 5，3 块 5.5t 的盘组 raid 5；两者方案对比：`5.5 * 2 + 3.6 * 6 = 32.6`、`3.6 * 9 = 32.4`，方便起见，可以选择 10 块全组 raid 5，由于最后是将 raid 阵列抽象成单个硬盘，因此组多个 raid 可以将数据分成多种类型来存储，例如 `3.6 * 6` 全部存种子下载的文件，`5.5 * 2` 存相片、录像文件
        3. 按照 `5.5 * 2 + 3.6 * 6 = 32.6` 的方式组建 raid 5，得到两个路径：`/mnt/md0`、`/mnt/md1`，之后存储数据只要选择这两个路径就可以了，剩下的交给 raid 5 系统来实现
    3. 进入 `web/网络存储/统一文件共享`

        1. 常规设置启用
        2. 在 `用户` 选项卡添加用户账密
        3. 在 `统一文件共享` 选项卡，路径 `/mnt/data_mdx`，名称 `storage`，用户勾选上刚才创建的用户
        4. 保存并应用
    4. 在 windows 上，资源管理器添加网络位置：`\\nas\storage`（这里的 `nas` 是主机名），选择一个名称即可
    5. 在 linux 上，需要手动 mount，debian 系参考如下

        1. `sudo apt update && sudo apt install cifs-utils`
        2. `mkdir -p /mnt/samba sudo mount -t cifs //192.168.9.4/storage /mnt/samba -o username=user`，然后输入密码
        3. 挂载完成后即可进入并访问
8. 配网，科学上网

    1. 到 [openclash](https://github.com/vernesong/OpenClash.git) 获取 ipk 文件：[luci-app-openclash-x.ipk](https://github.com/vernesong/OpenClash/releases/download/v0.46.014-beta/luci-app-openclash_0.46.014-beta_all.ipk)
    2. 安装前置：`opkg update`，`opkg install coreutils-nohup bash iptables dnsmasq-full curl ca-certificates ipset ip-full iptables-mod-tproxy iptables-mod-extra libcap libcap-bin ruby ruby-yaml kmod-tun kmod-inet-diag unzip luci-compat luci luci-base`
    3. 在 `web/iStore/手动安装` 选择下载好的 ipk 文件安装即可在 `web/服务/OpenClash` 里看到，第一次点进去可能会要求下载内核，选择一个可连接的 cdn 下载即可
    4. 除了要安装内核、上传配置文件外，还需要到 *web - 服务 - OpenClash - 覆写设置 - 常规设置* 最下方删除掉默认生成的一个账户，否则在使用代理时会报 407 错误，设置完成后点击应用设置

### ImmortalWrt

十分接近原版 OpenWrt，适合稳定、精简，旁路由只干好自己本职工作的场景，[镜像下载链接](https://mirrors.sdu.edu.cn/immortalwrt/releases/24.10.0/targets/x86/64/)；在当前场景的设计中，bcm5720 是一块免驱的 2 千兆口 PCIe 网卡，使用 f0 和 f1 来代表这两个网口，其中 f0 已经被用作 pve 的 vmbr0，打算将 f1 直通给 wrt，作为其 wan 口，让主路由给 f1 提供 wan（也就是 f1 连接主路由的 lan 口），pve 中其他虚拟机将 wrt 的 f1 设置为网关时，可以通过 *vmbr0（f0） -&gt; vSwitch（PCIe） -&gt; wrt 的 wan（f1）*  的方式吃满这张 bcm5720（即其他虚拟机成为了 wrt 的子网）

给的是 1c2g1g 的配置，大体上是参考上文 iStoreOS 的创建方式，下载文件系统然后导入到空磁盘安装，具体内容可以参考着执行，下面使用 qcow2 + efi 的方式来导入（这边的 vmid 是 100，后文碰到 vmid 的地方会直接写 100）：

1. 在创建虚拟机时，机型选择 q35 和 viommu intel（支持 amd）、内存 2048、处理器 1 插槽 1 核心选择 host、bios 选择 ovmf、网络（如果有多网卡，也要继续选择 VirtIO、vmbr0，这是为旁路由的设计）、硬盘去掉，其他默认即可
2. 选择 ext4 文件格式，方便有需求的情况下扩容：immortalwrt-x86-64-generic-ext4-combined-efi.qcow2.gz
3. 下载后的 qcow2.gz 无法在 pve 上通过工具直接解压，可以本地解压提取出其中的 qcow2 文件后再上传到 pve 里：`rsync -avtz --progress ./immortalwrt-x86-64-generic-ext4-combined-efi.qcow2 root@host:/tmp/immortalwrt-efi.qcow2`
4. 导入：`qm disk import 100 /tmp/immortalwrt-24.10.0-x86-64-generic-ext4-combined-efi.qcow2 local-lvm --format=qcow2`，导入完成后到 web 就可以看到 wrt 的硬件页面出现了未使用磁盘 0，点击编辑这个磁盘，然后再点添加即可
5. 在左侧 选项 里找到 引导顺序 选择 scsi0，拖动到顶端
6. 开机，初次进入可以为 root 账号配置一个密码：`passwd`

然后开始直通网卡

1. **注意：直通网卡前，需要通过 vfio 配置网卡隔离，如果未配置网卡隔离直接直通，会导致网卡被完全直通给虚拟机（常见于多网口的 PCIE 网卡），如果此时又正好是通过该 PCIE 网卡访问的 pve 后台，这将导致 pve 的后台无法通过之前的网口进入**，需要手动进入 pve 的 shell：`qm set vmid --delete hostpci0` 来删除网卡直通（可以通过 `qm config 100` 来查看其 pci 设备的 key）
2. 先修改 grub

    1. intel 的 cpu：`vim /etc/default/grub`，在 `GRUB_CMDLINE_LINUX_DEFAULT="quiet"` 修改成 `GRUB_CMDLINE_LINUX_DEFAULT="quiet intel_iommu=on"`
    2. amd 的是：`GRUB_CMDLINE_LINUX_DEFAULT="quiet amd_iommu=on"`
    3. 然后 `update-grub`
    4. `reboot`
3. 然后修改 `vim /etc/modules` 添加以下行，该文件默认为空

    ```ini
    vfio
    vfio_iommu_type1
    vfio_pci
    vfio_virqfd
    ```

    使用 `update-initramfs -k all -u` 更新内核，然后使用 `find /sys/kernel/iommu_groups/ -type l` 查看如果出现了很多直通组，就算开启直通成功一半了，输出示例如下

    ```bash
    $ find /sys/kernel/iommu_groups/ -type l
    /sys/kernel/iommu_groups/7/devices/0000:00:18.3
    /sys/kernel/iommu_groups/7/devices/0000:00:18.1
    /sys/kernel/iommu_groups/7/devices/0000:00:18.6
    /sys/kernel/iommu_groups/7/devices/0000:00:18.4
    /sys/kernel/iommu_groups/7/devices/0000:00:18.2
    /sys/kernel/iommu_groups/7/devices/0000:00:18.0
    /sys/kernel/iommu_groups/7/devices/0000:00:18.7
    ...

    $ dmesg | grep -e DMAR -e IOMMU
    [    0.000000] Warning: PCIe ACS overrides enabled; This may allow non-IOMMU protected peer-to-peer DMA
    [    0.390595] pci 0000:00:00.2: AMD-Vi: IOMMU performance counters supported
    [    0.401186] perf/amd_iommu: Detected AMD IOMMU #0 (2 banks, 4 counters/bank).
    ```
4. 现在解决另一半的直通：

    1. 输入 `for d in /sys/kernel/iommu_groups/*/devices/*; do n=${d#*/iommu_groups/*}; n=${n%%/*}; printf 'IOMMU Group %s ' "$n"; lspci -nns "${d##*/}"; done | grep Eth`，这个命令会列出系统中与网卡相关的 IOMMU 分组，示例如下

        ```bash
        # for d in /sys/kernel/iommu_groups/*/devices/*; do n=${d#*/iommu_groups/*}; n=${n%%/*}; printf 'IOMMU Group %s ' "$n"; lspci -nns "${d##*/}"; done | grep Eth
        IOMMU Group 8 04:00.0 Ethernet controller [0200]: Broadcom Inc. and subsidiaries NetXtreme BCM5720 Gigabit Ethernet PCIe [14e4:165f]
        IOMMU Group 8 04:00.1 Ethernet controller [0200]: Broadcom Inc. and subsidiaries NetXtreme BCM5720 Gigabit Ethernet PCIe [14e4:165f]
        IOMMU Group 8 07:00.0 Ethernet controller [0200]: Realtek Semiconductor Co., Ltd. RTL8125 2.5GbE Controller [10ec:8125] (rev 05)
        ```

        如果发现你的网口并没有被分到同一个 IOMMU Group，就可以直接跳过下面的步骤了
    2. 会发现上述三个网卡全都被分到了同一个 IOMMU 组，IOMMU 组是硬件设备的分组，同一组内的设备在 DMA 和中断处理上是相互关联的，必须一起直通给虚拟机，也就是无法隔离开来
    3. 想要实现 bcm5720 的两个网口 f0 和 f1，其中 f0 作为 pve 的管理口（也是其中其他虚拟机的 vmbr0 桥接口），f1 直通给 wrt，就必须拆分 IOMMU 分组，通过使用 [pcie_acs_override](https://lkml.org/lkml/2013/5/30/513) 功能强制将所有设备全部分开成不同的 IOMMU 分组，需要修改 `vim /etc/default/grub` 内容如下：

        ```ini
        GRUB_CMDLINE_LINUX_DEFAULT="quiet amd_iommu=on iommu=pt pcie_acs_override=downstream,multifunction"
        ```

        修改完成后 `update-grub`、`reboot`，之后再次重新查看：

        ```bash
        # for d in /sys/kernel/iommu_groups/*/devices/*; do n=${d#*/iommu_groups/*}; n=${n%%/*}; printf 'IOMMU Group %s ' "$n"; lspci -nns "${d##*/}"; done | grep Eth
        IOMMU Group 17 04:00.0 Ethernet controller [0200]: Broadcom Inc. and subsidiaries NetXtreme BCM5720 Gigabit Ethernet PCIe [14e4:165f]
        IOMMU Group 18 04:00.1 Ethernet controller [0200]: Broadcom Inc. and subsidiaries NetXtreme BCM5720 Gigabit Ethernet PCIe [14e4:165f]
        IOMMU Group 20 07:00.0 Ethernet controller [0200]: Realtek Semiconductor Co., Ltd. RTL8125 2.5GbE Controller [10ec:8125] (rev 05)
        ```

        此时的 IOMMU 就被强制分开了
5. 通过 `lspci | grep net` 找到自己的网卡设备，这边是打算将 `04:00.1` 直通给 wrt

    ```bash
    # lspci | grep net
    04:00.0 Ethernet controller: Broadcom Inc. and subsidiaries NetXtreme BCM5720 Gigabit Ethernet PCIe
    04:00.1 Ethernet controller: Broadcom Inc. and subsidiaries NetXtreme BCM5720 Gigabit Ethernet PCIe
    07:00.0 Ethernet controller: Realtek Semiconductor Co., Ltd. RTL8125 2.5GbE Controller (rev 05)
    ```
6. 到 web 界面中，wrt 的硬件里添加 pci 设备，这里应该可以看到 bcm5720 被分开不同的 IOMMU 组，**记得不要勾选所有功能**，否则会将 pcie 完全直通给 wrt，相当于前面白干
7. 如果成功了将在 web 里对应的虚拟机看到 pci 设备，进入系统后输入 `ip a` 也应该可以看到已经有了直通进来的网卡的 mac
8. 此时的 ip 是 192.168.1.1，不一定能访问得到，这里需要配置 `/etc/config/network` 实现设计的旁路由内容

    1. 由于既有 vmbr0 又有 f1（pcie 网卡） 直通，pve 会优先引导 vmbr0 然后才到 pcie，因此 vmbr0 对应 eth0、f1 对应 eth1
    2. 配置 `/etc/config/network` 如下

        ```bash
        root@ImmortalWrt:~# cat /etc/config/network
        config interface 'loopback'
                option device 'lo'
                option proto 'static'
                option ipaddr '127.0.0.1'
                option netmask '255.0.0.0'
        config globals 'globals'
                option ula_prefix 'fdf1:34ee:d0c2::/48'
                option packet_steering '1'
        config device
                option name 'br-lan'
                option type 'bridge'
                list ports 'eth0'
        config interface 'lan'
                option device 'br-lan'
                option proto 'static'
                option ipaddr '192.168.9.5'
                option netmask '255.255.255.0'
                option gateway '192.168.9.4'
                list dns '127.0.0.1'
                list dns '192.168.9.4'
                list dns '223.5.5.5'
        config interface 'wan'
                option device 'eth1'
                option proto 'static'
                option ipaddr '192.168.9.4'
                option netmask '255.255.255.0'
                option gateway '192.168.9.1'
                list dns '127.0.0.1'
                list dns '192.168.9.1'
                list dns '223.5.5.5'
        ```
    3. 配置完成后执行 `service network restart` 来应用网络

        ```bash
        root@ImmortalWrt:~# service network restart

        root@ImmortalWrt:~# ip a
        1: lo: <LOOPBACK,UP,LOWER_UP> mtu 65536 qdisc noqueue state UNKNOWN qlen 1000
            link/loopback 00:00:00:00:00:00 brd 00:00:00:00:00:00
            inet 127.0.0.1/8 scope host lo
               valid_lft forever preferred_lft forever
            inet6 ::1/128 scope host
               valid_lft forever preferred_lft forever
        2: eth0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc fq_codel state UP qlen 1000
            link/ether bc:24:11:82:eb:cb brd ff:ff:ff:ff:ff:ff
            inet 192.168.9.5/24 brd 192.168.9.255 scope global eth0
               valid_lft forever preferred_lft forever
        3: eth1: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc mq state UP qlen 1000
            link/ether 00:0a:f7:86:6d:99 brd ff:ff:ff:ff:ff:ff
            inet 192.168.9.4/24 brd 192.168.9.255 scope global eth1
               valid_lft forever preferred_lft forever

        root@ImmortalWrt:~# ip route
        default via 192.168.9.1 dev eth1
        192.168.9.0/24 dev br-lan scope link  src 192.168.9.5
        192.168.9.0/24 dev eth1 scope link  src 192.168.9.4
        ```
    4. 顺带可以修改 dhcp 配置，在 dhcp 配置中，关闭 lan 口的 dhcp，全部交给主路由来分配 ip

        ```bash
        root@ImmortalWrt:~# cat /etc/config/dhcp
        ...
        config dhcp 'lan'
                ...
                option ignore '1'
        ...
        ```

        `service dnsmasq restart`
    5.
9. 配置软件包

    1. 不建议换 ustc 的源，他们更新慢
    2. （可选）配置代理：`vim /etc/opkg.conf`，添加 `option http_proxy xxx`、`option https_proxy xxx`
    3. 更新：`opkg update`
    4. 安装主题：`wget https://github.com/jerrykuku/luci-theme-argon/releases/download/v2.3.1/luci-theme-argon_2.3.1_all.ipk`、`wget https://github.com/jerrykuku/luci-app-argon-config/releases/download/v0.9/luci-app-argon-config_0.9_all.ipk`，`opkg install luci*.ipk`
    5. 装点常用软件：`opkg install curl iperf3 rsync ddns-go`
    6. 一些项目推荐：

        1. ~~[nikkinikki-org/OpenWrt-nikki](https://github.com/nikkinikki-org/OpenWrt-nikki.git)~~ **请勿使用这个代理，不好用不说，作者态度傲慢**
        2. [vernesong/OpenClash](https://github.com/vernesong/OpenClash.git)

            1. 如果网络不好，需要把以下内容放到对应位置：

                ```bash
                # 文件 /usr/share/openclash/openclash_core.sh 中：
                # DOWNLOAD_URL="${github_address_mod}gh/vernesong/OpenClash@core/${RELEASE_BRANCH}/meta/clash-${CPU_MODEL}.tar.gz"
                wget https://cdn.jsdelivr.net/gh/vernesong/OpenClash@core/master/meta/clash-linux-amd64.tar.gz -O - | tar zxvfo -
                mv clash /etc/openclash/core/clash_meta

                wget https://testingcf.jsdelivr.net/gh/alecthw/mmdb_china_ip_list@release/lite/Country.mmdb -O /etc/openclash/Country.mmdb
                wget https://testingcf.jsdelivr.net/gh/Loyalsoldier/v2ray-rules-dat@release/geosite.dat -O /etc/openclash/GeoSite.dat
                wget https://testingcf.jsdelivr.net/gh/Loyalsoldier/v2ray-rules-dat@release/geoip.dat -O /etc/openclash/geoip.dat
                ```
            2. 启动 openclash 后，以下几个内容要配置一下：

                ```json

                ```
        3.
        4. luci-app-filebrowser，用于查看 wrt 内部文件，配置完成后在系统选项卡中查看
10. 通过 ip 访问 wrt 的网页，默认账密为 `root / password`，如果在上面使用过 `passwd` 来设置密码，那么密码就是所设置的

## vm

除了 nas、软路由，还需要选择一个可以访问图形界面的系统，这里以 RHEL 为例

1. 选择通过 iso 安装

    1. 去官网申请个 [个人开发者账号](https://developers.redhat.com/)
    2. 在开发者站点下获取 [RHEL：红帽企业版 Linux](https://access.redhat.com/downloads/content/rhel)
2. 磁盘选择 `local-lvm`，磁盘大小给到了 239GiB（就是所谓 256GB），注意这里如果要直通网卡给 rhel，记得选择 q35 和 viommu intel
3. cpu 给到 2 插槽 3 核心共 6 个核心，类别选择 host
4. 内存给 16384MiB（就是所谓 16GB）
5. 网络桥接到 vmbr0 即可
6. 开始安装系统

    1. 在 disk 分区那块，选择手动分区，主硬盘是 `primary 252.6GB ext4 /`，然后剩下一个 `logical 4GB swap swap`
    2. 在安装 grub 来 boot 系统那块，选择 primary disk，然后位置 `/dev/sda`
    3. 安装完成后，回到选项里在引导顺序中将 scsi0 移到顶上再重新启动系统即可进入 rhel
7. 安装成功，进入系统后，注册 rhel：`subscription-manager register --auto-attach --username=xxxx --password=xxxx`，这里的账密是上面注册的个人开发者账号
8. 安装完成后初始化方式就可以参考：[init-my-unix](https://www.majo.im/index.php/wkyuu/356.html)

## other

### 插槽

在创建虚拟机时，会碰上插槽和核心的概念，其实很简单：2 插槽 3 核心，指的是两块 cpu，每块 cpu 都是 3 核心，共 6 核心

如果选择模型是 host 模式，将把 cpu 上 6 个线程完全给虚拟机（超线程技术）

### u 盘不识别

1. 参照 [win10/win11 系统安装教程（新装、重装）](https://zhuanlan.zhihu.com/p/93127323) 安装 windows 系统，使用图吧工具箱测试性能
2. 清空 u 盘启动盘状态，恢复成普通 u 盘

    1. `diskpart`，使用 `?` 查看帮助
    2. `list disk` 查看硬体磁盘信息，找到 u 盘设备，这里是 `磁盘 2`
    3. 因此 `select disk 2`
    4. 清空：`clean`
    5. 创建主分区：`create partition primary`
    6. 选择该分区：`select partition 1`
    7. 格式化该分区：`format fs=ntfs quick`，fs 还可选 fat32，一般是为空间较小的 u 盘准备的
    8. 分配一个驱动器号：`assign`（这一步一般会在格式化后自动完成并识别出来，如果没有就手动分配）

### ssd 不识别

新买了一块 2t 的 ssd，插上 pve 开机时可能不识别，需要按照以下操作：

1. `lsblk` 查看新增的固态名称，这里是 nvme0n1
2. 对其格式化：`fdisk /dev/nvme0n1`，

    1. 输入 `n` 开始创建分区，这里 `p` 和 `e`，如果只想用来存数据，则选择 p 即可，然后一路回车默认即可
    2. 再次输入 `p` 可以查看分区表，确认分区已经创建
    3. 输入 `w` 写入分区表，然后会自动退出
3. `partprobe` 刷新系统的分区表信息，此时再 `lsblk` 就能看到 nvme0n1 有 disk 信息了
4. 想要系统能够使用该固态，需要将该固态修改成 ext4 文件系统：`sudo mkfs.ext4 /dev/nvme0n1p1`
5. 修改完成后即可挂载：`sudo mount /dev/nvme0n1p1 /mnt/nvme0n1`
6. 性能测试：`sudo apt-get update && sudo apt-get install fio`，然后简单测试：`sudo fio --name=randwrite --ioengine=libaio --direct=1 --rw=randwrite --bs=4k --numjobs=1 --size=1G --time_based --runtime=30 --group_reporting --allow_mounted_write=1 --filename=/dev/nvme0n1`

### 挂载机械硬盘

挂载系统中的机械硬盘（更推荐通过 ZFS 系统来配置自己的磁盘资源，参看前文），查看所有的机械盘信息：

```bash
$ lsblk
NAME                         MAJ:MIN RM   SIZE RO TYPE MOUNTPOINTS
sda                            8:0    0   3.6T  0 disk 
└─sda1                         8:1    0   128M  0 part 
sdb                            8:16   0   5.5T  0 disk 
└─sdb1                         8:17   0   128M  0 part 
sdc                            8:32   0   3.6T  0 disk 
└─sdc1                         8:33   0   128M  0 part 
sdd                            8:48   0   5.5T  0 disk 
└─sdd1                         8:49   0   128M  0 part 
sde                            8:64   0   3.6T  0 disk 
└─sde1                         8:65   0   128M  0 part 
sdf                            8:80   0   3.6T  0 disk 
└─sdf1                         8:81   0   128M  0 part 
sdg                            8:96   0   3.6T  0 disk 
└─sdg1                         8:97   0   128M  0 part 
sdh                            8:112  0   3.6T  0 disk 
└─sdh1                         8:113  0   128M  0 part 
sdi                            8:128  0   5.5T  0 disk 
└─sdi1                         8:129  0   128M  0 part 
sdj                            8:144  0   3.6T  0 disk 
└─sdj1                         8:145  0   128M  0 part 
nvme0n1                      259:0    0 931.5G  0 disk 
├─nvme0n1p1                  259:1    0  1007K  0 part 
├─nvme0n1p2                  259:2    0     1G  0 part /boot/efi
└─nvme0n1p3                  259:3    0 930.5G  0 part 
  ├─pve-swap                 252:0    0     8G  0 lvm  [SWAP]
  ├─pve-root                 252:1    0    96G  0 lvm  /
  ├─pve-data_tmeta           252:2    0   8.1G  0 lvm  
  │ └─pve-data-tpool         252:4    0 794.3G  0 lvm  
  │   ├─pve-data             252:5    0 794.3G  1 lvm  
  │   └─pve-vm--100--disk--0 252:6    0  60.4G  0 lvm  
  └─pve-data_tdata           252:3    0 794.3G  0 lvm  
    └─pve-data-tpool         252:4    0 794.3G  0 lvm  
      ├─pve-data             252:5    0 794.3G  1 lvm  
      └─pve-vm--100--disk--0 252:6    0  60.4G  0 lvm

$ df -h
Filesystem            Size  Used Avail Use% Mounted on
udev                   16G     0   16G   0% /dev
tmpfs                 3.1G  1.4M  3.1G   1% /run
/dev/mapper/pve-root   94G   18G   72G  20% /
tmpfs                  16G   46M   16G   1% /dev/shm
tmpfs                 5.0M     0  5.0M   0% /run/lock
efivarfs              128K   36K   88K  29% /sys/firmware/efi/efivars
/dev/nvme0n1p2       1022M   12M 1011M   2% /boot/efi
/dev/fuse             128M   16K  128M   1% /etc/pve
tmpfs                 3.1G     0  3.1G   0% /run/user/0
```

可以看到有 10 块机械硬盘没有被挂载，且只用了很小一部分的 ssd 作为 pve 的系统盘

1. 先格式化机械硬盘：`fdisk /dev/sda`，然后 `d` 删除分区，`n` 新建分区，默认分区号 `1`，默认起始和结束扇区，`w` 完成修改
2. 为空的机械硬盘创建文件系统 `mkfs -t ext4 /dev/sda1`
3. 创建目录并挂载：`mkdir -p /mnt/disk1`，`mount /dev/sda1 /mnt/disk1`
4. 配置自动挂载，需要编辑 `/etc/fstab` 文件，在末尾加入信息 `/dev/sda1 /mnt/disk1 ext4 defaults 0 0`，示例如下：

    ```ini
    # <file system> <mount point> <type> <options> <dump> <pass>
    /dev/pve/root / ext4 errors=remount-ro 0 1
    UUID=41F2-21AB /boot/efi vfat defaults 0 1
    /dev/pve/swap none swap sw 0 0
    proc /proc proc defaults 0 0
    /dev/sda1 /mnt/disk1 ext4 defaults 0 0
    ```

    修改完成后，输入 `systemctl daemon-reload` 重载配置，此时再 `df -h` 就可以看到已经挂载上了
5. 有 10 块盘，就循环配置并挂载、写入文件即可

    1. `mkdir -p /mnt/disk01-5.5t /mnt/disk02-5.5t /mnt/disk03-5.5t /mnt/disk04-3.6t /mnt/disk05-3.6t /mnt/disk06-3.6t /mnt/disk07-3.6t /mnt/disk08-3.6t /mnt/disk09-3.6t /mnt/disk10-3.6t`
    2. `touch /tmp/mount.sh && chmod +x /tmp/mount.sh`：

        ```bash
        #/usr/bin/env bash

        mount /dev/sdb1 /mnt/disk01-5.5t
        mount /dev/sdd1 /mnt/disk02-5.5t
        mount /dev/sdi1 /mnt/disk03-5.5t
        mount /dev/sda1 /mnt/disk04-3.6t
        mount /dev/sdc1 /mnt/disk05-3.6t
        mount /dev/sde1 /mnt/disk06-3.6t
        mount /dev/sdf1 /mnt/disk07-3.6t
        mount /dev/sdg1 /mnt/disk08-3.6t
        mount /dev/sdh1 /mnt/disk09-3.6t
        mount /dev/sdj1 /mnt/disk10-3.6t
        ```
    3. `vim /etc/fstab`

        ```ini
        # <file system> <mount point> <type> <options> <dump> <pass>
        /dev/pve/root / ext4 errors=remount-ro 0 1
        UUID=41F2-21AB /boot/efi vfat defaults 0 1
        /dev/pve/swap none swap sw 0 0
        proc /proc proc defaults 0 0
        /dev/sdb1 /mnt/disk01-5.5t ext4 defaults 0 0
        /dev/sdd1 /mnt/disk02-5.5t ext4 defaults 0 0
        /dev/sdi1 /mnt/disk03-5.5t ext4 defaults 0 0
        /dev/sda1 /mnt/disk04-3.6t ext4 defaults 0 0
        /dev/sdc1 /mnt/disk05-3.6t ext4 defaults 0 0
        /dev/sde1 /mnt/disk06-3.6t ext4 defaults 0 0
        /dev/sdf1 /mnt/disk07-3.6t ext4 defaults 0 0
        /dev/sdg1 /mnt/disk08-3.6t ext4 defaults 0 0
        /dev/sdh1 /mnt/disk09-3.6t ext4 defaults 0 0
        /dev/sdj1 /mnt/disk10-3.6t ext4 defaults 0 0
        ```

        `systemctl daemon-reload`
    4. 配置完可以 `reboot` 看看结果

到 *web - 数据中心 - 存储 - 添加* 选择添加目录，参考：ID 随便输可以与前文一致（`disk01-5.5t`），目录就选择对应的 `/mnt/disk`（`/mnt/disk01-5.5t`），内容选磁盘映像；此时应该可以在左侧看到已挂载的硬盘

### initramfs 问题

PVE 开机总是进入 initramfs 无法正常进入系统，[参考](https://www.bilibili.com/read/cv21618228/)：`sed 's/GRUB_CMDLINE_LINUX_DEFAULT="quiet"/GRUB_CMDLINE_LINUX_DEFAULT="rootdelay=10 quiet"/g' /etc/default/grub`

### 路由风暴问题（重要）

按照以上思路配置完设备后，当 pve 同时拥有两张网卡时，可能会因为相同路由导致局域网内的广播风暴，具体表现为局域网内其他设备会时不时断网，

```bash
# ip route
default via 192.168.9.1 dev vmbr0 proto kernel onlink
192.168.9.0/24 dev vmbr0 proto kernel scope link src 192.168.9.3
192.168.9.0/24 dev enp7s0 proto kernel scope link src 192.168.9.6
```

查看路由表，可以发现起初设计的由 enp7s0 提供 2.5g 带宽能力给 nas，vmbr0（使用 enp4s0f0 网口）提供 pve 及其虚拟机访问能力，在路由上出现了问题：**同一网段（192.168.9.0/24）有两条重复路由，一条通过 vmbr0，一条通过 enp7s0，系统不知道该通过哪个网卡发送数据包，这会导致路由混乱和 ARP 冲突**

为什么 ARP 表混乱和广播风暴会影响局域网其他设备？这实际上是一种无意的自我 DoS 攻击

1. PVE 主机使用两个不同的物理网卡（不同 MAC 地址）宣告了同一个子网的路由。当其他设备（如 192.168.9.2）需要与 PVE 通信时：

    - 它会发送 ARP 广播询问"谁是 192.168.9.3/192.168.9.6"

    - PVE 会从两个不同网卡回应，提供不同的 MAC 地址
    - 其他设备的 ARP 表会频繁更新，导致通信不稳定
    - 路由器的 ARP 表也会反复变化，造成路由不稳定
2. 广播风暴，当两个网卡都连接到同一个物理网络时：

    - 一个网卡接收的广播包会被另一个网卡重新发送
    - 形成广播循环，迅速耗尽网络带宽和设备处理能力
    - 网络设备因处理大量无效包而变得不可用

以下是 5 种解决思路

#### 链路聚合

最推荐

将 enp7s0 也添加到 vmbr0 桥接中，这种方式是将 enp4s0f0 和 enp7s0 都桥接给 vmbr0

但是这样就没法实现 enp7s0 单占一个 ip（不过这样子也方便于仅使用 pve 单个系统的情况），好处是可以通过链路聚合的方式实现两个网卡的负载均衡，且会优先使用 enp7s0 网卡

链路聚合是一种将多个物理网络接口组合成一个逻辑接口的技术，在 Linux 系统中，通过内核的 bonding 驱动实现，主要用于：

- 增加带宽容量：理论上可将多个网卡带宽合并
- 提供冗余：一个网卡失效时，另一个可继续工作
- 负载均衡：在多个网卡间分配流量，balance-alb 模式会自动优先使用 2.5G 网卡，在大文件传输时，系统会尽可能使用最快的链路，当多个客户端同时访问 NAS 时，流量可以分散到两个网卡，系统会动态平衡网络负载，提高整体吞吐量

如果明确不需要为 nas 单独分配 ip，那么选择链路聚合的方案可以简化网络结构

实现方式也简单，先安装 `apt install ifenslave`，然后启用模块：`modprobe bonding`，`echo "bonding" >> /etc/modules`

编辑 `vim /etc/network/interfaces`（注意注释内容不能写在配置后面，不然无法识别甚至报错）：

```ini
auto bond0
iface bond0 inet manual
		# 2.5G网卡放前面优先使用
        bond-slaves enp7s0 enp4s0f0
		# 自适应负载均衡模式
        bond-mode balance-alb
		# 链路监控间隔 1s
        bond-miimon 100
		# 基于IP+端口分配流量
        bond-xmit-hash-policy layer3+4
		# 明确指定2.5G为主要链路
        bond-primary enp7s0

auto vmbr0
iface vmbr0 inet static
        address 192.168.9.3/24
        gateway 192.168.9.1
        bridge-ports bond0
        bridge-stp off
        bridge-fd 0
```

重启系统即可，可以使用 `ip -s link show bond0; ip -s link show enp7s0; ip -s link show enp4s0f0` 来查看具体的链路运行情况，分到的包的数量

#### 策略路由

次要推荐，但是这种方式可能会比较复杂

首先配置网口控制文件：`vim /etc/network/interfaces`：

```ini
auto lo
iface lo inet loopback

iface enp4s0f0 inet manual
iface wlp6s0 inet manual

auto vmbr0
iface vmbr0 inet static
        address 192.168.9.3/24
        gateway 192.168.9.1
        bridge-ports enp4s0f0
        bridge-stp off
        bridge-fd 0

auto enp7s0
iface enp7s0 inet static
        address 192.168.9.6/24
        # 删除主路由表中的重复路由
        post-up ip route del 192.168.9.0/24 dev enp7s0 proto kernel scope link src 192.168.9.6

        # 策略路由配置, 添加双向策略路由规则
        post-up ip route add 192.168.9.0/24 dev enp7s0 src 192.168.9.6 table 200
        post-up ip route add default via 192.168.9.1 dev enp7s0 table 200
        post-up ip rule add from 192.168.9.6 lookup 200 priority 100
        post-up ip rule add to 192.168.9.6 lookup 200 priority 100
		# 确保从 192.168.9.6 发出的流量只使用 enp7s0
		# 发往 192.168.9.6 的流量只使用 enp7s0
		# 其他流量使用主路由表, 即通过 vmbr0/192.168.9.3

        # ARP和网络优化
		# 确保每个网卡只响应发给自己 IP 的 ARP 请求
        post-up echo 1 > /proc/sys/net/ipv4/conf/enp7s0/arp_filter
		# 只响应目标 IP 匹配的 ARP 请求
        post-up echo 2 > /proc/sys/net/ipv4/conf/enp7s0/rp_filter
		# 使用更严格的 ARP 通告策略
        post-up echo 1 > /proc/sys/net/ipv4/conf/enp7s0/arp_announce
        post-up echo 2 > /proc/sys/net/ipv4/conf/enp7s0/arp_ignore

        # 网络性能优化, tso: TCP 分段卸载, gso: 通用分段卸载, gro: 通用接收卸载
        post-up ethtool -K enp7s0 tso on gso on gro on

        # 清理接口关闭时的配置
        pre-down ip rule del from 192.168.9.6 lookup 200 priority 100
        pre-down ip rule del to 192.168.9.6 lookup 200 priority 100

source /etc/network/interfaces.d/*
```

然后修改系统 ipv4 吞吐性能 `vim /etc/sysctl.d/99-network-tuning.conf`：

```ini
# 基本网络优化
net.ipv4.tcp_timestamps = 1
net.ipv4.tcp_sack = 1

# 缓冲区优化
net.core.rmem_max = 16777216
net.core.wmem_max = 16777216
net.ipv4.tcp_rmem = 4096 87380 16777216
net.ipv4.tcp_wmem = 4096 65536 16777216

# TCP优化
net.ipv4.tcp_mtu_probing = 1
net.ipv4.tcp_window_scaling = 1
net.ipv4.tcp_slow_start_after_idle = 0

# 网络接口优化
net.core.netdev_max_backlog = 5000
```

修改完成后应用网络配置 `sysctl -p /etc/sysctl.d/99-network-tuning.conf`，重启网络 `systemctl restart networking`

通过以上配置，实现了：

- 完全隔离了两个网卡的流量路由
- 避免了 ARP 响应冲突
- 保持了 2.5G 网卡的独立带宽优势
- 优化了网络性能

#### 虚拟机直通

就是通过 pve 创建虚拟机，然后 enp7s0 直通给虚拟机就行，这么做就是把虚拟机抽象出来成为局域网的成员，两个不同的 Linux 内核管理两个不同的路由，自然不会风暴了

#### 配置不同子网

将 enp7s0 配置成不同的子网

```ini
iface enp7s0 inet static
        address 192.168.10.1/24
```

按照这么配置，带来以下问题：

1. 需要在主路由中配置相应的静态路由
2. 所有其他 192.168.9.0/24 的设备都需要添加一条到 192.168.10.0/24 的路由：`ip route add 192.168.10.0/24 via 192.168.9.1 dev IFNAME`

### 已安装虚拟机扩容

1. 在对应虚拟机的硬件选项中，调整要扩容的大小
2. （unix）开机，在系统中操作：

    1. 检查可用空间

        ```bash
        # 有 37G 的空间没有使用
        root@localhost:/opt# lsblk
        NAME        MAJ:MIN RM  SIZE RO TYPE MOUNTPOINTS
        sda           8:0    0  100G  0 disk 
        ├─sda1        8:1    0    1M  0 part 
        ├─sda2        8:2    0    1G  0 part /boot
        └─sda3        8:3    0   63G  0 part 
          ├─cs-root 253:0    0 39.7G  0 lvm  /
          ├─cs-swap 253:1    0  3.9G  0 lvm  [SWAP]
          └─cs-home 253:2    0 19.4G  0 lvm  /home

        root@localhost:/opt# fdisk -l /dev/sda
        GPT PMBR size mismatch (134217727 != 209715199) will be corrected by write.
        The backup GPT table is not on the end of the device.
        Disk /dev/sda: 100 GiB, 107374182400 bytes, 209715200 sectors
        Disk model: QEMU HARDDISK   
        Units: sectors of 1 * 512 = 512 bytes
        Sector size (logical/physical): 512 bytes / 512 bytes
        I/O size (minimum/optimal): 512 bytes / 512 bytes
        Disklabel type: gpt
        Disk identifier: C855F641-408D-4DE7-91A7-E1C57429C47E

        Device       Start       End   Sectors Size Type
        /dev/sda1     2048      4095      2048   1M BIOS boot
        /dev/sda2     4096   2101247   2097152   1G Linux extended boot
        /dev/sda3  2101248 134215679 132114432  63G Linux LVM
        ```

        这里可以看到要扩容目标的类型是 lvm
    2. 创建新的分区：

        ```bash
        root@localhost:/opt# fdisk /dev/sda

        Welcome to fdisk (util-linux 2.40.2).
        Changes will remain in memory only, until you decide to write them.
        Be careful before using the write command.

        GPT PMBR size mismatch (134217727 != 209715199) will be corrected by write.
        The backup GPT table is not on the end of the device. This problem will be corrected by write.
        This disk is currently in use - repartitioning is probably a bad idea.
        It's recommended to umount all file systems, and swapoff all swap
        partitions on this disk.

        # 新建分区
        Command (m for help): n
        # 回车默认最新的
        Partition number (4-128, default 4): 
        # 回车默认制定扇区的起始和结束地址
        First sector (134215680-209715166, default 134215680): 
        Last sector, +/-sectors or +/-size{K,M,G,T,P} (134215680-209715166, default 209713151): 

        Created a new partition 4 of type 'Linux filesystem' and of size 36 GiB.

        # 修改新分区类型为 lvm
        Command (m for help): t
        Partition number (1-4, default 4): 4
        # lvm alias for Linux LVM
        Partition type or alias (type L to list all): lvm

        Changed type of partition 'Linux filesystem' to 'Linux LVM'.

        # 保存更改
        Command (m for help): w
        The partition table has been altered.
        Syncing disks.
        ```
    3. 通知内核分区表变化：`partprobe`
    4. 创建物理卷：`pvcreate /dev/sda4`，这里 4 是上面对应创建的新分区号
    5. 将新物理卷添加到现有卷：`vgextend cs /dev/sda4`
    6. 此时输入 `vgdisplay cs` 可以检查是否出现可用 `Free PE / Size`
    7. 扩容 `lvextend -l +100%FREE /dev/cs/root`
    8. 最后调整文件系统大小（可以通过 `df -T /` 查看自己是什么类型文件系统）：

        1. ext4 系统：`resize2fs /dev/cs/root`
        2. xfs_growfs 系统（此处 lvm 就是）：`xfs_growfs /dev/cs/root`
    9. （可选）有的虚拟机用的 ext4，不支持动态扩容，需要手动操作：

        1. 关闭交换分区：`swapoff /dev/sda5`
        2. 在 fdisk 中操作

            ```bash
            fdisk /dev/sda
            ## 1. 删除所有分区（按顺序）
            d 5    # 删除交换分区
            d 2    # 删除扩展分区
            d 1    # 删除主分区
            ## 2. 创建新的主分区（根分区）
            n
            p    # 主分区
            1    # 分区号1
            回车  # 使用默认起始扇区 (2048)
            +28G # 分配28GB给根分区
            ## 3. 创建交换分区
            n
            p    # 主分区
            2    # 分区号2
            回车  # 使用默认起始扇区
            回车  # 使用剩余所有空间
            ## 4. 设置分区类型
            t    # 改变分区类型
            2    # 选择分区2
            82   # 设置为Linux swap类型
            ## 5. 查看分区表确认
            p
            ## 6. 写入更改
            w
            ```
        3. 重新加载分区表：`partprobe /dev/sda`
        4. 扩展文件系统和设置交换

            1. 扩展根文件系统：`resize2fs /dev/sda1`
            2. 创建交换文件系统：`mkswap /dev/sda2`
            3. 启用交换分区：`swapon /dev/sda2`
            4. 验证结果：`lsblk`
        5. 更新 fstab 文件：`genfstab -U / > /etc/fstab`
    10.

### 配置 fail2ban

通过 fail2ban 服务，保护 pve 的 ssh、web、smb 服务

1. `apt update && apt install fail2ban`
2. `cp /etc/fail2ban/jail.conf /etc/fail2ban/jail.local`，就用这个默认配置即可，也可以参考以下：

    ```ini
    # PVE fail2ban 配置文件 - 纯systemd journal
    # 放置在 /etc/fail2ban/jail.local

    [DEFAULT]
    # 忽略的IP地址（请根据你的网络环境修改）
    ignoreip = 127.0.0.1/8 ::1 192.168.0.0/16 10.0.0.0/8 172.16.0.0/12

    # 禁止IP的时间（秒）
    bantime = 3600

    # 监控时间窗口（秒）
    findtime = 600

    # 最大尝试次数
    maxretry = 5

    # 默认禁止动作
    banaction = iptables-multiport

    #
    # SSH 保护 - 使用systemd journal
    #
    [sshd]
    enabled = true
    port = 22
    filter = sshd
    backend = systemd
    journalmatch = _SYSTEMD_UNIT=ssh.service
    maxretry = 3
    bantime = 7200
    findtime = 600

    #
    # Proxmox Web 界面保护 (8006端口)
    #
    [proxmox]
    enabled = true
    port = 8006
    filter = proxmox
    backend = systemd
    journalmatch = _SYSTEMD_UNIT=pvedaemon.service + _SYSTEMD_UNIT=pveproxy.service
    maxretry = 3
    bantime = 3600
    findtime = 600

    #
    # SMB/CIFS 保护
    #
    [samba]
    enabled = true
    port = netbios-ns,netbios-dgm,netbios-ssn,microsoft-ds
    filter = samba
    backend = systemd
    journalmatch = _SYSTEMD_UNIT=smbd.service + _SYSTEMD_UNIT=nmbd.service
    maxretry = 3
    bantime = 3600
    findtime = 600
    ```
3. 然后配置 pve、smb 的 filter 文件：

    ```ini
    # Proxmox fail2ban 过滤器 - systemd journal版本
    # 保存为 /etc/fail2ban/filter.d/proxmox.conf

    [Definition]
    # 匹配 Proxmox VE 认证失败的日志模式
    failregex = pvedaemon\[.*\]: authentication failure; rhost=<HOST> user=.* msg=.*
                pveproxy\[.*\]: authentication failure; rhost=<HOST> user=.* msg=.*
                pvedaemon.*: authentication failure; rhost=<HOST>
                pveproxy.*: authentication failure; rhost=<HOST>

    # 忽略的正则表达式  
    ignoreregex =

    [Init]
    # systemd journal 配置
    journalmatch = _SYSTEMD_UNIT=pvedaemon.service + _SYSTEMD_UNIT=pveproxy.service

    ```

    ```ini
    # Samba fail2ban 过滤器 - systemd journal版本
    # 保存为 /etc/fail2ban/filter.d/samba.conf

    [Definition]
    # 匹配 Samba 认证失败的日志模式
    failregex = smbd\[.*\]: .*failed to authenticate.*from <HOST>
                smbd\[.*\]: .*authentication for user .* from <HOST> failed
                smbd\[.*\]: .*Authentication failed for user .* from <HOST>
                smbd.*: .*failed to authenticate.*from <HOST>
                smbd.*: .*authentication.*failed.*<HOST>

    # 忽略的正则表达式
    ignoreregex =

    [Init]
    # systemd journal 配置
    journalmatch = _SYSTEMD_UNIT=smbd.service + _SYSTEMD_UNIT=nmbd.service
    ```
4. 然后 `systemctl enable fail2ban.service --now` 开机自启动，`fail2ban-client -t` 用于测试配置是否成功
5. 使用

    1. 手动测试能否正常封禁：`fail2ban-client set proxmox banip 192.168.9.2`、`fail2ban-client set proxmox unbanip 192.168.9.2`
    2. 查看规则的状态：`fail2ban-client status proxmox`

### 硬盘迁移的识别

有一种情况，即从别处拆下来的移动硬盘，其中装载了系统，想要在 pve 中，以一个空虚拟机使用该硬盘的方式来实现迁移。

1. 首先按照正常操作添加虚拟机、添加硬盘直通、选择启动顺序，查看是否可以正常启动这个虚拟机
2. 若无法启动，可以参考下面的解决方案（在 PVE 上操作）：

    ```bash
    # lsblk
    NAME                 MAJ:MIN RM   SIZE RO TYPE MOUNTPOINTS
    sda                    8:0    0   1.8T  0 disk
    ├─sda1                 8:1    0     1M  0 part
    ├─sda2                 8:2    0   200M  0 part
    ├─sda3                 8:3    0     1G  0 part
    ├─sda4                 8:4    0     1K  0 part
    └─sda5                 8:5    0   1.7T  0 part
      └─rootvg01-lv01    252:0    0   1.7T  0 lvm

    # 扫描、启用新的盘
    vgscan
    vgchange -ay rootvg01

    mount /dev/mapper/rootvg01-lv01 /mnt/root --mkdir
    mount /dev/sda2 /mnt/root/boot
    mount --bind /dev /mnt/root/dev
    mount --bind /proc /mnt/root/proc
    mount --bind /sys /mnt/root/sys

    chroot /mnt/root/ bash
    cp -r /boot/grub2 /boot/grub2.backup

    grub2-install --target=i386-pc /dev/sda
    grub2-mkconfig -o /boot/grub2/grub.cfg
    ```
3. 一些比较旧的系统，不支持 UEFI，换成 SeaBIOS 即可

### 手动导入 iso

有一种情况，即通过 ftp、wget 直接在 pve 上下载了 iso 文件，而不是在 web 中上传，可以手动导入该 iso：

1. `cp xxx.iso /var/lib/vz/template/iso/`
2. `chmod 644 /var/lib/vz/template/iso/xxx.iso`

### 导入 vmware 虚拟机

1. 创建空的虚拟机：`qm create 101 --name "VM Name" --memory 1024 --cores 1 --sockets 1 --net0 virtio,bridge=vmbr0 --scsihw virtio-scsi-pci --ostype l26`
2. 将 vmdx 分片合并转换成单个文件：`qemu-img convert -f vmdk CentOS7.7-base-cl2.vmdk -O vmdk vm-full.vmdk`
3. `qm importvm 101 vm-full.vmdk local-lvm --format vmdk`，导入成功后会显示生成的卷 ID：`unused0:local-lvm:vm-101-disk-0`
4. 挂载磁盘到 IDE 总线：`qm set 101 --ide0 local-lvm:vm-101-disk-0`

如果虚拟机是 SCSI 硬盘，需要手动调整硬盘类型，一般是设置成 IDE 模式

导入选择快照问题

## refer

1. https://post.smzdm.com/p/a7nd00ql/
2. https://zahui.fan/posts/cfedbd03/
3. https://mdnice.com/writing/1e33dbfdbbab4fbeba0d4a4632d0208a
4. https://www.cnblogs.com/varden/p/15246180.html
5. https://www.orcy.net.cn/185.html
6. https://foxi.buduanwang.vip/virtualization/pve/561.html/
7. https://pve.proxmox.com/wiki/PCI_Passthrough


[pve.drawio](assets/pve-20250305005915-75pxsp8.drawio)

[装机.zip](assets/装机-20250313002051-ge0xleh.zip)