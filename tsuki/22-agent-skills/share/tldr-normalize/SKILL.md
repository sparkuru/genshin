---
name: tldr-normalize
description: "Normalizes *.tldr TOML files: fixes file structure order, removes redundant fields, standardizes placeholder syntax, and rewrites Chinese descriptions. Use when the user wants to clean up, fix, or 规范化 a .tldr file."
---

# tldr-normalize

收到目标文件路径后，立即执行规范化并覆盖写回文件。不询问、不逐字段解释，完成后输出 diff 摘要即可。

## .tldr 文件格式规范

解析器读取两个独立区块，渲染时分开展示：

- **`[[hit]]`**：用户个人速查条目，渲染在 `hit:` 区块下。字段：`command`、`description`
- **`[[examples]]`**：结构化官方示例，渲染在 `usage:` 区块下。字段：`title`、`command`、`description`
- `examples` 字段必须存在（缺失触发 Warning），为空时写 `examples = []`

标准结构（字段顺序固定）：

```toml
[meta]
name = "command-name"
description = "中文一句话描述工具用途"
url = "https://..."

examples = []

[[hit]]
command = "command <placeholder>"
description = "中文描述这条命令做什么"

# 若有官方示例：
[[examples]]
title = "示例标题"
command = "command --option <value>"
description = "可选补充说明"
```

## 需要修复的问题

**结构顺序：**
- `[meta]` 必须在文件最前面
- `examples = []`（或 `[[examples]]` 条目）紧随其后，不可删除
- `[[hit]]` 条目最后

**占位符格式（`command` 字段）：**

| 错误写法 | 正确写法 |
|---------|---------|
| `<wifi interface name>` | `<interface>` |
| `<ap name>` | `<ssid>` |
| `<"password">` | `<password>` |
| `<hacker host>` | `<host>` |
| `<con name>` | `<connection_name>` |

规则：
- 只用 `<snake_case>` 风格，无空格，无引号
- 名称尽量简短且语义明确
- 若命令中已有清晰上下文（如 `-u http://...`），占位符可以带前缀路径，如 `http://<host>:<port>`

**`meta.description` 字段：**
- 禁止使用 `"Quick reference for xxx"` 这类无意义占位文字
- 改写为中文，一句话说明这个工具是什么、用来做什么
- 格式：`用于 [做什么] 的 [类型] 工具` 或直接描述功能

**`[[hit]]` 的 `description` 字段：**
- 中文，动词开头
- 简洁说明这条命令的意图，不超过 20 字
- 不重复命令名本身（命令已经在 `command` 字段中）

**`meta.url` 字段：**
- 若为空且工具有 man page，填入 `https://man7.org/linux/man-pages/man8/<name>.8.html`（按实际 section 调整）
- 若无标准 man page，保留空字符串 `""`

## 处理流程

1. 读取目标 `.tldr` 文件
2. 解析 TOML 结构
3. 按上述规则逐项修正
4. 重新序列化为 TOML，字段顺序：`[meta]` → `[[hit]]` 条目
5. 覆盖写回原文件
6. 输出修改摘要（改了哪些字段、改了几处占位符）

## 示例

修复前：
```toml
examples = []
[[hit]]
command = "nmcli dev wifi hotspot ifname <wifi interface name> ssid <ap name> password <\"password\">"
description = "用 nmcli 起一个移动共享热点"

[meta]
name = "nmcli"
description = "Quick reference for nmcli"
url = ""
```

修复后：
```toml
[meta]
name = "nmcli"
description = "用于管理 NetworkManager 网络连接的命令行工具"
url = "https://man7.org/linux/man-pages/man1/nmcli.1.html"

examples = []

[[hit]]
command = "nmcli dev wifi hotspot ifname <interface> ssid <ssid> password <password>"
description = "创建 Wi-Fi 热点"
```
