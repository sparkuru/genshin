#!/bin/sh
set -eu

script_name=${0##*/}
interface_name=${WIREGUARD_INTERFACE:-wg0}
config_path=${WIREGUARD_CONFIG:-}
registry_path=${ROAD_WARRIOR_REGISTRY:-/etc/overlap-vpn/road-warriors.tsv}
project_dir=${WIREGUARD_PROJECT_DIR:-/opt/wireguard-server}
output_dir=${OVERLAP_VPN_BACKUP_DIR:-/var/backups/overlap-vpn}
stage_dir=
archive_tmp=
checksum_tmp=

usage() {
	cat >&2 <<EOF
Usage: $script_name [options]

Create an owner-only backup of the VPS WireGuard state and deployment files.

Options:
  --output-dir DIR   Archive directory (default: $output_dir)
  --project-dir DIR  WireGuard Docker project (default: $project_dir)
  --config PATH      WireGuard config (default: /etc/wireguard/NAME.conf)
  --registry PATH    Road-warrior registry (default: $registry_path)
  --interface NAME   WireGuard interface (default: $interface_name)
  -h, --help         Show this help
EOF
}

die() {
	printf 'Error: %s\n' "$*" >&2
	exit 1
}

require_command() {
	command -v "$1" >/dev/null 2>&1 || die "required command not found: $1"
}

cleanup() {
	if [ -n "${archive_tmp:-}" ] && [ -e "$archive_tmp" ]; then
		rm -f -- "$archive_tmp"
	fi
	if [ -n "${checksum_tmp:-}" ] && [ -e "$checksum_tmp" ]; then
		rm -f -- "$checksum_tmp"
	fi
	case "${stage_dir:-}" in
	/tmp/overlap-vpn-backup.*)
		if [ -d "$stage_dir" ]; then
			rm -rf -- "$stage_dir"
		fi
		;;
	esac
}

copy_file() {
	source_path=$1
	destination_path=$2
	[ -f "$source_path" ] || die "missing file: $source_path"
	cp -p -- "$source_path" "$destination_path"
}

write_runtime_state() {
	if wg show "$interface_name" >"$stage_dir/state/wg-show.txt" 2>/dev/null; then
		:
	else
		printf 'interface unavailable: %s\n' "$interface_name" >"$stage_dir/state/wg-show.txt"
	fi

	if ip -4 route show dev "$interface_name" >"$stage_dir/state/routes.txt" 2>/dev/null; then
		:
	else
		printf 'interface unavailable: %s\n' "$interface_name" >"$stage_dir/state/routes.txt"
	fi
}

write_manifest() {
	manifest_path=$stage_dir/MANIFEST.sha256
	(
		cd "$stage_dir"
		find . -type f ! -path './MANIFEST.sha256' -print | sort |
			while IFS= read -r relative_path; do
				sha256sum "$relative_path"
			done
	) >"$manifest_path"
	chmod 600 "$manifest_path"
}

parse_options() {
	while [ "$#" -gt 0 ]; do
		case $1 in
		--output-dir)
			[ "$#" -ge 2 ] || die "$1 requires a directory"
			output_dir=$2
			shift 2
			;;
		--project-dir)
			[ "$#" -ge 2 ] || die "$1 requires a directory"
			project_dir=$2
			shift 2
			;;
		--config)
			[ "$#" -ge 2 ] || die "$1 requires a path"
			config_path=$2
			shift 2
			;;
		--registry)
			[ "$#" -ge 2 ] || die "$1 requires a path"
			registry_path=$2
			shift 2
			;;
		--interface)
			[ "$#" -ge 2 ] || die "$1 requires a name"
			interface_name=$2
			shift 2
			;;
		-h | --help)
			usage
			return 1
			;;
		--)
			shift
			[ "$#" -eq 0 ] || die "unexpected argument: $1"
			return 0
			;;
		-*)
			die "unknown option: $1"
			;;
		*)
			die "unexpected argument: $1"
			;;
		esac
	done
}

main() {
	parse_options "$@" || return 0

	[ "$(id -u)" -eq 0 ] || die 'run as root so the WireGuard private key can be backed up safely'
	[ -n "$interface_name" ] || die 'interface name must not be empty'
	[ -n "$config_path" ] || config_path=/etc/wireguard/$interface_name.conf
	[ -f "$config_path" ] || die "missing WireGuard config: $config_path"
	[ -f "$registry_path" ] || die "missing road-warrior registry: $registry_path"
	[ -d "$project_dir" ] || die "missing WireGuard project: $project_dir"

	for command_name in cp date find id ip mktemp rm sha256sum tar wg; do
		require_command "$command_name"
	done

	trap cleanup EXIT HUP INT TERM
	mkdir -p "$output_dir"
	chmod 700 "$output_dir"
	stage_dir=$(mktemp -d /tmp/overlap-vpn-backup.XXXXXXXX)
	mkdir -p "$stage_dir/etc/wireguard" "$stage_dir/etc/overlap-vpn" "$stage_dir/project" "$stage_dir/state"

	copy_file "$config_path" "$stage_dir/etc/wireguard/$interface_name.conf"
	chmod 600 "$stage_dir/etc/wireguard/$interface_name.conf"
	copy_file "$registry_path" "$stage_dir/etc/overlap-vpn/road-warriors.tsv"
	chmod 600 "$stage_dir/etc/overlap-vpn/road-warriors.tsv"

	for relative_path in \
		.dockerignore \
		Dockerfile \
		README.md \
		entrypoint.sh \
		manage.sh \
		road-warrior-peer.sh \
		wg0.conf.example \
		wireguard-server.yml; do
		copy_file "$project_dir/$relative_path" "$stage_dir/project/$relative_path"
	done

	write_runtime_state
	write_manifest

	timestamp=$(date -u +%Y%m%dT%H%M%SZ)
	archive_path=$output_dir/overlap-vpn-state-$timestamp.tar.gz
	[ ! -e "$archive_path" ] || die "backup already exists: $archive_path"
	[ ! -e "$archive_path.sha256" ] || die "checksum already exists: $archive_path.sha256"

	archive_tmp=$(mktemp "$output_dir/.overlap-vpn-state.XXXXXXXX")
	tar -czf "$archive_tmp" -C "$stage_dir" .
	chmod 600 "$archive_tmp"
	mv -- "$archive_tmp" "$archive_path"
	archive_tmp=

	tar -tzf "$archive_path" >/dev/null
	checksum_tmp=$(mktemp "$output_dir/.overlap-vpn-checksum.XXXXXXXX")
	sha256sum "$archive_path" >"$checksum_tmp"
	chmod 600 "$checksum_tmp"
	mv -- "$checksum_tmp" "$archive_path.sha256"
	checksum_tmp=

	printf 'backup archive: %s\n' "$archive_path"
	printf 'checksum file: %s\n' "$archive_path.sha256"
	printf '%s\n' 'The archive contains /etc/wireguard/wg0.conf; keep it root-only and encrypt it before off-host storage.' >&2
}

main "$@"
