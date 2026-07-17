#!/usr/bin/env bash
set -Eeuo pipefail

readonly SCRIPT_NAME=${0##*/}
readonly SOURCE_BASE_URL="${HEDGEDOC_SOURCE_BASE_URL:-https://raw.githubusercontent.com/sparkuru/genshin/main/app/06-hedgedoc}"
readonly STYLE_RESET=$'\033[0m'
readonly STYLE_SUCCESS=$'\033[0;32m'
readonly STYLE_WARNING=$'\033[1;33m'
readonly STYLE_ERROR=$'\033[1;31m'

install_dir=''
public_url=''
db_url=''
offline=true
force=false
download_only=false
tmp_dir=''

usage() {
	printf 'Usage:\n' >&2
	printf '  %s --path <installation-directory> --public-url <url> [--offline] [--force]\n' "$SCRIPT_NAME" >&2
	printf '  %s --path <installation-directory> --public-url <url> --external-db --db-url <url> [--force]\n' "$SCRIPT_NAME" >&2
	printf '\nInstall HedgeDoc from the repository deployment templates.\n' >&2
	printf '\nOptions:\n' >&2
	printf '  --path <directory>    Installation directory (required).\n' >&2
	printf '  --public-url <url>    Canonical HTTP(S) URL used by browsers (required).\n' >&2
	printf '  --offline             Install HedgeDoc, MariaDB, and Nginx locally (default).\n' >&2
	printf '  --external-db         Install HedgeDoc for an existing MariaDB or MySQL database.\n' >&2
	printf '  --db-url <url>        Database URL required with --external-db.\n' >&2
	printf '  --force               Replace downloaded deployment templates and update the public URL.\n' >&2
	printf '  --download-only       Download and initialize files without starting containers.\n' >&2
	printf '  --help                Show this help message.\n' >&2
}

color_text() {
	local style=$1
	local message=$2

	if [[ -n ${NO_COLOR:-} || ! -t 1 ]]; then
		printf '%s' "$message"
		return
	fi

	printf '%s%s%s' "$style" "$message" "$STYLE_RESET"
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
	if [[ -n $tmp_dir && -d $tmp_dir ]]; then
		rm -rf -- "$tmp_dir"
	fi
}

parse_arguments() {
	while (($# > 0)); do
		case $1 in
		--path)
			(($# >= 2)) || die '--path requires a directory'
			[[ -z $install_dir ]] || die '--path may only be specified once'
			install_dir=$2
			shift 2
			;;
		--public-url)
			(($# >= 2)) || die '--public-url requires a value'
			[[ -z $public_url ]] || die '--public-url may only be specified once'
			public_url=$2
			shift 2
			;;
		--db-url)
			(($# >= 2)) || die '--db-url requires a value'
			[[ -z $db_url ]] || die '--db-url may only be specified once'
			db_url=$2
			shift 2
			;;
		--offline)
			offline=true
			shift
			;;
		--external-db)
			offline=false
			shift
			;;
		--force)
			force=true
			shift
			;;
		--download-only)
			download_only=true
			shift
			;;
		--help | -h)
			usage
			exit 0
			;;
		*)
			die "unknown argument: $1"
			;;
		esac
	done

	[[ -n $install_dir ]] || die 'an installation directory is required; pass --path <directory>'
	[[ -n $public_url ]] || die 'a public URL is required; pass --public-url <url>'
	if [[ $offline == true ]]; then
		[[ -z $db_url ]] || die '--db-url is only valid with --external-db'
	else
		[[ -n $db_url ]] || die '--external-db requires --db-url <url>'
	fi
}

resolve_install_dir() {
	if [[ $install_dir != /* ]]; then
		install_dir=$PWD/$install_dir
	fi

	install_dir=${install_dir%/}
	[[ -n $install_dir && $install_dir != / ]] || die 'refusing to use the filesystem root as the installation directory'
}

assert_replaceable() {
	local path=$1

	if [[ -e $path || -L $path ]]; then
		[[ $force == true ]] || die "path already exists: $path (pass --force to replace it)"
	fi
}

download_file() {
	local filename=$1
	local destination="$install_dir/$filename"
	local staged_file="$tmp_dir/$filename"

	assert_replaceable "$destination"
	curl --fail --location --retry 3 --silent --show-error --output "$staged_file" "$SOURCE_BASE_URL/$filename"
	mv -- "$staged_file" "$destination"
}

download_templates() {
	local compose_file
	local filename

	mkdir -p -- "$install_dir"
	tmp_dir=$(mktemp -d "${TMPDIR:-/tmp}/hedgedoc-deploy.XXXXXXXX")
	trap cleanup EXIT

	if [[ $offline == true ]]; then
		compose_file='hedgedoc-offline.yml'
	else
		compose_file='hedgedoc.yml'
	fi

	for filename in '.gitignore' 'init-hedgedoc.sh' 'nginx.conf' 'readme.md' "$compose_file"; do
		download_file "$filename"
	done
	chmod 755 -- "$install_dir/init-hedgedoc.sh"
}

initialize_installation() {
	local initializer="$install_dir/init-hedgedoc.sh"
	local command=("$initializer" --public-url "$public_url")

	if [[ $offline == false ]]; then
		command+=(--db-url "$db_url")
	fi
	if [[ $force == true && -f $install_dir/.hedgedoc.env ]]; then
		command+=(--force)
	fi

	"${command[@]}"
}

start_installation() {
	local compose_file

	if [[ $offline == true ]]; then
		compose_file='hedgedoc-offline.yml'
	else
		compose_file='hedgedoc.yml'
	fi

	(
		cd -- "$install_dir"
		docker compose --env-file .hedgedoc.env -f "$compose_file" up -d
	)
}

main() {
	parse_arguments "$@"
	resolve_install_dir
	require_command curl
	require_command mkdir
	require_command mktemp
	require_command mv
	require_command chmod

	if [[ $download_only == false ]]; then
		require_command docker
		docker compose version >/dev/null 2>&1 || die 'Docker Compose v2 is required'
	fi

	download_templates
	initialize_installation

	if [[ $download_only == true ]]; then
		info 'HedgeDoc deployment files downloaded and initialized'
		printf '  Directory: %s\n' "$install_dir"
		return
	fi

	start_installation
	info 'HedgeDoc installation complete'
	printf '  Directory: %s\n' "$install_dir"
	printf '  Public URL: %s\n' "$public_url"
}

main "$@"
