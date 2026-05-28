# llm workflow with trellis

trellis templates' workflow: https://github.com/mindfold-ai/Trellis.git

> trellis 的工作流和我本身与 LLM agent 交互的方式很像，只不过这个更加标准化，且持续迭代
> 
> 和 LLM 沟通比和人打交道简单多了

一个「团队级 AI 编码骨架（harness）」。它不替代 AI，而是在仓库里铺一层结构，让 AI 编码在团队规模下可复现、可审查、可积累。核心解决「AI 每次 session 从零开始、约定记不住、上下文丢失」的问题。

四块基础设施（都落在 `.trellis/` 目录，进仓库版本管理）：

| 系统               | 作用                                                   | 落盘位置                                   |
| ------------------ | ------------------------------------------------------ | ------------------------------------------ |
| Spec 系统      | 编码规范/约定写一次，按需自动注入，不靠 AI 记忆        | `.trellis/spec/<包>/<层>/index.md`         |
| Task 系统      | 每个任务一个目录，装 PRD、实现上下文、检查上下文、状态 | `.trellis/tasks/{MM-DD-name}/`             |
| Workspace 系统 | 记录每次 AI session，跨会话留痕                        | `.trellis/workspace/<开发者>/journal-N.md` |
| Developer 身份 | 区分是谁在干活（gitignore，不进仓库）                  | `.trellis/.developer`                      |

核心机制：用一个「per-turn 面包屑（breadcrumb）」状态机驱动 AI。`task.json.status` 在 `planning → in_progress → completed` 之间流转，每个状态对应 `workflow.md` 里一段 `[workflow-state:*]` 文本，由 hook 每轮注入到 AI 的上下文里，强制 AI 走对应阶段、不跳步。

三阶段循环：

```
Phase 1 Plan    → 想清楚做什么（brainstorm + research → prd.md）
Phase 2 Execute → 写代码 + 过质量检查（implement → check）
Phase 3 Finish  → 沉淀经验 + 收尾（update-spec → commit → finish-work）
```

关键设计哲学：

- Plan before code：先有 PRD 再写代码。
- Specs injected, not remembered：规范靠注入不靠记。
- Persist everything：研究、决策、教训全落文件——「对话会被压缩，文件不会」。
- 主 agent 默认不直接写代码：派 `trellis-implement` / `trellis-check` 子 agent 干活，因为子 agent 能拿到 `implement.jsonl` 注入的精准 spec 上下文，主线程拿不到。

## install

install via `sudo npm install -g @mindfoldhq/trellis@latest`

## usage

usage like this

```bash
$ trellis init -u unitree-g1-tests

$ tree -a -L3
.
├── AGENTS.md                              # 子代理总览说明（brainstorm/implement/check/research/update-spec）
├── .claude
│   ├── agents
│   │   ├── trellis-check.md               # check 阶段子代理
│   │   ├── trellis-implement.md           # implement 阶段子代理
│   │   └── trellis-research.md            # research 阶段子代理
│   ├── commands
│   │   └── trellis                        # /trellis 系列 slash command
│   ├── hooks
│   │   ├── inject-subagent-context.py     # 子代理启动时注入上下文
│   │   ├── inject-workflow-state.py       # 每次调用注入当前 workflow 阶段
│   │   └── session-start.py               # SessionStart 钩子，初始化 developer/会话
│   ├── settings.json                      # Claude Code 配置（hooks/权限/模型）
│   └── skills
│       ├── trellis-before-dev             # 开发前置检查 skill
│       ├── trellis-brainstorm             # 头脑风暴/方案探索 skill
│       ├── trellis-break-loop             # 跳出死循环 skill（卡住时切换思路）
│       ├── trellis-check                  # 自检/验收 skill
│       ├── trellis-meta                   # 元工作流 skill（管理 workflow 本身）
│       ├── trellis-spec-bootstarp         # spec 初始化 skill（原文 typo: bootstrap）
│       └── trellis-update-spec            # spec 增量更新 skill
└── .trellis                               # Trellis 项目记忆/配置根目录
    ├── config.yaml                        # 中央配置（Trellis 行为与平台）
    ├── .developer                         # 当前开发者身份文件
    ├── .gitignore
    ├── scripts                            # Python 工具集
    │   ├── add_session.py                 # 记录已完成的会话/产出
    │   ├── common                         # 公共工具模块
    │   ├── get_context.py                 # 拉取任务相关 spec
    │   ├── get_developer.py               # 读取 per-developer 状态
    │   ├── hooks                          # 钩子辅助脚本
    │   ├── init_developer.py              # 初始化 developer profile
    │   ├── __init__.py
    │   └── task.py                        # 任务生命周期管理
    ├── spec                               # 可复用规范，每次会话自动注入
    │   ├── backend                        # 后端规范
    │   ├── frontend                       # 前端规范
    │   └── guides                         # 通用指南
    ├── tasks
    │   └── 00-bootstrap-guidelines        # 初始 bootstrap 任务模板，建立基线约定
    ├── .template-hashes.json              # 模板文件版本哈希
    ├── .version                           # 当前 Trellis schema 版本
    ├── workflow.md                        # 4 阶段循环：Plan → Implement → Verify → Finish
    └── workspace                          # 开发者日志/会话记忆
        ├── index.md                       # workspace 索引
        └── unitree-g1-tests               # 本项目对应的工作区

26 directories, 21 files
```

then start the workflow in your repo dir with `claude`, `codex` ...

---

## 使用场景举例：「PM 按项目指标构思 demo」

背景：PM 看板上的指标——新用户注册后 7 日留存仅 12%，激活漏斗卡在「注册完不知道下一步干什么」。

PM 的诉求：不写需求文档扔给工程师排期，而是自己用 AI 直接攒一个可演示的 demo——「新用户引导清单（onboarding checklist）」，下周给 stakeholder 演示，论证它能把激活率拉起来。PM 不是工程师，但能用自然语言描述意图。

为什么用 Trellis 而不是直接问 AI：

- demo 要能讲清「为什么做」——PRD 自动沉淀，演示时直接拿来当说明。
- PM 改了几轮想法，Trellis 把每轮决策写进 `prd.md`，不会聊着聊着丢。
- 这个 demo 如果验证成立要转正式开发，task 目录、PRD、研究材料直接交接给工程团队，不用重述。

完整流程模拟（人 / 工作流 / 变更 三栏）

> 当前 SessionStart 显示 `DEVELOPER: Not initialized`，所以从第 0 步开始。

### 第 0 步 · 初始化身份（一次性）

|                  |                                                              |
| ---------------- | ------------------------------------------------------------ |
| 人做什么     | 跑 `python3 ./.trellis/scripts/init_developer.py pm-alice`   |
| 工作流做什么 | 建身份文件 + 个人 workspace                                  |
| 什么变了     | 新增 `.trellis/.developer`(gitignore)、`.trellis/workspace/pm-alice/` |

### Phase 1 — Plan

#### 1.0 创建任务 `[必需·一次]`

|                  |                                                              |
| ---------------- | ------------------------------------------------------------ |
| 人做什么     | 对 AI 说「我想做个新用户引导清单 demo，把 7 日留存拉起来」。这是「B 类·实现任务」，AI 跑 `task.py create "demo: 新用户引导清单" --slug onboarding-checklist-demo` |
| 工作流做什么 | 建任务目录，`status=planning`，自动把本 session 的「当前任务指针」指向它，面包屑切到 `[workflow-state:planning]` |
| 什么变了     | 新增 `.trellis/tasks/05-25-onboarding-checklist-demo/`，内含种子文件 `task.json`(status=planning)、`prd.md`(空模板)、`implement.jsonl` / `check.jsonl`(各一行 `_example` 种子)；`.trellis/.runtime/sessions/` 写入指针 |

> 注意：这一步只 create 不 start。提前 start 会把状态翻到实现阶段，AI 会跳过 brainstorm。

#### 1.1 需求探索 `[必需·可重复]`

|                  |                                                              |
| ---------------- | ------------------------------------------------------------ |
| 人做什么     | 回答 AI 的提问。AI 加载 `trellis-brainstorm` skill，一次问一个问题：清单放几条？触发时机（注册后首屏 / 第二次登录）？demo 用真数据还是 mock？演示重点是交互还是留存数字？PM 逐个拍板 |
| 工作流做什么 | brainstorm skill 引导 AI：优先给选项而非开放问题、优先自己查而非问人、每次回答后立刻写 `prd.md`，收敛到 MVP 范围 |
| 什么变了     | `prd.md` 持续被填充——目标（留存指标）、范围（5 条清单 + 进度条）、非目标（不接真实埋点，用 mock）、验收标准 |

#### 1.2 研究 `[可选·可重复]`

|                  |                                                              |
| ---------------- | ------------------------------------------------------------ |
| 人做什么     | （可由 AI 主动发起）PM 不用管                                |
| 工作流做什么 | AI 派 `trellis-research` 子 agent 查「onboarding checklist 的常见交互模式 / 同类产品怎么做的」，结果必须写进 `research/` |
| 什么变了     | 新增 `.trellis/tasks/05-25-onboarding-checklist-demo/research/onboarding-patterns.md` |

#### 1.3 配置上下文 `[必需·一次]`

|                  |                                                              |
| ---------------- | ------------------------------------------------------------ |
| 人做什么     | 一般不用动，AI 自动做                                        |
| 工作流做什么 | AI 跑 `get_context.py --mode packages` 找出相关 spec（如前端组件层规范），把 spec 路径 + research 文件写进 `implement.jsonl`（给实现子 agent）和 `check.jsonl`（给检查子 agent），删掉 `_example` 种子行 |
| 什么变了     | `implement.jsonl` / `check.jsonl` 被填入真实条目，形如 `{"file":".trellis/spec/frontend/ui/index.md","reason":"组件规范"}` |

> 这一步是「不靠记忆靠注入」的关键：子 agent 写代码时这些 spec 会被自动塞进它的 prompt。

#### 1.4 激活任务 `[必需·一次]`

|                  |                                                              |
| ---------------- | ------------------------------------------------------------ |
| 人做什么     | PRD 确认无误后，让 AI 跑 `task.py start 05-25-onboarding-checklist-demo` |
| 工作流做什么 | 状态翻 `planning → in_progress`，面包屑切到 `[workflow-state:in_progress]` |
| 什么变了     | `task.json` 的 `status` 改为 `in_progress`                   |

#### 1.5 完成判据

`prd.md` 存在 ✅ · 用户确认需求 ✅ · `task.py start` 已跑 ✅ · `implement.jsonl` 有真实条目 ✅

### Phase 2 — Execute

#### 2.1 实现 `[必需·可重复]`

|                  |                                                              |
| ---------------- | ------------------------------------------------------------ |
| 人做什么     | 让 AI 开始实现（说一句即可）。PM 不写代码                    |
| 工作流做什么 | 主 agent 派 `trellis-implement` 子 agent（默认不自己写）。hook 自动把 `implement.jsonl` 指向的 spec + `prd.md` 注入子 agent。子 agent 据 PRD 写 demo 代码，最后跑 lint + type-check。不 commit |
| 什么变了     | 新增/修改业务代码（如 `src/` 下的 onboarding 组件、mock 数据）；task 目录不变 |

#### 2.2 质量检查 `[必需·可重复]`

|                  |                                                              |
| ---------------- | ------------------------------------------------------------ |
| 人做什么     | 等结果                                                       |
| 工作流做什么 | 主 agent 派 `trellis-check` 子 agent，拿 `check.jsonl` 的 spec 对照 diff 审查、能改的当场改、跑 lint/type-check/tests，直到绿 |
| 什么变了     | 代码按检查结果被修正                                         |

#### 2.3 回滚 `[按需]`

检查发现 PRD 有缺陷 → 退回 Phase 1 改 `prd.md` 再重做 2.1。阶段可回卷。

### Phase 3 — Finish

#### 3.1 最终验证 `[必需·可重复]`

|                  |                                                              |
| ---------------- | ------------------------------------------------------------ |
| 人做什么     | PM 本地跑起来看 demo 效果                                    |
| 工作流做什么 | AI 加载 `trellis-check` 做收尾验证（spec / lint / type / tests / 跨层一致性） |
| 什么变了     | 必要时再修代码                                               |

#### 3.2 调试复盘 `[按需]`

若同一 bug 反复修，加载 `trellis-break-loop` 分类根因、解释为何前几次没修好、提出预防。本 demo 若顺利则跳过。

#### 3.3 Spec 更新 `[必需·一次]`

|                  |                                                              |
| ---------------- | ------------------------------------------------------------ |
| 人做什么     | 不用管                                                       |
| 工作流做什么 | AI 加载 `trellis-update-spec`，判断这次有没有产生值得留下的新约定（如「demo 类任务统一用 mock 数据的约定」），有就写回 spec。即使结论是「无需更新」也要走一遍判断 |
| 什么变了     | 可能新增/修改 `.trellis/spec/` 下文件                      |

#### 3.4 提交 `[必需·一次]`

|                  |                                                              |
| ---------------- | ------------------------------------------------------------ |
| 人做什么     | 看 AI 给的提交计划，回「ok / 行」                            |
| 工作流做什么 | AI 跑 `git status` + `git log -5` 学提交风格，把本 session 改的文件分组成逻辑 commit，一次性出计划让你确认，确认后 `git add`+`git commit`。不 amend、不 push。无法识别的脏文件单列、不偷偷带上 |
| 什么变了     | 代码改动落成 git commit（业务代码先提，bookkeeping 后提）    |

#### 3.5 收尾提醒

|                  |                                                              |
| ---------------- | ------------------------------------------------------------ |
| 人做什么     | 跑 `/trellis:finish-work`                                    |
| 工作流做什么 | 清当前任务指针、把 task 归档到 `archive/{年-月}/`（`status→completed`）、写 session journal |
| 什么变了     | task 目录移到 `.trellis/tasks/archive/2026-05/`；`.trellis/workspace/pm-alice/journal-N.md` 追加本次记录；runtime 指针删除 |

一句话总结全流程的「变更轨迹」

```
开始：创建身份文件 
→ task 目录(planning) 
→ prd.md(逐轮填) 
→ research/ 
→ implement.jsonl/check.jsonl(注入清单) 
→ status=in_progress 
→ 业务代码(子agent写) 
→ 代码修正(子agent查) 
→ spec回写 
→ git commit 
→ 归档 + journal(completed)
```

人只做四件事：描述意图、回答 brainstorm 提问、确认 PRD、确认提交计划。其余的状态流转、上下文注入、子 agent 调度、落盘归档全由工作流自动完成——这正是 Trellis 把「一个 PM 的临时想法」变成「可交接、可复现的结构化产物」的方式。