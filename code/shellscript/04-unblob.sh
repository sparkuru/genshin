#!/usr/bin/env bash
set -Eeuo pipefail

readonly SCRIPT_NAME=$(basename "$0")
readonly STYLE_RESET=$'\033[0m'
readonly STYLE_TITLE=$'\033[1;36m'
readonly STYLE_SUB_TITLE=$'\033[1;32m'
readonly STYLE_CONTENT=$'\033[1;37m'
readonly STYLE_EXAMPLE=$'\033[0;37m'
readonly STYLE_SUCCESS=$'\033[0;32m'
readonly STYLE_WARNING=$'\033[1;33m'
readonly STYLE_ERROR=$'\033[1;31m'

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

usage() {
    printf '%s\n' "$(color_text "$STYLE_TITLE" "Usage:")" >&2
    printf '  %s %s\n' "$SCRIPT_NAME" "$(color_text "$STYLE_CONTENT" "<file_path>")" >&2
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

require_command() {
    command -v "$1" >/dev/null 2>&1 || die "required command not found: $1"
}

cleanup() {
    if [[ -n "$tmp_dir" && -d "$tmp_dir" ]]; then
        rm -rf -- "$tmp_dir"
    fi
}

confirm_package() {
    local tar_path=$1
    local package_reply

    printf '%s ' "$(color_text "$STYLE_WARNING" "Package firmware archive at $tar_path? y/[n]:")" >&2
    read -r package_reply

    case "$package_reply" in
    y | Y)
        return 0
        ;;
    *)
        return 1
        ;;
    esac
}

extract_firmware() {
    local file_path=$1
    local file_name=$2
    local input_dir=$3
    local output_dir=$4

    mkdir -p -- "$input_dir" "$output_dir"
    cp -- "$file_path" "$input_dir/$file_name"

    docker run \
        --rm \
        --pull always \
        -u "$(id -u):$(id -g)" \
        -v "$output_dir:/data/output" \
        -v "$input_dir:/data/input:ro" \
        ghcr.io/onekey-sec/unblob:latest "/data/input/$file_name"
}

main() {
    if [[ $# -ne 1 ]]; then
        usage
        return 1
    fi

    require_command docker
    docker info >/dev/null 2>&1 || die 'docker is unavailable; start Docker or check permissions'

    local file_path=$1
    [[ -f "$file_path" ]] || die "input is not a regular file: $file_path"
    [[ -r "$file_path" ]] || die "input is not readable: $file_path"

    local file_name
    file_name=$(basename -- "$file_path")

    local work_dir
    work_dir=$(pwd -P)

    local rootfs_dir="$work_dir/$file_name-rootfs"
    local tar_path="$work_dir/$file_name-rootfs.tar"
    [[ ! -e "$rootfs_dir" ]] || die "output directory already exists: $rootfs_dir"
    [[ ! -e "$tar_path" ]] || die "output tar already exists: $tar_path"

    tmp_dir=$(mktemp -d "${TMPDIR:-/tmp}/unblob.XXXXXXXXXX")
    trap cleanup EXIT

    local input_dir="$tmp_dir/input"
    local output_dir="$tmp_dir/output"
    extract_firmware "$file_path" "$file_name" "$input_dir" "$output_dir"

    local extract_dir="$output_dir/${file_name}_extract"
    [[ -d "$extract_dir" ]] || die "unblob did not produce expected output: $extract_dir"

    mkdir -p -- "$rootfs_dir"
    shopt -s dotglob nullglob
    local extracted_items=("$extract_dir"/*)
    [[ ${#extracted_items[@]} -gt 0 ]] || die "unblob output is empty: $extract_dir"
    mv -- "${extracted_items[@]}" "$rootfs_dir/"

    if ! confirm_package "$tar_path"; then
        warn "skipped archive packaging"
        info "Extracted: $rootfs_dir"
        return 0
    fi

    tar -C "$work_dir" -cf "$tar_path" "$file_name-rootfs"

    info "Extracted: $rootfs_dir"
    info "Archive: $tar_path"
}

main "$@"
