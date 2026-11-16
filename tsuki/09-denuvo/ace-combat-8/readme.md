# ACE COMBAT 8

此方案包含 AC8 的 Windows 环境准备、检查、启动和回滚脚本。脚本本身不实现版本专用的加载器、配置或驱动；运行时仍需要自行准备与目标程序匹配的配套文件。

## 目录

```text
ace-combat-8/
├── readme.md
├── artifacts.json           文件、大小、哈希和来源状态
├── unique/                  专属或较难获取的文件及获取链接
├── scripts/                 检查、配置、验证、启动与回滚
│   └── research/            先前独立研究脚本
├── lib/                     主脚本使用的公共函数
├── docs/                    操作说明、兼容性和过程记录
└── workspace/               被 Git 忽略的样本、备份、日志和历史归档
```

主脚本从 `scripts/` 加载 `lib/00-common.ps1`；必须保留两者的相对位置。运行时备份和日志分别位于 `workspace/backups/` 与 `workspace/logs/`。研究脚本是独立的历史材料，其中部分会修改系统，并使用另一份示例备份目录，不应与主脚本的备份混用。

## 实现与使用

入口为 `scripts/01-check.ps1`、`02-apply.ps1`、`03-verify.ps1`、`04-launch.ps1` 和 `99-rollback.ps1`。默认游戏根目录是 `D:\game\ac8`，检查、验证和启动支持 `-GameDir`。例如，从本方案目录的管理员 PowerShell 运行：

```powershell
.\scripts\01-check.ps1 -GameDir 'D:\game\ac8'
.\scripts\02-apply.ps1 -DryRun
```

`-DryRun` 不应用配置命令，但仍会创建日志和备份。`01-check.ps1` 的最终结论没有把缺失的游戏文件计入失败，需另行检查输出中的文件项。完整步骤见 [操作指南](docs/KIT-GUIDE.md)和[过程记录](docs/PROCESS-AND-PITFALLS.md)。

现有 `99-rollback.ps1` 对部分 BCD 项使用固定值，而不是根据原始快照还原；导入注册表也不保证删除新增值，部分失败只打印日志。应保留快照并逐项核对，不能把该脚本视为完整还原保证。迁移后的脚本尚未在 Windows 上运行验证。

## 所需文件与版本专用内容

游戏主程序示例路径为 `Game/Binaries/Win64/AceCombat8.exe`。该目录还需要与主程序版本和 CPU 匹配的 `artifact.dll`、`artifact.json`、代理 `winmm.dll` 及对应的 AMD 或 Intel 组件；具体清单与本地样本哈希见 [artifacts.json](artifacts.json)。样本集合包括可选性尚未确认的文件，不能推断其中每个文件都必需。

本地保留的 10 个样本共 1,646,463 字节，专属组件位于 [unique/](unique/readme.md)，其余位于被 Git 忽略的 `workspace/samples/` 和 `workspace/archive/`；`unique/` 文件可根据需要提交，游戏主程序不在此目录中。样本里的配置、加载器和驱动不会由本项目生成；配置与加载器的公开来源及其与官方游戏发行包的关系尚未核实，驱动的公开上游见下文。

## 第三方来源

- [AC8 Steam 页面](https://store.steampowered.com/app/2288340/)：游戏获取入口，未确认可提供所需版本。
- [HyperDbg 发行页](https://github.com/HyperDbg/HyperDbg/releases/tag/v0.25)：Intel 组件的公开上游；已比较的发行版与本地驱动文件不同，但 `hyperlog.inf` 可由 v0.18 精确重建。
- [SimpleSvm 源码](https://github.com/tandasat/SimpleSvm)：AMD 组件的公开上游，与本地驱动包含多个相同的特征日志；重编译后的兼容性尚未验证。

逐文件比较过程见 [上游比较](docs/UPSTREAM-COMPARISON.md)；下载地址、哈希与匹配状态以 `artifacts.json` 为准。
