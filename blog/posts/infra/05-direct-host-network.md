---
title: "dev | connect-hosts-with-cables"
description: "使用一条网线连接多台主机的实现参考。"
date: "2023-08-13T10:23:54.000Z"
tags: []
draft: false
layout: "post"
slug: "direct-host-network"
---

## connect hosts with cables

>   使用一条网线连接多台主机的实现参考

假设环境：

1.   拥有一台主力工作机器，Windows
2.   备用生产机器，Ubuntu

平常需要在 Windows 下通过 ssh 连接到 Ubuntu，或者访问对应端口以测试环境，通过 WLAN 局域网时遇到用网高峰造成网速较慢，故尝试直接使用一条网线连接两台主机实现通信

## 实现方法

1.   使用线缆连接两台主机设备

2.   在 Windows 下进行如下设置：

     1.   网络和 Internet 设置 - 以太网 - 更改适配器选项；

     2.   找到 **以太网**，右键属性 - Internet 协议版本 4 - 属性，然后修改成如图所示配置

          ![](https://tataramoriko-oss.oss-cn-shenzhen.aliyuncs.com/markdown/image-20230813181047040.png)

          其中，

          1.   IP 地址项 不能和 默认网关项 相同
          2.   IP 地址项 和 默认网关项 的填写需要根据子网掩码的设置来配置（如果不知道如何配置，请直接按照图示分别改成 `192.168.a.x` 和 `192.168.a.y`，这里表示 a 项必须相同，这是由子网掩码决定的）

     3.   配置完成后确定

3.   在 Ubuntu 下进行如下设置

     1.   在 Ubuntu 打开终端，在 root 权限下配置网络设置：`sudo su`

     2.   确定网卡的接口名称，这里以 `enp3s0` 为例

     3.   修改 `/etc/network/interfaces` 文件如下

          ```ini
          auto enp3s0
          
          iface enp3s0 inet static
          address 192.168.7.3
          netmask 255.255.255.0
          ```

          其中，`netmask` 项必须和 Windows 下设置相同，address 项表示设定该 Ubuntu 的网络地址为 `192.168.7.3`

     4.   修改 `/etc/netplan/01-network-manager-all.yaml` 配置如下

          ```ini
          # Let NetworkManager manage all devices on this system
          network:
            version: 2
            renderer: NetworkManager
            ethernets:
              enp3s0:
                addresses: [192.168.7.3/24]
                gateway4: 192.168.7.1
          ```

          其中，`gateway4` 项必须和 Windows 下设置的网关地址相同

     5.   重启和应用网络服务：`systemctl restart NetworkManager.service`，`netplan apply`

4.   配置完成后，在 windows 下使用 `ping 192.168.7.3` 来测试能否 ping 通 ubuntu（使用 ubuntu ping windows 时，可能会因为 windows 的防火墙策略导致 ping 不通，但反过来限制就小得多）
