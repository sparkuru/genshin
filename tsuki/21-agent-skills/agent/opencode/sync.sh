#!/usr/bin/env bash
set -Eeuo pipefail

readonly SCRIPT_NAME="${0##*/}"
readonly STYLE_RESET=$'\033[0m'
readonly STYLE_SUCCESS=$'\033[0;32m'
readonly STYLE_ERROR=$'\033[1;31m'
readonly STYLE_TITLE=$'\033[1;36m'

temp_dir=""

cleanup() {
	case "$temp_dir" in
	"${TMPDIR:-/tmp}"/opencode-sync.*)
		[[ ! -d "$temp_dir" ]] || rm -rf -- "$temp_dir"
		;;
	esac
}

color_text() {
	local style=$1
	local text=$2

	if [[ -n "${NO_COLOR:-}" || ! -t 1 ]]; then
		printf '%s' "$text"
	else
		printf '%s%s%s' "$style" "$text" "$STYLE_RESET"
	fi
}

usage() {
	printf '%s\n' "$(color_text "$STYLE_TITLE" "Usage: $SCRIPT_NAME [--force] [--dry-run] [--target-dir DIR]")" >&2
	cat >&2 <<'USAGE'

Copy repository-owned opencode.jsonc and tui.json, and link AGENTS.md and
agents/sub_agent.md into the global OpenCode configuration directory.

  --force           Back up and replace conflicting managed files.
  --dry-run         Show planned changes without writing files.
  --target-dir DIR  Override ${XDG_CONFIG_HOME:-$HOME/.config}/opencode.
  --help, -h        Show this help.

Existing opencode.json, tui.jsonc, other agents, plugins, dependency files,
skills, credentials, and runtime data are left in place. Local tui.jsonc
settings are loaded after the managed tui.json, including Herdr integration.
Managed config files are replaced in full; keep machine-specific settings
in the unmanaged companion files. Conflicts require --force.
USAGE
}

die() {
	printf '%s\n' "$(color_text "$STYLE_ERROR" "Error: $*")" >&2
	exit 1
}

require_command() {
	command -v "$1" >/dev/null 2>&1 || die "required command not found: $1"
}

is_current() {
	local source_path=$1
	local target_path=$2
	if [[ "$source_path" == "$script_dir/"*.json* ]]; then
		[[ -f "$target_path" && ! -L "$target_path" ]] && cmp -s -- "$source_path" "$target_path"
	else
		[[ -L "$target_path" && "$(readlink -- "$target_path")" == "$source_path" ]]
	fi
}

main() {
	local force=false dry_run=false
	local script_dir target_dir
	target_dir="${XDG_CONFIG_HOME:-${HOME:?HOME is not set}/.config}/opencode"

	while [[ $# -gt 0 ]]; do
		case "$1" in
		--force) force=true ;;
		--dry-run) dry_run=true ;;
		--target-dir)
			[[ $# -ge 2 && -n "$2" ]] || die "--target-dir requires a directory"
			target_dir=$2
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
	for command_name in cat cmp cp dirname ln mkdir mktemp mv readlink rm; do
		require_command "$command_name"
	done
	script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
	[[ "$target_dir" == /* && "$target_dir" != / ]] || die "target directory must be an absolute path other than /"
	[[ ! -e "$target_dir" || -d "$target_dir" ]] || die "target is not a directory: $target_dir"
	if [[ -d "$target_dir" ]]; then
		target_dir=$(cd -- "$target_dir" && pwd -P)
	fi
	[[ "$target_dir" != "$script_dir" ]] || die "target directory must differ from the source directory"
	[[ ! -e "$target_dir/agents" || -d "$target_dir/agents" ]] || die "agents target is not a directory"
	[[ ! -L "$target_dir/agents" ]] || die "refusing to write through an agents directory symlink"

	local -a source_paths=(
		"$script_dir/opencode.jsonc"
		"$script_dir/tui.json"
		"$script_dir/agents.md"
		"$script_dir/agents/sub_agent.md"
	)
	local -a target_names=(opencode.jsonc tui.json AGENTS.md agents/sub_agent.md)
	local -a pending_indices=()
	local index source_path target_path
	local conflicts=false

	for index in "${!source_paths[@]}"; do
		source_path=${source_paths[$index]}
		target_path="$target_dir/${target_names[$index]}"
		[[ -f "$source_path" ]] || die "source file not found: $source_path"
		[[ ! -d "$target_path" ]] || die "managed target is a directory: $target_path"
		[[ ! -e "$target_path" || -f "$target_path" || -L "$target_path" ]] || die "unsupported managed target: $target_path"
		if is_current "$source_path" "$target_path"; then
			continue
		fi
		pending_indices+=("$index")
		if [[ -e "$target_path" || -L "$target_path" ]]; then
			conflicts=true
			printf 'Replace (backup first): %s\n' "$target_path"
		else
			printf 'Create: %s\n' "$target_path"
		fi
	done

	if [[ "$dry_run" == true ]]; then
		return 0
	fi
	[[ "$conflicts" != true || "$force" == true ]] || die "managed files conflict; rerun with --force to back them up and replace them"
	if [[ ${#pending_indices[@]} -eq 0 ]]; then
		printf '%s\n' "$(color_text "$STYLE_SUCCESS" 'OpenCode configuration is already synced.')"
		return 0
	fi

	umask 077
	temp_dir=$(mktemp -d "${TMPDIR:-/tmp}/opencode-sync.XXXXXXXXXX")
	trap cleanup EXIT
	cp -- "$script_dir/opencode.jsonc" "$temp_dir/opencode.jsonc"
	cp -- "$script_dir/tui.json" "$temp_dir/tui.json"
	mkdir -p -- "$target_dir/agents"
	local backup_dir=""
	if [[ "$conflicts" == true ]]; then
		backup_dir=$(mktemp -d "$target_dir/.opencode-sync-backup.XXXXXXXXXX")
		mkdir -- "$backup_dir/agents"
		for index in "${pending_indices[@]}"; do
			target_path="$target_dir/${target_names[$index]}"
			if [[ -e "$target_path" || -L "$target_path" ]]; then
				cp -Pp -- "$target_path" "$backup_dir/${target_names[$index]}"
			fi
		done
		printf 'Backup: %s\n' "$backup_dir"
	fi

	for index in "${pending_indices[@]}"; do
		source_path=${source_paths[$index]}
		target_path="$target_dir/${target_names[$index]}"
		if [[ "$index" -lt 2 ]]; then
			# Replace the path rather than following an existing symlink.
			mv -f -- "$temp_dir/${target_names[$index]}" "$target_path"
		else
			ln -sfn -- "$source_path" "$target_path"
		fi
	done
	printf '%s\n' "$(color_text "$STYLE_SUCCESS" "Synced OpenCode configuration to $target_dir")"
}

main "$@"
