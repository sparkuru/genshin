# -*- coding: utf-8 -*-

from pwn import *
context(log_level = 'debug', os = 'linux')

filename = './heap31'

p = process(filename)
elf = ELF(filename)

gdbscript = '''
b heap31.c:29
b heap31.c:37
'''

gdb.attach(p, gdbscript = gdbscript)
p.interactive()