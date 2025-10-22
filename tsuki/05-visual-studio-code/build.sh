#!/bin/bash
# refer to: https://github.com/valicm/appimage-bash/blob/main/build.sh

#region
white='\033[0m'
green='\033[0;32m'
blue='\033[0;34m'
red='\033[31m'
yellow='\033[33m'
grey='\e[37m'
pink='\033[38;5;218m'
cyan='\033[96m'

# echo -e "${red}xxx${nc}"
nc='\033[0m'
#endregion

cd $(dirname $0)

# 1. prepare environment
workdir="build"
distdir="dist"
bindir="$workdir/usr/bin"
tgz_extract_dir="$bindir"

apprun_download_url="https://raw.githubusercontent.com/AppImage/AppImageKit/master/resources/AppRun"
arch="x86_64"
appimagetool_download_url="https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-$arch.AppImage"

build() {
  rm -rf $workdir $distdir

  mkdir -p $bindir
  mkdir -p $tgz_extract_dir
  mkdir -p $workdir/usr/share/icons/hicolor/{128x128,256x256,512x512}/apps/
  mkdir -p $distdir

  # 2. parse vscode.desktop file
  sed_sth() {
    sed -n 's/^'"$1"'=//p' $2 | head -1
  }

  app_desktop_filename="vscode.desktop"
  app_name=$(sed_sth "Name" $app_desktop_filename)
  app_exec=$(sed_sth "Exec" $app_desktop_filename | cut -d" " -f1)
  app_icon=$(sed_sth "Icon" $app_desktop_filename)

  # 3. download and extract vscode.tgz from official repo
  app_download_url=$(sed_sth "DownloadUrl" $app_desktop_filename)
  echo -e "${green}download $app_name${nc}"
  wget --no-check-certificate -O "$distdir/$app_name".tgz "$app_download_url"

  echo -e "${green}extract $app_name.tgz${nc}"
  tar zxvf "$distdir/$app_name".tgz --strip-components=1 -C $tgz_extract_dir && rm -r "$distdir/$app_name".tgz

  # 4. parse vscode appimage info
  app_package_json_path="$tgz_extract_dir/resources/app/package.json"
  app_version=$(jq -r '."version"' $app_package_json_path)

  app_icon_name="code"
  app_icon_path=$(find "$tgz_extract_dir/resources/app/resources" -type f -name "$app_icon_name.*")
  app_icon_extension="${app_icon_path#*.}"
  cp "$app_icon_path" $workdir/$app_icon_name.$app_icon_extension
  if [ "$app_icon_extension" == "svg" ]; then
    cp "$app_icon_path" $workdir/usr/share/icons/hicolor/128x128/apps/$app_icon_name.$app_icon_extension
    cp "$app_icon_path" $workdir/usr/share/icons/hicolor/256x256/apps/$app_icon_name.$app_icon_extension
    cp "$app_icon_path" $workdir/usr/share/icons/hicolor/512x512/apps/$app_icon_name.$app_icon_extension
  else
    convert "$app_icon_path" -resize 128x128 $workdir/usr/share/icons/hicolor/128x128/apps/$app_icon_name.$app_icon_extension
    convert "$app_icon_path" -resize 256x256 $workdir/usr/share/icons/hicolor/256x256/apps/$app_icon_name.$app_icon_extension
    convert "$app_icon_path" -resize 512x512 $workdir/usr/share/icons/hicolor/512x512/apps/$app_icon_name.$app_icon_extension
  fi

  app_exec_path="$tgz_extract_dir/$app_exec"

  # 5. download and set AppRun binary
  apprun_path="$workdir/AppRun"
  echo -e "${green}download AppRun${nc}"
  wget --no-check-certificate -O $apprun_path $apprun_download_url && chmod +x $apprun_path

  cp $app_desktop_filename $workdir/$app_desktop_filename
  sed -i 's/^X-AppImage-Version=$/X-AppImage-Version='$app_version'/' $workdir/$app_desktop_filename
  sed -i 's/^DownloadVersion=$/DownloadVersion='$app_version'/' $workdir/$app_desktop_filename

  # 6. build appimage
  appimage_path="$app_name-$app_version-$arch.AppImage"
  if [ -f /.dockerenv ]; then
    appimagetool_path="/tmp/appimagetool-$arch.AppImage"
  else
    appimagetool_path="$distdir/appimagetool-$arch.AppImage"
  fi
  appimage_output_filename="$app_name-$arch.AppImage"

  wget --no-check-certificate -O $appimagetool_path $appimagetool_download_url && chmod +x $appimagetool_path

  echo -e "${green}building appimage...${nc}"
  ARCH=$arch $appimagetool_path --comp gzip $workdir -nv

  if [ $? -ne 0 ]; then
    echo -e "${red}build appimage failed${nc}"
    exit 1
  else
    echo -e "${green}build appimage success, check ${green}${distdir}/${appimage_path}.${nc}"
    mv $appimage_output_filename $distdir/$appimage_path
  fi
}

if [[ $1 == "clean" ]]; then
  rm -rf $workdir $distdir
  exit 0
elif [[ $1 == "build" ]]; then
  build
  exit 0
else
  echo -e "${red}usage: $0 [clean|build] ${nc}"
  exit 1
fi
