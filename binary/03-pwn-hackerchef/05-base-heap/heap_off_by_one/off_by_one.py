# -*- coding: utf -*-

from pwn import *
import pwn
context(arch = 'amd64', log_level = 'debug', os = 'linux')

p64 = pwn.p64

filePath = './off_by_one'
libcPath = '../libs/2.31/libc.so.6'

io = process(filePath)
elf = ELF(libcPath)

gdbscript = '''
b *off_by_one.c:102
b *off_by_one.c:132
'''

gdb.attach(io, gdbscript = gdbscript)

io.interactive()