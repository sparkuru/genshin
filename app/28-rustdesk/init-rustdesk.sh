#!/usr/bin/env bash
set -Eeuo pipefail

SCRIPT_NAME=${0##*/}
readonly SCRIPT_NAME
SCRIPT_DIR=$(cd -- "$(dirname -- "$0")" && pwd)
readonly SCRIPT_DIR
readonly ENV_TEMPLATE_PATH=$SCRIPT_DIR/.env.example
readonly RUNTIME_ENV_PATH=$SCRIPT_DIR/.env

usage() {
	printf 'Usage: %s [--force]\n' "$SCRIPT_NAME" >&2
	printf '\nCreate .env from .env.example and prepare the private data directory.\n' >&2
}

die() {
	printf 'Error: %s\n' "$*" >&2
	exit 1
}

require_commands() {
	local command_name

	for command_name in cp chmod install mktemp mv rm; do
		command -v "$command_name" >/dev/null 2>&1 || die "required command not found: $command_name"
	done
}

write_runtime_env() {
	local temporary_path

	temporary_path=$(mktemp "${RUNTIME_ENV_PATH}.XXXXXX")
	trap 'rm -f -- "$temporary_path"' RETURN
	cp -- "$ENV_TEMPLATE_PATH" "$temporary_path"
	chmod 600 -- "$temporary_path"
	mv -- "$temporary_path" "$RUNTIME_ENV_PATH"
	trap - RETURN
}

main() {
	local force=false

	while (($# > 0)); do
		case $1 in
		--force)
			force=true
			shift
			;;
		--help | -h)
			usage
			return 0
			;;
		*)
			die "unknown option: $1"
			;;
		esac
	done

	[[ -f $ENV_TEMPLATE_PATH ]] || die "missing template: $ENV_TEMPLATE_PATH"
	require_commands

	if [[ -e $RUNTIME_ENV_PATH && $force != true ]]; then
		printf 'Keeping existing %s\n' "$RUNTIME_ENV_PATH"
	else
		write_runtime_env
		printf 'Created %s\n' "$RUNTIME_ENV_PATH"
	fi

	install -d -m 700 -- "$SCRIPT_DIR/data"
	printf 'Prepared private data directory: %s\n' "$SCRIPT_DIR/data"
}

main "$@"
