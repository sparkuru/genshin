#!/usr/bin/env bash
set -Eeuo pipefail

readonly SCRIPT_NAME=${0##*/}
readonly MARKER='portable-pm2-v1'
readonly STYLE_RESET=$'\033[0m'
readonly STYLE_SUCCESS=$'\033[0;32m'
readonly STYLE_ERROR=$'\033[1;31m'
install_dir=''
node_version='lts'
pm2_version='latest'
tmp_dir=''
stage_dir=''
profile_tmp=''
user_home=''
config_dir=''
bin_dir=''
profiles=()

color_text() {
	local style=$1 message=$2
	if [[ -n ${NO_COLOR:-} || ! -t 1 ]]; then
		printf '%s' "$message"
	else
		printf '%s%s%s' "$style" "$message" "$STYLE_RESET"
	fi
}

die() {
	printf '%s\n' "$(color_text "$STYLE_ERROR" "Error: $*")" >&2
	exit 1
}

require_command() {
	command -v "$1" >/dev/null 2>&1 || die "required command not found: $1"
}

usage() {
	cat <<EOF
Usage: $SCRIPT_NAME --path <directory> [--node-version <version>] [--pm2-version <version>]

Install a private Node.js (including npm) and PM2 on glibc Linux x64/arm64.
The destination must be empty/new or an installation made by this script.
Existing managed installations are reused, never silently upgraded.
Version options accept exact versions; defaults are latest LTS and latest PM2.

Commands are linked into ~/.local/bin. Bash, zsh and POSIX login profiles
source ~/.local/share/portable-pm2/env.sh. Existing profiles are backed up.
Open a new shell or source that file to update an already-running shell.
An executable installer cannot change its parent shell's environment.

Usage after installation:
  pm2 start app.js --name my-app
  pm2 save
  pm2 startup                 Enable a systemd USER service; requires existing linger.
  pm2 startup --login         Explicitly accept startup only when the user manager starts.
  pm2 unstartup               Disable this user startup hook; keep running applications.

This script never invokes sudo, enables linger, edits system profiles, or
installs a system service. Boot before login requires the administrator to
have already enabled linger for this user. Without it, that guarantee is
impossible using only user service files. Other PM2 commands are forwarded.
Startup accepts only the systemd platform, for the current user/default PM2_HOME.
User services have their own PATH; they do not read interactive shell profiles.

The installation path may be outside HOME if its existing parent is owned
by this user, but system directories and other users' home trees are rejected.
Run without root or sudo. Dependencies: Bash, curl, tar, xz, GNU coreutils, awk, grep.
EOF
}

cleanup() {
	[[ -z $profile_tmp || ! -f $profile_tmp ]] || rm -f -- "$profile_tmp"
	if [[ -n $stage_dir && ${stage_dir##*/} == .pm2-install.* && -d $stage_dir && -O $stage_dir ]]; then
		rm -rf -- "$stage_dir"
	fi
	if [[ $tmp_dir == /tmp/pm2-install.* && -d $tmp_dir && -O $tmp_dir ]]; then
		rm -rf -- "$tmp_dir"
	fi
}

parse_arguments() {
	while (($#)); do
		case $1 in
		--path)
			[[ $# -ge 2 && -n $2 && -z $install_dir ]] || die '--path requires one directory'
			install_dir=$2
			shift 2
			;;
		--node-version | --pm2-version)
			[[ $# -ge 2 && $2 =~ ^v?[0-9]+\.[0-9]+\.[0-9]+$ ]] || die "$1 requires an exact version"
			if [[ $1 == --node-version ]]; then node_version=${2#v}; else pm2_version=${2#v}; fi
			shift 2
			;;
		--help | -h)
			usage
			exit 0
			;;
		*) die "unknown argument: $1" ;;
		esac
	done
	[[ -n $install_dir ]] || die 'pass --path <directory>'
}

assert_owned_parent() {
	local path=$1
	while [[ ! -e $path ]]; do
		path=${path%/*}
		[[ -n $path ]] || path=/
	done
	[[ -d $path && -O $path && -w $path ]] || die "directory must be owned and writable by this user: $path"
}

assert_home_path() {
	local path resolved
	path=$1
	resolved=$(realpath -m -- "$path")
	[[ $resolved == "$user_home/"* ]] || die "user configuration escapes HOME: $path"
	assert_owned_parent "$(dirname -- "$resolved")"
	if [[ -e $path || -L $path ]]; then
		[[ -O $path && ! -L $path ]] || die "refusing a symlink or foreign-owned configuration: $path"
	fi
}

preflight() {
	local tool profile zsh_dir
	[[ $EUID -ne 0 && -z ${SUDO_USER:-} ]] || die 'run as the ordinary user, without sudo'
	for tool in realpath dirname mkdir mktemp rm mv cp chmod ln readlink uname curl tar xz sha256sum awk grep find cat cmp; do
		require_command "$tool"
	done
	[[ $(uname -s) == Linux ]] || die 'this installer supports Linux (systemd user startup)'
	[[ -n ${HOME:-} && -d $HOME && -O $HOME ]] || die 'HOME must be an existing directory owned by this user'
	user_home=$(realpath -e -- "$HOME")
	install_dir=$(realpath -m -- "$install_dir")
	[[ ! $install_dir =~ [[:cntrl:]] && ! $user_home =~ [[:cntrl:]] ]] || die 'control characters in paths are unsupported'
	[[ $install_dir != *:* && $user_home != *:* ]] || die 'colons in PATH directories are unsupported'
	[[ $user_home/ != "$install_dir/"* ]] || die 'installation directory must not contain HOME'
	case $install_dir/ in
	/etc/* | /usr/* | /bin/* | /sbin/* | /lib/* | /lib64/* | /boot/* | /var/* | /run/* | /dev/* | /proc/* | /sys/* | /root/*)
		die "refusing a system installation path: $install_dir"
		;;
	/home/*) [[ $install_dir == "$user_home/"* ]] || die 'refusing another home directory' ;;
	esac
	assert_owned_parent "$(dirname -- "$install_dir")"
	if [[ -e $install_dir ]]; then
		[[ -d $install_dir && -O $install_dir ]] || die 'destination must be a user-owned directory'
		if [[ -f $install_dir/.portable-pm2 ]]; then
			[[ $(cat -- "$install_dir/.portable-pm2") == "$MARKER:$EUID" ]] || die 'installation marker does not match'
		else
			[[ -z $(find "$install_dir" -mindepth 1 -maxdepth 1 -print -quit) ]] || die 'destination is not empty or managed'
		fi
	fi
	config_dir=$user_home/.local/share/portable-pm2
	bin_dir=$user_home/.local/bin
	for profile in "$bin_dir" "$config_dir"; do
		[[ $install_dir/ != "$profile/"* && $profile/ != "$install_dir/"* ]] || die 'installation and user integration directories must not overlap'
		assert_home_path "$profile"
	done
	if [[ -e $config_dir ]]; then
		[[ -f $config_dir/install-path && $(cat -- "$config_dir/install-path") == "$install_dir" ]] || die 'another installation or unmanaged environment directory exists'
	fi
	for profile in "$config_dir/install-path" "$config_dir/env.sh"; do
		assert_home_path "$profile"
		[[ ! -e $profile || -f $profile ]] || die "not a regular environment file: $profile"
	done
	for tool in node npm npx pm2 pm2-runtime pm2-dev; do
		if [[ -e $bin_dir/$tool || -L $bin_dir/$tool ]]; then
			[[ -L $bin_dir/$tool && $(readlink -- "$bin_dir/$tool") == "$install_dir/bin/$tool" ]] || die "command already exists: $bin_dir/$tool"
		fi
	done
	zsh_dir=${ZDOTDIR:-$user_home}
	[[ $(realpath -m -- "$zsh_dir") == "$user_home" || $(realpath -m -- "$zsh_dir") == "$user_home/"* ]] || die 'ZDOTDIR must be inside HOME'
	profiles=("$user_home/.profile" "$user_home/.bashrc" "$zsh_dir/.zshrc" "$zsh_dir/.zprofile")
	for profile in "$user_home/.bash_profile" "$user_home/.bash_login"; do
		[[ ! -e $profile && ! -L $profile ]] || profiles+=("$profile")
	done
	for profile in "${profiles[@]}"; do
		assert_home_path "$profile"
		[[ ! -e $profile || -f $profile ]] || die "not a regular shell profile: $profile"
	done
}

write_launcher() {
	cat >"$stage_dir/bin/launch.sh" <<'LAUNCHER'
#!/usr/bin/env bash
set -Eeuo pipefail
[[ $EUID -ne 0 && -z ${SUDO_USER:-} ]] || {
	printf 'Run PM2 as the installing user, without sudo.\n' >&2
	exit 1
}
launcher=$(readlink -f -- "${BASH_SOURCE[0]}")
prefix=${launcher%/bin/launch.sh}
[[ -O $prefix/.portable-pm2 ]] || {
	printf 'This installation belongs to another user.\n' >&2
	exit 1
}
export PATH="$prefix/bin:$prefix/npm/bin:$HOME/.local/bin:$PATH"
export NPM_CONFIG_PREFIX="$prefix/npm"
command_name=${0##*/}
case $command_name in
npm | npx) cli="$prefix/node/lib/node_modules/npm/bin/$command_name-cli.js" ;;
pm2)
	startup_args=("$@")
	while [[ ${startup_args[0]:-} == --silent || ${startup_args[0]:-} == -s || ${startup_args[0]:-} == --no-color || ${startup_args[0]:-} == -- ]]; do
		startup_args=("${startup_args[@]:1}")
	done
	case ${startup_args[0]:-} in
	startup | unstartup) exec /bin/bash "$prefix/lib/user-startup.sh" "${startup_args[@]}" ;;
	esac
	# Do not let alternate leading-option syntax reach upstream's system installer.
	if [[ ${1:-} == -* ]]; then
		for argument in "$@"; do
			case $argument in
			startup | unstartup)
				printf 'Place startup/unstartup first (only --silent, -s and --no-color may precede it).\n' >&2
				exit 2
				;;
			esac
		done
	fi
	cli="$prefix/npm/lib/node_modules/pm2/bin/pm2"
	;;
pm2-runtime | pm2-dev) cli="$prefix/npm/lib/node_modules/pm2/bin/$command_name" ;;
*)
	printf 'Unknown launcher: %s\n' "$command_name" >&2
	exit 1
	;;
esac
exec "$prefix/node/bin/node" "$cli" "$@"
LAUNCHER
	chmod 755 -- "$stage_dir/bin/launch.sh"
	ln -s ../node/bin/node "$stage_dir/bin/node"
	local tool
	for tool in npm npx pm2 pm2-runtime pm2-dev; do ln -s launch.sh "$stage_dir/bin/$tool"; done
}

write_startup_helper() {
	cat >"$stage_dir/lib/user-startup.sh" <<'STARTUP'
#!/usr/bin/env bash
set -Eeuo pipefail
readonly UNIT_NAME='pm2-portable.service'
readonly UNIT_MARKER='# Managed by portable-pm2-v1'
startup_tmp=''
trap '[[ -z $startup_tmp || ! -f $startup_tmp ]] || rm -f -- "$startup_tmp"' EXIT
fail() {
	printf 'Error: %s\n' "$*" >&2
	exit 1
}
main() {
	local action=${1:-} login_only=false arg user_home config_dir unit_file linger parent
	[[ $EUID -ne 0 && -z ${SUDO_USER:-} ]] || fail 'run without root or sudo'
	shift
	for arg in "$@"; do
		case $arg in
		--help | -h)
			printf 'Usage: pm2 startup [systemd] [--login]\n       pm2 unstartup [systemd]\n'
			printf 'Default startup requires existing user linger. --login accepts login-time startup.\n'
			printf 'All operations use systemctl --user; no system startup hooks or linger settings are changed.\n'
			return
			;;
		systemd) ;;
		--login)
			[[ $action == startup ]] || fail '--login is only valid with startup'
			login_only=true
			;;
		*) fail 'supported: pm2 startup [systemd] [--login] or pm2 unstartup [systemd]' ;;
		esac
	done
	for arg in systemctl realpath mkdir mktemp mv rm grep cat cmp; do command -v "$arg" >/dev/null || fail "missing command: $arg"; done
	user_home=$(realpath -e -- "$HOME")
	[[ -O $user_home ]] || fail 'HOME must belong to this user'
	[[ $(realpath -m -- "${PM2_HOME:-$user_home/.pm2}") == "$user_home/.pm2" ]] || fail 'startup manages only the default ~/.pm2; unset custom PM2_HOME'
	config_dir=$(realpath -m -- "${XDG_CONFIG_HOME:-$user_home/.config}/systemd/user")
	[[ $config_dir == "$user_home/"* ]] || fail 'systemd user configuration must stay inside HOME'
	parent=$config_dir
	while [[ ! -e $parent ]]; do parent=${parent%/*}; done
	[[ -d $parent && -O $parent ]] || fail 'user unit parent directory is not owned by this user'
	unit_file=$config_dir/$UNIT_NAME
	if [[ -e $unit_file || -L $unit_file ]]; then
		[[ -f $unit_file && ! -L $unit_file && -O $unit_file ]] || fail 'refusing a foreign or symlinked unit'
		grep -Fqx -- "$UNIT_MARKER" "$unit_file" || fail 'refusing to replace an unmanaged unit'
	fi
	systemctl --user show-environment >/dev/null || fail 'no reachable systemd user manager; run in a normal login session'
	if [[ $action == unstartup ]]; then
		[[ -f $unit_file ]] || {
			printf 'No managed user startup unit exists.\n'
			return
		}
		systemctl --user disable "$UNIT_NAME"
		rm -- "$unit_file"
		systemctl --user daemon-reload
		printf 'User startup disabled; running applications were kept.\n'
		return
	fi
	[[ $action == startup ]] || fail 'unknown startup action'
	command -v loginctl >/dev/null || fail 'loginctl is required to check boot startup support'
	linger=$(loginctl show-user "$EUID" --property=Linger --value) || fail 'cannot determine linger state'
	if [[ $linger != yes && $login_only == false ]]; then
		fail 'linger is not enabled. Boot before login requires pre-existing administrator configuration. No settings changed. Use pm2 startup --login to accept startup at login.'
	fi
	mkdir -p -- "$config_dir"
	[[ -O $config_dir ]] || fail 'user unit directory is not owned by this user'
	startup_tmp=$(mktemp "$config_dir/.pm2-unit.XXXXXXXX")
	cat >"$startup_tmp" <<'UNIT'
# Managed by portable-pm2-v1
[Unit]
Description=Portable PM2 for the current user
Documentation=https://pm2.io/docs/runtime/guide/startup-hook/

[Service]
Type=forking
Environment="PM2_HOME=%h/.pm2"
PIDFile=%h/.pm2/pm2.pid
ExecStart="%h/.local/bin/pm2" resurrect
ExecReload="%h/.local/bin/pm2" reload all
ExecStop="%h/.local/bin/pm2" kill
Restart=on-failure
RestartSec=5
TimeoutStartSec=60
TimeoutStopSec=60

[Install]
WantedBy=default.target
UNIT
	if [[ -f $unit_file ]]; then
		cmp -s -- "$startup_tmp" "$unit_file" || fail 'managed unit has been edited; refusing to overwrite it'
	else
		mv -T -- "$startup_tmp" "$unit_file"
	fi
	systemctl --user daemon-reload
	systemctl --user enable "$UNIT_NAME"
	printf 'Enabled %s for this user. Run pm2 save after changing the process list.\n' "$UNIT_NAME"
	printf 'The hook runs on the next user-manager start; existing applications were not restarted.\n'
	if [[ $linger != yes ]]; then printf 'Login-only mode: no guarantee of startup before login or persistence after logout.\n'; fi
}
main "$@"
STARTUP
	chmod 755 -- "$stage_dir/lib/user-startup.sh"
}

download_runtime() {
	local architecture archive checksum
	case $(uname -m) in
	x86_64) architecture=x64 ;;
	aarch64 | arm64) architecture=arm64 ;;
	*) die 'supported architectures: x86_64 and aarch64' ;;
	esac
	tmp_dir=$(mktemp -d /tmp/pm2-install.XXXXXXXX)
	if [[ $node_version == lts ]]; then
		curl --fail --silent --show-error --location --retry 2 --proto '=https' --proto-redir '=https' --connect-timeout 15 --max-time 120 \
			-o "$tmp_dir/index.tab" https://nodejs.org/dist/index.tab
		node_version=$(awk 'NR > 1 && $10 != "-" { sub(/^v/, "", $1); print $1; exit }' "$tmp_dir/index.tab")
	fi
	[[ $node_version =~ ^[0-9]+\.[0-9]+\.[0-9]+$ ]] || die 'invalid Node.js release metadata'
	archive=node-v$node_version-linux-$architecture.tar.xz
	local resource
	for resource in "$archive" SHASUMS256.txt; do
		curl --fail --silent --show-error --location --retry 2 --proto '=https' --proto-redir '=https' --connect-timeout 15 --max-time 600 \
			-o "$tmp_dir/$resource" "https://nodejs.org/dist/v$node_version/$resource"
	done
	checksum=$(awk -v name="$archive" '$2 == name { print $1 }' "$tmp_dir/SHASUMS256.txt")
	[[ $checksum =~ ^[a-fA-F0-9]{64}$ ]] || die 'invalid or absent official archive checksum'
	printf '%s  %s\n' "$checksum" "$archive" >"$tmp_dir/checksum"
	(cd "$tmp_dir" && sha256sum --check checksum)
	mkdir -p -- "$(dirname -- "$install_dir")"
	# Stage beside the destination so publication is a same-filesystem rename.
	stage_dir=$(mktemp -d "$(dirname -- "$install_dir")/.pm2-install.XXXXXXXX")
	mkdir -- "$stage_dir/node" "$stage_dir/npm" "$stage_dir/bin" "$stage_dir/lib" "$stage_dir/backups"
	tar -xJf "$tmp_dir/$archive" --strip-components=1 --no-same-owner -C "$stage_dir/node"
	"$stage_dir/node/bin/node" --version
	: >"$tmp_dir/user.npmrc"
	: >"$tmp_dir/global.npmrc"
	PATH="$stage_dir/node/bin:$PATH" NPM_CONFIG_PREFIX="$stage_dir/npm" NPM_CONFIG_CACHE="$tmp_dir/npm-cache" \
		NPM_CONFIG_USERCONFIG="$tmp_dir/user.npmrc" NPM_CONFIG_GLOBALCONFIG="$tmp_dir/global.npmrc" \
		"$stage_dir/node/bin/node" "$stage_dir/node/lib/node_modules/npm/bin/npm-cli.js" \
		install --global --prefix "$stage_dir/npm" --registry=https://registry.npmjs.org --no-audit --no-fund --no-update-notifier "pm2@$pm2_version"
	[[ -f $stage_dir/npm/lib/node_modules/pm2/bin/pm2 ]] || die 'PM2 installation is incomplete'
	write_launcher
	write_startup_helper
	printf '%s:%s\n' "$MARKER" "$EUID" >"$stage_dir/.portable-pm2"
	mv -T -- "$stage_dir" "$install_dir"
	stage_dir=''
}

configure_environment() {
	local profile backup hook
	mkdir -p -- "$config_dir" "$bin_dir"
	printf '%s\n' "$install_dir" >"$config_dir/install-path"
	profile_tmp=$(mktemp "$config_dir/.env.XXXXXXXX")
	{
		printf '# Managed by portable-pm2-v1\n'
		local quoted_prefix=${install_dir//\'/\'\\\'\'}
		printf "export NPM_CONFIG_PREFIX='%s/npm'\n" "$quoted_prefix"
		cat <<'ENVIRONMENT'
case "$PATH" in
  "$HOME/.local/bin:$NPM_CONFIG_PREFIX/bin" | "$HOME/.local/bin:$NPM_CONFIG_PREFIX/bin:"*) ;;
  *) PATH="$HOME/.local/bin:$NPM_CONFIG_PREFIX/bin:$PATH" ;;
esac
export PATH
ENVIRONMENT
	} >"$profile_tmp"
	if [[ -f $config_dir/env.sh ]]; then
		cmp -s -- "$profile_tmp" "$config_dir/env.sh" || die 'managed environment file has been edited; refusing to overwrite it'
		rm -- "$profile_tmp"
	else
		mv -T -- "$profile_tmp" "$config_dir/env.sh"
	fi
	profile_tmp=''
	local tool
	for tool in node npm npx pm2 pm2-runtime pm2-dev; do
		[[ -L $bin_dir/$tool ]] || ln -s -- "$install_dir/bin/$tool" "$bin_dir/$tool"
	done
	# This hook is evaluated by a later user shell, not by the installer.
	# shellcheck disable=SC2016
	hook='[ ! -f "$HOME/.local/share/portable-pm2/env.sh" ] || . "$HOME/.local/share/portable-pm2/env.sh"'
	for profile in "${profiles[@]}"; do
		if [[ -f $profile ]] && grep -Fqx -- "$hook" "$profile"; then continue; fi
		mkdir -p -- "$(dirname -- "$profile")"
		profile_tmp=$(mktemp "$(dirname -- "$profile")/.pm2-profile.XXXXXXXX")
		if [[ -f $profile ]]; then
			backup=$(mktemp "$install_dir/backups/${profile##*/}.XXXXXXXX")
			cp -p -- "$profile" "$backup"
			cp -p -- "$profile" "$profile_tmp"
		fi
		printf '\n# Portable Node.js, npm and PM2 (current user only).\n%s\n' "$hook" >>"$profile_tmp"
		mv -T -- "$profile_tmp" "$profile"
		profile_tmp=''
	done
}

main() {
	parse_arguments "$@"
	preflight
	umask 077
	trap cleanup EXIT
	trap 'exit 130' INT
	trap 'exit 143' TERM
	if [[ -f $install_dir/.portable-pm2 ]]; then
		[[ $node_version == lts && $pm2_version == latest ]] || die 'version selection applies only to new installations; use a new destination for upgrades'
		[[ -x $install_dir/bin/pm2 && -x $install_dir/bin/node && -d $install_dir/backups ]] || die 'managed installation is incomplete'
		printf 'Reusing managed installation: %s\n' "$install_dir"
	else
		download_runtime
	fi
	configure_environment
	printf '%s\n' "$(color_text "$STYLE_SUCCESS" 'User-level Node.js, npm and PM2 installed.')"
	printf 'Installation: %s\nCommands: %s\nProfile backups: %s/backups\n' "$install_dir" "$bin_dir" "$install_dir"
	printf 'Activate in the current shell: . %q\n' "$config_dir/env.sh"
	printf 'Then: pm2 start app.js; pm2 save; pm2 startup\n'
	printf 'Use pm2 startup --login only if login-time startup is sufficient.\n'
}

if [[ ${BASH_SOURCE[0]} == "$0" ]]; then main "$@"; fi
