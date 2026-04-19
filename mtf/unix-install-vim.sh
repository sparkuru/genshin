#!/usr/bin/env bash

set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
NC='\033[0m'

ACTION=""
TARGET_SCOPE="all"
FORCE=0

log_info() {
    printf "%b\n" "${CYAN}$1${NC}"
}

log_warn() {
    printf "%b\n" "${YELLOW}$1${NC}"
}

log_ok() {
    printf "%b\n" "${GREEN}$1${NC}"
}

log_error() {
    printf "%b\n" "${RED}$1${NC}"
}

usage() {
    cat <<USAGE
usage: $0 <install|remove> [--user-only|--root-only] [--force]

options:
  --user-only   apply only to the primary login user
  --root-only   apply only to root user
  --force       overwrite existing files / relink conflicting paths
USAGE
}

parse_args() {
    if [[ $# -lt 1 ]]; then
        usage
        exit 1
    fi

    ACTION="$1"
    shift

    case "$ACTION" in
        install|remove) ;;
        *)
            usage
            exit 1
            ;;
    esac

    while [[ $# -gt 0 ]]; do
        case "$1" in
            --user-only)
                if [[ "$TARGET_SCOPE" == "root" ]]; then
                    log_error "--user-only and --root-only cannot be used together"
                    exit 1
                fi
                TARGET_SCOPE="user"
                ;;
            --root-only)
                if [[ "$TARGET_SCOPE" == "user" ]]; then
                    log_error "--user-only and --root-only cannot be used together"
                    exit 1
                fi
                TARGET_SCOPE="root"
                ;;
            --force)
                FORCE=1
                ;;
            -h|--help)
                usage
                exit 0
                ;;
            *)
                log_error "unknown option: $1"
                usage
                exit 1
                ;;
        esac
        shift
    done
}

resolve_home() {
    eval echo "~$1"
}

stat_owner() {
    local path="$1"

    if stat -c '%U' "$path" >/dev/null 2>&1; then
        stat -c '%U' "$path"
    else
        stat -f '%Su' "$path"
    fi
}

stat_group() {
    local path="$1"

    if stat -c '%G' "$path" >/dev/null 2>&1; then
        stat -c '%G' "$path"
    else
        stat -f '%Sg' "$path"
    fi
}

path_needs_sudo() {
    local path="$1"
    local probe="$path"

    if [[ "$(id -u)" -eq 0 ]]; then
        return 1
    fi

    while [[ ! -e "$probe" && "$probe" != "/" ]]; do
        probe="$(dirname "$probe")"
    done

    [[ ! -w "$probe" ]]
}

run_privileged() {
    if [[ "$(id -u)" -eq 0 ]]; then
        "$@"
    else
        sudo "$@"
    fi
}

remove_path() {
    local path="$1"

    if [[ ! -e "$path" && ! -L "$path" ]]; then
        return 0
    fi

    if path_needs_sudo "$path" || [[ "$(id -u)" -eq 0 ]]; then
        run_privileged rm -rf "$path"
    else
        rm -rf "$path"
    fi
}

ensure_dir() {
    local dir="$1"
    local owner="$2"
    local group="$3"

    if [[ -d "$dir" && ! -L "$dir" ]]; then
        return 0
    fi

    if [[ -e "$dir" || -L "$dir" ]]; then
        if [[ "$FORCE" -eq 1 ]]; then
            log_warn "replace existing path with directory: $dir"
            remove_path "$dir"
        else
            log_error "path exists and is not a plain directory: $dir (use --force to replace)"
            exit 1
        fi
    fi

    if path_needs_sudo "$dir" || [[ "$(id -u)" -eq 0 ]]; then
        run_privileged install -d -m 0755 -o "$owner" -g "$group" "$dir"
    else
        mkdir -p "$dir"
    fi
}

ensure_local_runtime_dir() {
    local dir="$1"
    local owner="$2"
    local group="$3"

    if [[ -L "$dir" ]]; then
        log_warn "portable mode requires a real directory, replace symlink: $dir -> $(readlink "$dir")"
        remove_path "$dir"
    fi

    ensure_dir "$dir" "$owner" "$group"
}

install_file() {
    local src="$1"
    local dest="$2"
    local owner="$3"
    local group="$4"

    if [[ "$FORCE" -eq 1 && ( -e "$dest" || -L "$dest" ) ]]; then
        remove_path "$dest"
    fi

    if path_needs_sudo "$dest" || [[ "$(id -u)" -eq 0 ]]; then
        run_privileged install -m 0644 -o "$owner" -g "$group" "$src" "$dest"
    else
        install -m 0644 "$src" "$dest"
    fi
}

create_symlink() {
    local link_path="$1"
    local target_path="$2"
    local owner="$3"
    local group="$4"

    if [[ -L "$link_path" ]]; then
        if [[ "$(readlink "$link_path")" == "$target_path" ]]; then
            log_info "skip existing symlink: $link_path"
            return 0
        fi

        if [[ "$FORCE" -eq 1 ]]; then
            log_warn "replace symlink: $link_path -> $target_path"
            remove_path "$link_path"
        else
            log_warn "existing symlink differs, keep it: $link_path"
            return 0
        fi
    elif [[ -e "$link_path" ]]; then
        if [[ "$FORCE" -eq 1 ]]; then
            log_warn "replace existing path with symlink: $link_path"
            remove_path "$link_path"
        else
            log_warn "existing path is not a symlink, keep it: $link_path"
            return 0
        fi
    fi

    ensure_dir "$(dirname "$link_path")" "$owner" "$group"

    if path_needs_sudo "$link_path" || [[ "$(id -u)" -eq 0 ]]; then
        run_privileged ln -s "$target_path" "$link_path"
        run_privileged chown -h "$owner:$group" "$link_path" 2>/dev/null || true
    else
        ln -s "$target_path" "$link_path"
    fi
}

download_file() {
    local target="$1"
    local url="$2"
    local owner="$3"
    local group="$4"

    if [[ "$FORCE" -eq 0 && -f "$target" ]]; then
        log_info "skip existing file: $target"
        return 0
    fi

    ensure_dir "$(dirname "$target")" "$owner" "$group"

    local tmp_file
    tmp_file="$(mktemp)"
    trap 'rm -f "$tmp_file"' RETURN

    if [[ "$FORCE" -eq 1 && ( -e "$target" || -L "$target" ) ]]; then
        log_info "overwrite $target <- $url"
    else
        log_info "download $target <- $url"
    fi

    curl -fsSL "$url" -o "$tmp_file"
    install_file "$tmp_file" "$target" "$owner" "$group"

    rm -f "$tmp_file"
    trap - RETURN
}

should_handle_primary() {
    [[ "$TARGET_SCOPE" == "all" || "$TARGET_SCOPE" == "user" ]]
}

should_handle_root() {
    [[ "$TARGET_SCOPE" == "all" || "$TARGET_SCOPE" == "root" ]]
}

detect_vim_root() {
    local root=""

    if [[ -n "$preferred_vim_bin" ]]; then
        root="$($preferred_vim_bin --version 2>/dev/null | sed -n 's/.*fall-back for \$VIM: "\(.*\)"/\1/p' | head -n 1)"
    fi

    if [[ -z "$root" ]]; then
        root="/usr/share/vim"
    fi

    printf '%s\n' "$root"
}

detect_vim_runtime_dir() {
    local vim_root="$1"

    if [[ ! -d "$vim_root" ]]; then
        return 0
    fi

    find "$vim_root" -maxdepth 1 -type d -name 'vim[0-9][0-9]' 2>/dev/null | sort | tail -n 1
}

resolve_context() {
    system_name="$(uname -s)"

    if [[ -n "${SUDO_USER:-}" && "${SUDO_USER}" != "root" ]]; then
        primary_user="$SUDO_USER"
    else
        primary_user="$(id -un)"
    fi

    primary_home="$(resolve_home "$primary_user")"
    primary_group="$(id -gn "$primary_user")"

    root_user="root"
    root_home="$(resolve_home root)"
    root_group="$(id -gn root)"

    default_vim_bin="$(command -v vim || true)"
    brew_vim_prefix=""
    brew_vim_bin=""

    if [[ "$system_name" == "Darwin" ]] && command -v brew >/dev/null 2>&1; then
        brew_vim_prefix="$(brew --prefix vim 2>/dev/null || true)"
        if [[ -n "$brew_vim_prefix" && -x "$brew_vim_prefix/bin/vim" ]]; then
            brew_vim_bin="$brew_vim_prefix/bin/vim"
        fi
    fi

    if [[ "$system_name" == "Darwin" ]]; then
        install_mode="portable_local"
        if [[ -n "$brew_vim_bin" ]]; then
            preferred_vim_bin="$brew_vim_bin"
            platform_desc="macOS + Homebrew Vim"
        else
            preferred_vim_bin="$default_vim_bin"
            platform_desc="macOS"
        fi
    else
        install_mode="traditional"
        preferred_vim_bin="$default_vim_bin"
        platform_desc="$system_name traditional unix-like"
    fi

    traditional_runtime_root=""
    traditional_runtime_dir=""
    runtime_owner="root"
    runtime_group="$root_group"

    if [[ "$install_mode" == "traditional" ]]; then
        traditional_runtime_root="$(detect_vim_root)"
        traditional_runtime_dir="$(detect_vim_runtime_dir "$traditional_runtime_root")"

        if [[ -z "$traditional_runtime_dir" ]]; then
            log_error "cannot detect traditional vim runtime directory under $traditional_runtime_root"
            exit 1
        fi

        runtime_owner="$(stat_owner "$traditional_runtime_dir")"
        runtime_group="$(stat_group "$traditional_runtime_dir")"
    fi
}

run_plug_install() {
    local target_user="$1"
    local target_home="$2"

    if [[ -z "$preferred_vim_bin" || ! -x "$preferred_vim_bin" ]]; then
        log_warn "vim not found, skip PlugInstall for $target_user"
        return 0
    fi

    log_info "run PlugInstall with $preferred_vim_bin for $target_user"

    if [[ "$(id -u)" -eq 0 ]]; then
        if [[ "$target_user" == "root" ]]; then
            HOME="$target_home" "$preferred_vim_bin" -u "$target_home/.vimrc" -c 'PlugInstall --sync' -c 'qa'
        else
            sudo -u "$target_user" env HOME="$target_home" "$preferred_vim_bin" -u "$target_home/.vimrc" -c 'PlugInstall --sync' -c 'qa'
        fi
    elif [[ "$target_user" == "root" ]]; then
        sudo -u root env HOME="$target_home" "$preferred_vim_bin" -u "$target_home/.vimrc" -c 'PlugInstall --sync' -c 'qa'
    else
        HOME="$target_home" "$preferred_vim_bin" -u "$target_home/.vimrc" -c 'PlugInstall --sync' -c 'qa'
    fi
}

install_portable_local_for_user() {
    local target_user="$1"
    local target_home="$2"
    local target_group="$3"
    local vim_root="$target_home/.vim"
    local vim_tmp_dir="$vim_root/tmp"
    local vim_autoload_dir="$vim_root/autoload"
    local vim_colors_dir="$vim_root/colors"
    local vimrc="$target_home/.vimrc"

    log_ok "install local vim config for $target_user ($target_home)"

    ensure_dir "$vim_root" "$target_user" "$target_group"
    ensure_dir "$vim_tmp_dir" "$target_user" "$target_group"
    ensure_local_runtime_dir "$vim_autoload_dir" "$target_user" "$target_group"
    ensure_local_runtime_dir "$vim_colors_dir" "$target_user" "$target_group"

    download_file \
        "$vimrc" \
        "https://raw.githubusercontent.com/sparkuru/vim/main/diy/unix-vimrc" \
        "$target_user" \
        "$target_group"
    download_file \
        "$vim_autoload_dir/plug.vim" \
        "https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim" \
        "$target_user" \
        "$target_group"
    download_file \
        "$vim_autoload_dir/gruvbox.vim" \
        "https://raw.githubusercontent.com/morhetz/gruvbox/master/autoload/gruvbox.vim" \
        "$target_user" \
        "$target_group"
    download_file \
        "$vim_colors_dir/gruvbox.vim" \
        "https://raw.githubusercontent.com/morhetz/gruvbox/master/colors/gruvbox.vim" \
        "$target_user" \
        "$target_group"

    run_plug_install "$target_user" "$target_home"
}

install_traditional_for_user() {
    local target_user="$1"
    local target_home="$2"
    local target_group="$3"
    local vim_root="$target_home/.vim"
    local vim_tmp_dir="$vim_root/tmp"
    local vim_autoload_dir="$vim_root/autoload"
    local vim_colors_dir="$vim_root/colors"
    local vimrc="$target_home/.vimrc"
    local autoload_owner="$target_user"
    local autoload_group="$target_group"
    local colors_owner="$target_user"
    local colors_group="$target_group"
    local autoload_install_dir="$vim_autoload_dir"
    local colors_install_dir="$vim_colors_dir"

    log_ok "install traditional vim config for $target_user ($target_home)"
    log_info "use vim runtime: $traditional_runtime_dir"

    ensure_dir "$vim_root" "$target_user" "$target_group"
    ensure_dir "$vim_tmp_dir" "$target_user" "$target_group"

    create_symlink "$vim_autoload_dir" "$traditional_runtime_dir/autoload" "$target_user" "$target_group"
    create_symlink "$vim_colors_dir" "$traditional_runtime_dir/colors" "$target_user" "$target_group"

    download_file \
        "$vimrc" \
        "https://raw.githubusercontent.com/sparkuru/vim/main/diy/unix-vimrc" \
        "$target_user" \
        "$target_group"

    if [[ -L "$vim_autoload_dir" ]]; then
        autoload_install_dir="$traditional_runtime_dir/autoload"
        autoload_owner="$runtime_owner"
        autoload_group="$runtime_group"
    else
        ensure_dir "$vim_autoload_dir" "$target_user" "$target_group"
    fi

    if [[ -L "$vim_colors_dir" ]]; then
        colors_install_dir="$traditional_runtime_dir/colors"
        colors_owner="$runtime_owner"
        colors_group="$runtime_group"
    else
        ensure_dir "$vim_colors_dir" "$target_user" "$target_group"
    fi

    download_file \
        "$autoload_install_dir/plug.vim" \
        "https://raw.githubusercontent.com/junegunn/vim-plug/master/plug.vim" \
        "$autoload_owner" \
        "$autoload_group"
    download_file \
        "$autoload_install_dir/gruvbox.vim" \
        "https://raw.githubusercontent.com/morhetz/gruvbox/master/autoload/gruvbox.vim" \
        "$autoload_owner" \
        "$autoload_group"
    download_file \
        "$colors_install_dir/gruvbox.vim" \
        "https://raw.githubusercontent.com/morhetz/gruvbox/master/colors/gruvbox.vim" \
        "$colors_owner" \
        "$colors_group"

    run_plug_install "$target_user" "$target_home"
}

install_for_user() {
    local target_user="$1"
    local target_home="$2"
    local target_group="$3"

    if [[ "$install_mode" == "portable_local" ]]; then
        install_portable_local_for_user "$target_user" "$target_home" "$target_group"
    else
        install_traditional_for_user "$target_user" "$target_home" "$target_group"
    fi
}

remove_for_user() {
    local target_user="$1"
    local target_home="$2"

    log_warn "remove vim config for $target_user ($target_home)"
    remove_path "$target_home/.vim"
    remove_path "$target_home/.vimrc"
}

install_vim() {
    resolve_context
    log_ok "detected mode: $platform_desc"
    log_info "target scope: $TARGET_SCOPE"

    if should_handle_primary; then
        install_for_user "$primary_user" "$primary_home" "$primary_group"
    fi

    if should_handle_root; then
        if [[ "$primary_user" == "root" && "$TARGET_SCOPE" == "all" ]]; then
            :
        else
            log_info "install root config so sudo vim can use the same setup"
            install_for_user "$root_user" "$root_home" "$root_group"
        fi
    fi
}

remove_vim() {
    resolve_context
    log_ok "detected mode: $platform_desc"
    log_info "target scope: $TARGET_SCOPE"

    if should_handle_primary; then
        remove_for_user "$primary_user" "$primary_home"
    fi

    if should_handle_root; then
        if [[ "$primary_user" == "root" && "$TARGET_SCOPE" == "all" ]]; then
            :
        else
            remove_for_user "$root_user" "$root_home"
        fi
    fi

    if [[ "$install_mode" == "traditional" ]]; then
        log_info "traditional shared runtime files are kept untouched: $traditional_runtime_dir"
    fi
}

parse_args "$@"

case "$ACTION" in
    install)
        install_vim
        ;;
    remove)
        remove_vim
        ;;
esac