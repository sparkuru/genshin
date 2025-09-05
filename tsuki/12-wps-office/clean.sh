#!/bin/bash

wps_config_file_dir="/home/$USER/.config/Kingsoft"

config_file_list=(
    "Office.conf"

)

# clean history record
keyword_list=(
    "RecentFiles"
    "openFile"
    "CloudFileDialog"
    "lastOpenDir"
    "FileDialog"
    "openfilelist"
)

# sed '/RecentFiles\|openFile\|CloudFileDialog\|lastOpenDir\|FileDialog\|openfilelist/d' $wps_config_file_dir/Office.conf

printf -v expr_str '%s\\|' "${keyword_list[@]}"
expr_str="${expr_str%\\|}"

for config_file in "${config_file_list[@]}"; do
    sed -i "/$expr_str/d" $wps_config_file_dir/$config_file
done

# remove wps cloud files
document_path=$(echo "$HOME/document/WPS Cloud Files" | sed 's|\/|\\/|g')
target_path="\/tmp\/wps"
sed -i "s/$document_path/$target_path/g" "$wps_config_file_dir/WPSCloud.conf"