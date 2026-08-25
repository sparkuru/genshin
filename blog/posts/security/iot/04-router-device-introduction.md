---
title: "iot-router-device-introduction"
description: "都说路由器是最好的 iot 安全入门设备"
date: "2024-01-14T10:09:00.000Z"
updated: "2024-08-20T02:28:50.000Z"
tags: []
draft: false
layout: "post"
slug: "router-device-introduction"
source: "online/01-iot.md#04-router-device-introduction"
---

## Router device introduction

## introduction

路由器，是比较容易接触到的智能设备，路由器的挖掘有：

-   从路由器的 web 管理界面下手，从登录界面开始就找什么弱口令、注入之类的，进去后还有命令执行、越权之类的，比起要用到逆向的知识，这更像是渗透或者 web 手做的事情
-   通过 binwalk 对 flash rom 处理提取出固件，再对固件展开逆向分析

## components

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

## references

1.   [智能设备漏洞挖掘中几个突破点](https://bbs.kanxue.com/thread-230095.html)
2.
