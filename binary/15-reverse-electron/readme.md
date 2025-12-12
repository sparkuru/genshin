# Electron 逆向

Electron 应用逆向分析笔记

- [01-asar.md](./01-asar.md) - asar 解包、分析与重打包
- 02-debug.md - 调试技巧
- 03-protection.md - 代码保护与绕过

Electron 应用特征, 识别 Electron 应用：
- 存在 `resources/app.asar` 或 `resources/app` 目录
- 包含 `electron.exe` 或类似命名的主程序
- `package.json` 中有 electron 依赖

常见目标: VS Code, Discord, Slack, Notion, Postman, 各类基于 Electron 的桌面客户端
