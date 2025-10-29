# 常用驱动

## general

1. cp210x：https://www.silabs.com/developer-tools/usb-to-uart-bridge-vcp-drivers?tab=downloads
2. Android MTK：https://mtkdriver.com/
3. 

## 紫光 sprd

1. SPD_Driver_R4.20.4201：https://androiddatahost.com/dsa6h

## yt6801 driver for linux kernel 6.16+.

get official driver here: https://www.motor-comm.com/product/ethernet-control-chip

if your kernel version is 6.16+, it might be error while `./yt_nic_install.sh`, then refer to this answer: https://aur.archlinux.org/packages/yt6801-dkms

usage like this:

```bash
$ cat << 'EOL' > /path/to/where/src/directory/in/yt6801-kernel-6.16.path
--- a/src/fuxi-gmac-net.c   2025-04-28 13:51:16.000000000 +0800
+++ b/src/fuxi-gmac-net.c   2025-08-14 23:12:32.145205587 +0800
@@ -772,7 +772,9 @@
 static void fxgmac_tx_hang_timer_handler(unsigned long data)
 #endif
 {
-#if (LINUX_VERSION_CODE >= KERNEL_VERSION(4,14,0))
+#if (LINUX_VERSION_CODE >= KERNEL_VERSION(6,16,0))
+    struct fxgmac_channel *channel = timer_container_of(channel, t, expansion.tx_hang_timer);
+#elif (LINUX_VERSION_CODE >= KERNEL_VERSION(4,14,0))
     struct fxgmac_channel *channel = from_timer(channel, t, expansion.tx_hang_timer);
 #else
     struct fxgmac_channel *channel = (struct fxgmac_channel *)data;
--- a/src/fuxi-gmac-phy.c   2025-04-28 13:51:16.000000000 +0800
+++ b/src/fuxi-gmac-phy.c   2025-08-14 23:18:43.972276438 +0800
@@ -322,7 +322,9 @@
 static void fxgmac_phy_link_poll(unsigned long data)
 #endif
 {
-#if (LINUX_VERSION_CODE >= KERNEL_VERSION(4,15,0))
+#if (LINUX_VERSION_CODE >= KERNEL_VERSION(6,16,0))
+    struct fxgmac_pdata *pdata = timer_container_of(pdata, t, expansion.phy_poll_tm);
+#elif (LINUX_VERSION_CODE >= KERNEL_VERSION(4,15,0))
     struct fxgmac_pdata *pdata = from_timer(pdata, t, expansion.phy_poll_tm);
 #else
     struct fxgmac_pdata *pdata = (struct fxgmac_pdata*)data;
@@ -350,7 +352,9 @@

 int fxgmac_phy_timer_init(struct fxgmac_pdata *pdata)
 {
-#if (LINUX_VERSION_CODE >= KERNEL_VERSION(4,15,0))
+#if (LINUX_VERSION_CODE >= KERNEL_VERSION(6,16,0))
+    timer_init_key(&pdata->expansion.phy_poll_tm, NULL, 0, "fuxi_phy_link_update_timer", NULL);
+#elif (LINUX_VERSION_CODE >= KERNEL_VERSION(4,15,0))
     init_timer_key(&pdata->expansion.phy_poll_tm, NULL, 0, "fuxi_phy_link_update_timer", NULL);
 #else
     init_timer_key(&pdata->expansion.phy_poll_tm, 0, "fuxi_phy_link_update_timer", NULL);
@@ -368,6 +372,10 @@

 void fxgmac_phy_timer_destroy(struct fxgmac_pdata *pdata)
 {
+#if (LINUX_VERSION_CODE >= KERNEL_VERSION(6,15,0))
+    timer_shutdown_sync(&pdata->expansion.phy_poll_tm);
+#else
     del_timer_sync(&pdata->expansion.phy_poll_tm);
+#endif
     DPRINTK("fxgmac_phy_timer removed\n");
 }
EOL

# tree like this
$ tree
.
├── yt6801-kernel-6.16.patch	# patch file here
├── log.txt
├── Makefile
├── README
├── src						# same level with src directory
│   ├── dkms.conf
│   ├── fuxi-dbg.h
│   ├── fuxi-efuse.c
│   ├── fuxi-efuse.h
│   ├── fuxi-errno.h
│   ├── fuxi-gmac-common.c
│   ├── fuxi-gmac-desc.c
│   ├── fuxi-gmac-ethtool.c
│   ├── fuxi-gmac.h
│   ├── fuxi-gmac-hw.c
│   ├── fuxi-gmac-ioctl.c
│   ├── fuxi-gmac-net.c
│   ├── fuxi-gmac-pci.c
│   ├── fuxi-gmac-phy.c
│   ├── fuxi-gmac-reg.h
│   ├── fuxi-os.h
│   ├── Makefile
│   ├── motorcomm
│   └── Notice.txt
└── yt_nic_install.sh

$ patch -p1 ./yt6801-kernel-6.16.patch
```




## 疑难杂症

1. 第三方inf不包含数字签名信息，https://blog.csdn.net/sinat_25683437/article/details/125301565