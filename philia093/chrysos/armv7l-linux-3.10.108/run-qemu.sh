#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_NAME="$(basename "$0")"
readonly SCRIPT_NAME
ROOT_DIR="$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd -P)"
readonly ROOT_DIR
readonly OUTPUT_DIR="$ROOT_DIR/out"
readonly RUN_DIR="$OUTPUT_DIR/run"
readonly PID_FILE="$RUN_DIR/qemu.pid"
readonly TELNET_PORT="4545"
readonly GUEST_TELNET_PORT="23"
readonly SERIAL_LOG_FILE="$RUN_DIR/qemu-serial.log"

usage() {
	cat >&2 <<EOF
Usage: $SCRIPT_NAME [--background] [--share DIRECTORY]

Start the Linux 3.10.108 ARMv7 guest.

  --background  Run QEMU in the background and expose guest telnetd on
                127.0.0.1:$TELNET_PORT.
  --share DIR   Mount an existing host directory read-only at /mnt/host.
EOF
}

die() {
	printf 'Error: %s\n' "$*" >&2
	exit 1
}

require_command() {
	command -v "$1" >/dev/null 2>&1 || die "required command not found: $1"
}

require_artifacts() {
	[[ -f "$OUTPUT_DIR/zImage" ]] || die "missing $OUTPUT_DIR/zImage; run ./build.sh"
	[[ -f "$OUTPUT_DIR/vexpress-v2p-ca9.dtb" ]] ||
		die "missing device tree; run ./build.sh"
}

running_pid() {
	local pid

	[[ -f "$PID_FILE" ]] || return 1
	pid=$(<"$PID_FILE")
	[[ "$pid" =~ ^[1-9][0-9]*$ ]] || return 1
	kill -0 "$pid" 2>/dev/null || return 1
	printf '%s\n' "$pid"
}

qemu_common_args() {
	local share_path=${1:-}
	local append_value='console=ttyAMA0,115200 earlyprintk=serial,ttyAMA0,115200 rdinit=/init'

	if [[ -n "$share_path" ]]; then
		append_value+=' chrysos.share=1'
	fi
	printf '%s\n' \
		-machine vexpress-a9 \
		-cpu cortex-a9 \
		-smp 4 \
		-m 256M \
		-kernel "$OUTPUT_DIR/zImage" \
		-dtb "$OUTPUT_DIR/vexpress-v2p-ca9.dtb" \
		-append "$append_value" \
		-nic "user,model=lan9118,restrict=on,hostfwd=tcp:127.0.0.1:$TELNET_PORT-:$GUEST_TELNET_PORT" \
		-no-reboot \
		-audio none \
		-display none \
		-monitor none
	if [[ -n "$share_path" ]]; then
		printf '%s\n' \
			-fsdev "local,id=hostshare,path=$share_path,security_model=none,readonly=on" \
			-device 'virtio-9p-device,fsdev=hostshare,mount_tag=hostshare'
	fi
}

start_foreground() {
	local share_path=$1
	local -a qemu_args
	local arg

	qemu_args=(qemu-system-arm)
	while IFS= read -r arg; do
		qemu_args+=("$arg")
	done < <(qemu_common_args "$share_path")
	qemu_args+=(-serial stdio)
	exec "${qemu_args[@]}"
}

start_background() {
	local share_path=$1
	local -a qemu_args
	local arg
	local pid

	mkdir -p -- "$RUN_DIR"
	if pid=$(running_pid); then
		die "QEMU is already running with PID $pid"
	fi
	rm -f -- "$PID_FILE"
	qemu_args=(qemu-system-arm)
	while IFS= read -r arg; do
		qemu_args+=("$arg")
	done < <(qemu_common_args "$share_path")
	qemu_args+=(-serial "file:$SERIAL_LOG_FILE")
	nohup "${qemu_args[@]}" >"$RUN_DIR/qemu.stdout.log" 2>&1 </dev/null &
	pid=$!
	printf '%s\n' "$pid" >"$PID_FILE"
	sleep 1
	if ! kill -0 "$pid" 2>/dev/null; then
		rm -f -- "$PID_FILE"
		die "QEMU exited during startup; inspect $RUN_DIR/qemu.stdout.log"
	fi
	printf 'QEMU started with PID %s\n' "$pid"
	printf 'Guest telnetd: telnet 127.0.0.1 %s\n' "$TELNET_PORT"
	printf 'Serial log: %s\n' "$SERIAL_LOG_FILE"
	if [[ -n "$share_path" ]]; then
		printf 'Read-only host share: %s -> /mnt/host\n' "$share_path"
	fi
	printf 'Stop: ./stop-qemu.sh\n'
}

main() {
	local mode=foreground
	local requested_share_path
	local share_path=

	require_command qemu-system-arm
	require_artifacts
	while (($# > 0)); do
		case "$1" in
		--background)
			mode=background
			shift
			;;
		--share)
			[[ -n "${2:-}" ]] || die "missing directory for --share"
			[[ -z "$share_path" ]] || die "--share may only be specified once"
			share_path=$2
			shift 2
			;;
		--help | -h)
			usage
			return 0
			;;
		*)
			usage
			die "unknown option: $1"
			;;
		esac
	done
	if [[ -n "$share_path" ]]; then
		require_command readlink
		requested_share_path=$share_path
		share_path=$(readlink --canonicalize "$share_path") ||
			die "shared directory does not exist: $requested_share_path"
		[[ -d "$share_path" ]] || die "shared path is not a directory: $share_path"
		[[ "$share_path" != *','* && "$share_path" != *$'\n'* ]] ||
			die "shared directory path must not contain commas or newlines"
	fi

	case "$mode" in
	foreground)
		start_foreground "$share_path"
		;;
	background)
		start_background "$share_path"
		;;
	esac
}

main "$@"
