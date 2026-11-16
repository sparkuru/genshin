# Phantom Blade Zero 目录与排障

示例目录结构：

```text
D:\game\pbz\
├── pbz\platform\steam\       PBZ.exe 与版本匹配的游戏组件
├── pbz\ProjectPBZ\            游戏数据
├── scripts\state\             环境原值 JSON 与 backup\ 快照
├── enable_bypass.ps1           环境配置与 -Revert 回滚
└── start.bat                   启动入口（--check 只验证路径）
```

`reorganize.ps1` 只移动已知游戏文件并创建状态目录，不处理其他已有文件。`start.bat` 使用自身所在目录定位游戏，因此需要放在部署根目录。

| 现象 | 检查方向 |
|---|---|
| `Wrong game version` | 核对 `PBZ.exe` 与 `artifact.json` 的版本和目标哈希 |
| `RFLAGS not equal` | 检查虚拟化环境、系统配置和 CPU 对应驱动 |
| `Service error` | 查看系统事件与游戏驱动服务状态 |
| 无反应或秒退 | 检查虚拟化占用、系统日志及游戏文件版本 |

每次环境配置的原始值保存在 `scripts\state\bypass-*.json`。使用自定义 `-StateDir` 时，回滚也必须指向同一目录。部署示例见 [INSTALL.md](INSTALL.md)。
