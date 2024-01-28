#!/bin/bash

# gcc -g -o heap31 -fstack-protector heap.c
# gcc -g -o heap_overflow heap_overflow.c

patchelf --set-interpreter /home/wkyuu/Desktop/cheap/libs/2.31/ld-2.31.so /home/wkyuu/Desktop/cheap/heap_off_by_one/off_by_one
patchelf --replace-needed libc.so.6 /home/wkyuu/Desktop/cheap/libs/2.31/libc.so.6 /home/wkyuu/Desktop/cheap/heap_off_by_one/off_by_one
ldd ./off_by_one

# gcc -no-pie -o ./heap_uaf/uaf -g ./heap_uaf/uaf.c