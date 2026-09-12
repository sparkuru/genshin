#!/usr/bin/env bash

set -Eeuo pipefail
umask 077

script_path=${BASH_SOURCE[0]}
script_dir=${script_path%/*}
if [[ "$script_dir" == "$script_path" ]]; then
	script_dir=.
fi
script_dir_path="$(cd -- "$script_dir" && pwd -P)"
readonly SCRIPT_DIR="$script_dir_path"
readonly SCRIPT_PATH="$SCRIPT_DIR/status.sh"

# shellcheck disable=SC1091  # The helper is shipped next to this script.
source "$SCRIPT_DIR/lib.sh"

requested_name=""
overall_failure=0

usage() {
	printf '%s\n' "$(color_text "$STYLE_TITLE" "Usage:")"
	printf '  sudo %s [--name collab-*]\n\n' "$SCRIPT_PATH"
	printf '%s\n' "$(color_text "$STYLE_TITLE" "Options:")"
	printf '  --name NAME              Show one managed account\n'
	printf '  -h, --help               Show this help\n'
}

parse_args() {
	while (($# > 0)); do
		case "$1" in
		--name)
			(($# >= 2)) || die "--name requires a value"
			requested_name=$2
			shift 2
			;;
		--name=*)
			requested_name=${1#*=}
			shift
			;;
		--)
			shift
			(($# == 0)) || die "unexpected positional argument: $1"
			;;
		-h | --help)
			usage
			exit 0
			;;
		-*)
			die "unknown option: $1"
			;;
		*)
			die "unexpected positional argument: $1"
			;;
		esac
	done
}

display_state() {
	local state_path=$1
	local state_version
	local state_status
	local state_username
	local state_user_uid
	local state_group_name
	local state_group_gid
	local state_home_dir
	local state_authorized_keys_path
	local state_sudoers_path
	local state_sudo_mode
	local state_service_unit
	local state_timer_unit
	local state_auto_revoke
	local state_expires_epoch
	local state_key_fingerprint
	local account_state
	local current_uid
	local sudo_state
	local timer_state
	local expiry_state
	local now_epoch

	if ! state_file_is_safe "$state_path"; then
		warn "ignoring unsafe state file: $state_path"
		return 1
	fi
	if ! state_version=$(read_state_value version "$state_path") || ! state_status=$(read_state_value status "$state_path") || ! state_username=$(read_state_value username "$state_path") || ! state_user_uid=$(read_state_value user_uid "$state_path") || ! state_group_name=$(read_state_value group_name "$state_path") || ! state_group_gid=$(read_state_value group_gid "$state_path") || ! state_home_dir=$(read_state_value home_dir "$state_path") || ! state_authorized_keys_path=$(read_state_value authorized_keys_path "$state_path") || ! state_sudoers_path=$(read_state_value sudoers_path "$state_path") || ! state_sudo_mode=$(read_state_value sudo_mode "$state_path") || ! state_service_unit=$(read_state_value service_unit "$state_path") || ! state_timer_unit=$(read_state_value timer_unit "$state_path") || ! state_auto_revoke=$(read_state_value auto_revoke "$state_path") || ! state_expires_epoch=$(read_state_value expires_epoch "$state_path") || ! state_key_fingerprint=$(read_state_value key_fingerprint "$state_path"); then
		warn "ignoring incomplete state file: $state_path"
		return 1
	fi
	if [[ "$state_version" != 1 || "$state_username" != "$state_group_name" ]]; then
		warn "ignoring malformed state file: $state_path"
		return 1
	fi
	case "$state_status" in
	active | provisioning | revoking | revoke-partial) ;;
	*)
		warn "ignoring malformed state file: $state_path"
		return 1
		;;
	esac
	if ! is_valid_username "$state_username" || [[ ! "$state_group_gid" =~ ^[0-9]+$ ]] || [[ -n "$state_user_uid" && ! "$state_user_uid" =~ ^[0-9]+$ ]]; then
		warn "ignoring malformed state file: $state_path"
		return 1
	fi
	if [[ "$state_home_dir" != "/home/$state_username" || "$state_authorized_keys_path" != "$state_home_dir/.ssh/authorized_keys" || "$state_sudoers_path" != "${SUDOERS_PREFIX}${state_username}" ]]; then
		warn "ignoring state file with unexpected paths: $state_path"
		return 1
	fi
	case "$state_sudo_mode" in
	none | full-root) ;;
	*)
		warn "ignoring state file with invalid sudo mode: $state_path"
		return 1
		;;
	esac
	case "$state_auto_revoke" in
	manual)
		[[ -z "$state_service_unit" && -z "$state_timer_unit" ]] || {
			warn "ignoring state file with unexpected systemd units: $state_path"
			return 1
		}
		;;
	systemd)
		[[ "$state_service_unit" == "mtf-aid-revoke-${state_username}.service" && "$state_timer_unit" == "mtf-aid-revoke-${state_username}.timer" ]] || {
			warn "ignoring state file with invalid systemd units: $state_path"
			return 1
		}
		;;
	*)
		warn "ignoring state file with invalid automatic revoke mode: $state_path"
		return 1
		;;
	esac

	account_state=absent
	current_uid=-
	if user_exists "$state_username"; then
		account_state=present
		current_uid=$(id -u "$state_username")
	fi
	if [[ "$state_sudo_mode" == full-root ]]; then
		if [[ -e "$state_sudoers_path" || -L "$state_sudoers_path" ]]; then
			sudo_state=installed
		else
			sudo_state=missing
		fi
	else
		sudo_state=none
	fi

	if [[ "$state_auto_revoke" == systemd ]]; then
		timer_state=not-scheduled
		if command -v systemctl >/dev/null 2>&1 && systemctl is-active --quiet "$state_timer_unit"; then
			timer_state=scheduled
		fi
	else
		timer_state=manual
	fi

	expiry_state=unknown
	if [[ "$state_expires_epoch" =~ ^[0-9]+$ ]]; then
		now_epoch=$(date +%s)
		if ((now_epoch >= state_expires_epoch)); then
			expiry_state=expired
		else
			expiry_state=active
		fi
	fi

	printf '%s\n' "$(color_text "$STYLE_TITLE" "$state_username")"
	printf '  state: %s\n' "$state_status"
	printf '  account: %s (uid=%s)\n' "$account_state" "${state_user_uid:-unknown}/$current_uid"
	printf '  group: %s (gid=%s)\n' "$state_group_name" "$state_group_gid"
	printf '  home: %s\n' "$state_home_dir"
	printf '  sudo: %s\n' "$sudo_state"
	printf '  expiry: %s (%s)\n' "$(format_epoch "$state_expires_epoch")" "$expiry_state"
	printf '  automatic revoke: %s\n' "$timer_state"
	if [[ "$state_auto_revoke" == systemd ]]; then
		printf '  timer unit: %s\n' "$state_timer_unit"
	fi
	printf '  key fingerprint: %s\n' "$state_key_fingerprint"
}

main() {
	parse_args "$@"
	ensure_root "$SCRIPT_PATH" "$@"

	local command_name
	for command_name in awk date getent id stat; do
		require_command "$command_name"
	done
	[[ -d "$STATE_DIR" ]] || {
		info "No managed collaboration accounts found."
		return 0
	}
	state_dir_is_safe || die "state directory must be owned by root with mode 700: $STATE_DIR"

	local -a state_files=()
	local state_path
	if [[ -n "$requested_name" ]]; then
		validate_username "$requested_name"
		state_path=$(state_path_for "$requested_name")
		[[ -f "$state_path" && ! -L "$state_path" ]] || die "no managed state found for account: $requested_name"
		state_files=("$state_path")
	else
		for state_path in "$STATE_DIR"/collab-*.state; do
			[[ -f "$state_path" && ! -L "$state_path" ]] || continue
			state_files+=("$state_path")
		done
		if ((${#state_files[@]} == 0)); then
			info "No managed collaboration accounts found."
			return 0
		fi
	fi

	for state_path in "${state_files[@]}"; do
		display_state "$state_path" || overall_failure=1
	done
	return "$overall_failure"
}

main "$@"
