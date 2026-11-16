# PBZ 配套文件与公开上游的比较

核对日期：2026-11-16。以下是静态比较，没有执行下载的程序，也没有验证不同构建能否在游戏中互换。

## 可以直接取得的文件

本地 `steamclient64.dll` 与 [GBE Fork release-2026_09_16_2](https://github.com/Detanup01/gbe_fork/releases/tag/release-2026_09_16_2) 中的文件完全一致：

- 发行包：`emu-win-release-vs26.7z`，SHA-256 `adca5355d5615d8846eac6379e89730494cfe64131d94c0b1372fcfe46670d9d`。
- 包内路径：`release/steamclient_experimental/steamclient64.dll`。
- 包内文件：22,404,008 B，SHA-256 `844676acebc626f22e4b10c2c143ffb3429c7d9d9213962396e1ab7c0c19150d`。

实际下载、计算发行包哈希并读取包内文件后，文件与本地样本逐字节一致。`steam_settings/steam_appid.txt` 的本地样本为 7 字节，其哈希与 ASCII 内容 `4115450` 相同；其他配置是否需要、应如何配置取决于实际环境。

## SimpleSvm 和 HyperDbg

公开的 [SimpleSvm 源码](https://github.com/tandasat/SimpleSvm/tree/c4a479e0244b5771c0c865f751f97d1b4f27c091)与本地 AMD 驱动包含多个相同的特征日志。上游仓库没有预编译的 `SimpleSvm.sys`；本地样本为 18,600 B，未验证使用上游源码重编译后能否直接替代。

对 [HyperDbg](https://github.com/HyperDbg/HyperDbg/releases) 官方 v0.15 至 v0.25（含 v0.18.1 和 v0.20-beta）发行包的同名文件进行了逐字节比较，本地 `hyperevade.dll`、`hyperhv.dll`、`hyperkd.sys`、`hyperlog.dll` 和 `kdserial.dll` 均未找到完全一致的发行文件，对应 `.text` 段也不同。本地 `hyperhv.dll` 的 294 个导出名中有 272 个与 v0.25 的 296 个导出名相同，说明其与公开项目密切相关；是否能直接替换仍需运行验证。

`hyperlog.inf` 可由 v0.18 发行包的 `release/hyperlog.inf` 精确重建：将 `DriverVer` 中的 `02/15/2026,21.35.3.178` 替换为 `10/28/2026,17.52.34.159` 后，与本地样本逐字节相同，SHA-256 为 `a4d8656225f64646bbe4dce7da160b894d6d3f88c7c8a546d6c581102fbd4546`。该 INF 及其引用的 `hyperlog.sys` / `hyperlog.cat` 是否为实际运行所需尚未确认。

## ColdLoader

[ColdLoader](https://github.com/denuvosanctuary/coldloader) 源码及发行包公开可得。逐项比较 v1.0.0 至 v1.4.0 的正式发行 DLL 后，本地 301524 样本中的 `coldloader.dll`（116,736 B）与这些发行文件均不相同，能否用公开版本替换尚未验证。

上游 v1.4.0 的 DLL 为 205,824 B，完整 SHA-256 为 `49d971ce473e3e91dcb365b088e3a08223107daeda6078afed1cc6400e805e63`，与 [302256 历史记录](HOST-STATE.md)中的大小和哈希前后缀吻合。由于历史记录的哈希被截断且原文件不在本机，尚不能确认两者完全相同。

## 仍需单独确认的文件

`artifact.dll`、`artifact.json` 及加载它的 `winmm.dll` 当前没有核实到匹配本地样本的公开来源；匹配的游戏主程序也未保留。逐文件来源与哈希见 [artifacts.json](../artifacts.json)。
