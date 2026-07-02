# -*- coding: utf-8 -*-

import argparse
from scapy.all import sniff, TCP, UDP
import netifaces

# 设置命令行参数
ap = argparse.ArgumentParser(description='tcpdump implementation using Scapy')
ap.add_argument('-p', '--port', type=int, required=True, help='指定监听端口')
ap.add_argument('-i', '--interface', nargs='*', help='指定监听的网卡')
ap.add_argument('-4', '--address', type=str, help='或者指定监听的地址')
args = vars(ap.parse_args())

if args['interface'] and args['address']:
    assert False, "dont use --address and --interface at the same time"

def get_interfaces_by_ip(ip_address):
    interfaces = []
    for interface in netifaces.interfaces():
        addrs = netifaces.ifaddresses(interface)
        if netifaces.AF_INET in addrs:
            for addr_info in addrs[netifaces.AF_INET]:
                if addr_info['addr'] == ip_address:
                    interfaces.append(interface)
    return interfaces

def packet_callback(packet):
    if (TCP in packet or UDP in packet) and (packet[TCP].dport == args['port'] or packet[UDP].dport == args['port']):
        print(packet.summary())

if args['address']:
    if args['address'] == '0.0.0.0':
        interfaces = netifaces.interfaces()
    else:
        interfaces = get_interfaces_by_ip(args['address']) 
        if not interfaces:
            print("No interfaces found with IP address {}".format(args['address']))
            exit(1)
elif args['interface']:
    interfaces = args['interface']
else:
    interfaces = netifaces.interfaces()

print("Listening on interfaces: {}, port {}".format(interfaces, args['port']))
for iface in interfaces:
    try:
        sniff(
            prn=lambda x: print(x.summary()), 
            store=False, 
            iface=iface, 
            filter="tcp or udp and port {}".format(args['port'])
        )
    except OSError as e:
        print(e)