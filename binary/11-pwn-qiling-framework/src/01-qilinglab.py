# -*- coding: utf-8 -*-

import os
import sys

import qiling

workdir = os.path.abspath(os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '../', 'archive')))
elf_path = os.path.join(workdir, 'binary', '01-qilinglab-x86_64')
rootfs_path = os.path.join(workdir, 'rootfs', 'x8664_linux')

argv = f'{elf_path}'.split(' ')
ql = qiling.Qiling(
    argv=argv, rootfs=rootfs_path,
    ostype=qiling.core.QL_OS.LINUX,
    archtype=qiling.core.QL_ARCH.X8664,
    verbose=qiling.core.QL_VERBOSE.DEBUG,
    console=False
)
ql.add_fs_mapper('/proc', '/proc')

# challenge 1
ql.hook_address(b'\x13\x37', 0x1337)

try:
    ql.run()
except Exception as e:
    print(f'Exception: {e}')
