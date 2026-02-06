#!/bin/bash
files=$(find . \( -name "*.c" -o -name "*.h" \) -type f | \
        xargs enca -L zh | grep GB2312 | cut -d: -f1)

for f in $files; do
  iconv -f GB2312 -t UTF-8 "$f" | dos2unix > "$f.tmp" && mv "$f.tmp" "$f"
done
