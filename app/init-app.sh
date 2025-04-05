#!/usr/bin/env zsh

create_dir() {
    if [ ! -d $1 ]; then
        mkdir -p $1
    fi
}

app=(
    ddns-go 
    alist 
    qbittorrent 
    synctv 
    transfersh 
    hedgedoc 
    outline 
    reference 
    cyberchef 
    gtfobins 
    explainshell 
    hastebin
    drawio
    openwebui
    matrix
    chromium
    redroid
)

app_length=${#app[@]}
url_base=https://raw.githubusercontent.com/shi9uma/genshin/main/app
work_dir=$(dirname $0)

for index in $(seq -f "%02g" 1 $app_length); do
    app_name=${app[$index]}
    echo $app_name
done

for index in $(seq -f "%02g" 1 $app_length); do
    app_name=${app[$index]}

    app_dir=$work_dir/$index-$app_name
    if [ ! -d $app_dir ]; then
        create_dir $app_dir
    fi


    init_file_name="init-$app_name.sh"
    init_file_path=$app_dir/$init_file_name
    url=$url_base/$index-$app_name/$init_file_name
    if [ ! -f $app_dir/$init_file_name ]; then
        curl -fLo $init_file_path $url
        chmod +x $init_file_path
        eval $init_file_path
    fi
done