#!/usr/bin/env bash
set -Eeuo pipefail

readonly SCRIPT_NAME=${0##*/}
readonly DEFAULT_INSTALL_DIR="$HOME/.local/bin/snipaste"
readonly APPIMAGE_URL='https://dl.snipaste.com/linux'
readonly GITHUB_CONTENT_BASE='https://raw.githubusercontent.com/sparkuru/genshin/main/tsuki/22-snipaste'

install_dir=$DEFAULT_INSTALL_DIR
force=false
tmp_dir=''

usage() {
	printf 'Usage: %s [--path <installation-directory>] [--force]\n' "$SCRIPT_NAME" >&2
	printf '\nDownload and install the latest Snipaste Linux AppImage.\n' >&2
	printf '\nOptions:\n' >&2
	printf '  --path <directory>   Installation directory (default: %s).\n' "$DEFAULT_INSTALL_DIR" >&2
	printf '  --force              Replace an existing installation and desktop-entry link.\n' >&2
	printf '  --help               Show this help message.\n' >&2
}

die() {
	printf 'Error: %s\n' "$*" >&2
	exit 1
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
			install_dir=$2
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
			die "unknown argument: $1"
			;;
		esac
	done
}

resolve_install_dir() {
	if [[ "$install_dir" != /* ]]; then
		install_dir=$PWD/$install_dir
	fi

	install_dir=${install_dir%/}
	[[ -n "$install_dir" && "$install_dir" != '/' && "$install_dir" != "$HOME" ]] || die 'refusing to use the filesystem root or home directory as the installation directory'
}

assert_replaceable() {
	local path=$1

	if [[ -e "$path" || -L "$path" ]]; then
		[[ "$force" == true ]] || die "path already exists: $path (pass --force to replace it)"
	fi
}

download_file() {
	local url=$1
	local output_path=$2

	curl --fail --location --retry 3 --output "$output_path" "$url"
}

configure_desktop_entry() {
	local desktop_file=$1
	local temporary_file

	temporary_file="$tmp_dir/Snipaste.desktop"
	awk -v executable="$install_dir/usr/bin/Snipaste" -v icon="$install_dir/Snipaste" '
		/^Exec=/ {
			print "Exec=" executable
			has_exec = 1
			next
		}
		/^Icon=/ {
			print "Icon=" icon
			has_icon = 1
			next
		}
		{ print }
		END {
			if (!has_exec || !has_icon) {
				exit 1
			}
		}
	' "$desktop_file" >"$temporary_file" || die 'failed to configure the Snipaste desktop entry'
	mv -- "$temporary_file" "$desktop_file"
}

install_snipaste() {
	local appimage_path staging_dir desktop_dir desktop_link install_parent

	desktop_dir="$HOME/.local/share/applications"
	desktop_link="$desktop_dir/Snipaste.desktop"
	assert_replaceable "$install_dir"
	assert_replaceable "$desktop_link"

	tmp_dir=$(mktemp -d "${TMPDIR:-/tmp}/snipaste-install.XXXXXXXX")
	trap cleanup EXIT
	appimage_path="$tmp_dir/Snipaste.AppImage"
	download_file "$APPIMAGE_URL" "$appimage_path"
	chmod +x -- "$appimage_path"
	(
		cd -- "$tmp_dir"
		"$appimage_path" --appimage-extract >/dev/null
	)

	staging_dir="$tmp_dir/squashfs-root"
	[[ -x "$staging_dir/usr/bin/Snipaste" ]] || die 'the AppImage does not contain the Snipaste executable'
	[[ -e "$staging_dir/Snipaste" ]] || die 'the AppImage does not contain the Snipaste icon'
	download_file "$GITHUB_CONTENT_BASE/ocr.sh" "$staging_dir/ocr.sh"
	download_file "$GITHUB_CONTENT_BASE/Snipaste.desktop" "$staging_dir/Snipaste.desktop"
	chmod +x -- "$staging_dir/ocr.sh"
	configure_desktop_entry "$staging_dir/Snipaste.desktop"

	install_parent=${install_dir%/*}
	[[ -n "$install_parent" ]] || install_parent='/'
	mkdir -p -- "$install_parent" "$desktop_dir"
	if [[ -e "$install_dir" || -L "$install_dir" ]]; then
		[[ ! -L "$install_dir" ]] || die "refusing to replace a symbolic-link installation directory: $install_dir"
		rm -rf -- "$install_dir"
	fi
	mv -- "$staging_dir" "$install_dir"

	if [[ -e "$desktop_link" || -L "$desktop_link" ]]; then
		rm -- "$desktop_link"
	fi
	ln -s -- "$install_dir/Snipaste.desktop" "$desktop_link"

	printf 'Snipaste installation complete\n'
	printf '  Installation directory: %s\n' "$install_dir"
	printf '  Desktop entry: %s\n' "$desktop_link"
}

main() {
	parse_arguments "$@"
	resolve_install_dir
	[[ "$(uname -s)" == 'Linux' ]] || die 'this installer supports Linux only'

	for command_name in awk chmod curl ln mkdir mktemp mv rm uname; do
		require_command "$command_name"
	done

	install_snipaste
}

main "$@"
