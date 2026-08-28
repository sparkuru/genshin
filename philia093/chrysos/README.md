# Chrysos Buildroot/QEMU platforms

本目录维护少量可独立启动的 Linux/QEMU 平台，用于把宿主机上的二进制程序只读挂载进 guest 后手工测试。它不是自动识别、调度或批量执行二进制的平台。

## 当前平台

| 目录 | 架构与运行库 | Linux | 用途 |
| --- | --- | --- | --- |
| `armv7l-linux-3.10.108/` | ARMv7、glibc ABI | 3.10.108 | 老 ARM 设备和旧内核程序 |
| `aarch64-linux-4.14.98/` | AArch64、glibc | 4.14.98 | 老一代 ARM64 设备 |
| `aarch64-linux-6.18.7/` | AArch64、glibc | 6.18.7 | 现代 ARM64 基线 |
| `x86_64-linux-6.18.7-glibc/` | x86-64、glibc | 6.18.7 | PC、服务器、NAS 和常见虚拟机 |
| `mipsel32r2-linux-4.14.336-uclibc-ng/` | MIPSel32r2、uClibc-ng | 4.14.336 | 小端 MIPS 路由器和嵌入式固件 |

## 通用操作

进入目标平台目录后执行：

```sh
./build.sh
./validate.sh
./run-qemu.sh --background --share /path/to/programs
telnet 127.0.0.1 PLATFORM_PORT
./stop-qemu.sh
```

共享目录在 guest 中位于 `/mnt/host`，默认只读。每次启动使用临时 rootfs 或内置 initramfs，不会修改发布镜像；端口和平台限制见各目录的 `readme.md`。

## 根目录结构

```text
chrysos/
├── ARCH-VERSION/   自包含的平台目录
├── templates/      新增平台的结构参考和一致性工具
├── README.md       操作入口和当前平台清单
└── prd.md          长期范围、架构取舍和后续规划
```

根目录不放运行脚本。Buildroot 平台的公共实现保存在各自的 `common.sh` 中，因此单独复制一个平台目录仍可构建、验证和启动。新增平台的约束与工具见 [`templates/README.md`](templates/README.md)。
