#!/usr/bin/env bash
set -Eeuo pipefail

readonly TELNET_PORT=${TELNET_PORT:-23}
readonly TELNET_USER=${TELNET_USER:-user}
readonly TELNET_PASS=${TELNET_PASS:-user}

main() {
    install -m 0644 /app/config/passwd.sample /etc/passwd

    echo "${TELNET_USER}:${TELNET_PASS}" | chpasswd

    if [ -f /etc/shadow ]; then
        sed -i 's|^root:[^:]*:|root:!*:|' /etc/shadow
    fi
    passwd -l root 2>/dev/null || true

    ln -sf /bin/busybox-full /bin/login

    install -m 0644 /app/config/profile /etc/profile
    install -m 0644 /app/config/issue /etc/issue
    install -m 0644 /app/config/issue /etc/issue.net
    install -m 0644 /app/config/motd /etc/motd

    echo "telnet listening on port ${TELNET_PORT} — login: ${TELNET_USER}"

    exec /bin/telnetd -F -f /etc/issue -p "$TELNET_PORT"
}

main "$@"