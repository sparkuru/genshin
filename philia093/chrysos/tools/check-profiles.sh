#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_NAME=$(basename "$0")
readonly SCRIPT_NAME
script_dir=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd -P)
readonly SCRIPT_DIR="$script_dir"
root_dir=$(CDPATH='' cd -- "$SCRIPT_DIR/.." && pwd -P)
readonly ROOT_DIR="$root_dir"

usage() {
	cat <<EOF
Usage: $SCRIPT_NAME

Validate every profile.env descriptor and its profile-specific lifecycle files.
The templates directory is intentionally excluded; template consistency is
checked by templates/tools/check-shell.sh.
EOF
}

die() {
	printf 'Error: %s\n' "$*" >&2
	exit 1
}

error() {
	printf 'Error: %s\n' "$*" >&2
}

require_command() {
	command -v "$1" >/dev/null 2>&1 || die "required command not found: $1"
}

profile_field() {
	local profile_env=$1
	local field_name=$2
	local profile_dir=${profile_env%/profile.env}

	(
		PROFILE_DIR=$profile_dir
		export PROFILE_DIR
		# shellcheck disable=SC1090 # Profile descriptors are discovered from this repository.
		source "$profile_env"
		# shellcheck disable=SC2153 # These variables are loaded from the descriptor above.
		case "$field_name" in
		PROFILE_NAME) printf '%s\n' "$PROFILE_NAME" ;;
		PROFILE_KIND) printf '%s\n' "$PROFILE_KIND" ;;
		QEMU_PORT) printf '%s\n' "$QEMU_PORT" ;;
		TARGET_ARCHITECTURE) printf '%s\n' "$TARGET_ARCHITECTURE" ;;
		KERNEL_MACHINE) printf '%s\n' "$KERNEL_MACHINE" ;;
		TARGET_ENDIAN) printf '%s\n' "$TARGET_ENDIAN" ;;
		TARGET_LIBC) printf '%s\n' "$TARGET_LIBC" ;;
		PROFILE_ABI) printf '%s\n' "$PROFILE_ABI" ;;
		PROFILE_FLOAT_ABI) printf '%s\n' "$PROFILE_FLOAT_ABI" ;;
		PROFILE_ELF_CLASS) printf '%s\n' "$PROFILE_ELF_CLASS" ;;
		USERSPACE_MODE) printf '%s\n' "$USERSPACE_MODE" ;;
		ROOTFS_INSTALL_DIR) printf '%s\n' "$ROOTFS_INSTALL_DIR" ;;
		TARGET_COMPILER_PATH) printf '%s\n' "${TARGET_COMPILER_PATH:-}" ;;
		QEMU_SYSTEM_BINARY) printf '%s\n' "$QEMU_SYSTEM_BINARY" ;;
		QEMU_BACKEND) printf '%s\n' "$QEMU_BACKEND" ;;
		QEMU_MACHINE) printf '%s\n' "$QEMU_MACHINE" ;;
		QEMU_SMP) printf '%s\n' "$QEMU_SMP" ;;
		QEMU_MEMORY) printf '%s\n' "$QEMU_MEMORY" ;;
		QEMU_SHARE_DEVICE) printf '%s\n' "$QEMU_SHARE_DEVICE" ;;
		KERNEL_IMAGE_NAME) printf '%s\n' "$KERNEL_IMAGE_NAME" ;;
		KERNEL_CONSOLE) printf '%s\n' "$KERNEL_CONSOLE" ;;
		ROOT_DEVICE) printf '%s\n' "$ROOT_DEVICE" ;;
		*) die "unsupported profile field: $field_name" ;;
		esac
	)
}

check_nonempty() {
	local profile_name=$1
	local field_name=$2
	local field_value=$3

	if [[ -z "$field_value" ]]; then
		error "$profile_name: empty profile field: $field_name"
		return 1
	fi
}

check_file() {
	local profile_name=$1
	local file_path=$2
	local description=$3

	if [[ ! -f "$file_path" ]]; then
		error "$profile_name: missing $description: $file_path"
		return 1
	fi
}

check_executable() {
	local profile_name=$1
	local file_path=$2
	local description=$3

	if [[ ! -x "$file_path" ]]; then
		error "$profile_name: missing or non-executable $description: $file_path"
		return 1
	fi
}

check_profile() {
	local profile_env=$1
	local profile_dir=${profile_env%/profile.env}
	local profile_basename=${profile_dir##*/}
	local profile_name
	local profile_kind
	local qemu_port
	local target_architecture
	local kernel_machine
	local target_endian
	local target_libc
	local profile_abi
	local profile_float_abi
	local profile_elf_class
	local userspace_mode
	local rootfs_install_dir
	local target_compiler_path
	local qemu_system_binary
	local qemu_backend
	local qemu_machine
	local qemu_smp
	local qemu_memory
	local qemu_share_device
	local kernel_image_name
	local kernel_console
	local root_device
	local status=0

	profile_name=$(profile_field "$profile_env" PROFILE_NAME)
	profile_kind=$(profile_field "$profile_env" PROFILE_KIND)
	qemu_port=$(profile_field "$profile_env" QEMU_PORT)
	target_architecture=$(profile_field "$profile_env" TARGET_ARCHITECTURE)
	kernel_machine=$(profile_field "$profile_env" KERNEL_MACHINE)
	target_endian=$(profile_field "$profile_env" TARGET_ENDIAN)
	target_libc=$(profile_field "$profile_env" TARGET_LIBC)
	profile_abi=$(profile_field "$profile_env" PROFILE_ABI)
	profile_float_abi=$(profile_field "$profile_env" PROFILE_FLOAT_ABI)
	profile_elf_class=$(profile_field "$profile_env" PROFILE_ELF_CLASS)
	userspace_mode=$(profile_field "$profile_env" USERSPACE_MODE)
	rootfs_install_dir=$(profile_field "$profile_env" ROOTFS_INSTALL_DIR)
	target_compiler_path=$(profile_field "$profile_env" TARGET_COMPILER_PATH)
	qemu_system_binary=$(profile_field "$profile_env" QEMU_SYSTEM_BINARY)
	qemu_backend=$(profile_field "$profile_env" QEMU_BACKEND)
	qemu_machine=$(profile_field "$profile_env" QEMU_MACHINE)
	qemu_smp=$(profile_field "$profile_env" QEMU_SMP)
	qemu_memory=$(profile_field "$profile_env" QEMU_MEMORY)
	qemu_share_device=$(profile_field "$profile_env" QEMU_SHARE_DEVICE)
	kernel_image_name=$(profile_field "$profile_env" KERNEL_IMAGE_NAME)
	kernel_console=$(profile_field "$profile_env" KERNEL_CONSOLE)
	root_device=$(profile_field "$profile_env" ROOT_DEVICE)

	check_nonempty "$profile_name" PROFILE_NAME "$profile_name" || status=1
	if [[ "$profile_name" != "$profile_basename" ]]; then
		error "$profile_basename: PROFILE_NAME does not match directory name: $profile_name"
		status=1
	fi
	check_nonempty "$profile_name" PROFILE_KIND "$profile_kind" || status=1
	check_nonempty "$profile_name" TARGET_ARCHITECTURE "$target_architecture" || status=1
	check_nonempty "$profile_name" KERNEL_MACHINE "$kernel_machine" || status=1
	check_nonempty "$profile_name" TARGET_LIBC "$target_libc" || status=1
	check_nonempty "$profile_name" PROFILE_ABI "$profile_abi" || status=1
	check_nonempty "$profile_name" PROFILE_FLOAT_ABI "$profile_float_abi" || status=1
	check_nonempty "$profile_name" USERSPACE_MODE "$userspace_mode" || status=1
	check_nonempty "$profile_name" ROOTFS_INSTALL_DIR "$rootfs_install_dir" || status=1
	check_nonempty "$profile_name" QEMU_SYSTEM_BINARY "$qemu_system_binary" || status=1
	check_nonempty "$profile_name" QEMU_BACKEND "$qemu_backend" || status=1
	check_nonempty "$profile_name" QEMU_MACHINE "$qemu_machine" || status=1
	check_nonempty "$profile_name" QEMU_MEMORY "$qemu_memory" || status=1
	check_nonempty "$profile_name" QEMU_SHARE_DEVICE "$qemu_share_device" || status=1
	check_nonempty "$profile_name" KERNEL_IMAGE_NAME "$kernel_image_name" || status=1
	check_nonempty "$profile_name" KERNEL_CONSOLE "$kernel_console" || status=1
	check_nonempty "$profile_name" ROOT_DEVICE "$root_device" || status=1

	if [[ ! "$qemu_port" =~ ^[0-9]+$ ]] || ((qemu_port < 1024 || qemu_port > 65535)); then
		error "$profile_name: QEMU_PORT must be between 1024 and 65535: $qemu_port"
		status=1
	fi
	if [[ "$target_endian" != little && "$target_endian" != big ]]; then
		error "$profile_name: TARGET_ENDIAN must be little or big: $target_endian"
		status=1
	fi
	if [[ "$profile_elf_class" != 32 && "$profile_elf_class" != 64 ]]; then
		error "$profile_name: PROFILE_ELF_CLASS must be 32 or 64: $profile_elf_class"
		status=1
	fi
	if [[ ! "$qemu_smp" =~ ^[1-9][0-9]*$ ]]; then
		error "$profile_name: QEMU_SMP must be a positive integer: $qemu_smp"
		status=1
	fi
	if [[ "$rootfs_install_dir" != "$profile_dir/"* ]]; then
		error "$profile_name: ROOTFS_INSTALL_DIR must stay inside the profile: $rootfs_install_dir"
		status=1
	fi

	case "$profile_kind" in
	buildroot)
		[[ "$userspace_mode" == buildroot-dynamic ]] || {
			error "$profile_name: Buildroot profiles must use buildroot-dynamic userspace"
			status=1
		}
		for required_file in build.sh validate.sh run-qemu.sh stop-qemu.sh common.sh \
			buildroot.defconfig.in board/linux.config \
			board/rootfs-overlay/etc/init.d/S99chrysos; do
			check_file "$profile_name" "$profile_dir/$required_file" "$required_file" || status=1
		done
		for lifecycle_file in build.sh validate.sh run-qemu.sh stop-qemu.sh; do
			check_executable "$profile_name" "$profile_dir/$lifecycle_file" "$lifecycle_file" || status=1
		done
		;;
	static-busybox)
		[[ "$userspace_mode" == static-busybox ]] || {
			error "$profile_name: static-busybox profiles must use static-busybox userspace"
			status=1
		}
		[[ "$target_libc" == none ]] || {
			error "$profile_name: static-busybox profiles must declare TARGET_LIBC=none"
			status=1
		}
		check_nonempty "$profile_name" TARGET_COMPILER_PATH "$target_compiler_path" || status=1
		for required_file in build.sh validate.sh run-qemu.sh stop-qemu.sh rootfs-template/init; do
			check_file "$profile_name" "$profile_dir/$required_file" "$required_file" || status=1
		done
		for lifecycle_file in build.sh validate.sh run-qemu.sh stop-qemu.sh; do
			check_executable "$profile_name" "$profile_dir/$lifecycle_file" "$lifecycle_file" || status=1
		done
		;;
	*)
		error "$profile_name: unsupported PROFILE_KIND: $profile_kind"
		status=1
		;;
	esac

	return "$status"
}

main() {
	local option=${1:-}
	local profile_env
	local profile_name
	local qemu_port
	local status=0
	local profile_count=0
	declare -A seen_names=()
	declare -A seen_ports=()

	case "$option" in
	"") ;;
	--help | -h)
		usage
		return 0
		;;
	*)
		usage >&2
		die "unknown option: $option"
		;;
	esac
	(($# <= 1)) || die "too many arguments"

	require_command find
	while IFS= read -r -d '' profile_env; do
		profile_count=$((profile_count + 1))
		if ! check_profile "$profile_env"; then
			status=1
		fi
		profile_name=$(profile_field "$profile_env" PROFILE_NAME)
		qemu_port=$(profile_field "$profile_env" QEMU_PORT)
		if [[ -n "${seen_names[$profile_name]+x}" ]]; then
			error "duplicate PROFILE_NAME: $profile_name"
			status=1
		fi
		if [[ -n "${seen_ports[$qemu_port]+x}" ]]; then
			error "duplicate QEMU_PORT $qemu_port: $profile_name and ${seen_ports[$qemu_port]}"
			status=1
		fi
		seen_names["$profile_name"]=$profile_env
		seen_ports["$qemu_port"]=$profile_name
		printf 'profile-ok name=%s arch=%s kind=%s port=%s\n' \
			"$profile_name" \
			"$(profile_field "$profile_env" TARGET_ARCHITECTURE)" \
			"$(profile_field "$profile_env" PROFILE_KIND)" \
			"$qemu_port"
	done < <(find "$ROOT_DIR" -mindepth 2 -maxdepth 2 -type f -name profile.env \
		-not -path "$ROOT_DIR/templates/*" -print0)

	((profile_count > 0)) || die "no profile.env descriptors found"
	if ((status == 0)); then
		printf 'Profile contract checks passed for %d profile(s).\n' "$profile_count"
	fi
	return "$status"
}

main "$@"
