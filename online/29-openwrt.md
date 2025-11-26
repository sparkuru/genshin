
选择 `immortalwrt-24.10.4-x86-64-generic-ext4-combined-efi.img.tar`

img.gz, qcow2, vdi, vhdx, vmdk 的区别

优先用带 efi 的，不然就是传统的 Legacy BIOS 启动


刷写：

```bash

# archiso

$ lsblk

$ mount /dev/sdc4 /mnt/sdc --mkdir

$ dd if=/path/to/immortalwrt-24.10.4-x86-64-generic-ext4-combined-efi.img of=/dev/sda bs=4M status=progress

```

系统配置：

可能会默认将 eth1 看作 wan，eth0 看作 lan

```bash

$ vi /etc/config/network
# 找到 config.interfacer wan 和 lan, 根据具体情况配置

$ service network restart

$ sed -e 's,https://downloads.immortalwrt.org,https://mirrors.cernet.edu.cn/immortalwrt,g' \
    -e 's,https://mirrors.vsean.net/openwrt,https://mirrors.cernet.edu.cn/immortalwrt,g' \
    -i.bak /etc/opkg/distfeeds.conf

$ opkg update

$ opkg install luci-compat; opkg install luci-lib-ipkg
$ wget --no-check-certificate https://github.com/jerrykuku/luci-theme-argon/releases/download/v2.3.1/luci-theme-argon_2.3.1_all.ipk -O luci-theme-argon_2.3.1_all.ipk
$ wget --no-check-certificate https://github.com/jerrykuku/luci-app-argon-config/releases/download/v0.9/luci-app-argon-config_0.9_all.ipk -O luci-app-argon-config_0.9_all.ipk
$ opkg install *.ipk

```