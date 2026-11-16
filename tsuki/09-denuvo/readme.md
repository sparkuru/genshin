本目录按游戏或目标分别保存环境脚本、实现说明和文件来源。现有脚本负责准备和检查运行环境；各方案依赖的版本专用组件并不由这些脚本生成。

每个方案使用相同的顶层结构：

```text
<solution>/
├── readme.md             目录、实现、使用方法和已知限制
├── artifacts.json        所需文件、本地哈希、来源与匹配状态
├── unique/               方案专属或较难获取的文件及获取链接
├── scripts/              可执行入口和研究脚本
├── lib/                  本方案内部可复用代码
├── docs/                 详细过程、版本和历史证据
└── workspace/            样本、日志、状态和本地归档；内容不提交
    └── readme.md         工作区说明，可提交
```

方案目录中的 `readme.md` 是入口；

`artifacts.json` 按文件记录目标路径、样本位置、大小和 SHA-256，并单独记录商店、源码或发行包的 URL。

`unique/` 用于保存该方案独有或难以公开获取的文件，也可在其中的 `links.md` 记录获取链接。

未验证的来源关系保持 `unverified`，不得当作已验证的下载依赖。清单格式见 [模板说明](template/readme.md)，并可用 [JSON Schema](artifacts.schema.json) 校验。

`unique/` 内的实体文件和链接均可纳入 Git；其他位置的二进制及 `workspace/` 仍按原规则忽略。

新 clone 能获取其中实际提交的文件或链接。

新增方案时复制 `template/`，填写 README 和 `artifacts.json`，将正式入口放入 `scripts/`、公用代码放入 `lib/`，将其他样本和运行数据放入 `workspace/`。

## entry

- [ACE COMBAT 8](ace-combat-8/readme.md)
- [Phantom Blade Zero](phantom-blade-zero/readme.md)
- [新方案模板](template/readme.md)

## resources

1. fitgirl.site
2. gamer520.com
