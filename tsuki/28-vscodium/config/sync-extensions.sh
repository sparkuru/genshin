#!/usr/bin/env bash
set -Eeuo pipefail

readonly SCRIPT_NAME=${0##*/}
readonly STYLE_RESET=$'\033[0m'
readonly STYLE_SUCCESS=$'\033[0;32m'
readonly STYLE_ERROR=$'\033[1;31m'

script_dir=$(dirname -- "$0")
SCRIPT_DIR=$(cd -- "$script_dir" && pwd)
readonly SCRIPT_DIR
readonly CONFIG_DIR="$SCRIPT_DIR"
readonly EXTENSIONS_FILE="$CONFIG_DIR/extensions.txt"

tmp_file=''

usage() {
	printf 'Usage: %s [--help]\n' "$SCRIPT_NAME" >&2
	printf '\nRefresh config/extensions.txt from installed VSCodium extensions.\n' >&2
}

color_text() {
	local style=$1
	local text=$2

	if [[ -n "${NO_COLOR:-}" || ! -t 1 ]]; then
		printf '%s' "$text"
		return
	fi

	printf '%s%s%s' "$style" "$text" "$STYLE_RESET"
}

info() {
	printf '%s\n' "$(color_text "$STYLE_SUCCESS" "$*")"
}

die() {
	if [[ -n "${NO_COLOR:-}" || ! -t 2 ]]; then
		printf 'Error: %s\n' "$*" >&2
	else
		printf '%sError: %s%s\n' "$STYLE_ERROR" "$*" "$STYLE_RESET" >&2
	fi
	exit 1
}

require_command() {
	command -v "$1" >/dev/null 2>&1 || die "required command not found: $1"
}

cleanup() {
	if [[ -n "$tmp_file" && -f "$tmp_file" ]]; then
		rm -- "$tmp_file"
	fi
}

parse_arguments() {
	while [[ $# -gt 0 ]]; do
		case "$1" in
		--help | -h)
			usage
			exit 0
			;;
		*)
			die "unknown argument: $1"
			;;
		esac
	done
}

main() {
	local codium_bin=${CODIUM_BIN:-codium}
	local extension_count

	parse_arguments "$@"
	[[ -d "$CONFIG_DIR" ]] || die "configuration directory not found: $CONFIG_DIR"
	require_command "$codium_bin"
	require_command cmp
	require_command mktemp
	require_command mv
	require_command sort
	require_command wc

	tmp_file=$(mktemp "$CONFIG_DIR/.extensions.txt.XXXXXXXX")
	trap cleanup EXIT
	"$codium_bin" --list-extensions | LC_ALL=C sort -u >"$tmp_file"
	extension_count=$(wc -l <"$tmp_file")

	if [[ -f "$EXTENSIONS_FILE" ]] && cmp -s "$tmp_file" "$EXTENSIONS_FILE"; then
		info "Extension manifest unchanged: $extension_count entries"
		return
	fi

	mv -- "$tmp_file" "$EXTENSIONS_FILE"
	tmp_file=''
	info "Extension manifest synchronized: $extension_count entries"
}

main "$@"
