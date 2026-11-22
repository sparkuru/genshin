#!/usr/bin/env bash
set -Eeuo pipefail

readonly SCRIPT_NAME="${0##*/}"
script_dir_path="$(
    case "${BASH_SOURCE[0]}" in
    */*) cd -- "${BASH_SOURCE[0]%/*}" ;;
    *) cd -- . ;;
    esac
    pwd -P
)"
readonly SCRIPT_DIR="$script_dir_path"
unset script_dir_path

usage() {
    printf 'Usage: %s [--force] [--help]\n\n' "$SCRIPT_NAME"
    printf 'Sync managed Herdr settings from sync.config.json.\n'
    printf 'Existing configurations require --force if changes are needed.\n'
    printf 'HERDR_CONFIG_PATH and XDG_CONFIG_HOME select the target configuration.\n'
    printf 'Requires Python 3.11 or later.\n'
}

die() {
    printf 'Error: %s\n' "$*" >&2
    exit 1
}

main() {
    local force=false
    while [[ $# -gt 0 ]]; do
        case "$1" in
        --force) force=true ;;
        --help | -h)
            usage
            return 0
            ;;
        *)
            usage >&2
            die "unknown option: $1"
            ;;
        esac
        shift
    done

    command -v python3 >/dev/null 2>&1 || die "required command not found: python3"
    python3 -c 'import fcntl, tomllib' 2>/dev/null || die "Python 3.11 or later with fcntl is required"

    local source_config="$SCRIPT_DIR/sync.config.json"
    local config_updater="$SCRIPT_DIR/sync_config.py"
    [[ -f "$source_config" ]] || die "source file not found: $source_config"
    [[ -f "$config_updater" ]] || die "source file not found: $config_updater"

    local target_path
    if [[ -n "${HERDR_CONFIG_PATH:-}" ]]; then
        target_path="$HERDR_CONFIG_PATH"
    else
        target_path="${XDG_CONFIG_HOME:-${HOME:?HOME is not set}/.config}/herdr/config.toml"
    fi

    local -a updater_args=("$source_config" "$target_path")
    if [[ "$force" == true ]]; then
        updater_args+=(--force)
    fi
    python3 "$config_updater" "${updater_args[@]}"
}

main "$@"
