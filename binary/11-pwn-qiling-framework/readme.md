# qiling

repo：https://github.com/qilingframework/qiling.git

## intro

1. feature

   1. cross platform、multi core
   2. sandbox emulate
   3. high level api
   4. python framework，easy to custom self script，就是可以利用这个框架来高度自定义地去分析固件，比如看运行时各种参数、内存，hook 中间运行时
   5. support gdbserver，gdb、ida、r2

2. can

   ```python
   from qiling import Qiling
   
   rootfs_path = './a-rootfs-x86_64'
   rootfs_argv = ['./a-rootfs-x86_64/elf/path', 'argv1', 'argv2']  # a-rootfs-x86_64/elf/path argv1 argv2
   qemu_env = ['HOME=/', 'PATH=/sbin:/bin']
   
   ql = Qiling(rootfs_argv, rootfs_path, qemu_env)
   
   
   # runtime hook
   buf = b'Hello, World!\n'
   ql.os.fd[write_fd].write(buf)
   ql.patch(0xdeadbeef, b'abcd\x00', filen_name='libxxx.so')
   
   # function hook
   def custom_puts(ql):
       pass
   def custom_syscall_read(ql):
       pass
   
   ql.set_api('puts', custom_puts)
   ql.set_syscall('read', custom_syscall_read)
   
   # register operation
   ql.reg.read('rax')  # 读 rax
   ql.reg.write('rax', 0x1234)  # 写 rax
   
   # memory operation
   ql.mem.map(0x1000, 0x1000)  # 操作内存前映射内存
   ql.mem.write(0x1000, b'Hello, World!\n\x00')  # 写内存
   ql.mem.search(0x1000, 0x2000, b'World')  # 搜索内存
   
   # filesystem operation
   from qiling.os.mapper import QlFsMappedObject
   class fake_urandom(QlFsMappedObject):
       def read(self, size):
           return b'\x01'
       def fstat(self):
           return {'st_size': 0}
   ql.add_fs_mapper('/dev/urandom', fake_urandom())
   
   # save state
   ql.save('state.pkl')
   ql.restore('state.pkl')
   ql.mem.save('mem.bin')
   ql.mem.restore('mem.bin')
   ql.reg.save('reg.bin')
   ql.reg.restore('reg.bin')
   
   # sandbox example, hook, breakpoint
   def save_content(ql, *args, **kwargs):  # save content when hit the breakpoint / address
       ql.save(cpu_context=False, snapshot='snapshot.bin')
       
   def patcher(ql):    # tmp patch the binary
       br0_addr = ql.mem.search('br0'.encode() + b'\x00')
       for addr in br0_addr:
           ql.mem.write(addr, b'lo\x00')
           
   def sandbox(path, rootfs):
       ql = Qiling(path, rootfs, output = 'debug', verbos = 5)
       ql.add_fs_mapper('/dev/urandom', '/dev/urandom')
       ql.hook_address(save_content, 0x1234dead)
       ql.hook_address(patcher, ql.loader.elf_entry)
       ql.run()
   
   import threading
   nvram_listener_thread = threading.Thread(target=nvram_listener, daemon=True)
   nvram_listener_thread.start()
   sandbox(rootfs_argv, rootfs_path)
   
   # debugger
   ql = Qiling(rootfs_argv, rootfs_path, output='debug')
   ql.multithread = False
   ql.debugger = 'gdb:rr'    # enable dbg with rr(record env, args and replay this instruction)
   ql.debugger = 'gdb:0.0.0.0:1234'    # internal gdbserver
   
   # run with afl
   '''
   #include <stdio.h>
   #include <stdlib.h>
   #include <unistd.h>
   
   int main(int argc, char **argv) {
       if (argc != 2) {
           fprintf(stderr, "Usage: %s <input>\n", argv[0]);
           return 1;
       }
   
       char command[256];
       snprintf(command, sizeof(command), "python3 qiling-afl.py %s", argv[1]);
       return system(command);
   }
   
   // gcc -o qiling_afl qiling_afl.c
   // afl-fuzz -i input_dir -o output_dir -- ./qiling_afl @@
   '''
   
   import sys
   input_data = sys.argv[1]
   rootfs_path = './a-rootfs-x86_64'
   rootfs_argv = ['./a-rootfs-x86_64/elf/path', input_data]
   ql = Qiling(rootfs_argv, rootfs_path, qemu_env)
   
   # runtime hook
   buf = b'Hello, World!\n'
   write_fd = 1  # 假设写入到标准输出
   ql.os.fd[write_fd].write(buf)
   ql.patch(0xdeadbeef, b'abcd\x00', file_name='libxxx.so')
   
   ql.run()
   ```

3. cli 工具：qltool

   1. 快速运行 elf：`qltool run -f elf_path --rootfs x8664_linux`
   2. 快速查看 elf 的 shellcode：`qltool code --os linux --arch mips --format hex -f rootfs/sbin/httpd`


## install

参照 [qiling setup guide](https://docs.qiling.io/en/latest/install/) 安装 qiling 框架：

```shell
#/usr/bin/env zsh

apt update
apt install -y \
    ack antlr3 aria2 asciidoc autoconf automake autopoint binutils bison build-essential \
    bzip2 ccache cmake cpio curl device-tree-compiler fastjar flex gawk gettext gcc-multilib g++-multilib \
    git gperf haveged help2man intltool libc6-dev-i386 libelf-dev libglib2.0-dev libgmp3-dev libltdl-dev \
    libmpc-dev libmpfr-dev libncurses5-dev libncursesw5-dev libreadline-dev libssl-dev libtool lrzsz \
    mkisofs msmtp nano ninja-build p7zip p7zip-full patch pkgconf python2.7 python3 python3-pip libpython3-dev qemu-utils \
    rsync scons squashfs-tools subversion swig texinfo uglifyjs upx-ucl unzip vim wget xmlto xxd zlib1g-dev

mv /usr/lib/python3.12/EXTERNALLY-MANAGED /usr/lib/python3.12/EXTERNALLY-MANAGED.backup
pip install qiling six
```

**注意：**pip 安装 qiling 框架时与 ipython 的依赖有冲突，可能面临二选一，解决方法是使用 venv 来管理 qiling：`python -m venv venv-qiling`

获取所使用的各种架构的 rootfs：https://github.com/qilingframework/rootfs.git

## refer

1.   https://github.com/qilingframework/qiling
2.   https://www.iotsec-zone.com/article/391
3.   https://www.shielder.com/blog/2021/07/qilinglab-release/
4.   https://www.bilibili.com/video/BV13T4y1N7M5
5.   