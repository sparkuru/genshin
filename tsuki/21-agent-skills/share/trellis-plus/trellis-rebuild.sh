#!/usr/bin/env bash
set -Eeuo pipefail
umask 077

SCRIPT_NAME=$(basename "$0")
readonly SCRIPT_NAME
readonly DEFAULT_SPEC_PATH=".trellis/spec/trellis-plus"

readonly -a DATA_PATHS=(
	".trellis/tasks"
	".trellis/workspace"
	".trellis/spec/trellis-plus"
	".trellis/mainline.md"
	".trellis/.developer"
	".trellis/.current-task"
	".trellis/.runtime/sessions"
)
readonly -a PROTECTED_PATHS=(
	".trellis/workflow.md"
	".trellis/scripts/**"
	".trellis/agents/**"
	".trellis/config.yaml"
	".trellis/.gitignore"
	".trellis/.version"
	".trellis/.template-hashes.json"
	".trellis/.backup-*"
	"Trellis-managed platform files"
)

REPO_ROOT=""
BACKUP_DIR=""
DEVELOPER=""
DEVELOPER_SOURCE=""
HASH_COMMAND=""

declare -a TEMP_FILES=()
declare -a SPEC_ARGS=()
declare -a SPEC_PATHS=()
declare -a INCLUDED_PATHS=()
declare -a RESTORED_PATHS=()
declare -a REPLACED_PATHS=()
declare -a IDENTICAL_PATHS=()
declare -a CONFLICT_PATHS=()

usage() {
	cat >&2 <<EOF
Usage:
  $SCRIPT_NAME backup  [options]
  $SCRIPT_NAME restore [options]

Backup options:
  --repo PATH             Git repository or a directory inside it (default: .)
  --backup-dir PATH       New backup directory (default: /tmp/...)
  --spec PATH             Additional project-authored spec; repeatable
  -h, --help              Show this help

Restore options:
  --repo PATH             Git repository or a directory inside it (default: .)
  --backup-dir PATH       Backup directory produced by backup
  -h, --help              Show this help

Manual workflow:
  $SCRIPT_NAME backup --repo /path/to/project
  rm -rf /path/to/project/.trellis
  trellis init -u "<developer shown by backup>"
  $SCRIPT_NAME restore --repo /path/to/project --backup-dir /tmp/trellis-data-...

This script never deletes .trellis, runs trellis init, stages files, or commits.
EOF
}

die() {
	printf 'Error: %s\n' "$*" >&2
	exit 1
}

info() {
	printf '%s\n' "$*"
}

warn() {
	printf 'Warning: %s\n' "$*" >&2
}

require_command() {
	command -v "$1" >/dev/null 2>&1 || die "required command not found: $1"
}

require_commands() {
	local command_name

	for command_name in awk basename bash cat cmp cp date dirname find git mkdir mktemp \
		readlink rm sed sort trellis; do
		require_command "$command_name"
	done
	if command -v sha256sum >/dev/null 2>&1; then
		HASH_COMMAND=sha256sum
	elif command -v shasum >/dev/null 2>&1; then
		HASH_COMMAND=shasum
	else
		die "required command not found: sha256sum or shasum"
	fi
}

cleanup_temp_files() {
	local path

	for path in "${TEMP_FILES[@]}"; do
		if [[ -n "$path" && -f "$path" ]]; then
			rm -f -- "$path"
		fi
	done
}

trap cleanup_temp_files EXIT

append_unique() {
	local array_name=$1
	local value=$2
	local -n target_array=$array_name
	local existing

	for existing in "${target_array[@]}"; do
		[[ "$existing" == "$value" ]] && return 0
	done
	target_array+=("$value")
}

is_present() {
	[[ -e "$1" || -L "$1" ]]
}

is_safe_relative_path() {
	local path=$1

	[[ -n "$path" ]] || return 1
	case "$path" in
	/* | .. | ../* | */../* | */..)
		return 1
		;;
	esac
	return 0
}

resolve_repo_root() {
	local input_path=$1
	local root

	[[ -d "$input_path" ]] || die "repository path is not a directory: $input_path"
	root=$(git -C "$input_path" rev-parse --show-toplevel 2>/dev/null) ||
		die "not a Git repository: $input_path"
	root=$(cd -- "$root" && pwd -P)
	[[ -d "$root/.trellis" || -L "$root/.trellis" ]] ||
		die "Trellis is not initialized: $root/.trellis"
	printf '%s\n' "$root"
}

resolve_new_backup_dir() {
	local input_path=$1
	local parent_path
	local base_name

	if [[ "$input_path" == /* ]]; then
		input_path=${input_path%/}
	else
		input_path="$PWD/${input_path%/}"
	fi
	[[ -n "$input_path" ]] || die "backup path is empty"
	[[ ! -e "$input_path" && ! -L "$input_path" ]] ||
		die "backup directory already exists: $input_path"
	parent_path=$(dirname -- "$input_path")
	base_name=$(basename -- "$input_path")
	[[ -n "$base_name" && "$base_name" != "." && "$base_name" != ".." ]] ||
		die "invalid backup directory: $input_path"
	parent_path=$(cd -- "$parent_path" && pwd -P) ||
		die "cannot access backup parent: $parent_path"
	printf '%s/%s\n' "$parent_path" "$base_name"
}

resolve_existing_dir() {
	local input_path=$1

	[[ -d "$input_path" ]] || die "directory does not exist: $input_path"
	(cd -- "$input_path" && pwd -P)
}

assert_backup_outside_repo() {
	local backup_path=$1

	case "$backup_path/" in
	"$REPO_ROOT/"*)
		die "backup directory must be outside repository: $backup_path"
		;;
	esac
}

sha256_file() {
	local path=$1

	if [[ "$HASH_COMMAND" == sha256sum ]]; then
		sha256sum -- "$path" | awk '{print $1}'
	else
		shasum -a 256 -- "$path" | awk '{print $1}'
	fi
}

normalize_spec_path() {
	local path=$1

	path=${path#./}
	case "$path" in
	.trellis/spec/*) ;;
	spec/*)
		path=".trellis/$path"
		;;
	*)
		path=".trellis/spec/$path"
		;;
	esac
	is_safe_relative_path "$path" || die "unsafe spec path: $path"
	[[ "$path" != ".trellis/spec" ]] || die "spec path must name a layer or file"
	printf '%s\n' "$path"
}

read_developer() {
	local developer_file="$REPO_ROOT/.trellis/.developer"
	local developer_line

	if [[ -f "$developer_file" ]]; then
		developer_line=$(sed -n '1p' "$developer_file")
		if [[ "$developer_line" == name=* ]]; then
			DEVELOPER=${developer_line#name=}
		else
			DEVELOPER=$developer_line
		fi
		DEVELOPER_SOURCE='.trellis/.developer'
	else
		DEVELOPER=$(git -C "$REPO_ROOT" config user.name 2>/dev/null || true)
		DEVELOPER_SOURCE='git config user.name'
	fi
	DEVELOPER=${DEVELOPER:-unknown}
	[[ "$DEVELOPER" != *$'\n'* && "$DEVELOPER" != *$'\r'* ]] ||
		die 'developer identity must be a single line'
}

copy_to_backup() {
	local relative_path=$1
	local source_path="$REPO_ROOT/$relative_path"
	local destination_parent

	is_present "$source_path" || die "source disappeared: $relative_path"
	[[ -d "$source_path" || -f "$source_path" || -L "$source_path" ]] ||
		die "unsupported source type: $relative_path"
	destination_parent="$BACKUP_DIR/data/$(dirname -- "$relative_path")"
	mkdir -p -- "$destination_parent"
	cp -a -- "$source_path" "$destination_parent/"
}

write_manifest() {
	local output_file=$1

	(cd -- "$BACKUP_DIR/data" &&
		find . \( -type f -o -type l \) -print | sed 's#^\./##' | sort) >"$output_file"
}

write_checksums() {
	local output_file="$BACKUP_DIR/checksums.sha256"
	local file
	local relative_path

	: >"$output_file"
	while IFS= read -r -d '' file; do
		relative_path=${file#"$BACKUP_DIR/data/"}
		printf '%s  %s\n' "$(sha256_file "$file")" "$relative_path" >>"$output_file"
	done < <(find "$BACKUP_DIR/data" -type f -print0)
	sort -o "$output_file" "$output_file"
}

verify_backup() {
	local current_manifest
	local line
	local expected
	local relative_path
	local target

	current_manifest=$(mktemp "${TMPDIR:-/tmp}/trellis-data-manifest.XXXXXXXXXX")
	TEMP_FILES+=("$current_manifest")
	write_manifest "$current_manifest"
	cmp -s "$BACKUP_DIR/metadata/manifest.txt" "$current_manifest" ||
		die 'backup manifest changed'

	while IFS= read -r line; do
		[[ -n "$line" ]] || continue
		expected=${line%%  *}
		relative_path=${line#*  }
		is_safe_relative_path "$relative_path" || die "unsafe checksum path: $relative_path"
		target="$BACKUP_DIR/data/$relative_path"
		[[ -f "$target" && ! -L "$target" ]] || die "checksum target is not a file: $relative_path"
		[[ "$(sha256_file "$target")" == "$expected" ]] ||
			die "backup checksum mismatch: $relative_path"
	done <"$BACKUP_DIR/checksums.sha256"
}

make_backup_private() {
	local path=$1

	chmod 700 -- "$path"
	find "$path" -type d -exec chmod 700 -- {} +
	find "$path" -maxdepth 1 -type f -exec chmod 600 -- {} +
	if [[ -d "$path/metadata" ]]; then
		find "$path/metadata" -type f -exec chmod 600 -- {} +
	fi
	if [[ -d "$path/after-init" ]]; then
		find "$path/after-init" -type f -exec chmod 600 -- {} +
	fi
}

write_classification() {
	local output_file="$BACKUP_DIR/metadata/classification.txt"

	{
		printf '%s\n' 'Project/personal data backed up by default:'
		printf '  %s/**\n' '.trellis/tasks'
		printf '  %s/**\n' '.trellis/workspace'
		printf '  %s/**\n' "$DEFAULT_SPEC_PATH"
		printf '  .trellis/mainline.md\n'
		printf '  .trellis/.developer\n'
		printf '  .trellis/.current-task\n'
		printf '  .trellis/.runtime/sessions/**\n'
		printf '%s\n' 'Additional project-authored specs included with --spec:'
		printf '  %s\n' "${SPEC_PATHS[@]:-none}"
		printf '%s\n' 'Other .trellis/spec layers are not included unless named with --spec.'
		printf '%s\n' 'Trellis process/runtime not backed up or restored:'
		printf '  %s\n' "${PROTECTED_PATHS[@]}"
		printf '%s\n' 'Files outside .trellis are untouched by this script.'
	} >"$output_file"
}

write_backup_summary() {
	local summary_file="$BACKUP_DIR/summary.txt"

	{
		printf '%s\n' 'Trellis data backup'
		printf 'Repository: %s\n' "$REPO_ROOT"
		printf 'Trellis version: %s\n' "$(sed -n '1p' "$BACKUP_DIR/metadata/trellis-version.txt")"
		printf 'Developer: %s (source: %s)\n' "$DEVELOPER" "$DEVELOPER_SOURCE"
		printf 'Active task pointer: %s\n' "$(sed -n '1p' "$BACKUP_DIR/metadata/active-task.txt")"
		printf 'Task records: %s\n' "$(awk 'END {print NR + 0}' "$BACKUP_DIR/metadata/tasks.tsv")"
		printf 'Included paths:\n'
		printf '  %s\n' "${INCLUDED_PATHS[@]}"
		printf 'Missing optional paths:\n'
		printf '  %s\n' "$(cat "$BACKUP_DIR/metadata/missing-paths.txt")"
		printf 'Classification: metadata/classification.txt\n'
		printf 'Manifest: metadata/manifest.txt\n'
		printf 'Checksums: checksums.sha256\n'
	} >"$summary_file"
}

backup_phase() {
	local repo_input=$1
	local backup_input=$2
	local path
	local safe_repo_name
	local timestamp

	REPO_ROOT=$(resolve_repo_root "$repo_input")
	read_developer
	SPEC_PATHS=()
	for path in "${SPEC_ARGS[@]}"; do
		path=$(normalize_spec_path "$path")
		append_unique SPEC_PATHS "$path"
	done

	INCLUDED_PATHS=()
	for path in "${DATA_PATHS[@]}" "${SPEC_PATHS[@]}"; do
		is_present "$REPO_ROOT/$path" && append_unique INCLUDED_PATHS "$path"
	done
	((${#INCLUDED_PATHS[@]} > 0)) || die 'no project/personal Trellis data found'

	if [[ -n "$backup_input" ]]; then
		BACKUP_DIR=$(resolve_new_backup_dir "$backup_input")
	else
		safe_repo_name=${REPO_ROOT##*/}
		safe_repo_name=$(printf '%s' "$safe_repo_name" | sed 's/[^A-Za-z0-9._-]/-/g')
		timestamp=$(date -u '+%Y%m%d-%H%M%S')
		BACKUP_DIR=$(resolve_new_backup_dir "/tmp/trellis-data-${safe_repo_name}-${timestamp}-$$")
	fi
	assert_backup_outside_repo "$BACKUP_DIR"

	mkdir -- "$BACKUP_DIR" "$BACKUP_DIR/data" "$BACKUP_DIR/metadata"
	: >"$BACKUP_DIR/metadata/missing-paths.txt"
	for path in "${DATA_PATHS[@]}" "${SPEC_PATHS[@]}"; do
		if is_present "$REPO_ROOT/$path"; then
			copy_to_backup "$path"
		else
			printf '%s\n' "$path" >>"$BACKUP_DIR/metadata/missing-paths.txt"
		fi
	done

	printf '%s\n' "$REPO_ROOT" >"$BACKUP_DIR/metadata/repo-root.txt"
	printf '%s\n' "$DEVELOPER" >"$BACKUP_DIR/metadata/developer.txt"
	printf '%s\n' "$DEVELOPER_SOURCE" >"$BACKUP_DIR/metadata/developer-source.txt"
	printf '%s\n' "$(trellis --version)" >"$BACKUP_DIR/metadata/trellis-version.txt"
	printf '%s\n' "${INCLUDED_PATHS[@]}" >"$BACKUP_DIR/metadata/included-paths.txt"
	(cd "$REPO_ROOT" && git status --short) >"$BACKUP_DIR/metadata/git-status.txt"
	if is_present "$REPO_ROOT/.trellis/.current-task"; then
		sed -n '1p' "$REPO_ROOT/.trellis/.current-task" >"$BACKUP_DIR/metadata/active-task.txt"
	else
		printf '%s\n' 'none' >"$BACKUP_DIR/metadata/active-task.txt"
	fi
	: >"$BACKUP_DIR/metadata/tasks.tsv"
	while IFS= read -r -d '' path; do
		printf '%s\n' "${path#"$REPO_ROOT/"}" >>"$BACKUP_DIR/metadata/tasks.tsv"
	done < <(find "$REPO_ROOT/.trellis/tasks" -type f -name task.json -print0 2>/dev/null)
	sort -o "$BACKUP_DIR/metadata/tasks.tsv" "$BACKUP_DIR/metadata/tasks.tsv"
	printf '%s\n' "${SPEC_PATHS[@]}" >"$BACKUP_DIR/metadata/spec-paths.txt"
	write_manifest "$BACKUP_DIR/metadata/manifest.txt"
	write_checksums
	verify_backup
	write_classification
	write_backup_summary
	printf '%s\n' 'backup-complete' >"$BACKUP_DIR/metadata/state"
	make_backup_private "$BACKUP_DIR"

	info 'Backup complete'
	printf 'Backup directory: %s\n' "$BACKUP_DIR"
	printf 'Developer: %s\n' "$DEVELOPER"
	printf 'Active task pointer: %s\n' "$(sed -n '1p' "$BACKUP_DIR/metadata/active-task.txt")"
	printf 'Included paths:\n'
	printf '  %s\n' "${INCLUDED_PATHS[@]}"
	printf 'Summary: %s\n' "$BACKUP_DIR/summary.txt"
	printf 'After manual rm/init, run:\n  %s restore --repo %q --backup-dir %q\n' "$SCRIPT_NAME" "$REPO_ROOT" "$BACKUP_DIR"
}

same_file() {
	local source_path=$1
	local target_path=$2

	if [[ -L "$source_path" || -L "$target_path" ]]; then
		[[ -L "$source_path" && -L "$target_path" ]] || return 1
		[[ "$(readlink -- "$source_path")" == "$(readlink -- "$target_path")" ]]
		return
	fi
	[[ -f "$source_path" && -f "$target_path" ]] && cmp -s "$source_path" "$target_path"
}

ensure_destination_parents() {
	local relative_path=$1
	local parent_rel=${relative_path%/*}
	local current_path="$REPO_ROOT"
	local component
	local -a components=()

	[[ "$parent_rel" != "$relative_path" ]] || return 0
	IFS='/' read -r -a components <<<"$parent_rel"
	for component in "${components[@]}"; do
		current_path="$current_path/$component"
		[[ -L "$current_path" ]] && return 1
	done
	return 0
}

record_restore_path() {
	local array_name=$1
	local log_name=$2
	local relative_path=$3

	append_unique "$array_name" "$relative_path"
	printf '%s\n' "$relative_path" >>"$BACKUP_DIR/metadata/$log_name"
}

restore_file_if_absent() {
	local relative_path=$1
	local source_path="$BACKUP_DIR/data/$relative_path"
	local target_path="$REPO_ROOT/$relative_path"
	local target_parent

	is_present "$source_path" || return 0
	[[ -f "$source_path" || -L "$source_path" ]] ||
		die "unsupported restore type: $relative_path"
	ensure_destination_parents "$relative_path" || {
		record_restore_path CONFLICT_PATHS conflicts.tsv "$relative_path (parent is symlink)"
		return 0
	}
	if ! is_present "$target_path"; then
		target_parent=$(dirname -- "$target_path")
		mkdir -p -- "$target_parent"
		cp -a -- "$source_path" "$target_parent/"
		record_restore_path RESTORED_PATHS restored.tsv "$relative_path"
	elif same_file "$source_path" "$target_path"; then
		record_restore_path IDENTICAL_PATHS identical.tsv "$relative_path"
	else
		record_restore_path CONFLICT_PATHS conflicts.tsv "$relative_path (destination exists and differs)"
	fi
}

restore_tree_if_absent() {
	local relative_path=$1
	local source_root="$BACKUP_DIR/data/$relative_path"
	local source_file
	local child_rel

	is_present "$source_root" || return 0
	if [[ ! -d "$source_root" || -L "$source_root" ]]; then
		restore_file_if_absent "$relative_path"
		return 0
	fi
	while IFS= read -r -d '' source_file; do
		child_rel=${source_file#"$source_root/"}
		restore_file_if_absent "$relative_path/$child_rel"
	done < <(find "$source_root" \( -type f -o -type l \) -print0)
}

replace_personal_state() {
	local relative_path=$1
	local source_path="$BACKUP_DIR/data/$relative_path"
	local target_path="$REPO_ROOT/$relative_path"
	local after_init_path
	local target_parent

	is_present "$source_path" || return 0
	[[ -f "$source_path" || -L "$source_path" ]] ||
		die "unsupported personal state type: $relative_path"
	ensure_destination_parents "$relative_path" || {
		record_restore_path CONFLICT_PATHS conflicts.tsv "$relative_path (parent is symlink)"
		return 0
	}
	if ! is_present "$target_path"; then
		target_parent=$(dirname -- "$target_path")
		mkdir -p -- "$target_parent"
		cp -a -- "$source_path" "$target_parent/"
		record_restore_path RESTORED_PATHS restored.tsv "$relative_path"
	elif same_file "$source_path" "$target_path"; then
		record_restore_path IDENTICAL_PATHS identical.tsv "$relative_path"
	elif [[ -L "$target_path" || -d "$target_path" ]]; then
		record_restore_path CONFLICT_PATHS conflicts.tsv "$relative_path (destination type differs)"
	elif [[ ! -f "$target_path" ]]; then
		record_restore_path CONFLICT_PATHS conflicts.tsv "$relative_path (destination type differs)"
	else
		after_init_path="$BACKUP_DIR/after-init/$relative_path"
		mkdir -p -- "$(dirname -- "$after_init_path")"
		cp -a -- "$target_path" "$(dirname -- "$after_init_path")/"
		target_parent=$(dirname -- "$target_path")
		cp -a -- "$source_path" "$target_parent/"
		record_restore_path REPLACED_PATHS replaced.tsv "$relative_path"
	fi
}

write_restore_summary() {
	local summary_file="$BACKUP_DIR/restore-summary.txt"

	{
		printf '%s\n' 'Trellis data restore'
		printf 'Repository: %s\n' "$REPO_ROOT"
		printf 'Backup: %s\n' "$BACKUP_DIR"
		printf 'Developer: %s\n' "$(sed -n '1p' "$BACKUP_DIR/metadata/developer.txt")"
		printf 'Restored paths:\n'
		printf '  %s\n' "${RESTORED_PATHS[@]:-none}"
		printf 'Replaced personal state:\n'
		printf '  %s\n' "${REPLACED_PATHS[@]:-none}"
		printf 'Identical paths:\n'
		printf '  %s\n' "${IDENTICAL_PATHS[@]:-none}"
		printf 'Conflicts requiring review:\n'
		printf '  %s\n' "${CONFLICT_PATHS[@]:-none}"
		printf 'Git status after restore: metadata/git-status-after.txt\n'
		printf 'Protected Trellis paths were not restored.\n'
		printf 'No git staging or commit was performed.\n'
	} >"$summary_file"
}

restore_phase() {
	local repo_input=$1
	local backup_input=$2
	local path
	local state

	BACKUP_DIR=$(resolve_existing_dir "$backup_input")
	[[ -d "$BACKUP_DIR/data" && -d "$BACKUP_DIR/metadata" ]] ||
		die "invalid backup directory: $BACKUP_DIR"
	state=$(sed -n '1p' "$BACKUP_DIR/metadata/state" 2>/dev/null || true)
	[[ "$state" == backup-complete ]] || die "backup is not ready: state=$state"
	REPO_ROOT=$(resolve_repo_root "$repo_input")
	assert_backup_outside_repo "$BACKUP_DIR"
	[[ "$(sed -n '1p' "$BACKUP_DIR/metadata/repo-root.txt")" == "$REPO_ROOT" ]] ||
		die 'backup belongs to a different repository'
	verify_backup

	: >"$BACKUP_DIR/metadata/restored.tsv"
	: >"$BACKUP_DIR/metadata/replaced.tsv"
	: >"$BACKUP_DIR/metadata/identical.tsv"
	: >"$BACKUP_DIR/metadata/conflicts.tsv"
	RESTORED_PATHS=()
	REPLACED_PATHS=()
	IDENTICAL_PATHS=()
	CONFLICT_PATHS=()

	while IFS= read -r path; do
		[[ -n "$path" ]] || continue
		case "$path" in
		.trellis/.developer | .trellis/.current-task)
			replace_personal_state "$path"
			;;
		*)
			restore_tree_if_absent "$path"
			;;
		esac
	done <"$BACKUP_DIR/metadata/included-paths.txt"

	(cd "$REPO_ROOT" && git status --short) >"$BACKUP_DIR/metadata/git-status-after.txt"
	write_restore_summary
	printf '%s\n' 'restore-complete' >"$BACKUP_DIR/metadata/state"
	make_backup_private "$BACKUP_DIR"

	info 'Restore complete'
	printf 'Backup directory: %s\n' "$BACKUP_DIR"
	printf 'Restored paths: %s\n' "${#RESTORED_PATHS[@]}"
	printf 'Replaced personal state: %s\n' "${#REPLACED_PATHS[@]}"
	printf 'Conflicts: %s\n' "${#CONFLICT_PATHS[@]}"
	printf 'Git status after restore: %s\n' "$BACKUP_DIR/metadata/git-status-after.txt"
	printf 'Summary: %s\n' "$BACKUP_DIR/restore-summary.txt"
	if [[ ${#CONFLICT_PATHS[@]} -gt 0 ]]; then
		warn 'restore completed with conflicts; inspect metadata/conflicts.tsv'
		return 1
	fi
}

parse_backup_args() {
	REPO_INPUT='.'
	BACKUP_INPUT=''
	SPEC_ARGS=()
	while [[ $# -gt 0 ]]; do
		case "$1" in
		--repo)
			[[ $# -ge 2 ]] || die '--repo requires a path'
			REPO_INPUT=$2
			shift 2
			;;
		--backup-dir)
			[[ $# -ge 2 ]] || die '--backup-dir requires a path'
			BACKUP_INPUT=$2
			shift 2
			;;
		--spec)
			[[ $# -ge 2 ]] || die '--spec requires a path'
			SPEC_ARGS+=("$2")
			shift 2
			;;
		-h | --help)
			usage
			exit 0
			;;
		*)
			die "unknown backup option: $1"
			;;
		esac
	done
}

parse_restore_args() {
	REPO_INPUT='.'
	BACKUP_INPUT=''
	while [[ $# -gt 0 ]]; do
		case "$1" in
		--repo)
			[[ $# -ge 2 ]] || die '--repo requires a path'
			REPO_INPUT=$2
			shift 2
			;;
		--backup-dir)
			[[ $# -ge 2 ]] || die '--backup-dir requires a path'
			BACKUP_INPUT=$2
			shift 2
			;;
		-h | --help)
			usage
			exit 0
			;;
		*)
			die "unknown restore option: $1"
			;;
		esac
	done
	[[ -n "$BACKUP_INPUT" ]] || die 'restore requires --backup-dir'
}

main() {
	local subcommand=${1:-}

	require_commands
	[[ -n "$subcommand" ]] || {
		usage
		return 1
	}
	shift
	case "$subcommand" in
	backup)
		parse_backup_args "$@"
		backup_phase "$REPO_INPUT" "$BACKUP_INPUT"
		;;
	restore)
		parse_restore_args "$@"
		restore_phase "$REPO_INPUT" "$BACKUP_INPUT"
		;;
	-h | --help)
		usage
		;;
	*)
		die "unknown subcommand: $subcommand"
		;;
	esac
}

main "$@"
