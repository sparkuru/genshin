# AC8 配套文件与公开上游的比较

核对日期：2026-11-16。以下是静态比较，没有执行下载的程序，也没有验证不同构建能否在游戏中互换。

## SimpleSvm

公开的 [SimpleSvm 源码](https://github.com/tandasat/SimpleSvm/tree/c4a479e0244b5771c0c865f751f97d1b4f27c091)在本次检出时的提交为 `c4a479e0244b5771c0c865f751f97d1b4f27c091`。本地 AMD 驱动中有多个与上游源码相同的特征日志，例如 `SVM is not fully supported on this processor.`，说明两者有明确关联。

上游仓库包含源码，但没有预编译的 `SimpleSvm.sys`。本地样本是 18,088 B，未在 Windows/WDK 中重新编译上游源码，也未验证重新编译的驱动能否替代样本。文件不同不意味着上游源码不可公开获取。

## HyperDbg

下载并核验了官方 v0.15、v0.16、v0.17、v0.18、v0.18.1、v0.19、v0.20-beta、v0.21、v0.22、v0.23、v0.24 和 v0.25 发行包。对包内同名文件逐字节比对后，下面的本地文件没有完全相同的发行文件；对应可执行代码段 `.text` 也没有完全相同的版本：

| 文件 | 本地大小 | v0.25 对应文件大小 |
|---|---:|---:|
| `hyperevade.dll` | 6,256 B | 6,144 B |
| `hyperhv.dll` | 551,080 B | 553,984 B |
| `hyperkd.sys` | 11,376 B | 140,608 B |
| `hyperlog.dll` | 13,992 B | 17,408 B |
| `kdserial.dll` | 30,984 B | 33,792 B |

本地 `hyperhv.dll` 的 292 个导出名中，有 272 个也出现在 v0.25 的 296 个导出名中，表明其与公开的 [HyperDbg](https://github.com/HyperDbg/HyperDbg) 存在密切关联。上述差异可能与版本、构建方式或改动有关；仅凭本次比较不能判断公开版本是否满足本方案的驱动协议。

`hyperlog.inf` 可以从公开版本精确重建：[v0.18 发行包](https://github.com/HyperDbg/HyperDbg/releases/tag/v0.18)内的 `release/hyperlog.inf` 只需把 `DriverVer` 中的 `02/15/2026,21.35.3.178` 改为 `09/24/2026,19.0.10.717`，结果与本地样本逐字节相同，SHA-256 为 `6692f919985e98bb9d35288ccddb8894b99cc30131bc565c217fcf0a389e7d66`。该文件和它引用的 `hyperlog.sys` / `hyperlog.cat` 是否为本方案实际运行所需，尚未确认。

## 仍需单独确认的文件

`artifact.dll`、`artifact.json` 和用于加载它的 `winmm.dll` 当前没有核实到匹配本地样本的公开来源；配套游戏主程序也未保留。它们与目标版本的关系见 [兼容性说明](COMPATIBILITY.md)，逐文件来源与哈希见 [artifacts.json](../artifacts.json)。
