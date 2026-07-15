#!/usr/bin/env bash
set -Eeuo pipefail

script_dir=$(dirname -- "$0")
SCRIPT_DIR=$(cd -- "$script_dir" && pwd)
readonly SCRIPT_DIR
readonly CONFIG_SOURCE_DIR="$SCRIPT_DIR/config"
readonly CONFIG_TARGET_DIR="$HOME/.config/VSCodium/User"

die() {
	printf 'Error: %s\n' "$*" >&2
	exit 1
}

link_file() {
	local source_path=$1
	local target_path=$2

	[[ -f "$source_path" ]] || die "configuration file not found: $source_path"
	if [[ -e "$target_path" && ! -L "$target_path" ]]; then
		die "refusing to replace existing file: $target_path"
	fi
	ln -sfnT -- "$source_path" "$target_path"
}

main() {
	mkdir -p -- "$CONFIG_TARGET_DIR"
	link_file "$CONFIG_SOURCE_DIR/settings.json" "$CONFIG_TARGET_DIR/settings.json"
	link_file "$CONFIG_SOURCE_DIR/keybindings.json" "$CONFIG_TARGET_DIR/keybindings.json"
}

main "$@"
