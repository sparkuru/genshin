#!/usr/bin/env bash

set -Eeuo pipefail

readonly SCRIPT_NAME=${0##*/}
readonly SOURCE_DIR=/home/wkyuu/cargo/repo/
readonly REMOTE_HOST=wkyuu@192.168.9.3
readonly DESTINATION_DIR=/home/wkyuu/cargo/repo/
readonly SSH_COMMAND='ssh -F /dev/null -o BatchMode=yes -o StrictHostKeyChecking=yes -o ConnectTimeout=10'
readonly STYLE_RESET=$'\033[0m'
readonly STYLE_SUCCESS=$'\033[0;32m'
readonly STYLE_ERROR=$'\033[1;31m'

color_text() {
	local style=$1
	local message=$2

	if [[ -n ${NO_COLOR:-} || ! -t 1 ]]; then
		printf '%s' "$message"
		return
	fi

	printf '%s%s%s' "$style" "$message" "$STYLE_RESET"
}

info() {
	printf '%s\n' "$(color_text "$STYLE_SUCCESS" "$*")"
}

die() {
	printf '%s\n' "$(color_text "$STYLE_ERROR" "Error: $*")" >&2
	exit 1
}

usage() {
	printf 'Usage: %s [--dry-run]\n' "$SCRIPT_NAME" >&2
}

require_command() {
	command -v "$1" >/dev/null 2>&1 || die "required command not found: $1"
}

main() {
	local dry_run=false
	local -a rsync_args=(
		--archive
		--hard-links
		--acls
		--xattrs
		--delete-delay
		--exclude='*.sock'
		--human-readable
		'--info=progress2,stats2'
	)

	while [[ $# -gt 0 ]]; do
		case "$1" in
		--dry-run)
			dry_run=true
			shift
			;;
		--help | -h)
			usage
			return 0
			;;
		*)
			die "unknown option: $1"
			;;
		esac
	done

	require_command rsync
	require_command ssh
	[[ -d "$SOURCE_DIR" ]] || die "source directory not found: $SOURCE_DIR"

	if "$dry_run"; then
		rsync_args+=(--dry-run)
		info "Previewing synchronization: $SOURCE_DIR -> $REMOTE_HOST:$DESTINATION_DIR"
	else
		info "Synchronizing: $SOURCE_DIR -> $REMOTE_HOST:$DESTINATION_DIR"
	fi

	rsync "${rsync_args[@]}" -e "$SSH_COMMAND" "$SOURCE_DIR" "$REMOTE_HOST:$DESTINATION_DIR"
	info "Synchronization completed."
}

main "$@"
