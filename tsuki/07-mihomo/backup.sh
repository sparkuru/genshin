#!/usr/bin/env bash

set -euo pipefail

readonly NC='\033[0m'
readonly GREEN='\033[0;32m'
readonly RED='\033[31m'
readonly YELLOW='\033[33m'

readonly WORKDIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]:-$0}")" && pwd)"
readonly OS_NAME="$(uname -s)"

operation=""
encrypt_key=""
reload_app=true
sync_link=true
temporary_file=""
replacement_file=""

usage() {
	printf 'usage: %s {enc|dec|show} [-k|--key <key>] [--no-reload] [--no-link]\n' "$0"
}

fail() {
	printf "${RED}%s${NC}\n" "$*" >&2
	exit 1
}

warn() {
	printf "${YELLOW}%s${NC}\n" "$*" >&2
}

info() {
	printf '%s: '"$GREEN"'%s'"$NC"'\n' "$1" "$2"
}

cleanup() {
	[ -z "$temporary_file" ] || rm -f -- "$temporary_file"
	[ -z "$replacement_file" ] || rm -f -- "$replacement_file"
}

trap cleanup EXIT

while [ "$#" -gt 0 ]; do
	case "$1" in
	-k | --key)
		[ "$#" -ge 2 ] || fail "$1 requires a value"
		encrypt_key="$2"
		shift 2
		;;
	--no-reload)
		reload_app=false
		shift
		;;
	--no-link)
		sync_link=false
		shift
		;;
	enc | dec | show)
		[ -z "$operation" ] || fail "operation specified more than once"
		operation="$1"
		shift
		;;
	-h | --help)
		usage
		exit 0
		;;
	*)
		fail "unknown option: $1"
		;;
	esac
done

[ -n "$operation" ] || {
	usage
	exit 1
}

find_genshin_dir() {
	local current_dir="$WORKDIR"

	while [ "$current_dir" != "/" ]; do
		if [ "$(basename -- "$current_dir")" = "03-genshin" ]; then
			printf '%s\n' "$current_dir"
			return
		fi
		current_dir="$(dirname -- "$current_dir")"
	done

	return 1
}

find_mihomo_dir() {
	local candidate
	local candidates=()

	if [ -n "${MIHOMO_PARTY_DIR:-}" ]; then
		candidates=("$MIHOMO_PARTY_DIR")
	else
		case "$OS_NAME" in
		Darwin)
			candidates=(
				"$HOME/Library/Application Support/mihomo-party"
				"$HOME/Library/Application Support/Clash Party"
			)
			;;
		Linux)
			candidates=(
				"${XDG_CONFIG_HOME:-$HOME/.config}/mihomo-party"
				"$HOME/.local/share/mihomo-party"
			)
			;;
		MINGW* | MSYS* | CYGWIN*)
			[ -z "${APPDATA:-}" ] || candidates+=("$APPDATA/mihomo-party")
			candidates+=("/d/software/mihomo-party/data")
			;;
		*)
			return 1
			;;
		esac
	fi

	for candidate in "${candidates[@]}"; do
		if [ -d "$candidate/profiles" ]; then
			printf '%s\n' "$candidate"
			return
		fi
	done

	return 1
}

read_current_profile_id() {
	local profile_config="$1"

	[ -f "$profile_config" ] || return 1
	awk '
        /^[[:space:]]*current:[[:space:]]*/ {
            sub(/^[[:space:]]*current:[[:space:]]*/, "")
            gsub(/^["'"'"']|["'"'"']$/, "")
            print
            exit
        }
    ' "$profile_config"
}

find_profile_path() {
	local data_dir="$1"
	local profiles_dir="$data_dir/profiles"
	local profile_id="${MIHOMO_PROFILE_ID:-}"
	local candidate
	local only_profile=""

	if [ -z "$profile_id" ]; then
		profile_id="$(read_current_profile_id "$data_dir/profile.yaml" || true)"
	fi

	if [ -n "$profile_id" ]; then
		[[ "$profile_id" =~ ^[A-Za-z0-9._-]+$ ]] || fail "invalid current profile id: $profile_id"
		candidate="$profiles_dir/$profile_id.yaml"
		[ -f "$candidate" ] || fail "current profile does not exist: $candidate"
		printf '%s\n' "$candidate"
		return
	fi

	if [ -f "$profiles_dir/magic.yaml" ]; then
		printf '%s\n' "$profiles_dir/magic.yaml"
		return
	fi

	for candidate in "$profiles_dir"/*.yaml; do
		[ -f "$candidate" ] || continue
		[ "$(basename -- "$candidate")" = "default.yaml" ] && continue
		[ -z "$only_profile" ] || fail "cannot determine the active profile from $profiles_dir"
		only_profile="$candidate"
	done

	[ -n "$only_profile" ] || fail "no usable profile found in $profiles_dir"
	printf '%s\n' "$only_profile"
}

find_python() {
	local candidate

	if [ -n "${PYTHON_BIN:-}" ]; then
		command -v "$PYTHON_BIN" >/dev/null 2>&1 || fail "python not found: $PYTHON_BIN"
		command -v "$PYTHON_BIN"
		return
	fi

	for candidate in python3 python; do
		if command -v "$candidate" >/dev/null 2>&1; then
			command -v "$candidate"
			return
		fi
	done

	return 1
}

run_crypto() {
	local mode="$1"
	local input_path="$2"
	local output_path="$3"
	local command=(
		"$PYTHON_PATH"
		"$ENCRYPT_SCRIPT_PATH"
		-i "$input_path"
		-o "$output_path"
	)

	if [ "$mode" = "enc" ]; then
		command+=(-s "$SALT_PATH")
	fi
	if [ -n "$encrypt_key" ]; then
		command+=(-k "$encrypt_key")
	fi
	command+=("$mode")

	"${command[@]}"
}

validate_profile() {
	"$PYTHON_PATH" - "$1" <<'PY'
import sys

path = sys.argv[1]
with open(path, "rb") as profile_file:
    raw = profile_file.read()

if not raw or b"\0" in raw:
    raise SystemExit("decrypted profile is empty or contains null bytes")

try:
    text = raw.decode("utf-8")
except UnicodeDecodeError as error:
    raise SystemExit(f"decrypted profile is not UTF-8: {error}")

try:
    import yaml
except ImportError:
    if not any(
        line.startswith(("proxies:", "proxy-providers:", "proxy-groups:", "rules:"))
        for line in text.splitlines()
    ):
        raise SystemExit("decrypted file does not look like a Mihomo profile")
else:
    profile = yaml.safe_load(text)
    if not isinstance(profile, dict):
        raise SystemExit("decrypted file is not a YAML mapping")
PY
}

sync_profile_link() {
	local link_dir="$WORKDIR/himitsu"
	local link_path="$link_dir/magic.yaml"

	mkdir -p -- "$link_dir"
	if [ -e "$link_path" ] && [ ! -L "$link_path" ]; then
		warn "profile link skipped because a regular file exists: $link_path"
		return
	fi
	ln -sfn -- "$PROFILE_PATH" "$link_path"
}

find_macos_app() {
	local candidate

	for candidate in \
		"/Applications/Clash Party.app" \
		"$HOME/Applications/Clash Party.app" \
		"/Applications/Mihomo Party.app" \
		"$HOME/Applications/Mihomo Party.app"; do
		if [ -d "$candidate" ]; then
			printf '%s\n' "$candidate"
			return
		fi
	done

	return 1
}

reload_macos_app() {
	local app_path
	local app_name
	local executable
	local was_running=false
	local attempt

	app_path="$(find_macos_app || true)"
	[ -n "$app_path" ] || {
		warn "Clash Party application not found; the profile will apply on the next launch"
		return
	}

	app_name="${app_path##*/}"
	app_name="${app_name%.app}"
	executable="$(/usr/libexec/PlistBuddy -c 'Print :CFBundleExecutable' "$app_path/Contents/Info.plist" 2>/dev/null || printf '%s' "$app_name")"

	if pgrep -x "$executable" >/dev/null 2>&1; then
		was_running=true
		osascript -e "tell application \"$app_name\" to quit"
		for attempt in 1 2 3 4 5 6 7 8 9 10; do
			pgrep -x "$executable" >/dev/null 2>&1 || break
			sleep 1
		done
	fi

	if [ "$was_running" = true ]; then
		pgrep -x "$executable" >/dev/null 2>&1 && fail "$app_name did not exit"
		open "$app_path"
		info "application" "$app_name restarted"
	else
		info "application" "$app_name will load the profile on next launch"
	fi
}

GENSHIN_DIR="$(find_genshin_dir)" || fail "03-genshin directory not found"
readonly GENSHIN_DIR
readonly ENCRYPT_SCRIPT_PATH="$GENSHIN_DIR/code/python/02-ez-encrypt.py"
readonly SALT_PATH="$GENSHIN_DIR/paimon"
readonly BACKUP_PATH="${MIHOMO_BACKUP_FILE:-$WORKDIR/magic.yaml}"
MIHOMO_DIR="$(find_mihomo_dir)" || fail "mihomo-party data directory not found for $OS_NAME"
readonly MIHOMO_DIR
PROFILE_PATH="$(find_profile_path "$MIHOMO_DIR")"
readonly PROFILE_PATH
PYTHON_PATH="$(find_python)" || fail "python3 or python is required"
readonly PYTHON_PATH

[ -f "$ENCRYPT_SCRIPT_PATH" ] || fail "encrypt script not found: $ENCRYPT_SCRIPT_PATH"
[ -f "$SALT_PATH" ] || fail "salt file not found: $SALT_PATH"

case "$operation" in
enc)
	backup_dir="$(dirname -- "$BACKUP_PATH")"
	[ -d "$backup_dir" ] || fail "backup directory does not exist: $backup_dir"
	temporary_file="$(mktemp "$backup_dir/.magic.yaml.XXXXXX")"
	run_crypto enc "$PROFILE_PATH" "$temporary_file"
	mv -f -- "$temporary_file" "$BACKUP_PATH"
	temporary_file=""
	[ "$sync_link" = false ] || sync_profile_link
	info "backup" "$BACKUP_PATH"
	;;
dec)
	[ -f "$BACKUP_PATH" ] || fail "backup file not found: $BACKUP_PATH"
	temporary_file="$(mktemp "${TMPDIR:-/tmp}/mihomo-profile.XXXXXX.yaml")"
	run_crypto dec "$BACKUP_PATH" "$temporary_file"
	validate_profile "$temporary_file"

	cp -p -- "$PROFILE_PATH" "$PROFILE_PATH.backup"
	replacement_file="$PROFILE_PATH.new.$$"
	cp -- "$temporary_file" "$replacement_file"
	mv -f -- "$replacement_file" "$PROFILE_PATH"
	replacement_file=""
	rm -f -- "$temporary_file"
	temporary_file=""

	[ "$sync_link" = false ] || sync_profile_link
	info "profile" "$PROFILE_PATH"
	info "previous profile" "$PROFILE_PATH.backup"
	if [ "$OS_NAME" = "Darwin" ] && [ "$reload_app" = true ]; then
		reload_macos_app
	fi
	;;
show)
	info "os" "$OS_NAME"
	info "workdir" "$WORKDIR"
	info "mihomo directory" "$MIHOMO_DIR"
	info "active profile" "$PROFILE_PATH"
	info "backup" "$BACKUP_PATH"
	info "python" "$PYTHON_PATH"
	if [ -n "$encrypt_key" ]; then
		info "encrypt key" "(specified)"
	else
		info "encrypt key" "(not specified)"
	fi
	;;
esac
