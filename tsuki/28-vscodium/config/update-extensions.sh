#!/usr/bin/env bash
set -Eeuo pipefail

readonly SCRIPT_NAME=${0##*/}
readonly STYLE_RESET=$'\033[0m'
readonly STYLE_SUCCESS=$'\033[0;32m'
readonly STYLE_WARNING=$'\033[1;33m'
readonly STYLE_ERROR=$'\033[1;31m'
SCRIPT_DIR=$(cd -- "$(dirname -- "$0")" && pwd)
readonly SCRIPT_DIR
readonly MANIFEST="$SCRIPT_DIR/extension.json"
readonly EXTENSION_LIST="$SCRIPT_DIR/extension.txt"

work_dir=''
extensions_dir=''
codium_bin=''
transaction_active=false
current_id=''

usage() {
	printf 'Usage: %s [--extensions-dir DIR] [--check] [--help]\n' "$SCRIPT_NAME" >&2
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
	if [[ -f "$work_dir/extension.json" ]]; then
		cp -p -- "$work_dir/extension.json" "$MANIFEST" || return 1
	fi
	warn "rolled back $current_id"
}

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
	cp -p -- "$MANIFEST" "$work_dir/extension.json"
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

	manifest_tmp=$(mktemp "$SCRIPT_DIR/.extension.json.XXXXXXXX")
	if ! jq --arg id "$id" --arg version "$version" '.[$id].version = $version' "$MANIFEST" >"$manifest_tmp"; then
		rm -f -- "$manifest_tmp"
		die "could not update extension.json: $id"
	fi
	if ! mv -- "$manifest_tmp" "$MANIFEST"; then
		rm -f -- "$manifest_tmp"
		die "could not replace extension.json: $id"
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
	[[ -f "$EXTENSION_LIST" ]] || die "extension list not found: $EXTENSION_LIST"
	platform=$(platform_name)
	work_dir=$(mktemp -d "${TMPDIR:-/tmp}/update-extensions.XXXXXXXX")
	trap cleanup EXIT
	: >"$work_dir/ids"
	while IFS= read -r id || [[ -n "$id" ]]; do
		id=${id%$'\r'}
		[[ -z "$id" || "$id" == \#* ]] && continue
		[[ "$id" =~ ^[A-Za-z0-9_-]+\.[A-Za-z0-9_.-]+$ ]] || die "invalid extension ID in extension.txt: $id"
		if [[ -z "${seen_ids[$id]+x}" ]]; then
			printf '%s\n' "$id" >>"$work_dir/ids"
			seen_ids[$id]=1
		fi
	done <"$EXTENSION_LIST"
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
	reconcile_manifest "$current_manifest" "$index_file" || die 'could not reconcile extension.json with extension.txt'
	jq -e 'type == "object" and all(to_entries[]; (.key | test("^[A-Za-z0-9_-]+\\.[A-Za-z0-9_.-]+$")) and (.value.url | type == "string") and (.value.version == null or (.value.version | type == "string")))' "$work_dir/manifest.json" >/dev/null || die 'invalid reconciled extension manifest'
	manifest_to_read="$work_dir/manifest.json"
	if [[ "$check_only" == false ]] && ! cmp -s "$work_dir/manifest.json" "$MANIFEST"; then
		manifest_tmp=$(mktemp "$SCRIPT_DIR/.extension.json.XXXXXXXX")
		if ! cp -- "$work_dir/manifest.json" "$manifest_tmp" || ! mv -- "$manifest_tmp" "$MANIFEST"; then
			rm -f -- "$manifest_tmp"
			die 'could not synchronize extension.json'
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
				rm -f -- "$work_dir/old-paths" "$work_dir/extensions.json" "$work_dir/index-absent" "$work_dir/extension.json" "$work_dir/package.vsix"
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
