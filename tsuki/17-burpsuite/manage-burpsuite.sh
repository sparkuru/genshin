#!/usr/bin/env bash
set -Eeuo pipefail

readonly SCRIPT_NAME=${0##*/}
readonly INSTALLER_URL='https://portswigger.net/burp/releases/download?product=community&type=Linux'
readonly DEFAULT_INSTALL_DIR="$HOME/cargo/bin/burpsuite"
readonly DESKTOP_DIR="$HOME/.local/share/applications"
readonly DESKTOP_FILE="$DESKTOP_DIR/burpsuite-community-edition.desktop"
readonly STYLE_RESET=$'\033[0m'
readonly STYLE_SUCCESS=$'\033[0;32m'
readonly STYLE_WARNING=$'\033[1;33m'
readonly STYLE_ERROR=$'\033[1;31m'

command_name=''
install_dir=$DEFAULT_INSTALL_DIR
force=false
tmp_dir=''

usage() {
	printf 'Usage:\n' >&2
	printf '  %s install [--path <installation-directory>] [--force]\n' "$SCRIPT_NAME" >&2
	printf '  %s no-update [--path <installation-directory>] [--force]\n' "$SCRIPT_NAME" >&2
	printf '  %s uninstall [--path <installation-directory>]\n' "$SCRIPT_NAME" >&2
	printf '  %s make-desktop [--path <installation-directory>] [--force]\n' "$SCRIPT_NAME" >&2
	printf '\nInstall Burp Suite Community, disable automatic updates, or uninstall it.\n' >&2
	printf '\nCommands:\n' >&2
	printf '  install       Download the official Community installer, install it, then apply no-update.\n' >&2
	printf '  no-update     Disable Burp automatic updates for this installation.\n' >&2
	printf '  uninstall     Run Burp\047s own unattended uninstaller; user data is preserved.\n' >&2
	printf '  make-desktop  Create or refresh the desktop shortcut.\n' >&2
	printf '\nOptions:\n' >&2
	printf '  --path <directory>  Installation directory (default: %s).\n' "$DEFAULT_INSTALL_DIR" >&2
	printf '  --force             Replace an existing installation or desktop shortcut.\n' >&2
	printf '  --help, -h          Show this help message.\n' >&2
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

cleanup() {
	if [[ -n "$tmp_dir" && -d "$tmp_dir" ]]; then
		rm -rf -- "$tmp_dir"
	fi
}

parse_arguments() {
	[[ $# -gt 0 ]] || {
		usage
		return 1
	}

	case "$1" in
	install | no-update | uninstall | make-desktop)
		command_name=$1
		shift
		;;
	--help | -h)
		usage
		exit 0
		;;
	*)
		die "unknown command: $1"
		;;
	esac

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

	[[ "$command_name" != uninstall || "$force" == false ]] || die '--force cannot be used with uninstall'
}

resolve_install_dir() {
	if [[ "$install_dir" != /* ]]; then
		install_dir=$PWD/$install_dir
	fi

	install_dir=${install_dir%/}
	[[ -n "$install_dir" && "$install_dir" != / ]] || die 'refusing to use the filesystem root as the installation directory'
}

confirm_installation() {
	local answer

	printf '是否安装到选中目录：%s [Y/n] ' "$install_dir"
	if ! IFS= read -r answer; then
		die 'could not read installation confirmation'
	fi

	case "$answer" in
	'' | Y | y)
		return
		;;
	*)
		info 'installation cancelled'
		return 1
		;;
	esac
}

confirm_desktop_shortcut() {
	local answer

	printf '是否创建快捷方式：%s [Y/n] ' "$DESKTOP_FILE"
	if ! IFS= read -r answer; then
		die 'could not read desktop shortcut confirmation'
	fi

	case "$answer" in
	'' | Y | y)
		make_desktop_shortcut
		;;
	*)
		info 'desktop shortcut creation skipped'
		;;
	esac
}

find_launcher() {
	local candidate

	for candidate in "$install_dir/BurpSuiteCommunity" "$install_dir/BurpSuite"; do
		if [[ -f "$candidate" && -x "$candidate" ]]; then
			printf '%s\n' "$candidate"
			return
		fi
	done

	die "Burp launcher not found in: $install_dir"
}

is_managed_desktop_file() {
	[[ -f "$DESKTOP_FILE" ]] && grep -Fqx -- 'X-BurpSuite-Manager=true' "$DESKTOP_FILE"
}

is_legacy_desktop_link() {
	[[ -L "$DESKTOP_FILE" ]] && [[ "$(readlink -- "$DESKTOP_FILE")" == "$install_dir/burpsuite-community-edition.desktop" ]]
}

remove_desktop_shortcut() {
	if is_managed_desktop_file || is_legacy_desktop_link; then
		rm -- "$DESKTOP_FILE"
		info 'desktop shortcut removed'
	elif [[ -e "$DESKTOP_FILE" || -L "$DESKTOP_FILE" ]]; then
		warn "leaving non-managed desktop shortcut unchanged: $DESKTOP_FILE"
	fi
}

make_desktop_shortcut() {
	local launcher
	local icon_path

	launcher=$(find_launcher)
	icon_path="$install_dir/.install4j/BurpSuiteCommunity.png"
	if [[ -e "$DESKTOP_FILE" || -L "$DESKTOP_FILE" ]]; then
		if ! is_managed_desktop_file && ! is_legacy_desktop_link && [[ "$force" == false ]]; then
			die "refusing to replace non-managed desktop shortcut: $DESKTOP_FILE (pass --force to replace it)"
		fi
		rm -- "$DESKTOP_FILE"
	fi

	mkdir -p -- "$DESKTOP_DIR"
	printf '%s\n' \
		'[Desktop Entry]' \
		'Type=Application' \
		'Name=Burp Suite Community Edition' \
		"Exec=\"$launcher\" %U" \
		"Icon=$icon_path" \
		'MimeType=application/x-extension-burp;' \
		'Categories=Development;Security;Network;' \
		'StartupWMClass=install4j-burp-StartBurp' \
		'Terminal=false' \
		'X-BurpSuite-Manager=true' >"$DESKTOP_FILE"
	chmod 644 -- "$DESKTOP_FILE"
	info 'desktop shortcut created'
	printf '  Shortcut: %s\n' "$DESKTOP_FILE"
}

remove_existing_installation() {
	local uninstaller="$install_dir/uninstall"
	local launcher
	local backup_path

	[[ -x "$uninstaller" ]] || die "existing path is not a Burp installation: $install_dir"
	launcher=$(find_launcher)
	backup_path="$launcher.burpsuite-manager.bak"
	warn "removing the existing Burp installation at: $install_dir"
	if [[ -f "$backup_path" ]]; then
		rm -- "$backup_path"
	fi
	"$uninstaller" -q
	if [[ -d "$install_dir" ]]; then
		rmdir -- "$install_dir" 2>/dev/null || die "uninstaller left files in the installation directory: $install_dir"
	fi
	[[ ! -e "$install_dir" ]] || die "uninstaller left the installation directory in place: $install_dir"
}

download_and_install() {
	local installer_path response_file

	if [[ -e "$install_dir" || -L "$install_dir" ]]; then
		[[ "$force" == true ]] || die "installation directory already exists: $install_dir (pass --force to replace it)"
		remove_existing_installation
	fi

	mkdir -p -- "$(dirname -- "$install_dir")"
	tmp_dir=$(mktemp -d "${TMPDIR:-/tmp}/burpsuite-install.XXXXXXXX")
	trap cleanup EXIT
	installer_path="$tmp_dir/burpsuite-installer.sh"
	response_file="$tmp_dir/response.varfile"

	curl --fail --location --retry 3 --output "$installer_path" "$INSTALLER_URL"
	chmod +x -- "$installer_path"
	printf '%s\n' \
		"sys.adminRights\$Boolean=false" \
		"sys.installationDir=$install_dir" \
		'sys.languageId=en' \
		"sys.programGroupDisabled\$Boolean=true" \
		"sys.symlinkDir=$HOME/.local/bin" >"$response_file"

	"$installer_path" -q -varfile "$response_file"
	find_launcher >/dev/null
	info 'Burp Suite Community installation complete'
}

patch_launcher() {
	local launcher=$1
	local backup_path="$launcher.burpsuite-manager.bak"
	local patched_path

	if grep -Fq -- '--disable-auto-update' "$launcher"; then
		return
	fi

	patched_path=$(mktemp "$install_dir/.${launcher##*/}.XXXXXXXX")
	awk '
		{
			gsub(/--user-config-file "[^"]*\/no-update\.json"[[:space:]]*/, "")
			if ($0 !~ /^[[:space:]]*#/ && $0 ~ /install4j\.burp\.StartBurp/ && $0 !~ /--disable-auto-update/) {
				sub(/install4j\.burp\.StartBurp[[:space:]]+/, "install4j.burp.StartBurp --disable-auto-update ")
			}
			print
		}
	' "$launcher" >"$patched_path"

	grep -Fq -- '--disable-auto-update' "$patched_path" || die "could not add the no-update flag to: $launcher"
	if [[ ! -e "$backup_path" ]]; then
		cp -p -- "$launcher" "$backup_path"
	fi
	mv -- "$patched_path" "$launcher"
	chmod +x -- "$launcher"
}

disable_updates() {
	local launcher

	launcher=$(find_launcher)
	patch_launcher "$launcher"
	info 'Automatic Burp updates are disabled'
	printf '  Launcher: %s\n' "$launcher"
}

uninstall_burpsuite() {
	local uninstaller="$install_dir/uninstall"
	local launcher
	local backup_path

	[[ -x "$uninstaller" ]] || die "Burp uninstaller not found: $uninstaller"
	launcher=$(find_launcher)
	backup_path="$launcher.burpsuite-manager.bak"
	if [[ -f "$backup_path" ]]; then
		rm -- "$backup_path"
	fi
	"$uninstaller" -q
	remove_desktop_shortcut
	[[ ! -e "$install_dir" ]] || warn "uninstaller left files in: $install_dir"
	info 'Burp Suite Community uninstalled; ~/.BurpSuite user data was preserved'
}

main() {
	parse_arguments "$@"
	resolve_install_dir
	require_command awk
	require_command chmod
	require_command cp
	require_command grep
	require_command mkdir
	require_command mktemp
	require_command mv
	require_command readlink
	require_command rm
	require_command rmdir

	case "$command_name" in
	install)
		require_command curl
		confirm_installation
		download_and_install
		disable_updates
		confirm_desktop_shortcut
		;;
	no-update)
		disable_updates
		;;
	uninstall)
		uninstall_burpsuite
		;;
	make-desktop)
		make_desktop_shortcut
		;;
	esac
}

main "$@"
