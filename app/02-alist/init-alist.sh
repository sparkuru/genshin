#/usr/bin/env zsh

index=02
app_name=alist
url=https://raw.githubusercontent.com/shi9uma/genshin/main/app/$index-$app_name/$app_name.yml

create_dir() {
    if [ ! -d $1 ]; then
        mkdir -p $1
    fi
}

work_dir=$(dirname $0)
file_path=$work_dir/$app_name.yml
if [ ! -f $file_path ]; then
    create_dir $work_dir/data
    create_dir $work_dir/nas/nas-storage
    create_dir $work_dir/nas/nas-torrent
    curl -fLo $file_path $url
fi

# sudo ln -s /mnt/