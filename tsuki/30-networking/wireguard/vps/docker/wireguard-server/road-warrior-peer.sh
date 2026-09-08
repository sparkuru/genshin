#!/bin/sh
set -eu

readonly SCRIPT_NAME="${0##*/}"
readonly CONFIG_PATH=/etc/wireguard/wg0.conf
readonly REGISTRY_PATH=/etc/overlap-vpn/road-warriors.tsv
readonly INTERFACE_NAME=wg0
readonly WG_HUB_ADDRESS="${OVERLAP_VPN_WG_HUB_ADDRESS:-10.90.0.1}"
readonly HOME_TRANSLATED_CIDR="${OVERLAP_VPN_HOME_TRANSLATED_CIDR:-10.91.0.0/24}"
readonly COMPANY_TRANSLATED_CIDR="${OVERLAP_VPN_COMPANY_TRANSLATED_CIDR:-10.92.0.0/24}"
readonly ROAD_WARRIOR_PREFIX="${OVERLAP_VPN_ROAD_WARRIOR_PREFIX:-10.93.0}"
readonly ENDPOINT_HOST="${OVERLAP_VPN_ENDPOINT_HOST:-vpn.example.invalid}"
readonly LOCK_DIR=/run/overlap-vpn-road-peer.lock
readonly FIRST_HOST=10
readonly LAST_HOST=250

lock_acquired=0
backup_dir=
work_dir=
config_backup=
registry_backup=
config_tmp=
registry_tmp=
client_private_key_tmp=
client_config_tmp=
registry_existed=0

usage() {
	printf 'Usage: %s add <name> <%s.HOST/32> <public-key>\n' "$SCRIPT_NAME" "$ROAD_WARRIOR_PREFIX" >&2
	printf '       %s issue <name> [%s.HOST/32] [--linux]\n' "$SCRIPT_NAME" "$ROAD_WARRIOR_PREFIX" >&2
	printf '%s\n' "       $SCRIPT_NAME list" >&2
	printf '       %s revoke <name|%s.HOST/32>\n' "$SCRIPT_NAME" "$ROAD_WARRIOR_PREFIX" >&2
}

die() {
	printf 'Error: %s\n' "$*" >&2
	exit 1
}

require_command() {
	command -v "$1" >/dev/null 2>&1 || die "required command not found: $1"
}

require_runtime_commands() {
	require_command awk
	require_command cat
	require_command chmod
	require_command cp
	require_command grep
	require_command id
	require_command install
	require_command ip
	require_command mkdir
	require_command mktemp
	require_command mv
	require_command rmdir
	require_command rm
	require_command wc
	require_command wg
	require_command wg-quick
}

validate_name() {
	name=$1
	case "$name" in
	'' | *[!A-Za-z0-9._-]*)
		die "name must contain only letters, numbers, dot, underscore, or hyphen"
		;;
	esac
}

validate_address() {
	address=$1
	case "$address" in
	"$ROAD_WARRIOR_PREFIX".*/32) ;;
	*) die "address must be in the form ${ROAD_WARRIOR_PREFIX}.HOST/32" ;;
	esac

	host=${address#"$ROAD_WARRIOR_PREFIX".}
	host=${host%/32}
	case "$host" in
	'' | 0* | *[!0-9]*) die "address host must be a decimal number without leading zero" ;;
	esac
	if [ "$host" -lt "$FIRST_HOST" ] || [ "$host" -gt "$LAST_HOST" ]; then
		die "address host must be between $FIRST_HOST and $LAST_HOST"
	fi
}

validate_public_key() {
	public_key=$1
	case "$public_key" in
	'' | *[!A-Za-z0-9+/=]*) die "public key is not base64-shaped" ;;
	esac
	[ "$(printf '%s' "$public_key" | wc -c)" -eq 44 ] ||
		die "public key must be 44 characters"
}

registry_contains() {
	name=$1
	address=$2
	public_key=$3
	[ -f "$REGISTRY_PATH" ] || return 1
	awk -F '\t' -v name="$name" -v address="$address" -v public_key="$public_key" '
        $0 !~ /^#/ && NF >= 3 && ($1 == name || $2 == address || $3 == public_key) { found = 1 }
        END { exit(found ? 0 : 1) }
    ' "$REGISTRY_PATH"
}

registry_owner_for_name() {
	name=$1
	[ -f "$REGISTRY_PATH" ] || return 0
	awk -F '\t' -v name="$name" '$0 !~ /^#/ && NF >= 3 && $1 == name { print $1; exit }' \
		"$REGISTRY_PATH"
}

registry_owner_for_address() {
	address=$1
	[ -f "$REGISTRY_PATH" ] || return 0
	awk -F '\t' -v address="$address" '$0 !~ /^#/ && NF >= 3 && $2 == address { print $1; exit }' \
		"$REGISTRY_PATH"
}

config_contains() {
	needle=$1
	grep -Fq -- "$needle" "$CONFIG_PATH"
}

address_has_route() {
	ip route show "$1" 2>/dev/null | grep -q .
}

address_is_in_use() {
	address=$1
	owner=$(registry_owner_for_address "$address")
	[ -n "$owner" ] && return 0
	config_contains "AllowedIPs = $address" && return 0
	address_has_route "$address" && return 0
	return 1
}

ensure_address_available() {
	address=$1
	owner=$(registry_owner_for_address "$address")
	[ -z "$owner" ] || die "address already exists: $address (peer $owner)"
	if config_contains "AllowedIPs = $address"; then
		die "address already exists in WireGuard config: $address"
	fi
	if address_has_route "$address"; then
		die "address already has a kernel route: $address"
	fi
	return 0
}

find_next_address() {
	host_number=$FIRST_HOST
	while [ "$host_number" -le "$LAST_HOST" ]; do
		address="$ROAD_WARRIOR_PREFIX.$host_number/32"
		if ! address_is_in_use "$address"; then
			printf '%s\n' "$address"
			return 0
		fi
		host_number=$((host_number + 1))
	done
	die "no available road-warrior address remains"
}

release_lock() {
	if [ "$lock_acquired" -eq 1 ]; then
		rmdir -- "$LOCK_DIR" 2>/dev/null || true
		lock_acquired=0
	fi
}

cleanup_operation() {
	if [ -n "${client_config_tmp:-}" ]; then
		rm -f -- "$client_config_tmp"
	fi
	if [ -n "${client_private_key_tmp:-}" ]; then
		rm -f -- "$client_private_key_tmp"
	fi
	if [ -n "${config_tmp:-}" ]; then
		rm -f -- "$config_tmp"
	fi
	if [ -n "${registry_tmp:-}" ]; then
		rm -f -- "$registry_tmp"
	fi
	if [ -n "${work_dir:-}" ]; then
		rmdir -- "$work_dir" 2>/dev/null || true
	fi
	release_lock
}

acquire_lock() {
	if ! mkdir -- "$LOCK_DIR" 2>/dev/null; then
		die "another road-warrior operation is in progress"
	fi
	lock_acquired=1
	trap cleanup_operation 0 HUP INT TERM
}

begin_operation() {
	backup_dir=$(mktemp -d /tmp/overlap-vpn-road-peer.XXXXXX)
	work_dir=$(mktemp -d /etc/wireguard/.road-peer.XXXXXX)
	config_backup=$backup_dir/wg0.conf.before
	registry_backup=$backup_dir/road-warriors.tsv.before
	config_tmp=$work_dir/wg0.conf
	registry_tmp=$work_dir/road-warriors.tsv

	cp -p -- "$CONFIG_PATH" "$config_backup"
	cp -p -- "$CONFIG_PATH" "$config_tmp"
	if [ -f "$REGISTRY_PATH" ]; then
		registry_existed=1
		cp -p -- "$REGISTRY_PATH" "$registry_backup"
		cp -p -- "$REGISTRY_PATH" "$registry_tmp"
	else
		printf '%s\n' '# name<TAB>address<TAB>public_key' >"$registry_tmp"
	fi
	chmod 600 "$config_tmp" "$registry_tmp"
}

restore_files() {
	mv -f -- "$config_backup" "$CONFIG_PATH"
	if [ "$registry_existed" -eq 1 ]; then
		mv -f -- "$registry_backup" "$REGISTRY_PATH"
	else
		rm -f -- "$REGISTRY_PATH"
	fi
}

persist_files() {
	if ! mv -f -- "$config_tmp" "$CONFIG_PATH"; then
		die "failed to persist WireGuard config"
	fi
	config_tmp=
	if ! mv -f -- "$registry_tmp" "$REGISTRY_PATH"; then
		restore_files
		die "failed to persist peer registry"
	fi
	registry_tmp=
}

rollback_added_peer() {
	public_key=$1
	address=$2
	wg set "$INTERFACE_NAME" peer "$public_key" remove 2>/dev/null || true
	ip route del "$address" dev "$INTERFACE_NAME" 2>/dev/null || true
	restore_files
}

append_peer_state() {
	name=$1
	address=$2
	public_key=$3

	printf '%s\n' '' '[Peer]' "# road-warrior: $name" \
		"PublicKey = $public_key" "AllowedIPs = $address" >>"$config_tmp"
	printf '%s\t%s\t%s\n' "$name" "$address" "$public_key" >>"$registry_tmp"
	chmod 600 "$config_tmp" "$registry_tmp"
	wg-quick strip "$config_tmp" >/dev/null
	persist_files

	if ! wg set "$INTERFACE_NAME" peer "$public_key" allowed-ips "$address"; then
		rollback_added_peer "$public_key" "$address"
		die "failed to add live WireGuard peer"
	fi
	if ! ip route replace "$address" dev "$INTERFACE_NAME"; then
		rollback_added_peer "$public_key" "$address"
		die "failed to add live return route"
	fi
}

add_peer() {
	name=$1
	address=$2
	public_key=$3

	validate_name "$name"
	validate_address "$address"
	validate_public_key "$public_key"
	require_runtime_commands
	[ "$(id -u)" -eq 0 ] || die "run as root"
	[ -f "$CONFIG_PATH" ] || die "missing $CONFIG_PATH"
	wg show "$INTERFACE_NAME" >/dev/null 2>&1 || die "$INTERFACE_NAME is not active"

	acquire_lock
	owner=$(registry_owner_for_name "$name")
	[ -z "$owner" ] || die "peer name already exists: $name"
	ensure_address_available "$address"
	registry_contains "$name" "$address" "$public_key" &&
		die "name, address, or public key already exists in registry"
	config_contains "PublicKey = $public_key" &&
		die "public key already exists in WireGuard config"

	begin_operation
	append_peer_state "$name" "$address" "$public_key"
	printf '%s\n' "peer added: $name $address" >&2
	printf 'rollback backup: %s\n' "$backup_dir" >&2
}

write_client_config() {
	name=$1
	address=$2
	profile=$3
	client_private_key=$(cat -- "$client_private_key_tmp")
	server_public_key=$(wg show "$INTERFACE_NAME" public-key)
	server_port=$(wg show "$INTERFACE_NAME" listen-port)
	[ -n "$server_public_key" ] || die "failed to read VPS public key"
	case "$server_port" in
	'' | *[!0-9]*) die "failed to read VPS listen port" ;;
	esac

	{
		printf '%s\n' '[Interface]'
		printf 'Address = %s\n' "$address"
		printf '%s\n' 'MTU = 1420'
		printf 'PrivateKey = %s\n' "$client_private_key"
		if [ "$profile" = linux ]; then
			printf '%s\n' 'Table = off'
			printf '%s\n' "PostUp = ip route replace $WG_HUB_ADDRESS/32 dev %i table 2023"
			printf '%s\n' "PostUp = ip route replace $HOME_TRANSLATED_CIDR dev %i table 2023"
			printf '%s\n' "PostUp = ip route replace $COMPANY_TRANSLATED_CIDR dev %i table 2023"
			printf '%s\n' "PostUp = ip rule add priority 8900 to $WG_HUB_ADDRESS/32 table 2023 2>/dev/null || true"
			printf '%s\n' "PostUp = ip rule add priority 8901 to $HOME_TRANSLATED_CIDR table 2023 2>/dev/null || true"
			printf '%s\n' "PostUp = ip rule add priority 8902 to $COMPANY_TRANSLATED_CIDR table 2023 2>/dev/null || true"
			printf '%s\n' "PostDown = ip rule del priority 8900 to $WG_HUB_ADDRESS/32 table 2023 2>/dev/null || true"
			printf '%s\n' "PostDown = ip rule del priority 8901 to $HOME_TRANSLATED_CIDR table 2023 2>/dev/null || true"
			printf '%s\n' "PostDown = ip rule del priority 8902 to $COMPANY_TRANSLATED_CIDR table 2023 2>/dev/null || true"
			printf '%s\n' "PostDown = ip route del $WG_HUB_ADDRESS/32 table 2023 2>/dev/null || true"
			printf '%s\n' "PostDown = ip route del $HOME_TRANSLATED_CIDR table 2023 2>/dev/null || true"
			printf '%s\n' "PostDown = ip route del $COMPANY_TRANSLATED_CIDR table 2023 2>/dev/null || true"
		fi
		printf '%s\n' '' '[Peer]'
		printf '%s\n' '# VPS / road-warrior hub'
		printf 'PublicKey = %s\n' "$server_public_key"
		printf 'Endpoint = %s:%s\n' "$ENDPOINT_HOST" "$server_port"
		printf '%s\n' "AllowedIPs = $WG_HUB_ADDRESS/32, $HOME_TRANSLATED_CIDR, $COMPANY_TRANSLATED_CIDR"
		printf '%s\n' 'PersistentKeepalive = 25'
	} >"$client_config_tmp"
	chmod 600 "$client_config_tmp"
	wg-quick strip "$client_config_tmp" >/dev/null
}

issue_peer() {
	name=$1
	address=$2
	profile=$3

	validate_name "$name"
	case "$profile" in
	simple | linux) ;;
	*) die "unknown issue profile: $profile" ;;
	esac
	require_runtime_commands
	[ "$(id -u)" -eq 0 ] || die "run as root"
	[ -f "$CONFIG_PATH" ] || die "missing $CONFIG_PATH"
	wg show "$INTERFACE_NAME" >/dev/null 2>&1 || die "$INTERFACE_NAME is not active"

	acquire_lock
	if [ -n "$address" ]; then
		validate_address "$address"
		ensure_address_available "$address"
	else
		address=$(find_next_address)
	fi
	owner=$(registry_owner_for_name "$name")
	[ -z "$owner" ] || die "peer name already exists: $name"
	begin_operation

	client_private_key_tmp=$work_dir/client-privatekey
	client_config_tmp=$work_dir/client.conf
	wg genkey >"$client_private_key_tmp"
	chmod 600 "$client_private_key_tmp"
	client_public_key=$(wg pubkey <"$client_private_key_tmp")
	validate_public_key "$client_public_key"
	write_client_config "$name" "$address" "$profile"
	append_peer_state "$name" "$address" "$client_public_key"

	printf '%s\n' "issued: $name $address ($profile)" >&2
	printf 'rollback backup: %s\n' "$backup_dir" >&2
	cat -- "$client_config_tmp"
}

config_peer_count() {
	public_key=$1
	awk -v public_key="$public_key" '
        function flush_section() {
                if (section_name == "Peer" && peer_public_key == public_key) {
                        count++
                }
        }
        /^\[[^]]*\][[:space:]]*$/ {
                if (section_name != "" || section_text != "") {
                        flush_section()
                }
                section_name = $0
                sub(/^\[/, "", section_name)
                sub(/\][[:space:]]*$/, "", section_name)
                section_text = $0 "\n"
                peer_public_key = ""
                next
        }
        {
                section_text = section_text $0 "\n"
                if (section_name == "Peer" && $0 ~ /^[[:space:]]*PublicKey[[:space:]]*=/) {
                        peer_public_key = $0
                        sub(/^[[:space:]]*PublicKey[[:space:]]*=[[:space:]]*/, "", peer_public_key)
                        sub(/[[:space:]]*$/, "", peer_public_key)
                }
        }
        END {
                if (section_name != "" || section_text != "") {
                        flush_section()
                }
                print count + 0
        }
    ' "$CONFIG_PATH"
}

remove_config_peer() {
	public_key=$1
	awk -v public_key="$public_key" '
        function flush_section() {
                if (!(section_name == "Peer" && peer_public_key == public_key)) {
                        printf "%s", section_text
                }
        }
        /^\[[^]]*\][[:space:]]*$/ {
                if (section_name != "" || section_text != "") {
                        flush_section()
                }
                section_name = $0
                sub(/^\[/, "", section_name)
                sub(/\][[:space:]]*$/, "", section_name)
                section_text = $0 "\n"
                peer_public_key = ""
                next
        }
        {
                section_text = section_text $0 "\n"
                if (section_name == "Peer" && $0 ~ /^[[:space:]]*PublicKey[[:space:]]*=/) {
                        peer_public_key = $0
                        sub(/^[[:space:]]*PublicKey[[:space:]]*=[[:space:]]*/, "", peer_public_key)
                        sub(/[[:space:]]*$/, "", peer_public_key)
                }
        }
        END {
                if (section_name != "" || section_text != "") {
                        flush_section()
                }
        }
    ' "$CONFIG_PATH" >"$config_tmp"
}

remove_registry_peer() {
	name=$1
	address=$2
	public_key=$3
	awk -F '\t' -v name="$name" -v address="$address" -v public_key="$public_key" '
        BEGIN { removed = 0 }
        $0 !~ /^#/ && NF >= 3 && $1 == name && $2 == address && $3 == public_key {
                removed++
                next
        }
        { print $0 }
        END { exit(removed == 1 ? 0 : 1) }
    ' "$REGISTRY_PATH" >"$registry_tmp"
}

rollback_revoked_peer() {
	public_key=$1
	address=$2
	wg set "$INTERFACE_NAME" peer "$public_key" allowed-ips "$address" 2>/dev/null || true
	ip route replace "$address" dev "$INTERFACE_NAME" 2>/dev/null || true
	restore_files
}

revoke_peer() {
	selector=$1
	selector_kind=name
	case "$selector" in
	"$ROAD_WARRIOR_PREFIX".*/32)
		validate_address "$selector"
		selector_kind=address
		;;
	*)
		validate_name "$selector"
		;;
	esac
	require_runtime_commands
	[ "$(id -u)" -eq 0 ] || die "run as root"
	[ -f "$CONFIG_PATH" ] || die "missing $CONFIG_PATH"
	[ -f "$REGISTRY_PATH" ] || die "peer registry is missing: $REGISTRY_PATH"
	wg show "$INTERFACE_NAME" >/dev/null 2>&1 || die "$INTERFACE_NAME is not active"

	acquire_lock
	if [ "$selector_kind" = address ]; then
		peer_name=$(awk -F '\t' -v address="$selector" \
			'$0 !~ /^#/ && NF >= 3 && $2 == address { print $1; exit }' "$REGISTRY_PATH")
	else
		peer_name=$(awk -F '\t' -v name="$selector" \
			'$0 !~ /^#/ && NF >= 3 && $1 == name { print $1; exit }' "$REGISTRY_PATH")
	fi
	[ -n "$peer_name" ] || die "peer not found: $selector"
	peer_address=$(awk -F '\t' -v name="$peer_name" \
		'$0 !~ /^#/ && NF >= 3 && $1 == name { print $2; exit }' "$REGISTRY_PATH")
	peer_public_key=$(awk -F '\t' -v name="$peer_name" \
		'$0 !~ /^#/ && NF >= 3 && $1 == name { print $3; exit }' "$REGISTRY_PATH")
	[ -n "$peer_address" ] || die "peer registry entry has no address: $peer_name"
	[ -n "$peer_public_key" ] || die "peer registry entry has no public key: $peer_name"
	[ "$(config_peer_count "$peer_public_key")" -eq 1 ] ||
		die "peer config entry is missing or ambiguous: $peer_name"

	begin_operation
	remove_config_peer "$peer_public_key"
	remove_registry_peer "$peer_name" "$peer_address" "$peer_public_key" ||
		die "peer registry entry changed while revoking: $peer_name"
	chmod 600 "$config_tmp" "$registry_tmp"
	wg-quick strip "$config_tmp" >/dev/null
	persist_files

	if ! wg set "$INTERFACE_NAME" peer "$peer_public_key" remove; then
		restore_files
		die "failed to remove live WireGuard peer"
	fi
	if address_has_route "$peer_address" &&
		! ip route del "$peer_address" dev "$INTERFACE_NAME"; then
		rollback_revoked_peer "$peer_public_key" "$peer_address"
		die "failed to remove live return route"
	fi

	printf '%s\n' "peer revoked: $peer_name $peer_address" >&2
	printf 'rollback backup: %s\n' "$backup_dir" >&2
}

parse_issue_args() {
	issue_name=
	issue_address=
	issue_profile=simple
	while [ "$#" -gt 0 ]; do
		case "$1" in
		--linux)
			[ "$issue_profile" = simple ] || die "issue profile specified more than once"
			issue_profile=linux
			;;
		--help | -h)
			usage
			return 0
			;;
		-*)
			die "unknown issue option: $1"
			;;
		*)
			if [ -z "$issue_name" ]; then
				issue_name=$1
			elif [ -z "$issue_address" ]; then
				issue_address=$1
			else
				die "issue accepts one name, one optional address, and --linux"
			fi
			;;
		esac
		shift
	done
	[ -n "$issue_name" ] || {
		usage
		return 1
	}
	issue_peer "$issue_name" "$issue_address" "$issue_profile"
}

list_peers() {
	require_command awk
	[ "$(id -u)" -eq 0 ] || die "run as root"
	if [ ! -f "$REGISTRY_PATH" ]; then
		printf '%s\n' 'No road-warrior peers are registered.'
		return 0
	fi
	awk -F '\t' '$0 !~ /^#/ && NF >= 3 { printf "%s\t%s\t%s\n", $1, $2, $3 }' \
		"$REGISTRY_PATH"
}

main() {
	[ "$#" -gt 0 ] || {
		usage
		return 1
	}
	case "$1" in
	add)
		[ "$#" -eq 4 ] || {
			usage
			return 1
		}
		add_peer "$2" "$3" "$4"
		;;
	issue)
		shift
		parse_issue_args "$@"
		;;
	list)
		[ "$#" -eq 1 ] || {
			usage
			return 1
		}
		list_peers
		;;
	revoke)
		[ "$#" -eq 2 ] || {
			usage
			return 1
		}
		revoke_peer "$2"
		;;
	--help | -h)
		usage
		;;
	*)
		usage
		return 1
		;;
	esac
}

main "$@"
