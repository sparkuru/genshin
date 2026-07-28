#!/usr/bin/env bash
set -Eeuo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
readonly SCRIPT_DIR="$script_dir"
lab_root=$(cd -- "$SCRIPT_DIR/../.." && pwd -P)
readonly LAB_ROOT="$lab_root"
readonly STATE_DIR="$LAB_ROOT/runtime/state"
readonly OVERLAY_IMAGE="$STATE_DIR/gameshell5-overlay.qcow2"
readonly PID_FILE="$STATE_DIR/gameshell5.pid"

die() {
	printf 'Error: %s\n' "$*" >&2
	exit 1
}

main() {
	if [[ -f "$PID_FILE" ]]; then
		local pid
		pid=$(<"$PID_FILE")
		if [[ "$pid" =~ ^[0-9]+$ ]] && kill -0 "$pid" 2>/dev/null; then
			die "stop GameShell5 before resetting its mutable overlay"
		fi
		rm -f -- "$PID_FILE"
	fi

	if [[ -f "$OVERLAY_IMAGE" ]]; then
		rm -f -- "$OVERLAY_IMAGE"
		printf 'Removed the mutable GameShell5 overlay.\n'
	else
		printf 'GameShell5 already has pristine mutable state.\n'
	fi
}

main "$@"
