# Pydantic AI 工程化 Agent 新范式

## Turn Index

| # | Export | Q | A | Note |
| --- | --- | --- | --- | --- |
| 1 | keep | 询问基于 Pydantic AI 构建项目与工程型 LLM Agent 的新方法及其核心变化。 | 从 Capabilities、Harness、Code Mode、DynamicWorkflow、Skills、类型契约和持久化执行等方面，说明 Agent 如何从逐步调用工具转向受控环境中的动态程序编排。 | 概念与架构总览 |
| 2 | keep | 要求通过一个工程化案例说明新范式相较固定工作流的优势。 | 以只读的工业设备故障诊断 Agent 为例，展示如何围绕领域模型、原子工具、动态编排、多专家协作、权限边界与验证体系构建可适应不同故障路径的系统。 | 工程案例与安全边界 |
| 3 | keep | 追问 Capability 与 MCP 的边界、系统规模是否可能通向 AGI、个人超级助手的可行性，以及下一代 Agent 架构。 | 区分能力接入协议、Agent 能力模型与运行时治理，分析模型智能和系统智能的关系，并提出由世界模型、事件驱动、程序合成、自创技能、模拟验证和长期目标组成的持续认知运行时。 | 边界辨析与未来推演 |

## 1. 理解 Pydantic AI 的工程化 Agent 范式

<div markdown="1" style="background-color: rgba(91, 155, 213, 0.12); border-left: 4px solid #5b9bd5; border-radius: 6px; margin: 16px 0; padding: 12px 16px;">

<h3 align="center"><strong>USER</strong></h3>

我注意到最近有一种基于 pydantic ai 去做项目、工程的新型 llm agent 应用方式。介绍一下

</div>

<h3 align="center"><strong>ASSISTANT</strong></h3>

你看到的很可能是 **Pydantic AI 在 2026 年形成的这一套新范式：`Capabilities + Harness + Code Mode + DynamicWorkflow`**。

它和传统“LLM + function calling”的区别相当大。核心变化是：**不再由开发者提前把 Agent 的执行流程写死，而是让 LLM 在受控环境中动态生成一段“执行程序”，再由框架负责类型、安全、工具、状态和可观测性。** Pydantic AI 官方现在已经把 `capabilities` 定义为主要扩展机制。

##### 1. 传统 Agent 是“模型一步一步调用工具”

传统模式通常是：

```text
用户任务
   ↓
LLM
   ↓
调用 tool A
   ↓
结果返回 LLM
   ↓
LLM 再思考
   ↓
调用 tool B
   ↓
再返回 LLM
   ↓
……
```

例如：

```text
查看代码
→ 搜索文件
→ 读文件
→ grep
→ 执行测试
→ 修改代码
→ 再测试
```

如果有 20 个操作，往往意味着很多次：

```text
LLM → tool → LLM → tool → LLM
```

问题是延迟高、token 消耗高，而且每个中间结果都会不断塞回模型上下文。

---

#### 2. 新模式：LLM 生成“执行程序”

Pydantic AI Harness 里的 **Code Mode** 把很多工具包装成一个 `run_code`。

于是模型不是这样：

```text
调用 read_file
调用 search
调用 read_file
调用 test
```

而是直接生成类似：

```python
files = search("authentication")

results = []

for file in files:
    content = read_file(file)

    if "jwt" in content.lower():
        results.append(content)

test_result = shell("pytest tests/auth")

return {
    "files": results,
    "tests": test_result
}
```

这一小段程序在 sandbox 中执行。

所以：

```text
以前：

LLM
 ↓
tool
 ↓
LLM
 ↓
tool
 ↓
LLM
 ↓
tool


现在：

LLM
 ↓
生成执行程序
 ↓
Sandbox
 ├─ tool
 ├─ tool
 ├─ tool
 ├─ 并发
 ├─ 条件判断
 └─ 循环
 ↓
最终结果
 ↓
LLM
```

Pydantic 官方明确把 Code Mode 描述为：模型写 Python，通过循环、条件、`asyncio.gather`、本地过滤等方式，一次模型 round-trip 完成 N 个工具调用。

这实际上已经接近一种：

> **LLM as runtime programmer**

而不只是：

> **LLM as tool selector**

这是我认为这套东西最重要的变化。

---

#### 3. `Capabilities`：Agent 开始像“组装操作系统能力”

第二个重要变化是：

```python
Agent(
    model=...,
    capabilities=[
        ...
    ]
)
```

Capability 可以同时携带：

- tools
- instructions
- lifecycle hooks
- model settings
- model selection
- context processing

因此不需要每个 Agent 自己实现一大坨 orchestration 逻辑。

现在官方核心以及 `pydantic-ai-harness` 已经覆盖了相当完整的一套能力，例如：

```text
Agent
│
├── Thinking
├── WebSearch
├── WebFetch
├── MCP
├── ToolSearch
│
├── CodeMode
├── FileSystem
├── Shell
├── RepoContext
│
├── Skills
├── Planning
├── Memory
├── Compaction
│
├── Subagents
├── DynamicWorkflow
│
├── StepPersistence
├── ConversationSearch
│
├── Guardrails
├── Approval
└── Spend / Usage limits
```

其中 Harness 专门负责那些“把普通 Agent 变成工程型 Agent”的能力，例如文件系统、Shell、代码执行、Memory、Planning、多 Agent、上下文管理和 Guardrails。

于是一个工程 Agent 可以开始像搭积木：

```python
agent = Agent(
    "anthropic:claude-opus-4-7",
    capabilities=[
        CodeMode(),
        FileSystem(...),
        Shell(...),
        Skills(...),
        Planning(...),
        Memory(...),
    ],
)
```

而不是自己实现一个庞大的 `while True: agent_loop()`。

---

### 4. `DynamicWorkflow` 更有意思

Code Mode 是：

> LLM 动态编排 tools。

DynamicWorkflow 则进一步变成：

> **LLM 动态编排 Agents。**

例如有：

```text
orchestrator
│
├─ security_reviewer
├─ backend_reviewer
├─ database_reviewer
└─ summarizer
```

传统 multi-agent 通常要开发者提前写：

```python
a = await security_agent(...)
b = await backend_agent(...)
c = await database_agent(...)

result = await summary_agent(a, b, c)
```

而 DynamicWorkflow 让 orchestrator **自己生成这个 workflow**：

```python
results = await asyncio.gather(
    security_reviewer(task=...),
    backend_reviewer(task=...),
    database_reviewer(task=...),
)

await summarizer(
    task="\n".join(results)
)
```

也就是说：

```text
过去：

人类写 workflow
LLM 执行 workflow


现在：

人类定义能力边界
LLM 生成 workflow
runtime 执行 workflow
```

而且子 Agent 可以并行、串联、投票，整个子 Agent 树可以只作为一次工具调用执行，避免每个中间结果都经过 orchestrator 的上下文。

这已经非常接近真正的 **Agentic Runtime**。

---

### 5. Skills 也发生了变化

以前常见做法：

```text
system prompt = 30000 tokens
```

把：

- Git 操作指南
- Python 指南
- 数据库指南
- API 文档
- 项目规则
- 部署规则

全部塞进去。

现在更倾向：

```text
Agent
│
├─ Skill: Python
├─ Skill: Git
├─ Skill: PostgreSQL
├─ Skill: Deployment
├─ Skill: Debugging
└─ Skill: Project-specific
```

而且 Capability 可以：

```python
defer_loading=True
```

默认只暴露很短的能力描述，Agent 真正需要时再加载。官方把这种机制称为 **on-demand capability**。

这解决了大型 Agent 很重要的一个问题：

```text
能力越来越多
        ↓
system prompt 越来越大
        ↓
context 污染
        ↓
模型注意力下降
```

新的方向变成：

```text
小核心 Prompt
+
按需能力
+
按需工具发现
+
按需 Skill
```

---

### 6. 于是“做 Agent 项目”的方式变了

以前工程结构可能是：

```text
agent.py
prompt.py
tools.py
workflow.py
router.py
memory.py
planner.py
executor.py
guardrails.py
```

大量代码其实是在维护 Agent framework 本身。

现在越来越像：

```text
project/
├─ agent.yaml
├─ skills/
│  ├─ debugging/
│  │  └─ SKILL.md
│  ├─ database/
│  │  └─ SKILL.md
│  └─ deploy/
│     └─ SKILL.md
│
├─ tools/
├─ domain/
└─ app.py
```

甚至 Agent 本身可以 YAML 定义：

```yaml
model: anthropic:claude-opus-4-6

instructions: |
  You are a software engineering agent.

capabilities:
  - WebSearch:
      local: duckduckgo

  - Thinking:
      effort: high
```

然后：

```python
agent = Agent.from_file("agent.yaml")
```

Pydantic AI 当前已经正式支持 Agent Specs，通过 YAML/JSON 定义 model、instructions、capabilities 等配置。

这意味着 **Agent configuration 和 application code 开始分离**。

---

### 7. Pydantic 在这里真正发挥作用的地方

名字叫 Pydantic AI 并不是因为“拿 Pydantic 验证一下 JSON”。

真正重要的是整个系统倾向：

```text
自然语言世界
      ↓
Pydantic Schema
      ↓
确定性 Python 世界
```

例如 Agent 最终必须产生：

```python
class Diagnosis(BaseModel):
    cause: str
    confidence: float
    evidence: list[str]
    actions: list[Action]
```

而不是：

```text
“我认为可能是数据库的问题……”
```

Tool 也是：

```python
def restart_service(
    service: ServiceName,
    environment: Environment,
) -> RestartResult:
```

Dependencies 也是 typed。

Agent output 也是 typed。

所以架构更接近：

```text
LLM = probabilistic decision engine

Pydantic =
    contract
    schema
    validation
    boundary

Python =
    deterministic execution

Capability =
    modular behavior

Harness =
    agent runtime components
```

Pydantic 团队自己把这个思想概括得很明确：GenAI application 仍然是 engineering，并重点强调 type safety、dependency injection、structured output、durable execution 和 observability。

---

### 8. 还有一个很关键的变化：Agent 可以“长时间运行”

传统 Agent：

```text
request
↓
agent
↓
response
```

更像 HTTP API。

现在的工程 Agent：

```text
任务
 ↓
Planning
 ↓
执行
 ↓
Checkpoint
 ↓
继续执行
 ↓
等待人工批准
 ↓
恢复
 ↓
调用外部系统
 ↓
失败
 ↓
恢复
 ↓
最终完成
```

Pydantic AI 已经把 **Durable Execution** 做成正式能力，目前官方文档列出了 Temporal、DBOS、Prefect、Restate 等集成，用于跨 API 故障、程序重启和长时间等待保存 Agent 进度。

这使得 Agent 从：

> chatbot

逐渐变成：

> **long-running autonomous worker**

---

### 9. 最终架构其实越来越像这样

```text
                     User
                       │
                       ▼
                ┌─────────────┐
                │ Orchestrator│
                │    Agent    │
                └──────┬──────┘
                       │
              Planning / Reasoning
                       │
               Dynamic Workflow
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
      Agent A       Agent B       Agent C
          │            │            │
          └────────────┼────────────┘
                       │
                    CodeMode
                       │
                sandbox program
                       │
       ┌───────────────┼──────────────┐
       ▼               ▼              ▼
   FileSystem         MCP           Shell
       │               │              │
       └───────────────┼──────────────┘
                       ▼
                 Real systems

            ┌──────────────────────┐
            │ Pydantic boundary    │
            │ Schema / Validation  │
            │ Dependency Injection │
            │ Guardrails           │
            └──────────────────────┘

            ┌──────────────────────┐
            │ Runtime layer        │
            │ Memory               │
            │ Persistence          │
            │ Compaction           │
            │ Observability        │
            │ Evals                │
            └──────────────────────┘
```

这就是它和早期 LangChain / ReAct Agent 最大的范式差异。

---

#### 10. 我认为可以把这类架构概括成三代

```text
第一代
LLM → Prompt → Text

第二代
LLM → Function Calling → Tools

第三代
LLM
 ↓
生成执行计划 / 程序
 ↓
Agent Runtime
 ↓
Tools + Skills + Agents + Code
 ↓
真实环境
```

Pydantic AI 最近明显在往第三种发展。

尤其这几个东西放在一起：

```text
Capabilities
+
CodeMode
+
DynamicWorkflow
+
Skills
+
MCP
+
Memory
+
Persistence
+
Guardrails
```

其实已经不是传统意义上的“Agent Framework”。

更准确地理解，它正在变成一种：

> **用于构建可编程、自适应、长时间运行 LLM Worker 的 Python Agent Runtime。**

这里最值得关注的不是 Pydantic 的 `BaseModel`，而是 **“让模型动态写 orchestration program，而宿主只负责能力、安全和边界”** 这个设计方向。

需要注意，目前 **Pydantic AI Harness 仍采用 0.x 版本策略**，官方明确说明 minor release 仍可能有 breaking changes；它目前更适合快速试验和新项目，而不是把 Harness API 当成长期冻结的基础设施接口。

## 2. 用工业故障诊断展示工程优势

<div markdown="1" style="background-color: rgba(91, 155, 213, 0.12); border-left: 4px solid #5b9bd5; border-radius: 6px; margin: 16px 0; padding: 12px 16px;">

<h3 align="center"><strong>USER</strong></h3>

举一个工程化的例子来体现这种新范式的优势？

</div>

<h3 align="center"><strong>ASSISTANT</strong></h3>

最能体现这种新范式优势的例子，是做一个**工厂设备故障诊断与处置 Agent**。

假设场景：

> 某包装线的目标伺服轴最近频繁出现瞬时跟随误差报警，操作员只告诉 Agent：  
> **“分析今天目标轴频繁停机的原因，给出证据和处理方案，不允许直接修改 PLC。”**

传统做法和 Pydantic AI 新范式的差别会非常明显。

---

#### 1. 传统 Agent：人先把诊断流程写出来

开发者通常会设计：

```text
读取报警
   ↓
判断报警类型
   ↓
查询历史趋势
   ↓
读取 PLC 参数
   ↓
查询维修记录
   ↓
查询设备手册
   ↓
做时间关联
   ↓
判断原因
   ↓
生成报告
```

然后代码变成：

```python
alarms = await get_alarms()

if has_servo_alarm(alarms):
    trend = await get_trend()

    if trend_is_abnormal(trend):
        params = await get_plc_params()
        ...
```

实际上你是在：

> **用 Python 写专家系统，LLM 只负责其中某几个判断。**

一旦现场问题变成：

- 有时候要查 PLC
- 有时候要查变频器
- 有时候要查历史工单
- 有时候需要对比 Git 中的 PLC 程序版本
- 有时候只需要查说明书
- 有时候需要同时分析 20 个报警点

workflow 很快膨胀。

---

### 2. 新范式：工程师只定义“世界”

你不再定义诊断步骤。

只定义 Agent 可以接触的能力和数据边界。

例如：

```python
class Alarm(BaseModel):
    timestamp: datetime
    device: str
    code: str
    message: str


class TrendPoint(BaseModel):
    timestamp: datetime
    value: float


class Diagnosis(BaseModel):
    fault: str
    confidence: float
    evidence: list[str]
    recommended_actions: list[str]
```

然后提供工具：

```python
async def query_alarm_history(
    device: str,
    start: datetime,
    end: datetime,
) -> list[Alarm]:
    ...


async def query_tag_history(
    tag: str,
    start: datetime,
    end: datetime,
) -> list[TrendPoint]:
    ...


async def read_plc_variables(
    plc: str,
    variables: list[str],
) -> dict[str, float]:
    ...


async def search_maintenance_records(
    equipment: str,
    query: str,
) -> list[str]:
    ...


async def search_manual(
    equipment_model: str,
    query: str,
) -> list[str]:
    ...
```

注意这里没有：

```python
diagnose_servo_fault()
```

因为**诊断流程本身不再由程序员写死**。

---

### 3. Agent 得到的是能力集合

概念上类似：

```python
agent = Agent(
    model,
    output_type=Diagnosis,
    capabilities=[
        CodeMode(),
    ],
)
```

然后注册：

```text
query_alarm_history
query_tag_history
read_plc_variables
search_maintenance_records
search_manual
get_program_version
compare_program_versions
```

Pydantic AI Harness 的 `CodeMode` 可以把这些普通 tool 暴露到一个沙箱 Python 环境中，让模型用循环、条件、局部计算和 `asyncio.gather()` 编排多个工具，而不是每个动作都重新进行一次模型回合。

---

### 4. 真正关键的地方来了

用户说：

> 分析今天目标轴频繁停机的原因。

LLM 可能自己生成类似这样的执行程序：

```python
alarms = await query_alarm_history(
    device="LINE-ID.AXIS-ID",
    start=today_start,
    end=now,
)

servo_alarms = [
    a for a in alarms
    if "following error" in a.message.lower()
]

times = [a.timestamp for a in servo_alarms]

position, torque, speed = await asyncio.gather(
    query_tag_history(
        "AXIS-ID.ActualPosition",
        min(times) - timedelta(seconds=10),
        max(times) + timedelta(seconds=10),
    ),
    query_tag_history(
        "AXIS-ID.Torque",
        min(times) - timedelta(seconds=10),
        max(times) + timedelta(seconds=10),
    ),
    query_tag_history(
        "AXIS-ID.Speed",
        min(times) - timedelta(seconds=10),
        max(times) + timedelta(seconds=10),
    ),
)
```

模型发现：

```text
每次报警前 300~500 ms
Torque 都突然升到 180%
```

于是它继续：

```python
maintenance, manual = await asyncio.gather(
    search_maintenance_records(
        equipment="LINE-ID.AXIS-ID",
        query="mechanical maintenance belt bearing gearbox",
    ),
    search_manual(
        equipment_model="XXX Servo",
        query="following error high torque mechanical load",
    ),
)
```

发现昨天维修记录：

```text
更换目标轴同步带
```

于是继续查：

```python
params = await read_plc_variables(
    "PLC-ID",
    [
        "AXIS-ID.PositionGain",
        "AXIS-ID.SpeedGain",
        "AXIS-ID.TorqueLimit",
    ],
)
```

参数没变化。

然后 Agent 自己形成证据链：

```text
报警时间
    ↓
Torque 突升
    ↓
Position Error 增大
    ↓
Servo Following Error
    ↓
昨天刚更换同步带
    ↓
控制参数没有发生变化
```

最终输出：

```python
Diagnosis(
    fault="Target-axis mechanical resistance increased after belt replacement",
    confidence=0.87,
    evidence=[
        "11/11 following-error alarms were preceded by torque spikes",
        "Torque reached 175%-190% immediately before alarm",
        "The target-axis timing belt was replaced yesterday",
        "Servo tuning parameters are unchanged",
    ],
    recommended_actions=[
        "Check timing-belt tension",
        "Check pulley alignment",
        "Check bearing preload",
        "Do not modify servo tuning parameters before mechanical inspection",
    ],
)
```

---

### 5. 新范式真正厉害的是：你没有写这条流程

开发者没有写：

```python
if servo_alarm:
    check_torque()

if torque_high:
    check_maintenance()

if maintenance_changed_belt:
    check_servo_params()
```

这些逻辑是 **LLM 根据现场证据动态生成的**。

你只写了：

```text
世界有哪些东西
Agent 可以做什么
数据是什么类型
什么操作禁止
最终必须输出什么结构
```

这实际上是：

```text
旧范式：

Programmer
   ↓
编写 Workflow
   ↓
LLM 填空


新范式：

Programmer
   ↓
定义 Environment
定义 Capability
定义 Contract
定义 Permission
   ↓
LLM
   ↓
动态生成 Workflow
```

这就是最大的变化。

---

### 6. 如果故障换了，代码不用改

第二天变成：

> “分析为什么 5 号电机凌晨出现三次过载。”

Agent 可能形成完全不同的程序：

```text
报警记录
 ↓
Motor Current
 ↓
VFD Frequency
 ↓
Conveyor Speed
 ↓
Production Batch
 ↓
Material Type
 ↓
历史相同批次
 ↓
维修记录
```

第三天：

> “为什么目标 PLC 昨天在某个时间点重启？”

它可能执行：

```text
PLC event log
+
UPS log
+
switch log
+
SCADA communication alarm
+
Windows event
+
maintenance record
```

**工程代码没有增加两个新的 workflow。**

这是这种架构可扩展性的核心。

---

### 7. Code Mode 对这种场景尤其合适

假设一次事故涉及：

```text
50 个报警
20 个模拟量
8 个设备
3 个历史系统
```

普通 Tool Calling 很容易变成：

```text
LLM
→ 查 alarm
→ LLM
→ 查 trend
→ LLM
→ 查 trend
→ LLM
→ 查 trend
→ ...
```

Pydantic AI Code Mode 可以让模型写：

```python
tags = [
    "motor_current",
    "motor_speed",
    "torque",
    "temperature",
    "line_speed",
]

results = await asyncio.gather(
    *[
        query_tag_history(tag, start, end)
        for tag in tags
    ]
)
```

然后直接在沙箱里：

```python
for tag, values in zip(tags, results):
    ...

correlations = ...
anomalies = ...
```

只把：

```text
异常点
相关性
关键时间窗口
```

返回 LLM。

官方给 Code Mode 的核心动机正是减少多批工具调用导致的模型往返、延迟和上下文膨胀，并允许在沙箱代码中进行并行、过滤和聚合。

---

### 8. 再进一步：引入多个专家 Agent

对于复杂故障，可以定义：

```text
PLC Expert
Servo Expert
Historian Analyst
Maintenance Expert
Network Expert
```

但仍然**不预定义什么时候调用谁**。

Orchestrator 可以动态生成：

```python
servo_result, history_result, maintenance_result = \
    await asyncio.gather(

        servo_expert(
            task="Analyse target-axis following-error alarms"
        ),

        historian_expert(
            task="Find correlated signals around alarm timestamps"
        ),

        maintenance_expert(
            task="Find recent changes to the target axis"
        ),
    )

if servo_result.confidence < 0.7:

    plc_result = await plc_expert(
        task="Check PLC-side causes for target-axis faults"
    )
```

Pydantic AI Harness 的 `DynamicWorkflow` 正是为这种 fan-out、串联、投票、重试等动态子 Agent 编排设计的；编排代码在一次 workflow tool 调用中执行，中间结果不必全部反复进入父 Agent 上下文。

于是架构变成：

```text
                 Maintenance Agent
                        │
                 分析当前问题
                        │
                动态生成 workflow
                        │
        ┌───────────────┼──────────────┐
        ▼               ▼              ▼
    PLC Expert      Servo Expert    Historian
        │               │              │
        └───────────────┼──────────────┘
                        ▼
                    CodeMode
                        │
           ┌────────────┼────────────┐
           ▼            ▼            ▼
         SCADA         PLC          CMMS
           │            │            │
       Historian       OPC UA       工单库
```

---

### 9. 安全边界反而可以更明确

这点对工控尤其重要。

不要给 Agent：

```python
write_plc_variable()
```

而是把工具分层：

```text
Level 0
读取文档

Level 1
读取 Historian

Level 2
读取 PLC

Level 3
执行诊断测试

Level 4
修改参数

Level 5
启停设备
```

Code Mode 只开放：

```python
CodeMode(
    tools=[
        "query_alarm_history",
        "query_tag_history",
        "read_plc_variables",
        "search_manual",
        "search_maintenance_records",
    ]
)
```

像：

```text
write_plc_variable
download_plc_program
start_motor
reset_safety
```

根本不进入沙箱。

官方 Code Mode 支持选择哪些 tools 可以进入 sandbox；默认沙箱也没有宿主文件系统、环境变量或时钟访问，必须显式授予。

所以这里出现一个很重要的工程思想：

> **Agent 的自主性来自“允许它自由组合安全能力”，而不是给它无限权限。**

---

### 10. 工程团队真正维护的东西变了

过去维护：

```text
workflow_001.py
workflow_002.py
workflow_003.py
servo_fault_flow.py
plc_fault_flow.py
network_fault_flow.py
...
```

新模式维护：

```text
industrial-agent/
│
├── domain/
│   ├── alarm.py
│   ├── equipment.py
│   └── diagnosis.py
│
├── tools/
│   ├── historian.py
│   ├── opcua.py
│   ├── cmms.py
│   ├── manuals.py
│   └── git.py
│
├── skills/
│   ├── siemens-plc/
│   ├── servo-diagnosis/
│   ├── profinet/
│   └── electrical/
│
├── agents/
│   ├── plc_expert.py
│   ├── servo_expert.py
│   └── historian_expert.py
│
├── permissions/
│
└── main.py
```

重点从：

> **维护流程代码**

变成：

> **维护能力、领域模型、权限边界和验证体系。**

---

#### 所以它真正的工程优势可以浓缩成一句话

传统 Agent：

```text
你告诉 AI：
“按照我设计的流程工作。”
```

新范式：

```text
你告诉 AI：

这里有哪些系统；
有哪些工具；
数据结构是什么；
哪些事情能做；
哪些事情不能做；
最终结果必须满足什么契约。

至于如何解决当前这个问题，
你自己生成程序。
```

这和“给 Agent 加几个 function calling”不是一个层级的变化。

**真正值得研究的是：软件工程的抽象单位正在从 `workflow` 转向 `capability + contract + environment`。**

对于工控、运维、DevOps、数据工程、代码工程这类**问题路径高度不确定，但可用能力和安全边界非常明确**的领域，这种范式的优势尤其明显。

## 3. 辨析 MCP、系统智能与下一代认知运行时

<div markdown="1" style="background-color: rgba(91, 155, 213, 0.12); border-left: 4px solid #5b9bd5; border-radius: 6px; margin: 16px 0; padding: 12px 16px;">

<h3 align="center"><strong>USER</strong></h3>

1、里面定义的边界、拥有的最小功能，和 mcp 有什么区别？
2、按照这个说法，如果结构足够准确、量级足够大，是不是有可能出现 agi？就算没那么大的预期，用来做个人超级助手，是不是足够智能了？
3、你认为，下一代可能是怎么样的？

</div>

<h3 align="center"><strong>ASSISTANT</strong></h3>

#### 1. Capability / 最小功能边界，和 MCP 到底差在哪里

两者不在一个抽象层。

**MCP 解决的是“能力怎么接进来”。Capability/Harness 解决的是“Agent 拥有什么能力，以及这些能力怎样参与它的认知和运行过程”。**

MCP 官方对自己的边界说得很清楚：它专注于 context/capability exchange 协议，不规定 AI 应用怎样使用 LLM，也不规定应用怎样管理上下文。即使 2026-07-28 的新 MCP 规范已经继续扩展 Tasks、extensions、授权等机制，其核心仍然是 Agent 世界里的通信/集成协议。

可以这样理解：

```text
                    Agent Runtime
                         │
        ┌────────────────┼────────────────┐
        │                │                │
     Memory          Planning        Guardrails
        │                │                │
        └──────────── Capabilities ───────┘
                         │
                  可调用的原子能力
                         │
             ┌───────────┼───────────┐
             │           │           │
          Python       MCP        Native API
             │           │
             ▼           ▼
           PLC         Gmail
        Historian      GitHub
```

在 Pydantic AI 里面，这个关系甚至已经非常明确：

> **MCP 本身就是一种 Capability。**

Pydantic AI 的 Capability 可以同时提供 tools、instructions、生命周期 hooks、model settings、甚至模型选择；官方把它定义成主要扩展点。MCP 则是其中一种把外部服务器能力带进 Agent 的方式。

因此可以用一句非常准确的话概括：

```text
MCP：
“外面的东西怎么向我提供能力？”

Capability：
“我的认知系统现在具备哪些能力？”

Harness / Runtime：
“这些能力在什么条件下、以什么权限、什么状态、什么流程被使用？”
```

##### 一个具体例子

一个 PLC MCP Server 可以暴露：

```text
read_tag
read_alarm
read_program_version
write_tag
restart_plc
download_program
```

MCP 负责描述和调用这些函数。

但你的 Agent 可能只获得：

```text
PLC_Diagnosis Capability
```

内部实际只允许：

```text
read_tag
read_alarm
read_program_version
```

并附带：

```text
只能读取
不能写入
诊断结论必须给出证据
不得根据单个报警直接判断根因
```

还可以再叠：

```text
ToolGuardrail
Approval
Audit
Budget
CodeMode
```

Pydantic Harness 的 guardrail 已经可以直接拦截 tool call，在真正执行工具之前决定 allow、block、replace、retry 或要求 approval。

所以从安全设计角度：

```text
MCP Server 暴露：
“这个系统理论上能干什么”

Agent Capability 定义：
“这个 Agent 被允许干什么”

Runtime 决定：
“这一次具体能不能干”
```

这三个边界最好分开。

我甚至会把 MCP 类比成：

> **Agent 世界的 USB / PCIe / RPC 总线。**

而 Capability 更类似：

> **操作系统里的设备能力 + 权限 + 驱动逻辑。**

---

### 2. 这种结构足够复杂，会不会走向 AGI？

这里必须把两个东西拆开：

##### Model Intelligence

即模型本身具有：

```text
理解
推理
抽象
迁移
预测
语言
代码
```

和：

##### System Intelligence

```text
LLM
+
Memory
+
Tools
+
Planning
+
Code execution
+
Search
+
Agents
+
Verification
+
World state
+
Long-running execution
```

我认为一个很重要的可能性是：

> **AGI 最终未必表现为“一个超级大的 LLM”，而可能首先表现为一个由模型驱动的智能系统。**

类似计算机。

CPU 本身不是：

```text
浏览器
数据库
IDE
操作系统
服务器
```

但：

```text
CPU
+
内存
+
存储
+
OS
+
程序
+
网络
```

形成了通用计算系统。

LLM 也可能类似。

---

但有一个重要限制：

> **堆很多 tools、memory 和 agents，并不会自动产生 AGI。**

因为：

```text
100 个不会正确推理的 Agent
≠
一个会正确推理的超级 Agent
```

甚至可能：

```text
错误率 × 工作流长度
```

导致可靠性下降。

真正需要突破的是：

```text
长期目标保持
因果理解
错误发现
错误恢复
不确定性判断
长期规划
有效学习
知识更新
现实反馈
自我校正
```

而不是单纯增加 MCP Server。

METR 最新的 agent time-horizon 研究也恰好反映了这一点：前沿 Agent 可以完成的自主任务长度正在快速增加，但成功率仍明显受到任务长度影响，而且他们明确提醒，这类 benchmark 主要集中在自包含的软件、ML、安全任务，并不能直接等价为开放世界通用自主能力。

所以我会把它近似理解为：

```text
系统智能能力

≈

基础模型能力
×
世界信息覆盖率
×
记忆质量
×
规划质量
×
执行能力
×
验证能力
×
长期稳定性
```

这里更接近**乘法**，而不是加法。

任何一个接近 0，整体都会受到严重限制。

---

#### 但“个人超级助手”是完全不同的问题

这个目标比 AGI 容易很多。

因为你并不需要：

> 理解世界上一切任务。

你只需要：

> **理解一个人的世界。**

假设一个 Agent 长期知道：

```text
你是谁
你的工作
你的设备
你的项目
你的文件
你的邮件
你的日程
你认识的人
你的长期目标
你的习惯
你正在学什么
哪些事情没完成
哪些事情正在等待别人
```

同时拥有：

```text
Browser
Files
Gmail
Calendar
Contacts
Shell
Python
MCP
搜索
代码环境
长期 Memory
```

这时它面对的是一个非常特殊的分布：

```text
整个世界
     ↓
你的世界
     ↓
非常有限的一部分
```

于是并不需要真正的 AGI，也可能表现出非常强的“通用性”。

我把这个称为：

> **Personal General Intelligence**

不是 AGI，但对一个人而言具有高度 general。

---

比如你告诉它：

> 我准备明年换一个工作方向。

传统 AI 会回答：

```text
建议学习 A、B、C……
```

Personal Agent 会产生一个长期对象：

```text
Goal:
转型到 X

Deadline:
TARGET-DATE

Constraints:
工作时间
收入
所在地
现有技能

Projects:
学习
作品
招聘信息
人脉
简历

Evidence:
招聘需求
岗位变化
技能缺口

State:
持续变化
```

随后几个月：

```text
发现招聘市场出现变化
        ↓
重新分析技能需求
        ↓
调整学习计划
        ↓
发现你项目停滞
        ↓
重新排计划
        ↓
发现合适岗位
        ↓
分析 JD
        ↓
比较你的能力
        ↓
准备材料
```

这就不是 chatbot 了。

而是：

> **持续存在的认知代理。**

Pydantic Harness 现在已经有跨 session Memory 和 durable execution 的基础组件；后者允许 Agent 在程序重启、API 故障、长时间等待以及 human-in-the-loop 工作流中保持执行进度。

但目前一个非常真实的问题是：**Memory 还不能等同于“可信世界模型”**。Pydantic 自己的文档都明确警告，Agent 写入的 memory 属于未可信内容，没有天然的来源证明，也不能因为“记住了”就认为事实是真的。

这实际上正好引出下一代。

---

### 3. 我认为下一代不会主要是“更强的 Agent”

而会是：

### **Persistent Cognitive Runtime**

即“持续存在的认知运行时”。

现在这一代大致还是：

```text
Task
 ↓
LLM
 ↓
Planning
 ↓
Tools
 ↓
结果
```

下一代我认为会变成：

```text
                   ┌──────────────┐
                   │   Goals      │
                   └──────┬───────┘
                          │
                          ▼
                  ┌──────────────┐
                  │ World Model  │
                  └──────┬───────┘
                         │
              ┌──────────┼───────────┐
              ▼          ▼           ▼
           Memory      Beliefs     Events
              │          │           │
              └──────────┼───────────┘
                         ▼
                   Goal Manager
                         │
                         ▼
                  Planner/Synthesizer
                         │
           ┌─────────────┼─────────────┐
           ▼             ▼             ▼
        Agent         CodeMode       Skills
           │             │             │
           └─────────────┼─────────────┘
                         ▼
                  Capability Mesh
                         │
               MCP / API / Computer
                         │
                         ▼
                     世界
                         │
                         ▼
                Observation / Feedback
                         │
                         └────→ World Model
```

最关键的变化有几个。

---

#### 第一：Memory → World Model

目前 memory 通常还是：

```text
用户喜欢什么
发生过什么
有哪些笔记
```

下一代应该是结构化的：

```text
Person
Project
Machine
Document
Goal
Task
Event
Belief
Constraint
Resource
Decision
```

以及关系：

```text
Project A
 ├─ depends_on → Person B
 ├─ blocked_by → Task C
 ├─ deadline → TARGET-DATE
 ├─ related_to → Document D
 └─ supports → Goal X
```

而事实本身还应该具有：

```text
source
timestamp
confidence
valid_until
contradictions
```

这样：

```text
Memory
```

才真正升级为：

```text
World State
```

这一步我认为极其重要。

---

#### 第二：Prompt-driven → Event-driven

今天是：

```text
你问它
↓
它工作
```

下一代：

```text
世界发生变化
↓
Agent 判断是否重要
↓
更新自己的世界模型
↓
判断是否影响已有目标
↓
必要时启动任务
```

例如：

```text
收到邮件
↓
发现供应商交货延期
↓
发现它影响 Project A
↓
Project A 影响周五检修窗口
↓
Agent 自动重新计算方案
↓
只在需要你决策时找你
```

这时候“聊天窗口”反而只是 UI 之一。

---

#### 第三：Planning → Program Synthesis

CodeMode 已经出现这个趋势。

模型不再只是：

```text
next tool = search()
next tool = read()
```

而是：

```python
async def solve():
    ...
```

Pydantic 当前的 CodeMode 已经允许模型在 sandbox 中通过循环、条件、变量、并行调用来编排工具，从而把很多模型回合压成一次程序执行。

下一阶段很可能是：

```text
Task
↓
生成临时程序
↓
执行
↓
测试
↓
检查结果
↓
失败则修改程序
↓
最终保留有价值的程序
```

也就是说：

> **推理结果不只是答案，还可以沉淀为软件。**

---

#### 第四：Skills → Self-created Skills

这一点其实已经开始出现了。

Pydantic AI Harness 现在已经有非常值得注意的 `Runtime Capability Creation`：

> Agent 可以在一次运行中自己编写、验证并保存新的 Pydantic Capability，在下一次运行中加载使用。

这已经出现一点：

```text
Agent 遇到问题
 ↓
发现没有合适能力
 ↓
自己写 capability
 ↓
验证
 ↓
保存
 ↓
以后直接使用
```

下一代真正成熟以后应该变成：

```text
遇到新问题
   ↓
解决一次
   ↓
总结可复用模式
   ↓
生成 Skill / Tool / Program
   ↓
自动测试
   ↓
安全检查
   ↓
性能评估
   ↓
加入能力库
```

于是一个长期运行的 Agent：

```text
第 1 天
能力 = 100

第 100 天
能力 = 180

第 1000 天
能力 = 600
```

而且这些不是模型权重里的“隐性能力”。

是：

> **它真正自己积累的软件能力。**

我认为这一点比简单的“模型上下文越来越长”重要得多。

---

#### 第五：Execution → Simulation → Execution

现在 Agent：

```text
思考
↓
执行
```

下一代应该大量使用：

```text
思考
↓
模拟
↓
预测结果
↓
Verifier
↓
执行
↓
观察真实结果
↓
比较预测
↓
更新模型
```

也就是：

> **先在内部世界里做实验，再作用于真实世界。**

对于工业领域尤其明显：

```text
修改参数
```

不能直接：

```text
LLM → PLC
```

而应该：

```text
LLM
↓
Digital Twin
↓
模拟
↓
Safety Constraints
↓
Verifier
↓
Human Approval
↓
PLC
```

这会逐渐产生真正的因果学习能力。

---

### 第六：Agent Framework → Agent OS

所以我认为未来真正重要的东西不会叫：

```text
Agent Framework 4.0
```

而会越来越类似：

```text
Agent Operating System
```

底层：

```text
MCP
APIs
Filesystem
Computer
Robotics
Sensors
```

类似“设备”。

中层：

```text
Capability
Permission
Sandbox
Transactions
Scheduler
Durability
Memory
```

类似“操作系统”。

上层：

```text
World Model
Goal Manager
Planner
Learner
Verifier
Self-improvement
```

类似“认知系统”。

然后最上面才是：

```text
用户
```

---

### 回到 AGI 那个问题

我认为最值得注意的路径不是：

```text
GPT-6
↓
GPT-7
↓
GPT-8
↓
突然 AGI
```

也可能是：

```text
Frontier Model
      +
Persistent World Model
      +
Long-term Memory
      +
Dynamic Programs
      +
Thousands of Capabilities
      +
Specialized Agents
      +
Simulation
      +
Verification
      +
Continuous Learning
      +
Self-created Tools
      +
Long-running Goals

              ↓

      System-level AGI
```

也就是说：

> **AGI 可能首先是一种系统属性，而不是一个模型属性。**

Pydantic AI 这类东西真正值得关注的原因就在这里。

它看起来只是：

```text
一个 Python Agent Framework
```

但它正在探索的其实是：

```text
如何把一个概率模型
包装成一个
持续存在、能行动、能记忆、能编程、能扩展自身能力的
软件实体
```

**我认为再下一代真正的分界点不是“Agent 会不会调用工具”，而是：**

> **Agent 能不能持续维护一个关于现实的可信模型，并根据目标主动行动；行动结果又能反过来修正它的世界模型和自身能力。**

一旦这个闭环稳定下来：

```text
Observe
  ↓
Model
  ↓
Plan
  ↓
Act
  ↓
Verify
  ↓
Learn
  ↓
Improve
  └────────→ Observe
```

那时讨论它到底算不算 AGI，反而可能已经没有今天这么重要了。
