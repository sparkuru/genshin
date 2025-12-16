#!/usr/bin/env bash

index=20
app_name=wireguard-server
url=https://raw.githubusercontent.com/sparkuru/genshin/main/app/$index-$app_name/$app_name.yml

create_dir() {
    if [ ! -d $1 ]; then
        mkdir -p $1
    fi
}

work_dir=$(dirname $0)
file_path=$work_dir/$app_name.yml

if [ ! -f $file_path ]; then
    curl -fLo $file_path $url
fi

create_dir $work_dir/config
