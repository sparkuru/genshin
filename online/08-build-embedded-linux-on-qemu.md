# build embedded linux on qemu

base refer to [基于qemu从0开始构建嵌入式linux系统](https://quard-star-tutorial.readthedocs.io/zh-cn/latest/index.html) and [embedded linux qemu labs](https://bootlin.com/doc/training/embedded-linux-qemu/embedded-linux-qemu-labs.pdf)，目标是在 qemu 上构建自己的 embedded linux 系统，除此以外还会学习如何在 qemu 上完全模拟一块真实的开发板

## pre

build embedded linux system 所需的内容（例如 kernel、配置文件、rootfs 等）被上传在了

```bash
$ wget https://bootlin.com/doc/training/embedded-linux-qemu/embedded-linux-qemu-labs.tar.xz
$ tar xvf embedded-linux-qemu-labs.tar.xz
```

实验环境使用的是 kali，理论上采取任何 debian 系 linux 都能得到相同的步骤；除此以外，需要一个趁手的文本编辑工具，例如 Vim、Emacs、VSCode 等

以下是原文的其他贴心提示，我认为对于技术向学习是十分通用的一种思考、行为方式：

```markdown
## More guidelines

Can be useful throughout any of the labs

- Read instructions and tips carefully. Lots of people make mistakes or waste time because they missed an explanation or a guideline.

- Always read error messages carefully, in particular the first one which is issued. Some people stumble on very simple errors just because they specified a wrong file path and didn’t pay enough attention to the corresponding error message.

- Never stay stuck with a strange problem more than 5 minutes. Show your problem to your colleagues or to the instructor.

- You should only use the root user for operations that require super-user privileges, such as: mounting a file system, loading a kernel module, changing file ownership, configuring the network. Most regular tasks (such as downloading, extracting sources, compiling...) can be done as a regular user.

- If you ran commands from a root shell by mistake, your regular user may no longer be able to handle the corresponding generated files. In this case, use the chown -R command to give the new files back to your regular user. Example: `$ sudo chown -R myuser.myuser linux/`
```

## 01 build a cross-compiling toolchain

准备好必要的跨平台编译工具链用于编译不同架构的软件包

```bash
$ sudo apt update
$ sudo apt upgrade-dist
$ sudo apt install build-essential git autoconf bison flex texinfo help2man gawk libtool-bin libncurses5-dev unzip
```

下载并编译跨平台编译工具 Crosstool-ng，这是一个用于

```bash
$ git clone https://github.com/crosstool-ng/crosstool-ng
$ cd crosstool-ng

# 与 tutor 使用的版本一致
$ git checkout crosstool-ng-1.26.0

# make makefile
$ ./bootstrap
$ ./configure --enable-local
$ make
```

按照上述操作本地编译完成后，需要额外配置本地参数

```bash
```






## refer

1. [QQxiaoming/quard_star_tutorial](https://github.com/QQxiaoming/quard_star_tutorial.git)
2. [基于qemu从0开始构建嵌入式linux系统](https://quard-star-tutorial.readthedocs.io/zh-cn/latest/index.html)
3. [embedded linux qemu labs](https://bootlin.com/doc/training/embedded-linux-qemu/embedded-linux-qemu-labs.pdf)
4. https://bootlin.com