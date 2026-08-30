#!/usr/bin/env bash

set -Eeuo pipefail

readonly TARGET_DIR_NAME="03-genshin"

# Add directories here as paths relative to the 03-genshin root.
ignored_dirs=(
	# "node_modules"
	# "path/to/archive"
  "philia093/chrysos"
)

die() {
	printf 'Error: %s\n' "$*" >&2
	exit 1
}

validate_ignored_dirs() {
	local ignored_dir

	for ignored_dir in "${ignored_dirs[@]}"; do
		case $ignored_dir in
		"" | . | /* | .. | ../* | */.. | */../* | */. | */./*)
			die "ignored directory must be a relative path without '.' or '..': $ignored_dir"
			;;
		esac
	done
}

find_genshin_dir() {
	local current_dir=$1

	while [[ $current_dir != / ]]; do
		if [[ $(basename "$current_dir") == "$TARGET_DIR_NAME" ]]; then
			printf '%s\n' "$current_dir"
			return 0
		fi
		current_dir=$(dirname "$current_dir")
	done

	return 1
}

find_markdown_files() {
	local genshin_dir_path=$1
	local permission_filter=$2
	local ignored_dir
	local is_first_ignored_dir=true
	local -a find_command=(find "$genshin_dir_path")

	if [[ ${#ignored_dirs[@]} -gt 0 ]]; then
		find_command+=("(" -type d "(")
		for ignored_dir in "${ignored_dirs[@]}"; do
			if [[ $is_first_ignored_dir == false ]]; then
				find_command+=(-o)
			fi
			find_command+=(-path "$genshin_dir_path/$ignored_dir")
			is_first_ignored_dir=false
		done
		find_command+=(")" -prune ")" -o)
	fi

	find_command+=(-type f -name "*.md")
	case $permission_filter in
	not-755)
		find_command+=(-not -perm 755)
		;;
	755)
		find_command+=(-perm 755)
		;;
	*)
		die "unsupported permission filter: $permission_filter"
		;;
	esac
	find_command+=(-print0)

	"${find_command[@]}"
}

chmod_markdown_files() {
	local genshin_dir_path=$1
	local file_path

	while IFS= read -r -d '' file_path; do
		chmod 755 "$file_path"
	done < <(find_markdown_files "$genshin_dir_path" not-755)
}

count_markdown_files() {
	local genshin_dir_path=$1
	local permission_filter=$2
	local file_path
	local count=0

	while IFS= read -r -d '' file_path; do
		((count += 1))
	done < <(find_markdown_files "$genshin_dir_path" "$permission_filter")

	printf '%d\n' "$count"
}

main() {
	local workdir
	local genshin_dir_path
	local count_md_not_755
	local count_md_755

	[[ $# -eq 0 ]] || die "this script does not accept arguments"
	validate_ignored_dirs

	workdir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]:-$0}")" && pwd)
	genshin_dir_path=$(find_genshin_dir "$workdir") ||
		die "could not find the $TARGET_DIR_NAME root from $workdir"

	count_md_not_755=$(count_markdown_files "$genshin_dir_path" not-755)
	printf 'count_md_not_755: %s, do chmod 755 ...\n' "$count_md_not_755"
	chmod_markdown_files "$genshin_dir_path"

	count_md_755=$(count_markdown_files "$genshin_dir_path" 755)
	printf 'count_md_755: %s, done.\n' "$count_md_755"
}

main "$@"
