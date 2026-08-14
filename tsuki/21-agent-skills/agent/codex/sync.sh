#!/usr/bin/env bash
set -Eeuo pipefail

readonly SCRIPT_NAME="${0##*/}"
script_dir_path="$(
	case "${BASH_SOURCE[0]}" in
	*/*) cd -- "${BASH_SOURCE[0]%/*}" ;;
	*) cd -- . ;;
	esac
	pwd -P
)"
readonly SCRIPT_DIR="$script_dir_path"
unset script_dir_path
readonly CODEX_HOME="${HOME:?HOME is not set}/.codex"

temp_dir=""

usage() {
	printf 'Usage: %s [--help]\n' "$SCRIPT_NAME" >&2
}

die() {
	printf 'Error: %s\n' "$*" >&2
	exit 1
}

require_command() {
	command -v "$1" >/dev/null 2>&1 || die "required command not found: $1"
}

cleanup() {
	if [[ -n "$temp_dir" && -d "$temp_dir" ]]; then
		case "$temp_dir" in
		"$CODEX_HOME"/.codex-sync.*)
			rm -rf -- "$temp_dir"
			;;
		esac
	fi
}

validate_dynamic_sections() {
	local config_path=$1

	[[ -f "$config_path" ]] || return 0

	awk '
        /^[[:space:]]*\[(hooks[.]state|projects[.])/ {
            header = $0
            sub(/^[[:space:]]*/, "", header)
            sub(/[[:space:]]*$/, "", header)
            if (seen[header]++) {
                printf "Error: duplicate user-managed TOML table on line %d\\n", NR > "/dev/stderr"
                exit 1
            }
        }
    ' "$config_path"
}

write_config() {
	local source_config=$1
	local target_config=$2
	local source_copy="$temp_dir/source-config.toml"
	local managed_config="$temp_dir/managed-config.toml"
	local preserved_config="$temp_dir/preserved-config.toml"

	cp -- "$source_config" "$source_copy"

	awk '
        /^[[:space:]]*\[(hooks[.]state|projects[.])/ { exit }
        { print }
    ' "$source_copy" >"$managed_config"

	if [[ -f "$target_config" ]]; then
		awk '
            /^[[:space:]]*\[(hooks[.]state|projects[.])/ { found = 1 }
            found { print }
        ' "$target_config" >"$preserved_config"
	else
		: >"$preserved_config"
	fi

	if [[ -s "$preserved_config" ]]; then
		[[ ! -s "$managed_config" ]] || printf '\n' >>"$managed_config"
		cat -- "$preserved_config" >>"$managed_config"
	fi

	mv -- "$managed_config" "$temp_dir/config.toml"
	mv -- "$temp_dir/config.toml" "$target_config"
}

link_path() {
	local source_path=$1
	local target_path=$2

	[[ -e "$source_path" || -L "$source_path" ]] || die "source path not found: $source_path"

	case "$target_path" in
	"$CODEX_HOME/AGENTS.md" | "$CODEX_HOME/agents" | "$CODEX_HOME/rules/default.rules") ;;
	*) die "refusing to replace unexpected target: $target_path" ;;
	esac

	if [[ -e "$target_path" || -L "$target_path" ]]; then
		rm -rf -- "$target_path"
	fi
	ln -s "$source_path" "$target_path"
}

main() {
	while [[ $# -gt 0 ]]; do
		case "$1" in
		--help | -h)
			usage
			return 0
			;;
		*)
			usage
			die "unknown option: $1"
			;;
		esac
	done

	local source_config="$SCRIPT_DIR/config.toml"
	local source_agents="$SCRIPT_DIR/agents"
	local source_rules="$SCRIPT_DIR/codex.rules"
	local source_agents_file="$SCRIPT_DIR/agents.md"
	local target_config="$CODEX_HOME/config.toml"

	for command_name in awk cat cp ln mkdir mktemp mv rm; do
		require_command "$command_name"
	done

	[[ -f "$source_config" ]] || die "source file not found: $source_config"
	[[ -d "$source_agents" ]] || die "source directory not found: $source_agents"
	[[ -f "$source_rules" ]] || die "source file not found: $source_rules"
	[[ -f "$source_agents_file" ]] || die "source file not found: $source_agents_file"

	mkdir -p -- "$CODEX_HOME/rules"
	temp_dir=$(mktemp -d "$CODEX_HOME/.codex-sync.XXXXXXXXXX")
	trap cleanup EXIT

	validate_dynamic_sections "$target_config"
	write_config "$source_config" "$target_config"
	link_path "$source_agents" "$CODEX_HOME/agents"
	link_path "$source_rules" "$CODEX_HOME/rules/default.rules"
	link_path "$source_agents_file" "$CODEX_HOME/AGENTS.md"

	printf 'Synced Codex configuration to %s\n' "$CODEX_HOME"
}

main "$@"
