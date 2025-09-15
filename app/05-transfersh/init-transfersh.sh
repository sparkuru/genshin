#/usr/bin/env zsh

index=05
app_name=transfersh
url=https://raw.githubusercontent.com/sparkuru/genshin/main/app/$index-$app_name/$app_name.yml
UID=$UID
GID=$GID

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
        -t transfersh-user \
        --build-arg RUNAS=any \
        --build-arg PUID=$UID \
        --build-arg PGID=$GID \
        .
fi
