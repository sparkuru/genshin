# dhcp delivery

如果目标设备支持 dhcp, 可以通过网线直连目标设备, 让测试机本身提供 dhcp 服务实现网络发现

## dnsmasq

快速搭建服务, 这个最简单

1. `sudo apt update`
2. `sudo apt install dnsmasq`

配置文件 `sudo vim /etc/dnsmasq.conf`：

```ini
interface=enp2s0
dhcp-range=192.168.9.100,192.168.9.200,12h
dhcp-option=3,8.8.8.8
dhcp-option=6,8.8.8.8
```

启动服务 `sudo systemctl start dnsmasq`

## isc-dhcp-server

通过 isc-dhcp-server 实现 dhcp 分发, 

1. `sudo apt update`
2. `sudo apt install isc-dhcp-server`

写一个最小配置文件 `sudo vim /etc/dhcp/dhcpd.conf`

```ini
default-lease-time 600;
max-lease-time 7200;
authoritative;

option domain-name "vxworks-router.lan";
option domain-name-servers 8.8.8.8, 223.5.5.5;

subnet 192.168.9.0 netmask 255.255.255.0 {
    range 192.168.9.100 192.168.9.200;
    option routers 192.168.9.1;
    option subnet-mask 255.255.255.0;
    option domain-name-servers 8.8.8.8;
}
```

配置 `/etc/default/isc-dhcp-server` 指定接口

```ini
INTERFACESv4="enp2s0";
# 如果不需要 ipv6, 可以配置为 ""
INTERFACESv6="";
```

`sudo systemctl start isc-dhcp-server`
