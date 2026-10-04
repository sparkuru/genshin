# Trellis Plus 检查清单

文件名固定为 `CHACKLIST.md`，供本 skill 与复制用 prompt 引用。

## 使用与报告约定

- 每次初始化/bootstrap、应用、重应用或只读复查，先读取与实际使用的 `SKILL.md` 同目录的本文件。授权初始化完成后重新判定适用性；应用增强后逐项自检，不能只凭写入成功就宣称完成。
- 本文件是当前 skill 的检查目录；[SKILL.md](SKILL.md) 与各条来源定义具体要求。完整复查/默认应用覆盖所有当前编号，读取来源中相关的具体程序，不以清单摘要代替来源。发现清单与来源不一致时指出具体差异，不宣称检查完整通过。
- 仅执行用户授权的范围。只读检查输出建议，不自动修复或运行有副作用的检查。明确限定某项增强时，只检查相关编号并说明未检查的范围，不能把范围外条目记为不适用或擅自安装额外增强。
- 每项独立要求按需拆为子编号（如 `16.1`），报告约束、现有情况及证据、目标情况、建议及影响路径。配置内容、实际加载与运行结果分开说明；没有活动任务或执行环境时明确尚未验证的场景。
- 接受有证据的等价方案与项目例外，保留用户值。当前目标仓库的共享 spec 是项目规则来源；不要把本文件复制到仓库形成第二套策略，也不要让未来项目任务必须访问此 skill 安装目录。

| 状态 | 判定 |
| --- | --- |
| PASS | 适用要求有具体证据满足；全部独立要求满足才可整项通过。 |
| GAP | 缺失、过时、部分满足或与目标不一致，说明差距。 |
| UNKNOWN | 证据不足、检查无法执行或只读范围无法确认，说明所需验证；不算 PASS。 |
| N/A | 按项目/任务条件不适用，说明依据；缺工具、缺测试和缺证据不等于不适用。 |

完整报告使用下表，保留 PASS 与条件项并统计各状态；报告后由用户选择保持现状或批准具体修改。授权后的收尾使用同一清单再次报告，未执行的验证写明未执行。

| 编号 | 约束及依据 | 状态 | 现有情况与证据 | 目标情况 | 建议修改及影响路径 |
| --- | --- | --- | --- | --- | --- |

## Skill 更新时同步维护

每次更新 Trellis Plus，在同一变更中同步核对并更新本文件，包括 `SKILL.md`、增强 registry、references 及其他支持行为的变化。新增要求增加编号，修改要求同步适用条件、目标与证据，撤销要求移除对应条目且不复用编号；未改变的编号保持稳定。

即使没有检查要求变化，也要核对全部受影响条目并更新下面的最近同步说明，写明实际审阅范围和结论。Prompt 只引用当前清单；仅其读取、报告或授权流程变化时同步修改 prompt，不保留固定检查项副本。

完成更新前确认：registry 各增强和跨项规则有覆盖、来源链接可解析、初始化/应用/复查入口必读本文件，skill 校验及 diff 检查通过。不同步清单的 skill 更新仍属未完成。核查发现同步缺口时，目标仓库的复查不得擅自修改 skill。

最近同步说明：建立当前清单，迁入原 prompt 的 01–32 项并补充 33；核对当前 `SKILL.md` 与全部 10 份 references，包括预览控制台契约；同步初始化/应用/复查加载与 prompt 引用流程。

2026-10-04 补充同步核对：预览控制台 reference、registry 与 Docker bootstrap 的强制链接，对应 16–21 项；统一输出、`ip -br a` 全地址发现与真实就绪要求已由 18–19 完整覆盖，本次不新增或复用编号。核对所有 registry 增强、来源链接及初始化/应用/复查的当前清单入口，保留其余检查项与 prompt 约定。

## 检查项

### 01. 文件归属与写入边界

- 适用条件：所有仓库。
- 核对要求：区分受保护 Trellis 文件、项目共享文件、个人/本地配置和普通项目代码；既有混合文件的来源是否明确。
- 验证证据：git 状态、候选路径归属、来源信息及共享写入规则。
- 依据：[SKILL.md](SKILL.md)、[references/license-safe-file-policy.md](references/license-safe-file-policy.md)。

### 02. 受保护材料

- 适用条件：所有仓库；不存在的受保护材料注明未发现，不据此推断整个安装完整。
- 核对要求：workflow、scripts、agents、config、更新元数据、备份、Trellis 管理的 AGENTS 块及平台文件是否被当作只读；既有违规改动只记录，不自动恢复。
- 验证证据：受保护路径清单、实际 diff 和 Trellis 管理/生成来源；只报告既有改动。
- 依据：[references/license-safe-file-policy.md](references/license-safe-file-policy.md)。

### 03. 共享配置唯一来源

- 适用条件：已初始化 Trellis 的仓库；未初始化时在初始化方案中列出目标，不能提前写入。
- 核对要求：.trellis/spec/trellis-plus/index.md 及其详情文件的归属、跟踪意图、链接和加载条件是否明确，是否存在重复或冲突的规则副本。
- 验证证据：共享 index、ownership/source/tracking 信息、详情链接及重复规则检查。
- 依据：[SKILL.md](SKILL.md)、[references/license-safe-file-policy.md](references/license-safe-file-policy.md)。

### 04. 规则可执行与可移植性

- 适用条件：所有已应用或拟应用的项目共享规则。
- 核对要求：触发条件、具体动作、项目实际路径/命令、例外和验证方法是否齐全；未来 agent 是否无需作者机器路径或本次对话即可使用。
- 验证证据：逐项规则正文中的触发、动作、项目命令、例外、成功/失败判断；未知能力明确标记。
- 依据：[SKILL.md](SKILL.md)。

### 05. 策略加载

- 适用条件：已有共享配置或正在应用增强的仓库；当前任务与未来任务入口分开检查。
- 核对要求：当前任务 implement/check context 是否实际引用所需共享规则；不跟随 Markdown 链接的加载器是否显式注册详情；未来任务入口是否可加载，缺口和手动步骤是否明确。没有活动任务时注明该场景尚无法验证。
- 验证证据：任务启动路径、AGENTS 读取机制、implement/check 记录或已解析输入；注明没有自动入口时的精确手动步骤。
- 依据：[SKILL.md](SKILL.md)。

### 06. 更新韧性

- 适用条件：已应用 Trellis Plus 的仓库；实际 update/备份恢复场景按可用证据检查。
- 核对要求：共享增强是否位于非模板覆盖目标，trellis update 后的规则、mainline、上下文和工具路径是否仍有效；旧备份内容是否被错误恢复到受保护文件，是否滥用 update.skip。
- 验证证据：版本/模板元数据、实际模板目标、最近相关备份和加载路径；没有 update 场景证据时不宣称经历更新验证。
- 依据：[SKILL.md](SKILL.md)、[references/license-safe-file-policy.md](references/license-safe-file-policy.md)。

### 07. 个人配置与暂存规则

- 适用条件：所有仓库。
- 核对要求：平台设置、.env 和本地状态是否保持本地；是否规定仅暂存明确路径、检查候选归属与 git diff --check，避免宽泛/强制暂存和收集无关改动。既有已跟踪个人文件只报告。
- 验证证据：ignore/跟踪状态、明确候选路径、暂存前检查规则和可用 staged diff；不实际暂存来测试。
- 依据：[references/license-safe-file-policy.md](references/license-safe-file-policy.md)。

### 08. 许可证与第三方 notices

- 适用条件：保留或分发第三方材料的仓库；普通依赖复用既有许可报告，不要求全部 vendor。
- 核对要求：实际保留材料的精确版本、来源、LICENSE/NOTICE/COPYRIGHT、third_party 或等价清单及原始声明是否齐全；缺失或未知记录 license-notice-needed，不擅自改根许可证。
- 验证证据：精确版本/源路径、第三方清单和 notice 文件，对照来源原文；缺失写明 license-notice-needed。
- 依据：[references/license-safe-file-policy.md](references/license-safe-file-policy.md)。

### 09. 开发阶段与例外

- 适用条件：所有仓库；每个已发布或有真实数据的受影响表面单独注明例外。
- 核对要求：开发默认值、已发布接口/真实用户/外部契约/生产数据例外、开发访问和认证便利边界是否有依据。
- 验证证据：开发阶段判断、外部承诺/数据证据、开发配置及网络/认证约束。
- 依据：[references/development-principles.md](references/development-principles.md)。

### 10. 实现与范围约束

- 适用条件：所有仓库；规则配置与具体任务的遵守证据分开记录。
- 核对要求：复用现有执行路径、避免无依据的抽象与兼容层、保护数据、控制依赖和改动范围、明确预期失败是否落实。
- 验证证据：共享规则、任务验收与已有变更证据；数据可丢弃性必须有依据。
- 依据：[references/development-principles.md](references/development-principles.md)。

### 11. 诊断与验证纪律

- 适用条件：所有仓库；没有诊断或验证任务证据时，只评估配置，不虚称执行通过。
- 核对要求：是否先建立行为和原因证据，验证真实用户行为，区分假设、实现和已验证结果，避免削弱断言、掩盖错误或过度验证。
- 验证证据：复现/原因证据、实际执行路径、真实检查命令和结果，明确未运行与失败。
- 依据：[references/development-principles.md](references/development-principles.md)。

### 12. 工作区与文档纪律

- 适用条件：所有仓库。
- 核对要求：是否保留用户改动、仅清理本任务临时产物、README 仅显式授权后修改、任务资料复用正常 Trellis 目录。
- 验证证据：git 状态/已有 diff、任务资料位置、README 修改授权及已知临时文件的来源。
- 依据：[references/development-principles.md](references/development-principles.md)。

### 13. 项目验证档案

- 适用条件：所有仓库；按项目真实工具链选取检查。
- 核对要求：自动检查、实际命令、风险加测、人工专属检查和不可运行项是否由 manifest/CI/任务证据支撑。
- 验证证据：manifest、CI、项目验证 profile、PRD/check 内容及精确检查命令。
- 依据：[references/submit-ready-human-review.md](references/submit-ready-human-review.md)。

### 14. 提交前人工评审

- 适用条件：所有已应用或拟应用 Trellis Plus 的仓库；当前任务尚未到提交点时不执行提交流程。
- 核对要求：human-required / human-optional / human-not-needed 的触发、阻塞规则、具体反馈内容与已有授权复用是否明确；是否发生在提交/完成/归档之前，安装规则是否误改任务状态。
- 验证证据：gate 正文、阻塞与非阻塞反馈格式、已授予授权及任务证据；检查增强未改变任务状态。
- 依据：[references/submit-ready-human-review.md](references/submit-ready-human-review.md)。

### 15. 开发命令入口

- 适用条件：需要开发工具链的项目；现有等价 wrapper 可满足，缺失时检查具体 before-dev checkpoint。
- 核对要求：hako 或等价 wrapper、工具链、Docker 使用路径、执行权限与限制是否可复用；缺失时是否有明确 before-dev checkpoint，不虚称权限已授予。
- 验证证据：wrapper/生命周期路径、工具链、基础 skill 路由、配置和执行限制；规则文件不是运行权限证明。
- 依据：[references/dev-it-in-docker-bootstrap.md](references/dev-it-in-docker-bootstrap.md)。

### 16. 服务与预览生命周期

- 适用条件：存在可预览服务的项目；库/CLI 等无此服务的项目应给出 N/A 依据。
- 核对要求：有预览服务时检查 preview.sh 与既有生命周期复用，start/stop/down/status/build、后台启动、就绪探测、重复调用、从其他目录调用、仅停止所属服务及保留数据；首用 build 再 start，启动不隐式安装/构建/测试。无服务时以证据标记 N/A。
- 验证证据：脚本实现、文档化命令、既有 smoke 结果；实际启停/build 要有授权，未运行明确记录。
- 依据：[references/dev-it-in-docker-bootstrap.md](references/dev-it-in-docker-bootstrap.md)。

### 17. 预览网络

- 适用条件：存在开发/预览服务的项目；遵守已明确的网络限制。
- 核对要求：实际监听与发布地址/端口、可信 LAN 默认和明确网络限制、动态端口、容器内部与主机可访问端点是否区分；不擅自改防火墙或额外暴露端口。
- 验证证据：有效 bind、主机发布映射、服务端口、动态值与网络例外；配置值不等于实际可达性。
- 依据：[references/dev-it-in-docker-bootstrap.md](references/dev-it-in-docker-bootstrap.md)、[references/development-principles.md](references/development-principles.md)。

### 18. 预览控制台契约

- 适用条件：存在 Trellis Plus 预览入口的项目，不因框架或服务不同豁免输出契约。
- 核对要求：是否采用当前 preview-console-contract.md 的完整要求，包括 System is ready.、Open / Local only (preview host) / Listeners / Published / Internal only / Notes 的顺序和格式、服务分组、每行完整 URL、实际路由和协议、日志及秘密处理。
- 验证证据：renderer 与共享 development spec 对照完整参考格式；已有 fixture/输出证据，不能只搜索 section 名就 PASS。
- 依据：[references/preview-console-contract.md](references/preview-console-contract.md)。

### 19. 主机地址发现与就绪真实性

- 适用条件：存在预览服务的项目；主机通配发布触发地址枚举要求，其余分支检查对应暴露规则。
- 核对要求：通配主机发布时是否在发布预览的主机执行 ip -br a，枚举全部合格地址，为每个入口生成 URL，正确处理 loopback/IPv6/容器内部地址及缺失 ip；所有必要服务就绪后才显示成功，不把映射、运行状态或地址候选当作可达性证明。
- 验证证据：发布主机上的 ip -br a 证据、地址解析/URL 生成分支、listener/映射与逐服务 readiness；地址候选不证明跨设备访问。
- 依据：[references/preview-console-contract.md](references/preview-console-contract.md)。

### 20. 环境配置

- 适用条件：需要可配置开发值、已有环境文件或新增配置的项目；预览服务适用根 .env 的额外要求。
- 核对要求：.env.example 或等价示例是否无秘密、键与真实消费者一致；预览根 .env 的账号、Docker 变量及监听/发布配置是否接入实际路径；加载和覆盖顺序、首次设置、需用户填写项及重启/重建步骤是否明确，不把 dotenv 当 shell 代码执行。
- 验证证据：示例键名、实际 loader/消费者/Compose 注入、优先级和 first-setup 说明；仅显示本地键名，不输出秘密值。
- 依据：[references/environment-configuration.md](references/environment-configuration.md)。

### 21. 配置增量更新

- 适用条件：已有或本次新增环境配置的项目；没有增量变更场景时核对持久规则，运行证据另记。
- 核对要求：已有值、空值、注释和格式是否保留，仅追加缺失键且重复执行不重复追加；重命名/删除键及已跟踪秘密文件是否报告而非擅改用户值或历史。
- 验证证据：增量逻辑与临时 fixture/已有验证记录，包括缺文件、自定义值、空值、新键和第二次运行；不展示本地 secret diff。
- 依据：[references/environment-configuration.md](references/environment-configuration.md)。

### 22. 前端识别与 UUPM 初始化

- 适用条件：仓库或活动任务具有前端/UI；backend-only 项目以实际证据标记 N/A。
- 核对要求：前端/UI 判断是否有实际证据；活动平台的项目本地入口及依赖是否完整；缺失时先征得 UUPM 初始化授权，全局安装不算项目初始化，拒绝后仍保留正常前端验证。
- 验证证据：实际 UI 源码/依赖/任务证据、活动平台项目入口及其脚本/data 完整性、已有初始化选择；只读阶段不运行 uipro。
- 依据：[references/ui-ux-pro-max-integration.md](references/ui-ux-pro-max-integration.md)。

### 23. UUPM 工作流

- 适用条件：具有前端/UI 的项目；尚未完成活动平台项目本地 UUPM 初始化时记录前提缺口或无法验证，不能仅因缺工具标记 N/A。用户明确拒绝初始化时可注明该授权例外并跳过 UUPM 工作流，正常 UI 验证仍适用。
- 核对要求：适用时是否覆盖 Plan → Implement → Check → Update Spec，研究和已批准 design 的任务内存放、双阶段上下文、响应式/状态/可访问性要求、稳定规则提升及来源许可边界。
- 验证证据：共享工作流、任务 research/design、批准记录、implement/check 引用和 UI 检查结果；无任务时说明运行场景未验证。
- 依据：[references/ui-ux-pro-max-integration.md](references/ui-ux-pro-max-integration.md)。

### 24. 浏览器自动化

- 适用条件：具有浏览器可访问 UI 的项目/任务；原生 UI 复用其设备测试流程，不把 Web Playwright 当作替代。
- 核对要求：是否区分 playwright-required / existing-equivalent / not-effective / unavailable，复用既有等价 runner，覆盖变更验收而非只证明页面加载，不用生产数据或个人会话。
- 验证证据：分类依据、已有 runner、目标验收/语义定位器、fixture 边界与真实 test command。
- 依据：[references/playwright-automated-validation.md](references/playwright-automated-validation.md)。

### 25. Playwright 项目档案与证据

- 适用条件：浏览器 UI 的验证档案；使用等价 runner 时依据其真实能力核对等价字段，不强制迁移。
- 核对要求：是否有单一、当前的 Playwright Validation Profile，包含执行模式、依赖/浏览器引导、应用启动与就绪/base URL、focused/CI 命令、配置、浏览器/视口、fixtures、视觉/可访问性策略和失败产物；是否优先读取档案并区分本次结果与持久规则。
- 验证证据：单一项目 profile 的全部字段、仓库命令与 CI 配置、加载入口和任务产物路径；缺字段逐项拆分。
- 依据：[references/playwright-automated-validation.md](references/playwright-automated-validation.md)。

### 26. 桌面与移动验证

- 适用条件：受影响的 UI 任务；按证据分别判定移动适用性、模拟与真实设备验证。
- 核对要求：是否在实现前判定 mobile-required / not-applicable / unavailable，适用任务分别记录桌面和窄屏交互/最终状态；排除是否有证据，模拟是否与真实设备验证区分；快照变更审核及失败 trace/截图/日志是否保留。
- 验证证据：移动适用性、已批准设计/验收、具体 viewport/device、交互与最终状态断言、桌面/移动独立结果及失败产物。
- 依据：[references/playwright-automated-validation.md](references/playwright-automated-validation.md)。

### 27. 人工与自动化的衔接

- 适用条件：需要提交前验证的项目/任务；只对实际残余风险要求人工反馈。
- 核对要求：可自动化项是否先做自动化，人工反馈是否只覆盖残余主观、真实设备、硬件或私有环境风险；无法运行的实质检查不能当作 PASS。
- 验证证据：可运行检查记录、自动化阻塞、残余风险和具体人工反馈请求，不能用泛化 smoke 请求替代可自动化检查。
- 依据：[references/submit-ready-human-review.md](references/submit-ready-human-review.md)、[references/playwright-automated-validation.md](references/playwright-automated-validation.md)。

### 28. 任务归档署名

- 适用条件：Codex/ChatGPT 参与的任务；非 Codex 工作不要求该署名，也不回填历史贡献。
- 核对要求：Codex 参与任务是否仅在成功归档提交中使用一次准确 trailer：Co-authored-by: OpenAI Codex <codex@openai.com>；普通工作/单独 journal 提交不由该规则加署名，不虚构历史贡献或改变 Git 身份。
- 验证证据：归档 policy、相关任务与成功归档提交消息，准确 trailer 恰好一次；失败/历史缺署名只报告。
- 依据：[references/chatgpt-codex-commit-trailer.md](references/chatgpt-codex-commit-trailer.md)。

### 29. 归档执行路径

- 适用条件：采用 Codex 任务归档署名的项目；缺少活动任务不妨碍检查支持接口，但不能虚称本次已归档。
- 核对要求：是否验证实际归档/日志命令、自动提交和暂存范围、消息入口或禁用自动提交的受支持路径；不支持时报告 archive-attribution-blocked，重试不重复归档/署名，不补空提交或自动改历史。
- 验证证据：实际归档/日志实现与接口、自动暂存路径、单任务路由、重试状态检查和 archive-attribution-blocked 处理规则。
- 依据：[references/chatgpt-codex-commit-trailer.md](references/chatgpt-codex-commit-trailer.md)。

### 30. 需求导入与 mainline

- 适用条件：所有仓库均检查连续性规则；有已声明主线或相关需求时检查 mainline 实体，无来源/目标时不要求编造记录。
- 核对要求：有主线或相关需求时是否建立 .trellis/mainline.md，保留来源、批准/草案/冲突、范围/非目标、验收和待决项；缺少目标时不编造主线，导入不改写源文档或擅自批准需求。
- 验证证据：需求源路径/章节、批准与 supersession 证据、mainline 中范围/验收/有序工作/依赖/决策；未批准内容保持 proposed。
- 依据：[references/mainline-continuity.md](references/mainline-continuity.md)。

### 31. 主线生命周期与 Project Pulse

- 适用条件：有相关项目状态/继续工作请求或任务生命周期的仓库；无记录场景应报告缺失证据。
- 核对要求：任务开始、中断恢复、批准变更、验证和归档是否维护证据；无任务时 Pulse 是否只读，明确当前目标、已完成证据、阻塞、候选与允许动作，未验证实现不算已完成验收。
- 验证证据：主线与任务映射、批准变更、真实验证和归档/commit 引用，Pulse 的证据及允许动作；静态存在不证明全生命周期执行。
- 依据：[references/mainline-continuity.md](references/mainline-continuity.md)、[references/development-principles.md](references/development-principles.md)。

### 32. 延续授权与职责

- 适用条件：所有项目的连续性规则；serial/paused 分支仅在有相应授权/状态时核对实际行为。
- 核对要求：guided 只建议并等用户选择，paused 不创建/实施，serial 仅推进明确授权列表中就绪项并遵守停止条件；是否沿用正常任务系统、保持主会话与 worker 职责，避免另建调度器或无限自动推进。
- 验证证据：guided/serial/paused 规则、明确串行授权列表/顺序/停止条件、主会话和 worker 职责及正常任务机制。
- 依据：[references/mainline-continuity.md](references/mainline-continuity.md)。

### 33. 当前清单读取与完整自检

- 适用条件：所有 Trellis Plus 初始化/bootstrap、应用、重应用和复查。
- 核对要求：读取实际使用的 skill 同目录最新 `CHACKLIST.md`，从当前条目生成报告；初始化后重判适用性，应用后逐项自检；完整检查保留所有编号及 PASS/N/A，限定范围明确未检查项；缺失清单、来源冲突或缺少运行证据不能宣称完整通过。
- 验证证据：报告中的 skill/清单实际来源、当前编号覆盖、依据链接、适用性及逐项证据；初始化或应用前后检查结果与剩余 GAP/UNKNOWN；原 prompt 不含旧的固定清单副本。
- 依据：[SKILL.md](SKILL.md) 中的 Operating Rules、Discovery Workflow 与 Checklist Self-Check And Skill Maintenance，以及本文件的使用与报告约定。
