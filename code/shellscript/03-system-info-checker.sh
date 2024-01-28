#!/bin/sh

#region
white='\033[0m'
green='\033[0;32m'
blue='\033[0;34m'
red='\033[31m'
yellow='\033[33m'
grey='\e[37m'
pink='\033[38;5;218m'
cyan='\033[96m'
#endregion

# 1. system
# region

system_info() {

    clear

    ipv4_address=$(curl -s --max-time 1 ipv4.ip.sb)
    ipv6_address=$(curl -s --max-time 1 ipv6.ip.sb)
    cpu_info=$(lscpu | awk -F': +' '/Model name:/ {print $2; exit}')
    cpu_usage_percent=$(awk '{u=$2+$4; t=$2+$4+$5; if (NR==1){u1=u; t1=t;} else printf "%.0f\n", (($2+$4-u1) * 100 / (t-t1))}' \
        <(grep 'cpu ' /proc/stat) <(sleep 1; grep 'cpu ' /proc/stat))

    cpu_cores=$(nproc)
    mem_info=$(free -b | awk 'NR==2{printf "%.2f/%.2f MB (%.2f%%)", $3/1024/1024, $2/1024/1024, $3*100/$2}')
    disk_info=$(df -h | awk '$NF=="/"{printf "%s/%s (%s)", $3, $2, $5}')
    ipinfo=$(curl -s ipinfo.io)
    country=$(echo "$ipinfo" | grep 'country' | awk -F': ' '{print $2}' | tr -d '",')
    city=$(echo "$ipinfo" | grep 'city' | awk -F': ' '{print $2}' | tr -d '",')
    isp_info=$(echo "$ipinfo" | grep 'org' | awk -F': ' '{print $2}' | tr -d '",')
    cpu_arch=$(uname -m)
    hostname=$(hostname)
    kernel_version=$(uname -r)
    congestion_algorithm=$(sysctl -n net.ipv4.tcp_congestion_control)
    queue_algorithm=$(sysctl -n net.core.default_qdisc)
    os_info=$(grep PRETTY_NAME /etc/os-release | cut -d '=' -f2 | tr -d '"')
    output=$(awk 'BEGIN { rx_total = 0; tx_total = 0 }
        NR > 2 { rx_total += $2; tx_total += $10 }
        END {
            rx_units = "Bytes";
            tx_units = "Bytes";
            if (rx_total > 1024) { rx_total /= 1024; rx_units = "KB"; }
            if (rx_total > 1024) { rx_total /= 1024; rx_units = "MB"; }
            if (rx_total > 1024) { rx_total /= 1024; rx_units = "GB"; }

            if (tx_total > 1024) { tx_total /= 1024; tx_units = "KB"; }
            if (tx_total > 1024) { tx_total /= 1024; tx_units = "MB"; }
            if (tx_total > 1024) { tx_total /= 1024; tx_units = "GB"; }

            printf("总接收: %.2f %s\n总发送: %.2f %s\n", rx_total, rx_units, tx_total, tx_units);
        }' /proc/net/dev)

    current_time=$(date "+%Y-%m-%d %I:%M %p")
    swap_info=$(free -m | awk 'NR==3{used=$3; total=$2; if (total == 0) {percentage=0} else {percentage=used*100/total}; printf "%dMB/%dMB (%d%%)", used, total, percentage}')
    runtime=$(cat /proc/uptime | awk -F. '{run_days=int($1 / 86400);run_hours=int(($1 % 86400) / 3600);run_minutes=int(($1 % 3600) / 60); if (run_days > 0) printf("%d天 ", run_days); if (run_hours > 0) printf("%d时 ", run_hours); printf("%d分\n", run_minutes)}')
    timezone=$(timedatectl | grep "Time zone" | awk '{print $3}')


    echo ""
    echo "系统信息查询"
    echo -e "${pink}============机器信息============${white}"
    echo "主机名: $hostname"
    echo "运营商: $isp_info"
    echo -e "${pink}============版本信息============${white}"
    echo "系统版本: $os_info"
    echo "Linux版本: $kernel_version"
    echo -e "${pink}============CPU 信息============${white}"
    echo "CPU架构: $cpu_arch"
    echo "CPU型号: $cpu_info"
    echo "CPU核心数: $cpu_cores"
    echo -e "${pink}============占用信息============${white}"
    echo "CPU占用: $cpu_usage_percent%"
    echo "物理内存: $mem_info"
    echo "虚拟内存: $swap_info"
    echo "硬盘占用: $disk_info"
    echo -e "${pink}============流量信息============${white}"
    echo "$output"
    echo -e "${pink}============算法信息============${white}"
    echo "网络拥堵算法: $congestion_algorithm $queue_algorithm"
    echo -e "${pink}============ IP 信息============${white}"
    echo "公网IPv4地址: $ipv4_address"
    echo "公网IPv6地址: $ipv6_address"
    echo -e "${pink}============时区信息============${white}"
    echo "地理位置: $country $city"
    echo "系统时区: $timezone"
    echo "系统时间: $current_time"
    echo -e "${pink}============运行时长============${white}"
    echo "系统运行时长: $runtime"
    echo

}
# endregion

system_info