---
title: OWN YOUR ANDROID
date: 2026-09-15
description: from zygote/art/classloader to native.
noindex: false
tags:
  - android
  - zygote
firefly:
  markers: []
draft: true
layout: post
presentation: firefly
access:
  visibility: public
---

# OWN YOUR ANDROID

不喜欢 oplus 等国产安卓系统内部的遥测、数据收集、分析行为，

考虑从以下几种方式处理

1. 通过 cfa 的 rule 规则限制相关 domain 联网；
2. 通过 root 防火墙限制联网
3. 通过 LSPosed 模块限制指定包的行为
4. 通过内核模块，拦截、修改遥测的内容
5. Hook 掉系统的 system_server 或 app 厂商的 native 服务

涉及相关技术有

1. Android 系统机制、底层：
   1. Zygote、ART Hook、ClassLoader
   2. Binder IPC
   3. PasckageManager
   4. JobScheduler、AlarmManager
   5. WorkManager
   6. background、broadcast、provider
2. LSPosed
    1. java、kotlin
    2. xposed Legacy api、libxposed api
    3. 作用范围
    4. hook 方式：方法、构造函数、返回值劫持
    5. 进程的启动时机
    6. 多进程判断
3. Android 逆向
    1. 怎么查找任务、域名、接口、后台服务
    2. jadx、apktool、aapt2、cfr、unblob
    3. 混淆
    4. 壳
4. 网络控制
    1. iptables、nftables 防火墙
    2. netd 网络权限行为
    3. tcpdump、dumpsys netstats
    4. okhttp、urlconnection、cronet
    5. protobuf：zarja
    6. 内置 TLS、证书、QUIC/DoH 行为
5. Native
    1. c/cpp ndk
    2. dlopen、dlsym
    3. native fn hook
    4. 修改 libc 函数实现
    5. 厂商的 .so 和独立 native daemon 分析
6. magisk
    1. magisk 模块的结构、开发
    2. systemless overlay
    3. resetprop
    4. selinux 上下文
    5. magiskpolicy
    6. 模块禁用
    7. 救砖

