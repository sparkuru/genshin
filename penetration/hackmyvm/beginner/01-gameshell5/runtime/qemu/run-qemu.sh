#!/usr/bin/env bash
set -Eeuo pipefail

script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
readonly SCRIPT_DIR="$script_dir"
lab_root=$(cd -- "$SCRIPT_DIR/../.." && pwd -P)
readonly LAB_ROOT="$lab_root"
readonly BASE_IMAGE="$LAB_ROOT/runtime/images/gameshell5-base.qcow2"
readonly STATE_DIR="$LAB_ROOT/runtime/state"
readonly OVERLAY_IMAGE="$STATE_DIR/gameshell5-overlay.qcow2"
readonly PID_FILE="$STATE_DIR/gameshell5.pid"
readonly LOG_FILE="$STATE_DIR/gameshell5-qemu.log"
readonly MONITOR_SOCKET="$STATE_DIR/gameshell5-monitor.sock"
readonly MONITOR_SOCKET_RELATIVE=runtime/state/gameshell5-monitor.sock
readonly QEMU_BRIDGE_HELPER=/usr/lib/qemu/qemu-bridge-helper
# Docker's default bridge.  These values are deliberately explicit so the
# target's network identity is visible before QEMU starts.
readonly BRIDGE_NAME=docker0
readonly NETWORK_SUBNET=10.160.0.0/20
readonly HOST_BRIDGE_ADDRESS=10.160.0.1
readonly TARGET_IP=10.160.0.10

die() {
	printf 'Error: %s\n' "$*" >&2
	exit 1
}

require_command() {
	command -v "$1" >/dev/null 2>&1 || die "required command not found: $1"
}

require_bridge_helper() {
	[[ -u "$QEMU_BRIDGE_HELPER" ]] || die "bridge helper is not setuid; run setup-bridge-helper.sh as root"
	[[ -r /etc/qemu/bridge.conf ]] || die "bridge helper configuration not found: /etc/qemu/bridge.conf"
	grep -Fxq "allow $BRIDGE_NAME" /etc/qemu/bridge.conf || die "bridge helper does not allow $BRIDGE_NAME"
}

main() {
	require_command qemu-img
	require_command qemu-system-x86_64
	require_command docker
	[[ -f "$BASE_IMAGE" ]] || die "base image not found: $BASE_IMAGE"
	require_bridge_helper
	"$SCRIPT_DIR/network-up.sh"

	mkdir -p -- "$STATE_DIR"
	rm -f -- "$MONITOR_SOCKET"

	if [[ -f "$PID_FILE" ]]; then
		local existing_pid
		existing_pid=$(<"$PID_FILE")
		if [[ "$existing_pid" =~ ^[0-9]+$ ]] && kill -0 "$existing_pid" 2>/dev/null; then
			die "GameShell5 is already running (PID $existing_pid)"
		fi
		rm -f -- "$PID_FILE"
	fi

	if [[ ! -f "$OVERLAY_IMAGE" ]]; then
		qemu-img create -f qcow2 -F qcow2 -b "$BASE_IMAGE" "$OVERLAY_IMAGE" >/dev/null
	fi

	local -a machine_args cpu_args
	if [[ -r /dev/kvm && -w /dev/kvm ]]; then
		machine_args=(-machine "q35,accel=kvm:tcg")
		cpu_args=(-cpu host)
	else
		machine_args=(-machine "q35,accel=tcg")
		cpu_args=(-cpu max)
	fi

	cd -- "$LAB_ROOT"
	qemu-system-x86_64 \
		"${machine_args[@]}" \
		"${cpu_args[@]}" \
		-name GameShell5 \
		-m 2048 \
		-smp 1 \
		-rtc base=utc \
		-vga vmware \
		-drive "file=$OVERLAY_IMAGE,format=qcow2,if=none,id=disk0" \
		-device ide-hd,bus=ide.0,drive=disk0 \
		-netdev "bridge,id=net0,br=$BRIDGE_NAME,helper=$QEMU_BRIDGE_HELPER" \
		-device e1000,netdev=net0,mac=08:00:27:EF:C9:BA,addr=0x3 \
		-vnc 127.0.0.1:1 \
		-display none \
		-monitor "unix:$MONITOR_SOCKET_RELATIVE,server=on,wait=off" \
		-daemonize \
		-pidfile "$PID_FILE" \
		-D "$LOG_FILE"

	printf 'GameShell5 started. VNC: 127.0.0.1:5901; docker0 subnet: %s; host/router: %s; QEMU: %s\n' \
		"$NETWORK_SUBNET" "$HOST_BRIDGE_ADDRESS" "$TARGET_IP"
}

main "$@"
