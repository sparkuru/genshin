# Live Subtitle Tool Windows 便携安装方案

本目录参考 `32-pm2` 的独立安装脚本形式，交付安装器、启动脚本、配置模板、官方下载清单和可复用提示词。**不包含、不自动下载、不复制模型**。解压后可在 Windows 10/11 x64 上使用，无需管理员权限。

## 快速安装

双击 `install.bat`，默认安装到安装器旁的 `LiveSubtitle` 目录；也可在普通 PowerShell 中指定目录：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\install-live-subtitle.ps1 -InstallDirectory 'D:\software\live-subtitle'
```

`ExecutionPolicy Bypass` 只作用于本次进程，不修改系统执行策略。安装器不修改全局 PATH、不安装 Python/pip/Conda/CUDA、不安装 Vulkan SDK、不修改 Defender。

软件文件约 141 MiB，首次解压与重打包需要额外临时空间，建议预留 1 GiB（不含模型）。系统需已有支持 Vulkan 的 GPU 驱动。默认按名称匹配 `AMD Radeon RX 9070 XT`，其他显卡需指定名称：

```powershell
.\install.bat -InstallDirectory 'E:\LiveSubtitle' -GpuName 'AMD Radeon RX 7900 XTX'
.\install.bat -InstallDirectory 'E:\LiveSubtitle' -Plan
```

`-Plan` 只显示软件和目标目录，不下载、不写入安装目录。设备枚举失败会中止，保留现有目录，不回退 CPU。名称需出现在 CrispASR 的 Vulkan 枚举中，设备编号不硬编码。

## 模型：自行获取或从已有设备复制

将下面两个文件保持原名放入 `<安装目录>\models\`。安装器没有模型下载选项。完整官方下载地址、固定提交、大小和 SHA256 均在 [assets.json](assets.json)。

| 用途 | 文件 | 官方 GGUF 页面 | 文件大小 |
| --- | --- | --- | --- |
| Qwen3-ASR | `qwen3-asr-1.7b-q4_k.gguf` | [cstr/qwen3-asr-1.7b-GGUF](https://huggingface.co/cstr/qwen3-asr-1.7b-GGUF) | 1,490,915,200 B |
| Hy-MT2 翻译 | `Hy-MT2-1.8B-UD-Q3_K_XL.gguf` | [unsloth/Hy-MT2-1.8B-GGUF](https://huggingface.co/unsloth/Hy-MT2-1.8B-GGUF) | 989,983,712 B |

ASR SHA256：`ec197cef7ccc589fdcae1becc3f4a3de119d0a41e790b898b519b1a048dad8d4`

翻译 SHA256：`bf575b6238c6ae3c35db73af36bc0a749aedf8de17426c1b506e2d332dd9c9ca`

放入后执行校验，再双击 `start.bat`：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File 'D:\software\live-subtitle\app\verify-install.ps1' -CheckModels
```

缺少模型时启动器弹出具体文件名并退出，不自动联网。默认自动检测原文语言、翻译为简体中文、显示原文与译文。首次模型加载需要时间，之后模型保持加载；重新停止/开始字幕会重新建立 ASR 会话，退出则释放模型。

## 架构和固定版本

核验日期：2026-09-27。软件锁定为已实际测试组合，避免上游升级破坏接口。

| 组件 | 版本 | 官方下载 |
| --- | --- | --- |
| Live Subtitle Tool | v2.1 | [live_subtitle.exe](https://github.com/kw4356/Live-subtitle-tool/releases/download/v2.1/live_subtitle.exe) |
| CrispASR | v0.8.37，Windows x86_64 Vulkan build | [Vulkan zip](https://github.com/CrispStrobe/CrispASR/releases/download/v0.8.37/crispasr-windows-x86_64-vulkan.zip) |
| 临时构建 Python | 3.11.9 embeddable x64 | [Python 官方 ZIP](https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip) |
| Microsoft app-local runtime | 14.44.35211.0 | [Microsoft 官方 redist](https://aka.ms/vs/17/release/vc_redist.x64.exe) |

每个软件文件的固定 SHA256 见 `assets.json`，为本次核验的官方来源文件指纹；不代表每个上游都另外发布了 SHA256。Python ZIP 同时与官方发行页 MD5 对照，解释器验证 Python Software Foundation 签名；Microsoft 原包与提取 DLL 验证 Microsoft 签名。Microsoft 地址会更新：若内容变更，安装器拒绝使用；可使用已校验版本的离线缓存，或核验新签名、结构、版本后更新清单并重测，不能跳过校验。

当前仓库主分支仍有旧 Whisper 代码；v2.1 Release 已接入 CrispASR。安装器使用 Release EXE 内置 Python 3.11、Qt 和 llama-cpp-python Vulkan 库，**不运行仓库旧 Python 入口，不下载独立 whisper-vulkan**。CrispASR 官方 ZIP 中存在 `whisper.dll`，属于上游同一构建内部组件。

`payload/app/portable.py` 是本次部署保留的本地适配层：处理 CrispASR 新版 stream JSON、整句最终结果、字幕去重、上下文翻译、WASAPI、GPU 选择和本地路径。`build-portable.py` 校验官方 EXE 精确哈希后，仅替换 PyInstaller 入口，产出 `LiveSubtitle.exe`；原版 `live_subtitle.exe` 保留。**适配后的 EXE 是本地生成文件，不是官方 standalone Release**。

Python embeddable 只在安装临时目录执行标准库构建与 CAB 提取，完成后删除解释器；运行时使用 EXE 自带运行环境。Microsoft redist 只作为数据提取九个已验签 DLL 和许可证，不运行 EXE/MSI，不登记系统安装。构建工具不成为最终运行依赖。

## GPU、音频和性能

ASR 固定 `--gpu-backend vulkan -dev 0`，先枚举物理设备、按名称匹配，再设置进程级 `GGML_VK_VISIBLE_DEVICES`；筛选后的设备编号为 0。翻译采用 `n_gpu_layers=-1`、同一 Vulkan 设备，不配置 CUDA。

默认 WASAPI Loopback 捕获 Windows 默认播放设备，可在界面选择耳机、扬声器、HDMI、USB DAC 等枚举到的输出；默认模式每 3 秒检查系统设备切换。不要求 Stereo Mix。

配置位于 `config/settings.json`，模型为相对路径。实时默认值：ASR 步长 1500 ms、窗口 12000 ms、静音终句 700 ms、WebRTC VAD、最长语句 20 s；翻译上下文 2 句、context 2048、batch 512、输出最多 384 token、temperature 0.1、线程 8。接收音频、重采样和 UI 仍使用 CPU，识别和翻译计算使用 GPU。

## 在其他设备复用、离线安装

已经准备好模型后，关闭软件，复制**整个安装目录**到另一盘符/Windows PC，直接双击 `start.bat`。启动脚本用 `%~dp0`，程序路径根据 EXE 所在目录计算。目标电脑仍需兼容的 x64 CPU、Windows 系统组件和 GPU 驱动；不同型号显卡修改 `config/settings.json` 的 `gpu_name`。音频设备名称不同则恢复 `audio_device` 为 `default`。

只有安装器包时，首次运行联网下载四个软件文件。安装后 `cache/downloads` 留下四个已校验原始软件文件，可复制到另一设备作为离线缓存（无模型）：

```powershell
.\install.bat -InstallDirectory 'E:\LiveSubtitle' -CacheDirectory 'E:\software-cache' -Offline
```

缓存目录需包含 `live_subtitle.exe`、`crispasr-windows-x86_64-vulkan.zip`、`python-3.11.9-embed-amd64.zip`、`vc_redist.x64.exe`。安装器读取缓存，不改动它。缺少文件或哈希错误时退出。安装目录必须为空/新建，或由本版本安装器管理；重复安装只校验程序文件，保留配置和模型，不静默升级，也不接管先前手工部署的目录。

安装成功后 `cache/downloads` 可以删除以节省空间，但先保留副本才能再次离线安装。

## 运行目录与启动脚本

```text
LiveSubtitle/
  LiveSubtitle.exe           本地适配入口
  live_subtitle.exe          官方原版，留作构建来源
  start.bat
  start-debug.bat
  INSTALL.md
  .live-subtitle-portable.json
  app/                      适配源代码、校验脚本、调试脚本、英语测试音频
  CrispASR/                 官方 Vulkan EXE/DLL、app-local Microsoft DLL、许可证
  models/                   安装时为空；自行放入两个 GGUF
  config/                   settings.json、assets.json
  cache/downloads/          四个软件安装源文件
  logs/                     枚举、运行、验收日志
  temp/                     PyInstaller 解包等运行临时文件
```

`start.bat`：

```bat
@echo off
setlocal
cd /d "%~dp0"
set "TEMP=%~dp0temp"
set "TMP=%~dp0temp"
set "CRISPASR_CACHE_DIR=%~dp0cache\crispasr"
start "" "%~dp0LiveSubtitle.exe" %*
endlocal
```

`start-debug.bat`：

```bat
@echo off
setlocal
cd /d "%~dp0"
set "TEMP=%~dp0temp"
set "TMP=%~dp0temp"
set "CRISPASR_CACHE_DIR=%~dp0cache\crispasr"
"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy Bypass -File "%~dp0app\debug-launch.ps1" %*
echo.
echo Live Subtitle exited. Logs: "%~dp0logs"
pause
endlocal
```

## 检查与英语测试

安装器先校验程序文件，再执行 CrispASR `--diagnostics`，确认 Vulkan 列出指定显卡。**枚举成功不等于两模型已经 GPU 推理**。模型放入后，双击 `start-debug.bat`、播放英语视频，查看 `logs/live-subtitle.log`：

- 显示 `GPU backend: Vulkan` 和目标 GPU 名称。
- CrispASR 显示 Vulkan 后端和模型初始化成功。
- llama.cpp 显示所有翻译层 `offloaded` 和 Vulkan buffer 分配。
- 中文字幕出现，任务管理器 GPU 专用显存有占用，软件关闭后无所属 CrispASR 残留。

也可运行 `start-debug.bat -SelfTest`，内置 JFK 英语 WAV 通过真实系统输出播放，再由 WASAPI 捕获；请暂停其他声音。完成后生成 `logs/validation.json`、`logs/subtitle-test.png`。该测试会切换音频选择项然后恢复默认设备；需人工检查 `errors` 为空、`child_process_closed=true`、最终文本和翻译，不能仅凭程序退出判定通过。内置音频来自 [whisper.cpp 官方 samples/jfk.wav](https://github.com/ggml-org/whisper.cpp/blob/master/samples/jfk.wav)，测试音频不参与识别模型加载。

本机原部署已验证 RX 9070 XT、双模型 Vulkan、英语视频 Loopback、双语字幕和跨盘复制。该结果仅说明原部署的验证情况，不保证另一台设备；**安装器本轮未下载模型，也未进行双模型推理**，详见 `VALIDATION.md`。

## Portable 范围、升级和卸载

应用配置、日志、模型、CrispASR 缓存与临时解包均在安装目录。只有实际使用的 `TEMP`、`TMP`、`CRISPASR_CACHE_DIR` 被设置，变量仅影响启动进程及子进程。没有机械设置 Hugging Face、pip、XDG 缓存变量。

Windows 的系统 DLL、Media Foundation、PowerShell、Vulkan ICD 和显卡驱动是系统依赖；AMD 驱动自身着色器缓存、Windows Prefetch/事件和 Defender 记录可能写入 AppData/系统目录。这些是操作系统/驱动管理的数据，不能承诺零系统痕迹。

升级程序：先检查官方 [Live Subtitle Releases](https://github.com/kw4356/Live-subtitle-tool/releases) 和 [CrispASR Releases](https://github.com/CrispStrobe/CrispASR/releases)，复核入口、Python 版本、stream JSON 和 GPU 后端兼容性，更新版本清单、构建脚本的官方哈希和适配层，然后装入**新目录**验证。v2.1 构建入口有精确哈希限制，不能仅替换 EXE。

升级模型：核对模型兼容性和作者许可，把新 GGUF 放入 `models`，修改配置的相对路径；需同步更新 `assets.json` 的文件名、提交、大小、SHA256，才能用于 `-CheckModels` 校验。保留旧模型至新模型验证通过。

彻底卸载：关闭软件并确认其子进程退出，删除整个安装目录和不再需要的安装器/离线缓存即可。没有服务、注册表、PATH 或系统 Python 需要撤销；系统管理的历史记录不会由卸载脚本清除。

## 文件索引与提示词

- `install-live-subtitle.ps1`：Windows 参数化安装器；`install.bat` 为双击入口。
- `verify-install.ps1`：文件 SHA256、Vulkan 枚举、可选模型校验，安装后复制至 `app`。
- `assets.json`：官方下载 URL、版本、模型链接和哈希。
- `payload/`：启动脚本、配置模板、运行适配代码、测试音频。
- `tools/extract-msvc.py`：Microsoft CAB 数据提取，不执行安装程序。
- `prompts/original.txt`：用户原始提示词的原样副本，保留原文中的 `RTX 9070XT` 笔误。
- `prompts/reuse.txt`：已修正 AMD 型号并加入“不下载模型”优先规则的复用提示词。
- `VALIDATION.md`：本安装器的测试结果、原部署证据边界。
- `package-files.sha256`：安装器包文件清单，非官方签名；用于复制后的完整性对照。

本地适配源文件没有附带上游主程序源码或 EXE；安装器从官方 Release 获取，保留 EXE 中已有许可。CrispASR ZIP 的 LICENSE/THIRD_PARTY_NOTICES 随程序保留，Microsoft app-local DLL 带其运行库许可；使用者仍需遵守程序和各模型的授权条款。
