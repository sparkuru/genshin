---
title: "app | vmware-workstation-handbook"
description: "刚开始用 VMware 的时候就被这个搞了好久，现在基本解决了，做一个备忘。"
date: "2022-06-27T07:46:00.000Z"
updated: "2024-02-21T12:06:16.000Z"
tags: []
draft: false
layout: "post"
slug: "vmware-workstation-handbook"
---

## VMware Workstation Handbook

本机配置

- 天选1，AMD Ryzen 7 4800H，RTX 2060 6G
- VMware Workstation 15.5.6

## PROBLEM

>  开启电脑的 Hyper-V 选项

1. 在开机时按住 `F2` 进机子的 bios 界面(不同的机子进bios的方式不同，[华硕的是F2](http://knowledge.ipason.com/ipKnowledge/knowledgedetail.html/158))
2. 新的主板进的一般都是 `EZ MODE`，在右下角有显示进入 `Advanced` 
3. 找到 `SYM Mode`，将下拉对话框中选成 `Enabled`
4. 按 `F10` 保存并重启

---

>  在 `启用或关闭Windows功能` 中没有 `Hyper-V` 相关选项：

1. 在桌面新建一个 `Hyper-V.cmd` 文件

2. 编辑这个文件，复制粘贴以下内容，保存

```txt
  pushd "%~dp0"
  dir /b %SystemRoot%\servicing\Packages\*Hyper-V*.mum >hyper-v.txt
  for /f %%i in ('findstr /i . hyper-v.txt 2^>nul') do dism /online /norestart /add-package:"%SystemRoot%\servicing\Packages\%%i"
  del hyper-v.txt
  Dism /online /enable-feature /featurename:Microsoft-Hyper-V-All /LimitAccess /ALL
```

3. 右键 `以管理员身份运行`，随后会跳出cmd，等待安装完成

4. 最后会询问是否重启电脑，选择是即可

---

>  打开虚拟机后出现 `vmware workstation 与 device/credential guard 不兼容。`

1. 使用 `win + X` 呼出菜单，选择 `命令提示符(管理员)`

2. 在 cmd 中输入

	`bcdedit /set hypervisorlaunchtype off`，

	如果想重新开启，则输入 `bcdedit /set hypervisorlaunchtype auto`

3. 重启

---
