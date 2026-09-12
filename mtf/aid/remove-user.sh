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
readonly SCRIPT_PATH="$SCRIPT_DIR/remove-user.sh"

# shellcheck disable=SC1091  # The helper is shipped next to this script.
source "$SCRIPT_DIR/lib.sh"

username=""
assume_yes=false
automatic=false

state_path=""
state_status=""
state_username=""
state_user_uid=""
state_group_name=""
state_group_gid=""
state_home_dir=""
state_authorized_keys_path=""
state_sudoers_path=""
state_sudo_mode=""
state_service_unit=""
state_timer_unit=""
state_service_unit_path=""
state_timer_unit_path=""
state_auto_revoke=""
identity_safe=true
failure=0

usage() {
	printf '%s\n' "$(color_text "$STYLE_TITLE" "Usage:")"
	printf '  sudo %s --name collab-* [--yes]\n\n' "$SCRIPT_PATH"
	printf '%s\n' "$(color_text "$STYLE_TITLE" "Options:")"
	printf '  --name NAME              Managed account to revoke (required)\n'
	printf '  --yes                    Skip the confirmation prompt\n'
	printf '  -h, --help               Show this help\n'
}

parse_args() {
	while (($# > 0)); do
		case "$1" in
		--name)
			(($# >= 2)) || die "--name requires a value"
			username=$2
			shift 2
			;;
		--name=*)
			username=${1#*=}
			shift
			;;
		--yes)
			assume_yes=true
			shift
			;;
		--auto)
			automatic=true
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

read_state() {
	state_status=$(read_state_value status "$state_path") || die "state file is missing the status field"
	state_username=$(read_state_value username "$state_path") || die "state file is missing the username field"
	state_user_uid=$(read_state_value user_uid "$state_path") || die "state file is missing the user_uid field"
	state_group_name=$(read_state_value group_name "$state_path") || die "state file is missing the group_name field"
	state_group_gid=$(read_state_value group_gid "$state_path") || die "state file is missing the group_gid field"
	state_home_dir=$(read_state_value home_dir "$state_path") || die "state file is missing the home_dir field"
	state_authorized_keys_path=$(read_state_value authorized_keys_path "$state_path") || die "state file is missing the authorized_keys_path field"
	state_sudoers_path=$(read_state_value sudoers_path "$state_path") || die "state file is missing the sudoers_path field"
	state_sudo_mode=$(read_state_value sudo_mode "$state_path") || die "state file is missing the sudo_mode field"
	state_service_unit=$(read_state_value service_unit "$state_path") || die "state file is missing the service_unit field"
	state_timer_unit=$(read_state_value timer_unit "$state_path") || die "state file is missing the timer_unit field"
	state_auto_revoke=$(read_state_value auto_revoke "$state_path") || die "state file is missing the auto_revoke field"
}

validate_state() {
	local state_version

	state_version=$(read_state_value version "$state_path") || die "state file is missing the version field"
	[[ "$state_version" == 1 ]] || die "unsupported state version: $state_version"
	case "$state_status" in
	active | provisioning | revoking | revoke-partial) ;;
	*) die "unsupported state status: $state_status" ;;
	esac
	[[ "$state_username" == "$username" ]] || die "state/account name mismatch"
	[[ "$state_group_name" == "$username" ]] || die "state group name is unexpected"
	[[ "$state_group_gid" =~ ^[0-9]+$ ]] || die "state group ID is invalid"
	[[ -z "$state_user_uid" || "$state_user_uid" =~ ^[0-9]+$ ]] || die "state account ID is invalid"
	[[ "$state_home_dir" == "/home/$username" ]] || die "state home path is unexpected"
	[[ "$state_authorized_keys_path" == "$state_home_dir/.ssh/authorized_keys" ]] || die "state SSH key path is unexpected"
	[[ "$state_sudoers_path" == "${SUDOERS_PREFIX}${username}" ]] || die "state sudoers path is unexpected"
	case "$state_sudo_mode" in
	none | full-root) ;;
	*) die "state sudo mode is invalid: $state_sudo_mode" ;;
	esac
	case "$state_auto_revoke" in
	manual)
		[[ -z "$state_service_unit" && -z "$state_timer_unit" ]] || die "manual state contains systemd units"
		;;
	systemd)
		[[ "$state_service_unit" == "mtf-aid-revoke-${username}.service" ]] || die "state service unit is unexpected"
		[[ "$state_timer_unit" == "mtf-aid-revoke-${username}.timer" ]] || die "state timer unit is unexpected"
		state_service_unit_path="/etc/systemd/system/$state_service_unit"
		state_timer_unit_path="/etc/systemd/system/$state_timer_unit"
		;;
	*) die "state automatic revoke mode is invalid: $state_auto_revoke" ;;
	esac
}

confirm_removal() {
	local confirmation

	if [[ "$assume_yes" == true || "$automatic" == true ]]; then
		return 0
	fi
	[[ -t 0 ]] || die "non-interactive removal requires --yes"
	printf 'Type %s to confirm account removal: ' "$username" >&2
	if ! read -r confirmation; then
		die "confirmation was not received"
	fi
	[[ "$confirmation" == "$username" ]] || die "confirmation did not match the account name"
}

remove_sudoers_file() {
	if [[ ! -e "$state_sudoers_path" && ! -L "$state_sudoers_path" ]]; then
		return 0
	fi
	if [[ -d "$state_sudoers_path" && ! -L "$state_sudoers_path" ]]; then
		warn "expected sudoers file is a directory; leaving it in place: $state_sudoers_path"
		return 1
	fi
	if [[ -L "$state_sudoers_path" ]]; then
		warn "sudoers path became a symlink; removing the symlink only: $state_sudoers_path"
	fi
	rm -f -- "$state_sudoers_path"
}

stop_revoke_units() {
	[[ "$state_auto_revoke" == systemd ]] || return 0
	require_command systemctl
	if ! disable_systemd_unit_if_present "$state_timer_unit"; then
		warn "could not stop automatic revoke timer: $state_timer_unit"
		failure=1
	fi
	if [[ "$automatic" != true ]] && ! stop_systemd_unit_if_present "$state_service_unit"; then
		warn "could not stop automatic revoke service: $state_service_unit"
		failure=1
	fi
}

remove_systemd_unit_files() {
	local cleanup_ok=true

	if [[ -L "$state_timer_unit_path" || -f "$state_timer_unit_path" ]]; then
		rm -f -- "$state_timer_unit_path" || cleanup_ok=false
	elif [[ -e "$state_timer_unit_path" ]]; then
		warn "expected timer unit path is not a file: $state_timer_unit_path"
		cleanup_ok=false
	fi
	if [[ -L "$state_service_unit_path" || -f "$state_service_unit_path" ]]; then
		rm -f -- "$state_service_unit_path" || cleanup_ok=false
	elif [[ -e "$state_service_unit_path" ]]; then
		warn "expected service unit path is not a file: $state_service_unit_path"
		cleanup_ok=false
	fi
	systemctl daemon-reload || cleanup_ok=false
	if [[ "$cleanup_ok" != true ]]; then
		return 1
	fi
}

revoke_units_active() {
	if systemctl is-active --quiet "$state_timer_unit"; then
		return 0
	fi
	if [[ "$automatic" != true ]] && systemctl is-active --quiet "$state_service_unit"; then
		return 0
	fi
	return 1
}

validate_current_account() {
	local current_uid
	local current_home

	if ! user_exists "$username"; then
		return 0
	fi

	current_uid=$(id -u "$username")
	if [[ -n "$state_user_uid" && "$current_uid" != "$state_user_uid" ]]; then
		warn "account ID changed from $state_user_uid to $current_uid; refusing to delete the account"
		identity_safe=false
		failure=1
	fi
	current_home=$(user_home_dir "$username")
	if [[ "$current_home" != "$state_home_dir" ]]; then
		warn "account home changed from $state_home_dir to $current_home; account will be deleted without recursive home removal"
	fi
}

remove_account() {
	local current_home

	if ! user_exists "$username"; then
		return 0
	fi

	current_home=$(user_home_dir "$username")
	if [[ "$current_home" == "$state_home_dir" && ! -L "$state_home_dir" ]]; then
		if ! userdel --remove -- "$username"; then
			warn "userdel could not remove the account and home: $username"
			failure=1
		fi
	else
		if ! userdel -- "$username"; then
			warn "userdel could not remove the account: $username"
			failure=1
		fi
	fi
	if user_exists "$username"; then
		warn "account still exists after userdel: $username"
		failure=1
	fi
}

remove_group() {
	local current_gid
	local members

	if ! group_exists "$state_group_name"; then
		return 0
	fi
	current_gid=$(get_group_gid "$state_group_name")
	if [[ "$current_gid" != "$state_group_gid" ]]; then
		warn "group ID changed from $state_group_gid to $current_gid; refusing to delete the group"
		failure=1
		return 0
	fi
	members=$(get_group_members "$state_group_name")
	if [[ -n "$members" ]] || has_primary_group_users "$state_group_gid"; then
		warn "group has other members or primary users; leaving it in place: $state_group_name"
		failure=1
		return 0
	fi
	if ! groupdel -- "$state_group_name"; then
		warn "could not remove the group: $state_group_name"
		failure=1
	fi
}

remove_leftover_home_path() {
	if [[ -L "$state_home_dir" ]]; then
		rm -f -- "$state_home_dir" || failure=1
	elif [[ -e "$state_home_dir" ]]; then
		warn "home directory remains for manual inspection: $state_home_dir"
		failure=1
	fi
}

verify_revocation() {
	if user_exists "$username"; then
		failure=1
	fi
	if group_exists "$state_group_name"; then
		failure=1
	fi
	if [[ -e "$state_sudoers_path" || -L "$state_sudoers_path" ]]; then
		warn "sudoers path still exists: $state_sudoers_path"
		failure=1
	fi
	if [[ -e "$state_home_dir" || -L "$state_home_dir" ]]; then
		warn "home path still exists: $state_home_dir"
		failure=1
	fi
	if [[ "$state_auto_revoke" == systemd ]]; then
		if revoke_units_active; then
			warn "automatic revoke unit is still active"
			failure=1
		fi
	fi
}

cleanup_shared_revoker() {
	local candidate

	for candidate in "$STATE_DIR"/collab-*.state; do
		if [[ -e "$candidate" || -L "$candidate" ]]; then
			return 0
		fi
	done
	rm -f -- "$STATE_DIR/remove-user.sh" "$STATE_DIR/lib.sh" || warn "could not remove the root-owned automatic revoke helper"
}

main() {
	parse_args "$@"
	[[ -n "$username" ]] || die "--name is required"
	validate_username "$username"
	if [[ "$automatic" == true && "$assume_yes" != true ]]; then
		die "--auto requires --yes"
	fi

	ensure_root "$SCRIPT_PATH" "$@"

	local command_name
	for command_name in awk chmod chown getent groupdel id mktemp mv pgrep pkill rm sleep stat userdel usermod; do
		require_command "$command_name"
	done
	[[ -d "$STATE_DIR" ]] || die "state directory does not exist: $STATE_DIR"
	state_dir_is_safe || die "state directory must be owned by root with mode 700: $STATE_DIR"

	state_path=$(state_path_for "$username")
	[[ -f "$state_path" && ! -L "$state_path" ]] || die "no managed state found for account: $username"
	state_file_is_safe "$state_path" || die "state file must be owned by root with mode 600: $state_path"
	read_state
	validate_state
	if [[ "$state_auto_revoke" == systemd ]]; then
		require_systemd_manager
	fi
	confirm_removal

	if ! update_state_status "$state_path" "revoking"; then
		die "could not mark state as revoking: $state_path"
	fi

	validate_current_account
	if [[ "$identity_safe" == true ]] && user_exists "$username"; then
		usermod --lock --expiredate 1970-01-01 -- "$username" || failure=1
		terminate_user_processes "$username"
	fi
	stop_revoke_units
	if [[ "$state_auto_revoke" == systemd ]]; then
		remove_systemd_unit_files || failure=1
	fi
	if [[ "$state_sudo_mode" == full-root ]]; then
		remove_sudoers_file || failure=1
	fi
	if [[ "$identity_safe" == true ]]; then
		remove_account
	else
		warn "account identity validation failed; skipping account deletion"
	fi
	remove_group
	remove_leftover_home_path

	if [[ "$state_auto_revoke" == systemd ]]; then
		if revoke_units_active; then
			warn "automatic revoke unit is still active"
			failure=1
		fi
	fi
	if command -v visudo >/dev/null 2>&1; then
		visudo -c >/dev/null || failure=1
	fi
	verify_revocation

	if [[ "$failure" != 0 ]]; then
		update_state_status "$state_path" "revoke-partial" || warn "could not update partial-revoke state"
		die "revocation is incomplete; state retained at $state_path"
	fi
	rm -f -- "$state_path"
	[[ ! -e "$state_path" && ! -L "$state_path" ]] || die "could not remove state file: $state_path"
	cleanup_shared_revoker
	info "Revoked temporary collaboration account: $username"
}

main "$@"
