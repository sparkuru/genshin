#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_NAME=$(basename "$0")
readonly SCRIPT_NAME
readonly DEFAULT_PORT="5555"
readonly DEFAULT_WINDOW_WIDTH="640"
readonly DEFAULT_WINDOW_HEIGHT="1400"
readonly DEFAULT_KEYBOARD_MODE="disabled"

readonly -a DEVICE_IDENTIFIER_PROPERTIES=(
	"ro.board.platform"
	"ro.product.board"
	"ro.product.device"
)
readonly -a DEVICE_PROFILES=(
	# identifier|window width|window height|keyboard mode
	"rk356x|1080|608|uhid"
)

usage() {
	printf 'Usage: %s [IP_ADDRESS[:PORT]]\n' "$SCRIPT_NAME" >&2
	printf 'An existing ADB device is used; IP_ADDRESS[:PORT] is required when none is connected.\n' >&2
}

die() {
	printf 'Error: %s\n' "$*" >&2
	exit 1
}

require_command() {
	command -v "$1" >/dev/null 2>&1 || die "required command not found: $1"
}

get_device_identifier() {
	local device property identifier

	device=$1
	for property in "${DEVICE_IDENTIFIER_PROPERTIES[@]}"; do
		if ! identifier=$(adb -s "$device" shell getprop "$property" 2>/dev/null); then
			continue
		fi

		identifier=${identifier//$'\r'/}
		if [[ -n "$identifier" && "$identifier" != "unknown" ]]; then
			printf '%s\n' "$identifier"
			return 0
		fi
	done

	return 1
}

find_device_profile() {
	local device_identifier profile profile_identifier profile_width profile_height profile_keyboard

	device_identifier=$1
	for profile in "${DEVICE_PROFILES[@]}"; do
		IFS='|' read -r profile_identifier profile_width profile_height profile_keyboard <<<"$profile"
		if [[ "$profile_identifier" == "$device_identifier" && -n "$profile_width" && -n "$profile_height" ]]; then
			printf '%s|%s|%s\n' "$profile_width" "$profile_height" "${profile_keyboard:-$DEFAULT_KEYBOARD_MODE}"
			return 0
		fi
	done

	return 1
}

find_connected_device() {
	local serial state

	while read -r serial state _; do
		if [[ "$state" == "device" ]]; then
			printf '%s\n' "$serial"
			return 0
		fi
	done < <(adb devices)

	return 1
}

main() {
	local device connected_device device_identifier profile_config window_width window_height keyboard_mode

	case "${1:-}" in
	--help | -h)
		usage
		return 0
		;;
	esac

	[[ $# -le 1 ]] || die "expected at most one device argument"
	require_command adb
	require_command scrcpy

	if [[ $# -eq 1 && -n "$1" ]]; then
		device=$1

		case "$device" in
		*:*) ;;
		*) device="$device:$DEFAULT_PORT" ;;
		esac

		if ! adb connect "$device"; then
			return 1
		fi
		printf 'Using supplied IP address: %s\n' "$device"
	elif connected_device=$(find_connected_device); then
		device=$connected_device
		printf 'Using connected device: %s\n' "$device"
	else
		die "no connected ADB device found; provide an IP address"
	fi

	window_width=$DEFAULT_WINDOW_WIDTH
	window_height=$DEFAULT_WINDOW_HEIGHT
	keyboard_mode=$DEFAULT_KEYBOARD_MODE
	if device_identifier=$(get_device_identifier "$device"); then
		printf 'Detected device identifier: %s\n' "$device_identifier"
		if profile_config=$(find_device_profile "$device_identifier"); then
			IFS='|' read -r window_width window_height keyboard_mode <<<"$profile_config"
			printf 'Using device profile: %s.\n' "$device_identifier"
		else
			printf 'Using default configuration.\n'
		fi
	else
		printf 'Device identifier unavailable; using default configuration.\n'
	fi

	exec scrcpy \
		--serial "$device" \
		--keyboard="$keyboard_mode" \
		--turn-screen-off \
		--stay-awake \
		--no-audio \
		--no-audio-playback \
		--window-width="$window_width" \
		--window-height="$window_height"
}

main "$@"
