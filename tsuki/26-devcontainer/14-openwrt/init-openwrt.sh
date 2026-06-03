#/usr/bin/env zsh

index=14
app_name=openwrt
url=https://raw.githubusercontent.com/sparkuru/genshin/main/tsuki/26-devcontainer/$index-$app_name/$app_name.yml

create_dir() {
    if [ ! -d $1 ]; then
        mkdir -p $1
    fi
}

work_dir="$(cd -- "$(dirname -- "$0")" && pwd)"
file_path=$work_dir/$app_name.yml
if [ ! -f $file_path ]; then
    create_dir $work_dir/config
    curl -fLo $file_path $url
fi
