#/usr/bin/env zsh

index=05
app_name=transfersh
url=https://raw.githubusercontent.com/shi9uma/genshin/main/app/$index-$app_name/$app_name.yml
UID=1000
GID=1000

create_dir() {
    if [ ! -d $1 ]; then
        mkdir -p $1
    fi
}

work_dir=$(dirname $0)
file_path=$work_dir/$app_name.yml
repo_path=$work_dir/repo
if [ ! -f $file_path ]; then
    create_dir $work_dir/storage
    curl -fLo $file_path $url

    create_dir $repo_path
    git clone \
        https://github.com/dutchcoders/transfer.sh.git \
        $repo_path
    cd $repo_path
    docker build \
        -t transfer.sh-$UID \
        --build-arg RUNAS=any \
        --build-arg PUID=$UID \
        --build-arg PGID=$GID \
        .
fi
