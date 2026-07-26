#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_NAME=$(basename "$0")
readonly SCRIPT_NAME
readonly DEFAULT_DEVICE="192.168.9.13"
readonly DEFAULT_PORT="5555"
readonly WINDOW_WIDTH="640"
readonly WINDOW_HEIGHT="1400"

usage() {
	printf 'Usage: %s [DEVICE[:PORT]]\n' "$SCRIPT_NAME" >&2
}

die() {
	printf 'Error: %s\n' "$*" >&2
	exit 1
}

require_command() {
	command -v "$1" >/dev/null 2>&1 || die "required command not found: $1"
}

main() {
	local device

	case "${1:-}" in
	--help | -h)
		usage
		return 0
		;;
	esac

	[[ $# -le 1 ]] || die "expected at most one device argument"
	device=${1:-$DEFAULT_DEVICE}

	case "$device" in
	*:*) ;;
	*) device="$device:$DEFAULT_PORT" ;;
	esac

	require_command adb
	require_command scrcpy

	if ! adb connect "$device"; then
		return 1
	fi

	exec scrcpy \
		--serial "$device" \
		--keyboard=disabled \
		--turn-screen-off \
		--stay-awake \
		--no-audio \
		--no-audio-playback \
		--window-width="$WINDOW_WIDTH" \
		--window-height="$WINDOW_HEIGHT"
}

main "$@"
