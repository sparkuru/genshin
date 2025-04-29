
新装、重装 unix 系统，一般都是按照以下流程来走的：

1. xxx
2. 2

现在尝试通过手动完全新装一个系统的方式，来走一遍这个流程，加深印象：

介绍 linux 系统的

1. 启动流程
2. 关键内容
3. 各目录介绍
4. 文件系统：常见文件系统 lfs、lvm 什么的
5. 内核

## question

现在模拟一个场景：系统使用 debian，但是误操作将 `/boot` 目录给删了，导致丢失内核、grub、efi

任务：在不重装系统、不丢配置的前提下，修复系统

## ss

相关：

1. livekit、arch-liveiso、gentoo-livegui
2. `mount`、`umount`
3. `genfstab`
4. `arch-install-scripts`
5. `mkfs.ext4`
6. `grub-mkconfig`
7. `swapon`
8. `efibootmgr`，可以整理 efi 启动项，例如去掉多系统的 efi 引导
9. 重新下载 linux 内核、