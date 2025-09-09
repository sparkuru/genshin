#!/bin/bash

wps_config_file_dir="/home/$USER/.config/Kingsoft"
wps_bin_root_dir="/opt/kingsoft/wps-office"

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

printf -v expr_str '%s\\|' "${keyword_list[@]}"
expr_str="${expr_str%\\|}"

for config_file in "${config_file_list[@]}"; do
    sed -i "/$expr_str/d" $wps_config_file_dir/$config_file
done

# turn off cloud sync function
sed -i "s/true$/false/g" "$wps_config_file_dir/WPSCloud.conf"

num_keyword_list=(
    "batchRemove"
    "supportPMoveFolder"
    "localsyncfolder"
    "showpanel"
)

for keyword in "${num_keyword_list[@]}"; do
    sed -i "s/$keyword=1/$keyword=0/g" "$wps_config_file_dir/WPSCloud.conf"
done

# remove wps cloud files
document_path=$(echo "$HOME/document/WPS Cloud Files" | sed 's|\/|\\/|g')
target_path="\/tmp\/wps"
sed -i "s/$document_path/$target_path/g" "$wps_config_file_dir/WPSCloud.conf"
sed -i "s/supportSecretFolderFunc_tmp=true/supportSecretFolderFunc_tmp=false/g" "$wps_config_file_dir/WPSCloud\\usercenter\\secretFolder.conf"

# other clean
old="00000001=eyJRUHVzaCI6InRydWUiLCJjcnlwdGNvb2tpZSI6InRydWUiLCJtb2JpbGVQdXNoIjoiZmFsc2UiLCJxaW5pdSI6Im9wZW4iLCJyZXN1bHQiOiJvayIsInJvYW1Ib21lcGFnZVNldHRpbmdHdWlkIjoidHJ1ZSIsInNob3dndWlkZSI6ImZhbHNlIiwidXBkYXRlVGlwSW50ZXJ2YWwiOiIzNjAwMCJ9"
new="00000001=eyJRUHVzaCI6ImZhbHNlIiwiY3J5cHRjb29raWUiOiJmYWxzZSIsIm1vYmlsZVB1c2giOiJmYWxzZSIsInFpbml1Ijoib2ZmIiwicmVzdWx0Ijoib2siLCJyb2FtSG9tZXBhZ2VTZXR0aW5nR3VpZCI6InRydWUiLCJzaG93Z3VpZGUiOiJmYWxzZSIsInVwZGF0ZVRpcEludGVydmFsIjoiMzYwMDAwMDAwMDAwMDAifQ=="
sed -i "s/$old/$new/g" "$wps_config_file_dir/WPSCloud.conf"

# remove "$HOME/document/WPS Cloud Files"
libso_file_path_list=(
    "$wps_bin_root_dir/office6/addons/qing/libqingbangong.so"
    "$wps_bin_root_dir/office6/addons/khyperion/libkhyperion.so"
)
for libso_file_path in "${libso_file_path_list[@]}"; do
    if [ -f "$wps_bin_root_dir/$libso_file_path" ]; then
        # recover by remove .backup extension
        mv "$wps_bin_root_dir/$libso_file_path" "$wps_bin_root_dir/$libso_file_path.backup"
    fi
done

echo "clean wps office done."
