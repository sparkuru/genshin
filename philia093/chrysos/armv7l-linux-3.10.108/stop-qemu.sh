#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_NAME="$(basename "$0")"
readonly SCRIPT_NAME
ROOT_DIR="$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd -P)"
readonly ROOT_DIR
readonly PID_FILE="$ROOT_DIR/out/run/qemu.pid"

usage() {
	cat >&2 <<EOF
Usage: $SCRIPT_NAME

Stop the background QEMU instance started by ./run-qemu.sh --background.
EOF
}

die() {
	printf 'Error: %s\n' "$*" >&2
	exit 1
}

main() {
	local option=
	local pid
	local command_name
	local attempt

	if (($# > 0)); then
		option=$1
	fi
	case "$option" in
	"") ;;
	--help | -h)
		usage
		return 0
		;;
	*)
		usage
		die "unknown option: $option"
		;;
	esac

	if [[ ! -f "$PID_FILE" ]]; then
		printf '%s\n' 'QEMU is not running'
		return 0
	fi
	pid=$(<"$PID_FILE")
	[[ "$pid" =~ ^[1-9][0-9]*$ ]] || die "invalid PID file: $PID_FILE"
	if ! kill -0 "$pid" 2>/dev/null; then
		rm -f -- "$PID_FILE"
		printf '%s\n' 'QEMU is not running'
		return 0
	fi
	command_name=$(<"/proc/$pid/comm")
	[[ "$command_name" == qemu-system-arm ]] ||
		die "PID $pid is not a QEMU process; refusing to stop it"

	kill "$pid"
	for attempt in 1 2 3 4 5; do
		if ! kill -0 "$pid" 2>/dev/null; then
			rm -f -- "$PID_FILE"
			printf 'Stopped QEMU PID %s\n' "$pid"
			return 0
		fi
		if [[ "$attempt" -eq 5 ]]; then
			break
		fi
		sleep 1
	done
	die "QEMU PID $pid did not stop after 5 seconds"
}

main "$@"
