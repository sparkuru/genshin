#!/usr/bin/env bash
set -Eeuo pipefail

# shellcheck shell=bash

if [[ "${BUILDROOT_COMMON_LOADED:-}" == 1 ]]; then
	return 0
fi
readonly BUILDROOT_COMMON_LOADED=1

readonly STYLE_RESET=$'\033[0m'
readonly STYLE_SUCCESS=$'\033[0;32m'
readonly STYLE_WARNING=$'\033[1;33m'
readonly STYLE_ERROR=$'\033[1;31m'

readonly DOWNLOADS_DIR="$PROFILE_DIR/downloads"
readonly DL_DIR="$DOWNLOADS_DIR/dl"
readonly BUILDROOT_SOURCE_DIR="$PROFILE_DIR/build/buildroot-$BUILDROOT_VERSION"
readonly BR_OUTPUT_DIR="$PROFILE_DIR/build/output"
readonly OUTPUT_DIR="$PROFILE_DIR/out"
readonly RUN_DIR="$OUTPUT_DIR/run"
readonly PID_FILE="$RUN_DIR/qemu.pid"
readonly SERIAL_LOG_FILE="$RUN_DIR/qemu-serial.log"
readonly VALIDATION_LOG_FILE="$OUTPUT_DIR/validation.log"
readonly RUNTIME_ROOTFS="$RUN_DIR/rootfs.ext4"
readonly VALIDATION_ROOTFS="$RUN_DIR/validation-rootfs.ext4"

color_text() {
	local style=$1
	local text=$2

	if [[ -n "${NO_COLOR:-}" || ! -t 1 ]]; then
		printf '%s' "$text"
		return 0
	fi
	printf '%s%s%s' "$style" "$text" "$STYLE_RESET"
}

info() {
	printf '%s\n' "$(color_text "$STYLE_SUCCESS" "$*")"
}

warn() {
	printf '%s\n' "$(color_text "$STYLE_WARNING" "Warning: $*")" >&2
}

die() {
	printf '%s\n' "$(color_text "$STYLE_ERROR" "Error: $*")" >&2
	exit 1
}

require_command() {
	command -v "$1" >/dev/null 2>&1 || die "required command not found: $1"
}

require_profile_variables() {
	local variable_name
	local -a required_variables=(
		PROFILE_DIR
		PROFILE_NAME
		BUILDROOT_VERSION
		BUILDROOT_ARCHIVE
		BUILDROOT_URL
		BUILDROOT_SHA256
		LINUX_VERSION
		LINUX_ARCHIVE
		LINUX_URL
		LINUX_SHA256
		LINUX_HEADERS_OPTION
		QEMU_PORT
		BUILDROOT_DEFCONFIG_TEMPLATE
	)

	for variable_name in "${required_variables[@]}"; do
		[[ -n "${!variable_name:-}" ]] || die "profile variable is empty: $variable_name"
	done
}

verify_file() {
	local expected=$1
	local file_path=$2

	[[ -f "$file_path" ]] || die "missing file: $file_path"
	printf '%s  %s\n' "$expected" "$file_path" | sha256sum --check --status - ||
		die "checksum mismatch: $file_path"
}

download_archive() {
	local url=$1
	local file_path=$2
	local checksum_file=$3
	local expected=$4
	local partial_path="$file_path.part"

	[[ "$expected" =~ ^[[:xdigit:]]{64}$ ]] ||
		die "invalid pinned checksum for $file_path"
	if [[ -f "$checksum_file" ]]; then
		local recorded
		recorded=$(awk 'NF >= 1 { print $1; exit }' "$checksum_file")
		[[ "$recorded" == "$expected" ]] ||
			die "checksum record does not match pinned checksum: $checksum_file"
	fi

	if [[ -f "$file_path" ]]; then
		verify_file "$expected" "$file_path"
		printf '%s  %s\n' "$expected" "$(basename "$file_path")" >"$checksum_file"
		return 0
	fi

	[[ ! -e "$partial_path" ]] || die "partial download exists: $partial_path"
	mkdir -p -- "$(dirname -- "$file_path")"
	info "Downloading $(basename "$file_path")"
	curl --fail --location --retry 3 --retry-delay 2 --connect-timeout 15 \
		--output "$partial_path" "$url"

	verify_file "$expected" "$partial_path"
	printf '%s  %s\n' "$expected" "$(basename "$file_path")" >"$checksum_file"
	mv -- "$partial_path" "$file_path"
}

extract_buildroot() {
	local archive_path="$DOWNLOADS_DIR/$BUILDROOT_ARCHIVE"

	if [[ -f "$BUILDROOT_SOURCE_DIR/.generated-by-chrysos" &&
		-f "$BUILDROOT_SOURCE_DIR/Makefile" ]]; then
		return 0
	fi
	[[ ! -e "$BUILDROOT_SOURCE_DIR" ]] ||
		die "incomplete generated Buildroot source directory exists: $BUILDROOT_SOURCE_DIR"

	mkdir -p -- "$BUILDROOT_SOURCE_DIR"
	tar --extract --file "$archive_path" --directory "$BUILDROOT_SOURCE_DIR" \
		--strip-components=1 --no-same-owner
	touch -- "$BUILDROOT_SOURCE_DIR/.generated-by-chrysos"
}

render_defconfig() {
	local rendered_path="$BR_OUTPUT_DIR/profile.defconfig"

	[[ -f "$BUILDROOT_DEFCONFIG_TEMPLATE" ]] ||
		die "missing Buildroot defconfig template: $BUILDROOT_DEFCONFIG_TEMPLATE"
	mkdir -p -- "$BR_OUTPUT_DIR"
	sed "s|@PROFILE_DIR@|$PROFILE_DIR|g" "$BUILDROOT_DEFCONFIG_TEMPLATE" >"$rendered_path"
	printf '%s\n' "$rendered_path"
}

buildroot_make() {
	GIT_CEILING_DIRECTORIES="$PROFILE_DIR" make -C "$BUILDROOT_SOURCE_DIR" \
		O="$BR_OUTPUT_DIR" \
		BR2_DL_DIR="$DL_DIR" "$@"
}

configure_buildroot() {
	local rendered_defconfig

	rendered_defconfig=$(render_defconfig)
	buildroot_make BR2_DEFCONFIG="$rendered_defconfig" defconfig
}

copy_output_file() {
	local source_path=$1
	local output_name=$2

	[[ -f "$source_path" ]] || die "Buildroot did not produce: $source_path"
	install -m 0644 -- "$source_path" "$OUTPUT_DIR/$output_name"
}

write_report() {
	local report_path="$OUTPUT_DIR/report.md"
	local generated_at

	generated_at=$(date -u '+%Y-%m-%dT%H:%M:%SZ')
	cat >"$report_path" <<EOF
# $PROFILE_NAME Buildroot report

Status: built

| Item | Value |
| --- | --- |
| Buildroot | $BUILDROOT_VERSION |
| Linux | $LINUX_VERSION |
| Architecture | AArch64 little-endian |
| CPU baseline | Cortex-A53 / Armv8-A |
| Toolchain headers | $LINUX_HEADERS_OPTION |
| QEMU machine | virt |
| Root filesystem | ext4 on virtio-blk |
| Host telnet port | 127.0.0.1:$QEMU_PORT |

## Inputs

| Input | SHA-256 |
| --- | --- |
| downloads/$BUILDROOT_ARCHIVE | $(sha256sum "$DOWNLOADS_DIR/$BUILDROOT_ARCHIVE" | awk '{ print $1 }') |
| $LINUX_ARCHIVE | $(sha256sum "$DL_DIR/$LINUX_ARCHIVE" | awk '{ print $1 }') |

## Derived artifacts

| Artifact | SHA-256 |
| --- | --- |
| out/Image | $(sha256sum "$OUTPUT_DIR/Image" | awk '{ print $1 }') |
| out/rootfs.ext4 | $(sha256sum "$OUTPUT_DIR/rootfs.ext4" | awk '{ print $1 }') |
| out/buildroot.config | $(sha256sum "$OUTPUT_DIR/buildroot.config" | awk '{ print $1 }') |

## Runtime boundary

The guest uses QEMU's generic virt machine with restricted user-mode
networking. Only TCP port 23 is forwarded to localhost when background mode
is selected. The filesystem is writable inside an ephemeral QEMU snapshot
during the guest session; the published ext4 image remains unchanged and no
host directory is shared.

Generated: $generated_at
EOF
}

prepare_runtime_rootfs() {
	local destination=$1

	rm -f -- "$destination"
	cp -- "$OUTPUT_DIR/rootfs.ext4" "$destination"
}

build_profile() {
	local option=
	local build_jobs=${JOBS:-4}
	local command_name

	require_profile_variables
	case "${1:-}" in
	"") ;;
	--help | -h)
		printf 'Usage: %s [--help]\n\n' "$SCRIPT_NAME"
		printf 'Build %s with Buildroot %s and Linux %s.\n' \
			"$PROFILE_NAME" "$BUILDROOT_VERSION" "$LINUX_VERSION"
		printf '\nEnvironment:\n  JOBS=N       Parallel build jobs. Default: 4.\n'
		printf '  NO_COLOR=1   Disable colored output.\n'
		return 0
		;;
	*)
		option=$1
		printf 'Usage: %s [--help]\n' "$SCRIPT_NAME" >&2
		die "unknown option: $option"
		;;
	esac

	[[ "$build_jobs" =~ ^[1-9][0-9]*$ ]] || die "JOBS must be a positive integer"
	for command_name in awk curl date install make mv mkdir sha256sum sed tar touch xz; do
		require_command "$command_name"
	done

	mkdir -p -- "$DOWNLOADS_DIR" "$DL_DIR" "$OUTPUT_DIR"
	download_archive "$BUILDROOT_URL" "$DOWNLOADS_DIR/$BUILDROOT_ARCHIVE" \
		"$DOWNLOADS_DIR/$BUILDROOT_ARCHIVE.sha256" "$BUILDROOT_SHA256"
	download_archive "$LINUX_URL" "$DL_DIR/$LINUX_ARCHIVE" \
		"$DOWNLOADS_DIR/$LINUX_ARCHIVE.sha256" "$LINUX_SHA256"
	extract_buildroot
	configure_buildroot
	info "Building $PROFILE_NAME with $build_jobs job(s)"
	buildroot_make -j"$build_jobs"

	copy_output_file "$BR_OUTPUT_DIR/images/Image" Image
	copy_output_file "$BR_OUTPUT_DIR/images/rootfs.ext4" rootfs.ext4
	copy_output_file "$BR_OUTPUT_DIR/.config" buildroot.config
	printf '%s\n' "$BUILDROOT_VERSION" >"$OUTPUT_DIR/buildroot.release"
	printf '%s\n' "$LINUX_VERSION" >"$OUTPUT_DIR/kernel.release"
	touch -- "$OUTPUT_DIR/.generated-by-chrysos"
	write_report
	info "Built $PROFILE_NAME in $OUTPUT_DIR"
	info "Run ./validate.sh before starting the interactive guest"
}

require_artifacts() {
	[[ -f "$OUTPUT_DIR/Image" ]] || die "missing $OUTPUT_DIR/Image; run ./build.sh"
	[[ -f "$OUTPUT_DIR/rootfs.ext4" ]] ||
		die "missing $OUTPUT_DIR/rootfs.ext4; run ./build.sh"
}

running_pid() {
	local pid
	local qemu_path

	[[ -f "$PID_FILE" ]] || return 1
	pid=$(<"$PID_FILE")
	[[ "$pid" =~ ^[1-9][0-9]*$ ]] || return 1
	kill -0 "$pid" 2>/dev/null || return 1
	command -v readlink >/dev/null 2>&1 || return 1
	qemu_path=$(command -v qemu-system-aarch64 2>/dev/null) || return 1
	qemu_path=$(readlink --canonicalize "$qemu_path") || return 1
	[[ -r "/proc/$pid/exe" ]] || return 1
	[[ "$(readlink --canonicalize "/proc/$pid/exe")" == "$qemu_path" ]] || return 1
	printf '%s\n' "$pid"
}

qemu_arguments() {
	local append_value=$1
	local serial_argument=$2
	local network_argument=${3:-"user,id=net0,restrict=on,hostfwd=tcp:127.0.0.1:$QEMU_PORT-:23"}
	local rootfs_image=${4:-"$OUTPUT_DIR/rootfs.ext4"}

	printf '%s\n' \
		qemu-system-aarch64 \
		-machine virt \
		-cpu cortex-a53 \
		-smp 2 \
		-m 512M \
		-kernel "$OUTPUT_DIR/Image" \
		-append "$append_value" \
		-netdev "$network_argument" \
		-device virtio-net-device,netdev=net0 \
		-drive "file=$rootfs_image,if=none,format=raw,id=hd0" \
		-device virtio-blk-device,drive=hd0 \
		-no-reboot \
		-display none \
		-serial "$serial_argument" \
		-monitor none
}

start_qemu_profile() {
	local option=${1:-}
	local mode=foreground
	local append_value='root=/dev/vda rw rootwait console=ttyAMA0,115200'
	local -a qemu_args=()
	local arg
	local qemu_status

	case "$option" in
	"") ;;
	--background)
		mode=background
		;;
	--help | -h)
		printf 'Usage: %s [--background]\n\n' "$SCRIPT_NAME"
		printf 'Start the %s AArch64 guest.\n' "$PROFILE_NAME"
		printf '  --background  Save serial output and expose telnet on '
		printf '127.0.0.1:%s.\n' "$QEMU_PORT"
		return 0
		;;
	*)
		printf 'Usage: %s [--background]\n' "$SCRIPT_NAME" >&2
		die "unknown option: $option"
		;;
	esac

	require_command cp
	require_command qemu-system-aarch64
	require_artifacts
	mkdir -p -- "$RUN_DIR"
	if [[ "$mode" == background ]]; then
		if running_pid >/dev/null; then
			die "QEMU is already running with PID $(running_pid)"
		fi
		rm -f -- "$PID_FILE"
	fi
	prepare_runtime_rootfs "$RUNTIME_ROOTFS"
	while IFS= read -r arg; do
		qemu_args+=("$arg")
	done < <(qemu_arguments "$append_value" "stdio" "" "$RUNTIME_ROOTFS")

	if [[ "$mode" == foreground ]]; then
		if "${qemu_args[@]}"; then
			qemu_status=0
		else
			qemu_status=$?
		fi
		rm -f -- "$RUNTIME_ROOTFS"
		return "$qemu_status"
	fi

	qemu_args=()
	while IFS= read -r arg; do
		qemu_args+=("$arg")
	done < <(qemu_arguments "$append_value" "file:$SERIAL_LOG_FILE" "" "$RUNTIME_ROOTFS")
	nohup "${qemu_args[@]}" >"$RUN_DIR/qemu.stdout.log" 2>&1 </dev/null &
	local pid=$!
	printf '%s\n' "$pid" >"$PID_FILE"
	sleep 1
	if ! running_pid >/dev/null; then
		rm -f -- "$PID_FILE"
		rm -f -- "$RUNTIME_ROOTFS"
		die "QEMU exited during startup; inspect $RUN_DIR/qemu.stdout.log"
	fi
	printf 'QEMU started with PID %s\n' "$pid"
	printf 'Guest telnetd: telnet 127.0.0.1 %s\n' "$QEMU_PORT"
	printf 'Serial log: %s\n' "$SERIAL_LOG_FILE"
	printf 'Stop: ./stop-qemu.sh\n'
}

stop_qemu_profile() {
	local option=${1:-}
	local pid
	local attempt

	case "$option" in
	"") ;;
	--help | -h)
		printf 'Usage: %s\n\n' "$SCRIPT_NAME"
		printf 'Stop the background QEMU instance for %s.\n' "$PROFILE_NAME"
		return 0
		;;
	*)
		printf 'Usage: %s\n' "$SCRIPT_NAME" >&2
		die "unknown option: $option"
		;;
	esac

	if ! pid=$(running_pid); then
		rm -f -- "$PID_FILE" "$RUNTIME_ROOTFS"
		printf '%s\n' 'QEMU is not running'
		return 0
	fi

	kill "$pid"
	for attempt in 1 2 3 4 5; do
		if ! kill -0 "$pid" 2>/dev/null; then
			rm -f -- "$PID_FILE" "$RUNTIME_ROOTFS"
			printf 'Stopped QEMU PID %s\n' "$pid"
			return 0
		fi
		if [[ "$attempt" -lt 5 ]]; then
			sleep 1
		fi
	done
	die "QEMU PID $pid did not stop after 5 seconds"
}

validate_profile() {
	local option=${1:-}
	local qemu_status
	local append_value
	local -a qemu_args=()
	local arg

	case "$option" in
	"") ;;
	--help | -h)
		printf 'Usage: %s\n\n' "$SCRIPT_NAME"
		printf 'Boot %s and verify kernel and AArch64 identity.\n' "$PROFILE_NAME"
		return 0
		;;
	*)
		printf 'Usage: %s\n' "$SCRIPT_NAME" >&2
		die "unknown option: $option"
		;;
	esac

	require_command cp
	require_command qemu-system-aarch64
	require_command timeout
	require_artifacts
	mkdir -p -- "$RUN_DIR"
	prepare_runtime_rootfs "$VALIDATION_ROOTFS"
	: >"$VALIDATION_LOG_FILE"
	append_value="root=/dev/vda rw rootwait console=ttyAMA0,115200 lab.validate=1"
	while IFS= read -r arg; do
		qemu_args+=("$arg")
	done < <(qemu_arguments "$append_value" "file:$VALIDATION_LOG_FILE" "user,id=net0,restrict=on" "$VALIDATION_ROOTFS")

	set +e
	timeout --signal=TERM 45s "${qemu_args[@]}"
	qemu_status=$?
	set -e
	if [[ "$qemu_status" -ne 0 && "$qemu_status" -ne 124 ]]; then
		rm -f -- "$VALIDATION_ROOTFS"
		die "QEMU validation failed with status $qemu_status; inspect $VALIDATION_LOG_FILE"
	fi
	rm -f -- "$VALIDATION_ROOTFS"
	grep --fixed-strings --quiet "$LINUX_VERSION" "$VALIDATION_LOG_FILE" ||
		die "kernel release was not observed; inspect $VALIDATION_LOG_FILE"
	grep --extended-regexp --quiet 'aarch64|AArch64' "$VALIDATION_LOG_FILE" ||
		die "AArch64 identity was not observed; inspect $VALIDATION_LOG_FILE"
	grep --fixed-strings --quiet 'validation-init-ok' "$VALIDATION_LOG_FILE" ||
		die "validation init path was not observed; inspect $VALIDATION_LOG_FILE"

	if [[ -f "$OUTPUT_DIR/report.md" ]]; then
		sed -i '/^## Validation result$/,$d' "$OUTPUT_DIR/report.md"
		cat >>"$OUTPUT_DIR/report.md" <<EOF

## Validation result

- Passed: QEMU booted the generated image and emitted Linux $LINUX_VERSION with AArch64 identity.
- Log: out/validation.log.
- Scope: boot, rootfs, network setup, and identity only; no exploit or vendor behavior was tested.
EOF
	fi
	printf 'Validation passed. Log: %s\n' "$VALIDATION_LOG_FILE"
}
