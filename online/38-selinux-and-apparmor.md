# selinux & apparmor

linux 上的强制访问控制方案，这二者功能类似，但是设计和实现方式不同

## selinux

tab

## apparmor


### 解决 cursor terminal sandbox 问题

discuss here: https://forum.cursor.com/t/terminal-sandbox-issue-linux/152979/

起因是某个 cursor 版本更新后，一直弹窗报错 `Terminal sandbox could not start. This may be caused by an AppArmor configuration on your Linux system (kernel 6.2+).`，点了不再提示也没用

cursor 官方也更新了多次，包括修改 apparmor 配置，但是效果并不好（至少对我来说）

相关版本信息如下

```
Version: 2.6.22
VSCode Version: 1.105.1
Commit: c6285feaba0ad62603f7c22e72f0a170dc8415a0
Date: 2026-03-27T15:59:31.561Z
Build Type: Stable
Release Track: Default
Electron: 39.8.1
Chromium: 142.0.7444.265
Node.js: 22.22.1
V8: 14.2.231.22-electron.0
OS: Linux x64 6.12.73+deb13-amd64
```

在官方讨论区里，有人汇总他人结论，提出了一个 [有效的解决方案](https://forum.cursor.com/t/terminal-sandbox-issue-linux/152979/48)，操作如下

```bash
sudo tee /etc/apparmor.d/cursor_sandbox << 'EOF'
include <tunables/global>

profile cursor_sandbox flags=(complain) {
  include <abstractions/base>
  network netlink raw,
  capability,
  file,
  unix,
}

profile cursor_sandbox_remote flags=(complain) {
  include <abstractions/base>
  network netlink raw,
  capability,
  file,
  unix,
}
EOF
```

然后重载并应用该配置：`sudo apparmor_parser -r /etc/apparmor.d/cursor_sandbox`