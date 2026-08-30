#!/usr/bin/env bash
set -Eeuo pipefail

readonly SCRIPT_NAME=${0##*/}
readonly INSTALL_MARKER='install-yakit.sh'
readonly DESKTOP_FILE_NAME='yakit.desktop'
readonly LAUNCHER_FILE_NAME='yakit-launcher'
readonly DEFAULT_OSS_DOMAIN='oss-qn.yaklang.com'
readonly OSS_DOMAINS=(
	'oss-qn.yaklang.com'
	'aliyun-oss.yaklang.com'
	'yaklang.oss-cn-beijing.aliyuncs.com'
	'yaklang.oss-accelerate.aliyuncs.com'
)
readonly STYLE_RESET=$'\033[0m'
readonly STYLE_SUB_TITLE=$'\033[1;32m'
readonly STYLE_CONTENT=$'\033[1;37m'
readonly STYLE_SUCCESS=$'\033[1;36m'
readonly STYLE_WARNING=$'\033[1;33m'
readonly STYLE_ERROR=$'\033[1;31m'

install_dir=''
appimage_source=''
requested_version=${YAKIT_VERSION:-latest}
force=false
uninstall=false
version_option_seen=false
tmp_parent_dir=${TMPDIR:-/tmp}
tmp_dir=''
appimage_arch=''
oss_domain=''
resolved_version=''
appimage_url=''

usage() {
	printf 'Usage:\n' >&2
	printf '  %s --path <installation-directory> [--version <version>] [--appimage <file>] [--force]\n' "$SCRIPT_NAME" >&2
	printf '  %s --uninstall --path <installation-directory>\n' "$SCRIPT_NAME" >&2
	printf '\nInstall or remove Yakit from a user-selected directory.\n' >&2
	printf '\nOptions:\n' >&2
	printf '  --path <directory>   Installation directory (required).\n' >&2
	printf '  --version <version>  Release version (default: latest).\n' >&2
	printf '  --appimage <file>    Use a local AppImage instead of downloading one.\n' >&2
	printf '  --force              Replace an existing installation and desktop link.\n' >&2
	printf '  --uninstall          Remove Yakit installed at --path.\n' >&2
	printf '  --help               Show this help message.\n' >&2
	printf '\nEnvironment:\n' >&2
	printf '  YAKIT_VERSION        Default value for --version.\n' >&2
	printf '  YAKIT_OSS_DOMAIN     Try this OSS host before the built-in mirrors.\n' >&2
	printf '  YAKIT_HOME           Runtime data directory for the generated launcher.\n' >&2
}

color_text() {
	local style=$1
	local message=$2

	if [[ -n "${NO_COLOR:-}" || ! -t 1 ]]; then
		printf '%s' "$message"
		return 0
	fi

	printf '%s%s%s' "$style" "$message" "$STYLE_RESET"
}

print_styled_line() {
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
	if [[ -n "${tmp_dir:-}" && -d "$tmp_dir" ]]; then
		case "$tmp_dir" in
		"$tmp_parent_dir"/yakit-install.*)
			rm -rf -- "$tmp_dir"
			;;
		esac
	fi
}

normalize_absolute_path() {
	local path=$1
	local component
	local normalized='/'
	local -a components=()
	local -a path_components=()

	IFS='/' read -r -a path_components <<<"$path"
	for component in "${path_components[@]}"; do
		case "$component" in
		'' | .) ;;
		..)
			if [[ ${#components[@]} -gt 0 ]]; then
				components=("${components[@]:0:${#components[@]}-1}")
			fi
			;;
		*)
			components+=("$component")
			;;
		esac
	done

	for component in "${components[@]}"; do
		normalized+="$component/"
	done
	[[ "$normalized" == '/' ]] || normalized=${normalized%/}
	printf '%s\n' "$normalized"
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
		--version)
			[[ $# -ge 2 ]] || die '--version requires a value'
			[[ "$version_option_seen" == false ]] || die '--version may only be specified once'
			requested_version=$2
			version_option_seen=true
			shift 2
			;;
		--appimage)
			[[ $# -ge 2 ]] || die '--appimage requires a file'
			[[ -z "$appimage_source" ]] || die '--appimage may only be specified once'
			appimage_source=$2
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
		--)
			shift
			[[ $# -eq 0 ]] || die "unexpected argument: $1"
			;;
		-*)
			die "unknown argument: $1"
			;;
		*)
			die "unexpected argument: $1"
			;;
		esac
	done

	[[ -n "$install_dir" ]] || die 'an installation directory is required; pass --path <directory>'
	[[ "$uninstall" == false || "$force" == false ]] || die '--force cannot be used with --uninstall'
	[[ "$uninstall" == false || -z "$appimage_source" ]] || die '--appimage cannot be used with --uninstall'
	[[ "$uninstall" == false || "$version_option_seen" == false ]] || die '--version cannot be used with --uninstall'
}

resolve_paths() {
	local home_dir current_dir

	[[ -n "${HOME:-}" ]] || die 'HOME is not set'
	[[ "$install_dir" != *$'\n'* && "$install_dir" != *$'\r'* ]] || die 'the installation directory cannot contain a newline'
	if [[ "$install_dir" != /* ]]; then
		install_dir="$PWD/$install_dir"
	fi
	install_dir=$(normalize_absolute_path "$install_dir")

	home_dir=$(normalize_absolute_path "$HOME")
	current_dir=$(normalize_absolute_path "$PWD")
	[[ "$install_dir" != '/' && "$install_dir" != "$home_dir" && "$install_dir" != "$current_dir" && "$install_dir" != "$tmp_parent_dir" ]] || die 'refusing to use the filesystem root, home, current directory, or temporary directory as the installation directory'
	case "$home_dir" in
	"$install_dir"/*) die 'refusing to use an ancestor of the home directory as the installation directory' ;;
	esac
	case "$current_dir" in
	"$install_dir"/*) die 'refusing to use an ancestor of the current directory as the installation directory' ;;
	esac
	case "$tmp_parent_dir" in
	"$install_dir"/*) die 'refusing to use an ancestor of the temporary directory as the installation directory' ;;
	esac

	if [[ -n "$appimage_source" && "$appimage_source" != /* ]]; then
		appimage_source="$PWD/$appimage_source"
	fi
}

resolve_tmp_parent() {
	[[ "$tmp_parent_dir" != *$'\n'* && "$tmp_parent_dir" != *$'\r'* ]] || die 'TMPDIR cannot contain a newline'
	if [[ "$tmp_parent_dir" != /* ]]; then
		tmp_parent_dir="$PWD/$tmp_parent_dir"
	fi
	tmp_parent_dir=$(normalize_absolute_path "$tmp_parent_dir")
	[[ "$tmp_parent_dir" != '/' ]] || die 'refusing to use the filesystem root as the temporary directory parent'
}

assert_replaceable() {
	local path=$1

	if [[ -e "$path" || -L "$path" ]]; then
		[[ "$force" == true ]] || die "path already exists: $path (pass --force to replace it)"
		[[ ! -d "$path" || -L "$path" ]] || die "refusing to replace a directory used as an integration path: $path"
	fi
}

assert_install_dir_replaceable() {
	if [[ -e "$install_dir" || -L "$install_dir" ]]; then
		[[ "$force" == true ]] || die "path already exists: $install_dir (pass --force to replace it)"
		[[ ! -L "$install_dir" ]] || die "refusing to replace a symbolic-link installation directory: $install_dir"
		[[ -d "$install_dir" ]] || die "refusing to replace a non-directory installation path: $install_dir"
	fi
}

detect_architecture() {
	case "$(uname -m)" in
	x86_64 | amd64)
		appimage_arch='amd64'
		;;
	aarch64 | arm64)
		appimage_arch='arm64'
		;;
	*)
		die "unsupported architecture: $(uname -m)"
		;;
	esac
}

validate_oss_domain() {
	[[ "$1" =~ ^[A-Za-z0-9.-]+$ ]] || die "invalid OSS domain: $1"
}

validate_version() {
	[[ "$1" =~ ^[0-9][0-9A-Za-z._-]*$ ]] || die "invalid Yakit version: $1"
}

fetch_latest_version() {
	local domain version_data
	local -a candidate_domains=()

	if [[ -n "${YAKIT_OSS_DOMAIN:-}" ]]; then
		validate_oss_domain "$YAKIT_OSS_DOMAIN"
		candidate_domains+=("$YAKIT_OSS_DOMAIN")
	fi
	candidate_domains+=("${OSS_DOMAINS[@]}")

	for domain in "${candidate_domains[@]}"; do
		version_data=''
		if version_data=$(curl --fail --location --silent --show-error --max-time 30 "https://${domain}/yak/latest/yakit-version.txt"); then
			version_data=$(printf '%s' "$version_data" | tr -d '[:space:]')
			if [[ "$version_data" =~ ^[0-9][0-9A-Za-z._-]*$ ]]; then
				oss_domain=$domain
				resolved_version=$version_data
				return 0
			fi
			warn "invalid version data from ${domain}"
		fi
	done

	die 'could not fetch a valid latest Yakit version from the official OSS mirrors'
}

resolve_download_url() {
	if [[ "$requested_version" == 'latest' ]]; then
		fetch_latest_version
	else
		validate_version "$requested_version"
		resolved_version=$requested_version
		oss_domain=${YAKIT_OSS_DOMAIN:-$DEFAULT_OSS_DOMAIN}
		validate_oss_domain "$oss_domain"
	fi

	appimage_url="https://${oss_domain}/yak/${resolved_version}/Yakit-${resolved_version}-linux-${appimage_arch}.AppImage"
}

prepare_tmp_dir() {
	mkdir -p -- "$tmp_parent_dir"
	tmp_dir=$(mktemp -d "$tmp_parent_dir/yakit-install.XXXXXXXX")
	trap cleanup EXIT
}

download_appimage() {
	local destination=$1

	if [[ -n "$appimage_source" ]]; then
		[[ -f "$appimage_source" ]] || die "AppImage not found: $appimage_source"
		cp -- "$appimage_source" "$destination"
		return 0
	fi

	resolve_download_url
	print_styled_line "$STYLE_SUB_TITLE" "Downloading Yakit ${resolved_version} (${appimage_arch})"
	printf '%s\n' "  URL: $appimage_url"
	curl --fail --location --retry 3 --output "$destination" "$appimage_url"
}

escape_desktop_exec_arg() {
	local value=$1

	value=${value//\\/\\\\}
	value=${value//"/\\"/}
	value=${value//\`/\\\`}
	value=${value//\$/\\\$}
	value=${value//%/%%}
	printf '"%s"' "$value"
}

write_launcher() {
	local target_file=$1
	local temporary_file="$tmp_dir/$LAUNCHER_FILE_NAME"

	# shellcheck disable=SC2016  # Preserve runtime variable expansion in the generated launcher.
	{
		printf '%s\n' '#!/usr/bin/env bash'
		printf '%s\n' 'set -Eeuo pipefail'
		printf '\n'
		printf '%s\n' 'launcher_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)'
		printf '%s\n' 'if [[ -n "${YAKIT_HOME:-}" ]]; then'
		printf '%s\n' 'data_dir=$YAKIT_HOME'
		printf '%s\n' 'elif [[ "${XDG_DATA_HOME:-}" == /* ]]; then'
		printf '%s\n' 'data_dir=$XDG_DATA_HOME/yakit'
		printf '%s\n' 'else'
		printf '%s\n' '[[ -n "${HOME:-}" ]] || { printf '\''Error: HOME is not set\n'\'' >&2; exit 1; }'
		printf '%s\n' 'data_dir=$HOME/.local/share/yakit'
		printf '%s\n' 'fi'
		printf '%s\n' 'if [[ "$data_dir" != /* ]]; then'
		printf '%s\n' 'data_dir=$PWD/$data_dir'
		printf '%s\n' 'fi'
		printf '%s\n' 'mkdir -p -- "$data_dir"'
		printf '%s\n' 'cd -- "$data_dir"'
		printf '%s\n' 'export YAKIT_HOME="$data_dir"'
		printf '%s\n' 'exec "$launcher_dir/AppRun" "$@"'
	} >"$temporary_file"
	chmod +x -- "$temporary_file"
	mv -- "$temporary_file" "$target_file"
}

write_desktop_entry() {
	local source_file=$1
	local target_file=$2
	local executable=$3
	local icon=$4
	local temporary_file="$tmp_dir/yakit.desktop"
	local escaped_executable
	local line
	local has_exec=false
	local has_icon=false

	escaped_executable=$(escape_desktop_exec_arg "$executable")
	while IFS= read -r line || [[ -n "$line" ]]; do
		case "$line" in
		Exec=*)
			printf 'Exec=%s %%U\n' "$escaped_executable" >>"$temporary_file"
			has_exec=true
			;;
		Icon=*)
			printf 'Icon=%s\n' "$icon" >>"$temporary_file"
			has_icon=true
			;;
		Path=*) ;;
		X-Yakit-Installed-By=*) ;;
		*)
			printf '%s\n' "$line" >>"$temporary_file"
			;;
		esac
	done <"$source_file"

	[[ "$has_exec" == true ]] || printf 'Exec=%s %%U\n' "$escaped_executable" >>"$temporary_file"
	[[ "$has_icon" == true ]] || printf 'Icon=%s\n' "$icon" >>"$temporary_file"
	printf 'X-Yakit-Installed-By=%s\n' "$INSTALL_MARKER" >>"$temporary_file"
	mv -- "$temporary_file" "$target_file"
}

is_managed_link() {
	local link_path=$1
	local expected_target=$2

	[[ -L "$link_path" ]] && [[ "$(readlink -- "$link_path")" == "$expected_target" ]]
}

is_managed_desktop_entry() {
	local desktop_file=$1
	shift
	local executable
	local escaped_executable

	grep -Fqx "X-Yakit-Installed-By=$INSTALL_MARKER" "$desktop_file" || return 1
	for executable in "$@"; do
		escaped_executable=$(escape_desktop_exec_arg "$executable")
		if grep -Fqx "Exec=$escaped_executable %U" "$desktop_file"; then
			return 0
		fi
	done
	return 1
}

install_yakit() {
	local desktop_dir="$HOME/.local/share/applications"
	local desktop_link="$desktop_dir/$DESKTOP_FILE_NAME"
	local appimage_path
	local staging_dir
	local source_desktop
	local icon_relative_path
	local install_parent

	assert_install_dir_replaceable
	assert_replaceable "$desktop_link"
	install_parent=${install_dir%/*}
	[[ -n "$install_parent" ]] || install_parent='/'
	mkdir -p -- "$install_parent" "$desktop_dir"
	[[ -w "$install_parent" ]] || die "installation parent is not writable: $install_parent"
	[[ -w "$desktop_dir" ]] || die "desktop directory is not writable: $desktop_dir"
	prepare_tmp_dir
	appimage_path="$tmp_dir/yakit.AppImage"
	staging_dir="$tmp_dir/squashfs-root"
	download_appimage "$appimage_path"
	chmod +x -- "$appimage_path"
	(
		cd -- "$tmp_dir"
		"$appimage_path" --appimage-extract >/dev/null
	)

	[[ -d "$staging_dir" ]] || die 'the AppImage did not produce an extracted filesystem'
	[[ -x "$staging_dir/AppRun" ]] || die 'the AppImage does not contain an executable AppRun'
	[[ -x "$staging_dir/yakit" ]] || die 'the AppImage does not contain the Yakit executable'
	source_desktop="$staging_dir/$DESKTOP_FILE_NAME"
	[[ -f "$source_desktop" ]] || die "the AppImage does not contain $DESKTOP_FILE_NAME"

	if [[ -e "$staging_dir/yakit.png" || -L "$staging_dir/yakit.png" ]]; then
		icon_relative_path='yakit.png'
	elif [[ -f "$staging_dir/usr/share/icons/hicolor/512x512/apps/yakit.png" ]]; then
		icon_relative_path='usr/share/icons/hicolor/512x512/apps/yakit.png'
	else
		die 'the AppImage does not contain a Yakit icon'
	fi

	write_launcher "$staging_dir/$LAUNCHER_FILE_NAME"
	write_desktop_entry "$source_desktop" "$staging_dir/$DESKTOP_FILE_NAME" "$install_dir/$LAUNCHER_FILE_NAME" "$install_dir/$icon_relative_path"

	if [[ -e "$install_dir" || -L "$install_dir" ]]; then
		rm -rf -- "$install_dir"
	fi
	mv -- "$staging_dir" "$install_dir"

	if [[ -e "$desktop_link" || -L "$desktop_link" ]]; then
		rm -- "$desktop_link"
	fi
	ln -s -- "$install_dir/$DESKTOP_FILE_NAME" "$desktop_link"

	printf '\n'
	print_styled_line "$STYLE_SUCCESS" 'Yakit installation complete'
	print_styled_line "$STYLE_SUB_TITLE" 'Installed locations'
	print_styled_line "$STYLE_CONTENT" "  Yakit directory: $install_dir"
	print_styled_line "$STYLE_CONTENT" "  Desktop entry:  $desktop_link"
}

uninstall_yakit() {
	local desktop_dir="$HOME/.local/share/applications"
	local desktop_link="$desktop_dir/$DESKTOP_FILE_NAME"
	local desktop_file="$install_dir/$DESKTOP_FILE_NAME"
	local desktop_entry_removed=false

	[[ -d "$install_dir" && ! -L "$install_dir" ]] || die "Yakit installation directory not found: $install_dir"
	[[ -x "$install_dir/AppRun" ]] || die "Yakit AppRun not found: $install_dir/AppRun"

	if [[ -L "$desktop_link" ]]; then
		if is_managed_link "$desktop_link" "$desktop_file"; then
			rm -- "$desktop_link"
			desktop_entry_removed=true
		else
			warn "leaving desktop link unchanged: $desktop_link"
		fi
	elif [[ -f "$desktop_link" ]] && is_managed_desktop_entry "$desktop_link" "$install_dir/$LAUNCHER_FILE_NAME" "$install_dir/AppRun"; then
		rm -- "$desktop_link"
		desktop_entry_removed=true
	fi

	rm -rf -- "$install_dir"
	printf '\n'
	print_styled_line "$STYLE_SUCCESS" 'Yakit uninstalled'
	print_styled_line "$STYLE_SUB_TITLE" 'Removed locations'
	print_styled_line "$STYLE_CONTENT" "  Yakit directory: $install_dir"
	if [[ "$desktop_entry_removed" == true ]]; then
		print_styled_line "$STYLE_CONTENT" "  Desktop entry:  $desktop_link"
	fi
}

main() {
	parse_arguments "$@"
	resolve_tmp_parent
	resolve_paths
	require_command uname
	[[ "$(uname -s)" == 'Linux' ]] || die 'this installer supports Linux only'
	require_command grep
	require_command ln
	require_command mkdir
	require_command readlink
	require_command rm

	if [[ "$uninstall" == true ]]; then
		uninstall_yakit
		return 0
	fi

	require_command chmod
	require_command cp
	if [[ -z "$appimage_source" ]]; then
		require_command curl
	fi
	require_command mktemp
	require_command mv
	require_command tr
	detect_architecture
	install_yakit
}

main "$@"
