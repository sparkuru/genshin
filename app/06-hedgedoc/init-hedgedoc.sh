#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
readonly SCRIPT_DIR
readonly RUNTIME_ENV_PATH="$SCRIPT_DIR/.hedgedoc.env"
readonly SESSION_SECRET_PATH="$SCRIPT_DIR/config/secrets/session-secret"

die() {
	printf 'Error: %s\n' "$*" >&2
	exit 1
}

usage() {
	printf 'Usage: %s --public-url <http://host[:port]|https://host[:port]> [--db-url <url>] [--force]\n' "${0##*/}"
}

parse_public_url() {
	local public_url=$1

	if [[ ! $public_url =~ ^(http|https)://([^/:]+)(:([1-9][0-9]{0,4}))?/?$ ]]; then
		die 'public URL must be an HTTP(S) origin without a path'
	fi

	protocol=${BASH_REMATCH[1]}
	domain=${BASH_REMATCH[2]}
	port=${BASH_REMATCH[4]:-}

	if [[ -z $port ]]; then
		if [[ $protocol == https ]]; then
			port=443
		else
			port=80
		fi
	fi

	((port <= 65535)) || die 'public URL port must be between 1 and 65535'

	if [[ $protocol == https ]]; then
		protocol_use_ssl=true
	else
		protocol_use_ssl=false
	fi

	if { [[ $protocol == http ]] && ((port == 80)); } || { [[ $protocol == https ]] && ((port == 443)); }; then
		url_add_port=false
		allow_origin=$domain
	else
		url_add_port=true
		allow_origin="$domain:$port"
	fi
}

generate_secret() {
	local secret_path=$1

	if [[ -f $secret_path ]]; then
		return
	fi

	umask 077
	mkdir -p -- "$(dirname -- "$secret_path")"
	openssl rand -hex 64 >"$secret_path"
}

write_runtime_env() {
	local output_path=$1
	local db_url=$2
	local db_password=$3
	local db_root_password=$4
	local bind_ip=$5
	local tmp_path

	tmp_path=$(mktemp "${output_path}.XXXXXX")
	{
		printf 'HEDGEDOC_HOST_PORT=%s\n' "$port"
		printf 'HEDGEDOC_APP_PORT=%s\n' "$port"
		printf 'HEDGEDOC_BIND_IP=%s\n' "$bind_ip"
		printf 'CMD_DOMAIN=%s\n' "$domain"
		printf 'CMD_PROTOCOL_USESSL=%s\n' "$protocol_use_ssl"
		printf 'CMD_URL_ADDPORT=%s\n' "$url_add_port"
		printf 'CMD_ALLOW_ORIGIN=%s\n' "$allow_origin"
		printf 'CMD_CSP_ENABLE=true\n'
		printf 'HEDGEDOC_DB_PASSWORD=%s\n' "$db_password"
		printf 'HEDGEDOC_DB_ROOT_PASSWORD=%s\n' "$db_root_password"
		[[ -n $db_url ]] && printf 'CMD_DB_URL=%s\n' "$db_url"
	} >"$tmp_path"
	chmod 600 -- "$tmp_path"
	mv -- "$tmp_path" "$output_path"
}

read_runtime_value() {
	local key=$1

	awk -F= -v key="$key" '$1 == key { print substr($0, length(key) + 2); exit }' "$RUNTIME_ENV_PATH"
}

main() {
	local public_url=''
	local db_url=''
	local force=false
	local db_password
	local db_root_password
	local bind_ip

	while (($# > 0)); do
		case $1 in
		--public-url)
			(($# >= 2)) || die '--public-url requires a value'
			public_url=$2
			shift 2
			;;
		--db-url)
			(($# >= 2)) || die '--db-url requires a value'
			db_url=$2
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
			die "unknown argument: $1"
			;;
		esac
	done

	[[ -n $public_url ]] || die '--public-url is required'
	command -v openssl >/dev/null 2>&1 || die 'required command not found: openssl'
	parse_public_url "$public_url"

	if [[ -f $RUNTIME_ENV_PATH && $force != true ]]; then
		die "$RUNTIME_ENV_PATH already exists; use --force to replace it"
	fi

	if [[ -d $SCRIPT_DIR/db && ! -f $RUNTIME_ENV_PATH ]]; then
		die 'existing database detected; restore its passwords in .hedgedoc.env before continuing'
	fi

	if [[ -f $RUNTIME_ENV_PATH ]]; then
		db_password=$(read_runtime_value HEDGEDOC_DB_PASSWORD)
		db_root_password=$(read_runtime_value HEDGEDOC_DB_ROOT_PASSWORD)
		bind_ip=$(read_runtime_value HEDGEDOC_BIND_IP)
		[[ -n $db_password && -n $db_root_password ]] || die 'existing runtime environment has no database passwords'
		[[ -n $db_url ]] || db_url=$(read_runtime_value CMD_DB_URL)
	else
		db_password=$(openssl rand -hex 32)
		db_root_password=$(openssl rand -hex 32)
		bind_ip=''
	fi
	bind_ip=${bind_ip:-0.0.0.0}
	generate_secret "$SESSION_SECRET_PATH"
	write_runtime_env "$RUNTIME_ENV_PATH" "$db_url" "$db_password" "$db_root_password" "$bind_ip"

	printf 'Created %s\n' "$RUNTIME_ENV_PATH"
	printf 'Public URL: %s://%s' "$protocol" "$domain"
	if [[ $url_add_port == true ]]; then
		printf ':%s' "$port"
	fi
	printf '\nRuntime configuration initialized\n'
}

main "$@"
