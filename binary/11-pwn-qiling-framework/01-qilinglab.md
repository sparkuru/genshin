# qiling lab

> The binary is not stripped, not obfuscated, and compiled with `gcc -O0`

## install

1. 参照 [qiling setup guide](https://docs.qiling.io/en/latest/install/) 安装 qiling 框架
2. 获取 qilinglab release 文件：[x86_64](https://www.shielder.com/attachments/qilinglab-x86_64) / [aarch64](https://www.shielder.com/attachments/qilinglab-aarch64)

## outline

1. Store 1337 at pointer 0x1337.
2. Make the `uname` syscall return the correct values.
3. Make `/dev/urandom` and `getrandom` “collide”.
4. Enter inside the “forbidden” loop.
5. Guess every call to `rand()`.
6. Avoid the infinite loop.
7. Don’t waste time waiting for `sleep`.
8. Unpack the struct and write at the target address.
9. Fix some string operation to make the iMpOsSiBlE come true.
10. Fake the `cmdline` line file to return the right content.
11. Bypass CPUID/MIDR_EL1 checks.

## 01

使用 qiling 启动程序：

```python
# -*- coding: utf-8 -*-

import os
import sys

from qiling import Qiling
from qiling.const import QL_VERBOSE

def xpath(path):
    return os.path.abspath(os.path.normpath(path))

workdir = xpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../', 'archive'))
elf_path = os.path.join(workdir, 'binary', '01-qilinglab-x86_64')
rootfs_path = os.path.join(workdir, 'rootfs', 'x8664_linux')

argv = f'{elf_path}'.split(' ')
ql = Qiling(argv = argv, rootfs = rootfs_path, verbose = QL_VERBOSE.DEBUG, console=False)
ql.add_fs_mapper('/proc', '/proc')

ql.run()
```

添加 ``



## refer

1. https://www.shielder.com/blog/2021/07/qilinglab-release/
2. 