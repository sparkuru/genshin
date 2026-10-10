#!/usr/bin/env bash
set -Eeuo pipefail

readonly SCRIPT_NAME="${0##*/}"
# Keep machine-specific variables here; source assignments for them are skipped.
readonly -a UNSYNCED_VARIABLES=(
	OPENCODE_API_KEY
	OPENAI_API_KEY
	ANTHROPIC_API_KEY
	ANTHROPIC_AUTH_TOKEN
)
readonly STYLE_RESET=$'\033[0m'
readonly STYLE_TITLE=$'\033[1;36m'
readonly STYLE_SUCCESS=$'\033[0;32m'
readonly STYLE_ERROR=$'\033[1;31m'

temp_dir=""
staged_path=""

color_text() {
	local style=$1 text=$2
	if [[ -n "${NO_COLOR:-}" || ! -t 1 ]]; then
		printf '%s' "$text"
	else
		printf '%s%s%s' "$style" "$text" "$STYLE_RESET"
	fi
}

usage() {
	printf '%s\n' "$(color_text "$STYLE_TITLE" "Usage: $SCRIPT_NAME [--dry-run] [--target-file PATH]")" >&2
	cat >&2 <<'USAGE'

Sync agent-envs to ~/.config/.agent-envs, replacing shared configuration and
preserving machine-local single-line assignments listed in UNSYNCED_VARIABLES
at the top of this script (including OPENCODE_APT_KEY). Source assignments for
these variables are excluded. The current process environment is not copied.

  --dry-run          Show the planned change without writing files.
  --target-file PATH Override the destination with an absolute file path.
  --help, -h         Show this help.

Local assignments are appended after shared configuration. Other local code
and settings are replaced. Changed destinations are backed up before writing;
the resulting file has mode 600. Multiline credentials are not supported.
USAGE
}

die() {
	printf '%s\n' "$(color_text "$STYLE_ERROR" "Error: $*")" >&2
	exit 1
}

require_command() {
	command -v "$1" >/dev/null 2>&1 || die "required command not found: $1"
}

cleanup() {
	[[ -z "$staged_path" || ! -f "$staged_path" ]] || rm -f -- "$staged_path"
	case "$temp_dir" in
	"${TMPDIR:-/tmp}"/agent-envs-sync.*)
		[[ ! -d "$temp_dir" ]] || rm -rf -- "$temp_dir"
		;;
	esac
}

select_env_lines() {
	local input_path=$1 output_path=$2 mode=$3 preserved_names=$4
	awk -v preserved_names="$preserved_names" -v mode="$mode" '
        BEGIN {
            count = split(preserved_names, names, ",")
            for (i = 1; i <= count; i++) preserve[names[i]] = 1
        }
        {
            line = $0
            sub(/^[ \t]*/, "", line)
            sub(/^export[ \t]+/, "", line)
            name = ""
            if (line ~ /^[A-Za-z_][A-Za-z0-9_]*=/) {
                name = line
                sub(/=.*/, "", name)
            }
            if (mode == "all") {
                if (name != "") print
                next
            }
            if (mode == "shared") {
                if (!(name in preserve)) print
                next
            }
            if (!(name in preserve)) next
            if ($0 ~ /\\$/) {
                printf "Error: multiline local assignment for %s is unsupported\n", name > "/dev/stderr"
                exit 1
            }
            print
        }
    ' "$input_path" >"$output_path"
}

main() {
	local dry_run=false preserved_names="" variable_name
	for variable_name in "${UNSYNCED_VARIABLES[@]}"; do
		[[ "$variable_name" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]] || die "invalid name in UNSYNCED_VARIABLES"
		preserved_names+="${preserved_names:+,}$variable_name"
	done
	local target_path="${HOME:?HOME is not set}/.config/.agent-envs"
	while [[ $# -gt 0 ]]; do
		case "$1" in
		--dry-run) dry_run=true ;;
		--target-file)
			[[ $# -ge 2 && -n "$2" ]] || die "--target-file requires a path"
			target_path=$2
			shift
			;;
		--help | -h)
			usage
			return 0
			;;
		*) die "unknown option: $1 (see --help)" ;;
		esac
		shift
	done

	local command_name
	for command_name in awk bash cat chmod cmp cp dirname mkdir mktemp mv rm; do
		require_command "$command_name"
	done
	local script_dir source_path target_dir
	script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
	source_path="$script_dir/agent-envs"
	[[ -f "$source_path" ]] || die "source file not found: $source_path"
	[[ "$target_path" == /* && "$target_path" != */ ]] || die "target must be an absolute file path"
	[[ ! -e "$target_path" || -f "$target_path" ]] || die "target is not a regular file: $target_path"
	[[ ! -L "$target_path" || -f "$target_path" ]] || die "target is a broken symlink: $target_path"
	[[ ! "$source_path" -ef "$target_path" ]] || die "target must differ from the source file"
	# Syntax checks must not echo credential-bearing source lines on failure.
	bash -n "$source_path" 2>/dev/null || die "source shell syntax is invalid"

	umask 077
	temp_dir=$(mktemp -d "${TMPDIR:-/tmp}/agent-envs-sync.XXXXXXXXXX")
	trap cleanup EXIT
	: >"$temp_dir/local-envs"
	if [[ -f "$target_path" ]]; then
		select_env_lines "$target_path" "$temp_dir/local-envs" all "$preserved_names"
	fi
	select_env_lines "$temp_dir/local-envs" "$temp_dir/local-credentials" local "$preserved_names"
	bash -n "$temp_dir/local-credentials" 2>/dev/null || die "local credentials must use complete single-line assignments"
	select_env_lines "$source_path" "$temp_dir/agent-envs" shared "$preserved_names"
	if [[ -s "$temp_dir/local-credentials" ]]; then
		printf '\n' >>"$temp_dir/agent-envs"
		cat -- "$temp_dir/local-credentials" >>"$temp_dir/agent-envs"
	fi
	bash -n "$temp_dir/agent-envs" 2>/dev/null || die "merged shell syntax is invalid"
	if [[ -f "$target_path" && ! -L "$target_path" ]] && cmp -s -- "$temp_dir/agent-envs" "$target_path"; then
		[[ "$dry_run" == true ]] || chmod 600 -- "$target_path"
		printf '%s\n' "$(color_text "$STYLE_SUCCESS" 'Agent environment configuration is already synced.')"
		return 0
	fi
	printf 'Sync shared configuration and preserve local credentials: %s\n' "$target_path"
	[[ "$dry_run" != true ]] || return 0

	target_dir=$(dirname -- "$target_path")
	mkdir -p -- "$target_dir"
	local backup_path
	if [[ -f "$target_path" ]]; then
		backup_path=$(mktemp "${TMPDIR:-/tmp}/${target_path##*/}.backup.XXXXXXXXXX")
		cp -- "$target_path" "$backup_path"
		chmod 600 -- "$backup_path"
		printf 'Backup: %s\n' "$backup_path"
	fi
	staged_path=$(mktemp "$target_dir/.agent-envs-sync.XXXXXXXXXX")
	cp -- "$temp_dir/agent-envs" "$staged_path"
	chmod 600 -- "$staged_path"
	mv -f -- "$staged_path" "$target_path"
	staged_path=""
	printf '%s\n' "$(color_text "$STYLE_SUCCESS" "Synced agent environment configuration to $target_path")"
}

main "$@"
