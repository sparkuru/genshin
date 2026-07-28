#!/usr/bin/env bash
set -Eeuo pipefail

# Docker owns docker0; this script only grants QEMU's helper permission to
# attach a TAP and never changes Docker's network configuration.
readonly BRIDGE_NAME=docker0
readonly HELPER_PATH=/usr/lib/qemu/qemu-bridge-helper
readonly CONFIG_DIR=/etc/qemu
readonly CONFIG_PATH="$CONFIG_DIR/bridge.conf"

die() {
	printf 'Error: %s\n' "$*" >&2
	exit 1
}

main() {
	[[ ${EUID} -eq 0 ]] || die "run this setup script as root"
	[[ -x "$HELPER_PATH" ]] || die "QEMU bridge helper not found: $HELPER_PATH"

	install -d -m 0755 "$CONFIG_DIR"
	if [[ ! -f "$CONFIG_PATH" ]] || ! grep -Fxq "allow $BRIDGE_NAME" "$CONFIG_PATH"; then
		local temp_file
		temp_file=$(mktemp "$CONFIG_DIR/bridge.conf.XXXXXXXX")
		trap 'rm -f -- "${temp_file:-}"' EXIT
		[[ -f "$CONFIG_PATH" ]] && cat "$CONFIG_PATH" >"$temp_file"
		printf 'allow %s\n' "$BRIDGE_NAME" >>"$temp_file"
		install -o root -g root -m 0644 "$temp_file" "$CONFIG_PATH"
	fi

	chown root:root "$HELPER_PATH"
	chmod 4755 "$HELPER_PATH"
	printf 'QEMU bridge helper configured for %s.\n' "$BRIDGE_NAME"
}

main "$@"
