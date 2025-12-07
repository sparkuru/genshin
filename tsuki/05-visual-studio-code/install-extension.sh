#!/bin/bash

# code --list-extensions | xargs -L 1 code --install-extension


github_content_base="https://raw.githubusercontent.com/sparkuru/genshin/main"
extension_url="$github_content_base/tsuki/05-visual-studio-code/extension.txt"
extensions_file="/tmp/extension.txt"

curl -sfL -o $extensions_file $extension_url
cat $extensions_file | xargs -L 1 code --install-extension

# windows powershell
# Get-Content extension.txt | ForEach-Object { code --install-extension $_ }