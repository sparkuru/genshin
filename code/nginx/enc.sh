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

src_file_path="$workdir/04-trojan.http.nginx"
target_file_path="$workdir/04-trojan.http.nginx.enc"
# loop encrypt/decrypt if needed
src_file_dir="/path/to/src/file/dir"
target_file_dir="/path/to/target/file/dir"
loop_file_list=(
    "file1"
    "file2"
    "file3"
)

do_encrypt() {
    if [ -n "$encrypt_key" ]; then
        python $encrypt_script_path \
            -i $src_file_path \
            -o $target_file_path \
            -s $salt_path \
            -k "$encrypt_key" \
            enc
    else
        python $encrypt_script_path \
            -i $src_file_path \
            -o $target_file_path \
            -s $salt_path \
            enc
    fi
}
do_decrypt() {
    if [ -n "$encrypt_key" ]; then
        python $encrypt_script_path \
            -i $target_file_path \
            -o $src_file_path \
            -k "$encrypt_key" \
            dec
    else
        python $encrypt_script_path \
            -i $target_file_path \
            -o $src_file_path \
            dec
    fi
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
# sth to do after encrypt/decrypt
hook() {
    echo -e "hook: ${green}${hook}${nc}"
}

echo -e "workdir: ${green}${workdir}${nc}"
echo -e "genshin_dir_path: ${green}${genshin_dir_path}${nc}"

encrypt_key=""
while [[ $# -gt 0 ]]; do
    case $1 in
    -k | --key)
        encrypt_key="$2"
        shift 2
        ;;
    enc | dec | show)
        operation="$1"
        shift
        ;;
    *)
        echo "Unknown option: $1"
        echo "usage: $0 {enc|dec|show} [-k|--key <key>]"
        exit 1
        ;;
    esac
done

if [ -z "$operation" ]; then
    echo "usage: $0 {enc|dec|show} [-k|--key <key>]"
    exit 1
fi

case "$operation" in
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
    if [ -n "$encrypt_key" ]; then
        echo -e "encrypt_key: ${green}${encrypt_key}${nc}"
    else
        echo -e "encrypt_key: ${yellow}(not specified)${nc}"
    fi
    ;;
esac
