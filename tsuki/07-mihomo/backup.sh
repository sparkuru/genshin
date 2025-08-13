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

current_dir=$workdir
target_dir_name="03-genshin"
while [ "$current_dir" != "/" ]; do
    tmp_base_name=$(basename $current_dir)
    if [[ "$tmp_base_name" == "$target_dir_name" ]]; then
        genshin_dir_path=$current_dir
        break
    fi
    current_dir=$(dirname $current_dir)
done

if [ -z "$genshin_dir_path" ]; then
    echo "$target_dir_name directory not found"
    exit 1
fi

encrypt_script_path="$genshin_dir_path/code/python/02-ez-encrypt.py"
salt_path="$genshin_dir_path/paimon"

if [ -d "/d/software/mihomo-party" ]; then
    src_file_path="/d/software/mihomo-party/data/profiles/192281f8f10.yaml"
elif [ -d "/home/wkyuu/.config/mihomo-party" ]; then
    src_file_path="/home/wkyuu/.config/mihomo-party/profiles/magic.yaml"
else
    echo "${red}mihomo-party not found${nc}"
    exit 1
fi

target_file_path="$workdir/magic.yaml"
# loop encrypt/decrypt if needed
src_file_dir="/path/to/src/file/dir"
target_file_dir="/path/to/target/file/dir"
loop_file_list=(
    "file1"
    "file2"
    "file3"
)

if [ $# -eq 0 ]; then
    echo "usage: $0 {enc|dec|show}"
    exit 1
fi

do_encrypt() {
    python $encrypt_script_path \
        -i $src_file_path \
        -o $target_file_path \
        -s $salt_path \
        enc
}
do_decrypt() {
    python $encrypt_script_path \
        -i $target_file_path \
        -o $src_file_path \
        dec
}
do_encrypt_loop() {
    echo -e "encrypt src dir: ${green}${src_file_dir}${nc}"
    for file in "${loop_file_list[@]}"; do
        src_file_path="$src_file_dir/$file"
        target_file_path="$target_file_dir/$file"
        do_encrypt
    done
}
do_decrypt_loop() {
    echo -e "decrypt target dir: ${green}${target_file_dir}${nc}"
    for file in "${loop_file_list[@]}"; do
        src_file_path="$src_file_dir/$file"
        target_file_path="$target_file_dir/$file"
        do_decrypt
    done
}

echo -e "workdir: ${green}${workdir}${nc}"
echo -e "genshin_dir_path: ${green}${genshin_dir_path}${nc}"
case "$1" in
enc)
    do_encrypt
    # do_encrypt_loop
    ;;
dec)
    do_decrypt
    # do_decrypt_loop
    ;;
show)
    echo -e "encrypt_script_path: ${green}${encrypt_script_path}${nc}"
    echo -e "salt_path: ${green}${salt_path}${nc}"
    echo -e "src_file_path: ${green}${src_file_path}${nc}"
    echo -e "target_file_path: ${green}${target_file_path}${nc}"
    echo -e "src_file_dir: ${green}${src_file_dir}${nc}"
    echo -e "target_file_dir: ${green}${target_file_dir}${nc}"
    ;;
*)
    echo "usage: $0 {enc|dec|show}"
    ;;
esac
