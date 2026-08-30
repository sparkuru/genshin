# 平台模板

`templates/` 只用于新增平台时参考结构、生成示例和检查一致性。现有平台运行时不依赖这里的任何文件。

## 目录

```text
templates/
├── buildroot-profile/         Buildroot 平台的完整结构参考
│   ├── common.sh              生命周期公共实现；生成后位于平台目录内部
│   ├── profile.env            版本、架构契约、libc 和 QEMU 元数据
│   ├── buildroot.defconfig.in Buildroot 配置模板
│   ├── board/                 内核、BusyBox 和 rootfs overlay
│   └── {build,validate,run-qemu,stop-qemu}.sh
└── tools/
    ├── new-aarch64-profile.sh 从参考模板生成 AArch64 平台
    └── check-shell.sh         格式、语法、ShellCheck 和 profile 检查
```

`buildroot-profile/` 使用 AArch64 `virt` 作为可运行示例。新建其他架构时保留目录和四个生命周期入口，但必须替换 `profile.env`、`board/linux.config`、Buildroot 架构选项及对应 QEMU backend；不能直接把 AArch64 内核配置改个目录名使用。

## 新增平台约束

- 平台目录必须自包含，不能在运行时 source `templates/` 或仓库根目录文件。
- 固定 Buildroot、Linux 和其他外部输入的版本及 SHA-256。
- 保留 `build.sh`、`validate.sh`、`run-qemu.sh`、`stop-qemu.sh`。
- `run-qemu.sh --share PATH` 只读挂载到 guest `/mnt/host`，guest 不自动执行共享文件。
- 每个平台使用独立的 localhost telnet 端口。
- `profile.env` 必须声明 `PROFILE_KIND`、端序、ABI、浮点 ABI、ELF 位数、用户态
  模式和 `ROOTFS_INSTALL_DIR`；这些字段共同定义可执行文件的目标契约。
- 架构差异写入平台自身配置；只有确定适用于全部 Buildroot 平台的改动才同步到各平台的 `common.sh`。

Buildroot 模板默认提供开发与调试 rootfs：Vim、Python 3、curl、wget、GNU
findutils、文件哈希和识别工具、ELF/系统调用追踪以及网络和进程
诊断工具，并额外安装按目标 ABI 静态构建的 `gdbserver`。默认 ext4 镜像大小为
512 MiB；新平台不应悄悄移除该基线。

## 生成 AArch64 示例

```sh
./templates/tools/new-aarch64-profile.sh \
  --profile-name aarch64-linux-X.Y.Z \
  --buildroot-version YYYY.MM.P \
  --buildroot-sha256 64_HEXADECIMAL_CHARACTERS \
  --linux-version X.Y.Z \
  --linux-sha256 64_HEXADECIMAL_CHARACTERS \
  --linux-headers-option BR2_PACKAGE_HOST_LINUX_HEADERS_CUSTOM_X_Y \
  --qemu-port 4550
```

生成器拒绝覆盖已有目录，并检查模板 token 和 Shell 语法。其他架构应复制最接近的现有平台，再按本文件的结构契约逐项核对。

## 一致性检查

```sh
./templates/tools/check-shell.sh --check
./tools/check-profiles.sh
```

不带 `--check` 时会先用 shfmt 格式化，再执行语法和 ShellCheck。QEMU 启动仍需进入各平台运行 `./validate.sh`。
