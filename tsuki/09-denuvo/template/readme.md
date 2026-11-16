# <方案名称>

复制整个 `template/` 为新的方案目录，将本文件中的占位说明替换为事实，并填写 [artifacts.json](artifacts.json)。保留不存在或尚未验证的信息为“未知”，不要用同名文件推断版本、来源或兼容性。

## 目录

```text
<solution>/
├── readme.md         本方案入口和使用说明
├── artifacts.json    文件与来源清单
├── unique/           专属或难以公开获取的文件及获取链接
├── scripts/          本方案可执行入口
├── lib/              本方案公共代码；没有则保留空目录
├── docs/             详细分析、操作过程、历史版本
└── workspace/        本地样本、运行状态、日志和临时归档
```

`workspace/readme.md` 可提交，其余 `workspace/` 内容由根目录 `.gitignore` 忽略。`unique/` 中的实体文件和链接均可根据需要纳入 Git，见 [unique/readme.md](unique/readme.md)。运行时的备份及用于回滚的状态需要按实际情况另行保存。

## 实现方案

- 目标与运行环境：<填写系统、目标程序、适用版本和前提>。
- 实现边界：<说明脚本实际负责什么，哪些组件需要外部提供>。
- 入口与流程：<列出脚本名称、参数、执行目录、输出和回滚方式>。
- 已知限制：<说明未经验证的步骤、版本约束与真实存在的问题>。

## 所需文件及目录

填写运行目录示例、程序与版本专用文件；区分必需、条件必需和尚不确定的文件。大小使用字节，哈希使用完整 SHA-256。逐项信息写入 `artifacts.json`，专属或较难获取的文件及链接放在 `unique/`。

## 独有文件

说明本方案需要自行保存、无法由脚本生成或不能直接从通用上游替换的文件；记录它们与程序版本、配置及 CPU 等条件的关系。不要因为文件名相同就认为不同方案的文件相同。

## 第三方链接

列出具体商店页面、项目源码或发行文件，并说明链接对应什么。给出压缩包哈希时，明确该哈希属于压缩包本身，不能当作解压后文件的哈希。

## 清单字段

[根目录的 JSON Schema](../artifacts.schema.json)定义通用格式。`artifacts.json` 包含：

- `project`：目录名风格的方案标识；`sample_version`：样本版本或未知说明。
- `target_base`：相对于目标部署根目录的文件基准目录；`target_path` 相对于该基准目录。
- `local_path`：相对于方案目录的本地样本路径；文件不存在或未保存时使用 `null`。
- `size_bytes` 和 `sha256`：实际文件的字节数与完整哈希，未知时使用 `null`。
- `group`：例如 `game`、`common`、`amd`、`intel` 或 `sample-config`；`necessity` 使用 `required`、`conditional`、`optional`、`unknown` 中的事实状态。
- `sources`：每个来源的 `id`、URL、类型、文件名、哈希及哈希依据；商店页面、源码页面和发行下载要区分。
- `source_refs`：逐文件关联来源，并为每一对文件和来源分别记录 `match_status`。仅在实际核对对应文件完整哈希一致后标记 `matched`；压缩包还应填写准确的 `archive_member`。其余保持 `unverified`。

空模板的 `artifacts` 和 `sources` 数组可以为空；新增记录时可参考已有方案的 `artifacts.json`。`null` 表示未知或不适用，不表示文件可以省略。

## 使用与验证

<填写可复制的命令、工作目录、参数和状态位置。记录实际执行过的验证、系统版本、结果以及尚未验证的部分。>
