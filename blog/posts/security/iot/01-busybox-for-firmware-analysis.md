---
title: "iot-busybox"
description: "my busybox."
date: "2024-04-26T08:26:00.000Z"
updated: "2024-08-20T02:46:09.000Z"
tags: []
draft: false
layout: "post"
slug: "busybox-for-firmware-analysis"
---

## busybox

制作一个自己的 busybox ...

1.   init all the env
2.   some scripts with python embedded
3.   一些常用指令的整合 like cat、curl、ps、netstat（我觉得 python 写起来就很好，也没有那么必要注意那一点性能）
4.   a binary to auto init in a mips、arm、x86、
     1.   .bash_rc
5.   a binary to auto get pwn tools、reverse
     1.   ropgadget
     2.   split
     3.   objdump
6.   a binary to solve misc、crypto
     1.   yafu
     2.   cyberchef

## before

:wqa
