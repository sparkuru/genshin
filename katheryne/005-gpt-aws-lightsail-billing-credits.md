# AWS Lightsail Billing and Credits Planning

## Turn Index

| # | Export | Q | A | Note |
| --- | --- | --- | --- | --- |
| 1 | keep | Ask when AWS Lightsail starts billing and what charges may still require payment before new-account credits expire. | Explain that Lightsail resources accrue charges from creation, credits may offset eligible usage, and some items such as taxes or domain registration may bypass promotional credits. | billing rules and credit limits |
| 2 | keep | Ask for the billing timeline for a single low-cost Lightsail instance with modest monthly traffic and no other subscribed services. | Estimate that the eligible instance should be free during the Lightsail trial, then consume credits after the trial, with cash billing only after credits expire or unsupported charges appear. | concrete Lightsail cost scenario |
| 3 | keep | Ask how to spend remaining AWS promotional credits within six months on useful service experiments. | Recommend a controlled learning path across Bedrock, serverless, RDS, S3 and CloudFront, IoT, monitoring, and security while avoiding services that can burn credits quickly. | six-month service exploration plan |

## 1. Clarify Lightsail Billing Start

<h3 align="center"><strong>USER</strong></h3>

一个新注册的 AWS global 账户启用了 Lightsail 服务；需要判断这项服务什么时候开始收费，以及在 promotional credits 到期前可能还需要支付哪些费用。

<h3 align="center"><strong>ASSISTANT</strong></h3>

结论：**Lightsail 从资源创建后就开始产生计费记录；但实际是否扣银行卡，取决于账户计划、免费试用、100 美元 credit 是否还能抵扣。**

#### 1. 100 美元不是现金余额

AWS 新账户现在会给 **100 美元 credits**；Free plan 通常最多 6 个月，或 credits 用完，以先到者为准。AWS 官方说明：Free plan 不会产生收费，除非账户升级到 Paid plan 或启用 paid-only 服务；Paid plan 下，超出 credit 或 credit 不适用的费用会按量收费。

这些 credits 会自动抵扣符合条件的 AWS 服务费用，直到用完或过期。它不是可提现余额，也不是现金。

#### 2. Lightsail 什么时候开始收费

**创建 Lightsail 实例、数据库、容器、负载均衡、磁盘、快照等资源后，就开始按小时计费。**  
Lightsail 实例和托管数据库即使处于 **stopped** 状态也继续计费，只有删除后才停止该资源的实例费用。

Lightsail 目前有 **90 天免费试用**，但只覆盖指定套餐，例如 Linux/Unix IPv4 的 `$5/mo、$7/mo、$12/mo`，Windows、IPv6-only、Micro container、`$15/mo` managed database 等指定项目。

所以判断方式是：

| 情况 | 是否扣银行卡 |
|---|---|
| 还在 Free plan，且未启用 paid-only 服务 | 一般不会扣 |
| 已升级 Paid plan，但还有 100 美元 credits | 符合条件的费用先扣 credits |
| credits 用完 / 过期 | 开始扣银行卡 |
| 使用 credit 不覆盖的项目 | 即使还有 credits，也可能扣银行卡 |
| Lightsail 免费试用外的资源或超额用量 | 先扣 credits；credits 不够再扣银行卡 |

#### 3. 额度到期前，最可能产生的费用

这些费用通常会先消耗账户内的 100 美元 credits：

1. **Lightsail 实例套餐费**  
   例如 `$5/mo`、`$7/mo`、`$12/mo` 等。实例停止也继续计费，删除才停。

2. **托管数据库费用**  
   数据库也是直到删除才停止计费，停止状态不等于免费。

3. **超出流量包的出站流量费**  
   Lightsail 套餐有流量额度；超出后，只对超额的 **outbound data transfer** 收费。免费试用期内超额流量也会收费。东京区超额出站是 `$0.14/GB`，新加坡是 `$0.12/GB`。

4. **未绑定实例的 Static IPv4**  
   Static IP 绑定在 Lightsail 实例上不额外收费；未绑定超过 1 小时后，按 `$0.005/hour` 收费。

5. **快照、块存储、负载均衡、对象存储、CDN 超额**  
   快照是 `$0.05/GB-month`；块存储从 `$0.10/GB-month` 起；Load balancer 是 `$18/mo`；对象存储和 CDN 超出免费额度后也计费。

6. **域名注册 / 续费 / 转入**  
   这类通常属于 Route 53 domain registration/transfer，AWS Promotional Credit 明确不抵扣这类费用，可能直接扣银行卡。

7. **税费**  
   AWS Promotional Credit 不抵扣销售税、使用税等交易税。账单地址触发税费时，可能需要银行卡支付。

#### 4. 实际判断

如果只是开了一个普通 Lightsail 小实例，未买域名、未开负载均衡、未做大量出站流量、未留未绑定静态 IP，那么在 100 美元 credits 到期或用完前，通常不会实际扣银行卡。

真正需要防的是：

- 停止实例但没删除；
- 删除实例后保留了快照、磁盘、静态 IP；
- 用了域名注册；
- 流量被爬虫、扫描器、下载流量打爆；
- 升级成 Paid plan 后忘记资源仍在跑；
- credits 到期后资源还存在。

## 2. Estimate Single Instance Cost

<h3 align="center"><strong>USER</strong></h3>

示例场景是一台 `$7/mo` 的 Lightsail 服务器，区域为日本东京，每月流量约 50GB，除此之外没有其他服务订阅；需要估算当前费用状态和后续时间节点。

<h3 align="center"><strong>ASSISTANT</strong></h3>

按示例场景描述：**东京区 Lightsail $7/mo Linux/Unix IPv4 实例，月流量约 50GB，无其他服务。正常情况下，当前不会产生现金扣款。**

#### 当前状态

这个 $7/mo Lightsail 实例属于 AWS Lightsail 免费试用覆盖范围：Linux/Unix IPv4 的 `$5/$7/$12` 套餐可试用 90 天；免费试用从第一个符合条件的 Lightsail 资源启动时开始。 

这个 `$7/mo` 套餐包含：

| 项目 | 数值 |
|---|---:|
| 内存 | 1 GB |
| vCPU | 2 |
| SSD | 40 GB |
| 月流量包 | 2 TB |

AWS Lightsail 官方价格表列明 `$7/mo` Linux/Unix IPv4 套餐为 1GB 内存、2 vCPU、40GB SSD、2TB Transfer。

每月 50GB 流量远低于 2TB。Lightsail 的入站和出站流量都会计入套餐流量包，但**只有超过套餐额度后的出站流量**才收费；东京区超额出站流量价格是 `$0.14/GB`。

所以流量部分：**0 美元**。

#### 时间节点

按 Lightsail 实例创建日作为第 0 天估算：

| 时间 | 状态 | 费用结果 |
|---|---|---:|
| 第 0 天 | Lightsail 90 天试用开始 | `$0` |
| 当月账期结束 | 首个账期结算 | `$0`，流量未超 |
| 第 2 个账期结束 | 继续处于试用期 | `$0`，流量未超 |
| 第 3 个账期结束 | 试用期接近结束 | `$0`，流量未超 |
| 约第 90 天 | 90 天 Lightsail 免费试用结束 | 开始按 `$7/mo` 计费 |
| 第 90 天之后 | 实例继续运行 | 先扣 AWS credits，不直接扣卡 |
| 约第 6 个月 | 若 AWS 账户/credits 是 6 个月周期，到期 | 仍运行且是 Paid plan，则开始扣银行卡 |

AWS 新账户有 `$100` credits；AWS 官方说明，新 Free Tier 账户创建后立即获得 `$100` credits，最多 6 个月；Free plan 不会收费，除非升级到 Paid plan 或启用 paid-only 服务。  
如果选择 Paid plan，6 个月结束或 credits 用完后，继续按量付费。

#### 实际费用判断

在这个配置下：

1. **前 90 天：基本是 `$0`。**  
   `$7/mo` 实例本身被 Lightsail 试用覆盖；50GB 流量不会超 2TB 包。

2. **90 天后到 credits 到期前：每月约扣 `$7` credits。**  
   不扣银行卡，只消耗 AWS credits。

3. **如果账号和 credits 是 6 个月周期，credits 大概率在注册后约 6 个月到期。**  
   从 90 天试用结束到 credits 到期，单台 `$7/mo` 实例通常只会消耗大约 `$21–22` credits。`$100` credits 通常用不完，主要问题是**到期作废**，不是额度不够。

4. **credits 到期后，如果实例还没删除，且账号是 Paid plan，开始实际扣卡。**  
   之后正常成本约为：  
   **`$7/月`**  
   只要月总流量仍约 50GB，不会有流量超额费。

#### 需要避免的额外费用

示例场景里没有这些资源，所以正常没有额外费用。但如果以后出现，费用会变：

| 项目 | 是否会收费 |
|---|---|
| 只运行这台 `$7/mo` Lightsail | 试用后 `$7/月` |
| 月流量 50GB | 不额外收费 |
| 实例 stopped 但未删除 | 仍计费 |
| 删除实例 | 实例停止计费 |
| 删除实例但保留快照 | 快照继续计费 |
| Static IP 已绑定实例 | 不额外收费 |
| Static IP 未绑定超过 1 小时 | `$0.005/hour` |
| DNS 区域正常使用 | Lightsail DNS 基本免费，超 300 万查询/月才收费 |
| 注册域名 | 单独收费，通常不等同 Lightsail 套餐 |

Lightsail 实例按小时计费，到月套餐上限为止；实例和数据库在删除前都会继续产生费用，即使 stopped 状态也一样。

#### 最终结论

该示例场景的当前风险很低。

在 50GB/月流量、东京区、单台 `$7/mo` Lightsail、无其他服务的条件下：

**现在到 90 天内：应为 `$0`。**  
**90 天后到 credits 到期前：每月约扣 `$7` credits。**  
**credits 到期后：如果实例还在，开始实际扣银行卡，约 `$7/月`。**

## 3. Plan AWS Credit Experiments

<h3 align="center"><strong>USER</strong></h3>

示例账户有约 `$80 + $100` promotional credits，可在 6 个月内用于体验 AWS 服务；需要规划哪些服务最值得尝试，同时避免意外超支。

<h3 align="center"><strong>ASSISTANT</strong></h3>

这些 credits 最值得花在这几类：**Bedrock AI、Serverless、RDS 数据库、S3/CloudFront、IoT/SiteWise、监控与安全**。不建议把额度浪费在长期跑 EC2、大规格数据库、NAT Gateway、EKS、SageMaker 训练、OpenSearch Serverless 这类容易烧钱的服务上。

#### 先定边界

AWS 新账户规则是：注册后有 **$100 credits**，完成 Explore AWS 活动可再拿 **最多 $100 credits**；Free plan 是 6 个月或 credits 用完，以先到者为准。AWS 文档列出的活动包括 EC2、Bedrock、Budgets、Lambda、RDS。

Promotional credits 只能抵扣合格服务。**Route 53 域名注册/转入、AWS Marketplace、AWS Training、AWS Certification、部分 Support、Professional Services、税费**等不抵扣，可能直接扣银行卡。

示例账户约有 **$180 credits**。现有 Lightsail `$7/月`，6 个月最多吃掉 `$42`；如果仍在 Lightsail 90 天试用内，6 个月内实际只会吃掉约 `$21`。可动用额度大致是 **$138–159**。

#### 6 个月体验路线

| 月份 | 体验主题 | 推荐服务 | 预算 |
|---|---|---|---:|
| 第 1 月 | 费用控制 + 基础云架构 | AWS Budgets、Cost Anomaly Detection、IAM、VPC、S3 | `$0–5` |
| 第 2 月 | Serverless Web App | Lambda、API Gateway/Function URL、DynamoDB、S3 | `$0–10` |
| 第 3 月 | 正规数据库 | RDS PostgreSQL/MySQL、备份、快照、参数组 | `$10–25` |
| 第 4 月 | 工控/IoT 数据链路 | IoT Core、IoT Rules、Timestream 或 SiteWise | `$10–30` |
| 第 5 月 | AI 应用 | Amazon Bedrock、Embedding、RAG、小型文本/图片实验 | `$20–50` |
| 第 6 月 | CDN + 安全 + 观测 | CloudFront、WAF、CloudWatch、GuardDuty 30 天试用 | `$10–30` |

总额约 **$50–150**，不会浪费，也能覆盖 AWS 的核心能力。

#### 优先体验 1：Amazon Bedrock

这是最值得用 credits 体验的服务。可尝试：

- 文本生成、总结、翻译、分类；
- 用 Embedding 做小型 RAG；
- 用 S3 存文档；
- 用 Lambda 做 API；
- 用 Lightsail 或静态前端调用后端。

Bedrock 官方说明，价格取决于模型、供应商、模态和区域；按需推理按 token 或图片数量计费。官方示例中，Titan Text Lite 一次 2K input + 1K output 约 `$0.001`；Titan Image 生成 1000 张 1024×1024 标准图约 `$10`。但不要开 Provisioned Throughput，官方示例一个月可能到 `$12,000–27,000+`。

**额度用法：**给 Bedrock 单独留 `$30–50`，足够体验很多次文本、embedding、少量图片生成。

#### 优先体验 2：Serverless 架构

组合：

- Lambda；
- API Gateway 或 Lambda Function URL；
- DynamoDB；
- S3；
- CloudWatch Logs；
- CloudFront。

Lambda 适合学习事件驱动、无服务器后端和低成本 API。AWS Lambda 每月有 100 万次请求免费额度和 400,000 GB-s 免费计算额度；超出后按请求和计算量计费。

**可做项目：**设备状态上报 API、报警 webhook、配置下发接口、轻量后台管理页面。

#### 优先体验 3：RDS 数据库

体验 PostgreSQL 或 MySQL，重点不是跑业务，而是学：

- 创建单 AZ 数据库；
- 参数组；
- 安全组；
- 备份；
- 快照；
- 从 Lightsail/EC2/Lambda 连接数据库；
- 删除数据库时处理 snapshot。

RDS 费用主要来自 DB instance hours、存储、I/O、备份和数据传输；新 Free Tier 账户用 credits 抵扣 RDS 费用。

**额度用法：**开一台小规格 RDS，跑 1–2 周后删除。不要 Multi-AZ，不要 Aurora 大规格，不要保留多份快照。

#### 优先体验 4：IoT Core + SiteWise / Timestream

这类最贴近工控运维。建议做一个“模拟设备数据上云”链路：

```text
模拟设备 / Python 脚本 / MQTT 客户端
        ↓
AWS IoT Core
        ↓
IoT Rule
        ↓
Timestream 或 IoT SiteWise
        ↓
CloudWatch / Grafana / 简单前端
```

IoT Core 官方 Free Tier 可支持一个 50 设备级别的示例负载：设备 24 小时连接、每天交换 300 条消息、使用 Device Shadow 和 Rules。

SiteWise 是专门用于工业设备数据采集、组织、处理和监控的托管服务；它按消息、处理、存储、导出、Monitor、Edge、Alarms 分项计费。SiteWise Edge 的 Data Collection Pack 免费，但 Data Processing Pack 是 `$200/active gateway/month`，不要开启。

**额度用法：**只模拟 5–10 台设备，采样间隔 10–60 秒，不要 1 秒级长期跑。SiteWise 官方示例中，10 台设备每秒 1 个测点，一个月约 `$39.48`；降低采样频率或只跑几天，费用会明显下降。

#### 优先体验 5：S3 + CloudFront

这组适合做静态网站、文件分发、前端托管、下载站、图片站。

CloudFront 新的 flat-rate CDN Free plan 是 `$0/month`，包含 CDN、WAF/DDoS、Route 53 DNS、TLS、Serverless Edge Compute 和一定 S3 storage credits；Free plan 额度包括 1M requests 和 100GB data transfer。

S3 是对象存储，按存储量、请求、数据取回、数据传输等计费；没有最低费用。

**额度用法：**把 Lightsail 网站静态资源放 S3 + CloudFront，学习缓存、HTTPS、WAF、日志。

#### 优先体验 6：安全与观测

应体验：

- AWS Budgets；
- Cost Anomaly Detection；
- CloudWatch Alarm；
- CloudWatch Logs；
- GuardDuty 30 天试用；
- CloudTrail 基础审计。

AWS Budgets 的前两个带动作的 budget 免费，之后 action-enabled budget 会产生费用；普通预算告警适合先设置 `$5/$20/$50/$100` 多级阈值。

GuardDuty 对从未启用过的账户有 30 天 Free Tier 试用；试用结束后继续开着会按分析的数据量计费。

CloudWatch 不要乱开高级功能。普通 alarm 成本低，但 Synthetics、RUM、Internet Monitor、Container Insights、网络监控可能迅速变贵。CloudWatch 官方示例中，一些网络/互联网监控场景可到数百甚至上千美元/月。

#### 不要优先体验的服务

| 服务/功能 | 原因 |
|---|---|
| EKS | 学习价值高，但 Kubernetes 集群、节点、负载均衡、日志都容易烧钱 |
| NAT Gateway | 每小时计费 + GB 处理费；空跑也收费 |
| OpenSearch Serverless | 常驻资源容易持续扣费 |
| SageMaker 训练/Notebook 长期开 | 忘关容易吃掉 credits |
| RDS Multi-AZ / Aurora 大规格 | 不是新手体验阶段该烧的 |
| EC2 多台公网 IPv4 | 公网 IPv4 每个 `$0.005/hour`，约 `$3.6/月/个`，多个很快累积  |
| AWS Config 全量开启 | 配置项、规则评估、合规包都计费，示例账单可到几十美元以上  |
| Route 53 域名注册 | credits 不抵扣 |
| AWS Certification / Training | credits 不抵扣 |

#### 最优组合

按这个学习目标，最有价值的是这套：

```text
Lightsail 网站
  + S3 静态资源
  + CloudFront CDN/WAF
  + Lambda API
  + DynamoDB / RDS
  + IoT Core MQTT 数据上报
  + Timestream 或 SiteWise 存时序数据
  + Bedrock 做报警文本总结/设备状态问答
  + CloudWatch/Budgets/GuardDuty 做监控与安全
```

这套架构能覆盖 AWS 的主干能力：计算、网络、存储、数据库、Serverless、IoT、AI、安全、监控。6 个月内用 `$100–150` credits 足够体验。
