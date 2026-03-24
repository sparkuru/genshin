#!/usr/bin/env bash
set -euo pipefail

start_ssh() {
  ssh-keygen -A >/dev/null 2>&1 || true
  /usr/sbin/sshd
}

start_nginx() {
  nginx
}

start_ftp() {
  /usr/sbin/vsftpd /etc/vsftpd.conf &
}

start_telnet() {
  /usr/sbin/xinetd -stayalive -pidfile /var/run/xinetd.pid
}

if [[ "${ENABLE_SSH:-1}" == "1" ]]; then
  start_ssh
fi

if [[ "${ENABLE_NGINX:-1}" == "1" ]]; then
  start_nginx
fi

if [[ "${ENABLE_FTP:-0}" == "1" ]]; then
  start_ftp
fi

if [[ "${ENABLE_TELNET:-0}" == "1" ]]; then
  start_telnet
fi

echo "Service status:"
echo "  ENABLE_SSH=${ENABLE_SSH:-1}"
echo "  ENABLE_NGINX=${ENABLE_NGINX:-1}"
echo "  ENABLE_FTP=${ENABLE_FTP:-0}"
echo "  ENABLE_TELNET=${ENABLE_TELNET:-0}"
