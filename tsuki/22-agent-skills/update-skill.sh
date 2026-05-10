#!/bin/bash

#region
white='\033[0m'
green='\033[0;32m'
blue='\033[0;34m'
red='\033[31m'
yellow='\033[33m'
grey='\e[37m'
pink='\033[38;5;218m'
cyan='\033[96m'

# echo -e "${red}xxx${nc}"
nc='\033[0m'
#endregion

workdir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]:-$0}")" && pwd)"

src_dir="$workdir"
target_dirs=(
    "$HOME/.claude/skills"
    "$HOME/.codex/skills"
)

collect_skills() {
    find -L "$src_dir" -type f -iname 'SKILL.md' -printf '%h\n' | sort -u
}

do_link_into() {
    local target_dir="$1"
    mkdir -p "$target_dir"

    local -A wanted=()
    local entries=() entry name link
    while IFS= read -r entry; do
        entries+=("$entry")
        wanted["$(basename "$entry")"]=1
    done < <(collect_skills)

    for entry in "${entries[@]}"; do
        link="$target_dir/$(basename "$entry")"
        if [ -L "$link" ]; then
            rm -f "$link"
        elif [ -e "$link" ]; then
            echo -e "skip (not a symlink): ${yellow}${link}${nc}"
            continue
        fi
        ln -s "$entry" "$link"
    done

    while IFS= read -r -d '' link; do
        name="$(basename "$link")"
        if [ -z "${wanted[$name]:-}" ] || [ ! -e "$link" ]; then
            echo -e "remove: ${red}${link}${nc}"
            rm -f "$link"
        fi
    done < <(find "$target_dir" -mindepth 1 -maxdepth 1 -type l ! -path "$target_dir/.*" -print0)
}

do_sync() {
    for t in "${target_dirs[@]}"; do
        echo -e "==> ${cyan}${t}${nc}"
        do_link_into "$t"
        ls -al "$t"
    done
}

do_show() {
    echo -e "src_dir: ${green}${src_dir}${nc}"
    echo -e "target_dirs:"
    for t in "${target_dirs[@]}"; do
        echo -e "  - ${green}${t}${nc}"
    done
    echo -e "skills:"
    while IFS= read -r entry; do
        echo -e "  - ${pink}${entry}${nc}"
    done < <(collect_skills)
}

echo -e "workdir: ${green}${workdir}${nc}"

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
