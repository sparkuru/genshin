---
title: "android | redmi-note-11tpro-plus-fash-LineageOS-record"
description: "小米系统开启 adb 安全调试功能需要联网并登陆小米账号。"
date: "2025-09-09T01:24:45.000Z"
tags: []
draft: false
layout: "post"
slug: "redmi-note-11t-pro-lineageos"
---

小米手机，开启 USB 调试（安全设置）需要联网并登陆小米账号，个人不能接受，解决方式可以参考 [不登陆小米账号启用 MIUI 的 ADB 调试（安全设置）和 ADB 应用安装（需 Root）](https://zhuanlan.zhihu.com/p/603628922)

**我这边打算直接给 redmi note 11tpro plus 刷 [LineageOS](https://zh.wikipedia.org/zh-sg/LineageOS)**

## 首先确定完成了以下准备

在继续之前，[请确保您已满足以下要求](https://wiki.itsvixano.me/)：

- 确保您的电脑已安装最新版本的 **ADB & Fastboot** 工具和 **Fastboot** 驱动程序
- 确保您的设备已解锁引导加载程序（bootloader）
- 确保您已备份手机上的 **所有数据**
- 这些版本支持 **OTA** 更新 Lineage
- **不支持** 自定义内核，**请勿** 刷入
- **只能** 使用 Lineage Recovery（LineageOS 恢复模式）来刷入 LineageOS（安装指南会告诉您如何刷入）

[下载](https://github.com/ItsVixano-releases/LineageOS_xaga.git) 对应版本的 lineageos rom，我的是 redmi note 11tpro ，其对应的是 xaga，则获取：

- `lineage-22.2-xxxxxxxx-UNOFFICIAL-xaga.zip`
- `boot.img`
- `vendor_boot.img`
- `dtbo.im`

先到 [官方页面](https://wiki.lineageos.org/devices/) 看看有没有自己设备的支持，如果没有就自己多找找设备对应的代号，然后用 `lineage_xxx` 一般可以很好找到

## （可选）GApps 支持

LineageOS 默认不包含 GApps（Google Apps add-on package），LineageOS 是一个开源项目，它的核心目标是提供一个纯净、安全、并且不包含任何闭源软件的 Android 版本，Google 的许多应用程序和服务，比如 Google Play 商店、Gmail、Google Maps 等都是闭源的，为了保持项目的开源性质，LineageOS 官方版本从一开始就决定不预装任何 Google 的专有软件

如果需要使用到 google 框架，需要在安装 lineageos 之前，先装上 gapps 支持，[参考 & 下载连接](https://wiki.itsvixano.me/gapps/)

由于上面使用的 lineageos 版本是 22.2，对应选择下载项中相应的 ARM64 版本 `MindTheGapps-15.0.0-arm64-xxxxxxxx_xxxxx.zip` 下载即可

## 安装 LineageOS

确保上面的准备工作都完成，相应的文件都下载好备用

这里需要分为三个步骤：

1. 刷入 LineageOS 的 recovery（刷写的主要的思想在 [readme](./readme.md) 里已经讨论过了，即通过 fastboot / recovery 刷入 img 文件）
2. 通过 LineageOS 的 recovery 侧载刷入 LineageOS
3. （可选）recovery 侧载刷入 GApps

操作简单如下： 

1. 通过 adb 重启设备到 fastboot 模式：`adb reboot fastboot`

2. 刷入三个分区

```bash
$ fastboot flash boot boot.img
Sending 'boot_a' (65536 KB)                        OKAY [  1.944s]
Writing 'boot_a'                                   OKAY [  0.116s]
Finished. Total time: 2.067s
                                                                                                                            
$ fastboot flash vendor_boot vendor_boot.img
Sending 'vendor_boot_a' (65536 KB)                 OKAY [  1.867s]
Writing 'vendor_boot_a'                            OKAY [  0.118s]
Finished. Total time: 1.989s
                                                                                                                      
$ fastboot flash dtbo dtbo.img
Sending 'dtbo_a' (84 KB)                           OKAY [  0.005s]
Writing 'dtbo_a'                                   OKAY [  0.002s]
Finished. Total time: 0.015s
```

  通过 fastboot 工具重启设备，进入到 recovery 模式：`fastboot reboot recovery`

4. 在 recovery 模式里

	1. 清空旧的数据，准备新的数据分区

		1. 点击 `Factory reset`
		2. 点击 `Format data/factory reset`
		3. 点击 `Format data`，下方会出现 `Data wipe complete`

	2. 然后左上角返回箭头，回到 HOME 界面

	3. 侧载 LineageOS 系统：

		1. 点击 `Apply update`

		2. 点击 `Apply from ADB`，此时 PC 上的 ADB 应该就能识别到设备了

		3. PC 上的 ADB 开始侧载 `adb sideload lineage-22.2-20250415-UNOFFICIAL-xaga.zip`，等待进度条完成，时间比较长，耐心等待即可

			1. 正常情况下会提示传输完成

			2. 有的情况下，会提示进度条卡在 47%，此时可以通过观察手机屏幕，如果此时出现了 recovery 界面，则表示安装成功了，而 PC 上可能会显示如下：

				```bash
				$ adb sideload lineage-22.2-20250415-UNOFFICIAL-xaga.zip    
				serving: 'lineage-22.2-20250415-UNOFFICIAL-xaga.zip'  (~47%)    
				adb: failed to read command: Success
				```

		4. 侧载完成，此时会弹出 recovery 界面，其提示重启到 recovery：如果需要安装 GApps，则选择 Yes；否则选择 No 即可正常开机

	4. 侧载 GApps.zip：

		1. 进入到 recovery HOME 后

		2. `Apply update` -> `Apply from ADB`

		3. 在 PC 上：`adb sideload ./MindTheGapps-15.0.0-arm64-20250812_214357.zip`，参考上面的侧载流程

			```bash
			$ adb sideload ./MindTheGapps-15.0.0-arm64-20250812_214357.zip 
			Total xfer: 1.00x
			```

到此流程结束，在 recovery HOME 里 `Reboot system now` 重启设备即可

至于后续的通过 magisk 来 root lineageos，和 readme 中提到的流程大致相似，使用上面的 boot.img 即可，特别注意，需要先到 设备 -> 关于本机 -> Build 号 按钮，点击多次以进入开发者模式

## refer

1. https://wiki.itsvixano.me/devices/xaga/
