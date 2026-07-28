# os network bridge

## how to design a qemu network

主要有 3 种方式

1. 宿主机创建一个独立的 linux bridge: br-qemu，让多个 qemu 共用
2. 直接为每个 qemu 创建 tap 接口，然后接入到默认的 linux bridge
3. 接入到 docker0，本质上也是一个 linux bridge

## network interface

### tap

tap 主要工作在二层，传输的是以太网帧（包括 ipv4/6、各类二层协议）

tap 可以理解为用于接入 linux bridge 的接口

一个示例 linux bridge 如下

```bash
qemu-bridge
├── eth0
├── wlan0
├── tap1/
│   └── qemu1
├── tap2/
│   └── qemu2
└── ...
```

在这个 bridge 里，eth0、wlan0、tapX 之间可以将数据摆渡到 qemu-bridge "链路"上

但是 tap 不会真的连接到硬件层，而是一个用户态的网络设施，他可以处理完整的以太网帧

当宿主机通过 tap0 发送一个以太网帧时，链路是

```
linux 网络栈 -> tap0 -> QEMU -> 虚拟机网卡（子系统内部的 interface）
```

反向回包就是正好对称着来

### tun

tun 网卡主要工作在三层，即传输的是 ipv4/6 数据包