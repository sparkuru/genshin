#!/usr/bin/env bash
set -Eeuo pipefail

readonly SCRIPT_NAME=${0##*/}
readonly RELEASES_API='https://api.github.com/repos/browseros-ai/BrowserOS/releases'
readonly RELEASE_DOWNLOAD_PREFIX='https://github.com/browseros-ai/BrowserOS/releases/download/'
readonly RELEASES_PAGE='https://github.com/browseros-ai/BrowserOS/releases'
readonly CDN_RELEASE_PREFIX='https://cdn.browseros.com/releases/browserclaw/'
readonly INSTALL_MARKER='browseros-neo-install-v1'
readonly DEFAULT_STATE_NAME='.browseros-neo'
readonly IMAGE_NAME='BrowserOS_neo.AppImage'
readonly LAUNCHER_NAME='browseros-neo'
readonly MARKER_NAME='.browseros-neo-install'
readonly VERSION_NAME='.browseros-neo-version'
readonly STATE_NAME='.browseros-neo-state-root'
readonly MCP_PROXY_NAME='browseros_mcp_proxy.py'
readonly MCP_SETUP_NAME='browseros_mcp_setup.py'
readonly MCP_MARKER_NAME='.browseros-neo-codex-mcp.json'
readonly STYLE_RESET=$'\033[0m'
readonly STYLE_TITLE=$'\033[1;36m'
readonly STYLE_OPTION=$'\033[1;32m'
readonly STYLE_EXAMPLE=$'\033[0;37m'
readonly STYLE_SUCCESS=$'\033[1;32m'
readonly STYLE_WARNING=$'\033[1;33m'
readonly STYLE_ERROR=$'\033[1;31m'

operation=''
install_dir=''
state_root=''
current_state_root=''
state_mode='keep'
state_explicit=false
force=false
enable_mcp_proxy=false
source_dir=''
python_bin=''
codex_config_path=''
architecture=''
elf_machine=''
bin_link=''
desktop_file=''
work_dir=''
transaction_dir=''
transaction_active=false
transaction_committed=false
created_bin_link=false
created_desktop=false
created_install_dir=false
desktop_temp=''
state_temp=''
release_version=''
asset_name=''
asset_url=''
asset_digest=''
asset_size=''
release_tag=''

usage() {
	local title='' option='' example='' reset=''
	if [[ -z "${NO_COLOR:-}" && -t 1 ]]; then
		title=$STYLE_TITLE
		option=$STYLE_OPTION
		example=$STYLE_EXAMPLE
		reset=$STYLE_RESET
	fi
	cat <<EOF
${title}Usage:${reset}
  ${example}$SCRIPT_NAME --install-path DIR [--force] [--state-root DIR] [--with-codex-autostart]${reset}
  ${example}$SCRIPT_NAME install --install-path DIR [--force] [--state-root DIR] [--with-codex-autostart]${reset}
  ${example}$SCRIPT_NAME update --install-path DIR [--state-root DIR] [--with-codex-autostart]${reset}
  ${example}$SCRIPT_NAME configure --install-path DIR [--state-root DIR]${reset}
  ${example}$SCRIPT_NAME proxy --install-path DIR${reset}
  ${example}$SCRIPT_NAME remove --install-path DIR${reset}

Install the latest stable BrowserOS neo AppImage for this machine, together
with a launcher, command link, and desktop entry. Browser profile and cache
are stored under the state root. The command link defaults to ~/.local/bin/browseros-neo;
the desktop entry uses ${XDG_DATA_HOME:-~/.local/share}/applications.

  ${option}--install-path DIR${reset}     Installation directory (required).
  ${option}--force${reset}                Reinstall an existing managed installation.
  ${option}--state-root DIR${reset}       Use DIR for profile, cache, browserclaw and browseros.
  ${option}--with-codex-autostart${reset} Install and enable the Codex MCP autostart proxy.
  ${option}--help${reset}                 Show this help.

The default state root is ~/.browseros-neo. Existing browser data is not
imported automatically. Changing state paths does not move existing data.
Configure changes only the saved state root and does not access the network.
The proxy command enables or updates the proxy without stopping the browser.
The proxy requires Python 3.11+ with the mcp, anyio and httpx packages.
Remove restores the managed Codex MCP entry and preserves profile, cache and state.
BROWSEROS_NEO_BIN_DIR may override the command-link directory.
EOF
}

die() {
	if [[ -n "${NO_COLOR:-}" || ! -t 2 ]]; then
		printf 'Error: %s\n' "$*" >&2
	else
		printf '%sError: %s%s\n' "$STYLE_ERROR" "$*" "$STYLE_RESET" >&2
	fi
	exit 1
}

warn() {
	if [[ -n "${NO_COLOR:-}" || ! -t 2 ]]; then
		printf 'Warning: %s\n' "$*" >&2
	else
		printf '%sWarning: %s%s\n' "$STYLE_WARNING" "$*" "$STYLE_RESET" >&2
	fi
}

success() {
	if [[ -n "${NO_COLOR:-}" || ! -t 1 ]]; then
		printf '%s\n' "$*"
	else
		printf '%s%s%s\n' "$STYLE_SUCCESS" "$*" "$STYLE_RESET"
	fi
}

require_command() {
	command -v "$1" >/dev/null 2>&1 || die "required command not found: $1"
}

validate_single_line() {
	local value=$1
	local description=$2
	[[ "$value" != *$'\n'* && "$value" != *$'\r'* && "$value" != *$'\t'* ]] ||
		die "$description must not contain a newline, carriage return, or tab"
}

parse_arguments() {
	[[ $# -gt 0 ]] || {
		usage >&2
		exit 1
	}
	case "$1" in
	install | update | configure | proxy | remove)
		operation=$1
		shift
		;;
	--help | -h)
		usage
		exit 0
		;;
	--*) operation=install ;;
	*) die "unknown command: $1" ;;
	esac

	while [[ $# -gt 0 ]]; do
		case "$1" in
		--install-path)
			[[ $# -ge 2 && -n "$2" ]] || die '--install-path requires a directory'
			[[ -z "$install_dir" ]] || die '--install-path may only be specified once'
			install_dir=$2
			shift 2
			;;
		--state-root)
			[[ $# -ge 2 && -n "$2" ]] || die '--state-root requires a directory'
			[[ "$state_mode" == keep ]] || die 'state directory options are mutually exclusive'
			state_root=$2
			state_mode=custom
			state_explicit=true
			shift 2
			;;
		--force)
			[[ "$force" == false ]] || die '--force may only be specified once'
			force=true
			shift
			;;
		--with-codex-autostart)
			[[ "$enable_mcp_proxy" == false ]] || die '--with-codex-autostart may only be specified once'
			enable_mcp_proxy=true
			shift
			;;
		--help | -h)
			usage
			exit 0
			;;
		*) die "unknown argument: $1" ;;
		esac
	done
	[[ -n "$install_dir" ]] || die 'pass --install-path DIR'
	[[ "$operation" == install || "$force" == false ]] || die '--force is only valid with install'
	[[ "$operation" != remove || "$state_mode" == keep ]] || die 'state options cannot be used with remove'
	[[ "$operation" != proxy || "$state_mode" == keep ]] || die 'state options cannot be used with proxy'
	if [[ "$operation" == proxy ]]; then
		enable_mcp_proxy=true
	elif [[ "$enable_mcp_proxy" == true && "$operation" != install && "$operation" != update ]]; then
		die '--with-codex-autostart is valid only with install or update'
	fi
}

resolve_paths() {
	local home_path data_home bin_dir state_file_exists=false
	[[ -n "${HOME:-}" && "$HOME" == /* ]] || die 'HOME must be an absolute path'
	validate_single_line "$install_dir" 'installation path'
	[[ ! -L "$install_dir" ]] || die 'installation path must not be a symbolic link'
	install_dir=$(realpath -m -- "$install_dir")
	home_path=$(realpath -m -- "$HOME")
	[[ "$install_dir" != / && "$install_dir" != "$home_path" ]] || die 'refusing to use the filesystem root or HOME as the installation directory'
	validate_single_line "$install_dir" 'installation path'
	[[ "$install_dir" != *'='* && "$install_dir" != *'%'* ]] ||
		die 'installation path cannot contain = or % in a desktop executable path'

	current_state_root="$HOME/$DEFAULT_STATE_NAME"
	if [[ -e "$install_dir/$STATE_NAME" || -L "$install_dir/$STATE_NAME" ]]; then
		[[ -f "$install_dir/$STATE_NAME" && ! -L "$install_dir/$STATE_NAME" ]] || die 'state-root configuration must be a regular file'
		IFS= read -r current_state_root <"$install_dir/$STATE_NAME" || die 'could not read state-root configuration'
		state_file_exists=true
	fi
	validate_single_line "$current_state_root" 'current state root'
	[[ "$current_state_root" == /* && "$current_state_root" != / ]] || die 'current state root must be an absolute non-root path'
	current_state_root=$(realpath -m -- "$current_state_root")
	if [[ "$state_mode" == keep && "$operation" == configure ]]; then
		state_root="$HOME/$DEFAULT_STATE_NAME"
		state_mode=custom
	elif [[ "$state_mode" == keep ]]; then
		state_root=$current_state_root
		if [[ "$operation" != remove && "$state_file_exists" == false ]]; then
			state_mode=custom
		fi
	fi
	validate_single_line "$state_root" 'state root'
	state_root=$(realpath -m -- "$state_root")
	[[ "$state_root" != / ]] || die 'state root must not be the filesystem root'

	bin_dir=${BROWSEROS_NEO_BIN_DIR:-"$HOME/.local/bin"}
	data_home=${XDG_DATA_HOME:-"$HOME/.local/share"}
	[[ "$bin_dir" == /* && "$data_home" == /* ]] || die 'command and XDG data directories must be absolute'
	validate_single_line "$bin_dir" 'command directory'
	validate_single_line "$data_home" 'XDG data directory'
	bin_dir=$(realpath -m -- "$bin_dir")
	data_home=$(realpath -m -- "$data_home")
	bin_link="$bin_dir/$LAUNCHER_NAME"
	desktop_file="$data_home/applications/browseros-neo.desktop"
	codex_config_path="${CODEX_HOME:-$HOME/.codex}/config.toml"
	[[ "$codex_config_path" == /* ]] || die 'Codex configuration path must be absolute'
	validate_single_line "$codex_config_path" 'Codex configuration path'
	source_dir=$(dirname -- "$(realpath -- "${BASH_SOURCE[0]}")")
	[[ "$bin_link" != "$install_dir/$LAUNCHER_NAME" ]] || die 'command-link directory cannot be the installation directory'
}

is_managed_install() {
	local marker=''
	[[ -f "$install_dir/$MARKER_NAME" && ! -L "$install_dir/$MARKER_NAME" ]] || return 1
	IFS= read -r marker <"$install_dir/$MARKER_NAME" || return 1
	[[ "$marker" == "$INSTALL_MARKER" ]]
}

is_managed_link() {
	[[ -L "$bin_link" && "$(readlink -- "$bin_link")" == "$install_dir/$LAUNCHER_NAME" ]]
}

is_managed_desktop() {
	local executable
	[[ -f "$desktop_file" && ! -L "$desktop_file" ]] || return 1
	executable=$(desktop_quote "$install_dir/$LAUNCHER_NAME")
	grep -Fqx -- 'X-BrowserOS-Neo-Managed=true' "$desktop_file" &&
		grep -Fqx -- "Exec=$executable %U" "$desktop_file"
}

ensure_profile_stopped() {
	local lock_path
	for lock_path in "$current_state_root/profile/SingletonLock" "$state_root/profile/SingletonLock" "$install_dir/profile/SingletonLock"; do
		[[ ! -e "$lock_path" && ! -L "$lock_path" ]] ||
			die "profile lock exists: $lock_path; close BrowserOS neo before continuing"
	done
}

check_installation() {
	local entry file
	if [[ -e "$install_dir" || -L "$install_dir" ]]; then
		[[ -d "$install_dir" && ! -L "$install_dir" ]] || die "not a real directory: $install_dir"
		if is_managed_install; then
			if [[ "$operation" == install && "$force" == false && -e "$install_dir/$IMAGE_NAME" ]]; then
				die 'installation already exists; use configure, update, or install --force'
			fi
		else
			[[ "$operation" == install ]] || die "not a managed installation: $install_dir"
			entry=$(find "$install_dir" -mindepth 1 -maxdepth 1 -print -quit)
			[[ -z "$entry" ]] || die "refusing to use a nonempty unmanaged directory: $install_dir"
		fi
	else
		[[ "$operation" == install ]] || die "installation directory not found: $install_dir"
	fi
	if [[ "$operation" != install ]] && is_managed_install; then
		[[ -f "$install_dir/$IMAGE_NAME" && ! -L "$install_dir/$IMAGE_NAME" ]] ||
			die "managed AppImage not found: $install_dir/$IMAGE_NAME"
	fi
	if [[ "$operation" == proxy ]]; then
		[[ -f "$install_dir/$LAUNCHER_NAME" && ! -L "$install_dir/$LAUNCHER_NAME" && -x "$install_dir/$LAUNCHER_NAME" ]] ||
			die "managed BrowserOS launcher not found: $install_dir/$LAUNCHER_NAME"
		return
	fi
	ensure_profile_stopped
	[[ ! -L "$state_root/profile" && ! -L "$state_root/cache" ]] ||
		die 'profile and cache must not be symbolic links'
	if [[ "$operation" == install || "$operation" == update ]]; then
		if [[ -e "$install_dir/profile" || -L "$install_dir/profile" ]]; then
			die "legacy profile found at $install_dir/profile; move it to $state_root/profile before updating"
		fi
	fi

	for file in "$IMAGE_NAME" "$LAUNCHER_NAME" "$MARKER_NAME" "$VERSION_NAME" "$STATE_NAME"; do
		if [[ -e "$install_dir/$file" || -L "$install_dir/$file" ]]; then
			[[ -f "$install_dir/$file" && ! -L "$install_dir/$file" ]] ||
				die "managed file is not a regular file: $install_dir/$file"
		fi
	done
	if [[ "$operation" != remove ]]; then
		if [[ -e "$bin_link" || -L "$bin_link" ]]; then
			is_managed_link || die "command entry belongs to another installation: $bin_link"
		fi
		if [[ -e "$desktop_file" || -L "$desktop_file" ]]; then
			is_managed_desktop || die "desktop entry belongs to another application: $desktop_file"
		fi
	fi
}

select_architecture() {
	case "$(uname -m)" in
	x86_64 | amd64)
		architecture=x64
		elf_machine=3e00
		;;
	aarch64 | arm64)
		architecture=arm64
		elf_machine=b700
		;;
	*) die "unsupported Linux architecture: $(uname -m)" ;;
	esac
}

fetch_latest_from_release_page() {
	local page=1 page_file entries candidates selected tag url version filename metadata
	page_file="$work_dir/release-page.html"
	entries="$work_dir/release-page-entries.tsv"
	candidates="$work_dir/release-page-candidates.tsv"
	: >"$candidates"
	while :; do
		((page <= 100)) || die 'release page listing exceeds the pagination limit'
		curl --fail --silent --show-error --location --retry 2 --connect-timeout 15 \
			--max-time 120 --proto '=https' --proto-redir '=https' \
			--output "$page_file" "$RELEASES_PAGE?page=$page" || die 'failed to fetch the official release page'
		awk -v arch="$architecture" '
			/<section id="release-browserclaw\/v[0-9]/ {
			  inside = 1; prerelease = 0; urls = ""; tag = $0
			  sub(/^.*<section id="release-/, "", tag); sub(/".*$/, "", tag)
			}
			inside {
			  if ($0 ~ /[Pp]re-release/ && $0 ~ /Label/) prerelease = 1
			  line = $0
			  pattern = "https://cdn[.]browseros[.]com/releases/browserclaw/[0-9]+[.][0-9]+[.][0-9]+([.][0-9]+)?/linux/BrowserOS_neo_v[0-9]+[.][0-9]+[.][0-9]+([.][0-9]+)?_" arch "[.]AppImage"
			  while (match(line, pattern)) {
			    urls = urls tag "\t" substr(line, RSTART, RLENGTH) "\n"
			    line = substr(line, RSTART + RLENGTH)
			  }
			  if ($0 ~ /<\/section>/) {
			    if (!prerelease) printf "%s", urls
			    inside = 0
			  }
			}
		' "$page_file" >"$entries" || die 'could not parse the official release page'
		while IFS=$'\t' read -r tag url; do
			[[ "$tag" =~ ^browserclaw/v[0-9]+(\.[0-9]+){2,3}$ ]] || continue
			if [[ "$url" =~ ^https://cdn\.browseros\.com/releases/browserclaw/([0-9]+(\.[0-9]+){2,3})/linux/BrowserOS_neo_v([0-9]+(\.[0-9]+){2,3})_${architecture}\.AppImage$ ]]; then
				[[ "${BASH_REMATCH[1]}" == "${BASH_REMATCH[3]}" ]] || continue
				printf '%s\t%s\t%s\n' "${BASH_REMATCH[1]}" "$tag" "$url" >>"$candidates"
			fi
		done <"$entries"
		[[ ! -s "$candidates" ]] || break
		grep -Fq -- 'rel="next"' "$page_file" || die "no stable BrowserOS neo AppImage release found for $architecture"
		((page += 1))
	done
	selected=$(LC_ALL=C sort -t $'\t' -k1,1V "$candidates" | tail -n 1)
	IFS=$'\t' read -r version tag url <<<"$selected"
	filename=${url##*/}
	metadata="$work_dir/release-linux.json"
	curl --fail --silent --show-error --location --retry 2 --connect-timeout 15 \
		--max-time 120 --proto '=https' --proto-redir '=https' \
		--output "$metadata" "$CDN_RELEASE_PREFIX$version/linux/release.json" || die 'failed to fetch official Linux release metadata'
	selected=$(jq -er --arg version "$version" --arg key "${architecture}_appimage" '
		select(.version == $version and .product == "browserclaw")
		| .artifacts[$key]
		| select(type == "object")
		| [(.filename // "missing"), (.sha256 // "missing"), (.size // 0 | tostring)] | @tsv
	' "$metadata") || die 'invalid official Linux release metadata'
	IFS=$'\t' read -r asset_name asset_digest asset_size <<<"$selected"
	[[ "$asset_name" == "$filename" ]] || die 'release page and metadata disagree on the AppImage filename'
	[[ "$asset_digest" =~ ^[0-9a-fA-F]{64}$ ]] || die 'official release metadata has no usable SHA-256'
	[[ "$asset_size" =~ ^[1-9][0-9]*$ ]] || die 'official release metadata has no valid size'
	release_version=$version
	release_tag=$tag
	asset_url=$url
	asset_digest=${asset_digest,,}
}

fetch_latest_release() {
	local page=1 count page_file candidates selected http_status
	page_file="$work_dir/releases.json"
	candidates="$work_dir/candidates.tsv"
	: >"$candidates"
	while :; do
		((page <= 100)) || die 'release listing exceeds the pagination limit'
		if ! http_status=$(curl --fail --silent --location --retry 2 --connect-timeout 15 \
			--max-time 120 --proto '=https' --proto-redir '=https' \
			--header 'Accept: application/vnd.github+json' \
			--header 'User-Agent: browseros-neo-installer' \
			--write-out '%{http_code}' --output "$page_file" "$RELEASES_API?per_page=100&page=$page"); then
			if [[ "$http_status" == 403 || "$http_status" == 429 ]]; then
				warn 'GitHub API rate limit reached; using the official release page and metadata'
				fetch_latest_from_release_page
				return
			fi
			die "failed to fetch GitHub release metadata (HTTP ${http_status:-unknown})"
		fi
		count=$(jq -er 'if type == "array" then length else error("expected an array") end' "$page_file") ||
			die 'invalid GitHub release response'
		jq -r --arg arch "$architecture" '
			.[]
			| select(.draft == false and .prerelease == false)
			| select((.tag_name // "") | test("^browserclaw/v[0-9]+(\\.[0-9]+){2,3}$"))
			| .tag_name as $tag
			| (.published_at // "unknown") as $published
			| .assets[]?
			| select(.state == "uploaded")
			| select((.name // "") | test("^BrowserOS_neo_v[0-9]+(\\.[0-9]+){2,3}_" + $arch + "\\.AppImage$"))
			| .name as $name
			| [($name | capture("^BrowserOS_neo_v(?<version>[0-9]+(\\.[0-9]+){2,3})_").version),
			   $name, (.browser_download_url // "missing"), (.digest // "missing"),
			   (.size // 0 | tostring), $tag, $published]
			| @tsv
		' "$page_file" >>"$candidates" || die 'could not parse GitHub release metadata'
		[[ ! -s "$candidates" ]] || break
		((count == 100)) || break
		((page += 1))
	done
	[[ -s "$candidates" ]] || die "no stable BrowserOS neo AppImage release found for $architecture"
	selected=$(LC_ALL=C sort -t $'\t' -k1,1V -k7,7 "$candidates" | tail -n 1)
	IFS=$'\t' read -r release_version asset_name asset_url asset_digest asset_size release_tag _ <<<"$selected"
	[[ "$asset_url" == "$RELEASE_DOWNLOAD_PREFIX"* && "$asset_url" == */"$asset_name" ]] ||
		die 'release asset URL is not an official BrowserOS GitHub download'
	[[ "$asset_digest" =~ ^sha256:[0-9a-fA-F]{64}$ ]] || die "release asset has no usable SHA-256: $asset_name"
	[[ "$asset_size" =~ ^[1-9][0-9]*$ ]] || die "release asset has no valid size: $asset_name"
	asset_digest=${asset_digest#sha256:}
	asset_digest=${asset_digest,,}
}

verify_image() {
	local image=$1 actual_size actual_digest magic machine
	actual_size=$(stat -c '%s' -- "$image")
	[[ "$actual_size" == "$asset_size" ]] || die "downloaded size does not match release metadata: $asset_name"
	actual_digest=$(sha256sum <"$image")
	actual_digest=${actual_digest%% *}
	[[ "$actual_digest" == "$asset_digest" ]] || die "SHA-256 mismatch: $asset_name"
	magic=$(od -An -tx1 -N11 -- "$image" | tr -d ' \n')
	[[ "$magic" == 7f454c4602010100414902 ]] || die 'downloaded file is not a 64-bit type 2 AppImage'
	machine=$(od -An -tx1 -j18 -N2 -- "$image" | tr -d ' \n')
	[[ "$machine" == "$elf_machine" ]] || die 'downloaded AppImage has the wrong architecture'
}

download_image() {
	local installed_image="$install_dir/$IMAGE_NAME" installed_digest installed_size
	if [[ -f "$installed_image" && ! -L "$installed_image" ]]; then
		installed_size=$(stat -c '%s' -- "$installed_image")
		if [[ "$installed_size" == "$asset_size" ]]; then
			installed_digest=$(sha256sum <"$installed_image")
			installed_digest=${installed_digest%% *}
			if [[ "$installed_digest" == "$asset_digest" ]]; then
				printf 'BrowserOS neo %s is already downloaded; reusing the verified image.\n' "$release_version"
				cp -- "$installed_image" "$work_dir/$IMAGE_NAME"
				verify_image "$work_dir/$IMAGE_NAME"
				return
			fi
		fi
	fi
	printf 'Downloading BrowserOS neo %s (%s)...\n' "$release_version" "$architecture"
	curl --fail --show-error --location --retry 2 --connect-timeout 15 --max-time 1800 \
		--proto '=https' --proto-redir '=https' --output "$work_dir/$IMAGE_NAME" "$asset_url" ||
		die "failed to download release asset: $asset_name"
	verify_image "$work_dir/$IMAGE_NAME"
}

write_launcher() {
	cat >"$work_dir/$LAUNCHER_NAME" <<'LAUNCHER'
#!/usr/bin/env bash
set -Eeuo pipefail

main() {
	local launcher_path install_dir state_root argument
	umask 077
	launcher_path=$(readlink -f -- "$0")
	install_dir=$(dirname -- "$launcher_path")
	[[ -n "${HOME:-}" && "$HOME" == /* ]] || {
		printf 'Error: HOME must be an absolute path.\n' >&2
		return 1
	}
	state_root="$HOME/.browseros-neo"
	for argument in "$@"; do
		case "$argument" in
		--user-data-dir | --user-data-dir=*)
			printf 'Error: the profile directory is managed by this launcher.\n' >&2
			return 1
			;;
		esac
	done
	if [[ -f "$install_dir/.browseros-neo-state-root" ]]; then
		IFS= read -r state_root <"$install_dir/.browseros-neo-state-root"
		[[ "$state_root" == /* && "$state_root" != / ]] || {
			printf 'Error: invalid BrowserOS neo state root.\n' >&2
			return 1
		}
	fi
	export BROWSERCLAW_DIR="$state_root/browserclaw"
	export BROWSEROS_DIR="$state_root/browseros"
	if [[ -e "$install_dir/profile" || -L "$install_dir/profile" ]]; then
		printf 'Error: legacy profile at %s must be migrated before launch.\n' "$install_dir/profile" >&2
		return 1
	fi
	[[ ! -L "$state_root/profile" && ! -L "$state_root/cache" ]] || {
		printf 'Error: profile and cache must not be symbolic links.\n' >&2
		return 1
	}
	mkdir -p -- "$state_root/profile" "$state_root/cache"
	export XDG_CACHE_HOME="$state_root/cache"
	exec "$install_dir/BrowserOS_neo.AppImage" "--user-data-dir=$state_root/profile" "$@"
}

main "$@"
LAUNCHER
	chmod 755 -- "$work_dir/$LAUNCHER_NAME"
}

desktop_quote() {
	local value=$1
	value=${value//\\/\\\\\\\\}
	value=${value//\"/\\\\\"}
	value=${value//\$/\\\\\$}
	value=${value//\`/\\\\\`}
	printf '"%s"' "$value"
}

write_desktop() {
	local executable
	executable=$(desktop_quote "$install_dir/$LAUNCHER_NAME")
	cat >"$work_dir/browseros-neo.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=BrowserOS neo
GenericName=Web Browser
Comment=Browser for agents
Exec=$executable %U
Icon=web-browser
Terminal=false
Categories=Network;WebBrowser;
MimeType=text/html;application/xhtml+xml;x-scheme-handler/http;x-scheme-handler/https;
StartupWMClass=chromium-browser
X-BrowserOS-Neo-Managed=true
EOF
	chmod 644 -- "$work_dir/browseros-neo.desktop"
}

replace_managed_file() {
	local name=$1 source=$2
	if [[ -e "$install_dir/$name" ]]; then
		: >"$transaction_dir/existed/$name"
	fi
	: >"$transaction_dir/touched/$name"
	if [[ -e "$install_dir/$name" ]]; then
		mv -- "$install_dir/$name" "$transaction_dir/previous/$name"
	fi
	if [[ -n "$source" ]]; then
		mv -- "$source" "$install_dir/$name"
	fi
}

rollback() {
	local name failed=false
	set +e
	if [[ "$created_desktop" == true ]] && is_managed_desktop; then
		rm -f -- "$desktop_file" || failed=true
	fi
	if [[ "$created_bin_link" == true ]] && is_managed_link; then
		rm -f -- "$bin_link" || failed=true
	fi
	for name in "$IMAGE_NAME" "$LAUNCHER_NAME" "$MARKER_NAME" "$VERSION_NAME" "$STATE_NAME" "$MCP_PROXY_NAME" "$MCP_SETUP_NAME"; do
		[[ -f "$transaction_dir/touched/$name" ]] || continue
		if [[ -e "$transaction_dir/previous/$name" ]]; then
			mv -f -- "$transaction_dir/previous/$name" "$install_dir/$name" || failed=true
		elif [[ ! -f "$transaction_dir/existed/$name" ]]; then
			rm -f -- "$install_dir/$name" || failed=true
		fi
	done
	if [[ "$failed" == true ]]; then
		warn "rollback was incomplete; retain and inspect: $transaction_dir"
		return 1
	fi
}

prepare_proxy() {
	local file
	require_command python3
	python_bin=$(command -v python3)
	[[ "$python_bin" == /* ]] || die 'python3 must resolve to an absolute path'
	python3 -c 'import sys, tomllib, anyio, httpx; from mcp.client.streamable_http import streamable_http_client; from mcp.server.stdio import stdio_server; sys.exit(sys.version_info < (3, 11))' ||
		die 'the MCP proxy requires Python 3.11+ and the mcp, anyio and httpx packages'
	for file in "$MCP_PROXY_NAME" "$MCP_SETUP_NAME"; do
		[[ -f "$source_dir/$file" && ! -L "$source_dir/$file" ]] || die "proxy source missing: $source_dir/$file"
		if [[ -e "$install_dir/$file" || -L "$install_dir/$file" ]]; then
			[[ -f "$install_dir/$file" && ! -L "$install_dir/$file" ]] || die "proxy target is not a regular file: $install_dir/$file"
			[[ -f "$install_dir/$MCP_MARKER_NAME" && ! -L "$install_dir/$MCP_MARKER_NAME" ]] ||
				die "refusing to replace an unmanaged proxy file: $install_dir/$file"
		fi
	done
	[[ ! -L "$install_dir/$MCP_MARKER_NAME" ]] || die 'proxy ownership record must not be a symbolic link'
	"$python_bin" "$source_dir/$MCP_SETUP_NAME" check "$codex_config_path" \
		"$install_dir/$MCP_PROXY_NAME" "$source_dir/$MCP_PROXY_NAME" "$python_bin" ||
		die 'Codex MCP configuration could not be updated safely'
}

install_proxy() {
	local stage_dir file
	if [[ "$transaction_active" == true && "$transaction_committed" == true ]]; then
		[[ -n "$transaction_dir" && "$transaction_dir" == "$install_dir/.browseros-neo-transaction."* && -d "$transaction_dir" && ! -L "$transaction_dir" ]] ||
			die 'invalid completed installation transaction directory'
		rm -rf -- "$transaction_dir"
		transaction_dir=''
		transaction_active=false
		created_desktop=false
		created_bin_link=false
		created_install_dir=false
	fi
	transaction_dir=$(mktemp -d "$install_dir/.browseros-neo-transaction.XXXXXXXX")
	stage_dir="$transaction_dir/staged"
	mkdir -- "$stage_dir" "$transaction_dir/previous" "$transaction_dir/touched" "$transaction_dir/existed"
	for file in "$MCP_PROXY_NAME" "$MCP_SETUP_NAME"; do
		cp -- "$source_dir/$file" "$stage_dir/$file"
		chmod 644 -- "$stage_dir/$file"
	done
	transaction_committed=false
	transaction_active=true
	for file in "$MCP_PROXY_NAME" "$MCP_SETUP_NAME"; do
		replace_managed_file "$file" "$stage_dir/$file"
	done
	"$python_bin" "$install_dir/$MCP_SETUP_NAME" enable "$codex_config_path" \
		"$install_dir/$MCP_PROXY_NAME" "$source_dir/$MCP_PROXY_NAME" "$python_bin" ||
		die 'application remains installed; proxy setup was rolled back'
	transaction_committed=true
	success "Enabled Codex MCP autostart: $install_dir/$MCP_PROXY_NAME"
	printf 'Start a new Codex session to load the updated connection.\n'
}

remove_proxy() {
	[[ -e "$install_dir/$MCP_MARKER_NAME" || -L "$install_dir/$MCP_MARKER_NAME" ]] || return 0
	[[ -f "$install_dir/$MCP_MARKER_NAME" && ! -L "$install_dir/$MCP_MARKER_NAME" ]] ||
		die 'proxy ownership record is not a regular file; preserving the application'
	require_command python3
	python_bin=$(command -v python3)
	[[ -f "$install_dir/$MCP_SETUP_NAME" && ! -L "$install_dir/$MCP_SETUP_NAME" ]] ||
		die 'managed MCP setup helper is missing; preserving the application and Codex config'
	"$python_bin" "$install_dir/$MCP_SETUP_NAME" disable "$codex_config_path" \
		"$install_dir/$MCP_PROXY_NAME" "$source_dir/$MCP_PROXY_NAME" "$python_bin" ||
		die 'could not safely restore Codex MCP configuration; preserving the application'
	rm -f -- "$install_dir/$MCP_PROXY_NAME" "$install_dir/$MCP_SETUP_NAME"
}

cleanup() {
	local result=$? rollback_ok=true
	trap - EXIT
	if [[ "$transaction_active" == true && "$transaction_committed" == false ]]; then
		rollback || rollback_ok=false
	fi
	if [[ "$rollback_ok" == true && -n "$transaction_dir" && -d "$transaction_dir" ]]; then
		rm -rf -- "$transaction_dir" || warn "could not remove temporary directory: $transaction_dir"
	fi
	if [[ -n "$desktop_temp" && -f "$desktop_temp" ]]; then
		rm -f -- "$desktop_temp" || warn "could not remove temporary file: $desktop_temp"
	fi
	if [[ -n "$state_temp" && -f "$state_temp" ]]; then
		rm -f -- "$state_temp" || warn "could not remove temporary file: $state_temp"
	fi
	if [[ "$transaction_committed" == false && "$rollback_ok" == true ]]; then
		if [[ "$created_install_dir" == true ]] && ! rmdir -- "$install_dir" 2>/dev/null; then
			warn "retained installation directory: $install_dir"
		fi
	fi
	if [[ -n "$work_dir" && -d "$work_dir" ]]; then
		rm -rf -- "$work_dir" || warn "could not remove temporary directory: $work_dir"
	fi
	exit "$result"
}

publish_installation() {
	local stage_dir name source
	mkdir -p -- "$(dirname -- "$install_dir")" "$(dirname -- "$bin_link")" "$(dirname -- "$desktop_file")"
	if [[ ! -d "$install_dir" ]]; then
		mkdir -m 700 -- "$install_dir"
		created_install_dir=true
	fi
	transaction_dir=$(mktemp -d "$install_dir/.browseros-neo-transaction.XXXXXXXX")
	stage_dir="$transaction_dir/staged"
	mkdir -- "$stage_dir" "$transaction_dir/previous" "$transaction_dir/touched" "$transaction_dir/existed"
	cp -- "$work_dir/$IMAGE_NAME" "$stage_dir/$IMAGE_NAME"
	cp -- "$work_dir/$LAUNCHER_NAME" "$stage_dir/$LAUNCHER_NAME"
	chmod 755 -- "$stage_dir/$IMAGE_NAME" "$stage_dir/$LAUNCHER_NAME"
	verify_image "$stage_dir/$IMAGE_NAME"
	printf '%s\n' "$INSTALL_MARKER" >"$stage_dir/$MARKER_NAME"
	printf '%s\n' "$release_version" >"$stage_dir/$VERSION_NAME"
	if [[ "$state_mode" == custom ]]; then
		printf '%s\n' "$state_root" >"$stage_dir/$STATE_NAME"
	fi
	ensure_profile_stopped
	transaction_active=true
	for name in "$IMAGE_NAME" "$LAUNCHER_NAME" "$MARKER_NAME" "$VERSION_NAME"; do
		replace_managed_file "$name" "$stage_dir/$name"
	done
	if [[ "$state_mode" == custom ]]; then
		source="$stage_dir/$STATE_NAME"
		replace_managed_file "$STATE_NAME" "$source"
	fi
	if [[ -e "$bin_link" || -L "$bin_link" ]]; then
		is_managed_link || die "command entry changed during installation: $bin_link"
	else
		ln -s -- "$install_dir/$LAUNCHER_NAME" "$bin_link"
		created_bin_link=true
	fi
	if [[ -e "$desktop_file" || -L "$desktop_file" ]]; then
		is_managed_desktop || die "desktop entry changed during installation: $desktop_file"
	else
		# Link creation is exclusive, so an existing desktop file is never replaced.
		desktop_temp=$(mktemp "$(dirname -- "$desktop_file")/.browseros-neo.XXXXXXXX")
		cp -- "$work_dir/browseros-neo.desktop" "$desktop_temp"
		chmod 644 -- "$desktop_temp"
		ln -- "$desktop_temp" "$desktop_file"
		created_desktop=true
		rm -- "$desktop_temp"
		desktop_temp=''
	fi
	transaction_committed=true
}

install_application() {
	work_dir=$(mktemp -d "${TMPDIR:-/tmp}/browseros-neo-install.XXXXXXXX")
	select_architecture
	fetch_latest_release
	download_image
	write_launcher
	write_desktop
	check_installation
	publish_installation
	success "Installed BrowserOS neo $release_version ($release_tag)."
	IFS= read -r state_root <"$install_dir/$STATE_NAME"
	printf '  Installation: %s\n  Profile: %s/profile\n  Cache: %s/cache\n  Command: %s\n  Desktop: %s\n' \
		"$install_dir" "$state_root" "$state_root" "$bin_link" "$desktop_file"
	printf '  State: %s/{browserclaw,browseros}\n' "$state_root"
	printf 'Existing state was not moved to the selected state root.\n'
	printf 'Existing browser profiles were not imported.\n'
}

configure_application() {
	state_temp=$(mktemp "$install_dir/.browseros-neo-state-root.XXXXXXXX")
	printf '%s\n' "$state_root" >"$state_temp"
	chmod 600 -- "$state_temp"
	ensure_profile_stopped
	[[ ! -L "$install_dir/$STATE_NAME" ]] || die 'state-root configuration must not be a symbolic link'
	mv -f -- "$state_temp" "$install_dir/$STATE_NAME"
	state_temp=''
	success "Configured BrowserOS neo state root: $state_root"
	printf 'Existing state was not moved to the selected state root.\n'
}

remove_application() {
	if is_managed_link; then
		rm -- "$bin_link"
	elif [[ -e "$bin_link" || -L "$bin_link" ]]; then
		warn "leaving an unrelated command entry unchanged: $bin_link"
	fi
	if is_managed_desktop; then
		rm -- "$desktop_file"
	elif [[ -e "$desktop_file" || -L "$desktop_file" ]]; then
		warn "leaving an unrelated desktop entry unchanged: $desktop_file"
	fi
	rm -f -- "$install_dir/$IMAGE_NAME" "$install_dir/$LAUNCHER_NAME"
	success "Removed BrowserOS neo from $install_dir."
	printf 'Preserved profile, cache, state and installation metadata.\n'
}

main() {
	parse_arguments "$@"
	umask 077
	[[ "$(uname -s)" == Linux ]] || die 'this installer supports Linux only'
	local command
	for command in realpath readlink find grep mkdir rmdir mktemp mv rm cp chmod ln dirname cat; do
		require_command "$command"
	done
	resolve_paths
	if [[ "$operation" == install && "$force" == false && "$state_explicit" == true ]] &&
		is_managed_install && [[ -f "$install_dir/$IMAGE_NAME" ]]; then
		operation=configure
	fi
	if [[ "$operation" == update && -e "$install_dir/$MCP_MARKER_NAME" ]]; then
		enable_mcp_proxy=true
	fi
	if [[ "$operation" == install || "$operation" == update ]]; then
		for command in curl jq sort tail stat sha256sum od tr awk; do
			require_command "$command"
		done
	fi
	check_installation
	if [[ "$enable_mcp_proxy" == true ]]; then
		prepare_proxy
	fi
	trap cleanup EXIT
	trap 'exit 130' INT
	trap 'exit 143' TERM
	case "$operation" in
	remove)
		remove_proxy
		remove_application
		;;
	proxy) install_proxy ;;
	configure)
		configure_application
		if [[ "$enable_mcp_proxy" == true ]]; then install_proxy; fi
		;;
	*)
		install_application
		if [[ "$enable_mcp_proxy" == true ]]; then install_proxy; fi
		;;
	esac
}

main "$@"
