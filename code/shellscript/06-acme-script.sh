#!/usr/bin/env bash
set -Eeuo pipefail

readonly WORKDIR="/opt/acme"
readonly HOME_ACME_DIR="/home/$USER/.acme.sh"
readonly DOMAIN="domain.top"    # change domain
readonly KEY_FILE_PATH="$WORKDIR/cert/$DOMAIN.key"
readonly CERT_FILE_PATH="$WORKDIR/cert/$DOMAIN.cer"
readonly FULLCHAIN_FILE_PATH="$WORKDIR/cert/fullchain.cer"

SUB_DOMAIN_LIST=(
	'*'
)

color() {
	printf '\033[33m%s\033[0m\n' "$1"
}

die() {
	printf 'Error: %s\n' "$*" >&2
	exit 1
}

append_domains() {
	local -n command_ref=$1
	local sub_domain

	command_ref+=(-d "$DOMAIN")
	for sub_domain in "${SUB_DOMAIN_LIST[@]}"; do
		command_ref+=(-d "$sub_domain.$DOMAIN")
	done
}

main() {
	local action=${1:-}
	local run_mode=${2:-}
	local debug_mode=${3:-}
	local reload_cmd
	local command=()

	[[ -n "$action" ]] || die "usage: $0 <issue|install|info> [run] [debug]"

	if [[ ! -d "$HOME_ACME_DIR" ]]; then
		color "no $HOME_ACME_DIR found, run curl https://get.acme.sh | sh -s email=my@example.com first."
		exit 1
	fi

	mkdir -p -- "$WORKDIR"
	cd "$WORKDIR"
	# shellcheck source=/dev/null
	. "$HOME_ACME_DIR/acme.sh.env"

	# Cloudflare DNS API for acme.sh dns_cf.
	export CF_Account_ID="32-length-string"
	export CF_Token="53-length-api-token"

	case "$action" in
	issue)
		command=(acme.sh --issue --dns dns_cf --force)
		append_domains command
		;;
	install)
		reload_cmd="sudo systemctl restart nginx"
		command=(
			acme.sh --install-cert
			--key-file "$KEY_FILE_PATH"
			--cert-file "$CERT_FILE_PATH"
			--fullchain-file "$FULLCHAIN_FILE_PATH"
			--reloadcmd "$reload_cmd"
		)
		append_domains command
		;;
	info)
		command=(acme.sh --info)
		append_domains command
		;;
	*)
		die "unknown action: $action"
		;;
	esac

	color "Execute: ${command[*]}"
	if [[ "$run_mode" == "run" ]]; then
		if [[ "$debug_mode" == "debug" ]]; then
			command+=(--debug)
		fi
		"${command[@]}"
	fi
}

main "$@"
