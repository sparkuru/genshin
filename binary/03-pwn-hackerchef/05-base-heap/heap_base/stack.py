# -*- coding: utf-8 -*-

from pwn import *
import pwn

p64 = pwn.p64

filename = './heap_base/stack'
io = process(filename)

gdbscript = '''
b *main+63
'''

gdb.attach(io, gdbscript=gdbscript)

payload = p64(0xdeadbeef)
# io.sendlineafter(b'input your overflow chain: \n', payload)

io.interactive()