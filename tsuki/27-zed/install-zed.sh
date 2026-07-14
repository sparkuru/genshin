#!/usr/bin/env bash
set -Eeuo pipefail

readonly SCRIPT_NAME=${0##*/}
readonly ZED_CHANNEL=${ZED_CHANNEL:-stable}
readonly ZED_VERSION=${ZED_VERSION:-latest}
readonly STYLE_RESET=$'\033[0m'
readonly STYLE_SUB_TITLE=$'\033[1;32m'
readonly STYLE_CONTENT=$'\033[1;37m'
readonly STYLE_EXAMPLE=$'\033[0;37m'
readonly STYLE_SUCCESS=$'\033[1;36m'
readonly STYLE_WARNING=$'\033[1;33m'
readonly STYLE_ERROR=$'\033[1;31m'

install_dir=''
force=false
uninstall=false
tmp_dir=''

usage() {
	printf 'Usage:\n' >&2
	printf '  %s --path <installation-directory> [--force]\n' "$SCRIPT_NAME" >&2
	printf '  %s --uninstall --path <installation-directory>\n' "$SCRIPT_NAME" >&2
	printf '\nInstall or remove Zed plus its command link and desktop entry.\n' >&2
	printf '\nOptions:\n' >&2
	printf '  --path <directory>  Installation directory (required).\n' >&2
	printf '  --force             Replace existing installation and integration files.\n' >&2
	printf '  --uninstall         Remove Zed installed at --path.\n' >&2
	printf '  --help              Show this help message.\n' >&2
}

color_text() {
	local style=$1
	local text=$2

	if [[ -n "${NO_COLOR:-}" || ! -t 1 ]]; then
		printf '%s' "$text"
		return
	fi

	printf '%s%s%s' "$style" "$text" "$STYLE_RESET"
}

print_styled_line() {
	color_text "$1" "$2"
	printf '\n'
}

die() {
	if [[ -n "${NO_COLOR:-}" || ! -t 2 ]]; then
		printf 'Error: %s\n' "$*" >&2
		exit 1
	fi

	printf '%sError: %s%s\n' "$STYLE_ERROR" "$*" "$STYLE_RESET" >&2
	exit 1
}

warn() {
	if [[ -n "${NO_COLOR:-}" || ! -t 2 ]]; then
		printf 'Warning: %s\n' "$*" >&2
		return
	fi

	printf '%sWarning: %s%s\n' "$STYLE_WARNING" "$*" "$STYLE_RESET" >&2
}

print_installation_summary() {
	local install_dir=$1
	local bin_dir=$2
	local bin_link=$3
	local desktop_dir=$4
	local desktop_file=$5

	printf '\n'
	print_styled_line "$STYLE_SUCCESS" 'Zed installation complete'
	print_styled_line "$STYLE_SUB_TITLE" 'Installed locations'
	color_text "$STYLE_CONTENT" '  Zed directory:         '
	printf '%s\n' "$install_dir"
	color_text "$STYLE_CONTENT" '  Command directory:     '
	printf '%s\n' "$bin_dir"
	color_text "$STYLE_CONTENT" '  Command link:          '
	printf '%s\n' "$bin_link"
	color_text "$STYLE_CONTENT" '  Desktop directory:     '
	printf '%s\n' "$desktop_dir"
	color_text "$STYLE_CONTENT" '  Desktop entry:         '
	printf '%s\n' "$desktop_file"
	printf '\n'
	print_styled_line "$STYLE_SUB_TITLE" 'Launch Zed'
	color_text "$STYLE_EXAMPLE" '  zed'
	printf '\n'
}

print_uninstallation_summary() {
	local install_dir=$1
	local bin_link=$2
	local desktop_file=$3
	local command_link_removed=$4
	local desktop_entry_removed=$5

	printf '\n'
	print_styled_line "$STYLE_SUCCESS" 'Zed uninstalled'
	print_styled_line "$STYLE_SUB_TITLE" 'Removed locations'
	color_text "$STYLE_CONTENT" '  Zed directory:         '
	printf '%s\n' "$install_dir"
	if [[ "$command_link_removed" == true ]]; then
		color_text "$STYLE_CONTENT" '  Command link:          '
		printf '%s\n' "$bin_link"
	fi
	if [[ "$desktop_entry_removed" == true ]]; then
		color_text "$STYLE_CONTENT" '  Desktop entry:         '
		printf '%s\n' "$desktop_file"
	fi
}

require_command() {
	command -v "$1" >/dev/null 2>&1 || die "required command not found: $1"
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
	[[ -n "$install_dir" && "$install_dir" != '.' ]] || die 'refusing to use the filesystem root as the installation directory'
	[[ "$install_dir" != '/' ]] || die 'refusing to use the filesystem root as the installation directory'
}

detect_architecture() {
	case "$(uname -m)" in
	aarch64 | arm64 | armv8l)
		printf '%s\n' 'aarch64'
		;;
	x86_64 | amd64 | i686 | i386)
		printf '%s\n' 'x86_64'
		;;
	*)
		die "unsupported architecture: $(uname -m)"
		;;
	esac
}

download_bundle() {
	local bundle_path=$1
	local arch=$2
	local url="https://cloud.zed.dev/releases/${ZED_CHANNEL}/${ZED_VERSION}/download?asset=zed&arch=${arch}&os=linux&source=install.sh"

	if [[ -n "${ZED_BUNDLE_PATH:-}" ]]; then
		[[ -f "$ZED_BUNDLE_PATH" ]] || die "bundle not found: $ZED_BUNDLE_PATH"
		cp -- "$ZED_BUNDLE_PATH" "$bundle_path"
		return
	fi

	if command -v curl >/dev/null 2>&1; then
		curl --fail --location --retry 3 --output "$bundle_path" "$url"
		return
	fi

	if command -v wget >/dev/null 2>&1; then
		wget --output-document="$bundle_path" "$url"
		return
	fi

	die "could not find 'curl' or 'wget' in PATH"
}

assert_replaceable() {
	local path=$1

	if [[ -e "$path" || -L "$path" ]]; then
		[[ "$force" == true ]] || die "path already exists: $path (pass --force to replace it)"
	fi
}

write_desktop_entry() {
	local desktop_file=$1
	local executable=$2
	local icon=$3

	cat >"$desktop_file" <<EOF
[Desktop Entry]
Name=Zed
Comment=A high-performance, multiplayer code editor
GenericName=Text Editor
Exec="$executable" %U
Icon=$icon
Type=Application
Terminal=false
Categories=Development;IDE;TextEditor;
MimeType=text/plain;
StartupWMClass=Zed
X-Zed-Installed-By=install-zed.sh
EOF
}

is_managed_link() {
	local bin_link=$1
	local executable=$2

	[[ -L "$bin_link" ]] && [[ "$(readlink -- "$bin_link")" == "$executable" ]]
}

is_managed_desktop_entry() {
	local desktop_file=$1
	local bin_link=$2

	grep -Fqx 'Name=Zed' "$desktop_file" && grep -Fqx "Exec=\"$bin_link\" %U" "$desktop_file"
}

uninstall_zed() {
	local bin_link=$1
	local desktop_file=$2
	local executable command_link_removed desktop_entry_removed

	[[ -d "$install_dir" && ! -L "$install_dir" ]] || die "Zed installation directory not found: $install_dir"
	executable="$install_dir/bin/zed"
	[[ -x "$executable" ]] || executable="$install_dir/bin/cli"
	[[ -x "$executable" ]] || die "Zed executable not found in: $install_dir"
	command_link_removed=false
	desktop_entry_removed=false

	if [[ -e "$bin_link" || -L "$bin_link" ]]; then
		if is_managed_link "$bin_link" "$executable"; then
			rm -- "$bin_link"
			command_link_removed=true
		else
			warn "leaving command link unchanged: $bin_link"
		fi
	fi

	if [[ -e "$desktop_file" || -L "$desktop_file" ]]; then
		if [[ -f "$desktop_file" ]] && is_managed_desktop_entry "$desktop_file" "$bin_link"; then
			rm -- "$desktop_file"
			desktop_entry_removed=true
		else
			warn "leaving desktop entry unchanged: $desktop_file"
		fi
	fi

	rm -rf -- "$install_dir"
	print_uninstallation_summary "$install_dir" "$bin_link" "$desktop_file" "$command_link_removed" "$desktop_entry_removed"
}

main() {
	local arch bundle_path staging_dir bin_dir bin_link desktop_dir desktop_file executable icon

	parse_arguments "$@"
	resolve_install_dir

	[[ "$(uname -s)" == 'Linux' ]] || die 'this installer supports Linux only'
	bin_dir="$HOME/.local/bin"
	bin_link="$bin_dir/zed"
	desktop_dir="$HOME/.local/share/applications"
	desktop_file="$desktop_dir/dev.zed.Zed.desktop"

	if [[ "$uninstall" == true ]]; then
		require_command rm
		require_command readlink
		require_command grep
		uninstall_zed "$bin_link" "$desktop_file"
		return
	fi

	require_command tar
	require_command mktemp
	require_command mkdir
	require_command mv
	require_command ln
	require_command rm
	require_command cp
	require_command cat
	require_command dirname

	assert_replaceable "$install_dir"
	assert_replaceable "$bin_link"
	assert_replaceable "$desktop_file"

	mkdir -p -- "$(dirname -- "$install_dir")"
	tmp_dir=$(mktemp -d "$(dirname -- "$install_dir")/.zed-install.XXXXXXXX")
	trap cleanup EXIT
	bundle_path="$tmp_dir/zed.tar.gz"
	staging_dir="$tmp_dir/app"

	arch=$(detect_architecture)
	print_styled_line "$STYLE_SUB_TITLE" "Downloading Zed version: $ZED_VERSION"
	download_bundle "$bundle_path" "$arch"
	mkdir -- "$staging_dir"
	tar -xzf "$bundle_path" --strip-components=1 -C "$staging_dir"

	executable="$staging_dir/bin/zed"
	[[ -x "$executable" ]] || executable="$staging_dir/bin/cli"
	[[ -x "$executable" ]] || die 'the downloaded archive does not contain a Zed executable'

	if [[ -e "$install_dir" || -L "$install_dir" ]]; then
		rm -rf -- "$install_dir"
	fi
	mv -- "$staging_dir" "$install_dir"

	executable="$install_dir/${executable#"$tmp_dir/app/"}"
	icon="$install_dir/share/icons/hicolor/512x512/apps/zed.png"
	[[ -f "$icon" ]] || icon='zed'

	mkdir -p -- "$bin_dir" "$desktop_dir"
	ln -sfnT -- "$executable" "$bin_link"
	write_desktop_entry "$desktop_file" "$bin_link" "$icon"

	print_installation_summary "$install_dir" "$bin_dir" "$bin_link" "$desktop_dir" "$desktop_file"
}

main "$@"
