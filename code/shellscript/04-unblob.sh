#!/bin/bash

if [ $# -ne 1 ]; then
    echo "Usage: $0 <file_path>"
    exit 1
fi

if [ $(id | grep -c "docker") -eq 0 ]; then
    echo "you are not in docker group, add it by sudo usermod -aG docker $USER"
    exit 1
fi

if [ $(which docker 2>&1 > /dev/null; echo $?) -ne 0 ]; then
    echo "docker not found, or place it in /usr/bin/docker"
    exit 1
fi

file_path=$1
file_name=$(basename $file_path)

work_dir=$(pwd)
input_dir="$work_dir/input"
output_dir="$work_dir/output"
rootfs_dir="$work_dir/$file_name-rootfs"

check_dir() {
    if ! [ -d $1 ]; then
        mkdir -p $1
    fi
}

_rm() {
    if [ -e $1 ]; then
        rm -rf $1
    fi
}

_rm $input_dir
_rm $output_dir

check_dir $work_dir
check_dir $input_dir
check_dir $output_dir
check_dir $rootfs_dir

cp $file_path $input_dir
docker run \
  --rm \
  --pull always \
  -u $UID:$GID \
  -v $output_dir:/data/output \
  -v $input_dir:/data/input \
  ghcr.io/onekey-sec/unblob:latest "/data/input/$file_name"

mv $output_dir/"$file_name"_extract/* $rootfs_dir/
tar cf $file_name-rootfs.tar $file_name-rootfs

_rm $input_dir
_rm $output_dir

chown -R $UID:$GID $rootfs_dir $file_name-rootfs.tar