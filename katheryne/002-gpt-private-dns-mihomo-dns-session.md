# Private DNS 与 Mihomo DNS 方案

---

| Field | Value |
| --- | --- |
| source file | HOME-PATH/.codex/sessions/DATE/rollout-DATE-SESSION-ID.jsonl |
| session id | SESSION-ID |
| title source | export plan |
| cwd | WORKSPACE-PATH |
| timestamp | DATE (UTC+OFFSET) |

---

## Turn Index

| # | Export | Q | A | Note |
| --- | --- | --- | --- | --- |
| 1 | keep | 检查本机和 VPS 的 DNS 污染情况，并评估 private DNS 风险。 | 发现本机明文 DNS 被污染、VPS 正常，建议小范围私用 DoH，不开放 53/853。 | main task |
| 2 | keep | 用户安装了 dig，要求补测 VPS DNS。 | 用 dig 验证 VPS 解析干净，并指出上游未做 DNSSEC validation。 | verification |
| 3 | keep | 解释 DoH、DoT，以及 nginx 后面藏 DNS 的拓扑。 | 用拓扑图说明 DoH/DoT/普通 DNS、nginx 反代和后端 resolver 的关系。 | explanation |
| 4 | keep | 查询 DoH/DoT 是否会被发现，以及是否常见因 private DNS 封 VPS IP。 | 检索后说明 DoT 易识别、DoH 可被识别但个人私用长期封 IP 案例不常见。 | risk research |
| 5 | keep | 查看 mihomo 配置是否支持连接自建 DoH，并比较橙云与 DNS only。 | 确认配置已用 DoH，mihomo 支持自建 DoH；实测一个域名走 Cloudflare、另一个直连，建议优先 DNS only。 | config review |
| 6 | keep | 解释 mihomo 代理机制里 DNS 的作用，以及访问 YouTube 时 DNS 在哪一侧解析。 | 说明 HTTP/SOCKS 入口通常以域名进 mihomo 后走代理，DNS 主要用于节点解析、DIRECT 流量和透明代理场景。 | follow-up |
| 7 | exclude | $session-export 保存到桌面，并要求脱敏。 | 仅用于触发归档，不进入正文。 | export request only |

---

## 1. 检查本机和 VPS 的 DNS 污染情况，并评估 private DNS 风险。

---

<h3 align="center"><strong>USER</strong></h3>

$remote-server-tasks  我考虑在 `ssh root@<PRIVATE_SSH_HOST>` 上创建 private dns 服务器；

原因是在大陆境内的 dns 并不安全，存在劫持 / 泄露的情况；

你先用本机测试一下 dns 情况，特别是访问海外服务器；然后在 vps 上测试 dns

最后给我一个方案。（并检索相关实现、事件，回答制作 private dns 是否有风险，例如导致 vps 被墙等）

<h3 align="center"><strong>ASSISTANT</strong></h3>

**结论**
本机网络的明文 DNS 明显不可信；VPS 侧 DNS 正常。可以做 private DNS，但不要做公开递归 DNS，更不要开放裸 `:53` 给全网。推荐在 VPS 现有 `nginx :443` 后面挂一个私有 DoH 入口，后端用 AdGuard Home 或 Unbound，只监听 localhost，并做访问控制、限速和日志最小化。

**测试结果**
本机 `/etc/resolv.conf`：`<LOCAL_ROUTER_DNS>`、IPv6 内网 DNS、`223.5.5.5`。

本机明文 DNS：
- `youtube.com` 返回 `174.132.167.252`
- `wikipedia.org` 返回 `31.13.88.169`
- `telegram.org` 返回 `96.44.137.28`
- 这些结果在 `1.1.1.1`、`8.8.8.8`、`9.9.9.9`、`223.5.5.5`、`114.114.114.114` 上都一致，且和真实 DoH 结果不符。
- DoH 直连对照正常：`youtube.com -> 142.250/142.251...`，`wikipedia.org -> 103.102.166.224`，`telegram.org -> 149.154.167.99`。

这很像路径上的 DNS 注入/污染。GFWatch 论文也记录过 GFW 会注入伪造 IPv4/IPv6，且污染 Google/Cloudflare 等公共 resolver 缓存：[How Great is the Great Firewall?](https://arxiv.org/abs/2106.02167)

VPS `root@<PRIVATE_SSH_HOST>`：
- Debian 13 trixie，root 登录正常。
- 系统 DNS：`<VPS_INTERNAL_DNS>`。
- 默认解析正常：`youtube.com -> 142.250/142.251...`，`wikipedia.org -> 103.102.166.224`，`telegram.org -> 149.154.167.99`。
- HTTPS 访问海外站正常。
- 当前端口：`80/443` 被 nginx 占用；`53/853` 未监听；有 `systemctl`、`docker`、`nginx`。

**推荐方案**
1. 后端：AdGuard Home 或 Unbound  
   - 想要管理界面、客户端配置、过滤规则：用 AdGuard Home。它官方支持 DoH/DoT/DoQ/DNSCrypt，并要求公网 IP、域名和 TLS 证书：[AdGuard Home DNS encryption](https://adguard-dns.io/kb/adguard-home/encryption/)
   - 想要轻量、少暴露面、纯递归缓存：用 Unbound。Unbound 配置支持 `access-control`，且 `unbound-checkconf` 可校验配置：[Unbound docs](https://unbound.docs.nlnetlabs.nl/en/latest/manpages/unbound.conf.html)

2. 暴露协议：优先 DoH over 443  
   - RFC 8484 定义 DoH，即 DNS 查询映射到 HTTPS 请求：[RFC 8484](https://datatracker.ietf.org/doc/html/rfc8484)
   - 不建议优先用 DoT `853`。RFC 7858 规定 DoT 默认端口是 `853`，这在跨境网络里非常容易被识别和单独干扰：[RFC 7858](https://datatracker.ietf.org/doc/html/rfc7858)

3. nginx 架构：
   - nginx 继续占用 `443`
   - 后端 DNS 服务只监听 `127.0.0.1`
   - nginx 反代 `/dns-query` 到后端 DoH
   - 加 `limit_req`、访问日志脱敏或关闭 query 日志
   - 如客户端 IP 稳定，直接 nginx allowlist；不稳定则至少用随机子域名/路径降低被扫到概率

4. 明确不要做：
   - 不要开放全网 UDP/TCP `53`
   - 不要做 open resolver
   - 不要公开分享这个 DNS
   - 不要把它和代理/VPN 混在同一个域名和 IP 行为上

**风险判断**
- 被墙风险：有，但比 VPN/代理低。DNS 只解决“域名解析被污染”，不解决 IP 封锁、SNI 封锁、TLS RST、QUIC 干扰。2025 年还出现过 GFW 对 TCP `443` 异常注入 RST 的事件，说明 HTTPS 也不是绝对稳：[Tom's Hardware 报道](https://www.tomshardware.com/tech-industry/cyber-security/chinas-great-firewall-blocked-all-traffic-to-a-common-https-port-for-over-an-hour-with-no-hint-as-to-its-intention)
- VPS 滥用风险：如果做成 open resolver，会被用于 DNS amplification DDoS。Cloudflare 明确指出开放递归 DNS 是 DNS 放大攻击的关键条件：[Cloudflare DNS amplification](https://www.cloudflare.com/learning/ddos/dns-amplification-ddos-attack/)
- 实用性风险：private DNS 只能修 DNS。访问 Google/YouTube/Wikipedia 这类服务时，即使解析正确，后续连接仍可能因 IP/SNI/协议特征被阻断。
- 合规风险：我不做法律意见；但如果服务被公开传播、用于规避封锁或和代理服务绑定，风险明显上升。

我的建议是：先做“小范围私用 DoH”，不开放 `53/853`，后端用 AdGuard Home 或 Unbound，运行一周观察从大陆网络的可用性和 VPS 连接日志，再决定是否加 DoT/iOS profile/DNSCrypt

---

## 2. 用户安装了 dig，要求补测 VPS DNS。

---

<h3 align="center"><strong>USER</strong></h3>

我已经安装了 dig，你可以用 dig 了

<h3 align="center"><strong>ASSISTANT</strong></h3>

补跑完了，VPS 上的 `dig` 结果和前面的判断一致：VPS DNS 干净，本机明文 DNS 被污染。

VPS 关键结果：

- `dig` 版本：`DiG 9.20.23-1~deb13u1-Debian`
- 默认解析器：`<VPS_INTERNAL_DNS>`
- 默认解析正常：
  - `youtube.com -> 142.250/142.251...`
  - `wikipedia.org -> 103.102.166.224`
  - `telegram.org -> 149.154.167.99`
  - `github.com -> 20.27.177.113`
- VPS 上查询 `1.1.1.1 / 8.8.8.8 / 9.9.9.9 / 223.5.5.5 / 114.114.114.114` 都没有出现本机那种 `youtube.com -> 174.132.167.252`、`wikipedia.org -> 31.13.88.169` 的异常。
- VPS 上 UDP 和 TCP 查询结果也一致正常。

一个额外发现：VPS 当前默认 DNS 对 `dnssec-failed.org` 返回了 `NOERROR`，说明 `<VPS_INTERNAL_DNS>` 这个上游大概率没有启用 DNSSEC validation。若你要做 private DNS，我会更偏向让后端自己用 Unbound 做递归 + DNSSEC，而不是只转发到 VPS 运营商 DNS。

更新后的方案不变，但更明确：

- 后端用 `Unbound` 做递归缓存和 DNSSEC validation。
- 只监听 `127.0.0.1:53`，不对公网开放 53。
- 前面用现有 `nginx :443` 反代一个私有 DoH 入口。
- 不开 `853`，除非你明确需要 Android Private DNS 的原生 DoT。
- 加访问控制和限速，避免变成 open resolver。

---

## 3. 解释 DoH、DoT，以及 nginx 后面藏 DNS 的拓扑。

---

<h3 align="center"><strong>USER</strong></h3>

我不太理解你说的 DoH、DoT 以及将 DNS 藏在 nginx 后相关实现。能不能举一个拓扑例子，让我理解？

<h3 align="center"><strong>ASSISTANT</strong></h3>

可以，把 DNS 当成“问路服务”理解。

**普通 DNS**
```text
你的电脑/手机
  |
  | UDP/TCP 53: youtube.com 的 IP 是多少？
  v
某个 DNS 服务器
```

问题是：传统 DNS 通常是明文 `53` 端口。路上有人可以看到你在问什么，也可以抢先塞一个假答案。你本机测试里看到的污染就是这种类型。

**DoT**
DoT = DNS over TLS。

```text
你的手机
  |
  | TLS 加密连接，TCP 853
  v
你的 VPS DNS 服务
```

它像“DNS 专用 HTTPS”，但默认端口是 `853`。优点是系统支持好，比如 Android 的“私人 DNS”就是 DoT。缺点是特征太明显：别人一看你连 `853`，大概率知道你在用加密 DNS。

**DoH**
DoH = DNS over HTTPS。

```text
你的浏览器/系统/客户端
  |
  | HTTPS 443: /dns-query
  v
你的 VPS nginx
  |
  | 本机转发
  v
DNS 后端服务
```

它把 DNS 查询包装进 HTTPS 请求里。外面看起来像你在访问一个普通网站的 HTTPS 接口。

一个具体拓扑例子：

```text
[你的手机]
  |
  | https://dns.example.com/dns-query
  | 443/TCP，HTTPS 加密
  v
[你的 VPS 公网 IP]
  |
  | nginx 监听 443
  | 看到路径是 /dns-query
  v
[AdGuard Home 或 DoH 网关]
  |
  | 127.0.0.1:5353 / 127.0.0.1:3000
  v
[Unbound]
  |
  | 向根 DNS / TLD / 权威 DNS 递归查询
  v
[互联网 DNS 权威服务器]
```

nginx 的作用不是解析 DNS，而是“门口的 HTTPS 接待员”：

```text
普通网站请求:
https://dns.example.com/
        |
        v
nginx 返回一个普通网页或 404

DNS 查询:
https://dns.example.com/dns-query
        |
        v
nginx 转发给本机 DNS 服务
```

所以“藏在 nginx 后面”的意思是：

```text
公网只暴露 443:
0.0.0.0:443 -> nginx

DNS 服务不直接暴露:
127.0.0.1:5353 -> DoH 后端
127.0.0.1:53   -> Unbound
```

外部不能直接访问你的 `53` 端口，也不能把你的 VPS 当公开 DNS 放大攻击工具用。只有知道你的 HTTPS 域名和 DoH 路径的客户端，才能通过 nginx 间接使用它。

最小实现可以是：

```text
客户端
  -> HTTPS DoH
  -> nginx :443
  -> AdGuard Home :3000
  -> Unbound :53
  -> 互联网权威 DNS
```

更简单一点也可以：

```text
客户端
  -> HTTPS DoH
  -> nginx :443
  -> AdGuard Home
  -> 上游 DoH/DoT 公共 DNS
```

但我更推荐第一种，因为 Unbound 自己递归 + DNSSEC，少依赖公共 DNS。

---

## 4. 查询 DoH/DoT 是否会被发现，以及是否常见因 private DNS 封 VPS IP。

---

<h3 align="center"><strong>USER</strong></h3>

DoT 和 DoH 会被发现吗？检查一下互联网，被发现导致后果的情况（例如封禁 ip）多吗？

<h3 align="center"><strong>ASSISTANT</strong></h3>

会。区别在于“多容易被发现”和“发现后通常怎么处理”。

**简短判断**
- `DoT`：很容易被发现。默认 `TCP 853`，特征直接。适合正常网络环境，不适合希望降低可见度的跨境场景。
- `DoH`：没那么容易，但不是隐身。外面看不到 DNS 查询内容，但能看到你连了哪个 IP/域名，通常还能看到 TLS SNI，流量形态也可能被分类。
- 小范围自用 private DoH：公开资料里我没看到“因为个人 private DoH 被长期封 VPS IP”的常见案例。更常见的是：公共 resolver、知名域名、知名 IP、代理/VPN 协议被阻断。
- 真实风险不是 0。尤其如果你公开分享、流量异常、和代理服务混在一起，风险会上升。

**为什么 DoT 容易被发现**
DoT 是 DNS over TLS，标准默认端口是 `853`。IETF RFC 7858 明确说 DoT 默认连接 `853`。所以过滤器不需要理解内容，只要看到你连境外 `:853`，就能判断“这是加密 DNS”。  
来源：[RFC 7858](https://datatracker.ietf.org/doc/html/rfc7858)

所以我不建议你优先开 DoT，除非你明确需要 Android “私人 DNS”的原生支持。

**为什么 DoH 更隐蔽但仍可发现**
DoH 是 DNS over HTTPS，走 `443`，路径通常是：

```text
https://dns.example.com/dns-query
```

外部观察者一般看不到 `/dns-query` 和 DNS 内容，因为 HTTPS 加密了 HTTP 层。但还能看到：

```text
你的客户端 -> VPS IP:443
TLS SNI: dns.example.com   # 如果未使用 ECH
连接频率、包大小、时序特征
```

学术研究也讨论过 DoH 检测：从静态封禁已知 DoH IP/域名，到用机器学习分析 HTTPS 流量模式。NinjaDoH 论文里总结：DoT/DoQ 因端口明显更容易挡，DoH 难挡一些，但仍可能被 IP/域名列表或流量模型识别。  
来源：[NinjaDoH](https://arxiv.org/abs/2411.02805)

**有没有被封案例**
有相关案例，但主要是“公共服务/知名服务”，不是个人 private DoH。

1. Cloudflare `1.1.1.1` 在中国出现过阻断/干扰  
GFW Report 记录 2023 年 10 月起中国出现 `1.1.1.1` blocking 报告，也提到此前 `1.1.1.1:443` 曾被 TCP RST 干扰。  
来源：[GFW Report: blocking of 1.1.1.1](https://gfw.report/blog/blocking_of_1111/en/)

2. GFW 能对加密流量做被动识别  
USENIX Security 2023 的 GFW Report 论文显示，GFW 对某些“看起来完全随机”的加密代理流量会被动检测并触发阻断；阻断对象是 `(客户端 IP, 服务器 IP, 服务器端口)` 这个三元组，残留时间约 180 秒。  
这不是 DoH 本身，但说明“加密了”不等于“不可识别”。  
来源：[How the Great Firewall Detects and Blocks Fully Encrypted Traffic](https://gfw.report/publications/usenixsecurity23/en/)

3. `443` 也不是绝对安全  
2025 年 8 月 20 日，GFW Report 记录过一次约 74 分钟的异常事件：GFW 对 TCP `443` 无条件注入 RST，影响中国与境外的 HTTPS 连接。  
这不是针对 DoH，但说明 `443` 是“更不显眼”，不是“不会被动”。  
来源：[GFW Report: unconditional port 443 block](https://gfw.report/blog/gfw_unconditional_rst_20250820/en/)

**对你的 VPS 的实际风险分级**
```text
低风险:
只给自己用 DoH，藏在 nginx 443 后面，不开放 53/853，不公开域名，不跑代理。

中风险:
固定域名叫 dns.xxx.com，标准 /dns-query，多个客户端长期高频使用。

高风险:
公开分享 DoH 地址；开 53 做 open resolver；和代理/VPN 同 IP 同域名；流量明显服务很多人。
```

我的建议仍然是：

```text
公网只开 443
nginx 反代 /dns-query
后端 DNS 只监听 127.0.0.1
不开 53
默认不开 853
加限速和访问控制
```

这不是“不会被发现”，而是把风险控制在“看起来像普通 HTTPS 小流量服务”，同时避免 open resolver、DoT 明显端口、DNS 放大攻击这些硬风险。

---

## 5. 查看 mihomo 配置是否支持连接自建 DoH，并比较橙云与 DNS only。

---

<h3 align="center"><strong>USER</strong></h3>

查看我的 mihomo 配置，其是否支持连接到我自己的 DoH？

如果 DoH 叫 <PRIVATE_DOH_DOMAIN>，且 /mirror-query，对比 <PRIVATE_DIRECT_DOMAIN>，前者可能会命中 cf 的橙云代理，后者是 dns only；

我担心的是加了 DoH 导致网络变慢（主要是 dns 查询的开销变大）

<h3 align="center"><strong>ASSISTANT</strong></h3>

支持。你的当前 mihomo 配置已经在用 DoH：

[`.config/mihomo-party/mihomo.yaml`](HOME-PATH/.config/mihomo-party/mihomo.yaml:44)

```yaml
dns:
  enable: true
  enhanced-mode: redir-host
  respect-rules: true
  default-nameserver:
    - 1.1.1.1
  nameserver:
    - https://223.5.5.5/dns-query
  proxy-server-nameserver:
    - https://120.53.53.53/dns-query
  direct-nameserver:
    - tls://223.5.5.5/dns-query
```

mihomo 官方文档也明确支持 `https://.../dns-query` 作为 `nameserver`，并支持给 DNS 服务器追加参数，例如指定走某个代理/接口。文档里还说 `default-nameserver` 用于解析 DNS 服务器自己的域名，必须是 IP，也可以是加密 DNS。来源：<https://wiki.metacubex.one/config/dns/>

**你的两个域名现状**

```text
<PRIVATE_DOH_DOMAIN>
  -> 104.21.68.148 / 172.67.196.47
  -> Cloudflare 橙云
  -> HTTPS header: server: cloudflare

<PRIVATE_DIRECT_DOMAIN>
  -> <VPS_PUBLIC_IP>
  -> DNS only，直连 nginx
```

所以如果 DoH 放在：

```text
https://<PRIVATE_DOH_DOMAIN>/mirror-query
```

路径会是：

```text
mihomo
  -> 先用 default-nameserver 解析 <PRIVATE_DOH_DOMAIN>
  -> 连 Cloudflare 443
  -> Cloudflare 转发到你的源站
  -> nginx /mirror-query
  -> DoH 后端
```

如果放在：

```text
https://<PRIVATE_DIRECT_DOMAIN>/mirror-query
```

路径会是：

```text
mihomo
  -> 先解析 <PRIVATE_DIRECT_DOMAIN>
  -> 直接连 <VPS_PUBLIC_IP>:443
  -> nginx /mirror-query
  -> DoH 后端
```

**性能判断**

你担心“加 DoH 变慢”，但严格说你现在已经在用 DoH：`https://223.5.5.5/dns-query`。所以不是“从普通 DNS 变 DoH”，而是“从阿里/腾讯 DoH 换成你自己的 DoH”。

真正增加的开销主要来自：

```text
Cloudflare 橙云链路
+ 你的 VPS 到上游/递归查询
+ TLS/HTTP 连接建立
```

mihomo 有 DNS 缓存，所以不是每个连接都重新 DNS 查询。变慢主要体现在首次访问、TTL 过期、或者大量新域名访问时。

我的建议：

```yaml
dns:
  nameserver:
    - https://<PRIVATE_DIRECT_DOMAIN>/mirror-query#DIRECT
```

优先用 `<PRIVATE_DIRECT_DOMAIN>` 的 DNS only，少一跳 Cloudflare，延迟更可控。

如果你更想隐藏源站，可以用：

```yaml
dns:
  nameserver:
    - https://<PRIVATE_DOH_DOMAIN>/mirror-query#DIRECT
```

但这会经过 Cloudflare，可能更慢，也可能受 CF 规则、缓存/WAF、HTTP/2/HTTP/3 行为影响。

保守配置我会这样放：

```yaml
dns:
  default-nameserver:
    - 223.5.5.5
    - 1.1.1.1
  nameserver:
    - https://<PRIVATE_DIRECT_DOMAIN>/mirror-query#DIRECT
  proxy-server-nameserver:
    - https://120.53.53.53/dns-query
  direct-nameserver:
    - https://223.5.5.5/dns-query
```

关键点：`proxy-server-nameserver` 先别改成你自己的 DoH。它负责解析代理节点域名，留一个稳定的公共 DoH 可以避免“为了连 DNS 先要解析代理、为了解析代理又要连 DNS”的启动绕圈问题。

---

## 6. 解释 mihomo 代理机制里 DNS 的作用，以及访问 YouTube 时 DNS 在哪一侧解析。

---

<h3 align="center"><strong>USER</strong></h3>

使用 mihomo 上网时，代理的机制是怎么实现的？dns 在其中的作用是什么？如果我要访问 youtube.com，是先走国内的 223.5.5.5 查询，然后走代理链路访问；还是代理链路做 dns 查询 + 访问？

<h3 align="center"><strong>ASSISTANT</strong></h3>

取决于入口模式，但按你现在的配置，核心结论是：

访问 `youtube.com` 这种代理域名时，通常不是“先用 223.5.5.5 查出 IP，再直连那个 IP”。mihomo 会先拿到域名，按规则决定走代理；真正的目标解析通常可以在代理链路另一侧完成，或者由代理协议把域名交给远端。

**简化流程**
你访问：

```text
https://youtube.com
```

如果浏览器走 mihomo 的 HTTP/SOCKS/mixed 代理端口：

```text
浏览器
  -> mihomo mixed-port
  -> 请求里带着 youtube.com
  -> mihomo 用 youtube.com 匹配规则
  -> 命中代理规则
  -> mihomo 连接你的代理节点
  -> 通过代理节点访问 youtube.com
```

这时本地 DNS 对 `youtube.com` 不是必需步骤。mihomo 已经从代理请求里知道域名。

**DNS 在这里的作用**
DNS 主要有几类作用：

```text
1. 解析代理节点域名
   例如你的节点 server: <PRIVATE_DIRECT_DOMAIN>
   这必须先解析，否则 mihomo 不知道代理服务器 IP。

2. 处理系统/应用发来的 DNS 查询
   比如某些程序不用 HTTP/SOCKS 代理，而是自己先查 youtube.com。

3. 给 DIRECT 流量解析目标 IP
   例如 baidu.com、国内站点、直连规则命中的域名。

4. 辅助规则判断
   有些规则基于 IP、GeoIP、fallback-filter，需要 DNS 结果参与判断。
```

**结合你的配置**
你现在的 DNS 段是：

```yaml
respect-rules: true

nameserver:
  - https://223.5.5.5/dns-query

proxy-server-nameserver:
  - https://120.53.53.53/dns-query

direct-nameserver:
  - tls://223.5.5.5/dns-query
```

含义大致是：

```text
proxy-server-nameserver:
  专门解析代理节点域名，比如 <PRIVATE_DIRECT_DOMAIN>。

nameserver:
  常规 DNS 查询默认用它。

direct-nameserver:
  DIRECT 出口的域名解析用它。

respect-rules: true:
  DNS 查询本身也会尽量遵守 mihomo 路由规则。
```

所以访问 `youtube.com` 时，更准确地说：

```text
1. mihomo 先要保证代理节点 <PRIVATE_DIRECT_DOMAIN> 可连接
   这个用 proxy-server-nameserver 解析。

2. 浏览器请求 youtube.com 进入 mihomo。

3. mihomo 根据 youtube.com 匹配规则，判断走代理。

4. mihomo 通过代理节点发起到 youtube.com 的连接。
   如果代理协议支持传域名，就把 youtube.com 交给远端处理；
   不一定在本地用 223.5.5.5 查 youtube.com。
```

**什么时候会先查 223.5.5.5？**
如果应用不是把域名交给 mihomo，而是自己先做 DNS 查询，例如：

```text
应用 -> 系统 DNS -> mihomo DNS -> 223.5.5.5
应用拿到 youtube.com 的 IP
应用再连接这个 IP
```

那 mihomo 看到的可能只是目标 IP。你配置里 `sniffer: enable: true`，mihomo 可能再从 TLS SNI/HTTP Host 里嗅探回 `youtube.com`，然后按域名规则走代理。

**一句话**
用 HTTP/SOCKS/mixed 代理访问 YouTube：通常是“域名进 mihomo，mihomo 判规则，走代理，远端访问”。

用 TUN/透明代理/应用自己 DNS：可能会先经过 mihomo DNS；这时你的 `nameserver`、`direct-nameserver`、`respect-rules` 才更关键。
