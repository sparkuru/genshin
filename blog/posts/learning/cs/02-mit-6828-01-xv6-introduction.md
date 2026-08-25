---
title: "course-operating-system | 6.828-chapter01"
description: "operating system engineering; mit 6.828; chapter01; lab1."
date: "2023-07-02T01:00:00.000Z"
updated: "2024-12-12T03:26:38.000Z"
tags: []
draft: false
layout: "post"
slug: "mit-6828-01-xv6-introduction"
---

## chapter01

关联目录：`6.828\labs\lab1`，

## lecture01-overview

### 01. goals

mit 6.828 课程目标：

1.   了解操作系统的设计和实现

2.   亲自实践构造一个小型的 O/S 系统

     对于该小型操作系统，设计需求（也是 OS 要实现的设计需求）如下

     1.   能够支持运行应用程序
     2.   Abstract the hardware for convenience and portability；将硬件抽象后使之变得便利和方便，即采用封装的思想，将硬件底层屏蔽，只提供接口
     3.   在多应用的情况下实现硬件间的通信
     4.   隔离应用以防止 bug 出现，即可以实现 debug
     5.   实现应用间的共享
     6.   高效能

     课程会在课上对一个已经比较成熟的教学用操作系统内核 xv6 进行讲解，然后在 labs 中手动实现自制的操作系统内核 JOS，这是一种 x86 架构下的外核（exokernel）结构

     **以下内容暂时不知道如何描述，待补充**

     1.   you build it, 5 labs + final lab of your choice
     2.   kernel interface: expose hardware, but protect -- few abstractions!
     3.   unprivileged user-level library: fork, exec, pipe, ...
     4.   applications: file system, shell, ..
     5.   development environment: gcc, qemu
     6.   lab 1 is out

### 02. ez-introduction

1.   计算机系统的组成：
     1.   硬件层；h/w，hardware，即 cpu、disk、mem 等
     2.   操作系统层；kernel，操作系统内核
     3.   用户层；应用程序
2.   一个典型的操作系统**内核**应该提供的服务：
     1.   进程管理
     2.   内存管理，存储器资源管理
     3.   文件管理；file contents，directories and file names
     4.   安全要求

### 03. system calls

一个系统调用的例子：基本 I/O，Input and Output

给出一个使用 c 语言编写的示例 `io.c` 如下：

```c
# include <stdio.h>
# include <stdlib.h>

int main () {
    char buf[20];
    read(0x0, buf, sizeof(buf));
    write(0x1, buf, 4);
    return 0;
}
```

使用 `gcc -o io io.c` 将其进行编译，得到可执行文件 `io`，输入 `./io` 运行该文件，可以得到输出如下：

```bash
deadbeef	# 输入
dead		# 输出
```

使用指令 `strace cmd`（macos 上是 `dtruss cmd`），这个指令可以用于跟踪指定的 `cmd` 使用到的系统调用信息，`strace ./io`，可以发现列出了很多与系统调用有关的函数，例如 `brk`，`close` 等

在这个示例中，`read(fd, ...)` 和 `write(fd, ...)` 中第一个参数名称为**文件标识符（file descriptor）**，其作用是告知 kernel 要对哪个文件进行操作，在 unix 类操作系统下，使用 0 当作标准输入，1 作标准输出。由此可以很明显得知，read 就是对标准输入进行操作，即从标准输入将 `deadbeef` 输入到 buf 中，write 同理。

这里的 `read` 和 `write` 函数就是一种系统调用，软件、程序通过**系统调用**来与 kernel 交互

## lab01

### getting started with x86 assembly

以下是贯穿整个课程的阅读参考资料：

1.   [Brennan's Guide to Inline Assembly](http://www.delorie.com/djgpp/doc/brennan/brennan_att_inline_djgpp.html)，将 Intel 汇编语法转换成 AT&T 汇编语法（本课程基于 GNU 汇编器，而 GNU 使用的是 AT&T 汇编语法）
2.   [80386 Programmer's Reference Manual](https://pdos.csail.mit.edu/6.828/2018/readings/i386/toc.htm)，涵盖且不仅限于本课程所有处理器知识点的手册，但是采用的是 Intel 语法，因此需要结合前面的语法转换手册来学习
3.   [IA-32 Intel Architecture Software Developer's Manuals](http://www.intel.com/content/www/us/en/processors/architectures-software-developer-manuals.html)，来自 Intel 的最新、最全的处理器参考资料，涵盖了处理器所有的功能，如果感兴趣，则可以用于学习之余的参考

### booting kernel

从公开页面的 lab 中获取 jos 的仓库：`git clone https://pdos.csail.mit.edu/6.828/2018/jos.git lab1`，对于整个实验环境，官网是这么说的：

>   If you are working on a non-Athena machine, you'll need to install `qemu` and possibly `gcc` following the directions on the [tools page](https://pdos.csail.mit.edu/6.828/2018/tools.html). We've made several useful debugging changes to `qemu` and some of the later labs depend on these patches, so you must build your own. If your machine uses a native ELF toolchain (such as Linux and most BSD's, but notably *not* OS X), you can simply install `gcc` from your package manager. Otherwise, follow the directions on the tools page.

1.   首先安装一些必要系统环境组件

     ```bash
     sudo apt-get install libglib2.0-dev libpixman-1-dev gcc-multilib build-essential gdb
     ```

2.   模拟器环境，emulator；在这边提到了 `qemu` 的概念，其可以类比于 vmware 这类虚拟平台，即一种模拟器解决方案，整个课程需要使用到 [QEMU Emulator](https://www.qemu.org/)，**这里需要使用课程魔改的版本**：

     1.   `git clone https://github.com/mit-pdos/6.828-qemu.git qemu-src`

     2.   `cd qemu-src`，`./configure --disable-kvm --disable-werror --prefix=[目标安装路径] --target-list="i386-softmmu x86_64-softmmu"`，其中的目标安装路径以 `6.828/labs/qemu` 为例

     3.   `make`，`make install`；

          如果出现 `python 2.4 later...` 的错误，需要为系统选择 python2 作为 python 的默认路径：`sudo update-alternatives --install /usr/bin/python python /usr/bin/python2 1`，后续要改回 python3 作为 python 默认路径：`sudo update-alternatives --install /usr/bin/python python /usr/bin/python3 2`；末尾的那个 1，2 数字越大，表明优先级越高

     4.   为 qemu 添加系统路径支持 `sudo ln -s 6.828/labs/qemu/bin/qemu-system-i386 /usr/bin/qemu`

     5.   检查是否编译成功并添加软链接：`qemu --version`

     提供一个自己编译的版本：[qemu-6.828-patched-binary.tar.gz](https://pan.baidu.com/s/1KTo8cLCaEu6LTSAF_FP6JA?pwd=pign)，md5：`0af0068a6434d44c4daef386edcffb17`，使用的编译平台：`GNU Make 4.3`，系统版本：`Linux kali 5.16.0-kali7-amd64 #1 SMP PREEMPT Debian 5.16.18-1kali1 (2022-04-01) x86_64 GNU/Linux`

2.   工具集，toolchain；这里提到，需要从他们的 [tools page](https://pdos.csail.mit.edu/6.828/2018/tools.html) 中获取到相关的工具集，即在本机（使用 Unix 类操作系统）上检查相关 toolchain 是否完备：
     1.   `objdump -i`，在打印出的信息中，第二行出现 `elf32-i386` 的信息即可
     2.   `gcc -m32 -print-libgcc-file-name`，回显出一行例如 `/usr/lib/gcc/x86_64-linux-gnu/12/32/libgcc.a` 的内容即可；

在确保以上环境能正常运转的情况下，则可以开始尝试 boot the kernel：

1.   `cd lab1`，`make`；
     
     1.   如果出现了 `__udivdi3` 类错误，代表系统中没有有效的 32 位运行支持库，需要运行 `sudo apt-get install gcc-multilib` 来安装
     2.   出现 `[-Werror]` 错误，需要在 `lab1/GNUmakefile` 文件中，第 93 行左右，添加一行内容 `CFLAGS += -Wno-error`
     
2.   `make qemu`；
     
     1.   此时就成功进入到了 qemu 的模拟环境，可以输入 `help` 指令查看信息；成功进入内核的回显信息如下：
     
          ```bash
          $ make qemu
          
          qemu -drive file=obj/kern/kernel.img,index=0,media=disk,format=raw -serial mon:stdio -gdb tcp::26000 -D qemu.log
          VNC server running on `::1:5900'
          6828 decimal is XXX octal!
          entering test_backtrace 5
          entering test_backtrace 4
          entering test_backtrace 3
          entering test_backtrace 2
          entering test_backtrace 1
          entering test_backtrace 0
          leaving test_backtrace 0
          leaving test_backtrace 1
          leaving test_backtrace 2
          leaving test_backtrace 3
          leaving test_backtrace 4
          leaving test_backtrace 5
          Welcome to the JOS kernel monitor!
          Type 'help' for a list of commands.
          
          K> help	# 打印帮助列表
          help - Display this list of commands
          kerninfo - Display information about the kernel
          
          K> kerninfo	# 查看内核信息
          Special kernel symbols:
            _start                  0010000c (phys)
            entry  f010000c (virt)  0010000c (phys)
            etext  f0101a1f (virt)  00101a1f (phys)
            edata  f0112060 (virt)  00112060 (phys)
            end    f01126c0 (virt)  001126c0 (phys)
          Kernel executable memory footprint: 74KB
          
          K>
          ```
     
     2.   要退出 qemu 模拟器，需要先输入 `ctrl + a`，随即输入 `x`
     
     3.   除了 `make qemu`，后续还有可能会接触到其他选项：
          1.   `make qemu`，最默认的手段使用 qemu 来启动内核，默认有图形化界面（不过该内核不包含图形化界面），图形化界面往往会占用更多的带宽资源
          1.   `make qemu-nox`，关闭图形化界面（更适合使用 ssh 连接来管理），在本 labs 示例中，有无图形化界面效果相同
          1.   `make qemu-gdb`，编译启动内核，但是会直接卡在第一条指令，并且等待 gdb 的连接；关于 gdb 的连接，需要另开一个 shell，在同目录下执行：`make gdb`，接下来就是使用 gdb 来对内核进行调试

### a pc's physical address space

早期使用的 16 位 8088 处理器，其只有 1MB 的寻址能力，使得早期的 pc 开始地址为 0x00000000，结束于 0x000FFFFF

\!\[图 1](E:\Pictures\markdown\image-20230703185935963.png)

### how pc start up



















### boot the xv6 kernel

还可以尝试编译执行课程提供的 xv6 内核

1.   获取源码，可以从课程提供的 [pdf](https://pdos.csail.mit.edu/6.828/2018/xv6/xv6-rev11.pdf) 文件编写代码，当然最直接的方式就是从课程仓库获取代码：`git clone https://github.com/mit-pdos/xv6-public.git ./xv6`
2.   安装环境依赖，参考前文 booting kernel 节配置的环境
3.   修改 xv6 的 makefile，在 `./xv6/Makefile` 的第 79 行左右，将 `CFLAGS = -fno-pic -static -fno-builtin -fno-strict-aliasing -O2 -Wall -MD -ggdb -m32 -Werror -fno-omit-frame-pointer`，修改成 `CFLAGS = -fno-pic -static -fno-builtin -fno-strict-aliasing -O2 -Wall -MD -ggdb -m32 -Wno-error -fno-omit-frame-pointer`，即把 `-Werror` 修改成 `-Wno-errer`
4.   编译，`make`
5.   使用 `Ctrl + a x` 退出模拟器

## differences between AT&T and Intel

| differences                     | AT&T                                                         | Intel                                                      |
| ------------------------------- | ------------------------------------------------------------ | ---------------------------------------------------------- |
| 寄存器（register）描述          | `%eax`                                                       | `eax`                                                      |
| 源操作数和目标操作数            | `movl %eax, %ebx`，left to right                             | `mov ebx, eax`，right to left                              |
| 立即数（immediate value）的表示 | `mov $foobar, %eax`，`mov $0x1, %eax`，使用符号 `$` 来表示立即数 | `mov eax, foobar`，`mov eax, 0x1`                          |
| 获取数据的 size 方式            | `movw %ax, %bx`，需要在操作指令中指明数据的大小，**b**yte、**w**ord、**l**ongword | `mov bx, ax`，使用 eax、ax、ah、al 来表示取得的数据的 size |
| 寻址方式，                      |                                                              |                                                            |
|                                 |                                                              |                                                            |
|                                 |                                                              |                                                            |
