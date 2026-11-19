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
readonly CODEX_DIR="${CODEX_HOME:-${HOME:?HOME is not set}/.codex}"
readonly -a MANAGED_LINK_TARGETS=(
	"$CODEX_DIR/AGENTS.md"
	"$CODEX_DIR/agents"
	"$CODEX_DIR/rules/default.rules"
)

usage() {
	printf 'Usage: %s [--help]\n\n' "$SCRIPT_NAME" >&2
	printf 'Update managed TOML blocks from sync.config.json and back up existing profiles.\n' >&2
	printf 'Set CODEX_HOME to select a target directory. Requires Python 3.11 or later.\n' >&2
}

die() {
	printf 'Error: %s\n' "$*" >&2
	exit 1
}

require_command() {
	command -v "$1" >/dev/null 2>&1 || die "required command not found: $1"
}

link_path() {
	local source_path=$1
	local target_path=$2
	local managed_target
	local target_is_managed=false

	[[ -e "$source_path" || -L "$source_path" ]] || die "source path not found: $source_path"

	for managed_target in "${MANAGED_LINK_TARGETS[@]}"; do
		if [[ "$target_path" == "$managed_target" ]]; then
			target_is_managed=true
			break
		fi
	done
	[[ "$target_is_managed" == true ]] || die "refusing to replace unexpected target: $target_path"

	if [[ -L "$target_path" && "$(readlink -- "$target_path")" == "$source_path" ]]; then
		return 0
	fi
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

	local source_config="$SCRIPT_DIR/sync.config.json"
	local config_updater="$SCRIPT_DIR/sync_config.py"
	local source_agents="$SCRIPT_DIR/agents"
	local source_rules="$SCRIPT_DIR/codex.rules"
	local source_agents_file="$SCRIPT_DIR/agents.md"
	local source_opencode_catalog="$SCRIPT_DIR/opencode.models.json"

	local command_name
	for command_name in cmp cp ln mkdir python3 readlink rm; do
		require_command "$command_name"
	done
	python3 -c 'import tomllib' 2>/dev/null || die "Python 3.11 or later is required"

	[[ -f "$source_config" ]] || die "source file not found: $source_config"
	[[ -f "$config_updater" ]] || die "source file not found: $config_updater"
	[[ -d "$source_agents" ]] || die "source directory not found: $source_agents"
	[[ -f "$source_rules" ]] || die "source file not found: $source_rules"
	[[ -f "$source_agents_file" ]] || die "source file not found: $source_agents_file"
	[[ -f "$source_opencode_catalog" ]] || die "source file not found: $source_opencode_catalog"

	mkdir -p -- "$CODEX_DIR/rules"
	python3 "$config_updater" "$source_config" "$CODEX_DIR"
	if ! cmp -s -- "$source_opencode_catalog" "$CODEX_DIR/opencode.models.json"; then
		cp -- "$source_opencode_catalog" "$CODEX_DIR/opencode.models.json"
	fi
	link_path "$source_agents" "$CODEX_DIR/agents"
	link_path "$source_rules" "$CODEX_DIR/rules/default.rules"
	link_path "$source_agents_file" "$CODEX_DIR/AGENTS.md"

	printf 'Synced Codex configuration to %s\n' "$CODEX_DIR"
}

main "$@"
