---
title: "penetration-john-the-ripper-hb"
description: "开源、跨平台的密码恢复、密码哈希分析工具 John The Ripper"
date: "2024-01-15T05:14:00.000Z"
updated: "2024-08-20T02:30:02.000Z"
tags: []
draft: false
layout: "post"
slug: "john-the-ripper-handbook"
---

## John The Ripper

>开源、跨平台的密码恢复、密码哈希分析工具 John The Ripper，kali 自带

Official document here：[Tool Documentation](https://www.kali.org/tools/john/)，install in kali：`sudo apt install john`，dictation file in `/usr/share/john/password.lst`

## question

>   拿到 /etc/passwd 和 /etc/shadow，john 批量破解

1.   结合密码文件：`unshadow PASSWORD-FILE SHADOW-FILE`

     ```bash
     $ cat /etc/passwd
     root:x:0:0:root:/root:/usr/bin/zsh
     
     $ cat /etc/shadow
     root:$1$$zdlNHiCDxYDfeF4MZL.H3/:19747:0:99999:7:::
     
     $ unshadow /etc/passwd /etc/shadow > unshadowed.txt
     
     $ cat unshadowed.txt
     root:$1$$zdlNHiCDxYDfeF4MZL.H3/:0:0:root:/root:/usr/bin/zsh
     ```

2.   默认规则破解 hash 值

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

1.   将有密码的 zip 文件导出：`zip2john test.zip > zip.hashes`
2.   破解密码：`john zip.hashes`

## end

最后附上 help 手册

## references

1.   [Cracking /etc/shadow with John](https://erev0s.com/blog/cracking-etcshadow-john/)
2.
