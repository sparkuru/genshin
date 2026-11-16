# AC8 运行与排障

环境脚本负责配置 Windows、检查状态、启动游戏和回滚；`artifact.dll`、配置文件和对应驱动来自游戏包。游戏目录示例为 `D:\game\ac8`。

## 配置与备份

- 先运行 `01-check.ps1` 查看 Secure Boot、测试签名、虚拟化和游戏文件状态。
- `02-apply.ps1` 会在 `workspace/backups/` 创建备份，再调整引导和注册表设置；改动后需要重启。`scripts/research/` 下独立脚本的备份位置与之不同，见工具包说明。
- Secure Boot 开启时可能无法启用测试签名；需要按设备固件设置处理。
- 修改引导设置前应确认 BitLocker 状态和恢复方式。`02-apply.ps1` 检测到加密时会要求明确使用 `-Force`。
- 关闭 Windows hypervisor 后，仍需检查 VBS、HVCI 和 System Guard；重启后运行 `03-verify.ps1`。

## 启动与排查

- 游戏进程可能自举并替换最初的 PID；启动脚本按进程名观察，不应仅凭第一个 PID 退出判断失败。
- 通过 SSH 或服务会话启动图形程序时，`04-launch.ps1` 可使用计划任务投递到控制台会话；也可以在交互式桌面启动。
- 无窗口或进程退出时，可检查 Windows 系统日志中的 Service Control Manager 记录，确认 `artifact` 服务及驱动的状态。
- 进程、内存和 GPU 计数只能辅助判断运行状态；画面是否正常仍需在游戏会话中确认。

## 回滚与脚本兼容

- `99-rollback.ps1` 优先使用 `workspace/backups/` 中最近的备份还原注册表；BCD 使用脚本中的固定值；注册表导入也不保证删除新增项，且部分错误不会使脚本返回失败，不能保证恢复为原始状态。Secure Boot 的固件设置需要自行恢复并重启。
- Windows PowerShell 5.1 运行包含中文的脚本时需要正确识别文件编码；本工具包的相应脚本使用 UTF-8 BOM。
- 游戏和驱动的版本、CPU 厂商及配置文件需要匹配，详见 [COMPATIBILITY.md](COMPATIBILITY.md)。
