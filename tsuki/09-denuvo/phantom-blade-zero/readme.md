# Phantom Blade Zero

此方案包含 PBZ 的 Windows 环境配置、启动和回滚脚本。游戏主程序与版本匹配的 ARTIFACT 加载器、配置和驱动需要自行准备；脚本不会生成这些组件。

## 目录

```text
phantom-blade-zero/
├── readme.md
├── artifacts.json       文件、大小、哈希和来源状态
├── unique/              专属或较难获取的文件及获取链接
├── scripts/             环境配置、启动和目录整理入口
├── lib/                 本方案的公共代码（当前为空）
├── docs/                部署、组件评估和历史版本记录
└── workspace/           被 Git 忽略的本地样本和运行数据
```

`scripts/enable_bypass.ps1` 配置环境并按其状态文件回滚；`scripts/start.bat` 从部署根目录定位游戏；`scripts/reorganize.ps1` 可选地整理游戏目录。部署时将前两个文件复制到示例根目录 `D:\game\pbz`，保留游戏的 `pbz/platform/steam/` 布局，详细步骤见 [部署说明](docs/INSTALL.md)。

## 实现与使用

在部署目录的管理员 PowerShell 中可使用：

```powershell
.\enable_bypass.ps1 -WhatIf
.\enable_bypass.ps1
# 重启后检查并启动
.\start.bat --check
.\start.bat
# 完成后预览回滚
.\enable_bypass.ps1 -Revert -WhatIf
```

`--check` 只检查 `PBZ.exe` 路径。脚本复制到部署根目录时，状态默认保存在该目录的 `scripts/state/`；直接运行本仓库的 `scripts/enable_bypass.ps1` 时，状态保存在 `workspace/state/`。两种位置的状态不会自动合并，使用 `-StateDir` 时配置与回滚必须指定同一目录。脚本在执行修改后写入 JSON，且会记录并继续处理部分步骤的异常，因此中途失败或中断时不能假定已完整保存原值。迁移后的脚本尚未在 Windows 上运行验证。

## 所需文件与版本专用内容

目标程序示例为 `pbz/platform/steam/PBZ.exe`。其目录需要版本匹配的 `artifact.dll`、`artifact.json`、代理 `winmm.dll`、对应 CPU 的驱动，以及样本中记录的其他配套组件；逐项信息见 [artifacts.json](artifacts.json)。这些文件的实际必需性并非全部经过运行时验证。

本地保留的 17 个样本共 24,345,274 字节，专属组件位于 [unique/](unique/readme.md)，其余位于被 Git 忽略的 `workspace/samples/ARTIFACT/platform/steam/`；`unique/` 文件可根据需要提交，主程序不在这里。样本的目标值与历史 301524 记录一致，但匹配的主程序未验证；历史 302256 的组件记录不同，不能直接混用。详见[组件评估](docs/EVAL.md)和[历史版本记录](docs/HOST-STATE.md)。

## 第三方来源

- [PBZ Steam 页面](https://store.steampowered.com/app/4115450/)：游戏获取入口，未确认可提供匹配版本。
- [HyperDbg](https://github.com/HyperDbg/HyperDbg/releases/tag/v0.25) 与 [SimpleSvm](https://github.com/tandasat/SimpleSvm)：驱动的公开上游；已比较的 HyperDbg 发行文件与本地样本不同，重编译和替换兼容性尚未验证。
- [ColdLoader 发行页](https://github.com/denuvosanctuary/coldloader/releases/tag/v1.4.0)：公开上游；当前本地 `coldloader.dll` 与已比较的发行 DLL 不同。
- [GBE Fork 发行页](https://github.com/Detanup01/gbe_fork/releases/tag/release-2026_09_16_2)：其中 `emu-win-release-vs26.7z` 的 `steamclient64.dll` 与本地样本逐字节一致。

逐文件比较过程见 [上游比较](docs/UPSTREAM-COMPARISON.md)；下载地址、哈希与匹配状态以 `artifacts.json` 为准。
