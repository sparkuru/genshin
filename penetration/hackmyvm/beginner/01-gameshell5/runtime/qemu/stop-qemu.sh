#!/usr/bin/env bash
set -Eeuo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
readonly SCRIPT_DIR="$script_dir"
lab_root=$(cd -- "$SCRIPT_DIR/../.." && pwd -P)
readonly LAB_ROOT="$lab_root"
readonly STATE_DIR="$LAB_ROOT/runtime/state"
readonly PID_FILE="$STATE_DIR/gameshell5.pid"
readonly NETWORK_DOWN_SCRIPT="$SCRIPT_DIR/network-down.sh"
readonly MONITOR_SOCKET="$STATE_DIR/gameshell5-monitor.sock"

die() {
	printf 'Error: %s\n' "$*" >&2
	exit 1
}

process_matches_lab() {
	local pid=$1
	local command_line

	[[ -r "/proc/$pid/cmdline" ]] || return 1
	command_line=$(tr '\0' ' ' <"/proc/$pid/cmdline")
	[[ "$command_line" == *qemu-system-x86_64* && "$command_line" == *"$LAB_ROOT"* ]]
}

main() {
	[[ -f "$PID_FILE" ]] || {
		"$NETWORK_DOWN_SCRIPT"
		printf 'GameShell5 is not running.\n'
		return 0
	}

	local pid
	pid=$(<"$PID_FILE")
	if [[ ! "$pid" =~ ^[0-9]+$ ]] || ! kill -0 "$pid" 2>/dev/null; then
		rm -f -- "$PID_FILE"
		"$NETWORK_DOWN_SCRIPT"
		printf 'Removed stale GameShell5 PID file.\n'
		return 0
	fi

	process_matches_lab "$pid" || die "refusing to signal unexpected PID $pid"
	kill -TERM "$pid"

	for _ in {1..25}; do
		if ! kill -0 "$pid" 2>/dev/null; then
			rm -f -- "$PID_FILE"
			rm -f -- "$MONITOR_SOCKET"
			"$NETWORK_DOWN_SCRIPT"
			printf 'GameShell5 stopped.\n'
			return 0
		fi
		sleep 0.2
	done

	die "GameShell5 did not stop within five seconds; inspect PID $pid"
}

main "$@"
