#!/usr/bin/env bash
set -Eeuo pipefail

readonly STYLE_RESET=$'\033[0m'
readonly STYLE_SUCCESS=$'\033[0;32m'
readonly STYLE_ERROR=$'\033[31m'
readonly STYLE_WARNING=$'\033[33m'
readonly STYLE_CONTENT=$'\033[38;5;218m'
readonly STYLE_TITLE=$'\033[96m'

workdir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]:-$0}")" && pwd)"

platform_name() {
    case "$(uname -s)" in
    Darwin)
        printf 'darwin'
        ;;
    Linux)
        printf 'linux'
        ;;
    *)
        uname -s | tr '[:upper:]' '[:lower:]'
        ;;
    esac
}

src_dir="$workdir"
platform="$(platform_name)"
base_skill_dir="$src_dir/base/$platform"
base_repo_path="$(cd "$workdir/../../../../" && pwd)"
geass_path="$base_repo_path/21-geass"
base_skill_path="$geass_path/skills"
target_dirs=(
    "$HOME/.claude/skills"
    "$HOME/.codex/skills"
    "$HOME/.config/opencode/skills"
)

change_count=0

color_text() {
    local style="$1"
    local text="$2"

    if [[ -n "${NO_COLOR:-}" || ! -t 1 ]]; then
        printf '%s' "$text"
        return 0
    fi

    printf '%s%s%s' "$style" "$text" "$STYLE_RESET"
}

die() {
    printf '%s\n' "$(color_text "$STYLE_ERROR" "Error: $*")" >&2
    exit 1
}

note_change() {
    change_count=$((change_count + 1))
}

print_sync() {
    local path="$1"

    note_change
    printf 'sync: %s\n' "$(color_text "$STYLE_SUCCESS" "$(display_path "$path")")"
}

print_remove() {
    local path="$1"

    note_change
    printf 'remove: %s\n' "$(color_text "$STYLE_ERROR" "$(display_path "$path")")"
}

print_skip() {
    local path="$1"

    printf 'skip (not a symlink): %s\n' "$(color_text "$STYLE_WARNING" "$(display_path "$path")")"
}

list_dir() {
    local path="$1"

    ls -al "$path"
}

collect_skills() {
    {
        find "$src_dir" -path "$src_dir/base" -prune -o -type f -iname 'SKILL.md' -exec dirname {} \;
        if [ -d "$base_skill_dir" ]; then
            find -L "$base_skill_dir" -type f -iname 'SKILL.md' -exec dirname {} \;
        fi
    } | sort -u
}

display_path() {
    local path="$1"

    if [[ "$path" == "$HOME" ]]; then
        printf '~'
    elif [[ "$path" == "$HOME/"* ]]; then
        printf '%s/%s' '~' "${path#"$HOME"/}"
    else
        printf '%s' "$path"
    fi
}

relative_path() {
    local from_dir="${1%/}"
    local target="${2%/}"

    local -a from_parts=()
    local -a target_parts=()
    local -a rel_parts=()
    local old_ifs="$IFS"
    local i common rel_path

    IFS=/
    read -r -a from_parts <<<"$from_dir"
    read -r -a target_parts <<<"$target"
    IFS="$old_ifs"

    common=0
    while [[ $common -lt ${#from_parts[@]} && $common -lt ${#target_parts[@]} && "${from_parts[$common]}" == "${target_parts[$common]}" ]]; do
        ((common += 1))
    done

    for ((i = common; i < ${#from_parts[@]}; i += 1)); do
        [ -n "${from_parts[$i]}" ] && rel_parts+=("..")
    done
    for ((i = common; i < ${#target_parts[@]}; i += 1)); do
        [ -n "${target_parts[$i]}" ] && rel_parts+=("${target_parts[$i]}")
    done

    rel_path=""
    for i in "${!rel_parts[@]}"; do
        if [[ $i -eq 0 ]]; then
            rel_path="${rel_parts[$i]}"
        else
            rel_path="$rel_path/${rel_parts[$i]}"
        fi
    done

    printf '%s' "${rel_path:-.}"
}

contains_name() {
    local wanted_name="$1"
    shift

    local name
    for name in "$@"; do
        [[ "$name" == "$wanted_name" ]] && return 0
    done
    return 1
}

sync_link() {
    local link="$1"
    local link_target="$2"

    if [ -L "$link" ]; then
        if [ "$(readlink "$link")" = "$link_target" ]; then
            return 0
        fi
        rm -f -- "$link"
    elif [ -e "$link" ]; then
        print_skip "$link"
        return 0
    fi

    ln -s "$link_target" "$link"
    print_sync "$link"
}

sync_base_links() {
    [ -d "$base_skill_path" ] || die "base skill directory not found: $base_skill_path"

    mkdir -p -- "$base_skill_dir"

    local skill_names=()
    local dir link link_target
    for dir in "$base_skill_path"/*/; do
        [ -d "$dir" ] || continue
        skill_names+=("$(basename "$dir")")
    done

    clean_stale_links "$base_skill_dir" "${skill_names[@]}"

    for dir in "$base_skill_path"/*/; do
        [ -d "$dir" ] || continue
        link="$base_skill_dir/$(basename "$dir")"
        link_target="$(relative_path "$base_skill_dir" "${dir%/}")"
        sync_link "$link" "$link_target"
    done
}

do_link_into() {
    local target_dir="$1"
    mkdir -p -- "$target_dir"

    local entries=() wanted_names=() entry link link_target
    while IFS= read -r entry; do
        entries+=("$entry")
        wanted_names+=("$(basename "$entry")")
    done < <(collect_skills)

    clean_stale_links "$target_dir" "${wanted_names[@]}"

    for entry in "${entries[@]}"; do
        link="$target_dir/$(basename "$entry")"
        link_target="$(relative_path "$target_dir" "$entry")"
        sync_link "$link" "$link_target"
    done
}

clean_stale_links() {
    local target_dir="$1"
    shift

    local link name
    local had_nullglob=false
    shopt -q nullglob && had_nullglob=true
    shopt -s nullglob

    for link in "$target_dir"/*; do
        [ -L "$link" ] || continue

        name="$(basename "$link")"
        if ! contains_name "$name" "$@" || [ ! -e "$link" ]; then
            print_remove "$link"
            rm -f -- "$link"
        fi
    done

    "$had_nullglob" || shopt -u nullglob
}

do_sync() {
    printf '==> %s\n' "$(color_text "$STYLE_TITLE" "$(display_path "$base_skill_dir")")"
    sync_base_links
    list_dir "$base_skill_dir"

    for t in "${target_dirs[@]}"; do
        printf '==> %s\n' "$(color_text "$STYLE_TITLE" "$(display_path "$t")")"
        do_link_into "$t"
        list_dir "$t"
    done

    if [ "$change_count" -eq 0 ]; then
        printf '%s\n' "$(color_text "$STYLE_SUCCESS" "No skill changes.")"
    fi
}

do_show() {
    sync_base_links

    printf 'src_dir: %s\n' "$(color_text "$STYLE_SUCCESS" "$(display_path "$src_dir")")"
    printf 'base_skill_path: %s\n' "$(color_text "$STYLE_SUCCESS" "$(display_path "$base_skill_path")")"
    printf 'target_dirs:\n'
    for t in "${target_dirs[@]}"; do
        printf '  - %s\n' "$(color_text "$STYLE_SUCCESS" "$(display_path "$t")")"
    done
    printf 'skills:\n'
    while IFS= read -r entry; do
        printf '  - %s\n' "$(color_text "$STYLE_CONTENT" "$(display_path "$entry")")"
    done < <(collect_skills)
}

while [[ $# -gt 0 ]]; do
    case $1 in
    sync | show)
        operation="$1"
        shift
        ;;
    *)
        printf 'Unknown option: %s\n' "$1" >&2
        printf 'usage: %s {sync|show}\n' "$0" >&2
        exit 1
        ;;
    esac
done

operation="${operation:-sync}"

printf 'workdir: %s\n' "$(color_text "$STYLE_SUCCESS" "$(display_path "$workdir")")"
printf 'platform: %s\n' "$(color_text "$STYLE_SUCCESS" "$platform")"

case "$operation" in
sync)
    do_sync
    ;;
show)
    do_show
    ;;
esac
