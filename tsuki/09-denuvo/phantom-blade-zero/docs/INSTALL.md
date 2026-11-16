# Phantom Blade Zero 部署与回滚

以下路径为示例：部署根目录 `D:\game\pbz`，游戏主程序位于 `D:\game\pbz\pbz\platform\steam\PBZ.exe`。请先准备与游戏版本匹配的游戏文件和配套组件。

## 1. 放置脚本和游戏

从仓库的 `phantom-blade-zero/` 方案目录，将 `scripts/enable_bypass.ps1` 与 `scripts/start.bat` 复制到部署根目录。如果游戏文件原先直接位于该根目录，可在游戏退出后从方案目录使用整理脚本：

```powershell
.\scripts\reorganize.ps1 -Root 'D:\game\pbz' -WhatIf
.\scripts\reorganize.ps1 -Root 'D:\game\pbz'
```

整理脚本只移动已知游戏文件至 `pbz\`，并创建 `scripts\state\`；其他已有文件保留原位。若游戏已经处于示例布局，可以跳过这一步。

## 2. 预览和配置环境

以管理员身份打开 PowerShell，在部署根目录执行：

```powershell
.\enable_bypass.ps1 -WhatIf
.\enable_bypass.ps1
```

`-WhatIf` 只预览计划，不创建状态文件或应用变更；为完整读取系统状态，应从管理员 PowerShell 运行。脚本按 Secure Boot 状态选择测试签名或一次性启动选项，并记录原始 BCD 和注册表值。配置完成后重启；使用一次性启动选项时需按屏幕提示操作。

状态默认保存在 `scripts\state\bypass-*.json`，BCD 和注册表快照保存在 `scripts\state\backup\`。可用 `-StateDir <目录>` 指定其他位置；配置和回滚必须使用同一目录。

## 3. 检查和启动

```powershell
.\start.bat --check
.\start.bat
```

第一条只检查主程序路径。游戏文件、配置和 CPU 对应的驱动必须来自匹配的版本；`Wrong game version` 通常表示主程序和 `artifact.json` 不匹配。

## 4. 回滚

```powershell
.\enable_bypass.ps1 -Revert -WhatIf
.\enable_bypass.ps1 -Revert
```

脚本读取状态目录中最近的 JSON，恢复其中记录的 BCD 和注册表值，然后需要重启。JSON 在执行修改后写入，部分步骤的异常会打印后继续；中途失败或中断时不能假定原值已完整保存。Secure Boot 的固件设置需要自行恢复。旧状态文件仍可读取，但其中没有记录的值无法自动还原；较早版本的记录可能不含 System Guard 的原值。

更多目录和排障说明见 [NOTES.md](NOTES.md)；版本和文件哈希见 [EVAL.md](EVAL.md)。
