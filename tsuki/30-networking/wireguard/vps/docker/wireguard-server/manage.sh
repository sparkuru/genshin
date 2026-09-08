#!/bin/sh
set -eu

script_dir=$(
	CDPATH=
	cd -- "$(dirname -- "$0")" && pwd
)
compose_file=$script_dir/wireguard-server.yml
container_name=wireguard-server

usage() {
	printf '%s\n' "Usage: ${0##*/} <command> [arguments...]" >&2
	printf '%s\n' 'Commands:' >&2
	printf '%s\n' '  validate                         Validate the Compose model' >&2
	printf '%s\n' '  build                            Build the WireGuard image' >&2
	printf '%s\n' '  up                               Build and start the container' >&2
	printf '%s\n' '  down                             Stop and remove the container' >&2
	printf '%s\n' '  restart                          Restart the container' >&2
	printf '%s\n' '  status                           Show container, WireGuard, and route state' >&2
	printf '%s\n' '  logs [lines]                     Show recent container logs' >&2
	printf '%s\n' '  road-list                        List registered road-warrior peers' >&2
	printf '%s\n' '  road-add <name> <address> <key>  Add one road-warrior peer' >&2
	printf '%s\n' '  road-issue <name> [address] [--linux]  Generate and issue a client config' >&2
	printf '%s\n' '  road-revoke <name|address>       Revoke one road-warrior peer' >&2
}

die() {
	printf 'Error: %s\n' "$*" >&2
	exit 1
}

require_docker() {
	command -v docker >/dev/null 2>&1 || die 'required command not found: docker'
	docker compose version >/dev/null 2>&1 || die 'Docker Compose plugin is unavailable'
}

compose() {
	docker compose -f "$compose_file" "$@"
}

container_exec() {
	docker exec "$container_name" "$@"
}

main() {
	[ "$#" -gt 0 ] || {
		usage
		return 1
	}

	require_docker

	case "$1" in
	validate)
		[ "$#" -eq 1 ] || die 'validate takes no arguments'
		compose config --quiet
		;;
	build)
		[ "$#" -eq 1 ] || die 'build takes no arguments'
		compose build
		;;
	up)
		[ "$#" -eq 1 ] || die 'up takes no arguments'
		compose up -d --build
		;;
	down)
		[ "$#" -eq 1 ] || die 'down takes no arguments'
		compose down
		;;
	restart)
		[ "$#" -eq 1 ] || die 'restart takes no arguments'
		compose restart
		;;
	status)
		[ "$#" -eq 1 ] || die 'status takes no arguments'
		compose ps
		printf '%s\n' '--- wg show ---'
		container_exec wg show wg0
		printf '%s\n' '--- routes ---'
		container_exec ip -4 route show dev wg0
		;;
	logs)
		[ "$#" -le 2 ] || die 'logs accepts at most one line-count argument'
		line_count=${2:-100}
		case "$line_count" in
		'' | *[!0-9]*) die 'line count must be a non-negative integer' ;;
		esac
		compose logs --tail="$line_count" wireguard
		;;
	road-list)
		[ "$#" -eq 1 ] || die 'road-list takes no arguments'
		container_exec /usr/local/sbin/overlap-vpn-road-peer list
		;;
	road-add)
		[ "$#" -eq 4 ] || die 'road-add requires name, address, and public key'
		shift
		container_exec /usr/local/sbin/overlap-vpn-road-peer add "$@"
		;;
	road-issue)
		[ "$#" -ge 2 ] || die 'road-issue requires a peer name'
		shift
		container_exec /usr/local/sbin/overlap-vpn-road-peer issue "$@"
		;;
	road-revoke)
		[ "$#" -eq 2 ] || die 'road-revoke requires a peer name or address'
		container_exec /usr/local/sbin/overlap-vpn-road-peer revoke "$2"
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
