#!/bin/bash
# Bypass mihomo's TUN auto-route for inbound DNAT replies.
# Inbound connections arriving on $WAN_IFACE from non-local sources get a fwmark;
# the mark rides on conntrack, so the reply path inherits it and routes via main
# (default route via the LAN router) instead of being swallowed by mihomo.

set -e

WAN_IFACE="${WAN_IFACE:-vmbr0}"
TUN_IFACE="${TUN_IFACE:-paimon}"
MARK="${MARK:-0x100/0x100}"
RULE_PREF="${RULE_PREF:-8500}"

IPT="iptables"   # via update-alternatives -> iptables-legacy

apply() {
  iptables -t mangle -C PREROUTING -j CONNMARK --restore-mark --nfmask 0x100 --ctmask 0x100 2>/dev/null \
    || iptables -t mangle -I PREROUTING 1 -j CONNMARK --restore-mark --nfmask 0x100 --ctmask 0x100

  iptables -t mangle -C PREROUTING -i "$WAN_IFACE" -m conntrack --ctstate NEW -m addrtype ! --src-type LOCAL -j MARK --set-xmark "$MARK" 2>/dev/null \
    || iptables -t mangle -A PREROUTING -i "$WAN_IFACE" -m conntrack --ctstate NEW -m addrtype ! --src-type LOCAL -j MARK --set-xmark "$MARK"

  iptables -t mangle -C PREROUTING -i "$WAN_IFACE" -m conntrack --ctstate NEW -m addrtype ! --src-type LOCAL -j CONNMARK --save-mark --nfmask 0x100 --ctmask 0x100 2>/dev/null \
    || iptables -t mangle -A PREROUTING -i "$WAN_IFACE" -m conntrack --ctstate NEW -m addrtype ! --src-type LOCAL -j CONNMARK --save-mark --nfmask 0x100 --ctmask 0x100

  ip rule show | grep -q "fwmark $MARK lookup main" \
    || ip rule add pref "$RULE_PREF" fwmark "$MARK" lookup main

  echo "[bypass] applied (iface=$WAN_IFACE mark=$MARK pref=$RULE_PREF)"
}

cleanup() {
  echo "[bypass] cleanup..."
  ip rule del pref "$RULE_PREF" fwmark "$MARK" lookup main 2>/dev/null || true
  iptables -t mangle -D PREROUTING -i "$WAN_IFACE" -m conntrack --ctstate NEW -m addrtype ! --src-type LOCAL -j CONNMARK --save-mark --nfmask 0x100 --ctmask 0x100 2>/dev/null || true
  iptables -t mangle -D PREROUTING -i "$WAN_IFACE" -m conntrack --ctstate NEW -m addrtype ! --src-type LOCAL -j MARK --set-xmark "$MARK" 2>/dev/null || true
  iptables -t mangle -D PREROUTING -j CONNMARK --restore-mark --nfmask 0x100 --ctmask 0x100 2>/dev/null || true
  echo "[bypass] cleaned"
  exit 0
}

trap cleanup INT TERM

i=0
while [ $i -lt 60 ]; do
  ip link show "$TUN_IFACE" >/dev/null 2>&1 && break
  i=$((i+1))
  sleep 1
done

apply

while :; do sleep 86400 & wait $!; done
