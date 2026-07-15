#!/usr/bin/env bash
set -Eeuo pipefail

readonly SCRIPT_NAME=${0##*/}
readonly STYLE_RESET=$'\033[0m'
readonly STYLE_SUB_TITLE=$'\033[1;32m'
readonly STYLE_CONTENT=$'\033[1;37m'
readonly STYLE_SUCCESS=$'\033[1;36m'
readonly STYLE_WARNING=$'\033[1;33m'
readonly STYLE_ERROR=$'\033[1;31m'

archive_path=''
install_dir=''
force=false
uninstall=false
tmp_dir=''

usage() {
	printf 'Usage:\n' >&2
	printf '  %s --archive <archive.tar.gz> --path <installation-directory> [--force]\n' "$SCRIPT_NAME" >&2
	printf '  %s --uninstall --path <installation-directory>\n' "$SCRIPT_NAME" >&2
	printf '\nInstall or remove VSCodium plus its command link and desktop entry.\n' >&2
	printf '\nOptions:\n' >&2
	printf '  --archive <file>     VSCodium Linux tar.gz archive (required for installation).\n' >&2
	printf '  --path <directory>   Installation directory (required).\n' >&2
	printf '  --force              Replace an existing installation and managed integration files.\n' >&2
	printf '  --uninstall          Remove VSCodium installed at --path.\n' >&2
	printf '  --help               Show this help message.\n' >&2
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

print_line() {
	color_text "$1" "$2"
	printf '\n'
}

die() {
	if [[ -n "${NO_COLOR:-}" || ! -t 2 ]]; then
		printf 'Error: %s\n' "$*" >&2
	else
		printf '%sError: %s%s\n' "$STYLE_ERROR" "$*" "$STYLE_RESET" >&2
	fi
	exit 1
}

warn() {
	if [[ -n "${NO_COLOR:-}" || ! -t 2 ]]; then
		printf 'Warning: %s\n' "$*" >&2
	else
		printf '%sWarning: %s%s\n' "$STYLE_WARNING" "$*" "$STYLE_RESET" >&2
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
		--archive)
			[[ $# -ge 2 ]] || die '--archive requires a file'
			[[ -z "$archive_path" ]] || die '--archive may only be specified once'
			archive_path=$2
			shift 2
			;;
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
	[[ "$uninstall" == true || -n "$archive_path" ]] || die 'an archive is required; pass --archive <archive.tar.gz>'
}

resolve_paths() {
	if [[ "$install_dir" != /* ]]; then
		install_dir=$PWD/$install_dir
	fi
	install_dir=${install_dir%/}
	[[ -n "$install_dir" && "$install_dir" != '.' && "$install_dir" != '/' ]] || die 'refusing to use the filesystem root as the installation directory'

	if [[ -n "$archive_path" && "$archive_path" != /* ]]; then
		archive_path=$PWD/$archive_path
	fi
}

assert_replaceable() {
	local path=$1

	if [[ -e "$path" || -L "$path" ]]; then
		[[ "$force" == true ]] || die "path already exists: $path (pass --force to replace it)"
	fi
}

is_managed_link() {
	local bin_link=$1
	local executable=$2

	[[ -L "$bin_link" ]] && [[ "$(readlink -- "$bin_link")" == "$executable" ]]
}

is_managed_desktop_entry() {
	local desktop_file=$1
	local executable=$2

	grep -Fqx 'Name=VSCodium' "$desktop_file" && grep -Fqx "Exec=$executable %F" "$desktop_file"
}

write_desktop_entry() {
	local desktop_file=$1
	local executable=$2
	local icon=$3

	cat >"$desktop_file" <<EOF
[Desktop Entry]
Name=VSCodium
Comment=Code editing. Redefined.
GenericName=Text Editor
Exec=$executable %F
Icon=$icon
Type=Application
Terminal=false
Categories=Utility;TextEditor;Development;IDE;
MimeType=text/plain;inode/directory;
StartupWMClass=VSCodium
X-VSCodium-Installed-By=install-vscodium.sh
EOF
}

uninstall_vscodium() {
	local bin_link=$1
	local desktop_file=$2
	local cli_executable desktop_executable command_link_removed desktop_entry_removed

	[[ -d "$install_dir" && ! -L "$install_dir" ]] || die "VSCodium installation directory not found: $install_dir"
	cli_executable="$install_dir/bin/codium"
	desktop_executable="$install_dir/codium"
	[[ -x "$cli_executable" ]] || die "VSCodium CLI executable not found in: $install_dir"
	[[ -x "$desktop_executable" ]] || die "VSCodium desktop executable not found in: $install_dir"
	command_link_removed=false
	desktop_entry_removed=false

	if [[ -e "$bin_link" || -L "$bin_link" ]]; then
		if is_managed_link "$bin_link" "$cli_executable"; then
			rm -- "$bin_link"
			command_link_removed=true
		else
			warn "leaving command link unchanged: $bin_link"
		fi
	fi

	if [[ -e "$desktop_file" || -L "$desktop_file" ]]; then
		if [[ -f "$desktop_file" ]] && is_managed_desktop_entry "$desktop_file" "$desktop_executable"; then
			rm -- "$desktop_file"
			desktop_entry_removed=true
		else
			warn "leaving desktop entry unchanged: $desktop_file"
		fi
	fi

	rm -rf -- "$install_dir"
	print_line "$STYLE_SUCCESS" 'VSCodium uninstalled'
	print_line "$STYLE_CONTENT" "  VSCodium directory: $install_dir"
	[[ "$command_link_removed" == true ]] && print_line "$STYLE_CONTENT" "  Command link: $bin_link"
	[[ "$desktop_entry_removed" == true ]] && print_line "$STYLE_CONTENT" "  Desktop entry: $desktop_file"
}

install_vscodium() {
	local bin_dir=$1
	local bin_link=$2
	local desktop_dir=$3
	local desktop_file=$4
	local staging_dir icon

	[[ -f "$archive_path" ]] || die "archive not found: $archive_path"
	assert_replaceable "$install_dir"
	assert_replaceable "$bin_link"
	assert_replaceable "$desktop_file"

	mkdir -p -- "$(dirname -- "$install_dir")"
	tmp_dir=$(mktemp -d "$(dirname -- "$install_dir")/.vscodium-install.XXXXXXXX")
	trap cleanup EXIT
	staging_dir="$tmp_dir/app"
	mkdir -- "$staging_dir"
	tar -xzf "$archive_path" -C "$staging_dir"
	[[ -x "$staging_dir/codium" ]] || die 'the archive does not contain the VSCodium desktop executable'
	[[ -x "$staging_dir/bin/codium" ]] || die 'the archive does not contain the VSCodium CLI executable'

	if [[ -e "$install_dir" || -L "$install_dir" ]]; then
		rm -rf -- "$install_dir"
	fi
	mv -- "$staging_dir" "$install_dir"

	mkdir -p -- "$bin_dir" "$desktop_dir"
	ln -sfnT -- "$install_dir/bin/codium" "$bin_link"
	icon="$install_dir/resources/app/resources/linux/code.png"
	[[ -f "$icon" ]] || icon='vscodium'
	write_desktop_entry "$desktop_file" "$install_dir/codium" "$icon"

	print_line "$STYLE_SUCCESS" 'VSCodium installation complete'
	print_line "$STYLE_SUB_TITLE" 'Installed locations'
	print_line "$STYLE_CONTENT" "  VSCodium directory: $install_dir"
	print_line "$STYLE_CONTENT" "  Command link: $bin_link"
	print_line "$STYLE_CONTENT" "  Desktop entry: $desktop_file"
}

main() {
	local bin_dir bin_link desktop_dir desktop_file

	parse_arguments "$@"
	resolve_paths
	[[ "$(uname -s)" == 'Linux' ]] || die 'this installer supports Linux only'
	require_command mkdir
	require_command tar
	require_command mktemp
	require_command mv
	require_command ln
	require_command rm
	require_command readlink
	require_command grep
	require_command cat
	require_command dirname

	bin_dir="$HOME/.local/bin"
	bin_link="$bin_dir/codium"
	desktop_dir="$HOME/.local/share/applications"
	desktop_file="$desktop_dir/com.vscodium.codium.desktop"

	if [[ "$uninstall" == true ]]; then
		uninstall_vscodium "$bin_link" "$desktop_file"
	else
		install_vscodium "$bin_dir" "$bin_link" "$desktop_dir" "$desktop_file"
	fi
}

main "$@"
