#!/usr/bin/env bash
set -Eeuo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
readonly SCRIPT_DIR="$script_dir"
lab_root=$(cd -- "$SCRIPT_DIR/../.." && pwd -P)
readonly LAB_ROOT="$lab_root"
readonly STATE_DIR="$LAB_ROOT/runtime/state"
readonly DHCP_SERVER="$SCRIPT_DIR/dhcp-server.py"
readonly DHCP_PID_FILE="$STATE_DIR/gameshell5-dhcp.pid"

stop_dhcp_server() {
	local pid command_line

	[[ -f "$DHCP_PID_FILE" ]] || return 0
	pid=$(<"$DHCP_PID_FILE")
	if [[ ! "$pid" =~ ^[0-9]+$ ]]; then
		rm -f -- "$DHCP_PID_FILE"
		return
	fi
	if ! sudo -n kill -0 "$pid" 2>/dev/null; then
		rm -f -- "$DHCP_PID_FILE"
		return
	fi
	command_line=$(sudo -n cat "/proc/$pid/cmdline" | tr '\0' ' ')
	[[ "$command_line" == *"$DHCP_SERVER"* ]] || return
	sudo -n kill -TERM "$pid"
	for _ in {1..25}; do
		if ! sudo -n kill -0 "$pid" 2>/dev/null; then
			rm -f -- "$DHCP_PID_FILE"
			return
		fi
		sleep 0.2
	done
}

main() {
	command -v sudo >/dev/null 2>&1 || return 0
	stop_dhcp_server
}

main "$@"
