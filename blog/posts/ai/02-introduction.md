---
title: "artificial-intelligence-intro"
description: "多学点热门技术，总会有用得上的地方的（"
date: "2024-02-18T00:35:00.000Z"
updated: "2024-12-12T08:23:47.000Z"
tags: []
draft: false
layout: "post"
slug: "introduction"
---

## artificial-intelligence-intro

>   Dare to create intelligence, are you the creator？

| 概念             | 核心作用                           | 设备诊断例子            |
| ---------------- | ---------------------------------- | ----------------------- |
| Model            | 推理大脑                           | GPT / Claude            |
| Prompt           | 告诉模型当前怎么做                 | “你是设备诊断专家……”    |
| Context          | 模型本轮实际看到的全部东西         | 问题+手册+趋势+Tool结果 |
| Tool             | 一个可执行能力                     | `get_alarm_history()`   |
| Function Calling | 模型表达“我要调用某工具”的机制     | 输出 Tool name + args   |
| MCP              | AI 与外部能力连接的标准协议        | Historian MCP           |
| Skill            | 专业知识/SOP/脚本能力包            | 变频器诊断 Skill        |
| RAG              | 从大量资料中找相关内容放入 Context | 搜索厂家手册            |
| Memory           | 跨轮次/跨任务保存状态              | 记住设备 ID、历史诊断   |
| Agent            | 能自主选择步骤和工具的模型系统     | 故障诊断 Agent          |
| Workflow         | 代码预先规定执行路径               | A→B→C固定流程           |
| Guardrail        | 限制允许做什么                     | 禁止直接写 PLC          |
| Sandbox          | 隔离执行代码/文件                  | Python 分析在容器执行   |
| Harness          | 控制 Agent 整体运行                | Loop、权限、状态、重试  |
| Trace            | 记录 Agent 整个执行轨迹            | 为什么调用某工具        |
| Eval             | 测试 Agent 到底好不好              | 100 个历史故障案例      |
| Handoff          | 一个 Agent 把任务交给另一个        | 电气 Agent → 机械 Agent |
