#!/usr/bin/env bash
set -Eeuo pipefail

script_dir=$(cd -- "$(dirname -- "$0")" && pwd)
readonly SCRIPT_DIR="$script_dir"
readonly SOURCE_PATH="$SCRIPT_DIR/config/oh-my-openagent.json"
readonly TARGET_DIR="$HOME/.config/opencode"
readonly TARGET_PATH="$TARGET_DIR/oh-my-openagent.json"

backup_existing=false

usage() {
	printf 'Usage: %s [--backup-existing]\n' "$(basename -- "$0")" >&2
}

die() {
	printf 'Error: %s\n' "$*" >&2
	exit 1
}

link_config() {
	[[ -f "$SOURCE_PATH" ]] || die "configuration file not found: $SOURCE_PATH"
	mkdir -p -- "$TARGET_DIR"

	if [[ -e "$TARGET_PATH" && ! -L "$TARGET_PATH" ]]; then
		if [[ "$backup_existing" != true ]]; then
			die "refusing to replace existing file: $TARGET_PATH"
		fi

		local backup_path
		backup_path="$TARGET_PATH.backup.$(date +%Y%m%d%H%M%S)"
		mv -- "$TARGET_PATH" "$backup_path"
		printf 'Backed up existing configuration to %s\n' "$backup_path"
	fi

	ln -sfn -- "$SOURCE_PATH" "$TARGET_PATH"
	printf 'Linked %s -> %s\n' "$TARGET_PATH" "$SOURCE_PATH"
}

main() {
	while [[ $# -gt 0 ]]; do
		case "$1" in
		--backup-existing)
			backup_existing=true
			;;
		--help | -h)
			usage
			return 0
			;;
		*)
			usage
			die "unknown option: $1"
			;;
		esac
		shift
	done

	link_config
}

main "$@"
