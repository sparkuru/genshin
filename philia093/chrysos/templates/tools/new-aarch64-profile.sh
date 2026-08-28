#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_NAME=$(basename "$0")
readonly SCRIPT_NAME
script_dir=$(CDPATH='' cd -- "$(dirname -- "$0")" && pwd -P)
readonly SCRIPT_DIR="$script_dir"
readonly TEMPLATE_DIR="$SCRIPT_DIR/../buildroot-profile"
repository_root=$(CDPATH='' cd -- "$SCRIPT_DIR/../.." && pwd -P)
readonly REPOSITORY_ROOT="$repository_root"

profile_name=
buildroot_version=
buildroot_sha256=
linux_version=
linux_sha256=
linux_headers_option=
qemu_port=
output_root="$REPOSITORY_ROOT"
tmp_dir=
readonly -a RENDER_PATHS=(
	profile.env
	buildroot.defconfig.in
	readme.md
	board/rootfs-overlay/etc/hostname
	board/rootfs-overlay/etc/motd
)

usage() {
	cat >&2 <<EOF
Usage: $SCRIPT_NAME [options]

Create a Buildroot/AArch64 profile from the repository template.

Required options:
  --profile-name NAME            Profile directory and guest hostname
  --buildroot-version VERSION    Pinned Buildroot release
  --buildroot-sha256 SHA256      Buildroot archive checksum
  --linux-version VERSION        Pinned Linux release
  --linux-sha256 SHA256          Linux archive checksum
  --linux-headers-option SYMBOL  Buildroot custom-header symbol
  --qemu-port PORT               Unique localhost telnet port

Optional:
  --output-dir DIRECTORY         Destination parent; defaults to repository root
  -h, --help                     Show this help
EOF
}

die() {
	printf 'Error: %s\n' "$*" >&2
	exit 1
}

require_command() {
	command -v "$1" >/dev/null 2>&1 || die "required command not found: $1"
}

require_value() {
	local option=$1
	local value=${2:-}

	[[ -n "$value" ]] || die "missing value for $option"
}

parse_arguments() {
	while (($# > 0)); do
		case "$1" in
		--profile-name | --buildroot-version | --buildroot-sha256 | --linux-version | --linux-sha256 | --linux-headers-option | --qemu-port | --output-dir)
			require_value "$1" "${2:-}"
			case "$1" in
			--profile-name) profile_name=$2 ;;
			--buildroot-version) buildroot_version=$2 ;;
			--buildroot-sha256) buildroot_sha256=$2 ;;
			--linux-version) linux_version=$2 ;;
			--linux-sha256) linux_sha256=$2 ;;
			--linux-headers-option) linux_headers_option=$2 ;;
			--qemu-port) qemu_port=$2 ;;
			--output-dir) output_root=$2 ;;
			esac
			shift 2
			;;
		-h | --help)
			usage
			return 1
			;;
		--)
			shift
			break
			;;
		-*) die "unknown option: $1" ;;
		*) die "unexpected argument: $1" ;;
		esac
	done

	(($# == 0)) || die "unexpected argument: $1"
}

validate_inputs() {
	local variable_name
	local -a required_variables=(
		profile_name
		buildroot_version
		buildroot_sha256
		linux_version
		linux_sha256
		linux_headers_option
		qemu_port
	)

	for variable_name in "${required_variables[@]}"; do
		[[ -n "${!variable_name}" ]] || die "required option is missing: ${variable_name//_/-}"
	done
	[[ "$profile_name" =~ ^[a-z0-9]([a-z0-9.-]*[a-z0-9])?$ ]] ||
		die "profile name must be a lowercase hostname using letters, digits, dots, and hyphens"
	((${#profile_name} <= 63)) || die "profile name must not exceed 63 characters"
	[[ "$buildroot_version" =~ ^[0-9][0-9A-Za-z._-]*$ ]] || die "invalid Buildroot version"
	[[ "$linux_version" =~ ^[0-9]+\.[0-9]+(\.[0-9A-Za-z._-]+)*$ ]] || die "invalid Linux version"
	[[ "$buildroot_sha256" =~ ^[[:xdigit:]]{64}$ ]] || die "invalid Buildroot SHA-256"
	[[ "$linux_sha256" =~ ^[[:xdigit:]]{64}$ ]] || die "invalid Linux SHA-256"
	[[ "$linux_headers_option" =~ ^BR2_PACKAGE_HOST_LINUX_HEADERS_CUSTOM_[A-Z0-9_]+$ ]] ||
		die "invalid Buildroot Linux headers option"
	[[ "$qemu_port" =~ ^[0-9]+$ ]] || die "QEMU port must be an integer"
	((qemu_port >= 1024 && qemu_port <= 65535)) || die "QEMU port must be between 1024 and 65535"
	[[ -d "$output_root" ]] || die "output directory does not exist: $output_root"
	[[ -d "$TEMPLATE_DIR" ]] || die "template directory does not exist: $TEMPLATE_DIR"
	[[ -f "$TEMPLATE_DIR/common.sh" ]] || die "template does not contain common.sh: $TEMPLATE_DIR"
}

replace_token() {
	local token=$1
	local value=$2
	local file_path
	local relative_path
	local rendered_path

	for relative_path in "${RENDER_PATHS[@]}"; do
		file_path="$tmp_dir/$relative_path"
		rendered_path="$file_path.rendered"
		sed "s|@$token@|$value|g" "$file_path" >"$rendered_path"
		mv -- "$rendered_path" "$file_path"
	done
}

cleanup() {
	if [[ -n "$tmp_dir" && -d "$tmp_dir" ]]; then
		rm -rf -- "$tmp_dir"
	fi
}

render_profile() {
	local destination="$output_root/$profile_name"
	local file_path
	local relative_path
	local -a syntax_files
	local -a rendered_files=()

	[[ ! -e "$destination" ]] || die "destination already exists: $destination"
	tmp_dir=$(mktemp -d "$output_root/.buildroot-profile.XXXXXXXXXX")
	trap cleanup EXIT
	cp -R -- "$TEMPLATE_DIR/." "$tmp_dir/"

	replace_token PROFILE_NAME "$profile_name"
	replace_token BUILDROOT_VERSION "$buildroot_version"
	replace_token BUILDROOT_SHA256 "${buildroot_sha256,,}"
	replace_token LINUX_VERSION "$linux_version"
	replace_token LINUX_SHA256 "${linux_sha256,,}"
	replace_token LINUX_HEADERS_OPTION "$linux_headers_option"
	replace_token QEMU_PORT "$qemu_port"

	for relative_path in "${RENDER_PATHS[@]}"; do
		rendered_files+=("$tmp_dir/$relative_path")
	done
	if grep -R --line-number --extended-regexp \
		'@(PROFILE_NAME|BUILDROOT_VERSION|BUILDROOT_SHA256|LINUX_VERSION|LINUX_SHA256|LINUX_HEADERS_OPTION|QEMU_PORT)@' \
		"${rendered_files[@]}"; then
		die "generated profile contains unresolved template tokens"
	fi

	syntax_files=(
		"$tmp_dir/profile.env"
		"$tmp_dir/build.sh"
		"$tmp_dir/validate.sh"
		"$tmp_dir/run-qemu.sh"
		"$tmp_dir/stop-qemu.sh"
	)
	for file_path in "${syntax_files[@]}"; do
		bash -n "$file_path"
	done
	chmod 0755 -- "${syntax_files[@]:1}" \
		"$tmp_dir/board/rootfs-overlay/etc/init.d/S99chrysos"
	mv -- "$tmp_dir" "$destination"
	tmp_dir=
	trap - EXIT
	printf 'Created Buildroot profile: %s\n' "$destination"
	printf 'Next: cd %q && ./build.sh\n' "$destination"
}

main() {
	require_command bash
	require_command cp
	require_command grep
	require_command mktemp
	require_command mv
	require_command sed

	if ! parse_arguments "$@"; then
		return 0
	fi
	validate_inputs
	render_profile
}

main "$@"
