# emulation over docker

使用系统内核功能 Miscellaneous Binary Format（binfmt_misc）将非本机的二进制文件自动与特定的解析器匹配，qemu user mode 就是这么实现的；启用 binfmt_misc，然后利用 docker build 不同架构（mips、arm、arm64、amd64）的镜像作为备用；以后每次使用只需要将相应的 rootfs 映射后即可实现仿真

## env

Windows、MacOS 桌面版 docker 自动启用 binfmt_misc，Linux 需要手动启动一下

首先检查 binfmt_misc 的启动情况：

1.   查看是否存在 binfmt_misc：

     ```bash
     ┌──(wkyuu㉿schale)-[~]
     └─$ ls -al /proc/sys/fs/binfmt_misc/
     总计 0
     drwxr-xr-x 2 root root 0  7月 10 00:23 .
     dr-xr-xr-x 1 root root 0  7月 10 00:23 ..
     -rw-r--r-- 1 root root 0  7月 10 00:23 qemu-aarch64
     -rw-r--r-- 1 root root 0  7月 10 00:23 qemu-alpha
     -rw-r--r-- 1 root root 0  7月 10 00:23 qemu-arm
     -rw-r--r-- 1 root root 0  7月 10 00:23 qemu-mips
     -rw-r--r-- 1 root root 0  7月 10 00:23 qemu-ppc
     -rw-r--r-- 1 root root 0  7月 10 00:23 qemu-riscv32
     -rw-r--r-- 1 root root 0  7月 10 00:23 qemu-s390x
     -rw-r--r-- 1 root root 0  7月 10 00:23 qemu-xtensaeb
     --w------- 1 root root 0  7月 10 00:23 register
     -rw-r--r-- 1 root root 0  7月 10 00:23 status
     
     ┌──(wkyuu㉿schale)-[~]
     └─$ cat /proc/sys/fs/binfmt_misc/qemu-aarch64
     enabled
     interpreter /usr/libexec/qemu-binfmt/aarch64-binfmt-P
     flags: POCF
     offset 0
     magic 7f454c460201010000000000000000000200b700
     mask ffffffffffffff00fffffffffffffffffeffffff
     ```

2.   想要 docker 能够拉取其他架构的镜像，需要手动配置一下启用 binfmt_misc

     1.   拉取一个特权镜像，该镜像会自动配置相应 binfmt_misc，`sudo docker run --rm --privileged docker/binfmt:a7996909642ee92942dcd6cff44b9b95f08dad64`
     2.   命令执行完成后，按照上述方式检测 binfmt_misc 是否成功启动

## emu

1.   去网上随便找一个固件，提取其 rootfs，检查架构 mips
2.   拉取一个 mips 的 docker：`docker run -it -p 8080:80 "/tmp/mips:/" mips64le/debian`
3.   将固件映射到 docker 中并启动：`docker run -it -p 8080:80 -v "/tmp/tmp/fw/fw-rootfs:/tmp/rootfs" mips64le/ubuntu`



patch 出错的地方

hook 掉 exit

patch 整个函数

## refer

1.   http://dockeradv.baoshu.red/buildx/multi-arch-images.html
2.   https://www.cnblogs.com/yaohong/p/17481358.html
3.   https://blog.lyle.ac.cn/2020/04/14/transparently-running-binaries-from-any-architecture-in-linux-with-qemu-and-binfmt-misc