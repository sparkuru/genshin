#!/bin/sh
set -eu

interface_name=${WIREGUARD_INTERFACE:-wg0}
config_path=/etc/wireguard/$interface_name.conf

usage() {
	printf 'Usage: %s\n' "${0##*/}" >&2
}

die() {
	printf 'Error: %s\n' "$*" >&2
	exit 1
}

require_command() {
	command -v "$1" >/dev/null 2>&1 || die "required command not found: $1"
}

cleanup() {
	wg-quick down "$interface_name" >/dev/null 2>&1 || :
}

main() {
	if [ "$#" -gt 0 ]; then
		case "$1" in
		--help | -h)
			usage
			return 0
			;;
		*)
			usage
			return 1
			;;
		esac
	fi

	[ -r "$config_path" ] || die "missing readable WireGuard config: $config_path"
	require_command ip
	require_command wg
	require_command wg-quick

	trap cleanup HUP INT TERM EXIT
	wg-quick up "$interface_name"
	printf '%s\n' "WireGuard interface is up: $interface_name"

	while :; do
		sleep 3600 &
		wait "$!"
	done
}

main "$@"
