---
title: openwrt
date: 2026-09-23
description: flash immortalwrt in my cudy tr3000
noindex: false
tags:
  - openwrt
  - immortalwrt
  - cudy
firefly:
  markers: []
draft: false
layout: post
presentation: firefly
contentTheme: default
access:
  visibility: public
---

# openwrt

## luci

### firewall

终于看懂防火墙了

| 区域 → 转发                              | 入站数据 | 出站数据 | 转发 | IP 动态伪装 | MSS 钳制 |
| ------------------------------------ | ---- | ---- | -- | ------- | ------ |
| **lan: [lan] → wan / wan2lan / IoT** | 接受   | 接受   | 接受 |      |     |
| **wan: [wan6, wwan] → REJECT**       | 拒绝   | 接受   | 拒绝 | √     |     |
| **wan2lan: [wan] → wan**             | 接受   | 接受   | 接受 |      |     |
| **IoT: [IoT] → lan**                 | 接受   | 接受   | 接受 | √     |     |

如表格所示，用一个例子说明，以第一行为例：

- 区域名称为 lan，区域下有多个 lan 口设备 `[eth0, wlan0]`；区域是一个逻辑概念，多个不同区域，都可以包含 eth0
- 还有其他几个区域：`wan`、`wan2lan`、`IoT`
- 入站、出站、转发，都是 `accept`

这里应该这么看：

1. 区域名（Zone）为 lan，其中涵盖多个接口 `[eth0, wlan0]`
2. 入站，表示来自 lan `[eth0, wlan0]` 的流量，能否进入到 openwrt；典型例子就是 icmp 能否到达 openwrt
3. 出站，表示从 openwrt 出去的流量，能否到达 lan `[eth0, wlan0]`；典型例子就是，如果同时允许入站、出站，则 ping 有 request 和 reply，表现即为能 ping 通
4. 转发，是指来自 lan 区域中的接口 `[eth0, wlan0]` 的流量，是否能够被转发到 `wan`、`wan2lan`、`IoT` 区域中，对应的端口
5. IP 动态伪装，即 NAT
6. MSS，指可以自动适应不同 MTU 的一种机制







