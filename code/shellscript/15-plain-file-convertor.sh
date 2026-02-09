#!/bin/bash

find . -type f -print0 \
  | xargs -0 -r file --mime-type \
  | awk -F: '$2 ~ /text\// {print $1}' \
  | xargs -r -d '\n' enca -L zh \
  | awk -F: '$2 !~ /utf-8/i && $2 ~ /(GB2312|GBK|GB18030)/ {print $1}' \
  | while IFS= read -r f; do
      iconv -f GB18030 -t UTF-8 -c "$f" | dos2unix > "$f.tmp" && mv "$f.tmp" "$f"
    done
