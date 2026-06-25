#!/usr/bin/env bash
set -Eeuo pipefail

portable_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
data_home="${XDG_DATA_HOME:-$HOME/.local/share}"
applications_dir="$data_home/applications"
fonts_dir="$data_home/fonts"
assume_yes=false
purge_user_data=false

desktop_files=(
	wps-office-wps.desktop
	wps-office-et.desktop
	wps-office-wpp.desktop
	wps-office-pdf.desktop
	wps-office-prometheus.desktop
)

bin_names=(
	wps
	et
	wpp
	wpspdf
)

usage() {
	printf 'Usage: %s [--yes] [--purge-user-data]\n' "${0##*/}" >&2
}

info() {
	printf '[i] %s\n' "$*"
}

die() {
	printf '[x] %s\n' "$*" >&2
	exit 1
}

confirm_uninstall() {
	local answer=

	if [[ "$assume_yes" == true ]]; then
		return 0
	fi

	printf 'Remove WPS portable installation at %s? This will not delete files under ~/document. (y/N) ' "$portable_dir"
	read -r answer

	case "$answer" in
	y | Y | yes | YES)
		return 0
		;;
	*)
		info "Cancelled."
		exit 0
		;;
	esac
}

remove_desktops() {
	local desktop_file

	for desktop_file in "${desktop_files[@]}"; do
		rm -f -- "$applications_dir/$desktop_file"
	done
}

remove_bin_wrappers() {
	local bin_name
	local path
	local target

	for bin_name in "${bin_names[@]}"; do
		path="$HOME/.local/bin/$bin_name"
		[[ -e "$path" || -L "$path" ]] || continue

		if [[ -L "$path" ]]; then
			target=$(readlink -f -- "$path" 2>/dev/null || true)
			if [[ "$target" == "$portable_dir/"* ]]; then
				rm -f -- "$path"
			fi
			continue
		fi

		if [[ -f "$path" ]] && grep -qF "portable_dir='$portable_dir'" "$path"; then
			rm -f -- "$path"
		fi
	done
}

remove_fonts() {
	local font_path
	local font_name

	[[ -d "$portable_dir/share/fonts/wps-office" ]] || return 0

	for font_path in "$portable_dir/share/fonts/wps-office/"*; do
		[[ -f "$font_path" ]] || continue
		font_name=$(basename "$font_path")
		rm -f -- "$fonts_dir/$font_name"
	done
}

remove_mime_references() {
	local mimeapps_file

	for mimeapps_file in "$HOME/.config/mimeapps.list" "$applications_dir/mimeapps.list"; do
		[[ -f "$mimeapps_file" ]] || continue
		cp -a -- "$mimeapps_file" "$mimeapps_file.bak"
		sed -i '/wps-office-\(wps\|et\|wpp\|pdf\|prometheus\)\.desktop/d' "$mimeapps_file"
	done
}

purge_user_config() {
	[[ "$purge_user_data" == true ]] || return 0

	rm -rf -- "$HOME/.config/Kingsoft" "$HOME/.local/share/Kingsoft"
}

main() {
	while [[ $# -gt 0 ]]; do
		case "$1" in
		--yes)
			assume_yes=true
			shift
			;;
		--purge-user-data)
			purge_user_data=true
			shift
			;;
		--help | -h)
			usage
			return 0
			;;
		*)
			usage
			die "unknown argument: $1"
			;;
		esac
	done

	[[ -d "$portable_dir/office6" ]] || die "not a WPS portable directory: $portable_dir"
	[[ -f "$portable_dir/install-local.sh" ]] || die "install-local.sh not found under: $portable_dir"
	[[ -n "$portable_dir" && "$portable_dir" != "/" && "$portable_dir" != "$HOME" ]] || die "refusing to remove unsafe directory: $portable_dir"

	confirm_uninstall
	remove_desktops
	remove_bin_wrappers
	remove_fonts
	remove_mime_references
	purge_user_config

	if command -v update-desktop-database >/dev/null 2>&1; then
		update-desktop-database "$applications_dir" 2>/dev/null || true
	fi

	if command -v fc-cache >/dev/null 2>&1; then
		fc-cache -f "$fonts_dir" 2>/dev/null || true
	fi

	rm -rf -- "$portable_dir"
	info "WPS portable installation removed. Documents under ~/document were not touched."
}

main "$@"
