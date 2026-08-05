#!/usr/bin/env bash
set -Eeuo pipefail

readonly SCRIPT_NAME=${0##*/}
readonly HERDR_INSTALLER_URL='https://herdr.dev/install.sh'
readonly STYLE_RESET=$'\033[0m'
readonly STYLE_SUCCESS=$'\033[0;32m'
readonly STYLE_WARNING=$'\033[1;33m'
readonly STYLE_ERROR=$'\033[1;31m'

install_dir=''
force=false
uninstall=false
tmp_dir=''
platform=''

usage() {
	printf 'Usage:\n' >&2
	printf '  %s --path <installation-directory> [--force]\n' "$SCRIPT_NAME" >&2
	printf '  %s --uninstall --path <installation-directory>\n' "$SCRIPT_NAME" >&2
	printf '\nInstall or remove herdr and its command link.\n' >&2
	printf '\nOptions:\n' >&2
	printf '  --path <directory>  Installation directory (required).\n' >&2
	printf '  --force             Replace existing herdr binary and command link.\n' >&2
	printf '  --uninstall         Remove herdr installed at --path.\n' >&2
	printf '  --help              Show this help message.\n' >&2
}

color_text() {
	local style=$1
	local message=$2

	if [[ -n "${NO_COLOR:-}" || ! -t 1 ]]; then
		printf '%s' "$message"
		return
	fi

	printf '%s%s%s' "$style" "$message" "$STYLE_RESET"
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

detect_platform() {
	local system architecture

	system=$(uname -s)
	architecture=$(uname -m)

	case "$system/$architecture" in
	Darwin/arm64 | Darwin/aarch64)
		platform='macos/aarch64'
		;;
	Darwin/x86_64 | Darwin/amd64)
		platform='macos/x86_64'
		;;
	Linux/arm64 | Linux/aarch64)
		platform='linux/aarch64'
		;;
	Linux/x86_64 | Linux/amd64)
		platform='linux/x86_64'
		;;
	*)
		die "unsupported system architecture: $system/$architecture"
		;;
	esac
}

cleanup() {
	if [[ -n "$tmp_dir" && -d "$tmp_dir" ]]; then
		rm -rf -- "$tmp_dir"
	fi
}

parse_arguments() {
	while [[ $# -gt 0 ]]; do
		case "$1" in
		--path)
			[[ $# -ge 2 ]] || die '--path requires a directory'
			[[ -z "$install_dir" ]] || die '--path may only be specified once'
			install_dir=$2
			shift 2
			;;
		--force)
			force=true
			shift
			;;
		--uninstall)
			uninstall=true
			shift
			;;
		--help | -h)
			usage
			exit 0
			;;
		*)
			die "unknown argument: $1"
			;;
		esac
	done

	[[ -n "$install_dir" ]] || die 'an installation directory is required; pass --path <directory>'
	[[ "$uninstall" == false || "$force" == false ]] || die '--force cannot be used with --uninstall'
}

resolve_install_dir() {
	if [[ "$install_dir" != /* ]]; then
		install_dir=$PWD/$install_dir
	fi

	install_dir=${install_dir%/}
	[[ -n "$install_dir" && "$install_dir" != '/' ]] || die 'refusing to use the filesystem root as the installation directory'
}

assert_replaceable() {
	local path=$1

	if [[ -e "$path" || -L "$path" ]]; then
		[[ "$force" == true ]] || die "path already exists: $path (pass --force to replace it)"
		[[ ! -d "$path" || -L "$path" ]] || die "refusing to replace directory: $path"
	fi
}

is_managed_link() {
	local bin_link=$1
	local executable=$2

	[[ -L "$bin_link" ]] && [[ "$(readlink -- "$bin_link")" == "$executable" ]]
}

create_command_link() {
	local executable=$1
	local bin_link=$2

	case "$platform" in
	macos/*)
		ln -sfn -- "$executable" "$bin_link"
		;;
	linux/*)
		ln -sfnT -- "$executable" "$bin_link"
		;;
	*)
		die "unsupported platform: $platform"
		;;
	esac
}

install_herdr() {
	local bin_dir=$1
	local bin_link=$2
	local executable="$install_dir/herdr"
	local installer_path

	assert_replaceable "$executable"
	assert_replaceable "$bin_link"

	mkdir -p -- "$install_dir" "$bin_dir"
	tmp_dir=$(mktemp -d "${TMPDIR:-/tmp}/herdr-install.XXXXXXXX")
	trap cleanup EXIT
	installer_path="$tmp_dir/install.sh"

	curl --fail --location --retry 3 --output "$installer_path" "$HERDR_INSTALLER_URL"
	HERDR_INSTALL_DIR="$install_dir" sh "$installer_path"
	[[ -x "$executable" ]] || die "installer did not create an executable: $executable"

	create_command_link "$executable" "$bin_link"

	info 'herdr installation complete'
	printf '  Binary:  %s\n' "$executable"
	printf '  Command: %s\n' "$bin_link"
}

uninstall_herdr() {
	local bin_link=$1
	local executable="$install_dir/herdr"

	[[ -f "$executable" && ! -L "$executable" ]] || die "herdr executable not found: $executable"

	if [[ -e "$bin_link" || -L "$bin_link" ]]; then
		if is_managed_link "$bin_link" "$executable"; then
			rm -- "$bin_link"
		else
			warn "leaving command link unchanged: $bin_link"
		fi
	fi

	rm -- "$executable"
	rmdir -- "$install_dir" 2>/dev/null || warn "leaving non-empty installation directory: $install_dir"

	info 'herdr uninstalled'
	printf '  Removed binary: %s\n' "$executable"
}

main() {
	local bin_dir bin_link

	parse_arguments "$@"
	resolve_install_dir
	require_command mkdir
	require_command rm
	require_command rmdir
	require_command readlink

	bin_dir="$HOME/.local/bin"
	bin_link="$bin_dir/herdr"

	if [[ "$uninstall" == true ]]; then
		uninstall_herdr "$bin_link"
		return
	fi

	require_command curl
	require_command mktemp
	require_command sh
	require_command ln
	require_command uname
	detect_platform
	install_herdr "$bin_dir" "$bin_link"
}

if [[ ${BASH_SOURCE[0]} == "$0" ]]; then
	main "$@"
fi
