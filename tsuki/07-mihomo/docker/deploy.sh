#!/usr/bin/env bash
set -Eeuo pipefail

# User configuration
REMOTE_HOST=""
REMOTE_USER="root"
# provide if needed
REMOTE_PASSWORD=""
REMOTE_PORT="22"
SSH_IDENTITY_FILE=""
REMOTE_DEPLOY_DIR="/opt/mihomua"
SUBSCRIPTION_URL=""
WAN_INTERFACE=""
LAN_CIDR=""
BUILD_PROXY=""
BUILD_MODE="local"
TUN_DEVICE="mihomua"
MIXED_PORT="1080"
CONTROLLER_PORT="1081"
WEB_PORT="1082"
IMAGE_TAG="v1"

SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
readonly SCRIPT_DIR
readonly RULES_TEMPLATE="$SCRIPT_DIR/../include.yaml"
readonly RULES_TEMPLATE_URL="https://raw.githubusercontent.com/sparkuru/genshin/refs/heads/main/tsuki/07-mihomo/include.yaml"
readonly IMAGE_NAME="mihomua:$IMAGE_TAG"
readonly BYPASS_IMAGE_NAME="mihomua-bypass:$IMAGE_TAG"

force_deploy=false
work_dir=""
image_archive=""
ssh_options=()
ssh_auth_mode="key"
ssh_password="$REMOTE_PASSWORD"

die() {
	printf 'Error: %s\n' "$*" >&2
	exit 1
}

info() {
	printf '%s\n' "$*"
}

usage() {
	printf 'Usage: %s [--force]\n' "$(basename -- "$0")" >&2
	printf 'Edit the User configuration block before running this script.\n' >&2
}

require_command() {
	command -v "$1" >/dev/null 2>&1 || die "required command not found: $1"
}

validate_value() {
	local value=$1
	local name=$2
	local pattern=$3

	[[ "$value" =~ $pattern ]] || die "invalid $name"
}

validate_configuration() {
	[[ -n "$REMOTE_HOST" ]] || die "REMOTE_HOST must be configured"
	[[ -n "$SUBSCRIPTION_URL" ]] || die "SUBSCRIPTION_URL must be configured"
	[[ -n "$WAN_INTERFACE" ]] || die "WAN_INTERFACE must be configured"
	[[ -n "$LAN_CIDR" ]] || die "LAN_CIDR must be configured"
	[[ -n "$BUILD_PROXY" ]] || die "BUILD_PROXY must be configured"
	[[ -f "$RULES_TEMPLATE" || -n "$RULES_TEMPLATE_URL" ]] || die "no rules template source is configured"
	[[ "$REMOTE_DEPLOY_DIR" == /* ]] || die "REMOTE_DEPLOY_DIR must be absolute"
	[[ "$SUBSCRIPTION_URL" != *"'"* ]] || die "SUBSCRIPTION_URL must not contain a single quote"
	validate_value "$REMOTE_HOST" "REMOTE_HOST" '^[A-Za-z0-9._:-]+$'
	validate_value "$REMOTE_USER" "REMOTE_USER" '^[A-Za-z0-9._-]+$'
	validate_value "$REMOTE_PORT" "REMOTE_PORT" '^[0-9]+$'
	validate_value "$REMOTE_DEPLOY_DIR" "REMOTE_DEPLOY_DIR" '^/[A-Za-z0-9._/-]+$'
	validate_value "$WAN_INTERFACE" "WAN_INTERFACE" '^[A-Za-z0-9_.:-]+$'
	validate_value "$TUN_DEVICE" "TUN_DEVICE" '^[A-Za-z0-9_.:-]+$'
	validate_value "$MIXED_PORT" "MIXED_PORT" '^[0-9]+$'
	validate_value "$CONTROLLER_PORT" "CONTROLLER_PORT" '^[0-9]+$'
	validate_value "$WEB_PORT" "WEB_PORT" '^[0-9]+$'
	[[ "$BUILD_MODE" == "local" || "$BUILD_MODE" == "remote" ]] || die "BUILD_MODE must be local or remote"
	[[ -z "$RULES_TEMPLATE_URL" || "$RULES_TEMPLATE_URL" =~ ^https:// ]] || die "RULES_TEMPLATE_URL must use HTTPS"
}

cleanup() {
	[[ -z "$image_archive" || ! -f "$image_archive" ]] || rm -f -- "$image_archive"
	[[ -z "$work_dir" || ! -d "$work_dir" ]] || rm -rf -- "$work_dir"
	unset ssh_password
}

configure_ssh() {
	ssh_options=(-p "$REMOTE_PORT" -o StrictHostKeyChecking=accept-new -o ConnectTimeout=15)
	if [[ -n "$SSH_IDENTITY_FILE" ]]; then
		[[ -f "$SSH_IDENTITY_FILE" ]] || die "SSH identity file not found: $SSH_IDENTITY_FILE"
		ssh_options+=(-i "$SSH_IDENTITY_FILE")
	fi
}

remote() {
	# shellcheck disable=SC2029  # Callers intentionally pass an already-quoted remote command.
	if [[ "$ssh_auth_mode" == "password" ]]; then
		SSHPASS="$ssh_password" sshpass -e ssh "${ssh_options[@]}" "$REMOTE_USER@$REMOTE_HOST" "$@"
	else
		ssh "${ssh_options[@]}" "$REMOTE_USER@$REMOTE_HOST" "$@"
	fi
}

copy_to_remote() {
	if [[ "$ssh_auth_mode" == "password" ]]; then
		SSHPASS="$ssh_password" sshpass -e scp "${ssh_options[@]}" "$@"
	else
		scp "${ssh_options[@]}" "$@"
	fi
}

authenticate_ssh() {
	if ssh "${ssh_options[@]}" -o BatchMode=yes -o PreferredAuthentications=publickey -o PasswordAuthentication=no "$REMOTE_USER@$REMOTE_HOST" true >/dev/null 2>&1; then
		info "SSH key authentication available"
		return 0
	fi

	require_command sshpass
	[[ -t 0 ]] || die "password authentication requires an interactive terminal"
	read -r -s -p "SSH password for $REMOTE_USER@$REMOTE_HOST: " ssh_password
	printf '\n' >&2
	[[ -n "$ssh_password" ]] || die "SSH password must not be empty"
	if SSHPASS="$ssh_password" sshpass -e ssh "${ssh_options[@]}" "$REMOTE_USER@$REMOTE_HOST" true >/dev/null; then
		ssh_auth_mode="password"
		info "SSH password authentication available"
		return 0
	fi

	die "SSH authentication failed"
}

prepare_worktree() {
	local rules_template_path

	work_dir=$(mktemp -d "${TMPDIR:-/tmp}/mihomua-deploy.XXXXXXXXXX")
	cp -a -- "$SCRIPT_DIR/." "$work_dir/"
	rules_template_path="$work_dir/config/include.yaml"
	if [[ -f "$RULES_TEMPLATE" ]]; then
		info "Using local rules template: $RULES_TEMPLATE"
		cp -- "$RULES_TEMPLATE" "$rules_template_path"
	else
		info "Downloading rules template"
		curl -fsSL --proto '=https' --tlsv1.2 "$RULES_TEMPLATE_URL" -o "$rules_template_path"
	fi
	test -s "$rules_template_path" || die "rules template is empty"
	sed -i -e 's#FROM docker.io/node:alpine AS web_builder#FROM docker.io/node:22-alpine AS web_builder#' -e 's#/build/dist/.#/build/packages/ui/.output/public/.#' "$work_dir/dockerfile"
	grep -q 'node:22-alpine' "$work_dir/dockerfile" || die "failed to update Node image"
	grep -q 'packages/ui/.output/public' "$work_dir/dockerfile" || die "failed to update web output path"
	awk -v "subscription_url=$SUBSCRIPTION_URL" -v "lan_cidr=$LAN_CIDR" '
        /^  - 10\.172\.0\.0\/16$/ { print; print "  - " lan_cidr; next }
        /^proxy-groups:/ {
            print "proxy-providers:"
            print "  subscription:"
            print "    type: http"
            print "    url: '\''" subscription_url "'\''"
            print "    path: /root/.config/mihomo/providers/subscription.yaml"
            print "    interval: 3600"
            print "    health-check:"
            print "      enable: true"
            print "      url: https://www.gstatic.com/generate_204"
            print "      interval: 300"
        }
        { print }
	' "$rules_template_path" | awk '
        /^rules:/ {
            print "  - name: ip"
            print "    type: select"
            print "    proxies:"
            print "      - DIRECT"
            print "      - outside"
        }
        /^  - name: / {
            if (selected) { print "    use:"; print "      - subscription"; selected = 0 }
            if ($0 ~ /name: outside/ || $0 ~ /name: llm/) { selected = 1 }
        }
        { print }
        END { if (selected) { print "    use:"; print "      - subscription" } }
    ' >"$work_dir/config/config.yaml"
	grep -q '^proxy-providers:$' "$work_dir/config/config.yaml" || die "failed to add subscription provider"
	grep -q '^  - name: ip$' "$work_dir/config/config.yaml" || die "failed to add ip group"
	grep -q "  - $LAN_CIDR" "$work_dir/config/config.yaml" || die "failed to add LAN exclusion"
	sed -i -e "s/^  device: .*/  device: $TUN_DEVICE/" -e "s/^port: .*/port: $MIXED_PORT/" -e "s#^external-controller: .*#external-controller: 0.0.0.0:$CONTROLLER_PORT#" "$work_dir/config/config.yaml"
	sed -i -e "s/- WEB_PORT=.*/- WEB_PORT=$WEB_PORT/" -e "s/WAN_IFACE=vmbr0/WAN_IFACE=$WAN_INTERFACE/" -e "s/TUN_IFACE=segfault/TUN_IFACE=$TUN_DEVICE/" "$work_dir/mihomua.yaml"
	sed -i "/- TZ=Asia\\/Shanghai/a\\      - HTTP_PROXY=$BUILD_PROXY\\n      - HTTPS_PROXY=$BUILD_PROXY\\n      - NO_PROXY=localhost,127.0.0.1,::1" "$work_dir/mihomua.yaml"
	chmod 0600 -- "$work_dir/config/config.yaml" "$work_dir/config/include.yaml"
	install -d -m 0700 -- "$work_dir/config/providers"
	printf 'config\ncache.db\ninclude.yaml\nproviders\n' >"$work_dir/.dockerignore"
}

build_images_locally() {
	info "Building images locally"
	docker build -t "$BYPASS_IMAGE_NAME" "$work_dir/bypass"
	docker build -t "$IMAGE_NAME" "$work_dir"
	image_archive=$(mktemp "${TMPDIR:-/tmp}/mihomua-images.XXXXXXXXXX.tar")
	docker save -o "$image_archive" "$IMAGE_NAME" "$BYPASS_IMAGE_NAME"
	sha256sum "$image_archive"
}

prepare_remote_directory() {
	local force_flag=0
	[[ "$force_deploy" == true ]] && force_flag=1
	remote "set -eu; if [ -e '$REMOTE_DEPLOY_DIR' ]; then [ '$force_flag' -eq 1 ] || { printf '%s\\n' 'deployment exists; rerun with --force' >&2; exit 1; }; if [ -f '$REMOTE_DEPLOY_DIR/mihomua.yaml' ]; then (cd '$REMOTE_DEPLOY_DIR' && docker compose -f mihomua.yaml down) || true; fi; stamp=\$(date -u +%Y%m%dT%H%M%SZ); install -d -m 0700 '$REMOTE_DEPLOY_DIR/backups/'\"\$stamp\"; [ ! -d '$REMOTE_DEPLOY_DIR/config' ] || cp -a '$REMOTE_DEPLOY_DIR/config' '$REMOTE_DEPLOY_DIR/backups/'\"\$stamp\"/config; else install -d -m 0750 '$REMOTE_DEPLOY_DIR'; fi"
}

upload_worktree() {
	info "Uploading deployment"
	copy_to_remote -r "$work_dir/." "$REMOTE_USER@$REMOTE_HOST:$REMOTE_DEPLOY_DIR/"
}

transfer_local_images() {
	info "Uploading local images"
	copy_to_remote "$image_archive" "$REMOTE_USER@$REMOTE_HOST:/tmp/mihomua-images.tar"
	remote "set -eu; docker load -i /tmp/mihomua-images.tar; rm -f /tmp/mihomua-images.tar; chmod 0600 '$REMOTE_DEPLOY_DIR/config/config.yaml' '$REMOTE_DEPLOY_DIR/config/include.yaml'"
}

build_images_remotely() {
	info "Building images on the target"
	remote "set -eu; cd '$REMOTE_DEPLOY_DIR'; DOCKER_BUILDKIT=0 docker build --network host --build-arg HTTP_PROXY='$BUILD_PROXY' --build-arg HTTPS_PROXY='$BUILD_PROXY' --build-arg NO_PROXY=localhost,127.0.0.1,::1 -t '$BYPASS_IMAGE_NAME' bypass; DOCKER_BUILDKIT=0 docker build --network host --build-arg HTTP_PROXY='$BUILD_PROXY' --build-arg HTTPS_PROXY='$BUILD_PROXY' --build-arg NO_PROXY=localhost,127.0.0.1,::1 -t '$IMAGE_NAME' .; chmod 0600 config/config.yaml config/include.yaml"
}

prepare_geodata() {
	remote "set -eu; curl -fsSL --proxy '$BUILD_PROXY' --connect-timeout 15 --max-time 120 https://testingcf.jsdelivr.net/gh/MetaCubeX/meta-rules-dat@release/country.mmdb -o '$REMOTE_DEPLOY_DIR/config/Country.mmdb'; chmod 0600 '$REMOTE_DEPLOY_DIR/config/Country.mmdb'"
}

validate_remote_config() {
	info "Validating target configuration"
	remote "set -eu; docker run --rm --network host -e HTTP_PROXY='$BUILD_PROXY' -e HTTPS_PROXY='$BUILD_PROXY' -e NO_PROXY=localhost,127.0.0.1,::1 -v '$REMOTE_DEPLOY_DIR/config:/root/.config/mihomo' --entrypoint /srv/mihomo '$IMAGE_NAME' -t; cd '$REMOTE_DEPLOY_DIR'; docker compose -f mihomua.yaml config -q"
}

start_and_verify() {
	info "Starting Mihomua"
	remote "set -eu; cd '$REMOTE_DEPLOY_DIR'; docker compose -f mihomua.yaml up -d --no-build; sleep 5; docker compose -f mihomua.yaml ps; test -d /sys/class/net/'$TUN_DEVICE'; ip rule show | grep -q '9002:'; ip rule show | grep -q '8500:'; test -s '$REMOTE_DEPLOY_DIR/config/providers/subscription.yaml'; secret=\$(grep '^secret:' '$REMOTE_DEPLOY_DIR/config/config.yaml' | cut -d '\"' -f2); test -n \"\$secret\"; curl -fsS -o /dev/null -H \"Authorization: Bearer \$secret\" http://127.0.0.1:$CONTROLLER_PORT/providers/proxies; printf '%s\\n' 'Mihomua deployment verified'"
}

main() {
	while [[ $# -gt 0 ]]; do
		case "$1" in
		--force) force_deploy=true ;;
		--help | -h)
			usage
			return 0
			;;
		*) die "unknown option: $1" ;;
		esac
		shift
	done
	require_command awk
	require_command cp
	require_command curl
	require_command scp
	require_command sed
	require_command sha256sum
	require_command ssh
	validate_configuration
	configure_ssh
	trap cleanup EXIT
	authenticate_ssh
	if [[ "$BUILD_MODE" == "local" ]]; then
		require_command docker
	fi
	remote true
	prepare_worktree
	prepare_remote_directory
	if [[ "$BUILD_MODE" == "local" ]]; then
		build_images_locally
		upload_worktree
		transfer_local_images
	else
		upload_worktree
		build_images_remotely
	fi
	prepare_geodata
	validate_remote_config
	start_and_verify
	info "Deployment completed: http://$REMOTE_HOST:$WEB_PORT"
}

main "$@"
