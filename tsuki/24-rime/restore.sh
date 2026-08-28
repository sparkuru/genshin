#!/usr/bin/env bash
set -Eeuo pipefail

script_name=$(basename "$0")
readonly SCRIPT_NAME=$script_name
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly SCRIPT_DIR=$script_dir
readonly BACKUP_ROOT="$SCRIPT_DIR/custom"
readonly DEFAULT_RIME_DIR="/home/wkyuu/.local/share/fcitx5/rime"
readonly DEFAULT_SHARED_DATA_DIR="/usr/share/rime-data"
readonly -a RESTORE_FILES=(
	"default.yaml"
	"rime_mint.custom.yaml"
	"dicts/custom_simple.dict.yaml"
)

rime_dir=$DEFAULT_RIME_DIR
shared_data_dir=$DEFAULT_SHARED_DATA_DIR
force_mode=false
with_userdb=false

usage() {
	printf 'Usage: %s [--rime-dir PATH] [--shared-data-dir PATH] [--with-userdb] --force\n' "$SCRIPT_NAME"
	printf '\n'
	printf 'Link the tracked Rime overlay and redeploy it.\n'
	printf 'Stop Fcitx5 before using --with-userdb.\n'
}

die() {
	printf 'Error: %s\n' "$*" >&2
	exit 1
}

warn() {
	printf 'Warning: %s\n' "$*" >&2
}

require_command() {
	command -v "$1" >/dev/null 2>&1 || die "required command not found: $1"
}

link_overlay_file() {
	local relative_path=$1
	local source_path="$BACKUP_ROOT/$relative_path"
	local destination_path="$rime_dir/$relative_path"

	[[ -f "$source_path" ]] || die "backup file not found: $source_path"
	if [[ -d "$destination_path" && ! -L "$destination_path" ]]; then
		die "destination is a directory: $destination_path"
	fi
	if [[ -L "$destination_path" && "$(readlink -- "$destination_path")" == "$source_path" ]]; then
		return
	fi
	mkdir -p -- "$(dirname -- "$destination_path")"
	rm -f -- "$destination_path"
	ln -s -- "$source_path" "$destination_path"
}

link_lua_files() {
	local lua_path
	local relative_path

	for lua_path in "$BACKUP_ROOT"/lua/*.lua; do
		[[ -f "$lua_path" ]] || continue
		relative_path=${lua_path#"$BACKUP_ROOT/"}
		link_overlay_file "$relative_path"
	done
}

restore_userdb() {
	local dict_name=$1
	local source_path="$BACKUP_ROOT/state/$dict_name.userdb.txt"

	[[ -f "$source_path" ]] || die "userdb export not found: $source_path"
	(
		cd -- "$rime_dir"
		rime_dict_manager --restore "$source_path"
	)
}

main() {
	local relative_path

	while [[ $# -gt 0 ]]; do
		case "$1" in
		--rime-dir)
			[[ $# -ge 2 ]] || die "--rime-dir requires a path"
			rime_dir=$2
			shift 2
			;;
		--shared-data-dir)
			[[ $# -ge 2 ]] || die "--shared-data-dir requires a path"
			shared_data_dir=$2
			shift 2
			;;
		--with-userdb)
			with_userdb=true
			shift
			;;
		--force)
			force_mode=true
			shift
			;;
		--help | -h)
			usage
			return 0
			;;
		--)
			shift
			break
			;;
		*)
			die "unknown argument: $1"
			;;
		esac
	done

	[[ $# -eq 0 ]] || die "unexpected argument: $1"
	[[ "$force_mode" == true ]] || die "restoring overwrites user files; pass --force explicitly"
	[[ -d "$rime_dir" ]] || die "Rime directory not found: $rime_dir"
	[[ -d "$shared_data_dir" ]] || die "Rime shared data directory not found: $shared_data_dir"

	require_command cp
	require_command dirname
	require_command fcitx5-remote
	require_command ln
	require_command mkdir
	require_command readlink
	require_command rm
	require_command rime_deployer

	for relative_path in "${RESTORE_FILES[@]}"; do
		link_overlay_file "$relative_path"
	done
	link_lua_files

	rime_deployer --build "$rime_dir" "$shared_data_dir" "$rime_dir/build"

	if [[ "$with_userdb" == true ]]; then
		require_command rime_dict_manager
		[[ -f "$rime_dir/installation.yaml" ]] || die "Rime installation.yaml is missing; initialize Rime before restoring userdb"
		restore_userdb rime_mint
		if [[ -f "$BACKUP_ROOT/state/melt_eng.userdb.txt" ]]; then
			restore_userdb melt_eng
		fi
	fi

	if ! fcitx5-remote -r; then
		warn "Fcitx5 reload failed; restart Fcitx5 from the desktop session"
	fi

	printf 'Rime overlay restored to %s\n' "$rime_dir"
	printf 'Included userdb exports: %s\n' "$with_userdb"
}

main "$@"
