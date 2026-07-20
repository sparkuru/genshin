#!/usr/bin/env bash
set -Eeuo pipefail

readonly SCRIPT_NAME=${0##*/}
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly SCRIPT_DIR=$script_dir
unset script_dir
readonly BIND_IP_COMPOSE_PATTERN="\${HEDGEDOC_BIND_IP:-0.0.0.0}"
readonly STYLE_RESET=$'\033[0m'
readonly STYLE_SUCCESS=$'\033[0;32m'
readonly STYLE_ERROR=$'\033[1;31m'

install_dir=$SCRIPT_DIR
bind_ip=''
public_host=''
port=''
protocol=''
compose_file=''
runtime_env_path=''
temp_env_path=''
backup_env_path=''
services=()

usage() {
	printf 'Usage: %s --ip <IPv4-address> --port <port> [options]\n' "$SCRIPT_NAME" >&2
	printf '\nChange the HedgeDoc bind address and restart only HedgeDoc services.\n' >&2
	printf '\nOptions:\n' >&2
	printf '  --ip <address>       Host IPv4 address to bind (required; use 0.0.0.0 for all interfaces).\n' >&2
	printf '  --domain <name>      Hostname used in the public URL (default: bind IP).\n' >&2
	printf '  --port <port>        Host and HedgeDoc application port (required).\n' >&2
	printf '  --path <directory>   HedgeDoc installation directory (default: script directory).\n' >&2
	printf '  --compose-file <f>   Compose file; required when both deployment modes exist.\n' >&2
	printf '  --protocol <http|https>  Public URL protocol (default: current setting).\n' >&2
	printf '  --help               Show this help message.\n' >&2
	printf '\nExamples:\n' >&2
	printf '  %s --ip 192.168.1.90 --domain schale.local --port 80\n' "$SCRIPT_NAME" >&2
	printf '  %s --ip 0.0.0.0 --domain schale.local --port 80\n' "$SCRIPT_NAME" >&2
}

color_text() {
	local style=$1
	local message=$2

	if [[ -n ${NO_COLOR:-} || ! -t 1 ]]; then
		printf '%s' "$message"
		return
	fi

	printf '%s%s%s' "$style" "$message" "$STYLE_RESET"
}

info() {
	printf '%s\n' "$(color_text "$STYLE_SUCCESS" "$*")"
}

die() {
	printf '%s\n' "$(color_text "$STYLE_ERROR" "Error: $*")" >&2
	exit 1
}

require_command() {
	command -v "$1" >/dev/null 2>&1 || die "required command not found: $1"
}

cleanup() {
	if [[ -n $temp_env_path && -f $temp_env_path ]]; then
		rm -f -- "$temp_env_path"
	fi
}

validate_ipv4() {
	local value=$1
	local octet
	local -a octets

	[[ $value =~ ^[0-9]+(\.[0-9]+){3}$ ]] || die "invalid IPv4 address: $value"
	IFS=. read -r -a octets <<<"$value"
	for octet in "${octets[@]}"; do
		((10#$octet <= 255)) || die "invalid IPv4 address: $value"
	done
}

validate_port() {
	[[ $port =~ ^[0-9]{1,5}$ ]] || die "invalid port: $port"
	((10#$port >= 1 && 10#$port <= 65535)) || die 'port must be between 1 and 65535'
}

validate_public_host() {
	[[ $public_host =~ ^[^/:[:space:]]+$ ]] || die "invalid domain or public host: $public_host"
}

parse_arguments() {
	while (($# > 0)); do
		case $1 in
		--ip)
			(($# >= 2)) || die '--ip requires an IPv4 address'
			[[ -z $bind_ip ]] || die '--ip may only be specified once'
			bind_ip=$2
			shift 2
			;;
		--port)
			(($# >= 2)) || die '--port requires a value'
			[[ -z $port ]] || die '--port may only be specified once'
			port=$2
			shift 2
			;;
		--domain)
			(($# >= 2)) || die '--domain requires a hostname'
			[[ -z $public_host ]] || die '--domain may only be specified once'
			public_host=$2
			shift 2
			;;
		--path)
			(($# >= 2)) || die '--path requires a directory'
			install_dir=$2
			shift 2
			;;
		--compose-file)
			(($# >= 2)) || die '--compose-file requires a file'
			[[ -z $compose_file ]] || die '--compose-file may only be specified once'
			compose_file=$2
			shift 2
			;;
		--protocol)
			(($# >= 2)) || die '--protocol requires http or https'
			[[ -z $protocol ]] || die '--protocol may only be specified once'
			protocol=$2
			shift 2
			;;
		--help | -h)
			usage
			exit 0
			;;
		*)
			die "unknown option: $1"
			;;
		esac
	done

	[[ -n $bind_ip ]] || die '--ip is required; use --ip 0.0.0.0 to bind all interfaces (for example, with --domain schale.local)'
	[[ -n $port ]] || die '--port is required'
	validate_ipv4 "$bind_ip"
	validate_port
	if [[ -z $public_host ]]; then
		[[ $bind_ip != 0.0.0.0 ]] || die '--domain is required when --ip is 0.0.0.0; for example, add --domain schale.local'
		public_host=$bind_ip
	fi
	validate_public_host

	case $protocol in
	'' | http | https) ;;
	*)
		die '--protocol must be http or https'
		;;
	esac
}

resolve_paths() {
	if [[ $install_dir != /* ]]; then
		install_dir=$PWD/$install_dir
	fi
	install_dir=${install_dir%/}
	[[ -d $install_dir ]] || die "installation directory not found: $install_dir"

	runtime_env_path=$install_dir/.hedgedoc.env
	[[ -f $runtime_env_path ]] || die "runtime environment not found: $runtime_env_path"
	[[ -x $install_dir/init-hedgedoc.sh ]] || die "initializer not found or not executable: $install_dir/init-hedgedoc.sh"

	if [[ -n $compose_file ]]; then
		if [[ $compose_file != /* ]]; then
			compose_file=$install_dir/$compose_file
		fi
	else
		local offline_file="$install_dir/hedgedoc-offline.yml"
		local external_file="$install_dir/hedgedoc.yml"
		if [[ -f $offline_file && ! -f $external_file ]]; then
			compose_file=$offline_file
		elif [[ -f $external_file && ! -f $offline_file ]]; then
			compose_file=$external_file
		else
			die 'both compose files exist; pass --compose-file hedgedoc-offline.yml or --compose-file hedgedoc.yml'
		fi
	fi

	[[ -f $compose_file ]] || die "compose file not found: $compose_file"
	if grep -Fq 'container_name: hedgedoc_nginx' "$compose_file"; then
		services=(hedgedoc nginx)
	else
		services=(hedgedoc)
	fi
	grep -Fq "$BIND_IP_COMPOSE_PATTERN" "$compose_file" || die 'compose file does not support HEDGEDOC_BIND_IP; use the updated deployment template'
}

read_runtime_value() {
	local key=$1
	awk -F= -v key="$key" '$1 == key { print substr($0, length(key) + 2); exit }' "$runtime_env_path"
}

resolve_protocol() {
	if [[ -n $protocol ]]; then
		return
	fi

	if [[ $(read_runtime_value CMD_PROTOCOL_USESSL) == true ]]; then
		protocol=https
	else
		protocol=http
	fi
}

backup_runtime_env() {
	backup_env_path=$(mktemp "$runtime_env_path.backup.XXXXXXXX")
	cp -- "$runtime_env_path" "$backup_env_path"
	chmod 600 -- "$backup_env_path"
}

set_bind_ip() {
	temp_env_path=$(mktemp "$runtime_env_path.XXXXXXXX")
	awk -F= -v bind_ip="$bind_ip" '
	BEGIN { updated = 0 }
	$1 == "HEDGEDOC_BIND_IP" {
		if (!updated) {
			print "HEDGEDOC_BIND_IP=" bind_ip
			updated = 1
		}
		next
	}
	{ print }
	END {
		if (!updated) print "HEDGEDOC_BIND_IP=" bind_ip
	}
	' "$runtime_env_path" >"$temp_env_path"
	chmod 600 -- "$temp_env_path"
	mv -- "$temp_env_path" "$runtime_env_path"
	temp_env_path=''
}

restart_services() {
	local -a compose_command=(docker compose --env-file "$runtime_env_path" -f "$compose_file")

	"${compose_command[@]}" config --quiet
	"${compose_command[@]}" up -d --no-deps --force-recreate "${services[@]}"
}

main() {
	parse_arguments "$@"
	require_command awk
	require_command grep
	resolve_paths
	resolve_protocol
	require_command chmod
	require_command cp
	require_command docker
	require_command mktemp
	require_command mv
	docker compose version >/dev/null 2>&1 || die 'Docker Compose v2 is required'

	backup_runtime_env
	"$install_dir/init-hedgedoc.sh" --public-url "$protocol://$public_host:$port" --force
	set_bind_ip
	restart_services

	info 'HedgeDoc address updated and services restarted'
	printf '  Bind address: %s:%s\n' "$bind_ip" "$port"
	printf '  Public URL: %s://%s:%s\n' "$protocol" "$public_host" "$port"
	printf '  Compose file: %s\n' "$compose_file"
	printf '  Database service was not restarted or removed\n'
	printf '  Environment backup: %s\n' "$backup_env_path"
}

trap cleanup EXIT
main "$@"
