---
title: "penetration | 20220421，一次简单的 wireshark 使用"
description: "wireshark，组网。"
date: "2022-04-21T12:43:00.000Z"
updated: "2024-02-21T12:12:47.000Z"
tags: []
draft: false
layout: "post"
slug: "wireshark-network-capture"
---

## 一次简单的wireshark抓包测试

~~水群~~发现有人推荐了一个在ios设备上看哔哩哔哩港澳台的app，在港区app store下的。
就还挺好奇，
就**我仅有的见识**来说，想要看港澳台肯定得有一个在那边的vps来做中转。
然后就是，如果有些哔哩哔哩港澳台要看4k的，带宽，流量这块，作为免费的app，服务商那边估计得够呛。
我还怀疑说是有人这么良心吗，白送的流量吗这不是，
如果我是国内厂商，那肯定得偷偷摸摸整点其他隐私数据发过去。
于是就有了这一次抓包测试。

## 环境

kali（VirtualBox），wireshark，iPhone

## 探测

在kali上 `$sudo wireshark` 打开wireshark，这里记得要把虚拟机中的kali桥接到网卡上，然后就是学校的无线AP做了隔离，所以推荐用自己的无线AP。

kali的ip是 `192.168.6.188`和本机windows 10是一个子网段的。
这里还需要找一下iPhone新的ip地址，这里在kali上用python打开了一个http服务，直接截取iPhone的访问ip。
`python3 http.server 1234 `，然后iPhone访问这个192.168.6.188:1234，就能获取iPhone的ip了。

![image-20220421203029403](https://tataramoriko-oss.oss-cn-shenzhen.aliyuncs.com/markdown/image-20220421203029403.png)

然后在wireshark中开始截取eth0的包，使用筛选器 `ip.addr==192.168.6.124`筛选iPhone的数据包，发现只抓得到IGMP组播策略和MDNS广播。

咨询了一下老师，抓eth0只是本机网卡，建议是用笔记本电脑开热点，再抓对应的子网。

开了个热点然后，并且ipconfig一下。

![image-20220421203427105](https://tataramoriko-oss.oss-cn-shenzhen.aliyuncs.com/markdown/image-20220421203427105.png)

---

![image-20220421202810898](https://tataramoriko-oss.oss-cn-shenzhen.aliyuncs.com/markdown/image-20220421202810898.png)

确定是本地连接10了，就用pc的wireshark（记得使用管理员模式打开）指定WLAN10连接（这里用kali就搜不到，只看得见107出来的，即windows10的网络访问）

![image-20220421203623069](https://tataramoriko-oss.oss-cn-shenzhen.aliyuncs.com/markdown/image-20220421203623069.png)

如图所示，确实能抓到iPhone出来的网路信息了。

![image-20220421202644040](https://tataramoriko-oss.oss-cn-shenzhen.aliyuncs.com/markdown/image-20220421205208936.png)

后续就是简单测试一下，在开启了《哔哔哈哈追番助手》之后，可以正常访问哔哩哔哩港澳台的片源了（对应在上图中就是连接到目标vps地址的数据包），网速还不错，然后在开着那个东西的情况下，刷QQ，网页啥的，不再产生新的连接数据。

居然真的有这么良心的app提供商吗。。。vps国际带宽不用钱吗。。被ban了之后要换一个ip地址还是挺麻烦的吧。

对于这个app，我的态度存疑，就目前来说，还没发现什么偷偷摸摸的行为。往后再看看吧。
