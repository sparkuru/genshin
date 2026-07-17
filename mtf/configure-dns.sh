#!/bin/bash

DEFAULT_DNS_SERVERS="223.5.5.5 1.1.1.1"
DNS_CONFIG_NAME="${DNS_CONFIG_NAME:-init-dpkg-dns}"
DNS_SERVERS="${DNS_SERVERS:-$DEFAULT_DNS_SERVERS}"
readonly STYLE_RESET=$'\033[0m'
readonly STYLE_PROGRESS=$'\033[1;36m'
readonly STYLE_SUCCESS=$'\033[1;32m'
readonly STYLE_DETECTED=$'\033[1;33m'

usage() {
	printf 'Usage: %s [--dns "SERVER ..."]\n' "$0"
	printf 'Default DNS servers: %s\n' "$DEFAULT_DNS_SERVERS"
}

die() {
	printf 'Error: %s\n' "$*" >&2
	exit 1
}

progress() {
	if [[ -n "${NO_COLOR:-}" || ! -t 1 ]]; then
		printf '\n==> %s\n' "$*"
		return 0
	fi
	printf '\n%s==> %s%s\n' "$STYLE_PROGRESS" "$*" "$STYLE_RESET"
}

success() {
	if [[ -n "${NO_COLOR:-}" || ! -t 1 ]]; then
		printf '==> %s\n' "$*"
		return 0
	fi
	printf '%s==> %s%s\n' "$STYLE_SUCCESS" "$*" "$STYLE_RESET"
}

status() {
	local style="$1"
	local label="$2"
	shift 2

	if [[ -n "${NO_COLOR:-}" || ! -t 1 ]]; then
		printf '%s: %s\n' "$label" "$*"
		return 0
	fi
	printf '%s%s: %s%s\n' "$style" "$label" "$*" "$STYLE_RESET"
}

detected() {
	status "$STYLE_DETECTED" "Detected" "$*"
}

updated() {
	status "$STYLE_SUCCESS" "Updated" "$*"
}

update_managed_block() {
	local file_path="$1"
	local begin_marker="$2"
	local end_marker="$3"
	local temp_file
	shift 3

	temp_file=$(mktemp)
	if [[ -f "$file_path" ]]; then
		sed "\\|^${begin_marker}$|,\\|^${end_marker}$|d" "$file_path" >"$temp_file"
	fi
	printf '%s\n' "$begin_marker" "$@" "$end_marker" >>"$temp_file"
	install -D -m 0644 -o root -g root "$temp_file" "$file_path"
	rm -f -- "$temp_file"
	updated "DNS configuration file: $file_path"
}

write_static_resolv_conf() {
	local resolv_conf="/etc/resolv.conf"
	local backup_file="/etc/resolv.conf.${DNS_CONFIG_NAME}.bak"
	local temp_file

	temp_file=$(mktemp)
	for dns_server in "${DNS_SERVER_LIST[@]}"; do
		printf 'nameserver %s\n' "$dns_server" >>"$temp_file"
	done
	printf '%s\n' 'options timeout:2 attempts:3' >>"$temp_file"

	if [[ ! -e "$backup_file" && (-e "$resolv_conf" || -L "$resolv_conf") ]]; then
		cp -a -- "$resolv_conf" "$backup_file"
	fi
	[[ ! -L "$resolv_conf" ]] || rm -f -- "$resolv_conf"
	install -m 0644 -o root -g root "$temp_file" "$resolv_conf"
	rm -f -- "$temp_file"
	updated "DNS resolver file: $resolv_conf"
}

configure_openresolv_dns() {
	command -v resolvconf >/dev/null 2>&1 || return 1
	resolvconf -v 2>&1 | grep -qi 'openresolv' || return 1

	detected "DNS manager: openresolv"
	progress "Configuring DNS through openresolv"
	update_managed_block "/etc/resolvconf.conf" "# BEGIN ${DNS_CONFIG_NAME}" "# END ${DNS_CONFIG_NAME}" \
		"name_servers=\"$DNS_SERVERS_SPACE\"" \
		'resolv_conf_passthrough=/dev/null' \
		'resolv_conf_options="timeout:2 attempts:3"'
	resolvconf -u
}

configure_debian_resolvconf_dns() {
	local config_dir="/etc/resolvconf/resolv.conf.d"
	local head_file="$config_dir/head"

	command -v resolvconf >/dev/null 2>&1 || return 1
	[[ -d "$config_dir" ]] || return 1
	detected "DNS manager: Debian resolvconf"
	progress "Configuring DNS through Debian resolvconf"
	update_managed_block "$head_file" "# BEGIN ${DNS_CONFIG_NAME}" "# END ${DNS_CONFIG_NAME}" \
		"$(printf 'nameserver %s\n' "${DNS_SERVER_LIST[@]}")" \
		'options timeout:2 attempts:3'
	resolvconf -u
	write_static_resolv_conf
}

configure_networkmanager_dns() {
	local config_file="/etc/NetworkManager/conf.d/90-${DNS_CONFIG_NAME}.conf"

	command -v nmcli >/dev/null 2>&1 || return 1
	detected "DNS manager: NetworkManager"
	progress "Configuring DNS through NetworkManager"
	mkdir -p /etc/NetworkManager/conf.d
	cat >"$config_file" <<EOF
[global-dns]
options=timeout:2,attempts:3

[global-dns-domain-*]
servers=$DNS_SERVERS_COMMA
EOF
	systemctl reload NetworkManager || return 1
	updated "DNS configuration file: $config_file"
}

netplan_section_ids() {
	local section_name="$1"

	netplan get "network.${section_name}" 2>/dev/null | awk -F: '/^[[:alnum:]_.-]+:$/ {print $1}'
}

restore_netplan_dns_config() {
	local config_file="$1"
	local backup_file="$2"

	if [[ -n "$backup_file" ]]; then
		mv -- "$backup_file" "$config_file"
	else
		rm -f -- "$config_file"
	fi
}

configure_netplan_dns() {
	local config_name="90-${DNS_CONFIG_NAME}"
	local config_file="/etc/netplan/${config_name}.yaml"
	local backup_file=""
	local device_type
	local device_id
	local configured=0

	command -v netplan >/dev/null 2>&1 || return 1
	compgen -G '/etc/netplan/*.yaml' >/dev/null || return 1
	detected "DNS configuration: Netplan"
	progress "Configuring DNS through Netplan"
	if [[ -e "$config_file" ]]; then
		backup_file=$(mktemp)
		cp -a -- "$config_file" "$backup_file"
	fi

	for device_type in ethernets wifis bridges bonds vlans; do
		while IFS= read -r device_id; do
			[[ -n "$device_id" ]] || continue
			if ! netplan set --origin-hint "$config_name" "network.${device_type}.${device_id}.nameservers.addresses=[${DNS_SERVERS_COMMA}]"; then
				restore_netplan_dns_config "$config_file" "$backup_file"
				return 1
			fi
			if ! netplan set --origin-hint "$config_name" "network.${device_type}.${device_id}.dhcp4-overrides.use-dns=false"; then
				restore_netplan_dns_config "$config_file" "$backup_file"
				return 1
			fi
			if ! netplan set --origin-hint "$config_name" "network.${device_type}.${device_id}.dhcp6-overrides.use-dns=false"; then
				restore_netplan_dns_config "$config_file" "$backup_file"
				return 1
			fi
			configured=1
		done < <(netplan_section_ids "$device_type")
	done

	if ((!configured)); then
		restore_netplan_dns_config "$config_file" "$backup_file"
		return 1
	fi
	if ! netplan generate; then
		restore_netplan_dns_config "$config_file" "$backup_file"
		return 1
	fi
	[[ -z "$backup_file" ]] || rm -f -- "$backup_file"
	netplan apply || return 1
	updated "Netplan DNS configuration: $config_file"
}

configure_systemd_resolved_dns() {
	local config_file="/etc/systemd/resolved.conf.d/90-${DNS_CONFIG_NAME}.conf"

	command -v resolvectl >/dev/null 2>&1 || return 1
	detected "DNS manager: systemd-resolved"
	progress "Configuring DNS through systemd-resolved"
	mkdir -p /etc/systemd/resolved.conf.d
	cat >"$config_file" <<EOF
[Resolve]
DNS=$DNS_SERVERS_SPACE
FallbackDNS=
Domains=~.
EOF
	systemctl restart systemd-resolved || return 1
	updated "DNS configuration file: $config_file"
}

configure_ifupdown_dns() {
	[[ -f /etc/network/interfaces || -d /etc/network/interfaces.d ]] || return 1

	detected "DNS configuration: ifupdown"
	progress "Configuring DNS through ifupdown"
	update_managed_block "/etc/dhcp/dhclient.conf" "# BEGIN ${DNS_CONFIG_NAME}" "# END ${DNS_CONFIG_NAME}" \
		"supersede domain-name-servers ${DNS_SERVERS_COMMA};"
	if [[ -f /etc/dhcpcd.conf ]] || command -v dhcpcd >/dev/null 2>&1; then
		update_managed_block "/etc/dhcpcd.conf" "# BEGIN ${DNS_CONFIG_NAME}" "# END ${DNS_CONFIG_NAME}" \
			"static domain_name_servers=${DNS_SERVERS_SPACE}"
	fi
	write_static_resolv_conf
}

configure_dns() {
	progress "Detecting a supported DNS manager"
	if configure_netplan_dns; then
		if systemctl is-active --quiet NetworkManager; then
			configure_networkmanager_dns || return 1
		fi
		if systemctl is-active --quiet systemd-resolved; then
			configure_systemd_resolved_dns || return 1
		fi
		return 0
	fi
	if systemctl is-active --quiet NetworkManager && configure_networkmanager_dns; then
		return 0
	fi
	if systemctl is-active --quiet systemd-resolved && configure_systemd_resolved_dns; then
		return 0
	fi
	if configure_openresolv_dns; then
		return 0
	fi
	if configure_debian_resolvconf_dns; then
		return 0
	fi
	if configure_ifupdown_dns; then
		return 0
	fi
	die "no supported DNS manager was detected"
}

main() {
	while [[ $# -gt 0 ]]; do
		case "$1" in
		--dns)
			[[ $# -ge 2 ]] || die "--dns requires one or more IP addresses"
			DNS_SERVERS="$2"
			shift 2
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
	if [ "$(id -u)" -ne 0 ]; then
		die "rerun $0 with root user permission"
	fi

	[[ "$DNS_CONFIG_NAME" =~ ^[[:alnum:]][[:alnum:]_.-]*$ ]] || die "DNS_CONFIG_NAME contains unsupported characters"
	read -r -a DNS_SERVER_LIST <<<"$DNS_SERVERS"
	[[ ${#DNS_SERVER_LIST[@]} -gt 0 ]] || die "at least one DNS server is required"
	for dns_server in "${DNS_SERVER_LIST[@]}"; do
		[[ "$dns_server" =~ ^[0-9A-Fa-f:.]+$ ]] || die "DNS servers must be IPv4 or IPv6 addresses"
	done
	DNS_SERVERS_SPACE="${DNS_SERVER_LIST[*]}"
	DNS_SERVERS_COMMA=$(
		IFS=,
		printf '%s' "${DNS_SERVER_LIST[*]}"
	)

	progress "Preparing DNS configuration for: $DNS_SERVERS"
	configure_dns
	success "DNS configuration completed"
}

main "$@"
