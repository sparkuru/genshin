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
Usage: $SCRIPT_NAME [--background]

Start the Linux 3.10.108 ARMv7 guest.

  --background  Run QEMU in the background and expose guest telnetd on
                127.0.0.1:$TELNET_PORT.
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
	printf '%s\n' \
		-machine vexpress-a9 \
		-cpu cortex-a9 \
		-smp 4 \
		-m 256M \
		-kernel "$OUTPUT_DIR/zImage" \
		-dtb "$OUTPUT_DIR/vexpress-v2p-ca9.dtb" \
		-append 'console=ttyAMA0,115200 earlyprintk=serial,ttyAMA0,115200 rdinit=/init' \
		-nic "user,model=lan9118,restrict=on,hostfwd=tcp:127.0.0.1:$TELNET_PORT-:$GUEST_TELNET_PORT" \
		-no-reboot \
		-audio none \
		-display none \
		-monitor none
}

start_foreground() {
	local -a qemu_args
	local arg

	qemu_args=(qemu-system-arm)
	while IFS= read -r arg; do
		qemu_args+=("$arg")
	done < <(qemu_common_args)
	qemu_args+=(-serial stdio)
	exec "${qemu_args[@]}"
}

start_background() {
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
	done < <(qemu_common_args)
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
	printf 'Stop: ./stop-qemu.sh\n'
}

main() {
	local option=
	local mode=foreground

	require_command qemu-system-arm
	require_artifacts
	if (($# > 0)); then
		option=$1
	fi
	case "$option" in
	"") ;;
	--background)
		mode=background
		;;
	--help | -h)
		usage
		return 0
		;;
	*)
		usage
		die "unknown option: $option"
		;;
	esac

	case "$mode" in
	foreground)
		start_foreground
		;;
	background)
		start_background
		;;
	esac
}

main "$@"
