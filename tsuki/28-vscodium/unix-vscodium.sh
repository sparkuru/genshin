#!/usr/bin/env bash
set -Eeuo pipefail

usage() {
	printf 'Usage: %s COMMAND [TARGET] [OPTIONS]\n' "${0##*/}" >&2
	printf '  install --archive FILE --path DIR [--force]\n' >&2
	printf '  remove --path DIR\n' >&2
	printf '  local sync [settings|keybindings|extensions]   Repository -> local (default: all)\n' >&2
	printf '  repo sync [settings|keybindings|extensions]    Local -> repository (default: all)\n' >&2
	printf '  update extensions [--check] [--extensions-dir DIR]\n' >&2
}

# Keep command state and EXIT traps local to each invocation.
install_application() (
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
	printf '  %s install --archive <archive.tar.gz> --path <installation-directory> [--force]\n' "$SCRIPT_NAME" >&2
	printf '  %s remove --path <installation-directory>\n' "$SCRIPT_NAME" >&2
	printf '\nInstall or remove VSCodium plus its command link and desktop entry.\n' >&2
	printf '\nOptions:\n' >&2
	printf '  --archive <file>     VSCodium Linux tar.gz archive (required for installation).\n' >&2
	printf '  --path <directory>   Installation directory (required).\n' >&2
	printf '  --force              Replace an existing installation and managed integration files.\n' >&2
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

# shellcheck disable=SC2317 # Invoked indirectly by the EXIT trap in this subshell.
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
X-VSCodium-Installed-By=unix-vscodium.sh
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
	return 0
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
)

sync_configuration() (
	set -Eeuo pipefail

	direction=$1
	target=$2
	script_dir=${BASH_SOURCE[0]}
	[[ "$script_dir" == */* ]] || script_dir="./$script_dir"
	script_dir=$(cd -- "${script_dir%/*}" && pwd -P)
	config_dir="$script_dir/config"
	local_dir="${XDG_CONFIG_HOME:-$HOME/.config}/VSCodium/User"
	codium_bin=${CODIUM_BIN:-codium}
	tmp_file=''
	extensions_tmp_file=''
	extension_ids=()

	die() {
		printf 'Error: %s\n' "$*" >&2
		exit 1
	}

	# shellcheck disable=SC2317 # Invoked indirectly by the EXIT trap in this subshell.
	cleanup() {
		if [[ -n "$tmp_file" && -f "$tmp_file" ]]; then
			rm -f -- "$tmp_file"
		fi
		if [[ -n "$extensions_tmp_file" && -f "$extensions_tmp_file" ]]; then
			rm -f -- "$extensions_tmp_file"
		fi
	}

	backup_file() {
		local path=$1
		local backup_path

		if [[ -e "$path" || -L "$path" ]]; then
			backup_path=$(mktemp "/tmp/vscodium-${path##*/}.backup.XXXXXXXX")
			cp -Pp -- "$path" "$backup_path"
			printf 'Backup: %s\n' "$backup_path"
		fi
	}

	replace_file() {
		local source_path=$1
		local target_path=$2

		if [[ ! -L "$target_path" ]] && cmp -s -- "$source_path" "$target_path"; then
			return 0
		fi
		tmp_file=$(mktemp "${TMPDIR:-/tmp}/vscodium-sync.XXXXXXXX")
		cp -Lp -- "$source_path" "$tmp_file"
		backup_file "$target_path"
		mv -fT -- "$tmp_file" "$target_path"
		tmp_file=''
	}

	sync_file() {
		local name=$1
		local repo_path="$config_dir/$name.json"
		local local_path="$local_dir/$name.json"

		if [[ "$direction" == repo ]]; then
			replace_file "$local_path" "$repo_path"
		else
			# Materialize repository links before linking back, including local -> repo reversals.
			if [[ -L "$repo_path" ]]; then
				replace_file "$repo_path" "$repo_path"
			fi
			if [[ "$local_path" -ef "$repo_path" ]]; then
				return 0
			fi
			backup_file "$local_path"
			ln -sfnT -- "$repo_path" "$local_path"
		fi
		printf '%s synchronized to %s\n' "$name" "$direction"
	}

	prepare_extensions() {
		local extension_id
		local list_path="$config_dir/extensions.txt"

		command -v "$codium_bin" >/dev/null 2>&1 || die "VSCodium command not found: $codium_bin"
		[[ ! -d "$list_path" ]] || die "extension list is a directory: $list_path"
		if [[ "$direction" == repo ]]; then
			extensions_tmp_file=$(mktemp "${TMPDIR:-/tmp}/vscodium-extensions.XXXXXXXX")
			"$codium_bin" --list-extensions | LC_ALL=C sort -u >"$extensions_tmp_file"
			list_path=$extensions_tmp_file
		fi
		[[ -f "$list_path" ]] || die "extension list not found: $list_path"
		while IFS= read -r extension_id || [[ -n "$extension_id" ]]; do
			extension_id=${extension_id%$'\r'}
			[[ -z "$extension_id" || "$extension_id" == \#* ]] && continue
			[[ "$extension_id" =~ ^[A-Za-z0-9_-]+\.[A-Za-z0-9_.-]+$ ]] || die "invalid extension ID: $extension_id"
			extension_ids+=("$extension_id")
		done <"$list_path"
	}

	sync_extensions() {
		local extension_id
		local -a unavailable_extensions=()

		if [[ "$direction" == repo ]]; then
			# An empty installed list is valid when local is the source of truth.
			if [[ -L "$config_dir/extensions.txt" ]] || ! cmp -s -- "$extensions_tmp_file" "$config_dir/extensions.txt"; then
				backup_file "$config_dir/extensions.txt"
				mv -fT -- "$extensions_tmp_file" "$config_dir/extensions.txt"
				extensions_tmp_file=''
			fi
			printf 'Extensions synchronized to repository: %s\n' "$config_dir/extensions.txt"
			return 0
		fi

		for extension_id in "${extension_ids[@]}"; do
			if ! "$codium_bin" --install-extension "$extension_id"; then
				unavailable_extensions+=("$extension_id")
			fi
		done

		if [[ ${#unavailable_extensions[@]} -gt 0 ]]; then
			printf 'Unavailable extensions:\n' >&2
			printf '  %s\n' "${unavailable_extensions[@]}" >&2
			return 1
		fi
	}

	main() {
		local command name source_path target_path
		local -a names=()

		for command in mkdir ln mktemp cp mv rm cmp sort; do
			command -v "$command" >/dev/null 2>&1 || die "required command not found: $command"
		done
		trap cleanup EXIT
		case "$target" in
		all) names=(settings keybindings) ;;
		settings | keybindings) names=("$target") ;;
		esac
		for name in "${names[@]}"; do
			source_path="$config_dir/$name.json"
			target_path="$local_dir/$name.json"
			if [[ "$direction" == repo ]]; then
				source_path="$local_dir/$name.json"
				target_path="$config_dir/$name.json"
			fi
			[[ -f "$source_path" ]] || die "configuration file not found: $source_path"
			[[ ! -d "$target_path" ]] || die "configuration target is a directory: $target_path"
		done
		if [[ "$target" == all || "$target" == extensions ]]; then
			prepare_extensions
		fi
		if [[ "$direction" == local && ${#names[@]} -gt 0 ]]; then
			mkdir -p -- "$local_dir"
		fi
		for name in "${names[@]}"; do
			sync_file "$name"
		done
		if [[ "$target" == all || "$target" == extensions ]]; then
			sync_extensions
		fi
	}

	main
)

update_extensions() (
set -Eeuo pipefail

readonly SCRIPT_NAME=${0##*/}
readonly STYLE_RESET=$'\033[0m'
readonly STYLE_SUCCESS=$'\033[0;32m'
readonly STYLE_WARNING=$'\033[1;33m'
readonly STYLE_ERROR=$'\033[1;31m'
SCRIPT_DIR=$(cd -- "$(dirname -- "$0")" && pwd)
readonly SCRIPT_DIR
readonly MANIFEST="$SCRIPT_DIR/config/extensions.json"
readonly EXTENSIONS_LIST="$SCRIPT_DIR/config/extensions.txt"

work_dir=''
extensions_dir=''
codium_bin=''
transaction_active=false
current_id=''

usage() {
	printf 'Usage: %s update extensions [--extensions-dir DIR] [--check] [--help]\n' "$SCRIPT_NAME" >&2
	printf 'Check Open VSX for newer versions and install verified VSIX packages.\n' >&2
	printf '  --extensions-dir DIR  VSCodium extensions directory (default: ~/.vscode-oss/extensions)\n' >&2
	printf '  --check               Report available updates without installing\n' >&2
}

print_status() {
	local style=$1
	local message=$2
	local fd=$3

	if [[ -n "${NO_COLOR:-}" || ! -t "$fd" ]]; then
		printf '%s\n' "$message" >&"$fd"
	else
		printf '%s%s%s\n' "$style" "$message" "$STYLE_RESET" >&"$fd"
	fi
}

die() {
	print_status "$STYLE_ERROR" "Error: $*" 2
	exit 1
}

warn() {
	print_status "$STYLE_WARNING" "Warning: $*" 2
}

success() {
	print_status "$STYLE_SUCCESS" "$*" 1
}

skip() {
	print_status "$STYLE_WARNING" "Skipped $*" 1
}

confirm_skip() {
	local id=$1
	local answer

	if [[ ! -t 0 ]]; then
		warn "no terminal input; skipping incompatible $id"
		return 0
	fi

	while true; do
		printf 'Skip incompatible %s and continue? [Y/n] ' "$id" >&2
		if ! IFS= read -r answer; then
			die "could not read an answer for $id"
		fi
		case "$answer" in
		'' | y | Y | yes | YES) return 0 ;;
		n | N | no | NO) return 1 ;;
		*) warn 'answer Y or n' ;;
		esac
	done
}

require_command() {
	command -v "$1" >/dev/null 2>&1 || die "required command not found: $1"
}

restore_extension() {
	local old_path
	local path

	if [[ -f "$work_dir/old-paths" ]]; then
		while IFS= read -r -d '' old_path; do
			path="$extensions_dir/$old_path"
			if [[ -d "$path" && ! -L "$path" ]]; then
				rm -rf -- "$path" || return 1
			fi
			cp -a -- "$work_dir/backup/$old_path" "$path" || return 1
		done <"$work_dir/old-paths"
	fi

	while IFS= read -r -d '' path; do
		if ! grep -Fxzq -- "${path##*/}" "$work_dir/old-paths"; then
			rm -rf -- "$path" || return 1
		fi
	done < <(find "$extensions_dir" -mindepth 1 -maxdepth 1 -type d -name "$current_id-*" -print0)

	if [[ -f "$work_dir/extensions.json" ]]; then
		cp -p -- "$work_dir/extensions.json" "$extensions_dir/extensions.json" || return 1
	elif [[ -f "$work_dir/index-absent" && -f "$extensions_dir/extensions.json" ]]; then
		rm -f -- "$extensions_dir/extensions.json" || return 1
	fi
	if [[ -f "$work_dir/repo-extensions.json" ]]; then
		cp -p -- "$work_dir/repo-extensions.json" "$MANIFEST" || return 1
	fi
	warn "rolled back $current_id"
}

# shellcheck disable=SC2317 # Invoked indirectly by the EXIT trap in this subshell.
cleanup() {
	local exit_status=$?
	trap - EXIT
	if [[ "$transaction_active" == true ]]; then
		if restore_extension; then
			transaction_active=false
		else
			print_status "$STYLE_ERROR" "Error: rollback failed for $current_id; backup: $work_dir" 2
		fi
	fi
	if [[ -n "$work_dir" && -d "$work_dir" && "$transaction_active" == false ]]; then
		rm -rf -- "$work_dir"
	fi
	exit "$exit_status"
}

version_is_newer() {
	local remote=$1
	local local_version=$2
	[[ -z "$local_version" ]] && return 0
	[[ "$remote" != "$local_version" ]] && [[ "$(printf '%s\n%s\n' "$remote" "$local_version" | LC_ALL=C sort -V | tail -n 1)" == "$remote" ]]
}

platform_name() {
	local arch
	case "$(uname -s)" in
	Linux) ;;
	*) die 'only Linux VSCodium installations are supported' ;;
	esac
	case "$(uname -m)" in
	x86_64) arch=x64 ;;
	aarch64) arch=arm64 ;;
	armv7l) arch=armhf ;;
	*) die "unsupported CPU architecture: $(uname -m)" ;;
	esac
	printf 'linux-%s\n' "$arch"
}

fetch_metadata() {
	local url=$1
	local platform=$2
	local output=$3

	if ! curl -fsSL --retry 2 --connect-timeout 10 --max-time 60 "$url/$platform" -o "$output" 2>/dev/null; then
		curl -fsSL --retry 2 --connect-timeout 10 --max-time 60 "$url/latest" -o "$output"
	fi
}

reconcile_manifest() {
	local current_file=$1
	local index_file=$2

	jq -Rn --slurpfile current "$current_file" --slurpfile installed "$index_file" '
		reduce inputs as $id ({};
			.[$id] = ($current[0][$id] // {
				url: ("https://open-vsx.org/api/" + ($id | split(".")[0]) + "/" + ($id | split(".")[1:] | join("."))),
				version: ([$installed[0][] | select(.identifier.id == $id) | .version] | last // null)
			})
		)
	' "$work_dir/ids" >"$work_dir/manifest.json"
}

backup_extension() {
	local path
	local name

	mkdir -p -- "$work_dir/backup"
	: >"$work_dir/old-paths"
	while IFS= read -r -d '' path; do
		name=${path##*/}
		[[ -L "$path" ]] && die "extension directory is a symlink: $path"
		printf '%s\0' "$name" >>"$work_dir/old-paths"
		cp -a -- "$path" "$work_dir/backup/$name"
	done < <(find "$extensions_dir" -mindepth 1 -maxdepth 1 -type d -name "$current_id-*" -print0)
	if [[ -f "$extensions_dir/extensions.json" ]]; then
		cp -p -- "$extensions_dir/extensions.json" "$work_dir/extensions.json"
	else
		: >"$work_dir/index-absent"
	fi
	cp -p -- "$MANIFEST" "$work_dir/repo-extensions.json"
	transaction_active=true
}

install_extension() {
	local id=$1
	local version=$2
	local download_url=$3
	local vsix="$work_dir/package.vsix"
	local package_id
	local package_version
	local manifest_tmp
	local install_log="$work_dir/install.log"

	[[ "$download_url" == https://* ]] || die "download URL is not HTTPS: $id"
	if ! curl -fsSL --retry 2 --connect-timeout 10 --max-time 300 "$download_url" -o "$vsix"; then
		die "download failed: $id@$version"
	fi
	if ! unzip -Z1 "$vsix" >"$work_dir/archive-paths"; then
		die "invalid VSIX archive: $id@$version"
	fi
	if grep -Eq '(^/|(^|/)\.\.(/|$)|\\)' "$work_dir/archive-paths"; then
		die "unsafe VSIX paths: $id"
	fi
	if ! unzip -tqq "$vsix"; then
		die "VSIX archive verification failed: $id@$version"
	fi
	mkdir -p -- "$work_dir/unpacked"
	if ! unzip -qq "$vsix" -d "$work_dir/unpacked"; then
		die "VSIX extraction failed: $id@$version"
	fi
	if [[ -n "$(find "$work_dir/unpacked" -type l -print -quit)" ]]; then
		die "VSIX contains a symlink: $id"
	fi
	[[ -f "$work_dir/unpacked/extension/package.json" ]] || die "VSIX lacks extension/package.json: $id"
	if ! package_id=$(jq -er '.publisher + "." + .name' "$work_dir/unpacked/extension/package.json"); then
		die "invalid VSIX package identity: $id@$version"
	fi
	if ! package_version=$(jq -er '.version' "$work_dir/unpacked/extension/package.json"); then
		die "invalid VSIX package version: $id@$version"
	fi
	[[ "${package_id,,}" == "${id,,}" && "$package_version" == "$version" ]] || die "VSIX identity mismatch: expected $id@$version, got $package_id@$package_version"

	backup_extension
	if ! "$codium_bin" --extensions-dir "$extensions_dir" --install-extension "$vsix" --force >"$install_log" 2>&1; then
		if grep -Eiq 'not compatible with (VSCodium|Visual Studio Code|VS Code)' "$install_log"; then
			if ! restore_extension; then
				die "rollback failed for incompatible $id@$version; backup: $work_dir"
			fi
			transaction_active=false
			if confirm_skip "$id@$version"; then
				skip "$id@$version: incompatible with this VSCodium"
				return 0
			fi
			die "update stopped after incompatible $id@$version"
		fi
		cat -- "$install_log" >&2
		die "installation failed: $id@$version"
	fi
	cat -- "$install_log"
	"$codium_bin" --extensions-dir "$extensions_dir" --list-extensions --show-versions |
		grep -Fxiq -- "$id@$version" || die "installed version could not be verified: $id@$version"

	manifest_tmp=$(mktemp "$SCRIPT_DIR/config/.extensions.json.XXXXXXXX")
	if ! jq --arg id "$id" --arg version "$version" '.[$id].version = $version' "$MANIFEST" >"$manifest_tmp"; then
		rm -f -- "$manifest_tmp"
		die "could not update extensions.json: $id"
	fi
	if ! mv -- "$manifest_tmp" "$MANIFEST"; then
		rm -f -- "$manifest_tmp"
		die "could not replace extensions.json: $id"
	fi
	transaction_active=false
	success "Updated $id to $version"
}

main() {
	local check_only=false
	local platform
	local id
	local manifest_to_read
	local manifest_tmp
	local current_manifest
	local index_file
	local url
	local installed_version
	local remote_version
	local remote_platform
	local download_url
	local update_count=0
	local error_count=0
	local -A seen_ids=()

	while [[ $# -gt 0 ]]; do
		case "$1" in
		--extensions-dir)
			[[ $# -ge 2 ]] || die '--extensions-dir requires a directory'
			extensions_dir=$2
			shift 2
			;;
		--check)
			check_only=true
			shift
			;;
		--help | -h)
			usage
			return 0
			;;
		*) die "unknown argument: $1" ;;
		esac
	done

	extensions_dir=${extensions_dir:-"$HOME/.vscode-oss/extensions"}
	codium_bin=${CODIUM_BIN:-codium}
	[[ -d "$extensions_dir" && ! -L "$extensions_dir" ]] || die "extension directory not found: $extensions_dir"
	for command in curl jq unzip mktemp cp mv rm find grep sort tail uname cmp; do
		require_command "$command"
	done
	if [[ "$check_only" == false ]]; then
		require_command "$codium_bin"
	fi
	[[ -f "$EXTENSIONS_LIST" ]] || die "extension list not found: $EXTENSIONS_LIST"
	platform=$(platform_name)
	work_dir=$(mktemp -d "${TMPDIR:-/tmp}/update-extensions.XXXXXXXX")
	trap cleanup EXIT
	: >"$work_dir/ids"
	while IFS= read -r id || [[ -n "$id" ]]; do
		id=${id%$'\r'}
		[[ -z "$id" || "$id" == \#* ]] && continue
		[[ "$id" =~ ^[A-Za-z0-9_-]+\.[A-Za-z0-9_.-]+$ ]] || die "invalid extension ID in extensions.txt: $id"
		if [[ -z "${seen_ids[$id]+x}" ]]; then
			printf '%s\n' "$id" >>"$work_dir/ids"
			seen_ids[$id]=1
		fi
	done <"$EXTENSIONS_LIST"
	index_file="$extensions_dir/extensions.json"
	if [[ ! -f "$index_file" ]]; then
		index_file="$work_dir/empty-index.json"
		printf '[]\n' >"$index_file"
	fi
	current_manifest=$MANIFEST
	if [[ ! -f "$current_manifest" ]]; then
		current_manifest="$work_dir/empty-manifest.json"
		printf '{}\n' >"$current_manifest"
	fi
	jq -e 'type == "object"' "$current_manifest" >/dev/null || die 'invalid extension manifest'
	reconcile_manifest "$current_manifest" "$index_file" || die 'could not reconcile extensions.json with extensions.txt'
	jq -e 'type == "object" and all(to_entries[]; (.key | test("^[A-Za-z0-9_-]+\\.[A-Za-z0-9_.-]+$")) and (.value.url | type == "string") and (.value.version == null or (.value.version | type == "string")))' "$work_dir/manifest.json" >/dev/null || die 'invalid reconciled extension manifest'
	manifest_to_read="$work_dir/manifest.json"
	if [[ "$check_only" == false ]] && ! cmp -s "$work_dir/manifest.json" "$MANIFEST"; then
		manifest_tmp=$(mktemp "$SCRIPT_DIR/config/.extensions.json.XXXXXXXX")
		if ! cp -- "$work_dir/manifest.json" "$manifest_tmp" || ! mv -- "$manifest_tmp" "$MANIFEST"; then
			rm -f -- "$manifest_tmp"
			die 'could not synchronize extensions.json'
		fi
		manifest_to_read=$MANIFEST
	fi

	while IFS= read -r id; do
		url=$(jq -r --arg id "$id" '.[$id].url' "$manifest_to_read")
		[[ "$url" == https://open-vsx.org/api/* ]] || die "unsupported metadata URL: $id"
		installed_version=''
		if [[ -f "$extensions_dir/extensions.json" ]]; then
			installed_version=$(jq -r --arg id "$id" '[.[] | select(.identifier.id == $id) | .version] | last // empty' "$extensions_dir/extensions.json")
		fi
		if ! fetch_metadata "$url" "$platform" "$work_dir/metadata.json"; then
			skip "$id: could not check Open VSX"
			((error_count += 1))
			continue
		fi
		remote_version=$(jq -r '.version // empty' "$work_dir/metadata.json")
		remote_platform=$(jq -r '.targetPlatform // "universal"' "$work_dir/metadata.json")
		download_url=$(jq -r '.files.download // empty' "$work_dir/metadata.json")
		[[ -n "$remote_version" && -n "$download_url" ]] || die "invalid Open VSX metadata: $id"
		if [[ "$remote_platform" != "$platform" && "$remote_platform" != universal ]]; then
			skip "$id: no compatible package for $platform"
			((error_count += 1))
			continue
		fi
		if version_is_newer "$remote_version" "$installed_version"; then
			printf '%s: %s -> %s\n' "$id" "${installed_version:-not installed}" "$remote_version"
			((update_count += 1))
			if [[ "$check_only" == false ]]; then
				current_id=$id
				install_extension "$id" "$remote_version" "$download_url"
				rm -rf -- "$work_dir/unpacked"
				rm -rf -- "$work_dir/backup"
				rm -f -- "$work_dir/old-paths" "$work_dir/extensions.json" "$work_dir/index-absent" "$work_dir/repo-extensions.json" "$work_dir/package.vsix"
			fi
		else
			skip "$id: installed $installed_version, latest $remote_version"
		fi
	done <"$work_dir/ids"
	printf 'Updates available: %d\n' "$update_count"
	if ((error_count > 0)); then
		print_status "$STYLE_ERROR" "Extensions not checked: $error_count" 2
		return 1
	fi
}

main "$@"
)

main() {
	local action=${1:-}
	local direction target
	[[ $# -eq 0 ]] || shift
	case "$action" in
	install) install_application "$@" ;;
	remove) install_application --uninstall "$@" ;;
	local | repo)
		direction=$action
		if [[ ${1:-} == --help || ${1:-} == -h ]]; then
			usage
			return 0
		fi
		[[ ${1:-} == sync ]] || {
			printf 'Error: expected "%s sync"\n' "$direction" >&2
			return 1
		}
		shift
		target=${1:-all}
		case "$target" in
		--help | -h)
			usage
			return 0
			;;
		settings | keybindings | extensions) ;;
		all) [[ $# -eq 0 ]] || {
			printf 'Error: omit the target to sync all\n' >&2
			return 1
		} ;;
		*)
			printf 'Error: unknown sync target: %s\n' "$target" >&2
			return 1
			;;
		esac
		[[ $# -eq 0 ]] || shift
		if [[ ${1:-} == --help || ${1:-} == -h ]]; then
			usage
			return 0
		fi
		[[ $# -eq 0 ]] || {
			printf 'Error: unexpected argument: %s\n' "$1" >&2
			return 1
		}
		sync_configuration "$direction" "$target"
		;;
	update)
		if [[ ${1:-} == extensions ]]; then shift; fi
		update_extensions "$@"
		;;
	--help | -h | help) usage ;;
	'')
		usage
		return 1
		;;
	*)
		printf 'Error: unknown command: %s\n' "$action" >&2
		usage
		return 1
		;;
	esac
}

main "$@"
