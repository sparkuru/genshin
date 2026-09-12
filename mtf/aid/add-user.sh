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
readonly SCRIPT_PATH="$SCRIPT_DIR/add-user.sh"
readonly BASH_PATH="$BASH"

# shellcheck disable=SC1091  # The helper is shipped next to this script.
source "$SCRIPT_DIR/lib.sh"

pubkey_file=""
private_key_file=""
generated_key=false
key_paths_reported=false
name_was_generated=false
key_owner=""
key_owner_uid=""
requested_name=""
ttl_text="$DEFAULT_TTL_TEXT"
full_root=false
confirm_full_root=false
no_auto_revoke=false
sudo_mode="none"
auto_revoke_mode="systemd"

username=""
user_uid=""
group_name=""
group_gid=""
home_dir=""
ssh_dir=""
authorized_keys_path=""
sudoers_path=""
service_unit=""
timer_unit=""
service_unit_path=""
timer_unit_path=""
revocation_script_path="${STATE_DIR}/remove-user.sh"
state_path=""
key_line=""
key_fingerprint=""
ttl_seconds=0
created_epoch=0
expires_epoch=0
expiry_iso=""
expiry_date=""
calendar_time=""

group_created=false
user_created=false
sudoers_created=false
timer_created=false
state_created=false
creation_committed=false

usage() {
	printf '%s\n' "$(color_text "$STYLE_TITLE" "Usage:")"
	printf '  sudo %s [options]\n\n' "$SCRIPT_PATH"
	printf '%s\n' "$(color_text "$STYLE_TITLE" "Options:")"
	printf '  --pubkey-file PATH       Install exactly one SSH public key\n'
	printf '  --private-key-file PATH  Write a generated private key here (without --pubkey-file)\n'
	printf '  --name NAME              Use a collab-* account name instead of generating one\n'
	printf '  --ttl DURATION           Lifetime: 5m..30d; default: %s\n' "$DEFAULT_TTL_TEXT"
	printf '  --full-root              Grant explicit NOPASSWD:ALL sudo access\n'
	printf '  --confirm-full-root      Required together with --full-root\n'
	printf '  --no-auto-revoke         Disable systemd automatic revocation\n'
	printf '  -h, --help               Show this help\n\n'
	printf '%s\n' "$(color_text "$STYLE_TITLE" "Examples:")"
	printf '  sudo %s --pubkey-file /path/to/collaborator.pub\n' "$SCRIPT_PATH"
	printf '  sudo %s --private-key-file /secure/path/collab.ed25519\n' "$SCRIPT_PATH"
	printf '  sudo %s --pubkey-file /path/to/collaborator.pub --ttl 4h --full-root --confirm-full-root\n' "$SCRIPT_PATH"
}

parse_args() {
	while (($# > 0)); do
		case "$1" in
		--pubkey-file)
			(($# >= 2)) || die "--pubkey-file requires a path"
			pubkey_file=$2
			shift 2
			;;
		--pubkey-file=*)
			pubkey_file=${1#*=}
			shift
			;;
		--private-key-file)
			(($# >= 2)) || die "--private-key-file requires a path"
			private_key_file=$2
			shift 2
			;;
		--private-key-file=*)
			private_key_file=${1#*=}
			shift
			;;
		--generated-key)
			generated_key=true
			shift
			;;
		--key-paths-reported)
			key_paths_reported=true
			shift
			;;
		--name)
			(($# >= 2)) || die "--name requires a value"
			requested_name=$2
			shift 2
			;;
		--name=*)
			requested_name=${1#*=}
			shift
			;;
		--ttl)
			(($# >= 2)) || die "--ttl requires a value"
			ttl_text=$2
			shift 2
			;;
		--ttl=*)
			ttl_text=${1#*=}
			shift
			;;
		--full-root)
			full_root=true
			shift
			;;
		--confirm-full-root)
			confirm_full_root=true
			shift
			;;
		--no-auto-revoke)
			no_auto_revoke=true
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

resolve_output_path() {
	local output_path=$1

	if [[ "$output_path" == /* ]]; then
		printf '%s\n' "$output_path"
	else
		printf '%s/%s\n' "$(pwd -P)" "$output_path"
	fi
}

resolve_key_owner() {
	local verified_uid

	key_owner=""
	key_owner_uid=""
	if ((EUID != 0)) || [[ ! "${SUDO_UID:-}" =~ ^[1-9][0-9]*$ ]] || [[ -z "${SUDO_USER:-}" ]]; then
		return 0
	fi
	if verified_uid=$(id -u "$SUDO_USER" 2>/dev/null) && [[ "$verified_uid" == "$SUDO_UID" ]]; then
		key_owner=$SUDO_USER
		key_owner_uid=$SUDO_UID
	fi
}

prepare_generated_key() {
	local key_parent
	local -a keygen_command

	if [[ -z "$username" ]]; then
		if [[ -n "$requested_name" ]]; then
			username=$requested_name
			validate_username "$username"
		else
			username=$(generate_username)
			name_was_generated=true
		fi
	fi

	if [[ -z "$private_key_file" ]]; then
		private_key_file="/tmp/${username}.ed25519"
	else
		private_key_file=$(resolve_output_path "$private_key_file")
	fi
	pubkey_file="${private_key_file}.pub"
	key_parent=${private_key_file%/*}

	[[ -d "$key_parent" && ! -L "$key_parent" ]] || die "private key parent is not a real directory: $key_parent"
	[[ -w "$key_parent" ]] || die "private key parent is not writable: $key_parent"
	[[ ! -e "$private_key_file" && ! -L "$private_key_file" ]] || die "refusing to overwrite existing private key: $private_key_file"
	[[ ! -e "$pubkey_file" && ! -L "$pubkey_file" ]] || die "refusing to overwrite existing public key: $pubkey_file"

	keygen_command=(ssh-keygen -q -t ed25519 -N '' -C "mtf-aid $username" -f "$private_key_file")
	if [[ -n "$key_owner_uid" ]]; then
		keygen_command=(sudo -H -u "#$key_owner_uid" -- "${keygen_command[@]}")
	fi
	if ! "${keygen_command[@]}"; then
		rm -f -- "$private_key_file" "$pubkey_file" || true
		die "could not generate an Ed25519 key pair"
	fi
	if [[ -n "$key_owner" ]] && ! chown -- "$key_owner" "$private_key_file" "$pubkey_file"; then
		rm -f -- "$private_key_file" "$pubkey_file" || true
		die "could not assign the generated key pair to the invoking user"
	fi
	if ! chmod 600 "$private_key_file" || ! chmod 644 "$pubkey_file"; then
		rm -f -- "$private_key_file" "$pubkey_file" || true
		die "could not set generated key permissions"
	fi
	generated_key=true
}

validate_generated_key() {
	if [[ "$generated_key" != true ]]; then
		return 0
	fi

	[[ -n "$requested_name" ]] || die "internal generated-key mode requires --name"
	[[ -n "$private_key_file" && -n "$pubkey_file" ]] || die "generated key paths are incomplete"
	[[ "$pubkey_file" == "${private_key_file}.pub" ]] || die "generated public key path does not match the private key path"
	[[ -f "$private_key_file" && ! -L "$private_key_file" ]] || die "generated private key is missing: $private_key_file"
	[[ -f "$pubkey_file" && ! -L "$pubkey_file" ]] || die "generated public key is missing: $pubkey_file"
	[[ "$(stat -c '%a' "$private_key_file")" == 600 ]] || die "generated private key must have mode 600: $private_key_file"
	if [[ -n "$key_owner_uid" ]]; then
		[[ "$(stat -c '%u' "$private_key_file")" == "$key_owner_uid" ]] || die "generated private key has an unexpected owner: $private_key_file"
		[[ "$(stat -c '%u' "$pubkey_file")" == "$key_owner_uid" ]] || die "generated public key has an unexpected owner: $pubkey_file"
	fi
}

report_generated_key_paths() {
	if [[ "$key_paths_reported" == true ]]; then
		return 0
	fi

	printf '  generated private key: %q\n' "$private_key_file"
	printf '  generated public key: %q\n' "$pubkey_file"
	warn "protect the generated private key; it is required for SSH access"
	key_paths_reported=true
}

reexec_as_root() {
	local -a reexec_args=("$@")

	if [[ "$generated_key" == true ]]; then
		reexec_args+=(--pubkey-file "$pubkey_file" --private-key-file "$private_key_file" --generated-key)
		reexec_args+=(--key-paths-reported)
		if [[ "$name_was_generated" == true ]]; then
			reexec_args+=(--name "$username")
		fi
	fi
	ensure_root "$SCRIPT_PATH" "${reexec_args[@]}"
}

write_state_file() {
	local status=$1
	local temp_path

	temp_path=$(mktemp "${STATE_DIR}/.${username}.state.XXXXXXXXXX")
	if ! {
		printf 'version=1\n'
		printf 'status=%s\n' "$status"
		printf 'username=%s\n' "$username"
		printf 'user_uid=%s\n' "$user_uid"
		printf 'group_name=%s\n' "$group_name"
		printf 'group_gid=%s\n' "$group_gid"
		printf 'home_dir=%s\n' "$home_dir"
		printf 'authorized_keys_path=%s\n' "$authorized_keys_path"
		printf 'sudoers_path=%s\n' "$sudoers_path"
		printf 'sudo_mode=%s\n' "$sudo_mode"
		printf 'service_unit=%s\n' "$service_unit"
		printf 'timer_unit=%s\n' "$timer_unit"
		printf 'auto_revoke=%s\n' "$auto_revoke_mode"
		printf 'ttl=%s\n' "$ttl_text"
		printf 'created_epoch=%s\n' "$created_epoch"
		printf 'expires_epoch=%s\n' "$expires_epoch"
		printf 'key_fingerprint=%s\n' "$key_fingerprint"
	} >"$temp_path"; then
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

write_authorized_keys() {
	local temp_path

	[[ ! -e "$authorized_keys_path" && ! -L "$authorized_keys_path" ]] || die "refusing to overwrite existing authorized_keys: $authorized_keys_path"
	temp_path=$(mktemp "${TMPDIR:-/tmp}/mtf-aid-authorized-keys.XXXXXXXXXX")
	if ! printf '%s\n' "$key_line" >"$temp_path"; then
		rm -f -- "$temp_path"
		return 1
	fi
	if ! install -m 600 -o "$username" -g "$group_name" "$temp_path" "$authorized_keys_path"; then
		rm -f -- "$temp_path"
		return 1
	fi
	rm -f -- "$temp_path"
}

write_sudoers_file() {
	local temp_path

	[[ ! -e "$sudoers_path" && ! -L "$sudoers_path" ]] || die "refusing to overwrite existing sudoers file: $sudoers_path"
	temp_path=$(mktemp "${TMPDIR:-/tmp}/mtf-aid-sudoers.XXXXXXXXXX")
	if ! printf '%s\n' "$username ALL=(ALL) NOPASSWD: ALL" >"$temp_path"; then
		rm -f -- "$temp_path"
		return 1
	fi
	chmod 440 "$temp_path"
	chown root:root "$temp_path"
	if ! visudo -cf "$temp_path" >/dev/null; then
		rm -f -- "$temp_path"
		return 1
	fi
	if ! install -m 440 -o root -g root "$temp_path" "$sudoers_path"; then
		rm -f -- "$temp_path"
		return 1
	fi
	sudoers_created=true
	rm -f -- "$temp_path"
}

install_revocation_helper() {
	local metadata

	if [[ -e "$revocation_script_path" || -L "$revocation_script_path" ]]; then
		[[ -f "$revocation_script_path" && ! -L "$revocation_script_path" ]] || return 1
		metadata=$(stat -c '%u %a' "$revocation_script_path") || return 1
		[[ "$metadata" == "0 700" ]] || return 1
	else
		install -m 700 -o root -g root "$SCRIPT_DIR/remove-user.sh" "$revocation_script_path" || return 1
	fi

	if [[ -e "${STATE_DIR}/lib.sh" || -L "${STATE_DIR}/lib.sh" ]]; then
		[[ -f "${STATE_DIR}/lib.sh" && ! -L "${STATE_DIR}/lib.sh" ]] || return 1
		metadata=$(stat -c '%u %a' "${STATE_DIR}/lib.sh") || return 1
		[[ "$metadata" == "0 600" ]] || return 1
	else
		install -m 600 -o root -g root "$SCRIPT_DIR/lib.sh" "${STATE_DIR}/lib.sh" || return 1
	fi
}

schedule_revoke() {
	local service_temp
	local timer_temp

	install_revocation_helper || return 1
	service_temp=$(mktemp "${TMPDIR:-/tmp}/mtf-aid-service.XXXXXXXXXX")
	if ! timer_temp=$(mktemp "${TMPDIR:-/tmp}/mtf-aid-timer.XXXXXXXXXX"); then
		rm -f -- "$service_temp"
		return 1
	fi
	if ! {
		printf '[Unit]\n'
		printf 'Description=mtf-aid automatic revoke for %s\n\n' "$username"
		printf '[Service]\n'
		printf 'Type=oneshot\n'
		printf 'ExecStart=%s %s --name %s --yes --auto\n' "$BASH_PATH" "$revocation_script_path" "$username"
	} >"$service_temp"; then
		rm -f -- "$service_temp" "$timer_temp"
		return 1
	fi
	if ! {
		printf '[Unit]\n'
		printf 'Description=mtf-aid timer for %s\n\n' "$username"
		printf '[Timer]\n'
		printf 'OnCalendar=%s\n' "$calendar_time"
		printf 'Persistent=true\n'
		printf 'Unit=%s\n\n' "$service_unit"
		printf '[Install]\n'
		printf 'WantedBy=timers.target\n'
	} >"$timer_temp"; then
		rm -f -- "$service_temp" "$timer_temp"
		return 1
	fi
	if ! chmod 644 "$service_temp" "$timer_temp" || ! chown root:root "$service_temp" "$timer_temp"; then
		rm -f -- "$service_temp" "$timer_temp"
		return 1
	fi
	if ! install -m 644 -o root -g root "$service_temp" "$service_unit_path"; then
		rm -f -- "$service_temp" "$timer_temp"
		return 1
	fi
	if ! install -m 644 -o root -g root "$timer_temp" "$timer_unit_path"; then
		rm -f -- "$service_temp" "$timer_temp"
		return 1
	fi
	rm -f -- "$service_temp" "$timer_temp"
	systemctl daemon-reload || return 1
	systemctl enable --now "$timer_unit" || return 1
}

remove_systemd_units() {
	local cleanup_ok=true

	set +e
	disable_systemd_unit_if_present "$timer_unit" || cleanup_ok=false
	stop_systemd_unit_if_present "$service_unit" || cleanup_ok=false
	rm -f -- "$timer_unit_path" "$service_unit_path" || cleanup_ok=false
	systemctl daemon-reload || cleanup_ok=false
	if [[ "$cleanup_ok" != true ]]; then
		return 1
	fi
}

rollback_creation() {
	local rollback_ok=true

	set +e
	if [[ "$timer_created" == true ]]; then
		remove_systemd_units || rollback_ok=false
	fi
	if [[ "$sudoers_created" == true ]]; then
		rm -f -- "$sudoers_path" || rollback_ok=false
	fi
	if [[ "$user_created" == true ]]; then
		if user_exists "$username"; then
			terminate_user_processes "$username"
			userdel --remove -- "$username" || true
		fi
		user_exists "$username" && rollback_ok=false
		if [[ -e "$home_dir" || -L "$home_dir" ]]; then
			rollback_ok=false
			warn "rollback left the home path in place: $home_dir"
		fi
	fi
	if [[ "$group_created" == true ]]; then
		if group_exists "$group_name"; then
			groupdel -- "$group_name" || rollback_ok=false
		fi
		group_exists "$group_name" && rollback_ok=false
	fi
	if [[ "$state_created" == true ]]; then
		if [[ "$rollback_ok" == true ]]; then
			rm -f -- "$state_path" || rollback_ok=false
		fi
	fi

	if [[ "$rollback_ok" != true ]]; then
		warn "automatic rollback was incomplete; retained state: $state_path"
	fi
}

on_exit() {
	local exit_status=$?

	if [[ "$creation_committed" != true ]]; then
		rollback_creation
		if [[ "$generated_key" == true && -n "$private_key_file" && -e "$private_key_file" ]]; then
			warn "generated key pair was left at $private_key_file; remove it if unused"
		fi
	fi
	return "$exit_status"
}

main() {
	parse_args "$@"
	[[ "$pubkey_file" != "-" ]] || die "--pubkey-file - is not supported; use a file path"
	if [[ -n "$pubkey_file" && -n "$private_key_file" && "$generated_key" != true ]]; then
		die "--private-key-file can only be used when --pubkey-file is omitted"
	fi
	if [[ "$generated_key" == true ]]; then
		[[ -n "$requested_name" ]] || die "internal generated-key mode requires --name"
		[[ -n "$private_key_file" && -n "$pubkey_file" ]] || die "generated key paths are incomplete"
		[[ "$pubkey_file" == "${private_key_file}.pub" ]] || die "generated public key path does not match the private key path"
	fi
	if [[ "$confirm_full_root" == true && "$full_root" != true ]]; then
		die "--confirm-full-root requires --full-root"
	fi
	if [[ "$full_root" == true && "$confirm_full_root" != true ]]; then
		die "--full-root requires --confirm-full-root"
	fi

	ttl_seconds=$(parse_ttl_seconds "$ttl_text")
	if ((EUID != 0)); then
		if [[ -z "$pubkey_file" ]]; then
			require_command date
			require_command getent
			require_command ssh-keygen
			require_command chmod
			require_command rm
			if [[ -n "$requested_name" ]]; then
				username=$requested_name
				validate_username "$username"
			fi
			prepare_generated_key
			report_generated_key_paths
		fi
		reexec_as_root "$@"
	fi

	local command_name
	for command_name in awk chage chmod chown date getent groupadd groupdel id install mktemp mv pgrep pkill rm sleep stat ssh-keygen useradd userdel usermod; do
		require_command "$command_name"
	done
	if [[ -z "$pubkey_file" || "$generated_key" == true ]]; then
		resolve_key_owner
		if [[ -n "$key_owner_uid" ]]; then
			require_command sudo
		fi
	fi
	if [[ "$full_root" == true ]]; then
		require_command visudo
		[[ -d "$SUDOERS_DIR" ]] || die "sudoers include directory does not exist: $SUDOERS_DIR"
	fi
	if [[ "$no_auto_revoke" != true ]]; then
		require_systemd_manager
	fi

	if [[ "$full_root" == true ]]; then
		sudo_mode=full-root
	fi
	if [[ "$no_auto_revoke" == true ]]; then
		auto_revoke_mode=manual
	fi

	if [[ -n "$requested_name" ]]; then
		username=$requested_name
		validate_username "$username"
	else
		username=$(generate_username)
		name_was_generated=true
	fi
	if [[ -z "$pubkey_file" ]]; then
		prepare_generated_key
	fi
	validate_generated_key

	key_line=$(extract_public_key "$pubkey_file")
	key_fingerprint=$(public_key_fingerprint "$key_line")
	created_epoch=$(date +%s)
	expires_epoch=$((created_epoch + ttl_seconds))
	if ! expiry_iso=$(format_epoch "$expires_epoch"); then
		die "could not format account expiry time"
	fi
	if [[ "$expiry_iso" =~ ^([0-9]{4}-[0-9]{2}-[0-9]{2})T([0-9]{2}:[0-9]{2}:[0-9]{2})Z$ ]]; then
		expiry_date=${BASH_REMATCH[1]}
		calendar_time="${BASH_REMATCH[1]} ${BASH_REMATCH[2]} UTC"
	else
		die "could not derive a systemd calendar time from account expiry"
	fi

	group_name=$username
	home_dir="/home/$username"
	ssh_dir="$home_dir/.ssh"
	authorized_keys_path="$ssh_dir/authorized_keys"
	sudoers_path="${SUDOERS_PREFIX}${username}"
	if [[ "$no_auto_revoke" != true ]]; then
		service_unit="mtf-aid-revoke-${username}.service"
		timer_unit="mtf-aid-revoke-${username}.timer"
		service_unit_path="/etc/systemd/system/$service_unit"
		timer_unit_path="/etc/systemd/system/$timer_unit"
	fi
	state_path=$(state_path_for "$username")
	if [[ -e "$state_path" || -L "$state_path" ]]; then
		die "state already exists for account: $username"
	fi
	if user_exists "$username"; then
		die "account already exists; refusing to modify it: $username"
	fi
	if group_exists "$group_name"; then
		die "group already exists; refusing to modify it: $group_name"
	fi
	if [[ -e "$home_dir" || -L "$home_dir" ]]; then
		die "home path already exists; refusing to modify it: $home_dir"
	fi
	if [[ "$full_root" == true && (-e "$sudoers_path" || -L "$sudoers_path") ]]; then
		die "sudoers path already exists; refusing to modify it: $sudoers_path"
	fi
	if [[ "$no_auto_revoke" != true ]] && [[ -e "$service_unit_path" || -L "$service_unit_path" || -e "$timer_unit_path" || -L "$timer_unit_path" ]]; then
		die "systemd unit path already exists; refusing to modify it"
	fi
	ensure_state_dir

	groupadd -- "$group_name"
	group_created=true
	group_gid=$(get_group_gid "$group_name")
	[[ "$group_gid" =~ ^[0-9]+$ ]] || die "could not determine created group ID: $group_name"

	state_created=true
	write_state_file "provisioning"

	useradd --create-home --home-dir "$home_dir" --shell /bin/bash --gid "$group_name" --comment "Temporary collaboration account" -- "$username"
	user_created=true
	user_uid=$(id -u "$username")
	[[ "$user_uid" =~ ^[0-9]+$ ]] || die "could not determine created account ID: $username"
	write_state_file "provisioning"
	[[ "$(user_home_dir "$username")" == "$home_dir" ]] || die "created account has an unexpected home path"
	usermod --lock -- "$username"
	chage -E "$expiry_date" "$username"

	[[ ! -e "$ssh_dir" && ! -L "$ssh_dir" ]] || die "unexpected SSH directory already exists: $ssh_dir"
	install -d -m 700 -o "$username" -g "$group_name" "$ssh_dir"
	write_authorized_keys

	if [[ "$full_root" == true ]]; then
		write_sudoers_file || die "could not install sudoers rule"
		visudo -c >/dev/null || die "complete sudoers configuration failed validation"
	fi

	if [[ "$no_auto_revoke" != true ]]; then
		timer_created=true
		schedule_revoke || die "could not schedule automatic revocation"
	else
		warn "automatic revocation is disabled; run remove-user.sh manually"
	fi

	write_state_file "active"
	creation_committed=true

	info "Created temporary collaboration account: $username"
	printf '  key fingerprint: %s\n' "$key_fingerprint"
	if [[ "$generated_key" == true ]]; then
		report_generated_key_paths
	fi
	printf '  expires: %s\n' "$(format_epoch "$expires_epoch")"
	if [[ "$full_root" == true ]]; then
		warn "full root access is enabled; revoke this account as soon as collaboration ends"
	else
		printf '  sudo access: none\n'
	fi
	if [[ "$no_auto_revoke" != true ]]; then
		printf '  automatic revoke: %s\n' "$timer_unit"
	fi
	printf '  revoke command: sudo %q --name %q\n' "$SCRIPT_DIR/remove-user.sh" "$username"
}

trap on_exit EXIT
main "$@"
