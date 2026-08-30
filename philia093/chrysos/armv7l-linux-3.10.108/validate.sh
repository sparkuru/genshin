#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_NAME="$(basename "$0")"
readonly SCRIPT_NAME
ROOT_DIR="$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd -P)"
readonly ROOT_DIR
PROFILE_DIR="$ROOT_DIR"
export PROFILE_DIR
# shellcheck disable=SC1091 # This static profile owns its descriptor.
source "$ROOT_DIR/profile.env"
readonly OUTPUT_DIR="$ROOT_DIR/out"
readonly LOG_FILE="$OUTPUT_DIR/validation.log"
readonly REPORT_FILE="$OUTPUT_DIR/report.md"

die() {
	printf 'Error: %s\n' "$*" >&2
	exit 1
}

usage() {
	cat >&2 <<EOF
Usage: $SCRIPT_NAME

Boot the generated guest, verify Linux 3.10.108 and ARMv7 identity, and power
the guest off without exercising any exploit or service.
EOF
}

require_command() {
	command -v "$1" >/dev/null 2>&1 || die "required command not found: $1"
}

main() {
	local option=
	local qemu_status

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

	require_command "$QEMU_SYSTEM_BINARY"
	require_command timeout
	[[ -f "$OUTPUT_DIR/zImage" ]] || die "missing $OUTPUT_DIR/zImage; run ./build.sh"
	[[ -f "$OUTPUT_DIR/vexpress-v2p-ca9.dtb" ]] ||
		die "missing device tree; run ./build.sh"
	mkdir -p -- "$OUTPUT_DIR"
	: >"$LOG_FILE"

	set +e
	timeout --signal=TERM 30s "$QEMU_SYSTEM_BINARY" \
		-machine "$QEMU_MACHINE" \
		-cpu "$QEMU_CPU" \
		-smp "$QEMU_SMP" \
		-m "$QEMU_MEMORY" \
		-kernel "$OUTPUT_DIR/zImage" \
		-dtb "$OUTPUT_DIR/vexpress-v2p-ca9.dtb" \
		-append "console=$KERNEL_CONSOLE earlyprintk=serial,$KERNEL_CONSOLE rdinit=/init user.validate=1" \
		-nic 'user,model=lan9118,restrict=on' \
		-no-reboot \
		-audio none \
		-display none \
		-monitor none \
		-serial "file:$LOG_FILE"
	qemu_status=$?
	set -e

	[[ "$qemu_status" -eq 0 || "$qemu_status" -eq 124 ]] ||
		die "QEMU validation failed with status $qemu_status; inspect $LOG_FILE"
	grep --fixed-strings --quiet "3.10.108" "$LOG_FILE" ||
		die "kernel release was not observed; inspect $LOG_FILE"
	grep --extended-regexp --quiet 'armv7l|armv7' "$LOG_FILE" ||
		die "ARMv7 identity was not observed; inspect $LOG_FILE"
	grep --fixed-strings --quiet 'validation-tooling-ok' "$LOG_FILE" ||
		die "static gdbserver validation was not observed; inspect $LOG_FILE"
	grep --fixed-strings --quiet 'validation-init-ok' "$LOG_FILE" ||
		die "validation init path was not observed; inspect $LOG_FILE"

	if [[ -f "$REPORT_FILE" ]]; then
		sed -i '/^## Validation result$/,$d' "$REPORT_FILE"
		cat >>"$REPORT_FILE" <<EOF

## Validation result

- Passed: QEMU booted the generated image and emitted Linux 3.10.108 with an ARMv7 machine name.
- Log: out/validation.log.
- Scope: boot and identity only; no exploit, flag, network endpoint, or vendor behavior was tested.
EOF
	fi
	printf 'Validation passed. Log: %s\n' "$LOG_FILE"
}

main "$@"
