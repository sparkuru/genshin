#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_NAME=$(basename "$0")
readonly SCRIPT_NAME
readonly DEFAULT_DEVICE="192.168.9.7"
readonly DEFAULT_PORT="5555"
readonly WINDOW_WIDTH="640"
readonly WINDOW_HEIGHT="1400"

usage() {
	printf 'Usage: %s [WIRELESS_DEVICE[:PORT]]\n' "$SCRIPT_NAME" >&2
	printf 'A connected wired device is preferred; the wireless device is used as a fallback.\n' >&2
}

die() {
	printf 'Error: %s\n' "$*" >&2
	exit 1
}

require_command() {
	command -v "$1" >/dev/null 2>&1 || die "required command not found: $1"
}

find_wired_device() {
	local serial state

	while read -r serial state _; do
		if [[ "$state" == "device" && "$serial" != *:* && "$serial" != emulator-* ]]; then
			printf '%s\n' "$serial"
			return 0
		fi
	done < <(adb devices)

	return 1
}

main() {
	local device wired_device

	case "${1:-}" in
	--help | -h)
		usage
		return 0
		;;
	esac

	[[ $# -le 1 ]] || die "expected at most one device argument"
	require_command adb
	require_command scrcpy

	if wired_device=$(find_wired_device); then
		device=$wired_device
		printf 'Using wired device: %s\n' "$device"
	else
		device=${1:-$DEFAULT_DEVICE}

		case "$device" in
		*:*) ;;
		*) device="$device:$DEFAULT_PORT" ;;
		esac

		if ! adb connect "$device"; then
			return 1
		fi
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
