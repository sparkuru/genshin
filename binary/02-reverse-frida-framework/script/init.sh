#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_NAME=$(basename "$0")
readonly SCRIPT_NAME
readonly DEFAULT_SERVER_DIR_NAME="frida-server"
readonly RELEASE_BASE_URL="https://github.com/frida/frida/releases/download"
readonly STYLE_RESET=$'\033[0m'
readonly STYLE_TITLE=$'\033[1;36m'
readonly STYLE_SUB_TITLE=$'\033[1;34m'
readonly STYLE_CONTENT=$'\033[0;37m'
readonly STYLE_SUCCESS=$'\033[0;32m'
readonly STYLE_WARNING=$'\033[1;33m'
readonly STYLE_ERROR=$'\033[1;31m'

server_dir=""
force=false
tmp_dir=""

color_text() {
	local style=$1
	local message=$2

	if [[ -n "${NO_COLOR:-}" || ! -t 1 ]]; then
		printf '%s' "$message"
		return 0
	fi

	printf '%s%s%s' "$style" "$message" "$STYLE_RESET"
}

info() {
	printf '%s\n' "$(color_text "$STYLE_CONTENT" "$*")"
}

title() {
	printf '\n%s\n' "$(color_text "$STYLE_TITLE" "== $* ==")"
}

section() {
	printf '%s\n' "$(color_text "$STYLE_SUB_TITLE" "-- $* --")"
}

success() {
	printf '%s\n' "$(color_text "$STYLE_SUCCESS" "$*")"
}

warn() {
	printf '%s\n' "$(color_text "$STYLE_WARNING" "Warning: $*")" >&2
}

die() {
	printf '%s\n' "$(color_text "$STYLE_ERROR" "Error: $*")" >&2
	exit 1
}

usage() {
	printf 'Usage: %s [--server-dir <directory>] [--force]\n' "$SCRIPT_NAME"
	printf '\nInstall frida-tools for the current user and download Android Frida servers.\n'
	printf 'The default server directory is a frida-server sibling of the frida executable.\n'
}

cleanup() {
	if [[ -n "$tmp_dir" && -d "$tmp_dir" ]]; then
		rm -rf -- "$tmp_dir"
	fi
}

require_command() {
	command -v "$1" >/dev/null 2>&1 || die "required command not found: $1"
}

find_python() {
	local candidate

	for candidate in python3 python; do
		if command -v "$candidate" >/dev/null 2>&1 && "$candidate" -c 'import sys' >/dev/null 2>&1; then
			printf '%s' "$candidate"
			return 0
		fi
	done

	die "Python 3 is required to install frida-tools"
}

find_frida() {
	local python_bin=$1
	local user_base
	local candidate

	candidate=$(command -v frida || true)
	if [[ -n "$candidate" && -x "$candidate" ]]; then
		printf '%s' "$candidate"
		return 0
	fi

	user_base=$("$python_bin" -c 'import site; print(site.USER_BASE)')
	candidate="$user_base/bin/frida"
	[[ -x "$candidate" ]] || die "frida was installed but is not executable at $candidate; add its bin directory to PATH"
	printf '%s' "$candidate"
}

download_server() {
	local version=$1
	local architecture=$2
	local destination=$3
	local archive_name="frida-server-${version}-android-${architecture}.xz"
	local source_url="${RELEASE_BASE_URL}/${version}/${archive_name}"
	local archive_path="$tmp_dir/$archive_name"

	if [[ -e "$destination" && "$force" != true ]]; then
		warn "keeping existing server: $destination"
		return 0
	fi

	info "Downloading Android ${architecture} server"
	curl --fail --location --retry 3 --output "$archive_path" "$source_url"
	xz --decompress --stdout "$archive_path" >"$destination"
	chmod 0755 "$destination"
}

parse_arguments() {
	while [[ $# -gt 0 ]]; do
		case "$1" in
		--server-dir)
			[[ $# -ge 2 ]] || die "--server-dir requires a directory"
			server_dir=$2
			shift 2
			;;
		--force)
			force=true
			shift
			;;
		--help | -h)
			usage
			exit 0
			;;
		*)
			die "unknown option: $1"
			;;
		esac
	done
}

main() {
	local python_bin
	local frida_bin
	local frida_version
	local architecture
	local destination

	parse_arguments "$@"
	title "Frida initialization"
	section "Checking prerequisites"
	require_command curl
	require_command xz
	python_bin=$(find_python)

	if ! "$python_bin" -m pip --version >/dev/null 2>&1; then
		"$python_bin" -m ensurepip --user || die "pip is unavailable; install pip for $python_bin"
	fi

	section "Installing Frida tools"
	info "Installing frida-tools for the current user"
	"$python_bin" -m pip install --user --upgrade frida-tools
	frida_bin=$(find_frida "$python_bin")
	frida_version=$("$frida_bin" --version)
	[[ "$frida_version" =~ ^[0-9][0-9A-Za-z.+-]*$ ]] || die "unexpected Frida version: $frida_version"

	if [[ -z "$server_dir" ]]; then
		server_dir="$(dirname "$frida_bin")/$DEFAULT_SERVER_DIR_NAME"
	fi
	mkdir -p -- "$server_dir"
	server_dir=$(cd "$server_dir" && pwd -P)

	tmp_dir=$(mktemp -d "${TMPDIR:-/tmp}/frida-init.XXXXXXXXXX")

	section "Preparing Android server binaries"
	info "Frida ${frida_version} installed at $frida_bin"
	info "Saving servers to $server_dir"
	for architecture in arm arm64 x86 x86_64; do
		destination="$server_dir/frida-server-${frida_version}-android-${architecture}"
		download_server "$frida_version" "$architecture" "$destination"
	done

	success "Frida Android servers are ready"
}

trap cleanup EXIT
main "$@"
