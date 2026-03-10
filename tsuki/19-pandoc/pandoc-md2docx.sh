#!/bin/bash

# `./16-pandoc-md2docx.sh 1` force cover the existing docx file

yellow='\033[1;33m'
green='\033[1;32m'
red='\033[1;31m'
reset='\033[0m'

workdir=$(cd $(dirname $0) && pwd)

dont_cover_file_index=(
	"01"
	"02"
	"03"
)

python_style_script="$workdir/docx-table-style.py"

flag=0
if [ $# -gt 0 ]; then
	flag=1
fi

markdown_file_dir=$workdir/workspace
output_dir=$workdir/docx
pandoc_template_file=$workdir/pandoc-template.docx

mkdir -p "$output_dir"
cd "$markdown_file_dir"

for file in *.md; do
	[ -e "$file" ] || continue

	filename="${file##*/}"
	filename="${filename%.md}"
	file_index="${filename%%-*}"
	src_markdown_file="$markdown_file_dir/$file"
	dst_docx_file="$output_dir/$filename.docx"

	if [ ! -s "$src_markdown_file" ]; then
		continue
	fi

	if [ -f "$dst_docx_file" ]; then
		if [ $flag -eq 0 ]; then
			echo -e "${red}[$(date +%Y-%m-%d\ %H:%M:%S)] ${dst_docx_file##*/} already exists, skip...${reset}"
			continue
		fi
	fi

	skip_this_file=0
	for ignore_index in "${dont_cover_file_index[@]}"; do
		if [ "$file_index" = "$ignore_index" ]; then
			skip_this_file=1
			break
		fi
	done

	if [ $skip_this_file -eq 1 ]; then
		echo -e "${yellow}[$(date +%Y-%m-%d\ %H:%M:%S)] ${dst_docx_file##*/} is in the ignore list, skip...${reset}"
		continue
	fi

	echo -e "${green}[$(date +%Y-%m-%d\ %H:%M:%S)] convert \n ${src_markdown_file##*/} --> ${dst_docx_file##*/}${reset}"
	pandoc --from markdown \
		--to docx \
		--reference-doc "$pandoc_template_file" \
		--output "$dst_docx_file" \
		"$src_markdown_file"
	if [ -f "$python_style_script" ]; then
		python3 "$python_style_script" "$dst_docx_file"
	fi
done
