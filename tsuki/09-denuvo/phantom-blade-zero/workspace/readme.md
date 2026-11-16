# 本地工作区

`samples/ARTIFACT/platform/steam/` 保存其他本机配套样本，专属组件位于上级的 [unique/](../unique/readme.md)。直接运行仓库中的环境脚本时，`state/` 保存其回滚状态；复制到部署根目录运行时，状态则位于部署目录的 `scripts/state/`。这些内容均被 Git 忽略或位于仓库外，需要自行保管。

除本说明外，此目录内容均被 Git 忽略，样本文件和哈希见上级 `artifacts.json`。
