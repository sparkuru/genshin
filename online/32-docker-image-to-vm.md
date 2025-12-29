
将 Docker 镜像转换为可直接用 QEMU 启动的 qcow2 磁盘镜像

核心是必须具备完备的 linux 启动逻辑, 包括内核、initrd、grub、kernel parameters 等, 下面就是围绕这个核心来展开的: 从 docker 拉取镜像, 制作 qcow2 镜像, 补充 kernel, initrd, grub 等组件, 最终得到一个可直接用 QEMU 启动的 qcow2 磁盘镜像.

## todo

1. docker 直接下载的镜像是什么, 和可用于正常启动的区别, 和宿主机引导的区别
2. qemu, pve 等可以提供什么条件
3. 为了正常启动基于 docker 的虚拟机, 需要补充哪些内容
4. 


安装前置 `sudo apt install qemu-utils parted docker.io`

文件准备: 

1. dockerfile, 创建一个包含完整系统组件（内核、systemd、grub）的 Docker 镜像
2. pack-qemu.sh, 打包脚本，将 Docker 镜像导出并安装 GRUB 到 MBR

## usage

以将 dvwa 镜像转换为 qcow2 镜像为例：

```bash
$ mkdir -p /tmp/dvwa-qemu
$ cd /tmp/dvwa-qemu

$ vim Dockerfile.qemu-ready
$ vim pack-qemu.sh

# 构建 Docker 镜像
$ docker build -f Dockerfile.qemu-ready -t dvwa-qemu .

# 打包
$ sudo ./pack-qemu.sh dvwa-qemu dvwa.qcow2 4G
```

启动虚拟机：

```bash
qemu-system-x86_64 \
  -hda dvwa.qcow2 \
  -m 1024 \
  -enable-kvm \
  -nographic \
  -serial mon:stdio \
  -net nic -net user,hostfwd=tcp::8080-:80,hostfwd=tcp::2222-:22
```

## qa

1. 启动后无法联网, 确保配置好了网络转发，端口之类的
2. 启动很慢, 可以通过 KVM 加速
3. 磁盘空间不足, 用 `qemu-img resize dvwa.qcow2 +2G`, 系统类 `resize2fs /dev/sda1` 扩展磁盘空间