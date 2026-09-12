#!/usr/bin/env bash

set -Eeuo pipefail

readonly STATE_DIR="/var/lib/mtf-aid"
readonly USER_PREFIX="collab-"
readonly SUDOERS_DIR="/etc/sudoers.d"
# shellcheck disable=SC2034  # Shared with the sibling lifecycle scripts.
readonly SUDOERS_PREFIX="${SUDOERS_DIR}/mtf-aid-"
# shellcheck disable=SC2034  # Shared with the account creation script.
readonly DEFAULT_TTL_TEXT="8h"
readonly MIN_TTL_SECONDS=300
readonly MAX_TTL_SECONDS=2592000

readonly STYLE_RESET=$'\033[0m'
# shellcheck disable=SC2034  # Shared with the sibling CLI scripts.
readonly STYLE_TITLE=$'\033[1;36m'
readonly STYLE_SUCCESS=$'\033[0;32m'
readonly STYLE_WARNING=$'\033[1;33m'
readonly STYLE_ERROR=$'\033[1;31m'

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

require_command() {
	local command_name=$1

	command -v "$command_name" >/dev/null 2>&1 || die "required command not found: $command_name"
}

ensure_root() {
	if ((EUID == 0)); then
		return 0
	fi

	require_command sudo
	exec sudo -- "$@"
}

require_systemd_manager() {
	require_command systemctl
	systemctl show --property=Version --value >/dev/null 2>&1 || die "a running systemd system manager is required"
}

validate_username() {
	local username=$1

	is_valid_username "$username" || die "invalid account name: $username"
	[[ "$username" != *- ]] || die "account name must not end with a hyphen: $username"
}

is_valid_username() {
	local username=$1

	[[ "$username" =~ ^collab-[a-z0-9][a-z0-9-]{0,24}$ && "$username" != *- ]]
}

user_exists() {
	getent passwd "$1" >/dev/null 2>&1
}

group_exists() {
	getent group "$1" >/dev/null 2>&1
}

state_path_for() {
	printf '%s/%s.state' "$STATE_DIR" "$1"
}

state_dir_is_safe() {
	local metadata

	[[ -d "$STATE_DIR" && ! -L "$STATE_DIR" ]] || return 1
	metadata=$(stat -c '%u %a' "$STATE_DIR") || return 1
	[[ "$metadata" == "0 700" ]]
}

ensure_state_dir() {
	if [[ -L "$STATE_DIR" || (-e "$STATE_DIR" && ! -d "$STATE_DIR") ]]; then
		die "state directory is not a real directory: $STATE_DIR"
	fi

	install -d -m 700 -o root -g root "$STATE_DIR"
	state_dir_is_safe || die "state directory must be owned by root with mode 700: $STATE_DIR"
}

state_file_is_safe() {
	local state_path=$1
	local metadata

	[[ -f "$state_path" && ! -L "$state_path" ]] || return 1
	metadata=$(stat -c '%u %a' "$state_path") || return 1
	[[ "$metadata" == "0 600" ]]
}

read_state_value() {
	local key=$1
	local state_path=$2

	awk -F= -v wanted_key="$key" '
		$1 == wanted_key {
			print substr($0, index($0, "=") + 1)
			found = 1
			exit
		}
		END {
			if (!found) {
				exit 1
			}
		}
	' "$state_path"
}

update_state_status() {
	local state_path=$1
	local new_status=$2
	local temp_path

	temp_path=$(mktemp "${STATE_DIR}/.state-update.XXXXXXXXXX")
	if ! awk -F= -v replacement="$new_status" '
		$1 == "status" {
			print "status=" replacement
			replaced = 1
			next
		}
		{ print }
		END {
			if (!replaced) {
				exit 1
			}
		}
	' "$state_path" >"$temp_path"; then
		rm -f -- "$temp_path"
		return 1
	fi

	if ! chmod 600 "$temp_path" || ! chown root:root "$temp_path"; then
		rm -f -- "$temp_path"
		return 1
	fi
	if ! mv -- "$temp_path" "$state_path"; then
		rm -f -- "$temp_path"
		return 1
	fi
}

parse_ttl_seconds() {
	local ttl_text=$1
	local value
	local unit
	local multiplier
	local seconds

	if [[ ! "$ttl_text" =~ ^([1-9][0-9]{0,5})([mhdw])$ ]]; then
		die "invalid TTL '$ttl_text'; use a value such as 30m, 8h, 2d, or 1w"
	fi

	value=${BASH_REMATCH[1]}
	unit=${BASH_REMATCH[2]}
	case "$unit" in
	m) multiplier=60 ;;
	h) multiplier=3600 ;;
	d) multiplier=86400 ;;
	w) multiplier=604800 ;;
	*) die "unsupported TTL unit: $unit" ;;
	esac

	seconds=$((value * multiplier))
	((seconds >= MIN_TTL_SECONDS && seconds <= MAX_TTL_SECONDS)) || die "TTL must be between 5m and 30d"
	printf '%s\n' "$seconds"
}

generate_username() {
	local candidate

	while :; do
		candidate=$(printf '%s%s-%04x' "$USER_PREFIX" "$(date -u +%Y%m%d-%H%M%S)" "$RANDOM")
		if ! user_exists "$candidate" && ! group_exists "$candidate" && [[ ! -e "$(state_path_for "$candidate")" && ! -L "$(state_path_for "$candidate")" ]]; then
			printf '%s\n' "$candidate"
			return 0
		fi
	done
}

extract_public_key() {
	local pubkey_file=$1
	local key_count
	local key_line
	local key_type
	local key_data

	[[ -f "$pubkey_file" ]] || die "public key file does not exist: $pubkey_file"
	key_count=$(awk 'NF && $1 !~ /^#/ {count++} END {print count + 0}' "$pubkey_file")
	[[ "$key_count" == 1 ]] || die "public key file must contain exactly one non-comment key"

	key_line=$(awk 'NF && $1 !~ /^#/ {print; exit}' "$pubkey_file")
	read -r key_type key_data _ <<<"$key_line"
	case "$key_type" in
	ssh-ed25519 | ssh-rsa | ecdsa-sha2-nistp256 | ecdsa-sha2-nistp384 | ecdsa-sha2-nistp521 | sk-ssh-ed25519@openssh.com | sk-ecdsa-sha2-nistp256@openssh.com) ;;
	*) die "unsupported or malformed SSH public key type: $key_type" ;;
	esac
	[[ "$key_data" =~ ^[A-Za-z0-9+/]+={0,2}$ ]] || die "malformed SSH public key data"
	ssh-keygen -lf <(printf '%s\n' "$key_line") >/dev/null 2>&1 || die "public key validation failed: $pubkey_file"

	printf '%s\n' "$key_line"
}

public_key_fingerprint() {
	local key_line=$1

	ssh-keygen -lf <(printf '%s\n' "$key_line") | awk 'NR == 1 {print $2}'
}

user_home_dir() {
	getent passwd "$1" | awk -F: 'NR == 1 {print $6; found = 1} END {if (!found) exit 1}'
}

get_group_gid() {
	getent group "$1" | awk -F: 'NR == 1 {print $3; found = 1} END {if (!found) exit 1}'
}

get_group_members() {
	getent group "$1" | awk -F: 'NR == 1 {print $4; found = 1} END {if (!found) exit 1}'
}

has_primary_group_users() {
	local target_gid=$1

	getent passwd | awk -F: -v target_gid="$target_gid" '$4 == target_gid {found = 1} END {exit found ? 0 : 1}'
}

terminate_user_processes() {
	local username=$1

	if command -v loginctl >/dev/null 2>&1; then
		loginctl terminate-user "$username" >/dev/null 2>&1 || true
	fi

	if pgrep -u "$username" >/dev/null 2>&1; then
		pkill -TERM -u "$username" >/dev/null 2>&1 || true
		sleep 1
		if pgrep -u "$username" >/dev/null 2>&1; then
			pkill -KILL -u "$username" >/dev/null 2>&1 || true
		fi
	fi
}

stop_systemd_unit_if_present() {
	local unit_name=$1

	[[ -n "$unit_name" ]] || return 0
	if systemctl stop "$unit_name" >/dev/null 2>&1; then
		return 0
	fi
	if systemctl show "$unit_name" >/dev/null 2>&1; then
		return 1
	fi
	return 0
}

disable_systemd_unit_if_present() {
	local unit_name=$1

	[[ -n "$unit_name" ]] || return 0
	if systemctl disable --now "$unit_name" >/dev/null 2>&1; then
		return 0
	fi
	if systemctl show "$unit_name" >/dev/null 2>&1; then
		return 1
	fi
	return 0
}

format_epoch() {
	local epoch=$1

	if date -u -d "@$epoch" '+%Y-%m-%dT%H:%M:%SZ' 2>/dev/null; then
		return 0
	fi
	if date -u -r "$epoch" '+%Y-%m-%dT%H:%M:%SZ' 2>/dev/null; then
		return 0
	fi
	printf '%s' "$epoch"
}
