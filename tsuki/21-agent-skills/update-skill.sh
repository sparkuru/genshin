#!/usr/bin/env bash
set -Eeuo pipefail

readonly STYLE_RESET=$'\033[0m'
readonly STYLE_SUCCESS=$'\033[0;32m'
readonly STYLE_ERROR=$'\033[31m'
readonly STYLE_WARNING=$'\033[33m'
readonly STYLE_CONTENT=$'\033[38;5;218m'
readonly STYLE_TITLE=$'\033[96m'

if [[ -n "${NO_COLOR:-}" || ! -t 1 ]]; then
    readonly COLOR_ENABLED=false
else
    readonly COLOR_ENABLED=true
fi

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
agy_skill_dir="$HOME/.gemini/antigravity-cli/skills"
target_dirs=(
    "$HOME/.claude/skills"
    "$HOME/.codex/skills"
    "$HOME/.config/opencode/skills"
    "$agy_skill_dir"
)

change_count=0
selected_target=""
adopt_legacy=false
verbose=false

color_text() {
    local style="$1"
    local text="$2"

    if [[ "$COLOR_ENABLED" != true ]]; then
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
    printf '%s: %s\n' "$(color_text "$STYLE_SUCCESS" 'sync')" "$(color_text "$STYLE_SUCCESS" "$(display_path "$path")")"
}

print_remove() {
    local path="$1"

    note_change
    printf '%s: %s\n' "$(color_text "$STYLE_ERROR" 'remove')" "$(color_text "$STYLE_ERROR" "$(display_path "$path")")"
}

print_skip() {
    local path="$1"

    printf 'skip (not a symlink): %s\n' "$(color_text "$STYLE_WARNING" "$(display_path "$path")")"
}

list_dir() {
    local path="$1"

    if [[ "$verbose" == true ]]; then
        ls -al "$path"
    fi
}

scan_skill_roots() {
    local root="$1"
    local excluded="$2"
    find -L "$root" -path "$excluded" -prune -o \
        \( -type d -exec sh -c '
            for file in "$1"/[sS][kK][iI][lL][lL].[mM][dD]; do
                [ -f "$file" ] && exit 0
            done
            exit 1
        ' sh '{}' \; -print -prune \)
}

skill_document() {
    local folder="$1" file found=""
    for file in "$folder"/[sS][kK][iI][lL][lL].[mM][dD]; do
        [[ -f "$file" ]] || continue
        [[ -z "$found" ]] || die "multiple skill entrypoints in: $folder"
        found="$file"
    done
    [[ -n "$found" ]] || return 1
    printf '%s' "$found"
}

collect_skills() {
    {
        if [[ -d "$base_skill_dir" ]]; then
            scan_skill_roots "$base_skill_dir" "" | LC_ALL=C sort || exit 1
        fi
        scan_skill_roots "$src_dir" "$src_dir/base" | LC_ALL=C sort || exit 1
    }
}

select_skill_roots() {
    local discovered entry name document index existing_document found
    local -a names=() paths=()
    discovered="$(collect_skills)" || die "failed to discover skills"
    [[ -n "$discovered" ]] || return 0

    while IFS= read -r entry; do
        name="$(basename "$entry")"
        [[ "$name" != *$'\t'* && "$entry" != *$'\t'* ]] || die "tabs are not supported in skill paths"
        document="$(skill_document "$entry")" || die "skill entrypoint is absent: $entry"
        found=false
        for index in "${!names[@]}"; do
            [[ "${names[$index]}" == "$name" ]] || continue
            existing_document="$(skill_document "${paths[$index]}")" || die "skill entrypoint is absent: ${paths[$index]}"
            if [[ ! "$document" -ef "$existing_document" ]]; then
                [[ "${paths[$index]}" == "$base_skill_dir/"* && "$entry" == "$src_dir/"* && "$entry" != "$base_skill_dir/"* ]] || \
                    die "conflicting skill roots named $name: ${paths[$index]} and $entry"
            fi
            paths[index]="$entry"
            found=true
            break
        done
        if [[ "$found" != true ]]; then
            names+=("$name")
            paths+=("$entry")
        fi
    done <<< "$discovered"
    printf '%s\n' "${paths[@]}"
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

is_legacy_link() {
    local target_dir="$1" link_target="$2" prefix remainder
    prefix="$(relative_path "$target_dir" "$src_dir")"
    [[ "$link_target" == "$prefix/"* ]] || return 1
    remainder="${link_target#"$prefix"/}"
    [[ -n "$remainder" && "/$remainder/" != *"/../"* && "/$remainder/" != *"/./"* ]]
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
    [[ ! -L "$target_dir" ]] || die "skills directory must not be a symlink: $target_dir"
    [[ ! -e "$target_dir" || -d "$target_dir" ]] || die "skills target is not a directory: $target_dir"
    mkdir -p -- "$target_dir"

    local manifest="$target_dir/.agent-skills-managed.tsv"
    [[ ! -L "$manifest" ]] || die "skill manifest must not be a symlink: $manifest"
    [[ ! -e "$manifest" || -f "$manifest" ]] || die "invalid skill manifest: $manifest"

    local -a old_names=() old_targets=() wanted_names=() wanted_targets=() wanted_sources=() new_names=() new_targets=()
    local name previous extra entry target index link is_owned entries_text
    if [[ -f "$manifest" ]]; then
        while IFS=$'\t' read -r name previous extra || [[ -n "$name$previous$extra" ]]; do
            [[ -n "$name" && "$name" != */* && "$name" != . && "$name" != .. && -n "$previous" && -z "$extra" ]] || die "invalid skill manifest: $manifest"
            contains_name "$name" "${old_names[@]}" && die "duplicate entry in skill manifest: $name"
            old_names+=("$name")
            old_targets+=("$previous")
        done < "$manifest"
    fi

    if [[ "$adopt_legacy" == true ]]; then
        for link in "$target_dir"/*; do
            [[ -L "$link" ]] || continue
            name="$(basename "$link")"
            contains_name "$name" "${old_names[@]}" && continue
            previous="$(readlink "$link")"
            if is_legacy_link "$target_dir" "$previous"; then
                old_names+=("$name")
                old_targets+=("$previous")
            fi
        done
    fi

    entries_text="$(select_skill_roots)" || die "failed to select skills"
    if [[ -n "$entries_text" ]]; then
        while IFS= read -r entry; do
            name="$(basename "$entry")"
            wanted_names+=("$name")
            wanted_targets+=("$(relative_path "$target_dir" "$entry")")
            wanted_sources+=("$entry")
        done <<< "$entries_text"
    fi

    for index in "${!old_names[@]}"; do
        link="$target_dir/${old_names[$index]}"
        [[ -L "$link" && "$(readlink "$link")" == "${old_targets[$index]}" ]] || continue
        if ! contains_name "${old_names[$index]}" "${wanted_names[@]}"; then
            rm -f -- "$link"
            print_remove "$link"
        fi
    done

    for index in "${!wanted_names[@]}"; do
        name="${wanted_names[$index]}"
        target="${wanted_targets[$index]}"
        link="$target_dir/$name"
        is_owned=false
        if [[ -L "$link" ]]; then
            previous="$(readlink "$link")"
            if [[ "$previous" == "$target" ]]; then
                is_owned=true
            else
                local old_index current_document source_document
                for old_index in "${!old_names[@]}"; do
                    if [[ "${old_names[$old_index]}" == "$name" && "${old_targets[$old_index]}" == "$previous" ]]; then
                        is_owned=true
                        break
                    fi
                done
                if [[ "$is_owned" != true ]] && current_document="$(skill_document "$link")" && source_document="$(skill_document "${wanted_sources[$index]}")"; then
                    [[ "$current_document" -ef "$source_document" ]] && is_owned=true
                fi
                if [[ "$is_owned" == true ]]; then
                    rm -f -- "$link"
                    if ! ln -s "$target" "$link"; then
                        ln -s "$previous" "$link" || die "failed to restore previous skill link: $link"
                        die "failed to update skill link: $link"
                    fi
                    print_sync "$link"
                fi
            fi
        fi
        if [[ "$is_owned" != true && ( -e "$link" || -L "$link" ) ]]; then
            printf 'skip (existing skill): %s\n' "$(display_path "$link")" >&2
            continue
        fi
        if [[ "$is_owned" != true ]]; then
            ln -s "$target" "$link"
            print_sync "$link"
        fi
        new_names+=("$name")
        new_targets+=("$target")
    done

    local temp_manifest
    temp_manifest="$(mktemp "$target_dir/.agent-skills-managed.XXXXXXXXXX")"
    for index in "${!new_names[@]}"; do
        printf '%s\t%s\n' "${new_names[$index]}" "${new_targets[$index]}" >> "$temp_manifest"
    done
    if [[ -f "$manifest" ]] && cmp -s -- "$temp_manifest" "$manifest"; then
        rm -f -- "$temp_manifest"
    else
        mv -f -- "$temp_manifest" "$manifest"
    fi
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
    if [[ -z "$selected_target" ]]; then
        if [[ "$verbose" == true ]]; then
            printf '%s %s\n' "$(color_text "$STYLE_WARNING" '==>')" "$(color_text "$STYLE_TITLE" "$(display_path "$base_skill_dir")")"
        fi
        sync_base_links
        list_dir "$base_skill_dir"
    fi

    for t in "${target_dirs[@]}"; do
        if [[ "$verbose" == true ]]; then
            printf '%s %s\n' "$(color_text "$STYLE_WARNING" '==>')" "$(color_text "$STYLE_TITLE" "$(display_path "$t")")"
        fi
        do_link_into "$t"
        list_dir "$t"
    done

    if [ "$change_count" -eq 0 ]; then
        printf '%s\n' "$(color_text "$STYLE_SUCCESS" "No skill changes.")"
    fi
}

do_show() {
    printf 'src_dir: %s\n' "$(color_text "$STYLE_SUCCESS" "$(display_path "$src_dir")")"
    printf 'base_skill_path: %s\n' "$(color_text "$STYLE_SUCCESS" "$(display_path "$base_skill_path")")"
    printf 'target_dirs:\n'
    for t in "${target_dirs[@]}"; do
        printf '  - %s\n' "$(color_text "$STYLE_SUCCESS" "$(display_path "$t")")"
    done
    printf 'skills:\n'
    local entries_text entry
    entries_text="$(select_skill_roots)" || die "failed to select skills"
    if [[ -n "$entries_text" ]]; then
        while IFS= read -r entry; do
            printf '  - %s\n' "$(color_text "$STYLE_CONTENT" "$(display_path "$entry")")"
        done <<< "$entries_text"
    fi
}

usage() {
    printf '%s\n' "$(color_text "$STYLE_TITLE" "Usage: ${0##*/} [sync|show] [--target claude|codex|opencode|agy] [--adopt-legacy] [-v]")"
    printf '%s\n' 'A targeted run uses the current base skills without refreshing them.'
    printf '%s\n' 'Skill roots are discovered once and their contents are not scanned recursively.'
    printf '%s\n' '--adopt-legacy also manages old links whose targets are inside this repository.'
    printf '%s\n' '-v shows sync details and the contents of each synced directory.'
}

while [[ $# -gt 0 ]]; do
    case $1 in
    sync | show)
        operation="$1"
        shift
        ;;
    --target)
        [[ $# -ge 2 && -n "$2" ]] || die "--target requires a name"
        selected_target="$2"
        shift 2
        ;;
    --adopt-legacy)
        adopt_legacy=true
        shift
        ;;
    -v)
        verbose=true
        shift
        ;;
    --help | -h)
        usage
        exit 0
        ;;
    *)
        printf 'Unknown option: %s\n' "$1" >&2
        usage >&2
        exit 1
        ;;
    esac
done

operation="${operation:-sync}"

case "$selected_target" in
"") ;;
claude) target_dirs=("$HOME/.claude/skills") ;;
codex) target_dirs=("$HOME/.codex/skills") ;;
opencode) target_dirs=("$HOME/.config/opencode/skills") ;;
agy) target_dirs=("$agy_skill_dir") ;;
*) die "unknown target: $selected_target" ;;
esac

printf '%s %s\n' "$(color_text "$STYLE_TITLE" 'workdir:')" "$(color_text "$STYLE_SUCCESS" "$(display_path "$workdir")")"
printf '%s %s\n\n' "$(color_text "$STYLE_TITLE" 'platform:')" "$(color_text "$STYLE_SUCCESS" "$platform")"

case "$operation" in
sync)
    do_sync
    ;;
show)
    do_show
    ;;
esac
