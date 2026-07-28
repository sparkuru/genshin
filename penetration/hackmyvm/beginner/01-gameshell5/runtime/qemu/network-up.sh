#!/usr/bin/env bash
set -Eeuo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
readonly SCRIPT_DIR="$script_dir"
lab_root=$(cd -- "$SCRIPT_DIR/../.." && pwd -P)
readonly LAB_ROOT="$lab_root"
readonly STATE_DIR="$LAB_ROOT/runtime/state"
# Docker manages this default network.  Do not create, alter, or remove it.
readonly DOCKER_NETWORK_NAME=bridge
readonly BRIDGE_NAME=docker0
readonly NETWORK_SUBNET=10.160.0.0/20
readonly HOST_BRIDGE_ADDRESS=10.160.0.1
readonly TARGET_IP=10.160.0.10
readonly NETWORK_BROADCAST=10.160.15.255
readonly NETWORK_MASK=255.255.240.0
readonly DNS_SERVER=1.1.1.1
readonly DHCP_SERVER="$SCRIPT_DIR/dhcp-server.py"
readonly DHCP_PID_FILE="$STATE_DIR/gameshell5-dhcp.pid"
readonly DHCP_LOG="$STATE_DIR/gameshell5-dhcp.log"

die() {
	printf 'Error: %s\n' "$*" >&2
	exit 1
}

require_command() {
	command -v "$1" >/dev/null 2>&1 || die "required command not found: $1"
}

validate_docker_bridge() {
	local subnet gateway bridge_address target_in_use

	subnet=$(docker network inspect --format '{{range .IPAM.Config}}{{.Subnet}}{{end}}' "$DOCKER_NETWORK_NAME")
	gateway=$(docker network inspect --format '{{range .IPAM.Config}}{{.Gateway}}{{end}}' "$DOCKER_NETWORK_NAME")
	bridge_address=$(ip -o -4 address show dev "$BRIDGE_NAME" | awk '{print $4}')
	target_in_use=$(docker network inspect --format '{{range .Containers}}{{.IPv4Address}}{{"\\n"}}{{end}}' "$DOCKER_NETWORK_NAME")

	[[ "$subnet" == "$NETWORK_SUBNET" ]] || die "docker0 subnet is $subnet, expected $NETWORK_SUBNET"
	[[ "$gateway" == "$HOST_BRIDGE_ADDRESS" ]] || die "docker0 gateway is $gateway, expected $HOST_BRIDGE_ADDRESS"
	[[ "$bridge_address" == "$HOST_BRIDGE_ADDRESS/20" ]] || die "docker0 address is $bridge_address, expected $HOST_BRIDGE_ADDRESS/20"
	if grep -Fxq "$TARGET_IP/20" <<<"$target_in_use"; then
		die "QEMU address $TARGET_IP is already allocated to a Docker endpoint"
	fi
}

dhcp_process_running() {
	local pid

	[[ -f "$DHCP_PID_FILE" ]] || return 1
	pid=$(<"$DHCP_PID_FILE")
	[[ "$pid" =~ ^[0-9]+$ ]] || return 1
	sudo -n kill -0 "$pid" 2>/dev/null
}

start_dhcp_server() {
	if dhcp_process_running; then
		return
	fi

	rm -f -- "$DHCP_PID_FILE"
	# shellcheck disable=SC2024  # User-owned runtime log is intentionally opened before sudo.
	sudo -n env \
		GAMESHELL5_DHCP_INTERFACE="$BRIDGE_NAME" \
		GAMESHELL5_DHCP_PID_FILE="$DHCP_PID_FILE" \
		GAMESHELL5_DHCP_SERVER_ADDRESS="$HOST_BRIDGE_ADDRESS" \
		GAMESHELL5_DHCP_LEASE_ADDRESS="$TARGET_IP" \
		GAMESHELL5_DHCP_SUBNET_MASK="$NETWORK_MASK" \
		GAMESHELL5_DHCP_BROADCAST_ADDRESS="$NETWORK_BROADCAST" \
		GAMESHELL5_DHCP_ROUTER_ADDRESS="$HOST_BRIDGE_ADDRESS" \
		GAMESHELL5_DHCP_DNS_SERVER="$DNS_SERVER" \
		python3 "$DHCP_SERVER" >"$DHCP_LOG" 2>&1 &

	for _ in {1..30}; do
		if dhcp_process_running; then
			return
		fi
		sleep 0.1
	done

	die "DHCP server did not start; inspect $DHCP_LOG"
}

main() {
	require_command docker
	require_command ip
	require_command python3
	require_command sudo
	[[ -f "$DHCP_SERVER" ]] || die "DHCP server not found: $DHCP_SERVER"
	mkdir -p -- "$STATE_DIR"

	validate_docker_bridge
	start_dhcp_server

	printf 'Docker bridge ready: %s; subnet=%s; host/router=%s; QEMU=%s; DNS=%s\n' \
		"$BRIDGE_NAME" "$NETWORK_SUBNET" "$HOST_BRIDGE_ADDRESS" "$TARGET_IP" "$DNS_SERVER"
}

main "$@"
