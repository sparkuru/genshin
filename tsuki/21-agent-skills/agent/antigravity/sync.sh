#!/usr/bin/env bash
set -Eeuo pipefail

readonly SCRIPT_NAME="${0##*/}"
readonly STYLE_RESET=$'\033[0m'
readonly STYLE_TITLE=$'\033[1;36m'
readonly STYLE_ERROR=$'\033[1;31m'

color_text() {
	local style=$1
	local message=$2
	if [[ -n "${NO_COLOR:-}" || ! -t 1 ]]; then
		printf '%s' "$message"
	else
		printf '%s%s%s' "$style" "$message" "$STYLE_RESET"
	fi
}

usage() {
	printf '%s\n' "$(color_text "$STYLE_TITLE" "Usage: $SCRIPT_NAME [--dry-run] [--force] [--target-dir DIR]")"
	cat <<'USAGE'

Merge settings.managed.json into Antigravity CLI settings and link the global
AGENTS.md. Other settings, MCP servers, skills, credentials and runtime data
remain local. The global instructions also apply to Antigravity App.

  --dry-run         Show changes without writing files.
  --force           Back up and replace a conflicting AGENTS.md.
  --target-dir DIR  Override the Gemini directory (default: $HOME/.gemini).
  --help, -h        Show this help.

Changed settings are backed up before replacement. Managed allow rules come
first, followed by additional local rules. Removing a managed allow rule from
the repository does not revoke a rule already present locally. Other managed
settings are restored to their repository values on the next sync.
USAGE
}

die() {
	printf '%s\n' "$(color_text "$STYLE_ERROR" "Error: $*")" >&2
	exit 1
}

main() {
	local dry_run=false force=false target_dir script_dir
	target_dir="${HOME:?HOME is not set}/.gemini"

	while [[ $# -gt 0 ]]; do
		case "$1" in
		--dry-run) dry_run=true ;;
		--force) force=true ;;
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

	command -v python3 >/dev/null 2>&1 || die "python3 is required"
	script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
	exec python3 "$script_dir/sync_config.py" "$script_dir" "$target_dir" "$dry_run" "$force"
}

main "$@"
