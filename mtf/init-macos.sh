#!/usr/bin/env bash

set -Eeuo pipefail

SCRIPT_NAME="$(basename "$0")"
readonly SCRIPT_NAME
readonly GITHUB_URL_BASE="https://raw.githubusercontent.com/sparkuru/genshin/main"
FORCE=0
PROXY_URL="${VIM_INSTALL_PROXY:-${all_proxy:-${ALL_PROXY:-${https_proxy:-${HTTPS_PROXY:-}}}}}"
TEMP_DIR=""

usage() {
	cat <<USAGE
Usage: $SCRIPT_NAME [options]

Options:
  -h, --help   show this help message
  --force      overwrite existing files and configuration
  --proxy URL  use this proxy for downloads and PlugInstall
USAGE
}

die() {
	printf 'Error: %s\n' "$*" >&2
	exit 1
}

log_info() {
	printf '%s\n' "$*"
}

log_warn() {
	printf 'Warning: %s\n' "$*" >&2
}

parse_args() {
	while [[ $# -gt 0 ]]; do
		case "$1" in
		-h | --help)
			usage
			exit 0
			;;
		--force)
			FORCE=1
			;;
		--proxy)
			[[ $# -ge 2 ]] || die "--proxy requires a URL"
			PROXY_URL="$2"
			shift
			;;
		--)
			shift
			[[ $# -eq 0 ]] || die "unexpected argument: $1"
			return 0
			;;
		-*)
			die "unknown option: $1"
			;;
		*)
			die "unexpected argument: $1"
			;;
		esac
		shift
	done
}

configure_proxy() {
	local proxy_pattern='^[a-zA-Z][a-zA-Z0-9+.-]*://[^[:space:]"]+$'

	if [[ -z "$PROXY_URL" ]]; then
		return 0
	fi

	[[ "$PROXY_URL" =~ $proxy_pattern ]] ||
		die "invalid proxy URL: $PROXY_URL"

	export ALL_PROXY="$PROXY_URL"
	export HTTP_PROXY="$PROXY_URL"
	export HTTPS_PROXY="$PROXY_URL"
	export all_proxy="$PROXY_URL"
	export http_proxy="$PROXY_URL"
	export https_proxy="$PROXY_URL"
}

cleanup() {
	if [[ -n "$TEMP_DIR" && -d "$TEMP_DIR" ]]; then
		rm -rf -- "$TEMP_DIR"
	fi
}

require_command() {
	command -v "$1" >/dev/null 2>&1 || die "required command not found: $1"
}

_curl() {
	local target="$1"
	local url="$2"
	local tmp_file

	if [[ -e "$target" || -L "$target" ]]; then
		if [[ "$FORCE" -eq 0 ]]; then
			log_info "skip existing file: $target"
			return 0
		fi
		[[ -d "$target" && ! -L "$target" ]] && die "refuse to overwrite directory: $target"
		log_warn "overwrite existing file: $target"
	else
		log_info "download $target <- $url"
	fi

	mkdir -p "$(dirname "$target")"
	tmp_file="$(mktemp "$TEMP_DIR/download.XXXXXXXXXX")"
	if ! curl --fail --location --silent --show-error --output "$tmp_file" "$url"; then
		die "download failed: $url"
	fi

	if [[ -e "$target" || -L "$target" ]]; then
		[[ "$FORCE" -eq 1 ]] || die "target appeared during download: $target"
		[[ -d "$target" && ! -L "$target" ]] && die "refuse to overwrite directory: $target"
		rm -f -- "$target"
	fi

	install -m 0644 "$tmp_file" "$target"
}

ensure_symlink() {
	local target="$1"
	local link_path="$2"

	if [[ -L "$link_path" && "$(readlink "$link_path")" == "$target" ]]; then
		log_info "skip existing symlink: $link_path"
		return 0
	fi

	if [[ -e "$link_path" || -L "$link_path" ]]; then
		[[ "$FORCE" -eq 1 ]] || die "existing path will not be replaced: $link_path (use --force)"
		[[ -d "$link_path" && ! -L "$link_path" ]] && die "refuse to replace directory: $link_path"
		log_warn "replace existing path with symlink: $link_path"
		sudo rm -f -- "$link_path"
	fi

	sudo mkdir -p "$(dirname "$link_path")"
	sudo ln -s "$target" "$link_path"
}

git_config_set() {
	local key="$1"
	local value="$2"

	if git config --global --get-all "$key" >/dev/null 2>&1; then
		if [[ "$FORCE" -eq 0 ]]; then
			log_info "keep existing Git config: $key"
			return 0
		fi
		log_warn "overwrite Git config: $key"
		git config --global --replace-all "$key" "$value"
		return 0
	fi

	git config --global "$key" "$value"
}

write_pip_config() {
	local home_dir="$1"
	local config_path="$home_dir/.config/pip/pip.conf"
	local tmp_file

	if [[ -e "$config_path" || -L "$config_path" ]]; then
		[[ -d "$config_path" && ! -L "$config_path" ]] && die "pip config path is a directory: $config_path"
		if [[ "$FORCE" -eq 0 ]]; then
			log_info "keep existing pip config: $config_path"
			return 0
		fi
		log_warn "overwrite pip config: $config_path"
	fi

	mkdir -p "$(dirname "$config_path")"
	tmp_file="$(mktemp "$TEMP_DIR/pip.conf.XXXXXXXXXX")"
	cat >"$tmp_file" <<'PIP_CONFIG'
[global]
index-url = https://mirrors.ustc.edu.cn/pypi/simple
break-system-packages = true
user = true
[install]
trusted-host = mirrors.ustc.edu.cn
PIP_CONFIG
	chmod 0644 "$tmp_file"

	if [[ -e "$config_path" || -L "$config_path" ]]; then
		[[ "$FORCE" -eq 1 ]] || die "pip config appeared during update: $config_path"
		[[ -d "$config_path" && ! -L "$config_path" ]] && die "pip config path is a directory: $config_path"
		rm -f -- "$config_path"
	fi
	install -m 0644 "$tmp_file" "$config_path"
}

run_vim_install() {
	local installer_path="$TEMP_DIR/unix-install-vim.sh"
	local vim_args=(install)

	_curl "$installer_path" "$GITHUB_URL_BASE/mtf/unix-install-vim.sh"
	if [[ "$FORCE" -eq 1 ]]; then
		vim_args+=(--force)
	fi
	[[ -n "$PROXY_URL" ]] && vim_args+=(--proxy "$PROXY_URL")
	bash "$installer_path" "${vim_args[@]}"
}

main() {
	parse_args "$@"
	[[ -n "${HOME:-}" ]] || die "HOME is not set"
	configure_proxy

	require_command brew
	require_command curl
	require_command git
	require_command mktemp
	require_command install
	require_command sudo

	TEMP_DIR="$(mktemp -d "${TMPDIR:-/tmp}/genshin-init-macos.XXXXXXXXXX")"
	trap cleanup EXIT

	local to_install_list=(
		curl net-tools openvpn rsync proxychains-ng jq tcp-traceroute iproute2mac
		gnupg2 binutils file fd btop tmux strace coreutils
		scons squashfs subversion swig texinfo upx unzip 7z-zip git
		python qemu fzf ripgrep vim
		docker docker-compose colima
		ghidra rizin radare2 patchelf
		nmap hydra john telnet scroll-reverser android-platform-tools
		tree glow pidof node openjdk wireguard-tools
	)

	brew install "${to_install_list[@]}"
	require_command pip

	ensure_symlink \
		/opt/homebrew/opt/openjdk/libexec/openjdk.jdk \
		/Library/Java/JavaVirtualMachines/openjdk.jdk

	git_config_set init.defaultbranch main
	git_config_set core.editor vim
	git_config_set core.autocrlf false
	git_config_set core.quotepath false
	git_config_set pull.rebase true

	_curl "$HOME/.gitignore_global" "$GITHUB_URL_BASE/mtf/.gitignore_global"
	git_config_set core.excludesfile "$HOME/.gitignore_global"

	write_pip_config "$HOME"
	pip install \
		setuptools setuptools_rust datetime argparse ipython getpass4 \
		colorama cryptography ifaddr virtualenv ropgadget pwntools shodan \
		ollama readchar rich watchdog psutil faker python-docx toml

	run_vim_install
}

main "$@"
