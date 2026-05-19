# busybox

制作一个自己的 busybox ...

1.   init all the env
2.   some scripts with python embedded
3.   一些常用指令的整合 like cat、curl、ps、netstat（我觉得 python 写起来就很好，也没有那么必要注意那一点性能）
4.   a binary to auto init in a mips、arm、x86、
     1.   .bash_rc
5.   a binary to auto get pwn tools、reverse
     1.   ropgadget
     2.   split
     3.   objdump
6.   a binary to solve misc、crypto
     1.   yafu
     2.   cyberchef

## before



## refer

1. 官方 busybox 仓库：https://busybox.net/downloads/binaries/
2. https://github.com/tiiuae/aarch64_bin_builder.git
3. mips static binary 文件：https://github.com/darkerego/mips-binaries.git
4. arm、ppc、x86，static binary 文件：https://github.com/ernw/static-toolbox.git