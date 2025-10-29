#!/bin/bash

cd $(dirname $0)

rss_url="https://cursor.com/api/download?platform=linux-x64&releaseTrack=stable"
download_url=$(curl -fsL $rss_url | jq -r '.downloadUrl')
version=$(echo $download_url | grep -o "[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,10\}")

appname="cursor"
platform="linux"
arch="x86_64"
appimage_name="${appname}-${platform}-${arch}-${version}.AppImage"
desktop_file_name="${appname}.desktop"

current_version=$(grep -o '[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,10\}' $desktop_file_name)
if [ $current_version == $version ]; then
	echo "already up to date, current version: $current_version, latest version: $version"
	exit 0
fi

if [[ ! -f $appimage_name || ! -s $appimage_name ]]; then
	echo "downloading ${appname} via $download_url"
	wget -vO $appimage_name $download_url
	if [ $? -ne 0 ]; then
		echo "failed to download $download_url, try \nwget -vN $download_url -O $appimage_name"
		exit 1
	fi
fi

chmod +x $appimage_name
./$appimage_name --appimage-extract
rsync -avtz --progress squashfs-root/* .

if [ $(grep -o '[0-9]\{1,3\}\.[0-9]\{1,3\}\.[0-9]\{1,10\}' $desktop_file_name) == $version ]; then
	rm -rf squashfs-root
	rm $appimage_name
fi

echo -e "\n\n> ${appname} updated to $version done."
