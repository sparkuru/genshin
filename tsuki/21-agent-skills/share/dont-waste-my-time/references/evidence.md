# 证据与编排记录格式

## 固定约定

- 时间：各 P 独立从原视频起点计秒，浮点秒用于 JSON，正文标注 P 号与 `mm:ss`。不能把 P2 的 00:10 误指向 P1。
- 原始：平台 `.raw.json`、ASR 各块的 `raw_segments`、OCR TSV 不回写编辑后的文字。
- 字幕统一轨：`{kind, part, segments: [{id, start, end, text, ...}]}`。ASR 还保留 words、块偏移、模型快照与原始段 ID。
- 来源：`meta.json` 保存可交付的源身份、选择范围、实际媒体参数和处理版本，不保存 Cookie、完整播放器 API 响应或临时签名下载链接。
- 时间轴：`evidence/pNNN-timeline.json` 的每行保留所选轨原文、重叠 ASR 段 ID、最近粗采样帧及其实际时刻。不进行无来源的自动“纠错融合”。
- 资源：报告位于 `markdown/report.md`，原图用 `../assets/文件.jpg`，视频用 `../video/part-001.mp4#t=20`。PNG/JPG 图片必须来自已记录的 `frame` 提取。

`media` 的完整解码证据保存输入哈希、实际命令和成功退出状态。`state.json` 记录输入/参数/镜像指纹、完成产物哈希和阶段状态，位于 bundle 外。`manifest.json` 覆盖 bundle 文件，排除清单本身。

## editorial-review.json

这个文件由 agent 在阅读证据后编写，不能通过把初始字段全部设为 true 代替审读。下面是**单 P、60 秒、有 ASR、有一张关键帧**的格式示例；实际时长、文字、文件名和判断必须来自当前材料。所有路径相对 bundle。

```json
{
  "reviewed_by": "agent",
  "intent": "保留作者对该主题的解释与适用条件",
  "scope": "仅处理用户指定的第 1 P，报告未覆盖其他 P",
  "parts": [
    {
      "part": 1,
      "subtitle_assessment": {
        "observed_status": "none",
        "chosen_track": "transcripts/p001-asr.json",
        "reason": "已检查实际字幕库存；使用独立语音识别并复核关键画面文字"
      },
      "asr": {"decision": "run", "reason": "没有可用文本字幕"},
      "visuals": {"decision": "run", "reason": "图表承载主要论据"},
      "coverage": [
        {"start": 0, "end": 50, "topic": "问题、解释及条件", "treatment": "included", "reason": "构成论证主线"},
        {"start": 50, "end": 60, "topic": "重复与结束语", "treatment": "omitted", "reason": "不新增实质信息"}
      ]
    }
  ],
  "figures": [
    {
      "asset": "assets/p001-t0000020000.jpg",
      "part": 1,
      "time_seconds": 20,
      "caption": "图 1 · P1 00:20：作者展示的比较图",
      "purpose": "保留解释所依赖的图示及文字",
      "visually_reviewed": true
    }
  ],
  "edits": [
    {
      "id": "E1",
      "kind": "ambiguity",
      "material": true,
      "part": 1,
      "start": 20,
      "end": 25,
      "original": "来自实际源轨道的原始文字",
      "processed": "处理后的表述或尚未消歧的候选",
      "reason": "说明判断依据与残留不确定性",
      "source": "transcripts/p001-asr.json",
      "segment_ids": ["asr-p001-s3"]
    }
  ],
  "skills": [],
  "limitations": ["保留机器识别记录，未做全片逐字人工听校"]
}
```

### 字段规则

`parts` 覆盖所有实际 selected_parts。observed_status 必须等于 meta 中的字幕可用性状态，chosen_track 必须等于最终时间轴主轨；视觉主轨用 null。ASR 与画面决定使用 run/skip，附具体理由。run 时必须有实际产物。visuals 表示是否运行粗采样/截图/OCR链，粗采样做过就写 run，即使没有正文配图。skip 必须说明已有实际画面评估依据或用户明确要求，不表示“无需判断画面”。

平台字幕质量足够、抽样发现画面无实质信息时，可记录 `asr: {decision: "skip", reason: "..."}`、`visuals: {decision: "run", reason: "已查看粗采样，画面仅为重复背景，不选入正文"}`、`figures: []`，chosen_track 指实际平台轨。不能为了无图而把已运行的粗采样改记为 skip。

`coverage` 以不留未说明时间空洞的区间覆盖每个已选 P。处理方式为 included、condensed 或 omitted，所有取舍都附 topic 与 reason。它是审读记录，不是自动证明内容理解正确的证书。

`figures` 一一对应 Markdown 实际采用的图片，caption 必须出现在最终 Markdown；文件、源哈希、时刻与 `frame` 产生的同名 evidence JSON 一致。脚本核验一致性，agent 查看实际画面。允许不配图，此时 figures 为空并记录跳过原因。

`edits` 记录关键修订与歧义。source 指实际 JSON 证据；若源是字幕/ASR，应列真实 segment_ids，original 必须能从其原文找到。对原始 OCR 可指向包含该文字的帧证据 JSON 并省略 segment_ids。material 缺省为 true，这类记录的 id、original、processed 都必须出现在最终 Markdown 的溯源表或脚注中。不能将仍可能关键的修改改成 material=false 来绕过呈现。

`skills` 可记录 `{name, purpose, source, added_interpretation}`；可选联动不构成必需依赖。`limitations` 记录真实限制，重要限制同时写进报告；不能把缺失交付物藏在这里当成完成。

## 验证与完成的区别

`verify` 检查真实文件、时间界限、引用关系、原文可定位性、图片来源、覆盖记录和导出一致性，成功写入 `evidence/validation.json` 与 `manifest.json`。验证器还不能证明：所选内容是否代表全片、原文是否被听对、作者观点是否正确、截图是否最有价值、报告是否忠实。最终语义审读仍属于 agent 的工作。

不要手写通过结果、伪造解码退出状态或凭一个成功的 `prepare` 就声称 ASR/报告已经可用。修改源、轨道、正文、图片或样式后重新执行受影响阶段、导出与验证。
