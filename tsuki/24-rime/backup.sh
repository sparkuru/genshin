#!/usr/bin/env bash
set -Eeuo pipefail

script_name=$(basename "$0")
readonly SCRIPT_NAME=$script_name
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly SCRIPT_DIR=$script_dir
readonly BACKUP_ROOT="$SCRIPT_DIR/custom"
readonly DEFAULT_RIME_DIR="/home/wkyuu/.local/share/fcitx5/rime"
readonly -a BACKUP_FILES=(
	"default.yaml"
	"rime_mint.custom.yaml"
	"dicts/custom_simple.dict.yaml"
)

rime_dir=$DEFAULT_RIME_DIR
force_mode=false
with_userdb=false
tmp_dir=""

usage() {
	printf 'Usage: %s [--rime-dir PATH] [--with-userdb] [--force]\n' "$SCRIPT_NAME"
	printf '\n'
	printf 'Snapshot user-owned Rime files into this repository.\n'
	printf 'Use --with-userdb to include exported user dictionaries.\n'
	printf 'Use --force to replace existing backup files.\n'
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

cleanup_workspace() {
	local temp_root=${TMPDIR:-/tmp}

	if [[ -n "${tmp_dir:-}" && "$tmp_dir" == "${temp_root%/}"/rime-backup.* && -d "$tmp_dir" ]]; then
		rm -rf -- "$tmp_dir"
	fi
}

find_latest_sync_export() {
	local dict_name=$1
	local candidate
	local latest_path=""
	local latest_mtime=-1
	local mtime

	for candidate in "$rime_dir"/sync/*/"$dict_name".userdb.txt; do
		[[ -f "$candidate" ]] || continue
		mtime=$(stat -c '%Y' -- "$candidate")
		if ((mtime > latest_mtime)); then
			latest_mtime=$mtime
			latest_path=$candidate
		fi
	done

	[[ -n "$latest_path" ]] || return 1
	printf '%s\n' "$latest_path"
}

copy_source_file() {
	local relative_path=$1
	local source_path="$rime_dir/$relative_path"
	local stage_path="$tmp_dir/$relative_path"

	[[ -f "$source_path" ]] || die "source file not found: $source_path"
	mkdir -p -- "$(dirname -- "$stage_path")"
	cp -- "$source_path" "$stage_path"
}

copy_userdb_export() {
	local dict_name=$1
	local source_path
	local stage_path="$tmp_dir/state/$dict_name.userdb.txt"

	source_path=$(find_latest_sync_export "$dict_name") || die "no sync export found for $dict_name"
	mkdir -p -- "$(dirname -- "$stage_path")"
	cp -- "$source_path" "$stage_path"
}

write_manifest() {
	local rime_commit="unknown"
	local origin_url="unknown"
	local distribution_code_name="unknown"
	local distribution_version="unknown"
	local rime_version="unknown"
	local relative_path
	local digest
	local -a manifest_files=("$@")

	if command -v git >/dev/null 2>&1 && git -C "$rime_dir" rev-parse --is-inside-work-tree >/dev/null 2>&1; then
		rime_commit=$(git -C "$rime_dir" rev-parse HEAD 2>/dev/null || printf '%s' unknown)
		origin_url=$(git -C "$rime_dir" remote get-url origin 2>/dev/null || printf '%s' unknown)
	fi

	if [[ -f "$rime_dir/installation.yaml" ]]; then
		distribution_code_name=$(sed -n 's/^distribution_code_name: "\(.*\)"$/\1/p' "$rime_dir/installation.yaml" | head -n 1)
		distribution_version=$(sed -n 's/^distribution_version: \(.*\)$/\1/p' "$rime_dir/installation.yaml" | head -n 1)
		rime_version=$(sed -n 's/^rime_version: \(.*\)$/\1/p' "$rime_dir/installation.yaml" | head -n 1)
		distribution_code_name=${distribution_code_name:-unknown}
		distribution_version=${distribution_version:-unknown}
		rime_version=${rime_version:-unknown}
	fi

	{
		printf 'format_version: 1\n'
		printf 'captured_at_utc: %s\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
		printf 'source_schema: rime_mint\n'
		printf 'source_rime_commit: %s\n' "$rime_commit"
		printf 'source_origin: %s\n' "$origin_url"
		printf 'distribution_code_name: %s\n' "$distribution_code_name"
		printf 'distribution_version: %s\n' "$distribution_version"
		printf 'rime_version: %s\n' "$rime_version"
		printf 'includes_userdb: %s\n' "$with_userdb"
		printf 'files:\n'
		for relative_path in "${manifest_files[@]}"; do
			digest=$(sha256sum -- "$tmp_dir/$relative_path" | awk '{print $1}')
			printf '  - path: %s\n' "$relative_path"
			printf '    sha256: %s\n' "$digest"
		done
	} >"$tmp_dir/manifest.yaml"
}

copy_stage_to_backup() {
	local relative_path=$1
	local destination="$BACKUP_ROOT/$relative_path"

	mkdir -p -- "$(dirname -- "$destination")"
	cp -- "$tmp_dir/$relative_path" "$destination"
}

main() {
	local lua_path
	local relative_path
	local -a staged_files=("${BACKUP_FILES[@]}")

	for lua_path in "$BACKUP_ROOT"/lua/*.lua; do
		[[ -f "$lua_path" ]] || continue
		relative_path=${lua_path#"$BACKUP_ROOT/"}
		staged_files+=("$relative_path")
	done

	while [[ $# -gt 0 ]]; do
		case "$1" in
		--rime-dir)
			[[ $# -ge 2 ]] || die "--rime-dir requires a path"
			rime_dir=$2
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
	[[ -d "$rime_dir" ]] || die "Rime directory not found: $rime_dir"

	require_command awk
	require_command cp
	require_command date
	require_command dirname
	require_command git
	require_command mkdir
	require_command mktemp
	require_command rm
	require_command sha256sum
	require_command stat

	tmp_dir=$(mktemp -d "${TMPDIR:-/tmp}/rime-backup.XXXXXXXXXX")
	trap cleanup_workspace EXIT

	for relative_path in "${staged_files[@]}"; do
		copy_source_file "$relative_path"
	done

	if [[ "$with_userdb" == true ]]; then
		copy_userdb_export rime_mint
		copy_userdb_export melt_eng
		staged_files+=(
			"state/rime_mint.userdb.txt"
			"state/melt_eng.userdb.txt"
		)
	fi

	write_manifest "${staged_files[@]}"
	staged_files+=(manifest.yaml)

	if [[ "$force_mode" != true ]]; then
		for relative_path in "${staged_files[@]}"; do
			[[ ! -e "$BACKUP_ROOT/$relative_path" ]] || die "backup file exists; rerun with --force: $BACKUP_ROOT/$relative_path"
		done
	fi

	for relative_path in "${staged_files[@]}"; do
		copy_stage_to_backup "$relative_path"
	done

	printf 'Backup updated at %s\n' "$BACKUP_ROOT"
	printf 'Included userdb exports: %s\n' "$with_userdb"
}

main "$@"
