#!/bin/bash

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

count_md_not_755=`find $genshin_dir_path -name "*.md" -type f -not -perm 755 | wc -l`

echo "count_md_not_755: $count_md_not_755, do chmod 755 ..."
find $genshin_dir_path -name "*.md" -type f -not -perm 755 -exec chmod 755 {} \;

count_md_755=`find $genshin_dir_path -name "*.md" -type f -perm 755 | wc -l`
echo "count_md_755: $count_md_755, done."