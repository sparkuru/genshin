#/usr/bin/env zsh

index=10
app_name=gtfobins
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