---
title: "enjoy AWS Cloud"
description: "enjoy aws cloud services."
date: "2026-09-13T17:15:43+08:00"
tags: []
draft: true
layout: "post"
slug: "enjoy-aws-cloud"
---

# Enjoy AWS Cloud

免费额度是 200$，体验真的很牛

参考 [脚本](https://www.nodeseek.com/post-809052-1): `bash <(curl -fsSL https://tcpquality.ibsgss.uk/run)`

lightsail jp 结果如下

```bash
------------------------------------------------------------
报告时间：2026-09-13 13:13:40 CST（北京时间）

IPv4回程 统计摘要  零丢包: 92    1-20%:  0    >20%:  1

三网概览                  电信        /               联通        /               移动
河北                163   71ms     0% /        4837  107ms     0% /         CMI   71ms     0%
山西                163   67ms     0% /        4837  106ms     0% /         CMI   71ms     0%
辽宁                163   73ms     0% /        4837  111ms     0% /         CMI   97ms     0%
吉林                163   81ms     0% /        4837   -1ms   100% /         CMI   73ms     0%
黑龙江              163  177ms     0% /        4837  122ms     0% /         CMI   73ms     0%
江苏                163   75ms     0% /        4837   96ms     0% /         CMI   46ms     0%
浙江                163   69ms     0% /        4837   96ms     0% /         CMI   60ms     0%
安徽                163   62ms     0% /        4837   90ms     0% /         CMI   54ms     0%
福建                163   64ms     0% /        4837   97ms     0% /         CMI   80ms     0%
江西                163   77ms     0% /        4837   81ms     0% /         CMI   67ms     0%
山东                163   87ms     0% /        4837  100ms     0% /         CMI   65ms     0%
河南                163   79ms     0% /        4837   95ms     0% /         CMI   63ms     0%
湖北                163   64ms     0% /        4837   90ms     0% /         CMI   70ms     0%
湖南                163   68ms     0% /        4837   92ms     0% /         CMI   86ms     0%
广东                163  170ms     0% /        4837   88ms     0% /         CMI  100ms     0%
海南                163   61ms     0% /        4837  102ms     0% /         CMI   72ms     0%
四川                163   78ms     0% /        4837  106ms     0% /         CMI   93ms     0%
贵州                163   70ms     0% /        4837  103ms     0% /         CMI   85ms     0%
云南                163   88ms     0% /        4837  100ms     0% /         CMI   95ms     0%
陕西                163   68ms     0% /        4837  104ms     0% /         CMI   96ms     0%
甘肃                163   75ms     0% /        4837  104ms     0% /         CMI   99ms     0%
青海                163  142ms     0% /        4837  117ms     0% /         CMI   74ms     0%
内蒙古              163   68ms     0% /        4837  102ms     0% /         CMI   87ms     0%
广西                163  185ms     0% /        4837   94ms     0% /         CMI   70ms     0%
西藏                163   83ms     0% /        4837  127ms     0% /         CMI   82ms     0%
宁夏                163   85ms     0% /        4837  104ms     0% /         CMI   93ms     0%
新疆                163   66ms     0% /        4837  108ms     0% /         CMI  114ms     0%
北京                163   56ms     0% /        4837  100ms     0% /         CMI   56ms     0%
天津                163   61ms     0% /        4837   99ms     0% /         CMI   60ms     0%
上海                163   50ms     0% /        4837  258ms     0% /         CMI   40ms     0%
重庆                163   78ms     0% /        4837  101ms     0% /         CMI   89ms     0%
颜色: 正常  延迟151-240ms或1-20%重传  延迟>240ms或>20%重传，或失败
```


## lightsail

默认用户是 admin，改成了 wkyuu，要记得在 `/etc/ssh/sshd_config` 里信任 lightsail 的 ca，并且将自己的 pub 放到 `/home/admin/.ssh/authorized_keys` 里

```ini
# Port 22
# AddressFamily any
# ListenAddress 0.0.0.0
# ListenAddress ::

Include /etc/ssh/sshd_config.d/*.conf

AddressFamily inet
X11Forwarding yes
UsePAM yes
UseDNS no

SyslogFacility AUTHPRIV
PermitRootLogin yes
PubkeyAuthentication yes
KbdInteractiveAuthentication no
ChallengeResponseAuthentication no
PasswordAuthentication no

PrintMotd no
AcceptEnv LANG LC_*
Subsystem sftp /usr/lib/openssh/sftp-server
TrustedUserCAKeys /etc/ssh/lightsail_instance_ca.pub
```

### 运营商不当人

```markdown
对照测试完成，结果支持“lan1 出口到 VPS 的 TCP/22 路径被间歇性处理”。

路径                                测试结果
lan1 a1 → VPS                      第一轮前 3 次成功，随后连续失败；第二轮 8 次全部在 banner 阶段超时
lan1 c → VPS:22                    反复只有 SYN 重传，没有 SYN/ACK
lan1 c → VPS:443/3440/3445/3447	   均能收到 SYN/ACK
跳板链 → VPS                         全部成功
VPS SSH 日志                        跳板连接来自 45.62.172.112，均能正常认证

现在结论可以更新为：

- VPS 的 sshd、资源和服务本身没有表现出导致此次故障的异常；
- lan1 到 VPS 并非整个 IP 不通，因为其他端口正常；
- 故障高度集中在 112.172.116.42 → VPS:22；
- 故障时有些 SYN 根本到不了 VPS，另一些连接则到达后在认证前超时；
- 最可能是 lan1 运营商或其上游对 TCP/22 的临时过滤、限流或路由异常；
- 仍不能完全排除 AWS/Lightsail 外层对该来源 IP 的端口策略，但 VPS 内部防火墙和 sshd 已基本排除。

所以目前可以较有把握地说：这是“lan1 出口/上游与该 VPS TCP/22 的路径问题”，不是 VPS 被 DDoS 打垮。
```

## tab

参考 `https://raw.githubusercontent.com/sparkuru/genshin/refs/heads/main/katheryne/005-gpt-aws-lightsail-billing-credits.md`