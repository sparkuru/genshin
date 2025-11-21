#!/bin/bash

#region
white='\033[0m'
green='\033[0;32m'
blue='\033[0;34m'
red='\033[31m'
yellow='\033[33m'
grey='\e[37m'
pink='\033[38;5;218m'
cyan='\033[96m'

# echo -e "${red}xxx${nc}"
nc='\033[0m'
#endregion

workdir=$(
    cd $(dirname $0)
    pwd
)

mount_point=(
    "504EC6424EC62098:/media/wkyuu/windows/c"
    "93BE384002291866:/media/wkyuu/windows/d"
)

uid=$(id -u $USER)
gid=$(id -g $USER)

for mount_point in "${mount_point[@]}"; do
    UUID=$(echo $mount_point | cut -d':' -f1)
    target_dir=$(echo $mount_point | cut -d':' -f2)
    if [[ ! -d $target_dir ]]; then
        mkdir -p $target_dir
    fi
    echo -e "mount ${green}$UUID${nc} to ${green}$target_dir${nc}"
    sudo mount -t ntfs -o uid=$uid,gid=$gid -U $UUID $target_dir
done

# 1. 用 `sudo fdisk -l` 确定双系统情况下, windows 盘符的路径, 例如 /dev/nvme0n1p3, /dev/nvme0n1p4
# 2. 获取盘符的 UUID, `sudo blkid -s UUID -o value /dev/nvme0n1p3`, 例如 4BCFEC67674D8E07, 502996621F78DAE0
# 3. 用 `sudo mount -t ntfs -o uid=$(id -u wkyuu),gid=$(id -g wkyuu) -U $UUID $target_dir` 挂载
# 双系统下, 建议关闭 windows 的快速启动, 反正也没啥用
