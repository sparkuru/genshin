#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)
readonly SCRIPT_DIR
readonly KDE_ROOT="$SCRIPT_DIR"
readonly CONFIG_ROOT="$KDE_ROOT/config"
readonly STATE_ROOT="${XDG_STATE_HOME:-$HOME/.local/state}/mtf-kde-backups"
readonly REPOSITORY_URL="https://github.com/sparkuru/genshin.git"
readonly REPOSITORY_BRANCH="main"

tmp_dir=''

readonly -a CONFIG_FILES=(
	"kdeglobals"
)

readonly -a LEGACY_CONFIG_FILES=(
	"baloofilerc"
	"dolphinrc"
	"kglobalshortcutsrc"
	"khotkeysrc"
	"konsolerc"
	"ksmserverrc"
	"kwinrc"
	"plasmarc"
	"plasma-org.kde.plasma.desktop-appletsrc"
)

usage() {
	printf 'Usage: %s <backup|capture|deploy|status>\n' "$(basename -- "$0")" >&2
	printf '\n' >&2
	printf '  backup   Save the selected current KDE settings into this repository.\n' >&2
	printf '  capture  Alias for backup.\n' >&2
	printf '  deploy   Fetch the repository, install its KDE content, then create links.\n' >&2
	printf '  status   Report whether each selected setting is linked correctly.\n' >&2
}

die() {
	printf 'Error: %s\n' "$*" >&2
	exit 1
}

require_command() {
	command -v "$1" >/dev/null 2>&1 || die "required command not found: $1"
}

cleanup() {
	[[ -n "$tmp_dir" && -d "$tmp_dir" ]] && rm -rf -- "$tmp_dir"
}

link_matches() {
	local target=$1
	local source=$2

	[[ -L "$target" ]] || return 1
	[[ "$(readlink -f -- "$target")" == "$(readlink -f -- "$source")" ]]
}

capture_path() {
	local source=$1
	local destination=$2
	local backup_root=$3
	local backup_path

	[[ -e "$source" ]] || {
		printf 'Skip absent path: %s\n' "$source"
		return 0
	}
	link_matches "$source" "$destination" && {
		printf 'Already captured: %s\n' "$source"
		return 0
	}

	if [[ -e "$destination" || -L "$destination" ]]; then
		backup_path="$backup_root/${destination#"$KDE_ROOT/"}"
		mkdir -p -- "$(dirname -- "$backup_path")"
		mv -- "$destination" "$backup_path"
		printf 'Preserved repository version: %s\n' "$destination"
	fi

	mkdir -p -- "$(dirname -- "$destination")"
	cp -a -- "$source" "$destination"
	printf 'Captured: %s\n' "$source"
}

deploy_path() {
	local source=$1
	local target=$2
	local backup_root=$3
	local backup_path

	[[ -e "$source" ]] || die "repository setting is absent: $source"
	link_matches "$target" "$source" && {
		printf 'Linked: %s\n' "$target"
		return 0
	}

	if [[ -e "$target" || -L "$target" ]]; then
		backup_path="$backup_root/${target#"$HOME/"}"
		mkdir -p -- "$(dirname -- "$backup_path")"
		mv -- "$target" "$backup_path"
		printf 'Backed up: %s\n' "$target"
	fi

	mkdir -p -- "$(dirname -- "$target")"
	ln -s -- "$source" "$target"
	printf 'Linked: %s\n' "$target"
}

backup() {
	local item
	local timestamp
	local backup_root

	timestamp=$(date '+%Y%m%d-%H%M%S')
	backup_root="$STATE_ROOT/repository-$timestamp"

	for item in "${CONFIG_FILES[@]}"; do
		capture_path "$HOME/.config/$item" "$CONFIG_ROOT/$item" "$backup_root"
	done
}

refresh_kde_content() {
	local source_root=$1
	local source
	local destination
	local timestamp
	local backup_root

	timestamp=$(date '+%Y%m%d-%H%M%S')
	backup_root="$STATE_ROOT/repository-refresh-$timestamp"
	source="$source_root/config"
	destination="$KDE_ROOT/config"
	[[ -e "$source" ]] || die "downloaded KDE content is absent: $source"

	if [[ -e "$destination" || -L "$destination" ]]; then
		mkdir -p -- "$(dirname -- "$backup_root/config")"
		mv -- "$destination" "$backup_root/config"
		printf 'Preserved local KDE content: %s\n' "$destination"
	fi

	mv -- "$source" "$destination"
	printf 'Moved downloaded KDE content: %s\n' "$destination"
}

remove_obsolete_link() {
	local target=$1
	local link_target

	[[ -L "$target" ]] || return 0
	link_target=$(readlink -- "$target")
	case "$link_target" in
	"$KDE_ROOT"/*)
		rm -- "$target"
		printf 'Removed obsolete link: %s\n' "$target"
		;;
	esac
}

prune_obsolete_links() {
	local item

	for item in "${LEGACY_CONFIG_FILES[@]}"; do
		remove_obsolete_link "$HOME/.config/$item"
	done
}

fetch_kde_content() {
	local repository_dir
	local source_root

	tmp_dir=$(mktemp -d "${TMPDIR:-/tmp}/mtf-kde.XXXXXXXXXX")
	repository_dir="$tmp_dir/repository"
	git clone --depth=1 --branch "$REPOSITORY_BRANCH" "$REPOSITORY_URL" "$repository_dir"
	source_root="$repository_dir/mtf/kde"
	[[ -d "$source_root" ]] || die "downloaded repository does not contain mtf/kde"
	refresh_kde_content "$source_root"
}

deploy() {
	local item
	local timestamp
	local backup_root

	timestamp=$(date '+%Y%m%d-%H%M%S')
	backup_root="$STATE_ROOT/$timestamp"
	fetch_kde_content
	prune_obsolete_links
	for item in "${CONFIG_FILES[@]}"; do
		deploy_path "$CONFIG_ROOT/$item" "$HOME/.config/$item" "$backup_root"
	done
	printf 'Conflicting settings were saved below: %s\n' "$backup_root"
}

status() {
	local item
	local source
	local target
	local missing=0

	while IFS=$'\t' read -r source target; do
		if link_matches "$target" "$source"; then
			printf 'linked  %s\n' "$target"
		else
			printf 'missing %s\n' "$target"
			missing=1
		fi
	done < <(
		for item in "${CONFIG_FILES[@]}"; do
			printf '%s\t%s\n' "$CONFIG_ROOT/$item" "$HOME/.config/$item"
		done
	)

	return "$missing"
}

main() {
	require_command cp
	require_command date
	require_command ln
	require_command mkdir
	require_command mv
	require_command readlink
	require_command rm
	trap cleanup EXIT

	case "${1:-}" in
	backup | capture)
		[[ $# -eq 1 ]] || die "$1 accepts no options"
		backup
		;;
	deploy)
		[[ $# -eq 1 ]] || die "deploy accepts no options"
		require_command git
		require_command mktemp
		deploy
		;;
	status)
		[[ $# -eq 1 ]] || die "status accepts no options"
		status
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
