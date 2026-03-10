#!/bin/bash

# `./16-pandoc-md2docx.sh any` force to cover the existing docx file

yellow='\033[1;33m'
green='\033[1;32m'
red='\033[1;31m'
reset='\033[0m'

link_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]:-$0}")" && pwd)"
script_path="$(readlink -f -- "${BASH_SOURCE[0]:-$0}" 2>/dev/null || printf '%s' "${BASH_SOURCE[0]:-$0}")"
repo_dir="$(cd -- "$(dirname -- "$script_path")" && pwd -P)"

dont_cover_file_index=(
	"01"
	"02"
	"03"
)

tool_dir="$link_dir"

flag=0
root_dir="$tool_dir"
markdown_dir=""
single_markdown_file=""
for arg in "$@"; do
	case "$arg" in
	-f | --force)
		flag=1
		;;
	*)
		if [ -z "$markdown_dir" ] && [ -z "$single_markdown_file" ]; then
			if [ -f "$arg" ]; then
				single_markdown_file="$arg"
			else
				markdown_dir="$arg"
			fi
		fi
		;;
	esac
done
if [ -z "$markdown_dir" ]; then
	if [ -n "$single_markdown_file" ]; then
		markdown_dir="$(cd -- "$(dirname -- "$single_markdown_file")" && pwd)"
		single_markdown_file="$markdown_dir/$(basename -- "$single_markdown_file")"
	else
		if [ -d "$root_dir/markdown" ]; then
			markdown_dir="$root_dir/markdown"
		else
			markdown_dir="$PWD"
		fi
	fi
fi

python_style_script="$tool_dir/docx-table-style.py"
if [ ! -f "$python_style_script" ]; then
	python_style_script="$repo_dir/docx-table-style.py"
fi

pandoc_template_file="$tool_dir/pandoc-template.docx"
if [ ! -f "$pandoc_template_file" ]; then
	pandoc_template_file="$repo_dir/pandoc-template.docx"
fi

use_pandoc_template=1
if [ ! -f "$pandoc_template_file" ]; then
	use_pandoc_template=0
	echo -e "${yellow}[$(date +%Y-%m-%d\ %H:%M:%S)] pandoc-template.docx not found; using pandoc default template${reset}"
	echo -e "${yellow}[$(date +%Y-%m-%d\ %H:%M:%S)] tip: place pandoc-template.docx next to this script to customize styles${reset}"
fi

python_bin="python3"
if [ -f "$python_style_script" ]; then
	if [ -x "$root_dir/.venv/bin/python" ]; then
		python_bin="$root_dir/.venv/bin/python"
	elif [ -x "$root_dir/venv/bin/python" ]; then
		python_bin="$root_dir/venv/bin/python"
	elif [ -x "$markdown_dir/.venv/bin/python" ]; then
		python_bin="$markdown_dir/.venv/bin/python"
	elif [ -x "$markdown_dir/venv/bin/python" ]; then
		python_bin="$markdown_dir/venv/bin/python"
	fi

	if ! "$python_bin" -c 'import docx' >/dev/null 2>&1; then
		echo -e "${red}[$(date +%Y-%m-%d\ %H:%M:%S)] python-docx not found for: $python_bin${reset}"
		echo -e "${yellow}install: pip install python-docx${reset}"
		echo -e "${yellow}or: uv init; uv add python-docx${reset}"
		exit 1
	fi
fi

output_dir="$root_dir/docx"
if [ ! -d "$output_dir" ]; then
	mkdir -p "$output_dir"
fi

cd "$markdown_dir"

converted_count=0
found_markdown=0
if [ -n "$single_markdown_file" ]; then
	if [ ! -s "$single_markdown_file" ]; then
		echo -e "${red}[$(date +%Y-%m-%d\ %H:%M:%S)] markdown file not found or empty: $single_markdown_file${reset}"
		exit 1
	fi
	file_list=("$single_markdown_file")
else
	file_list=( *.md )
fi

for file in "${file_list[@]}"; do
	[ -e "$file" ] || continue

	filename="${file##*/}"
	filename="${filename%.md}"
	file_index="${filename%%-*}"
	src_markdown_file="$markdown_dir/$file"
	dst_docx_file="$output_dir/$filename.docx"

	if [ ! -s "$src_markdown_file" ]; then
		continue
	fi

	found_markdown=1

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
	if [ $use_pandoc_template -eq 1 ]; then
		pandoc --from markdown \
			--to docx \
			--reference-doc "$pandoc_template_file" \
			--output "$dst_docx_file" \
			"$src_markdown_file"
	else
		pandoc --from markdown \
			--to docx \
			--output "$dst_docx_file" \
			"$src_markdown_file"
	fi
	if [ -f "$python_style_script" ]; then
		"$python_bin" "$python_style_script" "$dst_docx_file" --format-table
	fi
	converted_count=$((converted_count + 1))
done

if [ $converted_count -eq 0 ] && [ $found_markdown -eq 0 ]; then
	echo -e "${yellow}[$(date +%Y-%m-%d\ %H:%M:%S)] no markdown files found in: $markdown_dir${reset}"
	echo -e "${yellow}[$(date +%Y-%m-%d\ %H:%M:%S)] tip: run './md2docx.sh ./markdown' or put *.md under ./markdown${reset}"
fi
