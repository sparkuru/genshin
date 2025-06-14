# binary-env-config

主要的作业流程迁移到了 kali for wsl 上来，对整个环境的配置重新写一篇文章，包含 pwntools 的配置、pwndbg 的配置与使用、tmux 的配置

目录拓扑如下：

```bash
.
├── glibc_all_in_one
│   ├── ...
│   ├── download
│   ├── libs
│   │   └── 2.27-3ubuntu1_amd64
│   ├── ...
│   └── update_list
└── pwndbg
    ├── plugins
    │   └── splitmind
    └── repo
        ├── ...
        ├── gdbinit.py
        ├── pwndbg
        ├── setup.sh
        └── ...
```

为了方便，下列全部使用 wkyuu 作为用户名，注意修改之

## pwntools

1.   基础必备环境：`sudo apt install curl aptitude`，`sudo aptitude install python3 python3-pip python3-venv python3-dev git libssl-dev libffi-dev build-essential gcc-multilib gdb-multiarch libncurses-dev make cmake libc6-dbg libc6-dbg:i386 gdb patchelf tmux radare2 ghidra rizin python3-ropgadget fzf ripgrep` 已经安装过了的会跳过，安就是了
2.   更新 python 环境：
     1.   确定已有的 python 环境：`which python` 返回 */usr/bin/python*，进一步查看 `ls /usr/bin/python*`，确定只有 */usr/bin/python3.x*、*/usr/bin/python3*、*/usr/bin/python* 等几个选项，以免乱环境
     2.   `python3 -m pip install --upgrade pip`，`pip install ipython setuptools setuptools_rust`，`pip install --upgrade pwntools`
     3.   验证是否安装成功：`python -c "from pwn import *;print(asm('ret'))"`，返回操作码 *b'\xc3'* 即为成功
     4.   一些其他 package：`pip install r2pipe python3-ropgadget`

## pwndbg

get src here：[pwndbg/pwndbg](https://github.com/pwndbg/pwndbg.git)

### main

1.   创建环境根目录：`sudo mkdir -p /home/app/pwnenv/pwndbg`，`sudo chown -R wkyuu:wkyuu /home/app`
2.   `git clone https://github.com/pwndbg/pwndbg.git /home/app/pwnenv/pwndbg/repo`
3.   `cd /home/app/pwnenv/pwndbg/repo`，`chmod +x ./setup.sh`，`sudo ./setup.sh` 执行安装
4.   一般来说网络通畅的条件下都可以正常安装，如果不行就配置 `export all_proxy="addr:port"`

### plugins

[pwngdb](https://github.com/scwuaptx/Pwngdb.git)（和新版本的 pwndbg 不是很适配，旧版本的可以用） 和 [splitmind](https://github.com/jerdna-regeiz/splitmind.git)（搭配 tmux）

1.   ~~pwngdb 包含 angelheap，通过 curl 直接获取，确保 pwndbg 的根路径是 `/home/app/pwnenv/pwndbg`~~

     1.   ~~`curl -o /home/app/pwnenv/pwndbg/repo/pwndbg/pwngdb.py https://raw.githubusercontent.com/scwuaptx/Pwngdb/master/pwndbg/pwngdb.py`、`curl -o /home/app/pwnenv/pwndbg/repo/pwndbg/commands/pwngdb.py https://raw.githubusercontent.com/scwuaptx/Pwngdb/master/pwndbg/commands/pwngdb.py`~~
     2.   ~~`curl -o /home/app/pwnenv/pwndbg/repo/pwndbg/angelheap.py https://raw.githubusercontent.com/scwuaptx/Pwngdb/master/pwndbg/angelheap.py`、`curl -o /home/app/pwnenv/pwndbg/repo/pwndbg/commands/angelheap.py https://raw.githubusercontent.com/scwuaptx/Pwngdb/master/pwndbg/commands/angelheap.py`~~

2.   splitmind 的主要作用是在使用 tmux 时方便将各种 pwndbg 输出重定向到不同的区块

     1.   获取插件内容：`git clone https://github.com/jerdna-regeiz/splitmind.git /home/app/pwnenv/pwndbg/plugins/splitmind`

     2.   `echo "source /home/app/pwnenv/pwndbg/plugins/splitmind/gdbinit.py" >> ~/.gdbinit`

     3.   然后需要在 `~/.gdbinit` 里写上 splitmind 的生成脚本，[内容参考](https://bbs.kanxue.com/thread-276203-1.htm) 如下：

          ```ini
          set context-clear-screen on
          set follow-fork-mode parent
          python
          import splitmind
          (splitmind.Mind()
            .tell_splitter(show_titles=True)
            .tell_splitter(set_title="Main")
            .right(display="backtrace", size="25%")
            .above(of="main", display="disasm", size="80%", banner="top")
            .show("code", on="disasm", banner="none")
            .right(cmd='tty; tail -f /dev/null', size="65%", clearing=False)
            .tell_splitter(set_title='Input / Output')
            .above(display="stack", size="75%")
            .above(display="legend", size="25")
            .show("regs", on="legend")
            .below(of="backtrace", cmd="ipython", size="30%")
          ).build(nobanner=True)
          end
          set context-code-lines 30
          set context-source-code-lines 30
          set context-sections  "regs args code disasm stack backtrace"
          ```
     
     4.   使用时需要先开 tmux；python exp 中需要如下语句：`context.terminal = ['tmux', 'splitw', '-h']`


完整的 `~/.gdbinit` 文件如下，参考了 [NoneShell/OwnConfigs](https://github.com/NoneShell/OwnConfigs/blob/main/.gdbinit) 的配置，一键 `curl -o ~/.gdbinit https://raw.githubusercontent.com/sparkuru/genshin/main/pwn/07_blog7_environment_configuration/.gdbinit`：

```ini
source /home/app/pwnenv/pwndbg/repo/gdbinit.py
source /home/app/pwnenv/pwndbg/plugins/splitmind/gdbinit.py

# splitmind
set context-clear-screen off
set debug-events off

python
sections = "regs"
mode = input("source/disasm/mixed mode:?(s/d/m)") or "d"
import splitmind
spliter = splitmind.Mind()
spliter.select("main").right(display="regs", size="50%").below(cmd="ipython", size="30%")
gdb.execute("set context-stack-lines 10")
legend_on = "code"

if mode == "d":
    legend_on = "disasm"
    sections += " disasm"
    spliter.select("main").above(display="disasm", size="40%", banner="none")
    gdb.execute("set context-code-lines 15")
elif mode == "s":
    sections += " code"
    spliter.select("main").above(display="code", size="40%", banner="none")
    gdb.execute("set context-source-code-lines 15")
else:
    sections += " disasm code"
    spliter.select("main").above(display="code", size="70%")
    spliter.select("code").below(display="disasm", size="40%")
    gdb.execute("set context-code-lines 8")
    gdb.execute("set context-source-code-lines 20")

sections += " args stack backtrace expressions"

spliter.show("legend", on=legend_on)
spliter.show("stack", on="regs")
spliter.show("backtrace", on="regs")
spliter.show("args", on="regs")
spliter.show("expressions", on="args")

gdb.execute("set context-sections \"%s\"" % sections)
gdb.execute("set show-retaddr-reg on")

spliter.build()
end
```

在使用 tmux 时，按 ctrl + b 进入命令模式，然后直接输入 `:set -g mouse on` 开启鼠标滚轮的滑动

## glibc all in one

输入 `ldd /usr/bin/cat`，可以得到 *libc.so.6 => /lib/x86_64-linux-gnu/libc.so.6* 和 */lib64/ld-linux-x86-64.so.2* 的回显，简单理解起来就是，cat 这个 elf 需要 libc.so.6 库来提供所需的函数实现，而动态链接器 ld-linux-x86-64.so.2 作为 cat 和 libc.so.6 的中间桥梁，作装载解释的作用，因此一般特定 glibc.so.6 都有其对应的 ld-linux.so.2

不同的 elf 可能有不同的 libc.so.6 版本，以及对应的 ld-linux.so.2，有时会提供，但是在正式的环境还是需要自己去获取，也可以查看本机最大使用的 glibc 版本：`strings /usr/lib/x86_64-linux-gnu/libc.so.6 | grep GLIBC`，默认向下兼容

为了学习或者研究特定环境下的漏洞，有的漏洞只有在低版本的 libc 有效，因此需要手动指定这些 libc.so 和解释器 ld-linux.so，glibc all in one 就是这么一个用来获取这些内容的项目

1.   `git clone https://github.com/matrix1001/glibc-all-in-one.git /home/app/pwnenv/glibc_all_in_one`
2.   `cd /home/app/pwnenv/glibc_all_in_one`，`chmod +x update_list download extract`，更新列表：`./update_list`，查看更新的结果：`cat list`，会列出一大串不同版本的 `2.xx-ubuntux.x`，根据 elf 文件所需的 libc 信息获取之，这里以 `2.27-3ubuntu1_amd64` 为例
3.   下载之：`./download 2.27-3ubuntu1_amd64`，下载完成的文件在 `/home/app/pwnenv/glibc_all_in_one/libs/2.27-3ubuntu1_amd64`  里，大部分环境所需的只有 `2.27-3ubuntu1_amd64/libc-2.27.so` 和 `2.27-3ubuntu1_amd64/ld-2.27.so`，分别对应 `libc.so.6 => /lib/x86_64-linux-gnu/libc.so.6` 和 `/lib64/ld-linux-x86-64.so.2`

如何使用以上的 libc.so 和 ld-linux.so，有两种方法，并且记住核心就是得先找 ld-linux.so，使得 ld-linux.so 去加载 libc.so.6：

1.   临时使用，有两种方式
     1.   通过 hook 的方式来使用：`LD_PRELOAD=2.27-3ubuntu1_amd64/libc-2.27.so 2.27-3ubuntu1_amd64/ld-2.27.so ./elf`，也可以直接 export 到环境变量里
     2.   通过控制环境变量中库的搜索路径顺序：`export LD_LIBRARY_PATH=2.27-3ubuntu1_amd64/libc-2.27.so:$LD_LIBRARY_PATH`，然后 `2.27-3ubuntu1_amd64/ld-2.27.so ./elf` 程序在运行时就会优先使用手动提供的 libc.so.6，不过这样会影响其他应用的使用，注意如果只指定了 libc.so 而没有指定对应版本的 ld-linux.so.2 就会出错
     3.   ~~还有一种 chroot 修改路径的方式，不过不推荐使用~~
2.   通过 patchelf 永久地修改 elf 的加载路径
     1.   `patchelf --replace-needed libc.so.6 2.27-3ubuntu1_amd64/libc-2.27.so ./elf`
     2.   `patchelf --set-interpreter 2.27-3ubuntu1_amd64/ld-2.27.so ./elf`
3.   在 python 脚本中该这么写：`p = process(['2.27-3ubuntu1_amd64/ld-2.27.so', './elf'], env={'LD_PRELOAD': 'libc.so.6 2.27-3ubuntu1_amd64/libc-2.27.so'})`
4.   如果想要编译时使用特定版本 libc.so.6 和 ld-linux.so.2
     1.   在编译时指定链接器：`gcc -o elf elf.c -Wl,--dynamic-linker=2.27-3ubuntu1_amd64/ld-2.27.so`
     2.   在使用时劫持环境变量：`export LD_LIBRARY_PATH=2.27-3ubuntu1_amd64/libc-2.27.so:$LD_LIBRARY_PATH`，然后 `./elf`

## exp templates

:wq

## useful

1.   https://ropemporium.com/challenge/split.html
2.   ropgadget
3.   [david942j/one_gadget](https://github.com/david942j/one_gadget.git)
4.   

## tmp

1.   ~~pwntools，pwndbg，splitmind，angelheap，tmux 安装配置~~
2.   pwn exp templates
3.   pwndbg cli command
4.   other cli command
5.   ~~patchelf，LE_PRELOAD~~
6.   用 nc 直接开一个端口来交互
7.   python，ord chr bin u64 p64 字符串转 bytes