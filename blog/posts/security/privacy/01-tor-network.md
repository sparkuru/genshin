---
title: tor-network
date: 2026-10-13
description: tor network and darkweb.
noindex: false
firefly:
  markers: []
draft: true
layout: post
presentation: firefly
contentTheme: default
license: CC-BY-NC-4.0
access:
  visibility: public
---

# introducing to TOR network

## 原理

已知一对公私钥：公钥可以加密、私钥可以解密。

有 a、e 两个端点分别代表本机（客户端）、目标网站（`xxx.onion`），B、C（C1、C2、Cx）、D 代表 tor 网络里的节点。

连接路径：a > B > C > Cx ... > D > e，B 称为 guard，只有他知道你的 ip 地址（或者说机场的地址）。a 想要连接 tor 网络访问某个 onion 网站时，会经历如下步骤：

1. a 先连接网桥，该网桥就是一条从 a > ... > e 的路径（由洋葱浏览器从 tor 中继网络中随机选择 3 个及以上的节点），获取 B、Cx、D 的公钥 pk-x，然后 `pk-D( pk-Cx( pk-B( packet-frame-a ) ) )` 一层一层包着 a 真正发送的数据

## 注意事项

下面视频参考里面已经讲的很清楚了，这里列出一些可能会遇到的问题：

1. 个人尝试了 3 个机场，都开了流量嗅探，或是直接禁止了 tor 网络的连接，通过他们去访问 tor 网桥是没办法了，最后是通过自建阿里云香港 vps 才连接上的网桥，慢得可以。
2. onion 上的网站基本都要搞很多人机验证，挺唐的，但是隐蔽性可以，基本都是直接注册，记一个恢复码。

## refer

1. [【黑暗网络】最详细进入暗网方法大全，互联网中的罪恶都市，什么是暗网？暗网有多恐怖？Tor网络和黑暗网站的区别|dark web，windows/mac/linux/ios/android进入洋葱网络](https://www.youtube.com/watch?v=W0o9CpcSIyU&t=921s)