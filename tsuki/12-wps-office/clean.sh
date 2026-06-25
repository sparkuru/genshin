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
	konlinefileconfig
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

clean_office_conf() {
	local config_dir=$1
	local office_conf="${config_dir}/Office.conf"
	local expression=

	[[ -f "$office_conf" ]] || return 0

	printf -v expression '%s\\|' "${HISTORY_PATTERNS[@]}"
	expression=${expression%\\|}
	sed_in_place "$office_conf" "/$expression/d"
	fix_component_mode "$office_conf"
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
