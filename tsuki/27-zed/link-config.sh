#!/usr/bin/env sh
set -eu

script_dir=$(dirname "$0")
SCRIPT_DIR=$(cd "$script_dir" && pwd)
readonly SCRIPT_DIR
readonly CONFIG_SOURCE_DIR="$SCRIPT_DIR/config"
readonly CONFIG_TARGET_DIR="$HOME/.config/zed"

die() {
	printf 'Error: %s\n' "$*" >&2
	exit 1
}

link_file() {
	source_path=$1
	target_path=$2

	if [ -e "$target_path" ] && [ ! -L "$target_path" ]; then
		die "refusing to replace existing file: $target_path"
	fi

	ln -sfn "$source_path" "$target_path"
}

main() {
	[ -d "$CONFIG_SOURCE_DIR" ] || die "configuration directory not found: $CONFIG_SOURCE_DIR"

	mkdir -p "$CONFIG_TARGET_DIR"
	link_file "$CONFIG_SOURCE_DIR/settings.json" "$CONFIG_TARGET_DIR/settings.json"
	link_file "$CONFIG_SOURCE_DIR/keymap.json" "$CONFIG_TARGET_DIR/keymap.json"
	link_file "$CONFIG_SOURCE_DIR/tasks.json" "$CONFIG_TARGET_DIR/tasks.json"
}

main "$@"
