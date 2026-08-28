#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_NAME=$(basename "$0")
readonly SCRIPT_NAME
script_dir=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd -P)
readonly SCRIPT_DIR="$script_dir"
root_dir=$(CDPATH='' cd -- "$SCRIPT_DIR/../.." && pwd -P)
readonly ROOT_DIR="$root_dir"

usage() {
	cat >&2 <<EOF
Usage: $SCRIPT_NAME [--check]

Without options, format repository-owned shell scripts and then run checks.
With --check, report formatting differences without changing files.
EOF
}

die() {
	printf 'Error: %s\n' "$*" >&2
	exit 1
}

require_command() {
	command -v "$1" >/dev/null 2>&1 || die "required command not found: $1"
}

collect_shell_files() {
	find "$ROOT_DIR" \
		-type d \( -name .git -o -name build -o -name downloads -o -name out \) -prune -o \
		-type f \( \
		-name '*.sh' -o \
		-name 'profile.env' -o \
		-path '*/board/rootfs-overlay/etc/init.d/*' -o \
		-path '*/rootfs-template/init' -o \
		-path '*/rootfs-template/sbin/*' -o \
		-path '*/rootfs-template/usr/share/udhcpc/*' \
		\) -print0
}

check_buildroot_profiles() {
	local profile_env
	local profile_dir
	local common_file
	local reference_common="$ROOT_DIR/templates/buildroot-profile/common.sh"
	local status=0
	local lifecycle_file
	local -a lifecycle_files=(build.sh validate.sh run-qemu.sh stop-qemu.sh)

	[[ -f "$reference_common" ]] || die "missing Buildroot common reference: $reference_common"
	while IFS= read -r -d '' profile_env; do
		profile_dir=$(dirname -- "$profile_env")
		common_file="$profile_dir/common.sh"
		if [[ ! -f "$common_file" ]]; then
			printf 'Error: Buildroot profile is missing common.sh: %s\n' "$profile_dir" >&2
			status=1
		elif ! cmp --silent "$reference_common" "$common_file"; then
			printf 'Error: common.sh differs from template: %s\n' "$profile_dir" >&2
			status=1
		fi
		for lifecycle_file in "${lifecycle_files[@]}"; do
			if [[ ! -x "$profile_dir/$lifecycle_file" ]]; then
				printf 'Error: lifecycle entry is missing or not executable: %s\n' \
					"$profile_dir/$lifecycle_file" >&2
				status=1
			elif ! cmp --silent \
				"$ROOT_DIR/templates/buildroot-profile/$lifecycle_file" \
				"$profile_dir/$lifecycle_file"; then
				printf 'Error: lifecycle entry differs from template: %s\n' \
					"$profile_dir/$lifecycle_file" >&2
				status=1
			fi
		done
	done < <(find "$ROOT_DIR" -mindepth 2 -maxdepth 2 -type f -name profile.env -print0)
	return "$status"
}

main() {
	local mode=format
	local status=0
	local file_path
	local -a shell_files=()

	case "${1:-}" in
	"") ;;
	--check) mode=check ;;
	-h | --help)
		usage
		return 0
		;;
	*)
		usage
		die "unknown option: $1"
		;;
	esac
	(($# <= 1)) || die "too many arguments"

	require_command bash
	require_command cmp
	require_command find
	require_command shellcheck
	require_command shfmt

	while IFS= read -r -d '' file_path; do
		shell_files+=("$file_path")
	done < <(collect_shell_files)
	((${#shell_files[@]} > 0)) || die "no shell scripts found"

	if [[ "$mode" == format ]]; then
		shfmt -w "${shell_files[@]}"
	elif ! shfmt -d "${shell_files[@]}"; then
		status=1
	fi

	for file_path in "${shell_files[@]}"; do
		if ! bash -n "$file_path"; then
			status=1
		fi
	done
	if ! shellcheck "${shell_files[@]}"; then
		status=1
	fi
	if ! check_buildroot_profiles; then
		status=1
	fi

	if ((status == 0)); then
		printf 'Shell format, syntax, and lint checks passed for %d file(s).\n' \
			"${#shell_files[@]}"
	fi
	return "$status"
}

main "$@"
