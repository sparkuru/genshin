#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_NAME=$(basename "$0")
readonly SCRIPT_NAME
readonly DEFAULT_TIMEOUT=1
readonly DEFAULT_WORKERS=64

readonly STYLE_RESET=$'\033[0m'
readonly STYLE_TITLE=$'\033[1;36m'
readonly STYLE_SUB_TITLE=$'\033[1;32m'
readonly STYLE_EXAMPLE=$'\033[0;37m'
readonly STYLE_SUCCESS=$'\033[0;32m'
readonly STYLE_WARNING=$'\033[1;33m'
readonly STYLE_ERROR=$'\033[1;31m'

DEBUG_MODE=false
target=""
timeout=$DEFAULT_TIMEOUT
workers=$DEFAULT_WORKERS
show_down=false
tmp_dir=""

color_text() {
    local style=$1
    local text=$2

    if [[ -n "${NO_COLOR:-}" || ! -t 1 ]]; then
        printf '%s' "$text"
        return 0
    fi

    printf '%s%s%s' "$style" "$text" "$STYLE_RESET"
}

info() {
    printf '%s\n' "$(color_text "$STYLE_SUCCESS" "$*")"
}

warn() {
    printf '%s\n' "$(color_text "$STYLE_WARNING" "Warning: $*")" >&2
}

die() {
    printf '%s\n' "$(color_text "$STYLE_ERROR" "Error: $*")" >&2
    exit 1
}

debug() {
    [[ "$DEBUG_MODE" == true ]] || return 0
    printf '%s\n' "$(color_text "$STYLE_WARNING" "Debug: $*")" >&2
}

cleanup() {
    [[ -n "${tmp_dir:-}" && -d "$tmp_dir" ]] || return 0
    rm -rf -- "$tmp_dir"
}

usage() {
    printf '%s\n' "$(color_text "$STYLE_TITLE" "Small ICMP ping sweep CLI.")"
    printf 'Usage: %s -h CIDR [-t SECONDS] [-w COUNT] [--show-down] [--log]\n\n' "$SCRIPT_NAME"
    printf '%s\n' "$(color_text "$STYLE_SUB_TITLE" "Options:")"
    printf '  %s  Target network, for example 192.168.9.1/24\n' "$(color_text "$STYLE_SUB_TITLE" "-h, --host CIDR")"
    printf '  %s  Ping timeout per host\n' "$(color_text "$STYLE_SUB_TITLE" "-t, --timeout SECONDS")"
    printf '  %s  Maximum concurrent ping commands\n' "$(color_text "$STYLE_SUB_TITLE" "-w, --workers COUNT")"
    printf '  %s  Print hosts that do not respond\n' "$(color_text "$STYLE_SUB_TITLE" "--show-down")"
    printf '  %s  Enable debug logging\n' "$(color_text "$STYLE_SUB_TITLE" "--log")"
    printf '  %s  Show this help message and exit\n\n' "$(color_text "$STYLE_SUB_TITLE" "--help")"
    printf '%s\n' "$(color_text "$STYLE_SUB_TITLE" "Examples:")"
    printf '  %s\n' "$(color_text "$STYLE_EXAMPLE" "$SCRIPT_NAME -h 192.168.9.1/24")"
    printf '  %s\n' "$(color_text "$STYLE_EXAMPLE" "$SCRIPT_NAME -h 192.168.9.1/24 -t 1 -w 16")"
}

require_command() {
    command -v "$1" >/dev/null 2>&1 || die "required command not found: $1"
}

parse_args() {
    while [[ $# -gt 0 ]]; do
        case "$1" in
            -h | --host)
                [[ $# -ge 2 ]] || die "missing value for $1"
                target=$2
                shift 2
                ;;
            -t | --timeout)
                [[ $# -ge 2 ]] || die "missing value for $1"
                timeout=$2
                shift 2
                ;;
            -w | --workers)
                [[ $# -ge 2 ]] || die "missing value for $1"
                workers=$2
                shift 2
                ;;
            --show-down)
                show_down=true
                shift
                ;;
            --log)
                DEBUG_MODE=true
                shift
                ;;
            --help)
                usage
                exit 0
                ;;
            *)
                die "unknown option: $1"
                ;;
        esac
    done
}

validate_args() {
    [[ -n "$target" ]] || die "target is required"
    [[ "$target" =~ ^([0-9]{1,3}\.){3}[0-9]{1,3}/([0-9]|[12][0-9]|3[0-2])$ ]] || die "target must be CIDR, for example 192.168.9.1/24"
    [[ "$timeout" =~ ^[0-9]+$ && "$timeout" -gt 0 ]] || die "timeout must be a positive integer"
    [[ "$workers" =~ ^[0-9]+$ && "$workers" -gt 0 ]] || die "workers must be a positive integer"
}

ip_to_int() {
    local ip=$1
    local a b c d

    IFS=. read -r a b c d <<<"$ip"
    printf '%u\n' "$(((a << 24) + (b << 16) + (c << 8) + d))"
}

int_to_ip() {
    local value=$1

    printf '%u.%u.%u.%u\n' \
        "$(((value >> 24) & 255))" \
        "$(((value >> 16) & 255))" \
        "$(((value >> 8) & 255))" \
        "$((value & 255))"
}

validate_ip_octets() {
    local ip=${target%/*}
    local a b c d

    IFS=. read -r a b c d <<<"$ip"
    for octet in "$a" "$b" "$c" "$d"; do
        [[ "$octet" -le 255 ]] || die "invalid IPv4 address: $ip"
    done
}

expand_cidr() {
    local ip=${target%/*}
    local prefix=${target#*/}
    local ip_int mask network broadcast start end current

    ip_int=$(ip_to_int "$ip")
    if [[ "$prefix" -eq 0 ]]; then
        mask=0
    else
        mask=$(((0xFFFFFFFF << (32 - prefix)) & 0xFFFFFFFF))
    fi
    network=$((ip_int & mask))
    broadcast=$((network | (0xFFFFFFFF ^ mask)))

    if [[ "$prefix" -ge 31 ]]; then
        start=$network
        end=$broadcast
    else
        start=$((network + 1))
        end=$((broadcast - 1))
    fi

    current=$start
    while [[ "$current" -le "$end" ]]; do
        int_to_ip "$current"
        current=$((current + 1))
    done
}

ping_one() {
    local ip=$1

    debug "ping $ip"
    if ping -c 1 -W "$timeout" "$ip" >/dev/null 2>&1; then
        printf '[+] %s\n' "$ip"
        return 0
    fi

    if [[ "$show_down" == true ]]; then
        printf '[-] %s\n' "$ip"
    fi
    return 1
}

wait_for_slot() {
    while [[ "$(jobs -rp | wc -l)" -ge "$workers" ]]; do
        wait -n || true
    done
}

run_sweep() {
    local alive_count=0
    local host_count=0
    local status_file

    tmp_dir=$(mktemp -d "${TMPDIR:-/tmp}/ping-sweep.XXXXXXXXXX")
    status_file="$tmp_dir/alive"
    trap cleanup EXIT

    info "Start ping sweep: $target"
    while IFS= read -r ip; do
        host_count=$((host_count + 1))
        wait_for_slot
        {
            if ping_one "$ip"; then
                printf '1\n' >>"$status_file"
            fi
        } &
    done < <(expand_cidr)

    wait || true
    if [[ -f "$status_file" ]]; then
        alive_count=$(wc -l <"$status_file")
    fi
    info "Hosts: $host_count"
    info "Alive: $alive_count"
}

main() {
    require_command ping
    require_command mktemp
    require_command wc
    parse_args "$@"
    validate_args
    validate_ip_octets
    run_sweep
}

main "$@"
