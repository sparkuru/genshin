#!/usr/bin/env bash
set -Eeuo pipefail

readonly DEFAULT_DEB_URL="https://mirrors.aliyun.com/ubuntukylin/pool/partner/wps-office_12.1.0.17881_amd64.deb"
readonly DEFAULT_INSTALL_DIR="$PWD/wps-office-portable"
readonly TMP_PARENT_DIR="/tmp/install-wps-office"

deb_url=$DEFAULT_DEB_URL
deb_path=
install_dir=$DEFAULT_INSTALL_DIR
force=false

tmp_dir=

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

generate_clean_helper() {
	local target=$1

	cat >"$target" <<'CLEAN_SCRIPT_EOF'
#!/usr/bin/env bash
set -Eeuo pipefail

readonly OFFICE_ROOT="/opt/kingsoft/wps-office"
readonly DEFAULT_USER_NAME="${SUDO_USER:-${USER:-}}"

OFFICE6_DIR="${OFFICE_ROOT}/office6"
TARGET_USER_NAME="$DEFAULT_USER_NAME"
TARGET_USER_HOME=
DRY_RUN=false
SKIP_USER_CONFIG=false
USER_CONFIG_ONLY=false

readonly ROGUE_BINS=(
	wpscloudsvr
	wpscloudsrv
	wpsofd
	transerr
	wpslingxi
	ksolaunch
	EverythingDaemon
	KPacketInstall
	kccdelete
	wpsquery
	wpsEnvCheckTool
	wpsd
	promecefpluginhost
	ofd
	eptools
)

readonly ROGUE_ADDONS=(
	kaiaccompanywrite
	kaichatclient
	kaipushsdk
	kaiwpp
	kcopilotentry
	kcopilotentrylite
	kcopilotjsapi
	kcopilotsdk
	ketcopilot
	kwppcopilot
	kpdfcopilot
	kwpscopilot
	ktaskpanelcopilot
	kwebwpscopilot
	kwebaipdfinsight
	kwebaireport
	kwebaiaccompanywrite
	kwebaihistorysession
	kwebaireference
	kwebwpsainewfilepanel
	kwebwpsdoccomposing
	kwpsaigc
	kwpsaidoc2ppt
	kwpsaifindreplace
	kwpsaitablestyle
	kwpsaitypeset
	kwpsaiwritingsuggest
	kpdfaigcbox
	kpdfaisearch
	kpubaigcbox
	kwpslingxi
	ketaitoolbox
	ketaidataanalysis
	kwpsmathor
	kwppmathor
	kwpsformulaconverter
	kwebmultformulamatch
	kwpsincparser
	karticlewebcloudsummary
	kproofread
	ksoformatproof
	kwppbeautify
	wpsassistanttool
	cloudpushsdk
	messagepush
	kcloudadapter
	kclouddocs
	kcloudfiledialog
	kwpscloudmodule
	kwpscloudskin
	kwebclouddrivesetting
	kwebdoccloudsync
	kwebwpsyunboxdoccloudsync
	kwebdocscontrol
	kwebadaptersyncfolder
	qing
	yunbox
	yunkitapi
	kdocerbase
	kdocercore
	kdocercorelite
	kdocerjsapi20
	kdocerjsapilite20
	kdocerpage
	kdocerresapply
	kdocerresnetwork
	kdocerresource
	kdocfinalizedlist
	kdocfinalizedmgr
	konlinefonts
	kwebdashboard
	officespace
	wpsdoccenter
	kaccessbase
	kqingdlg
	kspostpay
	kusercenter
	kpromeaccountpanel
	kpromebrowser
	kpromechuangkit
	kpromeprocesson
	kpromeprocessonlocal
	kprometheusjsapi
	kpromewebapp
	kpromewebappruninfo
	kpromeworkarea
	kstartpage
	kappcenter
	kapplist
	kappmgr
	kappentryobject
	kappessbuiltinjsapi
	kappesscommon
	kappessdoccommon
	kappessframework
	kwebpromehelp
	kwebextensionlist
	khelp
	kwebeditioninfo
	kwebwpscustomtemplateconf
	kwebwpsdocofficial
	kwpsofficial
	kwebsuwellaidocument
	kwebwpsmarkdown
	kwpsmarkdown
	kwebwpsinstructioncenter
	khoneycomb
	kwhatsnew
	ktipsclientmanager
	ktipsmanager
	kwebintegratedpanel
	kapmsdk
	secanalyze
	ksphotokit
	kwebdoctranslate
	kwebocrtool
	kscreengrabocrent
	knetwork
	knetworkhook
	kappconnectivity
	kbasewebapi
	ketbasewebapi
	kdomainservice
	kentcloudconfig
	kmessagecentersdk
	kmessagecentersrv
	kwebmessagecenterpanel
	kfeedback
	kfeedbackcmds
	kqrcode
	knewshare
	shareplay
	kcooperatearea
	ksoftbus
	ksoftbuscore
	ksoftbusproxy
	kplugindistributer
	linkeddatatype
	kwebetpowerquery
	kwebetpowerquerysidepanel
	kwebettaskpane
	kpowerquery
	kccsdk
	cef
	kcef
	kcefwidgetpool
)

readonly ROGUE_PLUGINS=(
	khelp
	kwebpromehelp
	kwebeditioninfo
	kprometheusjsapi
	kwebdoccloudsync
	ksoftbusproxy
	ketcopilot
	kcopilotentrylite
	kcopilotjsapi
	kwebdoctranslate
	kwebsplitmerge
	kwebocrtool
	kwebmessagecenterpanel
	kmessagecentersdk
	kpromeworkarea
	kwebintegratedpanel
	kpromebrowser
	kwebwpsainewfilepanel
	kwebwpsinstructioncenter
	kwebaireport
	kwebdocscontrol
	kwpscloudmodule
	kpromewebappruninfo
	ketbasewebapi
	ketaitoolbox
	kwebettaskpane
	kwpsofficial
	kwebwpsdocofficial
	kwebwpscustomtemplateconf
	kwebsuwellaidocument
	kwppcopilot
	ktaskpanelcopilot
	kwpscopilot
	kwpsaitypeset
	kwebwpscopilot
	kwebaipdfinsight
	kwebwpsdoccomposing
	kcopilotentry
	kwpsaidoc2ppt
	kdocercore
	kdocerjsapi20
	kwebaireference
	kwebaihistorysession
	kwpsaiwritingsuggest
	kwpsaigc
	kwpsincparser
	kwpsmathor
	kwpsformulaconverter
	kwebmultformulamatch
	kwebetpowerquery
	kwebetpowerquerysidepanel
	kpowerquery
	kwebdashboard
	kpubaigcbox
	kpdfaigcbox
	kpdfcopilot
	karticlewebcloudsummary
	ketaidataanalysis
	kwebaiaccompanywrite
	kaiaccompanywrite
	kwebclouddrivesetting
	kwebwpsyunboxdoccloudsync
	kwebadaptersyncfolder
	kwpsaitablestyle
	kwpsserver
	ktipsmanager
	kwpsmarkdown
	kwebwpsmarkdown
	kmessagecentersrv
	kpromegovaffairs
	officespace
)

readonly HISTORY_PATTERNS=(
	RecentFiles
	openFile
	CloudFileDialog
	lastOpenDir
	FileDialog
	openfilelist
	AutoRecoverFilePath
)

readonly CLOUD_NUMERIC_FLAGS=(
	batchRemove
	supportPMoveFolder
	localsyncfolder
	showpanel
)

info() {
	printf '[i] %s\n' "$*"
}

warn() {
	printf '[!] %s\n' "$*" >&2
}

die() {
	printf '[x] %s\n' "$*" >&2
	exit 1
}

usage() {
	printf 'Usage: %s [--dry] [--office6 <dir>] [--user <name>] [--home <dir>] [--skip-user-config|--user-config-only] [clean|status|list]\n' "${0##*/}" >&2
}

resolve_user_home() {
	local user_name=${1:-}
	local home_override=${2:-}
	local user_home=

	if [[ -n "$home_override" ]]; then
		printf '%s\n' "$home_override"
		return 0
	fi

	if [[ -n "$user_name" && "$user_name" != "root" ]] && command -v getent >/dev/null 2>&1; then
		user_home=$(getent passwd "$user_name" | cut -d ':' -f 6 || true)
	fi

	if [[ -z "$user_home" ]]; then
		user_home=${HOME:-/root}
	fi

	printf '%s\n' "$user_home"
}

backup_once() {
	local path=$1

	[[ -f "$path" ]] || return 0
	[[ "$DRY_RUN" == false ]] || return 0
	[[ -f "$path.bak" ]] || cp -a -- "$path" "$path.bak"
}

sed_in_place() {
	local path=$1
	local expression=$2

	[[ -f "$path" ]] || return 0
	backup_once "$path"
	[[ "$DRY_RUN" == false ]] || return 0
	sed -i "$expression" "$path"
}

disable_path() {
	local path=$1
	local disabled_path="${path}.disabled"

	[[ -e "$path" ]] || return 1
	[[ ! -e "$disabled_path" ]] || return 1

	if [[ "$DRY_RUN" == false ]]; then
		mv -n -- "$path" "$disabled_path"
	fi

	return 0
}

write_noop_binary() {
	local path=$1

	[[ "$DRY_RUN" == false ]] || return 0
	printf '#!/usr/bin/env bash\nexit 0\n' >"$path"
	chmod 0755 "$path"
}

disable_cloud_server() {
	local count=0
	local binary path legacy_backup

	for binary in wpscloudsvr wpscloudsrv; do
		path="${OFFICE6_DIR}/${binary}"
		legacy_backup="${path}.shit"

		if [[ -e "$legacy_backup" && ! -e "${path}.disabled" ]]; then
			if [[ "$DRY_RUN" == false ]]; then
				mv -n -- "$legacy_backup" "${path}.disabled"
			fi
			count=$((count + 1))
		fi

		if [[ -e "$path" && ! -e "${path}.disabled" ]]; then
			if [[ "$DRY_RUN" == false ]]; then
				mv -n -- "$path" "${path}.disabled"
			fi
			count=$((count + 1))
		fi

		if [[ -e "${path}.disabled" ]]; then
			write_noop_binary "$path"
		fi
	done

	printf '%s\n' "$count"
}

disable_cloud_libraries() {
	local count=0
	local library
	local libraries=(
		"${OFFICE6_DIR}/addons/qing/libqingbangong.so"
		"${OFFICE6_DIR}/addons/khyperion/libkhyperion.so"
	)

	for library in "${libraries[@]}"; do
		if disable_path "$library"; then
			count=$((count + 1))
		fi
	done

	printf '%s\n' "$count"
}

disable_rogue_binaries() {
	local count=0
	local binary

	for binary in "${ROGUE_BINS[@]}"; do
		if disable_path "${OFFICE6_DIR}/${binary}"; then
			count=$((count + 1))
		fi
	done

	printf '%s\n' "$count"
}

disable_rogue_addons() {
	local count=0
	local addon

	for addon in "${ROGUE_ADDONS[@]}"; do
		if disable_path "${OFFICE6_DIR}/addons/${addon}"; then
			count=$((count + 1))
		fi
	done

	printf '%s\n' "$count"
}

count_plugin_lines() {
	local path=$1
	local count

	count=$(grep -c '<plugin' "$path" 2>/dev/null || true)
	printf '%s\n' "${count:-0}"
}

purge_plugin_registry() {
	local path="${OFFICE6_DIR}/setupplugincfg/setupplugin.plg"
	local before=0
	local after=0
	local plugin

	[[ -f "$path" ]] || {
		printf '0 -> 0\n'
		return 0
	}

	before=$(count_plugin_lines "$path")

	if [[ "$DRY_RUN" == false ]]; then
		backup_once "$path"
		for plugin in "${ROGUE_PLUGINS[@]}"; do
			sed -i "/<plugin .*name=\"$plugin\"/d" "$path"
		done
	fi

	after=$(count_plugin_lines "$path")
	if [[ "$DRY_RUN" == true ]]; then
		printf '%s -> preview\n' "$before"
	else
		printf '%s -> %s\n' "$before" "$after"
	fi
}

fix_component_mode() {
	local office_conf=$1

	[[ -f "$office_conf" ]] || return 0

	sed_in_place "$office_conf" 's/AppComponentModeInstall=prome_fushion/AppComponentModeInstall=prome_independ/g'

	if grep -q 'AppComponentMode=prome_fushion' "$office_conf"; then
		sed_in_place "$office_conf" 's/AppComponentMode=prome_fushion/AppComponentMode=prome_independ/g'
	elif ! grep -q 'AppComponentMode=prome_independ' "$office_conf" && grep -q 'AppComponentModeInstall' "$office_conf"; then
		backup_once "$office_conf"
		if [[ "$DRY_RUN" == false ]]; then
			sed -i '/AppComponentModeInstall/i wpsoffice\\Application%20Settings\\AppComponentMode=prome_independ' "$office_conf"
		fi
	fi
}

fix_window_geometry() {
	local office_conf=$1
	local app

	[[ -f "$office_conf" ]] || return 0

	for app in wps et wpp pdf wpsoffice; do
		sed_in_place "$office_conf" "s#^${app}\\\\Application%20Settings\\\\WindowPosX=.*#${app}\\\\Application%20Settings\\\\WindowPosX=0#"
		sed_in_place "$office_conf" "s#^${app}\\\\Application%20Settings\\\\WindowPosY=.*#${app}\\\\Application%20Settings\\\\WindowPosY=0#"
		sed_in_place "$office_conf" "s#^${app}\\\\Application%20Settings\\\\WindowWidth=-1#${app}\\\\Application%20Settings\\\\WindowWidth=1600#"
		sed_in_place "$office_conf" "s#^${app}\\\\Application%20Settings\\\\WindowHeight=-1#${app}\\\\Application%20Settings\\\\WindowHeight=1000#"
		sed_in_place "$office_conf" "s#^${app}\\\\Application%20Settings\\\\WindowIsMaximized=true#${app}\\\\Application%20Settings\\\\WindowIsMaximized=false#"
	done
}

clean_office_conf() {
	local config_dir=$1
	local office_conf="${config_dir}/Office.conf"
	local expression=

	[[ -f "$office_conf" ]] || return 0

	printf -v expression '%s\\|' "${HISTORY_PATTERNS[@]}"
	expression=${expression%\\|}
	sed_in_place "$office_conf" "/$expression/d"
	fix_component_mode "$office_conf"
	fix_window_geometry "$office_conf"
}

clean_cloud_conf() {
	local config_dir=$1
	local user_home=$2
	local cloud_conf="${config_dir}/WPSCloud.conf"
	local secret_conf="${config_dir}/WPSCloud\\usercenter\\secretFolder.conf"
	local document_path="${user_home}/document/WPS Cloud Files"
	local escaped_document_path
	local flag
	local old_blob
	local new_blob

	[[ -f "$cloud_conf" ]] || return 0

	escaped_document_path=${document_path//\//\\/}
	sed_in_place "$cloud_conf" 's/true$/false/g'

	for flag in "${CLOUD_NUMERIC_FLAGS[@]}"; do
		sed_in_place "$cloud_conf" "s/${flag}=1/${flag}=0/g"
	done

	sed_in_place "$cloud_conf" "s/${escaped_document_path}/\\/tmp\\/wps/g"

	old_blob='00000001=eyJRUHVzaCI6InRydWUiLCJjcnlwdGNvb2tpZSI6InRydWUiLCJtb2JpbGVQdXNoIjoiZmFsc2UiLCJxaW5pdSI6Im9wZW4iLCJyZXN1bHQiOiJvayIsInJvYW1Ib21lcGFnZVNldHRpbmdHdWlkIjoidHJ1ZSIsInNob3dndWlkZSI6ImZhbHNlIiwidXBkYXRlVGlwSW50ZXJ2YWwiOiIzNjAwMCJ9'
	new_blob='00000001=eyJRUHVzaCI6ImZhbHNlIiwiY3J5cHRjb29raWUiOiJmYWxzZSIsIm1vYmlsZVB1c2giOiJmYWxzZSIsInFpbml1Ijoib2ZmIiwicmVzdWx0Ijoib2siLCJyb2FtSG9tZXBhZ2VTZXR0aW5nR3VpZCI6InRydWUiLCJzaG93Z3VpZGUiOiJmYWxzZSIsInVwZGF0ZVRpcEludGVydmFsIjoiMzYwMDAwMDAwMDAwMDAifQ=='
	sed_in_place "$cloud_conf" "s/${old_blob}/${new_blob}/g"

	sed_in_place "$secret_conf" 's/supportSecretFolderFunc_tmp=true/supportSecretFolderFunc_tmp=false/g'
}

kill_rogue_processes() {
	local process

	[[ "$DRY_RUN" == false ]] || return 0
	command -v pkill >/dev/null 2>&1 || return 0

	for process in "${ROGUE_BINS[@]}"; do
		pkill -9 -x "$process" 2>/dev/null || true
	done
}

run_clean() {
	local user_home
	local config_dir
	local cloud_server_count=0
	local library_count=0
	local binary_count=0
	local addon_count=0
	local plugin_summary="0 -> 0"

	if [[ "$USER_CONFIG_ONLY" == false ]]; then
		[[ -d "$OFFICE6_DIR" ]] || die "WPS office6 directory not found: $OFFICE6_DIR"
		[[ -w "$OFFICE6_DIR" ]] || die "WPS office6 directory is not writable: $OFFICE6_DIR"
	fi

	user_home=$(resolve_user_home "$TARGET_USER_NAME" "$TARGET_USER_HOME")
	config_dir="${user_home}/.config/Kingsoft"

	info "Cleaning WPS Office at $OFFICE6_DIR"
	[[ "$DRY_RUN" == false ]] || info "Dry run mode; no files will be changed."

	if [[ "$SKIP_USER_CONFIG" == false ]]; then
		clean_office_conf "$config_dir"
		clean_cloud_conf "$config_dir" "$user_home"
	fi

	if [[ "$USER_CONFIG_ONLY" == false ]]; then
		cloud_server_count=$(disable_cloud_server)
		library_count=$(disable_cloud_libraries)
		binary_count=$(disable_rogue_binaries)
		addon_count=$(disable_rogue_addons)
		plugin_summary=$(purge_plugin_registry)

		if [[ "$OFFICE6_DIR" == "${OFFICE_ROOT}/office6" ]]; then
			kill_rogue_processes
		fi
	fi

	info "Cloud server stubs prepared: $cloud_server_count"
	info "Cloud libraries disabled: $library_count"
	info "Rogue binaries disabled: $binary_count"
	info "Rogue addons disabled: $addon_count"
	info "Plugin registry lines: $plugin_summary"
	info "WPS Office clean finished."
}

show_status() {
	local disabled_binaries=0
	local disabled_addons=0
	local active_addons=0
	local plugin_registry="${OFFICE6_DIR}/setupplugincfg/setupplugin.plg"

	[[ -d "$OFFICE6_DIR" ]] || die "WPS office6 directory not found: $OFFICE6_DIR"

	disabled_binaries=$(find "$OFFICE6_DIR" -maxdepth 1 -name '*.disabled' 2>/dev/null | wc -l)
	if [[ -d "${OFFICE6_DIR}/addons" ]]; then
		disabled_addons=$(find "${OFFICE6_DIR}/addons" -maxdepth 1 -mindepth 1 -type d -name '*.disabled' 2>/dev/null | wc -l)
		active_addons=$(find "${OFFICE6_DIR}/addons" -maxdepth 1 -mindepth 1 -type d ! -name '*.disabled' 2>/dev/null | wc -l)
	fi

	printf 'WPS office6: %s\n' "$OFFICE6_DIR"
	printf 'Disabled binaries: %s\n' "$disabled_binaries"
	printf 'Disabled addons: %s\n' "$disabled_addons"
	printf 'Active addons: %s\n' "$active_addons"

	if [[ -f "$plugin_registry" ]]; then
		printf 'Plugin registry lines: %s\n' "$(count_plugin_lines "$plugin_registry")"
	fi
}

list_targets() {
	printf 'Rogue binaries (%s):\n' "${#ROGUE_BINS[@]}"
	printf '  %s\n' "${ROGUE_BINS[@]}"
	printf 'Rogue addons (%s):\n' "${#ROGUE_ADDONS[@]}"
	printf '  %s\n' "${ROGUE_ADDONS[@]}"
	printf 'Rogue plugin registry entries (%s):\n' "${#ROGUE_PLUGINS[@]}"
	printf '  %s\n' "${ROGUE_PLUGINS[@]}"
}

main() {
	local command=clean

	while [[ $# -gt 0 ]]; do
		case "$1" in
		--dry)
			DRY_RUN=true
			shift
			;;
		--office6)
			[[ $# -ge 2 ]] || die "--office6 requires a directory."
			OFFICE6_DIR=$2
			shift 2
			;;
		--user)
			[[ $# -ge 2 ]] || die "--user requires a user name."
			TARGET_USER_NAME=$2
			shift 2
			;;
		--home)
			[[ $# -ge 2 ]] || die "--home requires a directory."
			TARGET_USER_HOME=$2
			shift 2
			;;
		--skip-user-config)
			SKIP_USER_CONFIG=true
			shift
			;;
		--user-config-only)
			USER_CONFIG_ONLY=true
			shift
			;;
		--help | -h)
			usage
			return 0
			;;
		clean | all | status | list)
			command=$1
			shift
			;;
		*)
			usage
			die "Unknown argument: $1"
			;;
		esac
	done

	case "$command" in
	clean | all)
		run_clean
		;;
	status)
		show_status
		;;
	list)
		list_targets
		;;
	esac
}

main "$@"
CLEAN_SCRIPT_EOF

	chmod 0755 "$target"
	bash -n "$target"
	grep -q -- '--office6' "$target" || die "generated clean.sh does not support --office6"
	grep -q -- '--skip-user-config' "$target" || die "generated clean.sh does not support --skip-user-config"
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
privacy_mode=ask

usage() {
	printf 'Usage: %s [--link-bin] [--privacy-mode|--no-privacy-mode]\n' "${0##*/}" >&2
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

write_bin_wrappers() {
	local bin_dir="$HOME/.local/bin"

	mkdir -p -- "$portable_dir/bin"

	cat >"$portable_dir/bin/wps" <<WRAPPER_EOF
#!/usr/bin/env bash
set -Eeuo pipefail

portable_dir='$portable_dir'
privacy_mode=$privacy_mode

clean_after_exit() {
	if [[ "\$privacy_mode" == true && -x "\$portable_dir/clean.sh" ]]; then
		"\$portable_dir/clean.sh" --office6 "\$portable_dir/office6" --home "\$HOME" --user-config-only clean >/dev/null 2>&1 || true
	fi
}

run_app() {
	local status=0

	set +e
	"\$@"
	status=\$?
	set -e

	clean_after_exit
	exit "\$status"
}

if [[ \$# -gt 0 ]]; then
	first_arg=\${1#file://}
	extension=\${first_arg##*.}
	extension=\$(printf '%s' "\$extension" | tr '[:upper:]' '[:lower:]')

	case "\$extension" in
	xls | xlsx | xlsm | xlsb | csv | et | ett | xlt | xltx | xltm | uos | uos3)
		run_app "\$portable_dir/office6/et" "\$@"
		;;
	ppt | pptx | pptm | dps | dpt | pot | potx | potm | uop | uop3)
		run_app "\$portable_dir/office6/wpp" "\$@"
		;;
	pdf)
		run_app "\$portable_dir/office6/wpspdf" "\$@"
		;;
	esac
fi

run_app "\$portable_dir/office6/wps" "\$@"
WRAPPER_EOF

	cat >"$portable_dir/bin/et" <<WRAPPER_EOF
#!/usr/bin/env bash
set -Eeuo pipefail

portable_dir='$portable_dir'
privacy_mode=$privacy_mode

set +e
"\$portable_dir/office6/et" "\$@"
status=\$?
set -e

if [[ "\$privacy_mode" == true && -x "\$portable_dir/clean.sh" ]]; then
	"\$portable_dir/clean.sh" --office6 "\$portable_dir/office6" --home "\$HOME" --user-config-only clean >/dev/null 2>&1 || true
fi

exit "\$status"
WRAPPER_EOF

	cat >"$portable_dir/bin/wpp" <<WRAPPER_EOF
#!/usr/bin/env bash
set -Eeuo pipefail

portable_dir='$portable_dir'
privacy_mode=$privacy_mode

set +e
"\$portable_dir/office6/wpp" "\$@"
status=\$?
set -e

if [[ "\$privacy_mode" == true && -x "\$portable_dir/clean.sh" ]]; then
	"\$portable_dir/clean.sh" --office6 "\$portable_dir/office6" --home "\$HOME" --user-config-only clean >/dev/null 2>&1 || true
fi

exit "\$status"
WRAPPER_EOF

	cat >"$portable_dir/bin/wpspdf" <<WRAPPER_EOF
#!/usr/bin/env bash
set -Eeuo pipefail

portable_dir='$portable_dir'
privacy_mode=$privacy_mode

set +e
"\$portable_dir/office6/wpspdf" "\$@"
status=\$?
set -e

if [[ "\$privacy_mode" == true && -x "\$portable_dir/clean.sh" ]]; then
	"\$portable_dir/clean.sh" --office6 "\$portable_dir/office6" --home "\$HOME" --user-config-only clean >/dev/null 2>&1 || true
fi

exit "\$status"
WRAPPER_EOF

	chmod 0755 "$portable_dir/bin/wps" "$portable_dir/bin/et" "$portable_dir/bin/wpp" "$portable_dir/bin/wpspdf"

	if [[ "$link_bin" == true ]]; then
		mkdir -p -- "$bin_dir"
		ln -sfn -- "$portable_dir/bin/wps" "$bin_dir/wps"
		ln -sfn -- "$portable_dir/bin/et" "$bin_dir/et"
		ln -sfn -- "$portable_dir/bin/wpp" "$bin_dir/wpp"
		ln -sfn -- "$portable_dir/bin/wpspdf" "$bin_dir/wpspdf"
	fi
}

register_mime_defaults() {
	local mime_type
	local writer_mimes=(
		application/wps-office.docx
		application/wps-office.doc
		application/vnd.openxmlformats-officedocument.wordprocessingml.document
		application/msword
		application/wps-office.wps
		application/wps-office.dotx
		application/wps-office.dot
		application/rtf
	)
	local spreadsheet_mimes=(
		application/wps-office.xlsx
		application/wps-office.xls
		application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
		application/vnd.ms-excel
		application/wps-office.et
		application/wps-office.ett
		text/csv
	)
	local presentation_mimes=(
		application/wps-office.pptx
		application/wps-office.ppt
		application/vnd.openxmlformats-officedocument.presentationml.presentation
		application/vnd.ms-powerpoint
		application/wps-office.dps
		application/wps-office.dpt
	)

	command -v xdg-mime >/dev/null 2>&1 || return 0
	mkdir -p -- "$HOME/.config"

	for mime_type in "${writer_mimes[@]}"; do
		xdg-mime default wps-office-wps.desktop "$mime_type"
	done

	for mime_type in "${spreadsheet_mimes[@]}"; do
		xdg-mime default wps-office-et.desktop "$mime_type"
	done

	for mime_type in "${presentation_mimes[@]}"; do
		xdg-mime default wps-office-wpp.desktop "$mime_type"
	done

	xdg-mime default wps-office-pdf.desktop application/pdf
}

generate_uninstaller() {
	local target="$portable_dir/uninstall.sh"

	cat >"$target" <<'UNINSTALL_EOF'
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
	local target_path

	for bin_name in "${bin_names[@]}"; do
		path="$HOME/.local/bin/$bin_name"
		[[ -e "$path" || -L "$path" ]] || continue

		if [[ -L "$path" ]]; then
			target_path=$(readlink -f -- "$path" 2>/dev/null || true)
			if [[ "$target_path" == "$portable_dir/"* ]]; then
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
UNINSTALL_EOF

	chmod 0755 "$target"
}

prompt_privacy_mode() {
	local answer=

	if [[ "$privacy_mode" != ask ]]; then
		return 0
	fi

	if [[ ! -t 0 ]]; then
		privacy_mode=false
		return 0
	fi

	printf 'Enable privacy mode and clean WPS user data after each exit? (y/N) '
	read -r answer

	case "$answer" in
	y | Y | yes | YES)
		privacy_mode=true
		;;
	*)
		privacy_mode=false
		;;
	esac
}

while [[ $# -gt 0 ]]; do
	case "$1" in
	--link-bin)
		link_bin=true
		shift
		;;
	--privacy-mode)
		privacy_mode=true
		shift
		;;
	--no-privacy-mode)
		privacy_mode=false
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

prompt_privacy_mode
generate_uninstaller
write_bin_wrappers
generate_desktops "$portable_dir/bin" "$portable_dir/share/icons" "$portable_dir/share/applications"

mkdir -p -- "$applications_dir"
cp -af -- "$portable_dir/share/applications/"*.desktop "$applications_dir/"
register_mime_defaults

if [[ -d "$portable_dir/share/fonts/wps-office" ]]; then
	mkdir -p -- "$fonts_dir"
	cp -an -- "$portable_dir/share/fonts/wps-office/"* "$fonts_dir/" 2>/dev/null || true
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
info "Run $portable_dir/install-local.sh again any time to change desktop, bin link, or privacy-mode choices."
info "Portable directory: $portable_dir"
EOF

	chmod 0755 "$installer_path"
}

generate_uninstaller() {
	local target="$install_dir/uninstall.sh"

	cat >"$target" <<'EOF'
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
	local target_path

	for bin_name in "${bin_names[@]}"; do
		path="$HOME/.local/bin/$bin_name"
		[[ -e "$path" || -L "$path" ]] || continue

		if [[ -L "$path" ]]; then
			target_path=$(readlink -f -- "$path" 2>/dev/null || true)
			if [[ "$target_path" == "$portable_dir/"* ]]; then
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
EOF

	chmod 0755 "$target"
}

prompt_register_desktop() {
	local answer=
	local local_installer="$install_dir/install-local.sh"

	if [[ ! -t 0 ]]; then
		return 0
	fi

	printf 'Register .desktop links now? (y/N) '
	read -r answer

	case "$answer" in
	y | Y | yes | YES)
		"$local_installer" --link-bin
		;;
	*)
		info "Skipped desktop registration."
		;;
	esac
}

build_portable() {
	local extract_dir
	local package_root
	local wps_root

	require_command dpkg-deb
	prepare_tmp_dir
	safe_prepare_install_dir
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

	info "Generating clean helper."
	generate_clean_helper "$install_dir/clean.sh"

	info "Purging portable office6."
	"$install_dir/clean.sh" --office6 "$install_dir/office6" --skip-user-config clean

	info "Generating target-machine installer."
	generate_local_installer

	info "Generating uninstall helper."
	generate_uninstaller

	info "Portable WPS is ready: $install_dir"
	prompt_register_desktop
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
