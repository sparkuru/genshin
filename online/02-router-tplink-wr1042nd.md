# Analysis tplink wr1042ndv1

get firmware here：[TP-Link TL-WR1042NDv1 Router Firmware 130923](https://drivers.softpedia.com/get/Router-Switch-Access-Point/TP-Link/TP-Link-TL-WR1042NDv1-Router-Firmware-130923.shtml)；以 `$` 为宿主机，`$$` 为 guest 虚拟环境

## front

```bash
$ unzip TL-WR1042ND_V1_130923.zip
Archive:  TL-WR1042ND_V1_130923.zip
  inflating: wr1042nv1_en_3_15_7_up_boot(130923).bin

$ ls
 TL-WR1042ND_V1_130923.zip  'wr1042nv1_en_3_15_7_up_boot(130923).bin'

$ file wr1042nv1_en_3_15_7_up_boot\(130923\).bin
wr1042nv1_en_3_15_7_up_boot(130923).bin: firmware 1042 v1 TP-LINK Technologies ver. 1.0, version 3.15.7, 8258048 bytes or less, at 0x200 998400 bytes , at 0x100000 7077888 bytes

$ binwalk wr1042nv1_en_3_15_7_up_boot\(130923\).bin
DECIMAL       HEXADECIMAL     DESCRIPTION
--------------------------------------------------------------------------------
0             0x0             TP-Link firmware header, firmware version: 0.25336.3, image version: "", product ID: 0x0, product version: 272760833, kernel load address: 0x0, kernel entry point: 0x20000, kernel offset: 8258048, kernel length: 512, rootfs offset: 998400, rootfs length: 1048576, bootloader offset: 7077888, bootloader length: 0
5824          0x16C0          LZMA compressed data, properties: 0x5D, dictionary size: 8388608 bytes, uncompressed size: 72992 bytes
131584        0x20200         TP-Link firmware header, firmware version: 0.0.3, image version: "", product ID: 0x0, product version: 272760833, kernel load address: 0x0, kernel entry point: 0x20000, kernel offset: 8126464, kernel length: 512, rootfs offset: 998400, rootfs length: 1048576, bootloader offset: 7077888, bootloader length: 0
142344        0x22C08         LZMA compressed data, properties: 0x5D, dictionary size: 8388608 bytes, uncompressed size: 3100784 bytes
1180160       0x120200        Squashfs filesystem, little endian, version 4.0, compression:lzma, size: 2722564 bytes, 763 inodes, blocksize: 131072 bytes, created: 2013-09-23 07:39:23
```

使用 `dd if=wr1042nv1_en_3_15_7_up_boot\(130923\).bin bs=1 skip=1180160 of=output-rootfs.sqfs`，dd（data duplicator），if（input file），bs（block size，每次读几个字节），skip（从 offset 处开始），of（output file，选择导出一个后缀为 sqfs 的文件），sqfs（SquashFS）是一种只读文件系统，压缩率高，适用于嵌入式等其他需要高度压缩的场景；

使用 binwalk 可以发现除了 linux fs 还有一些 lzma 数据，则 `dd if=wr1042nv1_en_3_15_7_up_boot\(130923\).bin bs=1 skip=142344 count=$((1180160-142343)) of=output-rootfs.sqfs` 分段提取

对 output-rootfs.sqfs 进行分析，列出固件内容：`unsquashfs -l output-rootfs.sqfs`；提取固件：`sudo unsquashfs output-rootfs.sqfs`，也可以 `binwalk -Me wr1042nv1_en_3_15_7_up_boot\(130923\).bin`

## before front

```bash
$ sudo unsquashfs output-rootfs.sqfs
total 60K
drwxrwxr-x 15   501   502 4.0K Sep 23  2013 .
drwxr-xr-x  3 wkyuu wkyuu 4.0K Mar  1 12:51 ..
drwxrwxr-x  2   501   502 4.0K Sep 23  2013 bin
drwxrwxr-x  5   501   502 4.0K Sep 23  2013 dev
drwxrwxr-x  4   501   502 4.0K Sep 23  2013 etc
drwxrwxr-x  2   501   502 4.0K Sep 23  2013 home
lrwxrwxrwx  1   501   502   11 Sep 23  2013 init -> bin/busybox
drwxrwxr-x  3   501   502 4.0K Sep 23  2013 lib
lrwxrwxrwx  1   501   502   11 Sep 23  2013 linuxrc -> bin/busybox
drwxrwxr-x  2   501   502 4.0K Sep 23  2013 mnt
drwxrwxr-x  2   501   502 4.0K Sep 23  2013 proc
drwxrwxr-x  2   501   502 4.0K Sep 23  2013 sbin
drwxrwxr-x  2   501   502 4.0K Sep 23  2013 sys
drwxrwxr-x  2   501   502 4.0K Sep 23  2013 tmp
drwxrwxr-x  5   501   502 4.0K Sep 23  2013 usr
drwxrwxr-x  2   501   502 4.0K Sep 23  2013 var
drwxrwxr-x  9   501   502 4.0K Sep 23  2013 web
```

尝试看一下超级管理员的口令

```bash
$ cat ./etc/shadow
root:$1$$zdlNHiCDxYDfeF4MZL.H3/:10933:0:99999:7:::
Admin:$1$$zdlNHiCDxYDfeF4MZL.H3/:10933:0:99999:7:::
bin::10933:0:99999:7:::
daemon::10933:0:99999:7:::
adm::10933:0:99999:7:::
lp:*:10933:0:99999:7:::
sync:*:10933:0:99999:7:::
shutdown:*:10933:0:99999:7:::
halt:*:10933:0:99999:7:::
uucp:*:10933:0:99999:7:::
operator:*:10933:0:99999:7:::
nobody::10933:0:99999:7:::
ap71::10933:0:99999:7:::

$ john --wordlist=/usr/share/john/password.lst shadow
Warning: detected hash type "md5crypt", but the string is also recognized as "md5crypt-long"
Use the "--format=md5crypt-long" option to force loading these as that type instead
Using default input encoding: UTF-8
Loaded 1 password hash (md5crypt, crypt(3) $1$ (and variants) [MD5 256/256 AVX2 8x3])
No password hashes left to crack (see FAQ)

$ john --show shadow
root:5up:10933:0:99999:7:::
Admin:5up:10933:0:99999:7:::
bin:NO PASSWORD:10933:0:99999:7:::
daemon:NO PASSWORD:10933:0:99999:7:::
adm:NO PASSWORD:10933:0:99999:7:::
nobody:NO PASSWORD:10933:0:99999:7:::
ap71:NO PASSWORD:10933:0:99999:7:::

7 password hashes cracked, 0 left
```

检查一下有无可利用的 binary

```bash
$ file /bin/busybox
busybox: ELF 32-bit MSB executable, MIPS, MIPS-I version 1 (SYSV), dynamically linked, interpreter /lib/ld-uClibc.so.0, no section header
```

这是一个 mips 架构的 binary，需要使用模拟器来装载和使用，这里选择 [qemu]()，以 system 模式装载该固件：

```bash
$ sudo qemu-system-mips -M malta -append "root=/dev/sda1 console=tty0" -net nic -net tap,ifname=tap0,script=no,downscript=no -kernel vmlinux-3.2.0-4-4kc-malta -hda debian-mips-wheezy-standard.qcow2
$ tar -cvf firmware.tar squashfs-root
$ scp firmware.tar root@172.17.0.2:/root

$$ tar -xvf firmware.tar
$$ cd /root/squashfs-root
$$ chroot . bin/sh
busybox v1.01 built-in shell (msh)
Enter 'help' for a list of built-in commands.
$$ help
Build-in commands: break cd continue eval exec exit export help login newgrp read readonly set shift times trap umask wait
```

## not yet

破解出路由器的超管口令后，可以尝试在 shodan 之类测绘引擎中搜索该路由器并利用；亦或者修改路由器的 hash，再刷回路由器获取 root；再高级一点的，往往可以从固件中嗅探出源码，找到 api 密钥、互联网痕迹等信息

## main



## references

1.   [IoT hacking — Reversing a router firmware](https://kavigihan.medium.com/iot-hacking-reversing-a-router-firmware-df6e06cc0dc9)
2.   [john handbook](https://www.kali.org/tools/john/)
3.   [逆向分析工具 Ghidra 实战教程 以破解注册码题目为例介绍分析技巧和方法](https://www.bilibili.com/video/av865759744)
4.   