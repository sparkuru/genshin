#!/bin/bash

workdir=$(cd $(dirname $0); pwd)

mount_point=(
    "4BCFEC67674D8E07:/media/wkyuu/windows/c"
    "502996621F78DAE0:/media/wkyuu/windows/d"
)

uid=$(id -u $USER)
gid=$(id -g $USER)

for mount_point in "${mount_point[@]}"; do
    UUID=$(echo $mount_point | cut -d':' -f1)
    target_dir=$(echo $mount_point | cut -d':' -f2)
    echo "mount $UUID to $target_dir"
    sudo mount -t ntfs -o uid=$uid,gid=$gid -U $UUID $target_dir
done

# 1. 用 `sudo fidsk -l` 确定双系统情况下, windows 盘符的路径, 例如 /dev/nvme0n1p3, /dev/nvme0n1p4
# 2. 获取盘符的 UUID, `sudo blkid -s UUID -o value /dev/nvme0n1p3`, 例如 4BCFEC67674D8E07, 502996621F78DAE0
# 3. 用 `sudo mount -t ntfs -o uid=$(id -u wkyuu),gid=$(id -g wkyuu) -U $UUID $target_dir` 挂载
# 双系统下, 建议关闭 windows 的快速启动, 反正也没啥用