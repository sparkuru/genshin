#!/usr/bin/env bash
set -Eeuo pipefail

readonly SCRIPT_NAME="${0##*/}"
readonly SMB_USER='wkyuu'
readonly CONFIG_PATH='/etc/samba/smb.conf'
readonly TMP_SHARE='/tmp/tmp'
readonly HOME_SHARE='/home/wkyuu'
readonly CONFIG_BEGIN='# BEGIN genshin-managed SMB shares'
readonly CONFIG_END='# END genshin-managed SMB shares'

readonly STYLE_RESET=$'\033[0m'
readonly STYLE_SUCCESS=$'\033[0;32m'
readonly STYLE_WARNING=$'\033[1;33m'
readonly STYLE_ERROR=$'\033[1;31m'

action='start'
set_password=false
config_changed=false
work_file=''
share_block_file=''

color_text() {
	local style=$1
	local message=$2

	if [[ -n "${NO_COLOR:-}" || ! -t 1 ]]; then
		printf '%s' "$message"
		return 0
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

usage() {
	printf '%s\n' \
		"Usage: $SCRIPT_NAME [--set-password|--stop|--status|--help]" \
		'' \
		'Start Samba manually and expose the /tmp/tmp and /home/wkyuu shares.' \
		'' \
		'Options:' \
		'  --set-password  Set or add the Samba password for wkyuu.' \
		'  --stop          Stop the Samba service.' \
		'  --status        Show the Samba service status.' \
		'  --help           Show this help message.'
}

require_command() {
	command -v "$1" >/dev/null 2>&1 || die "Required command not found: $1"
}

cleanup() {
	if [[ -n "$work_file" && -e "$work_file" ]]; then
		rm -f -- "$work_file"
	fi
	if [[ -n "$share_block_file" && -e "$share_block_file" ]]; then
		rm -f -- "$share_block_file"
	fi
}

parse_options() {
	while (($# > 0)); do
		case "$1" in
		--set-password)
			set_password=true
			;;
		--stop)
			action='stop'
			;;
		--status)
			action='status'
			;;
		--help | -h)
			usage
			exit 0
			;;
		--)
			shift
			break
			;;
		-* | *)
			die "Unknown option: $1"
			;;
		esac
		shift
	done

	(($# == 0)) || die 'Unexpected positional argument.'
	[[ "$action" == 'start' || "$set_password" == false ]] ||
		die '--set-password can only be used while starting Samba.'
}

escalate_if_needed() {
	((EUID == 0)) && return 0

	require_command sudo
	require_command readlink

	local script_path
	script_path=$(readlink -f -- "$0") || die 'Could not resolve the script path.'
	exec sudo -- "$script_path" "$@"
}

systemd_available() {
	[[ -d /run/systemd/system ]] || return 1
	command -v systemctl >/dev/null 2>&1 || return 1
	systemctl show --property=Version --value >/dev/null 2>&1
}

unit_file_exists() {
	local unit=$1
	local unit_path

	for unit_path in \
		"/etc/systemd/system/$unit" \
		"/run/systemd/system/$unit" \
		"/usr/lib/systemd/system/$unit" \
		"/lib/systemd/system/$unit"; do
		[[ -e "$unit_path" ]] && return 0
	done

	return 1
}

get_systemd_unit() {
	local unit

	for unit in smbd.service smb.service; do
		if unit_file_exists "$unit"; then
			printf '%s\n' "$unit"
			return 0
		fi
	done

	return 1
}

get_sysv_service() {
	local service_name

	for service_name in smbd smb; do
		if [[ -x "/etc/init.d/$service_name" ]]; then
			printf '%s\n' "$service_name"
			return 0
		fi
	done

	return 1
}

disable_unit_if_enabled() {
	local unit=$1
	local state

	unit_file_exists "$unit" || return 0

	if state=$(systemctl is-enabled "$unit" 2>/dev/null); then
		case "$state" in
		enabled | enabled-runtime | alias)
			systemctl disable "$unit" >/dev/null
			info "Disabled automatic start for $unit."
			;;
		esac
	fi
}

disable_autostart() {
	local unit

	if ! systemd_available; then
		return 0
	fi

	for unit in \
		smbd.service \
		smb.service \
		nmbd.service \
		nmb.service \
		smbd.socket \
		smb.socket; do
		disable_unit_if_enabled "$unit"
	done
}

write_share_block() {
	printf '%s\n' \
		'' \
		"$CONFIG_BEGIN" \
		'[tmp]' \
		'   comment = Temporary files' \
		"   path = $TMP_SHARE" \
		'   browseable = yes' \
		'   read only = no' \
		'   guest ok = no' \
		"   valid users = $SMB_USER" \
		'   create mask = 0664' \
		'   directory mask = 0775' \
		'' \
		'[wkyuu]' \
		'   comment = Wkyuu home directory' \
		"   path = $HOME_SHARE" \
		'   browseable = yes' \
		'   read only = no' \
		'   guest ok = no' \
		"   valid users = $SMB_USER" \
		'   create mask = 0664' \
		'   directory mask = 0775' \
		"$CONFIG_END"
}

install_config() {
	local generated_file=$1
	local success_message=$2

	testparm -s "$generated_file" >/dev/null || die 'Generated Samba configuration failed validation.'

	if [[ -f "$CONFIG_PATH" && ! -e "${CONFIG_PATH}.genshin.bak" ]]; then
		cp -a -- "$CONFIG_PATH" "${CONFIG_PATH}.genshin.bak"
		info "Backed up the original configuration to ${CONFIG_PATH}.genshin.bak."
	fi

	install -m 0644 -- "$generated_file" "$CONFIG_PATH"
	config_changed=true
	info "$success_message"
}

ensure_share_config() {
	require_command awk
	require_command cp
	require_command grep
	require_command install
	require_command id
	require_command mkdir
	require_command mktemp
	require_command rm
	require_command testparm

	[[ -d "$TMP_SHARE" ]] || die "Share path does not exist: $TMP_SHARE"
	[[ -d "$HOME_SHARE" ]] || die "Share path does not exist: $HOME_SHARE"
	id "$SMB_USER" >/dev/null 2>&1 || die "Unix user does not exist: $SMB_USER"

	if [[ -f "$CONFIG_PATH" ]] && grep -Fq -- "$CONFIG_BEGIN" "$CONFIG_PATH"; then
		grep -Fq -- "$CONFIG_END" "$CONFIG_PATH" ||
			die "Incomplete managed Samba share block in $CONFIG_PATH."

		work_file=$(mktemp "${TMPDIR:-/tmp/tmp}/genshin-smb.XXXXXXXX")
		share_block_file=$(mktemp "${TMPDIR:-/tmp/tmp}/genshin-smb-block.XXXXXXXX")
		write_share_block >"$share_block_file"

		if ! awk \
			-v begin="$CONFIG_BEGIN" \
			-v end="$CONFIG_END" \
			-v replacement="$share_block_file" '
			$0 == begin {
				while ((getline replacement_line < replacement) > 0) {
					print replacement_line
				}
				close(replacement)
				in_block = 1
				next
			}
			$0 == end {
				in_block = 0
				next
			}
			!in_block { print }
			END {
				if (in_block) {
					exit 2
				}
			}
		' "$CONFIG_PATH" >"$work_file"; then
			die "Could not replace the managed Samba share block."
		fi

		install_config "$work_file" 'Updated Samba share configuration.'
		return 0
	fi

	if [[ -f "$CONFIG_PATH" ]] && grep -Eq '^[[:space:]]*\[(tmp|wkyuu)\][[:space:]]*$' "$CONFIG_PATH"; then
		die "Share name [tmp] or [wkyuu] already exists in $CONFIG_PATH; refusing to overwrite it."
	fi

	work_file=$(mktemp "${TMPDIR:-/tmp/tmp}/genshin-smb.XXXXXXXX")
	if [[ -f "$CONFIG_PATH" ]]; then
		cp -- "$CONFIG_PATH" "$work_file"
	else
		mkdir -p /etc/samba
		printf '%s\n' '[global]' '   server role = standalone server' >"$work_file"
	fi

	write_share_block >>"$work_file"
	install_config "$work_file" 'Configured Samba shares.'
}

set_smb_password() {
	require_command smbpasswd

	info "Set the Samba password for $SMB_USER."
	if ! smbpasswd "$SMB_USER"; then
		smbpasswd -a "$SMB_USER"
	fi
}

start_samba() {
	require_command smbd

	local restart_required=${1:-false}
	local unit=''
	local service_name=''

	if systemd_available && unit=$(get_systemd_unit); then
		if [[ "$restart_required" == true ]]; then
			systemctl restart "$unit"
			info "Restarted Samba service after configuration update: $unit."
		else
			systemctl start "$unit"
			info "Started Samba service: $unit."
		fi
		return 0
	fi

	if service_name=$(get_sysv_service); then
		require_command service
		if [[ "$restart_required" == true ]]; then
			service "$service_name" restart
			info "Restarted Samba service after configuration update: $service_name."
		else
			service "$service_name" start
			info "Started Samba service: $service_name."
		fi
		return 0
	fi

	if command -v pgrep >/dev/null 2>&1 && pgrep -x smbd >/dev/null 2>&1; then
		if [[ "$restart_required" == true ]]; then
			if command -v smbcontrol >/dev/null 2>&1; then
				smbcontrol all reload-config
			elif command -v pkill >/dev/null 2>&1; then
				pkill -HUP -x smbd
			else
				warn 'Samba configuration changed, but no reload command is available.'
			fi
		fi
		info 'Samba is already running.'
		return 0
	fi

	smbd -D
	info 'Started Samba directly in daemon mode.'
}

stop_samba() {
	local unit=''
	local service_name=''

	if systemd_available && unit=$(get_systemd_unit); then
		systemctl stop "$unit"
		info "Stopped Samba service: $unit."
		return 0
	fi

	if service_name=$(get_sysv_service); then
		require_command service
		service "$service_name" stop
		info "Stopped Samba service: $service_name."
		return 0
	fi

	if command -v smbcontrol >/dev/null 2>&1; then
		smbcontrol all shutdown
		info 'Requested Samba shutdown.'
		return 0
	fi

	require_command pgrep
	require_command pkill
	if pgrep -x smbd >/dev/null 2>&1; then
		pkill -TERM -x smbd
		info 'Stopped Samba processes.'
	else
		info 'Samba is not running.'
	fi
}

status_samba() {
	local unit=''
	local service_name=''

	if systemd_available && unit=$(get_systemd_unit); then
		systemctl --no-pager --full status "$unit"
		return $?
	fi

	if service_name=$(get_sysv_service); then
		require_command service
		service "$service_name" status
		return $?
	fi

	require_command pgrep
	if pgrep -x smbd >/dev/null 2>&1; then
		info 'Samba is running.'
	else
		warn 'Samba is not running.'
		return 3
	fi
}

main() {
	local -a original_args=("$@")

	parse_options "$@"
	escalate_if_needed "${original_args[@]}"

	case "$action" in
	start)
		disable_autostart
		ensure_share_config
		if [[ "$set_password" == true ]]; then
			set_smb_password
		fi
		start_samba "$config_changed"
		info 'Shares: \\<linux-host>\tmp and \\<linux-host>\wkyuu.'
		info 'Run this script again after the next reboot; Samba is not enabled for autostart.'
		;;
	stop)
		stop_samba
		;;
	status)
		status_samba
		;;
	esac
}

trap cleanup EXIT
main "$@"
