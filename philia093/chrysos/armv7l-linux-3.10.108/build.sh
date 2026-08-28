#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_NAME="$(basename "$0")"
readonly SCRIPT_NAME
ROOT_DIR="$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd -P)"
readonly ROOT_DIR
readonly DOWNLOADS_DIR="$ROOT_DIR/downloads"
readonly BUILD_DIR="$ROOT_DIR/build"
readonly OUTPUT_DIR="$ROOT_DIR/out"
readonly ROOTFS_TEMPLATE_DIR="$ROOT_DIR/rootfs-template"
readonly KERNEL_VERSION="3.10.108"
readonly BUSYBOX_VERSION="1.36.1"
readonly TOOLCHAIN_VERSION="12.3.rel1"
readonly KERNEL_ARCHIVE="linux-$KERNEL_VERSION.tar.xz"
readonly BUSYBOX_ARCHIVE="busybox-$BUSYBOX_VERSION.tar.bz2"
readonly TOOLCHAIN_ARCHIVE="arm-gnu-toolchain-$TOOLCHAIN_VERSION-x86_64-arm-none-linux-gnueabihf.tar.xz"
readonly KERNEL_URL="https://cdn.kernel.org/pub/linux/kernel/v3.x/$KERNEL_ARCHIVE"
readonly BUSYBOX_URL="https://busybox.net/downloads/$BUSYBOX_ARCHIVE"
readonly TOOLCHAIN_URL="https://developer.arm.com/-/media/Files/downloads/gnu/$TOOLCHAIN_VERSION/binrel/$TOOLCHAIN_ARCHIVE"
readonly KERNEL_SHA256="3849ea8119517f605f9d53c57dd6c539af8d584c2f1d9031f4f56283af3409a5"
readonly BUSYBOX_SHA256="b8cc24c9574d809e7279c3be349795c5d5ceb6fdf19ca709f80cde50e47de314"
readonly TOOLCHAIN_SHA256="f5f3c1cfcb429833d363e8fec31bb1282974b119ca8169d6277ce8a549e26d54"
readonly TOOLCHAIN_ROOT="$BUILD_DIR/arm-gnu-toolchain-12.3.rel1-x86_64-arm-none-linux-gnueabihf"
readonly KERNEL_SOURCE_DIR="$BUILD_DIR/linux-$KERNEL_VERSION"
readonly KERNEL_BUILD_DIR="$BUILD_DIR/kernel"
readonly BUSYBOX_SOURCE_DIR="$BUILD_DIR/busybox-$BUSYBOX_VERSION"
readonly BUSYBOX_BUILD_DIR="$BUILD_DIR/busybox-build"
readonly ROOTFS_DIR="$BUILD_DIR/rootfs"
readonly ROOTFS_DEVICE_LIST="$BUILD_DIR/rootfs-devices.list"
readonly ROOTFS_SU_BINARY="$BUILD_DIR/busybox-su"
readonly GENERATED_MARKER_NAME=".generated-by-user-qemu"

if [[ -v JOBS ]]; then
	build_jobs=$JOBS
else
	build_jobs=4
fi

style_reset=$'\033[0m'
style_success=$'\033[0;32m'
style_warning=$'\033[1;33m'
style_error=$'\033[1;31m'

color_text() {
	local style=$1
	local text=$2

	if [[ -v NO_COLOR || ! -t 1 ]]; then
		printf '%s' "$text"
		return 0
	fi
	printf '%s%s%s' "$style" "$text" "$style_reset"
}

info() {
	printf '%s\n' "$(color_text "$style_success" "$*")"
}

warn() {
	printf '%s\n' "$(color_text "$style_warning" "Warning: $*")" >&2
}

die() {
	printf '%s\n' "$(color_text "$style_error" "Error: $*")" >&2
	exit 1
}

usage() {
	cat >&2 <<EOF
Usage: $SCRIPT_NAME [--help]

Build Linux $KERNEL_VERSION for ARMv7 and a static BusyBox initramfs for QEMU.

Environment:
  JOBS=N       Parallel build jobs. Default: 4.
  NO_COLOR=1   Disable colored output.
EOF
}

require_command() {
	command -v "$1" >/dev/null 2>&1 || die "required command not found: $1"
}

require_commands() {
	local command_name

	for command_name in "$@"; do
		require_command "$command_name"
	done
}

validate_jobs() {
	[[ "$build_jobs" =~ ^[1-9][0-9]*$ ]] || die "JOBS must be a positive integer"
}

verify_file() {
	local expected=$1
	local file_path=$2

	[[ -f "$file_path" ]] || die "missing file: $file_path"
	printf '%s  %s\n' "$expected" "$file_path" | sha256sum --check --status - ||
		die "checksum mismatch: $file_path"
}

download_verified() {
	local url=$1
	local file_path=$2
	local expected=$3
	local partial_path="$file_path.part"

	if [[ -f "$file_path" ]]; then
		verify_file "$expected" "$file_path"
		return 0
	fi

	mkdir -p -- "$(dirname -- "$file_path")"
	info "Downloading $(basename "$file_path")"
	curl --fail --location --retry 3 --retry-delay 2 --connect-timeout 15 \
		--output "$partial_path" "$url"
	verify_file "$expected" "$partial_path"
	mv -- "$partial_path" "$file_path"
}

download_toolchain() {
	local file_path="$DOWNLOADS_DIR/$TOOLCHAIN_ARCHIVE"

	[[ -n "$TOOLCHAIN_SHA256" ]] || die "the toolchain checksum is not pinned in build.sh"
	download_verified "$TOOLCHAIN_URL" "$file_path" "$TOOLCHAIN_SHA256"
}

extract_source() {
	local archive_path=$1
	local target_dir=$2

	if compgen -G "$target_dir/.generated-by-*-qemu" >/dev/null; then
		return 0
	fi
	[[ ! -e "$target_dir" ]] || die "incomplete generated source directory exists: $target_dir"

	mkdir -p -- "$target_dir"
	tar --extract --file "$archive_path" --directory "$target_dir" \
		--strip-components=1 --no-same-owner
	touch -- "$target_dir/$GENERATED_MARKER_NAME"
}

extract_toolchain() {
	local archive_path="$DOWNLOADS_DIR/$TOOLCHAIN_ARCHIVE"

	if [[ -x "$TOOLCHAIN_ROOT/bin/arm-none-linux-gnueabihf-gcc" ]]; then
		return 0
	fi
	[[ ! -e "$TOOLCHAIN_ROOT" ]] || die "incomplete generated toolchain directory exists: $TOOLCHAIN_ROOT"

	mkdir -p -- "$BUILD_DIR"
	tar --extract --file "$archive_path" --directory "$BUILD_DIR" --no-same-owner
	[[ -x "$TOOLCHAIN_ROOT/bin/arm-none-linux-gnueabihf-gcc" ]] ||
		die "unexpected toolchain layout: $TOOLCHAIN_ROOT"
}

apply_kernel_compatibility() {
	local uaccess_file="$KERNEL_SOURCE_DIR/arch/arm/include/asm/uaccess.h"
	local old_declaration='register const typeof(*(p)) __r2 asm("r2")'
	local new_declaration='register typeof(*(p)) __r2 asm("r2")'

	[[ -f "$uaccess_file" ]] || die "missing ARM uaccess header: $uaccess_file"
	if grep --fixed-strings --quiet "$old_declaration" "$uaccess_file"; then
		sed --in-place 's/register const typeof(\*(p)) __r2/register typeof(\*(p)) __r2/' \
			"$uaccess_file"
	fi
	grep --fixed-strings --quiet "$new_declaration" "$uaccess_file" ||
		die "ARM uaccess compatibility patch did not apply"
}

set_config_value() {
	local config_file=$1
	local key=$2
	local value=$3

	if grep --fixed-strings --quiet "$key=" "$config_file"; then
		sed --in-place "s/^$key=.*/$key=$value/" "$config_file"
	elif grep --fixed-strings --quiet "# $key is not set" "$config_file"; then
		sed --in-place "s/^# $key is not set$/$key=$value/" "$config_file"
	else
		printf '%s=%s\n' "$key" "$value" >>"$config_file"
	fi
}

configure_busybox() {
	local config_file="$BUSYBOX_BUILD_DIR/.config"

	mkdir -p -- "$BUSYBOX_BUILD_DIR"
	make -C "$BUSYBOX_SOURCE_DIR" O="$BUSYBOX_BUILD_DIR" \
		CROSS_COMPILE="$CROSS_COMPILE" ARCH=arm defconfig
	set_config_value "$config_file" CONFIG_STATIC y
	set_config_value "$config_file" CONFIG_FEATURE_SH_STANDALONE n
	set_config_value "$config_file" CONFIG_FEATURE_SH_NOFORK y
	set_config_value "$config_file" CONFIG_INIT y
	set_config_value "$config_file" CONFIG_MOUNT y
	set_config_value "$config_file" CONFIG_UMOUNT y
	set_config_value "$config_file" CONFIG_MDEV y
	set_config_value "$config_file" CONFIG_SU y
	set_config_value "$config_file" CONFIG_LOGIN y
	set_config_value "$config_file" CONFIG_ADDUSER y
	set_config_value "$config_file" CONFIG_SETSID y
	set_config_value "$config_file" CONFIG_POWEROFF y
	set_config_value "$config_file" CONFIG_FEATURE_SYSLOG y
	set_config_value "$config_file" CONFIG_TELNETD y
	set_config_value "$config_file" CONFIG_FEATURE_TELNETD_STANDALONE y
	set_config_value "$config_file" CONFIG_UDHCPC y
	set_config_value "$config_file" CONFIG_IFCONFIG y
	set_config_value "$config_file" CONFIG_ROUTE y
	make -C "$BUSYBOX_SOURCE_DIR" O="$BUSYBOX_BUILD_DIR" \
		CROSS_COMPILE="$CROSS_COMPILE" ARCH=arm silentoldconfig </dev/null >/dev/null
}

build_busybox() {
	local file_type

	if [[ ! -x "$BUSYBOX_BUILD_DIR/busybox" ]]; then
		configure_busybox
		make -C "$BUSYBOX_SOURCE_DIR" O="$BUSYBOX_BUILD_DIR" \
			CROSS_COMPILE="$CROSS_COMPILE" ARCH=arm -j"$build_jobs"
	fi

	file_type=$(file -b "$BUSYBOX_BUILD_DIR/busybox")
	[[ "$file_type" == *ARM* && "$file_type" == *"statically linked"* ]] ||
		die "BusyBox is not a static ARM binary: $file_type"
}

prepare_rootfs() {
	[[ -d "$ROOTFS_TEMPLATE_DIR" ]] || die "missing rootfs template: $ROOTFS_TEMPLATE_DIR"
	[[ -f "$ROOTFS_TEMPLATE_DIR/init" ]] || die "missing init script"

	rm -rf -- "$ROOTFS_DIR"
	mkdir -p -- "$ROOTFS_DIR"
	make -C "$BUSYBOX_SOURCE_DIR" O="$BUSYBOX_BUILD_DIR" \
		CROSS_COMPILE="$CROSS_COMPILE" ARCH=arm CONFIG_PREFIX="$ROOTFS_DIR" install
	rm -f -- "$ROOTFS_DIR/bin/su"
	install -m 0755 -- "$BUSYBOX_BUILD_DIR/busybox" "$ROOTFS_SU_BINARY"
	cp --archive -- "$ROOTFS_TEMPLATE_DIR/." "$ROOTFS_DIR/"
	mkdir -p -- "$ROOTFS_DIR/dev/pts" "$ROOTFS_DIR/proc" "$ROOTFS_DIR/sys" \
		"$ROOTFS_DIR/tmp" "$ROOTFS_DIR/run" "$ROOTFS_DIR/root" "$ROOTFS_DIR/home/user"
	printf '%s\n' \
		'nod /dev/console 0600 0 0 c 5 1' \
		"file /bin/su $ROOTFS_SU_BINARY 04755 0 0" >"$ROOTFS_DEVICE_LIST"
	chmod 0755 "$ROOTFS_DIR/init"
	chmod 0755 "$ROOTFS_DIR/sbin/telnet-login"
	chmod 0755 "$ROOTFS_DIR/usr/share/udhcpc/default.script"
	chmod 0600 "$ROOTFS_DIR/etc/shadow"
	touch -- "$ROOTFS_DIR/$GENERATED_MARKER_NAME"
}

configure_kernel() {
	local config_file="$KERNEL_BUILD_DIR/.config"
	local config_tool="$KERNEL_SOURCE_DIR/scripts/config"

	mkdir -p -- "$KERNEL_BUILD_DIR"
	make -C "$KERNEL_SOURCE_DIR" O="$KERNEL_BUILD_DIR" ARCH=arm \
		CROSS_COMPILE="$CROSS_COMPILE" vexpress_defconfig
	[[ -x "$config_tool" ]] || chmod +x "$config_tool"
	"$config_tool" --file "$config_file" --enable AEABI
	"$config_tool" --file "$config_file" --enable OABI_COMPAT
	"$config_tool" --file "$config_file" --enable VFP
	"$config_tool" --file "$config_file" --disable DEBUG_VEXPRESS_UART0_DETECT
	"$config_tool" --file "$config_file" --enable DEBUG_VEXPRESS_UART0_CA9
	"$config_tool" --file "$config_file" --enable DEVTMPFS
	"$config_tool" --file "$config_file" --enable DEVTMPFS_MOUNT
	"$config_tool" --file "$config_file" --enable BLK_DEV_INITRD
	"$config_tool" --file "$config_file" --enable VIRTIO
	"$config_tool" --file "$config_file" --enable VIRTIO_MMIO
	"$config_tool" --file "$config_file" --enable NET_9P
	"$config_tool" --file "$config_file" --enable NET_9P_VIRTIO
	"$config_tool" --file "$config_file" --enable 9P_FS
	"$config_tool" --file "$config_file" --set-str INITRAMFS_SOURCE \
		"$ROOTFS_DIR $ROOTFS_DEVICE_LIST"
	"$config_tool" --file "$config_file" --enable BINFMT_ELF
	"$config_tool" --file "$config_file" --enable BINFMT_SCRIPT
	"$config_tool" --file "$config_file" --enable KALLSYMS
	"$config_tool" --file "$config_file" --enable KALLSYMS_ALL
	"$config_tool" --file "$config_file" --enable DEBUG_INFO
	"$config_tool" --file "$config_file" --enable FRAME_POINTER
	"$config_tool" --file "$config_file" --enable MODULES
	"$config_tool" --file "$config_file" --enable MODULE_UNLOAD
	"$config_tool" --file "$config_file" --enable IKCONFIG
	"$config_tool" --file "$config_file" --enable IKCONFIG_PROC
	"$config_tool" --file "$config_file" --enable USER_NS
	"$config_tool" --file "$config_file" --set-str LOCALVERSION ""
	make -C "$KERNEL_SOURCE_DIR" O="$KERNEL_BUILD_DIR" ARCH=arm \
		CROSS_COMPILE="$CROSS_COMPILE" olddefconfig
}

build_kernel() {
	configure_kernel
	make -C "$KERNEL_SOURCE_DIR" O="$KERNEL_BUILD_DIR" ARCH=arm \
		CROSS_COMPILE="$CROSS_COMPILE" \
		HOSTCFLAGS=-fcommon -j"$build_jobs" zImage dtbs
	[[ -f "$KERNEL_BUILD_DIR/arch/arm/boot/zImage" ]] || die "kernel zImage was not produced"
	[[ -f "$KERNEL_BUILD_DIR/arch/arm/boot/dts/vexpress-v2p-ca9.dtb" ]] ||
		die "vexpress-v2p-ca9.dtb was not produced"
}

write_outputs() {
	mkdir -p -- "$OUTPUT_DIR"
	install -m 0644 "$KERNEL_BUILD_DIR/arch/arm/boot/zImage" "$OUTPUT_DIR/zImage"
	install -m 0644 "$KERNEL_BUILD_DIR/arch/arm/boot/dts/vexpress-v2p-ca9.dtb" \
		"$OUTPUT_DIR/vexpress-v2p-ca9.dtb"
	install -m 0644 "$KERNEL_BUILD_DIR/.config" "$OUTPUT_DIR/kernel.config"
	printf '%s\n' "$KERNEL_VERSION" >"$OUTPUT_DIR/kernel.release"
	touch -- "$OUTPUT_DIR/$GENERATED_MARKER_NAME"
}

write_report() {
	local report_path="$OUTPUT_DIR/report.md"
	local readme_path="$OUTPUT_DIR/README.md"
	local generated_at

	generated_at=$(date -u '+%Y-%m-%dT%H:%M:%SZ')
	cat >"$readme_path" <<EOF
# ARMv7 Linux 3.10.108 QEMU environment

Reproduction tier: authoritative-high-fidelity for the supplied kernel version and architecture.

The source metadata only identifies Linux $KERNEL_VERSION on armv7l; it does not include the original firmware, root filesystem, device tree, or hardware configuration. This workspace therefore builds a minimal static BusyBox initramfs and boots the matching upstream kernel on QEMU's ARM Versatile Express A9 model.

## Start

Build the environment:

    ./build.sh
    ./validate.sh

Run an interactive unprivileged shell:

    ./run-qemu.sh

The foreground console is attached to the terminal. The initramfs starts the user account; use su - root when a root shell is required. The root account has an empty password because this is a disposable local lab image.

For a background VM, use ./run-qemu.sh --background and connect only through telnet 127.0.0.1 4545. Add --share /path/to/programs to mount that host directory read-only at /mnt/host. Stop the VM with ./stop-qemu.sh.

## Reset and isolation

The guest has no disk. Every boot creates a fresh in-kernel initramfs. QEMU uses the emulated Cortex-A9 CPU and the vexpress-a9 machine; KVM is not required. The emulated LAN9118 NIC uses restricted QEMU user networking. Only guest TCP port 23 is forwarded to host 127.0.0.1:4545 in background mode. A host directory is shared only when --share is selected, and that mount is read-only. No LAN bridge, host networking, USB, or clipboard is configured.

## Limitations

This is a same-version, same-architecture kernel laboratory, not a claim that the original target's vendor configuration or vulnerability state is reproduced. Kernel configuration, compiler, initramfs contents, virtual hardware, timing, and device names differ from the unknown source device. No exploit, flag, or non-documented service behavior is exercised.

Generated: $generated_at
EOF

	cat >"$report_path" <<EOF
# QEMU normalization report

Status: normalized
Reproduction tier: authoritative-high-fidelity

## Source evidence

- readme.txt: Linux $KERNEL_VERSION, armv7l.
- No kernel image, rootfs, disk image, firmware, service bundle, or hardware manifest was supplied.
- Artifact form: source-only target metadata; no original VM or disk artifact.

## Runtime decision

QEMU ARMv7 is authoritative because the requested reproduction depends on an exact kernel release and architecture. Docker was not proposed: the kernel, boot chain, privilege model, and virtual hardware are relevant or unknown.

The generated kernel source receives one compatibility-only adjustment in the ARM uaccess header: the const qualifier is removed from a local register variable so modern GCC preserves the required r2 allocation. This does not change the kernel release string or the supplied source archive.

## Inputs

| Input | SHA-256 |
| --- | --- |
| downloads/$KERNEL_ARCHIVE | $(sha256sum "$DOWNLOADS_DIR/$KERNEL_ARCHIVE" | cut -d ' ' -f 1) |
| downloads/$BUSYBOX_ARCHIVE | $(sha256sum "$DOWNLOADS_DIR/$BUSYBOX_ARCHIVE" | cut -d ' ' -f 1) |
| downloads/$TOOLCHAIN_ARCHIVE | $(sha256sum "$DOWNLOADS_DIR/$TOOLCHAIN_ARCHIVE" | cut -d ' ' -f 1) |

## Derived artifacts

| Artifact | SHA-256 |
| --- | --- |
| out/zImage | $(sha256sum "$OUTPUT_DIR/zImage" | cut -d ' ' -f 1) |
| out/vexpress-v2p-ca9.dtb | $(sha256sum "$OUTPUT_DIR/vexpress-v2p-ca9.dtb" | cut -d ' ' -f 1) |
| out/kernel.config | $(sha256sum "$OUTPUT_DIR/kernel.config" | cut -d ' ' -f 1) |

## Virtual hardware and policy

- QEMU machine: vexpress-a9; CPU: cortex-a9; RAM: 256 MiB.
- Kernel console: ttyAMA0, 115200 baud, attached to the foreground terminal; background serial output is saved in out/run/qemu-serial.log.
- Storage: none; the BusyBox initramfs is built into the kernel.
- Network: QEMU user-mode LAN9118 NIC with restrict=on; guest DHCP is ephemeral.
- Host exposure: guest telnetd is forwarded only to 127.0.0.1:4545 in background mode.
- Optional host share: --share mounts one existing host directory read-only at /mnt/host through virtio-9p.
- State: ephemeral; rebooting resets the initramfs.

## Validation

Run ./validate.sh to boot a non-interactive validation path. It checks the kernel's reported release and machine name, then requests a guest poweroff. Validation covers boot and identity only; it does not test an exploit or claim vendor-firmware equivalence.

Generated: $generated_at
EOF
}

main() {
	local option=

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

	require_commands curl sha256sum tar make file grep sed cp chmod mkdir install touch date cut qemu-system-arm
	validate_jobs
	mkdir -p -- "$DOWNLOADS_DIR" "$BUILD_DIR" "$OUTPUT_DIR"

	download_verified "$KERNEL_URL" "$DOWNLOADS_DIR/$KERNEL_ARCHIVE" "$KERNEL_SHA256"
	download_verified "$BUSYBOX_URL" "$DOWNLOADS_DIR/$BUSYBOX_ARCHIVE" "$BUSYBOX_SHA256"
	download_toolchain
	extract_source "$DOWNLOADS_DIR/$KERNEL_ARCHIVE" "$KERNEL_SOURCE_DIR"
	extract_source "$DOWNLOADS_DIR/$BUSYBOX_ARCHIVE" "$BUSYBOX_SOURCE_DIR"
	extract_toolchain
	apply_kernel_compatibility

	readonly CROSS_COMPILE="$TOOLCHAIN_ROOT/bin/arm-none-linux-gnueabihf-"
	build_busybox
	prepare_rootfs
	build_kernel
	write_outputs
	write_report

	info "Built Linux $KERNEL_VERSION for ARMv7 in $OUTPUT_DIR"
	info "Run ./validate.sh before starting the interactive VM"
}

main "$@"
