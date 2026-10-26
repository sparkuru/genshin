# 运行、初始化与恢复

以下 `skill_dir` 指本 Skill 的绝对目录，`job_dir` 指 `init` 返回的实际私有目录。命令不依赖调用时 CWD，不覆盖 HOME 等系统变量。

## 初始化

```bash
skill_dir=/absolute/dont-waste-my-time
python3 "$skill_dir/scripts/dwmt.py" init --url 'https://www.bilibili.com/video/BVxxxxxxxxxx/'
# Save the returned path, then let the user fill its credentials.env.
job_dir=/tmp/dont-waste-my-time.ACTUAL_JOB
python3 "$skill_dir/scripts/dwmt.py" prepare --job "$job_dir"
```

本地输入：`init --video /absolute/input.mp4`。可选参数：`--cookie-file` 为用户明确提供的 `.env`；`--reference-docx` 为参考文档；`--cache` 为已有 `/tmp` 专用模型缓存根目录，不能是整个 `/tmp`。宿主机 Python 仅使用标准库，不需要 uv/pip。当前已实现 Linux/Unix 宿主机与本地 Unix Docker endpoint，不将本地 job 路径错误地绑定到远程 daemon。其他架构与宿主平台需实际构建和探针验证。运行时不修改 Skill，也不建立项目内 venv。

`prepare` 使用 `docker/requirements.lock`、Dockerfile、代码和 assets 的内容指纹命名镜像，构建日志位于 bundle 的 `logs/`。基础 Python 镜像固定摘要，Python 依赖固定版本，Debian 包的实际版本以工具探针为准；apt 仓库不是历史快照，不能声称跨时间构建逐字节相同。

| 观察 | 处理 |
|---|---|
| Docker/Compose、镜像和探针正常 | 直接复用 |
| 镜像不存在 | 在已授权初始化范围内构建本 Skill 配方 |
| 只有选定 ASR 模型缺失 | 运行 `models --model ...`；无需重建工具镜像 |
| Docker socket 被沙箱拒绝 | 走客户端既有审批机制重试原探针；不改组权限或 socket 权限 |
| Docker/Compose 缺失或 daemon 不可用 | 说明具体缺失层；主机安装/服务变更需要相应授权，不能冒充视频或 Cookie 失败 |
| 构建或模型下载失败 | 保存退出状态与脱敏日志，修复明确原因后续跑；不无依据切换镜像源 |

Compose 无常驻业务服务、开放端口或数据库；三个入口复用一套工具镜像。处理器断网；获取服务独占 Cookie 文件；模型服务没有 Cookie 和本地输入挂载。默认缓存为 `/tmp/dwmt-model-cache-UID`。

## 获取与检查

用户确认 Cookie 已填写或明确提供已有凭据后：

```bash
python3 "$skill_dir/scripts/dwmt.py" run --job "$job_dir" -- inspect
# Read work/bundle/evidence/source-inventory.json before choosing parts.
python3 "$skill_dir/scripts/dwmt.py" run --job "$job_dir" -- fetch
python3 "$skill_dir/scripts/dwmt.py" run --job "$job_dir" -- probe --part 1
```

默认 `fetch --parts requested`：若 URL 带 `p=`，仅取该 P；否则取 inventory 中所有 P。也可明确传 `--parts all` 或 `--parts 1,3`。逐 P 执行后续处理，不要自动把编号 1 当作用户指定的视频。下载请求画质代码默认 80，但实际分辨率以 FFprobe 为准。

本地视频不运行网络 `inspect`，直接 `fetch`、`probe`。`probe` 不全片解码，只观察流；`media` 才完整解码、提取音频并提取内嵌文本字幕。内嵌图像字幕需要截图/OCR或其他明确工具，不能由提取文本失败推出“没有字幕”。烧录字幕不在字幕轨清单中，必须查看画面。

```bash
python3 "$skill_dir/scripts/dwmt.py" run --job "$job_dir" -- media --part 1
# If multiple audio streams were observed, choose their actual index:
# ... -- media --part 1 --audio-stream 2
```

API 返回无字幕为 `none`；请求失败为 `error`；本地内嵌字幕为 `embedded`；有平台字幕为 `available`。这些是可用性事实，字幕质量由 agent 阅读判断。`media` 后检查 `meta.json` 中 `tracks` 的实际路径。

## 识别与画面

需要 ASR 时才准备模型：

```bash
python3 "$skill_dir/scripts/dwmt.py" run --job "$job_dir" -- models --model small
python3 "$skill_dir/scripts/dwmt.py" run --job "$job_dir" -- asr --part 1 --model small --language zh
```

模型可选 tiny/base/small/medium/large-v3，结合语言、音质、术语和资源决定。CPU/int8 为当前实现，不宣称自动使用 GPU。`--language` 缺省时由模型检测。保留原始分块段、逐词时间、模型摘要和快照 ID。

默认每 300 秒保存一个完成块，可用 `--chunk-seconds 10..1800` 调整。按实际抽取音轨时长分块，不用可能更长的视频容器时长创建空尾块；不足一秒的末块并入上一块。音频使用 source-relative 时间并保留开头静音，词级时间再加块偏移。阶段复用核对输入字节、参数、镜像 ID和产物哈希；完整块可复用，中断中的块重算。分块边界可能切断口语，重要边界需对照原视频，必要时换更长分块重跑；不能宣称无损的逐词人工对齐。ASR 没有识别到语音时保留空结果，不能用空轨作为正文主轨；可结合可用字幕或有依据的视觉主轨继续。

```bash
python3 "$skill_dir/scripts/dwmt.py" run --job "$job_dir" -- frames --part 1 --interval 20 --ocr
# Inspect inventories and contact sheets; labels are frame indices.
python3 "$skill_dir/scripts/dwmt.py" run --job "$job_dir" -- frame --part 1 --time 42.5 --ocr
```

粗采样及 OCR 在 `evidence/frames/`；选定关键帧在 `assets/`，时刻、源视频哈希和截图哈希在同名 evidence JSON。以实际视频流区间采样，音轨可能比画面更长；时间轴保留真实最近帧时刻，不把最后画面延长到音轨结尾。Tesseract 默认中英文，置信度原样保存，不作为经过校准的“正确概率”。粗采样超过 1000 帧会要求提高间隔，再针对重点补帧；不会静默截掉后半部分。

## 时间对齐、编排与导出

```bash
# Choose an actual track after reviewing its quality:
python3 "$skill_dir/scripts/dwmt.py" run --job "$job_dir" -- index --part 1 --track transcripts/p001-asr.json
# For a justified visual-only source:
# ... -- index --part 1 --visual-only
```

若只有一条平台/内嵌轨可以省略 `--track`；没有这类轨但已有 ASR 时使用 ASR。有多条字幕时需显式选择。默认选轨只是工具便利，不能替代质量判断。帧关联保留“最近帧实际时刻”，不声称与字幕严格同步。

阅读完整 `transcripts/pNNN-timed.md` 及相关原始材料，按 [编排规则](editorial.md) 和 [格式](evidence.md) 写 `markdown/report.md`、`evidence/editorial-review.json`。所有编辑都在 `/tmp` 中。

```bash
python3 "$skill_dir/scripts/dwmt.py" run --job "$job_dir" -- export
python3 "$skill_dir/scripts/dwmt.py" run --job "$job_dir" -- verify
```

```text
JOB/
  credentials.env             # Private; never deliver
  job.json                    # Host paths; never deliver
  input/                      # Explicit staged inputs
  work/
    audio/                    # Recognition intermediates
    state.json                # Checkpoints; not proof of a live process
    bundle/                   # Deliver this entire directory
      video/part-001.mp4
      markdown/report.md
      docx/report.docx
      assets/
      transcripts/
      evidence/editorial-review.json
      evidence/validation.json
      meta.json
      logs/
      report.html
      manifest.json
```

保持整个 bundle 相对结构以保留 Markdown 链接。HTML 内嵌图片并修正为 bundle 根目录下的本地链接。DOCX 内嵌图片，但外部材料链接不保证跨 Word 应用保持可点击，仍以 bundle 和 Markdown 溯源为准。

`verify` 通过后生成 SHA-256 清单。最终校验的宿主机调度日志放在 bundle 外，避免校验后继续改变被哈希的日志。后续修改需重新导出/校验；检查状态不会改变已封存的 bundle。

## 继续、重试与清理

```bash
python3 "$skill_dir/scripts/dwmt.py" status --job "$job_dir"
```

该命令同时报告记录状态与当前 Docker 容器观察；观察失败时明确为未验证。一次 running 记录、日志静止或观察超时不能证明进程停止。保持原工具会话/容器句柄，检查同一任务，再决定是否重试。

失败后重执行相同阶段，会复用匹配输入和产物；`--force` 显式重算。默认一项任务一次只运行一个写阶段；锁竞争返回 2，不会并发改坏状态。

不默认清理视频、失败证据、Cookie 或共享缓存。交付时报告 bundle、凭据和缓存路径，以及 `/tmp` 可能被系统清理的事实。用户要求清理时只处理确认归属本任务的具体路径，不执行全局 `docker prune` 或扫描其他 Cookie。
