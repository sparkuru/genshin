#!/usr/bin/env bash
set -Eeuo pipefail

readonly -a CONFIG_FILES=(
	"baloofilerc"
	"dolphinrc"
	"kdeglobals"
	"kglobalshortcutsrc"
	"khotkeysrc"
	"konsolerc"
	"ksmserverrc"
	"kwinrc"
	"plasmarc"
	"plasma-org.kde.plasma.desktop-appletsrc"
)

readonly -a PLASMA_DIRECTORIES=(
	"desktoptheme/UnityAmbiance"
	"look-and-feel/com.github.yeyushengfan258.WinConceptOS"
	"plasmoids"
)

apply=false
mirror=false
user=''
host=''
control_dir=''
control_path=''
ssh_transport=''

usage() {
	printf 'Usage: %s [--apply] -u <USERNAME> --host <HOST>\n' "$(basename -- "$0")" >&2
	printf '\n' >&2
	printf '  Without --apply, show the rsync changes without writing the target.\n' >&2
	printf '  --apply                 Copy the selected KDE files to the target.\n' >&2
	printf '  -u, --user <USERNAME>   Remote SSH user.\n' >&2
	printf '  --host <HOST>           SSH host or SSH config alias.\n' >&2
	printf '  --mirror                With --apply, remove target-only directory files.\n' >&2
}

die() {
	printf 'Error: %s\n' "$*" >&2
	exit 1
}

require_command() {
	command -v "$1" >/dev/null 2>&1 || die "required command not found: $1"
}

cleanup() {
	if [[ -n "$control_path" && -S "$control_path" && -n "${KDE_SYNC_TARGET:-}" ]]; then
		ssh -o "ControlPath=$control_path" -O exit "$KDE_SYNC_TARGET" >/dev/null 2>&1 || :
	fi
	[[ -n "$control_dir" && -d "$control_dir" ]] && rm -rf -- "$control_dir"
}

establish_connection() {
	control_dir=$(mktemp -d "${TMPDIR:-/tmp}/sync-kde.XXXXXXXXXX")
	control_path="$control_dir/control"
	ssh_transport="ssh -o ControlMaster=auto -o ControlPersist=300 -o ControlPath=$control_path"

	ssh -o ControlMaster=auto -o ControlPersist=300 -o "ControlPath=$control_path" "$KDE_SYNC_TARGET" true
}

sync_path() {
	local source=$1
	local destination=$2
	local -a command

	[[ -e "$source" ]] || {
		printf 'Skip absent path: %s\n' "$source"
		return 0
	}

	command=(rsync -a --human-readable --itemize-changes --protect-args -e "$ssh_transport")
	"$apply" || command+=(--dry-run)
	if "$mirror" && [[ -d "$source" ]]; then
		command+=(--delete --delete-delay)
	fi
	command+=(--exclude '*.bak' --exclude '*.tbcache' --exclude 'containmentpreviews/' -- "$source" "$KDE_SYNC_TARGET:$destination")
	"${command[@]}"
}

prepare_target() {
	ssh -o "ControlPath=$control_path" "$KDE_SYNC_TARGET" 'mkdir -p "$HOME/.config" "$HOME/.local/share/konsole" "$HOME/.local/share/color-schemes" "$HOME/.local/share/plasma/desktoptheme" "$HOME/.local/share/plasma/look-and-feel" "$HOME/.local/share/plasma/plasmoids"'
}

sync() {
	local item

	establish_connection
	if "$apply"; then
		prepare_target
	fi

	for item in "${CONFIG_FILES[@]}"; do
		sync_path "$HOME/.config/$item" './.config/'
	done
	sync_path "$HOME/.local/share/konsole/" './.local/share/konsole/'
	sync_path "$HOME/.local/share/color-schemes/" './.local/share/color-schemes/'
	for item in "${PLASMA_DIRECTORIES[@]}"; do
		sync_path "$HOME/.local/share/plasma/$item/" "./.local/share/plasma/$item/"
	done
}

parse_arguments() {
	while [[ $# -gt 0 ]]; do
		case "$1" in
		--apply)
			apply=true
			shift
			;;
		--mirror)
			mirror=true
			shift
			;;
		-u | --user)
			[[ $# -ge 2 ]] || die "$1 requires a username"
			user=$2
			shift 2
			;;
		--host)
			[[ $# -ge 2 ]] || die "--host requires a host"
			host=$2
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

	[[ -n "$user" ]] || die "--user is required"
	[[ -n "$host" ]] || die "--host is required"
	[[ "$user" != -* && "$host" != -* ]] || die "invalid SSH user or host"
	"$mirror" && ! "$apply" && die "--mirror requires --apply"

	export KDE_SYNC_USER="$user"
	export KDE_SYNC_HOST="$host"
	export KDE_SYNC_TARGET="$KDE_SYNC_USER@$KDE_SYNC_HOST"
	readonly KDE_SYNC_USER KDE_SYNC_HOST KDE_SYNC_TARGET
}

main() {
	require_command rsync
	require_command ssh
	require_command mktemp
	require_command rm
	trap cleanup EXIT

	parse_arguments "$@"
	sync
}

main "$@"
