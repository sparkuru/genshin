#!/usr/bin/env bash
set -Eeuo pipefail

readonly DEFAULT_DEB_URL="https://mirrors.aliyun.com/ubuntukylin/pool/partner/wps-office_12.1.0.17881_amd64.deb"
readonly CLEAN_SCRIPT_URL="https://raw.githubusercontent.com/sparkuru/genshin/refs/heads/main/tsuki/12-wps-office/clean.sh"
readonly DEFAULT_INSTALL_DIR="$PWD/wps-office-portable"
readonly TMP_PARENT_DIR="/tmp/install-wps-office"

deb_url=$DEFAULT_DEB_URL
deb_path=
install_dir=$DEFAULT_INSTALL_DIR
force=false

tmp_dir=
clean_script=

usage() {
	printf 'Usage: %s [--url <deb-url>] [--deb <path>] [--install-dir <dir>] [--force]\n' "${0##*/}" >&2
}

info() {
	printf '[i] %s\n' "$*"
}

die() {
	printf '[x] %s\n' "$*" >&2
	exit 1
}

cleanup() {
	if [[ -n "${tmp_dir:-}" && -d "$tmp_dir" ]]; then
		rm -rf -- "$tmp_dir"
	fi
}

trap cleanup EXIT

abs_path() {
	local path=$1
	local parent
	local name

	parent=$(dirname "$path")
	name=$(basename "$path")
	mkdir -p -- "$parent"
	parent=$(cd "$parent" && pwd)
	printf '%s/%s\n' "$parent" "$name"
}

require_command() {
	command -v "$1" >/dev/null 2>&1 || die "required command not found: $1"
}

prepare_tmp_dir() {
	mkdir -p -- "$TMP_PARENT_DIR"
	tmp_dir=$(mktemp -d "${TMP_PARENT_DIR}/work.XXXXXXXXXX")
}

safe_prepare_install_dir() {
	install_dir=$(abs_path "$install_dir")

	if [[ -e "$install_dir" && "$force" == false ]]; then
		die "install directory already exists: $install_dir; pass --force to replace it."
	fi

	if [[ -e "$install_dir" ]]; then
		[[ -n "$install_dir" && "$install_dir" != "/" && "$install_dir" != "$HOME" ]] || die "refusing to replace unsafe install directory: $install_dir"
		rm -rf -- "$install_dir"
	fi

	mkdir -p -- "$install_dir"
}

download_deb() {
	local file_name

	if [[ -n "$deb_path" ]]; then
		[[ -f "$deb_path" ]] || die "deb file not found: $deb_path"
		deb_path=$(abs_path "$deb_path")
		return 0
	fi

	require_command curl

	file_name=${deb_url##*/}
	[[ -n "$file_name" && "$file_name" == *.deb ]] || file_name="wps-office.deb"
	deb_path="${tmp_dir}/${file_name}"

	info "Downloading WPS deb: $deb_url"
	curl -L --fail --progress-bar -o "$deb_path" "$deb_url"
}

download_clean_script() {
	require_command curl

	clean_script="${tmp_dir}/clean.sh"
	info "Downloading clean helper: $CLEAN_SCRIPT_URL"
	curl -fsSL -o "$clean_script" "$CLEAN_SCRIPT_URL"
	chmod 0755 "$clean_script"

	bash -n "$clean_script"
	grep -q -- '--office6' "$clean_script" || die "downloaded clean.sh does not support --office6: $CLEAN_SCRIPT_URL"
	grep -q -- '--skip-user-config' "$clean_script" || die "downloaded clean.sh does not support --skip-user-config: $CLEAN_SCRIPT_URL"
}

copy_if_dir_exists() {
	local source_dir=$1
	local target_dir=$2

	if [[ -d "$source_dir" ]]; then
		mkdir -p -- "$(dirname "$target_dir")"
		cp -a -- "$source_dir" "$target_dir"
	fi
}

resolve_icon() {
	local icon_base=$1
	local icon_name=$2
	local size

	for size in 512x512 256x256 128x128 96x96 64x64 48x48 32x32 24x24 16x16 scalable; do
		if [[ "$size" == "scalable" && -f "$icon_base/hicolor/$size/apps/$icon_name.svg" ]]; then
			printf '%s\n' "$icon_base/hicolor/$size/apps/$icon_name.svg"
			return 0
		fi

		if [[ "$size" != "scalable" && -f "$icon_base/hicolor/$size/apps/$icon_name.png" ]]; then
			printf '%s\n' "$icon_base/hicolor/$size/apps/$icon_name.png"
			return 0
		fi
	done

	printf '%s\n' "$icon_name"
}

emit_desktop() {
	local file=$1
	local exec_path=$2
	local name=$3
	local name_zh=$4
	local wm_class=$5
	local icon=$6
	local mime_type=$7
	local categories=$8

	cat >"$file" <<EOF
[Desktop Entry]
Type=Application
Name=$name
Name[zh_CN]=$name_zh
Exec=$exec_path %U
Icon=$icon
MimeType=$mime_type
Categories=$categories
StartupNotify=false
Terminal=false
StartupWMClass=$wm_class
InitialPreference=3
EOF
}

generate_desktops() {
	local office6_dir=$1
	local icon_base=$2
	local applications_dir=$3
	local wps_icon
	local et_icon
	local wpp_icon
	local pdf_icon

	mkdir -p -- "$applications_dir"
	wps_icon=$(resolve_icon "$icon_base" wps-office2023-wpsmain)
	et_icon=$(resolve_icon "$icon_base" wps-office2023-etmain)
	wpp_icon=$(resolve_icon "$icon_base" wps-office2023-wppmain)
	pdf_icon=$(resolve_icon "$icon_base" wps-office2023-pdfmain)

	emit_desktop "$applications_dir/wps-office-wps.desktop" "$office6_dir/wps" "WPS Writer" "WPS 文字" wps "$wps_icon" \
		"application/wps-office.docx;application/wps-office.doc;application/vnd.openxmlformats-officedocument.wordprocessingml.document;application/msword;application/wps-office.wps;application/wps-office.dotx;application/wps-office.dot;application/rtf;application/wps-office.uot3;application/wps-office.uott3;application/wps-office.msg;application/wps-office.eml" "Office;WordProcessor;Qt;"
	emit_desktop "$applications_dir/wps-office-et.desktop" "$office6_dir/et" "WPS Spreadsheets" "WPS 表格" et "$et_icon" \
		"application/wps-office.xlsx;application/wps-office.xls;application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;application/vnd.ms-excel;application/wps-office.et;application/wps-office.ett;application/wps-office.uos;application/wps-office.uos3" "Office;Spreadsheet;Qt;"
	emit_desktop "$applications_dir/wps-office-wpp.desktop" "$office6_dir/wpp" "WPS Presentation" "WPS 演示" wpp "$wpp_icon" \
		"application/wps-office.pptx;application/wps-office.ppt;application/vnd.openxmlformats-officedocument.presentationml.presentation;application/vnd.ms-powerpoint;application/wps-office.dps;application/wps-office.dpt;application/wps-office.uop;application/wps-office.uop3" "Office;Presentation;Qt;"
	emit_desktop "$applications_dir/wps-office-pdf.desktop" "$office6_dir/wpspdf" "WPS PDF" "WPS PDF" wpspdf "$pdf_icon" \
		"application/pdf" "Office;Viewer;Qt;"
	emit_desktop "$applications_dir/wps-office-prometheus.desktop" "$office6_dir/wps" "WPS Office" "WPS Office" wps "$wps_icon" \
		"" "Office;Qt;"
}

generate_local_installer() {
	local installer_path="$install_dir/install-local.sh"

	cat >"$installer_path" <<'EOF'
#!/usr/bin/env bash
set -Eeuo pipefail

portable_dir=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
data_home="${XDG_DATA_HOME:-$HOME/.local/share}"
applications_dir="$data_home/applications"
fonts_dir="$data_home/fonts"
link_bin=false

usage() {
	printf 'Usage: %s [--link-bin]\n' "${0##*/}" >&2
}

info() {
	printf '[i] %s\n' "$*"
}

resolve_icon() {
	local icon_base=$1
	local icon_name=$2
	local size

	for size in 512x512 256x256 128x128 96x96 64x64 48x48 32x32 24x24 16x16 scalable; do
		if [[ "$size" == "scalable" && -f "$icon_base/hicolor/$size/apps/$icon_name.svg" ]]; then
			printf '%s\n' "$icon_base/hicolor/$size/apps/$icon_name.svg"
			return 0
		fi

		if [[ "$size" != "scalable" && -f "$icon_base/hicolor/$size/apps/$icon_name.png" ]]; then
			printf '%s\n' "$icon_base/hicolor/$size/apps/$icon_name.png"
			return 0
		fi
	done

	printf '%s\n' "$icon_name"
}

emit_desktop() {
	local file=$1
	local exec_path=$2
	local name=$3
	local name_zh=$4
	local wm_class=$5
	local icon=$6
	local mime_type=$7
	local categories=$8

	cat >"$file" <<DESKTOP_EOF
[Desktop Entry]
Type=Application
Name=$name
Name[zh_CN]=$name_zh
Exec=$exec_path %U
Icon=$icon
MimeType=$mime_type
Categories=$categories
StartupNotify=false
Terminal=false
StartupWMClass=$wm_class
InitialPreference=3
DESKTOP_EOF
}

generate_desktops() {
	local office6_dir=$1
	local icon_base=$2
	local desktop_dir=$3
	local wps_icon
	local et_icon
	local wpp_icon
	local pdf_icon

	mkdir -p -- "$desktop_dir"
	wps_icon=$(resolve_icon "$icon_base" wps-office2023-wpsmain)
	et_icon=$(resolve_icon "$icon_base" wps-office2023-etmain)
	wpp_icon=$(resolve_icon "$icon_base" wps-office2023-wppmain)
	pdf_icon=$(resolve_icon "$icon_base" wps-office2023-pdfmain)

	emit_desktop "$desktop_dir/wps-office-wps.desktop" "$office6_dir/wps" "WPS Writer" "WPS 文字" wps "$wps_icon" \
		"application/wps-office.docx;application/wps-office.doc;application/vnd.openxmlformats-officedocument.wordprocessingml.document;application/msword;application/wps-office.wps;application/wps-office.dotx;application/wps-office.dot;application/rtf;application/wps-office.uot3;application/wps-office.uott3;application/wps-office.msg;application/wps-office.eml" "Office;WordProcessor;Qt;"
	emit_desktop "$desktop_dir/wps-office-et.desktop" "$office6_dir/et" "WPS Spreadsheets" "WPS 表格" et "$et_icon" \
		"application/wps-office.xlsx;application/wps-office.xls;application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;application/vnd.ms-excel;application/wps-office.et;application/wps-office.ett;application/wps-office.uos;application/wps-office.uos3" "Office;Spreadsheet;Qt;"
	emit_desktop "$desktop_dir/wps-office-wpp.desktop" "$office6_dir/wpp" "WPS Presentation" "WPS 演示" wpp "$wpp_icon" \
		"application/wps-office.pptx;application/wps-office.ppt;application/vnd.openxmlformats-officedocument.presentationml.presentation;application/vnd.ms-powerpoint;application/wps-office.dps;application/wps-office.dpt;application/wps-office.uop;application/wps-office.uop3" "Office;Presentation;Qt;"
	emit_desktop "$desktop_dir/wps-office-pdf.desktop" "$office6_dir/wpspdf" "WPS PDF" "WPS PDF" wpspdf "$pdf_icon" \
		"application/pdf" "Office;Viewer;Qt;"
	emit_desktop "$desktop_dir/wps-office-prometheus.desktop" "$office6_dir/wps" "WPS Office" "WPS Office" wps "$wps_icon" \
		"" "Office;Qt;"
}

while [[ $# -gt 0 ]]; do
	case "$1" in
	--link-bin)
		link_bin=true
		shift
		;;
	--help | -h)
		usage
		exit 0
		;;
	*)
		usage
		printf '[x] unknown argument: %s\n' "$1" >&2
		exit 1
		;;
	esac
done

generate_desktops "$portable_dir/office6" "$portable_dir/share/icons" "$portable_dir/share/applications"

mkdir -p -- "$applications_dir"
cp -af -- "$portable_dir/share/applications/"*.desktop "$applications_dir/"

if [[ -d "$portable_dir/share/fonts/wps-office" ]]; then
	mkdir -p -- "$fonts_dir"
	cp -an -- "$portable_dir/share/fonts/wps-office/"* "$fonts_dir/" 2>/dev/null || true
fi

if [[ "$link_bin" == true ]]; then
	mkdir -p -- "$HOME/.local/bin"
	ln -sfn -- "$portable_dir/office6/wps" "$HOME/.local/bin/wps"
	ln -sfn -- "$portable_dir/office6/et" "$HOME/.local/bin/et"
	ln -sfn -- "$portable_dir/office6/wpp" "$HOME/.local/bin/wpp"
	ln -sfn -- "$portable_dir/office6/wpspdf" "$HOME/.local/bin/wpspdf"
fi

if [[ -x "$portable_dir/clean.sh" ]]; then
	"$portable_dir/clean.sh" --office6 "$portable_dir/office6" --home "$HOME" --user-config-only clean
fi

if command -v update-desktop-database >/dev/null 2>&1; then
	update-desktop-database "$applications_dir" 2>/dev/null || true
fi

if command -v fc-cache >/dev/null 2>&1; then
	fc-cache -f "$fonts_dir" 2>/dev/null || true
fi

info "WPS portable desktop entries installed."
info "Portable directory: $portable_dir"
EOF

	chmod 0755 "$installer_path"
}

build_portable() {
	local extract_dir
	local package_root
	local wps_root

	require_command dpkg-deb
	prepare_tmp_dir
	safe_prepare_install_dir
	download_clean_script
	download_deb

	extract_dir="$tmp_dir/extract"

	info "Extracting deb: $deb_path"
	dpkg-deb -x "$deb_path" "$extract_dir"

	package_root="$extract_dir"
	wps_root="$package_root/opt/kingsoft/wps-office"
	[[ -d "$wps_root/office6" ]] || die "office6 not found in deb: $wps_root/office6"

	info "Copying WPS program files."
	cp -a -- "$wps_root/." "$install_dir/"

	info "Copying icons and fonts."
	copy_if_dir_exists "$package_root/usr/share/icons" "$install_dir/share/icons"
	copy_if_dir_exists "$package_root/usr/share/fonts/wps-office" "$install_dir/share/fonts/wps-office"

	info "Generating desktop entries."
	generate_desktops "$install_dir/office6" "$install_dir/share/icons" "$install_dir/share/applications"

	info "Copying clean helper."
	cp -a -- "$clean_script" "$install_dir/clean.sh"
	chmod 0755 "$install_dir/clean.sh"

	info "Purging portable office6."
	"$clean_script" --office6 "$install_dir/office6" --skip-user-config clean

	info "Generating target-machine installer."
	generate_local_installer

	info "Portable WPS is ready: $install_dir"
	info "On another Linux machine, run: $install_dir/install-local.sh"
}

main() {
	while [[ $# -gt 0 ]]; do
		case "$1" in
		--url)
			[[ $# -ge 2 ]] || die "--url requires a value."
			deb_url=$2
			shift 2
			;;
		--deb)
			[[ $# -ge 2 ]] || die "--deb requires a path."
			deb_path=$2
			shift 2
			;;
		--install-dir)
			[[ $# -ge 2 ]] || die "--install-dir requires a directory."
			install_dir=$2
			shift 2
			;;
		--force)
			force=true
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

	build_portable
}

main "$@"
