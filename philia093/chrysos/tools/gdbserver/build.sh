#!/usr/bin/env bash
set -Eeuo pipefail

script_name=$(basename "$0")
readonly SCRIPT_NAME="$script_name"
script_dir=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd -P)
readonly SCRIPT_DIR="$script_dir"
workspace_dir=$(CDPATH='' cd -- "$SCRIPT_DIR/../.." && pwd -P)
readonly WORKSPACE_DIR="$workspace_dir"
readonly SOURCE_DIR="$SCRIPT_DIR/src"
readonly BUILDS_DIR="$SCRIPT_DIR/builds"
readonly GDB_VERSION="14.2"
readonly GDB_ARCHIVE="gdb-$GDB_VERSION.tar.xz"
readonly GDB_URL="https://ftp.gnu.org/gnu/gdb/$GDB_ARCHIVE"
readonly GDB_SHA512="7e07941f1fe661288cc571b4964012ceabc1760624fce20320db2f470c01439b2386f859b5288da13204b758e2e3b22a74c68c012178db93b9529b06f1e22ede"
temporary_build_dir=""

if [[ -v JOBS ]]; then
	build_jobs=$JOBS
else
	build_jobs=4
fi

usage() {
	cat >&2 <<EOF
Usage: $SCRIPT_NAME (--arch <architecture[,architecture...]> | --profile <profile> | --list) [--install-rootfs] [--help]

Build static GNU gdbserver sidecar binaries for Chrysos profiles.

Architectures and profiles are discovered from profile.env descriptors.
Use --list to print the current registry. --arch all builds every profile.

Examples:
  ./$SCRIPT_NAME --arch aarch64,riscv64,mips32r2
  ./$SCRIPT_NAME --profile x86_64-linux-6.18.7-glibc --install-rootfs
  JOBS=8 ./$SCRIPT_NAME --arch all

The script downloads GNU GDB $GDB_VERSION from the official GNU mirror,
checks its published SHA-512 digest, and validates that each output has no
ELF interpreter and is statically linked.
EOF
}

die() {
	printf 'Error: %s\n' "$*" >&2
	exit 1
}

cleanup() {
	if [[ -n "$temporary_build_dir" && -d "$temporary_build_dir" &&
		"$temporary_build_dir" == "$BUILDS_DIR"/.gdbserver-* ]]; then
		rm -rf -- "$temporary_build_dir"
	fi
}

require_command() {
	command -v "$1" >/dev/null 2>&1 || die "required command not found: $1"
}

verify_sha512() {
	local file_path=$1

	printf '%s  %s\n' "$GDB_SHA512" "$file_path" | sha512sum --check --status - ||
		die "GNU GDB source checksum mismatch: $file_path"
}

prepare_source() {
	local archive_path="$SOURCE_DIR/$GDB_ARCHIVE"
	local partial_path="$archive_path.part"
	local source_tree="$SOURCE_DIR/gdb-$GDB_VERSION"

	mkdir -p -- "$SOURCE_DIR"
	if [[ ! -f "$archive_path" ]]; then
		require_command curl
		printf 'Downloading %s\n' "$GDB_URL"
		curl --fail --location --retry 3 --retry-delay 2 --connect-timeout 15 \
			--output "$partial_path" "$GDB_URL"
		verify_sha512 "$partial_path"
		mv -- "$partial_path" "$archive_path"
	fi
	verify_sha512 "$archive_path"

	if [[ ! -d "$source_tree" ]]; then
		printf 'Extracting %s\n' "$GDB_ARCHIVE"
		tar --extract --file "$archive_path" --directory "$SOURCE_DIR" --no-same-owner
	fi
	[[ -x "$source_tree/configure" ]] || die "unexpected GNU GDB source layout: $source_tree"
}

profile_env_paths() {
	find "$WORKSPACE_DIR" -mindepth 2 -maxdepth 2 -type f -name profile.env \
		-not -path "$WORKSPACE_DIR/templates/*" -print0
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
		TARGET_ARCHITECTURE) printf '%s\n' "$TARGET_ARCHITECTURE" ;;
		TARGET_COMPILER_PATH) printf '%s\n' "${TARGET_COMPILER_PATH:-}" ;;
		ROOTFS_INSTALL_DIR) printf '%s\n' "$ROOTFS_INSTALL_DIR" ;;
		*) die "unsupported profile field: $field_name" ;;
		esac
	)
}

profile_env_path() {
	local requested_name=$1
	local profile_env
	local profile_name

	while IFS= read -r -d '' profile_env; do
		profile_name=$(profile_field "$profile_env" PROFILE_NAME)
		if [[ "$profile_name" == "$requested_name" ]]; then
			printf '%s\n' "$profile_env"
			return 0
		fi
	done < <(profile_env_paths)
	die "unknown profile: $requested_name"
}

profile_directory() {
	local profile_env

	profile_env=$(profile_env_path "$1")
	printf '%s\n' "${profile_env%/profile.env}"
}

list_profiles() {
	local profile_env

	while IFS= read -r -d '' profile_env; do
		printf '%-36s %-14s %s\n' \
			"$(profile_field "$profile_env" PROFILE_NAME)" \
			"$(profile_field "$profile_env" TARGET_ARCHITECTURE)" \
			"$(profile_field "$profile_env" PROFILE_KIND)"
	done < <(profile_env_paths)
}

compiler_path() {
	local profile_name=$1
	local profile_env
	local profile_dir
	local configured_path
	local -a candidates=()

	profile_env=$(profile_env_path "$profile_name")
	profile_dir=$(profile_directory "$profile_name")
	configured_path=$(profile_field "$profile_env" TARGET_COMPILER_PATH)
	if [[ -n "$configured_path" ]]; then
		printf '%s\n' "$configured_path"
		return 0
	fi

	shopt -s nullglob
	candidates=("$profile_dir"/build/output/host/bin/*buildroot*-gcc)
	shopt -u nullglob
	[[ ${#candidates[@]} -eq 1 ]] ||
		die "expected one Buildroot cross compiler for $profile_name; build the profile first"
	printf '%s\n' "${candidates[0]}"
}

write_manifest() {
	local artifact_path=$1
	local manifest_path=$2
	local profile_name=$3
	local target_tuple=$4
	local target_readelf=$5
	local file_type
	local artifact_sha256

	file_type=$(file --brief "$artifact_path")
	[[ "$file_type" == *"statically linked"* ]] ||
		die "gdbserver is not statically linked for $profile_name: $file_type"
	if "$target_readelf" --program-headers "$artifact_path" | grep --quiet 'INTERP'; then
		die "gdbserver unexpectedly has an ELF interpreter: $profile_name"
	fi
	artifact_sha256=$(sha256sum "$artifact_path" | awk '{print $1}')

	cat >"$manifest_path" <<EOF
profile: $profile_name
target_tuple: $target_tuple
gdb_version: $GDB_VERSION
source_url: $GDB_URL
source_sha512: $GDB_SHA512
artifact: gdbserver
artifact_sha256: $artifact_sha256
file: $file_type
elf_interpreter: none
EOF
}

install_profile_rootfs() {
	local profile_name=$1
	local artifact_path=$2
	local profile_env
	local destination_path

	profile_env=$(profile_env_path "$profile_name")
	destination_path="$(profile_field "$profile_env" ROOTFS_INSTALL_DIR)/gdbserver"

	install -D -m 0755 -- "$artifact_path" "$destination_path"
	printf 'Installed %s into %s rootfs source\n' "$artifact_path" "$profile_name"
}

build_profile() {
	local profile_name=$1
	local compiler
	local compiler_prefix
	local cxx_compiler
	local target_readelf
	local target_tuple
	local source_tree="$SOURCE_DIR/gdb-$GDB_VERSION"
	local final_dir="$BUILDS_DIR/$profile_name/gdb-$GDB_VERSION"
	local temporary_dir

	compiler=$(compiler_path "$profile_name")
	[[ -x "$compiler" ]] || die "missing cross compiler for $profile_name: $compiler"
	compiler_prefix=${compiler%-gcc}
	cxx_compiler="${compiler_prefix}-g++"
	target_readelf="${compiler_prefix}-readelf"
	[[ -x "$cxx_compiler" ]] ||
		die "missing C++ cross compiler for $profile_name: $cxx_compiler"
	[[ -x "$target_readelf" ]] || die "missing target readelf for $profile_name: $target_readelf"
	target_tuple=$("$compiler" -dumpmachine)

	if [[ -e "$final_dir" ]]; then
		[[ -x "$final_dir/gdbserver" ]] ||
			die "existing build output is incomplete: $final_dir"
		write_manifest "$final_dir/gdbserver" "$final_dir/manifest.yml" "$profile_name" \
			"$target_tuple" "$target_readelf"
		printf 'Using existing %s\n' "$final_dir/gdbserver"
		if [[ "$install_rootfs" == true ]]; then
			install_profile_rootfs "$profile_name" "$final_dir/gdbserver"
		fi
		return 0
	fi
	mkdir -p -- "$(dirname -- "$final_dir")"
	temporary_dir=$(mktemp -d "$BUILDS_DIR/.gdbserver-$profile_name.XXXXXXXXXX")
	temporary_build_dir=$temporary_dir

	printf 'Building static gdbserver for %s (%s)\n' "$profile_name" "$target_tuple"
	(
		cd -- "$temporary_dir"
		mkdir -- build
		cd -- build
		env \
			CC="$compiler" \
			CXX="$cxx_compiler" \
			AR="${compiler_prefix}-ar" \
			RANLIB="${compiler_prefix}-ranlib" \
			CFLAGS="-O2 -pipe" \
			CXXFLAGS="-O2 -pipe" \
			LDFLAGS="-static" \
			"$source_tree/configure" \
			--build="$(gcc -dumpmachine)" \
			--host="$target_tuple" \
			--target="$target_tuple" \
			--disable-binutils \
			--disable-install-libbfd \
			--disable-ld \
			--disable-gas \
			--disable-gprof \
			--without-uiout \
			--disable-gdbtk \
			--without-x \
			--disable-sim \
			--without-included-gettext \
			--disable-werror \
			--enable-static \
			--disable-shared \
			--disable-source-highlight \
			--disable-gdb \
			--without-curses \
			--without-system-zlib \
			--enable-gdbserver \
			--disable-inprocess-agent
		make -j"$build_jobs"
	)

	[[ -x "$temporary_dir/build/gdbserver/gdbserver" ]] ||
		die "GNU GDB did not produce gdbserver for $profile_name"
	install -m 0755 -- "$temporary_dir/build/gdbserver/gdbserver" "$temporary_dir/gdbserver"
	write_manifest "$temporary_dir/gdbserver" "$temporary_dir/manifest.yml" "$profile_name" \
		"$target_tuple" "$target_readelf"
	mv -- "$temporary_dir" "$final_dir"
	temporary_build_dir=""
	printf 'Built %s\n' "$final_dir/gdbserver"
	if [[ "$install_rootfs" == true ]]; then
		install_profile_rootfs "$profile_name" "$final_dir/gdbserver"
	fi
}

append_profiles() {
	local requested_architecture=$1
	local profile_env
	local target_architecture
	local profile_name
	local found=false
	local selected_profile

	while IFS= read -r -d '' profile_env; do
		target_architecture=$(profile_field "$profile_env" TARGET_ARCHITECTURE)
		if [[ "$requested_architecture" != all &&
			"$target_architecture" != "$requested_architecture" ]]; then
			continue
		fi
		profile_name=$(profile_field "$profile_env" PROFILE_NAME)
		found=true
		for selected_profile in "${selected_profiles[@]}"; do
			[[ "$selected_profile" != "$profile_name" ]] || continue 2
		done
		selected_profiles+=("$profile_name")
	done < <(profile_env_paths)

	[[ "$found" == true ]] || die "unknown architecture: $requested_architecture"
}

main() {
	local arch_value=""
	local profile_value=""
	local list_only=false
	local architecture
	local -a requested_architectures=()

	while [[ $# -gt 0 ]]; do
		case "$1" in
		--arch)
			[[ $# -ge 2 ]] || die "--arch requires a value"
			arch_value=$2
			shift 2
			;;
		--profile)
			[[ $# -ge 2 ]] || die "--profile requires a value"
			profile_value=$2
			shift 2
			;;
		--install-rootfs)
			install_rootfs=true
			shift
			;;
		--list)
			list_only=true
			shift
			;;
		--help | -h)
			usage
			return 0
			;;
		*) die "unknown option: $1" ;;
		esac
	done

	[[ -n "$arch_value" || -n "$profile_value" ]] || {
		if [[ "$list_only" == true ]]; then
			require_command find
			list_profiles
			return 0
		fi
		usage
		return 1
	}
	[[ "$list_only" == false ]] || die "--list cannot be combined with a profile selection"
	[[ -z "$arch_value" || -z "$profile_value" ]] ||
		die "--arch and --profile cannot be used together"
	[[ "$build_jobs" =~ ^[1-9][0-9]*$ ]] || die "JOBS must be a positive integer"
	if [[ -n "$profile_value" ]]; then
		profile_directory "$profile_value" >/dev/null
		selected_profiles+=("$profile_value")
	else
		local IFS=','
		read -r -a requested_architectures <<<"$arch_value"
		for architecture in "${requested_architectures[@]}"; do
			[[ -n "$architecture" ]] || die "--arch contains an empty architecture"
			append_profiles "$architecture"
		done
	fi

	require_command awk
	require_command file
	require_command find
	require_command gcc
	require_command grep
	require_command install
	require_command make
	require_command mktemp
	require_command sha256sum
	require_command sha512sum
	require_command tar
	prepare_source
	for architecture in "${selected_profiles[@]}"; do
		build_profile "$architecture"
	done
}

declare -a selected_profiles=()
install_rootfs=false
trap cleanup EXIT
main "$@"
