# AC8 专属或较难获取的文件

此目录保存本方案需要单独准备的文件，或者记录它们的获取链接。当前本地样本包括 `artifact.dll`、`artifact.json` 和用于加载它的 `winmm.dll`；它们应与目标游戏版本配套。逐文件大小、SHA-256 和目标路径见 [artifacts.json](../artifacts.json)。

如果有可用来源，可以填写 [links.md](links.md)，也可以在此目录放 `.url` 链接文件。尚未确认的来源应标为待核实，并同步更新 `artifacts.json`。

此目录下的实体文件和链接均可根据需要纳入 Git；新 clone 能获取其中实际提交的文件或链接。其他位置的 DLL 和 `workspace/` 仍按原规则忽略。
