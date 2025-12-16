#!/bin/bash

SOURCE_DIR="$HOME/download"
DEST_DIR="./image"

mkdir -p "$DEST_DIR"

find "$SOURCE_DIR" -maxdepth 1 -type f -regextype posix-extended \
    -regex '.*/[0-9a-fA-F]{32}\.(jpg|jpeg|png|gif)$' -printf '%f\0' |
    rsync -avz --progress --remove-source-files --files-from=- --from0 "$SOURCE_DIR/" "$DEST_DIR/"
