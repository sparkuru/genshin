#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_NAME=$(basename "$0")
readonly SCRIPT_NAME
readonly DEFAULT_SERVER_DIR_NAME="frida-server"
readonly DEFAULT_REMOTE_PATH="/data/local/tmp/frida-server"
readonly STYLE_RESET=$'\033[0m'
readonly STYLE_TITLE=$'\033[1;36m'
readonly STYLE_SUB_TITLE=$'\033[1;34m'
readonly STYLE_CONTENT=$'\033[1;37m'
readonly STYLE_EXAMPLE=$'\033[0;37m'
readonly STYLE_SUCCESS=$'\033[0;32m'
readonly STYLE_WARNING=$'\033[1;33m'
readonly STYLE_ERROR=$'\033[1;31m'

server_dir="${FRIDA_SERVER_DIR:-}"
remote_path="$DEFAULT_REMOTE_PATH"
serial=""
declare -a adb_command=(adb)

color_text() {
	local style=$1
	local message=$2

	if [[ -n "${NO_COLOR:-}" || ! -t 1 ]]; then
		printf '%s' "$message"
		return 0
	fi

	printf '%s' "$style$message$STYLE_RESET"
}

info() {
	printf '%s\n' "$(color_text "$STYLE_CONTENT" "$*")"
}

title() {
	printf '\n%s\n' "$(color_text "$STYLE_TITLE" "== $* ==")"
}

section() {
	printf '%s\n' "$(color_text "$STYLE_SUB_TITLE" "-- $* --")"
}

success() {
	printf '%s\n' "$(color_text "$STYLE_SUCCESS" "$*")"
}

example() {
	printf '%s\n' "$(color_text "$STYLE_EXAMPLE" "$*")"
}

warn() {
	printf '%s\n' "$(color_text "$STYLE_WARNING" "Warning: $*")" >&2
}

die() {
	printf '%s\n' "$(color_text "$STYLE_ERROR" "Error: $*")" >&2
	exit 1
}

usage() {
	printf 'Usage: %s [--serial <device-id>] [--server-dir <directory>] [--remote-path <path>]\n' "$SCRIPT_NAME"
	printf '\nUpload the matching local Android Frida server, start it with root privileges, and verify USB connectivity.\n'
	printf 'Set FRIDA_SERVER_DIR to reuse a non-default server directory.\n'
}

require_command() {
	command -v "$1" >/dev/null 2>&1 || die "required command not found: $1; run init.sh first if it is a Frida command"
}

find_frida() {
	local candidate

	candidate=$(command -v frida || true)
	if [[ -n "$candidate" && -x "$candidate" ]]; then
		printf '%s' "$candidate"
		return 0
	fi

	candidate="$HOME/.local/bin/frida"
	[[ -x "$candidate" ]] || die "frida not found; run init.sh first or add Frida to PATH"
	printf '%s' "$candidate"
}

find_frida_ps() {
	local frida_bin=$1
	local candidate

	candidate="$(dirname "$frida_bin")/frida-ps"
	if [[ -x "$candidate" ]]; then
		printf '%s' "$candidate"
		return 0
	fi

	candidate=$(command -v frida-ps || true)
	[[ -n "$candidate" && -x "$candidate" ]] || die "frida-ps not found; run init.sh first"
	printf '%s' "$candidate"
}

adb_run() {
	"${adb_command[@]}" "$@"
}

server_architecture_for_abi() {
	case "$1" in
	arm64-v8a)
		printf '%s' arm64
		;;
	armeabi-v7a | armeabi)
		printf '%s' arm
		;;
	x86_64)
		printf '%s' x86_64
		;;
	x86)
		printf '%s' x86
		;;
	*)
		return 1
		;;
	esac
}

parse_arguments() {
	while [[ $# -gt 0 ]]; do
		case "$1" in
		--serial)
			[[ $# -ge 2 ]] || die "--serial requires a device ID"
			serial=$2
			shift 2
			;;
		--server-dir)
			[[ $# -ge 2 ]] || die "--server-dir requires a directory"
			server_dir=$2
			shift 2
			;;
		--remote-path)
			[[ $# -ge 2 ]] || die "--remote-path requires a path"
			remote_path=$2
			shift 2
			;;
		--help | -h)
			usage
			exit 0
			;;
		*)
			die "unknown option: $1"
			;;
		esac
	done
}

validate_remote_path() {
	[[ "$remote_path" =~ ^/[A-Za-z0-9._/-]+$ ]] || die "remote path contains unsupported characters: $remote_path"
}

main() {
	local frida_bin
	local frida_ps_bin
	local frida_version
	local device_state
	local device_abi
	local device_abis
	local device_model
	local android_version
	local server_architecture
	local server_file
	local shell_uid
	local su_uid
	local root_mode
	local frida_processes

	parse_arguments "$@"
	title "Frida Android connection"
	section "Checking local tools"
	validate_remote_path
	require_command adb
	frida_bin=$(find_frida)
	frida_ps_bin=$(find_frida_ps "$frida_bin")
	frida_version=$("$frida_bin" --version)
	[[ "$frida_version" =~ ^[0-9][0-9A-Za-z.+-]*$ ]] || die "unexpected Frida version: $frida_version"

	if [[ -n "$serial" ]]; then
		adb_command+=(-s "$serial")
	fi
	section "Inspecting Android device"
	device_state=$(adb_run get-state 2>/dev/null || true)
	[[ "$device_state" == "device" ]] || die "ADB device is unavailable (state: ${device_state:-none})"

	device_abi=$(adb_run shell getprop ro.product.cpu.abi | tr -d '\r')
	device_abis=$(adb_run shell getprop ro.product.cpu.abilist | tr -d '\r')
	device_model=$(adb_run shell getprop ro.product.model | tr -d '\r')
	android_version=$(adb_run shell getprop ro.build.version.release | tr -d '\r')
	server_architecture=$(server_architecture_for_abi "$device_abi") || die "unsupported Android ABI: $device_abi (reported ABI list: $device_abis)"

	if [[ -z "$server_dir" ]]; then
		server_dir="$(dirname "$frida_bin")/$DEFAULT_SERVER_DIR_NAME"
	fi
	server_file="$server_dir/frida-server-${frida_version}-android-${server_architecture}"
	[[ -f "$server_file" ]] || die "matching server is missing: $server_file; run init.sh first"
	[[ -s "$server_file" ]] || die "matching server is empty: $server_file"

	section "Checking root access"
	shell_uid=$(adb_run shell id -u | tr -d '\r')
	if [[ "$shell_uid" == "0" ]]; then
		root_mode=shell
	else
		su_uid=$(adb_run shell "su -c 'id -u'" 2>/dev/null | tr -d '\r' || true)
		[[ "$su_uid" == "0" ]] || die "root access is required; adb shell and su are both non-root"
		root_mode=su
	fi

	info "Device: ${device_model:-unknown} (Android ${android_version:-unknown}, ${device_abi})"
	section "Uploading and starting server"
	info "Uploading ${server_file##*/} to $remote_path"
	adb_run push "$server_file" "$remote_path" >/dev/null
	adb_run shell chmod 0700 "$remote_path"

	if [[ "$root_mode" == "shell" ]]; then
		adb_run shell "$remote_path >/dev/null 2>&1 &"
	else
		adb_run shell "su -c '$remote_path >/dev/null 2>&1 &'"
	fi

	section "Verifying USB connection"
	sleep 1
	if ! frida_processes=$("$frida_ps_bin" -U 2>&1); then
		printf '%s\n' "$frida_processes" >&2
		die "server was uploaded and launch was requested, but Frida could not connect"
	fi

	success "Frida server is running and USB connection succeeded"
	example "Use: $frida_ps_bin -U"
}

main "$@"
