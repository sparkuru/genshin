两种办法都搞一下：降级拿 ssh、uart 进 uboot 刷

## info

ChinaNet-k7cx / 4vs7cb93

192.168.2.1，n69k5fn6

## do

大致的流程如下：

1.   通过杜邦线进入 u-boot 的 TTL 终端
2.   从 TTL 读取内存信息并备份
3.   往 rootfs 刷入 openwrt 固件直接替换，设置 uboot 启动环境
4.   重启路由器，自动进入 openwrt

### 进入调试环境

1.   杜邦线接上 uart，串口改好，波特率改好 115200，putty 打开准备

2.   上电并长按 reset，在 putty 狂按任意按键，直到进入 uboot 的 TTL 命令窗口，查看版本信息如下：

     ```bash
     IPQ5018# version
     
     U-Boot 2016.01 (Nov 29 2023 - 13:59:38 +0000)
     arm-openwrt-linux-muslgnueabi-gcc (OpenWrt GCC 5.2.0 f586b1d+r49254) 5.2.0
     GNU ld (GNU Binutils) 2.24.0
     ```

3.   修改 boot 环境变量，方便后续调试

     1.   `setenv boot_wait on`
     2.   `setenv uart_en 1`
     3.   `saveenv`

     之后只需要通过 uart 和 putty 连接后，5s 内直接回车即可进入 TTL

### 备份文件

主要是备份 bdata，这里存的是

1.   下载 [tftpd64](https://bitbucket.org/phjounin/tftpd64/downloads/)，

2.   在 ttl 中：`printenv` 打印出系统信息，将其保存下来

     ```bash
     IPQ5018# printenv
     CountryCode=CN
     ISP_EI=182858442207206
     ISP_SN=5B1iS7BGxhoPC1700811256586FFMgCYwr
     SN=49584/K3V807206
     boot_wait=on
     bootargs=ubi.mtd=rootfs root=mtd:ubi_rootfs rootfstype=squashfs cnss2.bdf_integrated=0x23 cnss2.bdf_pci0=0x60 cnss2.bdf_pci1=0x60 cnss2.skip_radio_bmap=4 rootwait
     bootcmd=bootmiwifi
     bootdelay=5
     bootfile=miwifi_cr8809_firmware_b814a_6.2.102.bin
     color=101
     elink_en=1
     eth1addr=a4:a9:30:66:11:f8
     eth2addr=a4:a9:30:02:05:fd
     eth3addr=a4:a9:30:66:11:f8
     ethact=eth1
     ethaddr=a4:a9:30:2:5:fd
     ethprime=eth1
     fdt_high=0x4A400000
     fdtcontroladdr=4a9d4004
     fileaddr=44000000
     filesize=1b40414
     flag_boot_rootfs=0
     flag_boot_success=1
     flag_boot_type=2
     flag_last_success=0
     flag_ota_reboot=0
     flag_try_sys1_failed=0
     flag_try_sys2_failed=0
     flash_type=11
     fsbootargs=ubi.mtd=rootfs root=mtd:ubi_rootfs rootfstype=squashfs cnss2.bdf_integrated=0x23 cnss2.bdf_pci0=0x60 cnss2.bdf_pci1=0x60 cnss2.skip_radio_bmap=4
     gatewayip=192.168.31.1
     ipaddr=192.168.31.102
     machid=8040002
     mgtpsd=n69k5fn6
     mode=Router
     model=CR8819
     mtdids=nand0=nand0
     netmask=255.255.255.0
     no_wifi_dev_times=0
     rand_key=b
     rand_nonce=a
     restore_defaults=0
     security_level=0
     serverip=192.168.31.100
     soc_hw_version=20180101
     soc_version_major=1
     soc_version_minor=1
     ssh_en=0
     stderr=serial@78AF000
     stdin=serial@78AF000
     stdout=serial@78AF000
     telnet_en=0
     uart_en=1
     wifipsd=4vs7cb93
     wl0_radio=1
     wl0_ssid=ChinaNet-k7cx-5G
     wl1_radio=1
     wl1_ssid=ChinaNet-k7cx
     
     Environment size: 2932/65532 bytes
     ```

3.   使用 `smeminfo` 查看 bdata 数据：

     ```bash
     IPQ5018# smeminfo
     ubi0: attaching mtd1
     ubi0: scanning is finished
     ubi0: attached mtd1 (name "mtd=0", size 30 MiB)
     ubi0: PEB size: 131072 bytes (128 KiB), LEB size: 126976 bytes
     ubi0: min./max. I/O unit sizes: 2048/2048, sub-page size 2048
     ubi0: VID header offset: 2048 (aligned 2048), data offset: 4096
     ubi0: good PEBs: 240, bad PEBs: 0, corrupted PEBs: 0
     ubi0: user volume: 2, internal volumes: 1, max. volumes count: 128
     ubi0: max/mean erase counter: 1/0, WL threshold: 4096, image sequence number: 1034468636
     ubi0: available PEBs: 20, total reserved PEBs: 220, PEBs reserved for bad PEB handling: 20
     flash_type:             0xb
     flash_index:            0x0
     flash_chip_select:      0x0
     flash_block_size:       0x20000
     flash_density:          0x80000
     partition table offset  0x0
     No.: Name             Attributes            Start             Size
       0: 0:SBL1           0x0000ffff              0x0          0x80000
       1: 0:MIBIB          0x0000ffff          0x80000          0x80000
       2: 0:BOOTCONFIG     0x0000ffff         0x100000          0x40000
       3: 0:BOOTCONFIG1    0x0000ffff         0x140000          0x40000
       4: 0:QSEE           0x0000ffff         0x180000         0x100000
       5: 0:QSEE_1         0x0000ffff         0x280000         0x100000
       6: 0:DEVCFG         0x0000ffff         0x380000          0x40000
       7: 0:DEVCFG_1       0x0000ffff         0x3c0000          0x40000
       8: 0:CDT            0x0000ffff         0x400000          0x40000
       9: 0:CDT_1          0x0000ffff         0x440000          0x40000
      10: 0:APPSBLENV      0x0000ffff         0x480000          0x80000
      11: 0:APPSBL         0x0000ffff         0x500000         0x140000
      12: 0:APPSBL_1       0x0000ffff         0x640000         0x140000
      13: 0:ART            0x0000ffff         0x780000         0x100000
      14: 0:TRAINING       0x0000ffff         0x880000          0x80000
      15: bdata            0x0000ffff         0x900000          0x80000
      16: crash            0x0000ffff         0x980000          0x80000
      17: crash_syslog     0x0000ffff         0xa00000          0x80000
      18: rootfs           0x0000ffff         0xa80000        0x1e00000
             ubi vol 0 kernel
             ubi vol 1 ubi_rootfs
      19: rootfs_1         0x0000ffff        0x2880000        0x1e00000
      20: overlay          0x0000ffff        0x4680000        0x3980000
     ```

     则 bdata 数据在 `0x900000 ~ 0x900000 + 0x80000` 数据段，

4.   需要备份 bdata、rootfs、rootfs_1 这几个数据块（后两者是官方原厂固件，我这里是 `miwifi_cr8809_firmware_b814a_6.2.102.bin`，其实不用备份也行，可以从网上直接下载），在后期如果想刷回官方固件需要用到

     1.   

## wrt

选择的 wrt 固件是 [immortalwrt](https://github.com/immortalwrt/immortalwrt.git)

## refer

1.   https://github.com/NakanoSanku/StudyShare/blob/master/ax3000/ax3000-cr880x-SSH.md
2.   https://www.right.com.cn/forum/forum.php?mod=viewthread&tid=8255711&highlight=ttl&mobile=no
3.   https://www.blumia.net/2024/05/25/ax3000t-uboot-immortalwrt.html
4.   