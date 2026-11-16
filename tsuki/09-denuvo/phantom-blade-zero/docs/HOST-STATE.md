# 影之刃零绕 D 环境记录（2026-11-14）

本文保留当时的游戏版本与 ARTIFACT 组件记录，不代表当前机器状态。路径使用示例目录 `D:\game\pbz`。

## 版本与关键文件

| 项 | 记录值 |
|---|---|
| 游戏构建 | `CL-302256_JKS-17280`（Steam build 26367565） |
| `PBZ.exe` | 498,913,272 B · SHA256 `4415933C…9E423` |
| `artifact.json` | 15,325 B · 目标 hash `c1ed8a00d0c8c8df` · SHA256 `9987107F…D386F` |
| `artifact.dll` | 1,280,000 B · SHA256 `71AE5CC3…67A8D` |
| `coldloader.dll` | 205,824 B（Fixed.DLL 版）· SHA256 `49D971CE…05E63` |
| `steamclient64.dll` | 22,404,008 B · SHA256 `844676AC…9150D` |
| `winmm.dll` | 14,848 B · SHA256 `1DAF6203…18D6D` |
| `steam_api64.dll` | 319,128 B |

## 游戏目录

```text
D:\game\pbz\
├── pbz\platform\steam\     PBZ.exe 与配套 ARTIFACT 组件
├── pbz\ProjectPBZ\          游戏数据与存档目录
├── scripts\                  辅助脚本与状态备份
├── enable_bypass.ps1          环境开关
└── start.bat                  启动入口
```

## 版本兼容

- 记录中的 302256 更新包带有对应版本的 `artifact.dll` 和 `artifact.json`。
- 当时使用 `Fixed.DLL` 版 `coldloader.dll` 修复存档与 DLC 报错。
- 旧 301524 版 `Crackfix-ARTIFACT.rar` 的目标 hash 为 `a551c95bdaf4d7a9`，与 302256 的记录值不符，不能混用。
- 配置文件中的目标 hash 与游戏程序版本绑定；替换游戏程序或组件前应核对完整版本和哈希。

## 备份与回滚

原始游戏文件和存档应另行备份，例如放在 `D:\game\backup\pbz`。环境脚本默认将变更记录保存在部署目录的 `scripts\state\` 下，`-Revert` 依赖该目录中的记录。这个示例路径不代表备份已存在。
