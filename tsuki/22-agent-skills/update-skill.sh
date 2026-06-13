#!/usr/bin/env bash
set -Eeuo pipefail

white='\033[0m'
green='\033[0;32m'
blue='\033[0;34m'
red='\033[31m'
yellow='\033[33m'
grey='\e[37m'
pink='\033[38;5;218m'
cyan='\033[96m'

nc='\033[0m'

workdir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]:-$0}")" && pwd)"

src_dir="$workdir"
target_dirs=(
    "$HOME/.claude/skills"
    "$HOME/.codex/skills"
    "$HOME/.config/opencode/skills"
)

collect_skills() {
    find -L "$src_dir" -type f -iname 'SKILL.md' -exec dirname {} \; | sort -u
}

display_path() {
    local path="$1"

    if [[ "$path" == "$HOME" ]]; then
        printf '~'
    elif [[ "$path" == "$HOME/"* ]]; then
        printf '~/%s' "${path#"$HOME"/}"
    else
        printf '%s' "$path"
    fi
}

relative_link_target() {
    local from_dir="$1"
    local target="$2"

    if [[ "$from_dir" != "$HOME/"* || "$target" != "$HOME/"* ]]; then
        printf '%s' "$target"
        return 0
    fi

    local from_rel="${from_dir#"$HOME"/}"
    local target_rel="${target#"$HOME"/}"
    local -a from_parts=()
    local -a target_parts=()
    local -a rel_parts=()
    local old_ifs="$IFS"
    local i common rel_path

    IFS=/
    read -r -a from_parts <<<"$from_rel"
    read -r -a target_parts <<<"$target_rel"
    IFS="$old_ifs"

    common=0
    while [[ $common -lt ${#from_parts[@]} && $common -lt ${#target_parts[@]} && "${from_parts[$common]}" == "${target_parts[$common]}" ]]; do
        ((common += 1))
    done

    for ((i = common; i < ${#from_parts[@]}; i += 1)); do
        rel_parts+=("..")
    done
    for ((i = common; i < ${#target_parts[@]}; i += 1)); do
        rel_parts+=("${target_parts[$i]}")
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

do_link_into() {
    local target_dir="$1"
    mkdir -p -- "$target_dir"

    local entries=() wanted_names=() entry name link link_target
    while IFS= read -r entry; do
        entries+=("$entry")
        wanted_names+=("$(basename "$entry")")
    done < <(collect_skills)

    clean_stale_links "$target_dir" "${wanted_names[@]}"

    for entry in "${entries[@]}"; do
        link="$target_dir/$(basename "$entry")"
        link_target="$(relative_link_target "$target_dir" "$entry")"
        if [ -L "$link" ]; then
            rm -f -- "$link"
        elif [ -e "$link" ]; then
            echo -e "skip (not a symlink): ${yellow}$(display_path "$link")${nc}"
            continue
        fi
        ln -s "$link_target" "$link"
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
            echo -e "remove: ${red}$(display_path "$link")${nc}"
            rm -f -- "$link"
        fi
    done

    "$had_nullglob" || shopt -u nullglob
}

do_sync() {
    for t in "${target_dirs[@]}"; do
        echo -e "==> ${cyan}$(display_path "$t")${nc}"
        do_link_into "$t"
        ls -al "$t"
    done
}

do_show() {
    echo -e "src_dir: ${green}$(display_path "$src_dir")${nc}"
    echo -e "target_dirs:"
    for t in "${target_dirs[@]}"; do
        echo -e "  - ${green}$(display_path "$t")${nc}"
    done
    echo -e "skills:"
    while IFS= read -r entry; do
        echo -e "  - ${pink}$(display_path "$entry")${nc}"
    done < <(collect_skills)
}

echo -e "workdir: ${green}$(display_path "$workdir")${nc}"

while [[ $# -gt 0 ]]; do
    case $1 in
    sync | show)
        operation="$1"
        shift
        ;;
    *)
        echo "Unknown option: $1"
        echo "usage: $0 {sync|show}"
        exit 1
        ;;
    esac
done

operation="${operation:-sync}"

case "$operation" in
sync)
    do_sync
    ;;
show)
    do_show
    ;;
esac
