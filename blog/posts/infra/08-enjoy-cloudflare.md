---
title: "enjoy-cloudflare"
description: "体验了 cloudflare 后，你是怎么再忍受得了国内厂商的"
date: "2026-07-05T05:37:29.000Z"
tags: []
draft: false
layout: "post"
slug: "cloudflare-web-service"
source: "online/44-enjoy-cloudflare.md"
---

## Enjoy Cloudflare

## building web service with cloudflare

国内 vps 用久了，也该试一下国外的了。将 vps 转到 aws lightsail（新账户注册送 100 刀账户余额，做任务额外得 100 刀，1 年内有效），dns 转到 cloudflare

对于个人站长，Free 完全够用

### 结构变化对比

旧架构: `用户真实 ip -> nginx -> 后端服务`，即 dns 直接返回 ip 地址，用户直接访问 vps 的 ip

在 cf 启用的 dns 可以选择套上 cf 家的橙云代理，也就是天然带了一层 cf 的防 ddos 机制

橙云的本质是让 http/https 流量不再直接到服务器，而是先走 cf，这样带来的好处有

- 隐藏源站 ip：普通访问者解析到的是 cf ip，不是真实的 vps ip
- 抗 DDoS：攻击先打到 cf
- Bot 管理/挑战页，即常见的 cf 机器人认证
- Under Attack 模式，手动开关，让 cf 帮你防住非白名单内的 url 访问
- 自带 cdn，静态资源可以直接从 cf 边缘节点返回
- 高级用法：为 `admin.example.com` 这种敏感域名加规则，比如只允许指定 ip 登录、加上 cf access 头登录

以上服务都是 free 套餐里带有的，很难想象国内云服务商是怎么能这么不要脸的

新架构变成: `用户真实 ip -> cf -> nginx -> 后端服务`

这时 nginx 直接看到的 `$remote_addr` 不是用户 ip，而是 cf 节点 ip，现在 nginx 反代给后端时写的是：

```nginx
proxy_set_header X-Real-ip $remote_addr;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
```

开橙云后，后端收到的 `X-Real-ip` 会变成 cf ip，不是用户真实 ip

但是 cf 也提供了修正的方式，即在 nginx 里信任 cf 的来源段，然后从 `CF-Connecting-ip` 头里还原用户的真实 ip

```nginx
set_real_ip_from 173.245.48.0/20;
set_real_ip_from 103.21.244.0/22;
# ... 其他 cf ip 段
real_ip_header CF-Connecting-ip;
real_ip_recursive on;
```

配置后，nginx 的 `$remote_addr` 会被替换成真实访客 ip，方便风控审计

### 操作步骤

注册一个 cf 账号，然后 `面板 -> 域名 -> 概览 -> 添加站点 -> 连接域名 -> 输入自己的域名 -> 选择免费计划`

确认 DNS 配置，可以参考以下内容

```
A     *       <源站ip>     Proxied / 橙云，任意二级域名都走 cf 代理
A     @       <源站ip>     Proxied 或 DNS only，单独决定
A     www     <源站ip>     Proxied 或 DNS only，单独决定
A     proxy   <源站ip>     DNS only / 灰云，访问 proxy. 返回真实 ip，多用于临时开发等
A     ssh     <源站ip>     DNS only / 灰云，用于远程连接 vps
```

cloudflare [文档](https://developers.cloudflare.com/dns/manage-dns-records/reference/wildcard-dns-records/) 明确说：wildcard 只有在查询名没有精确记录时才生效（即上面的橙云），精确 DNS 记录（灰云）优先于 wildcard

确认无误，继续前往激活，按照页面提示走，其会返回如下的 cf 名称服务器

```
amber.ns.cloudflare.com
vicente.ns.cloudflare.com
```

到 域名注册商 处，将原本的 dns 名称服务器删掉，改成上面两条，保存。等待 1-2 小时，让 dns 域名广播完成

### 配置 acme

参考 [acme-script.sh](https://raw.githubusercontent.com/sparkuru/genshin/refs/heads/main/code/shellscript/06-acme-script.sh) 和 [官方文档](https://go-acme.github.io/lego/dns/cloudflare/)

使用 cf 管理域名后，也需要对应地将 acme 中自动签发验证流程的 dns key 改成 cf

需要先在 cf 里申请令牌：`面板 -> 管理账户 -> 账户 API 令牌 -> 创建令牌`，在 权限策略 右侧模板里选择 `Edit zone DNS`

- 编辑策略：所有域名
- 权限组：`DNS & ZONE / DNS / Edit` 和 `DNS & ZONE / Zone / Read`
- 令牌过期时间：无过期时间

确认后点击 审核令牌，然后确认令牌，复制弹出对话框里的 ID 和 API_key，修改 acme 更新脚本即可

```
xcaggexgdgxxbgddabexdaeggebacfbc    # 即 acme 脚本里的 CF_Account_ID
gfexcebfaffgcgddaxedbfxxxcabxfaxgdeexebcxxfabgxggfaxb   # CF_Token
```

### 配置 nginx real ip

橙云代理打开后，nginx 看到的 `$remote_addr` 默认是 cf 边缘节点 ip，不是用户真实 ip。由于 cf 会在 HTTP 请求里带上 `CF-Connecting-IP`，可以用 nginx 的 `realip` 模块把 `$remote_addr` 修正回来。

将 [cf.nginx]([../code/nginx/cf.nginx](https://raw.githubusercontent.com/sparkuru/genshin/refs/heads/main/code/nginx/05-cloudflare-real-ip.http.nginx)) 放到 nginx 的 `sites-available` 目录中，然后在 `sites-enabled` 中建立软链接。例如当前配置结构是：

`cf.nginx` 的核心配置是：

```nginx
set_real_ip_from 173.245.48.0/20;
set_real_ip_from 103.21.244.0/22;
# ... 其他 cf 官方 ip 段
real_ip_header CF-Connecting-IP;
real_ip_recursive on;
```

这段配置的含义是：只有请求来源属于 cf 官方 ip 段时，nginx 才信任 `CF-Connecting-IP`，并把 `$remote_addr` 改成真实用户 ip。这样后端继续使用：

```nginx
proxy_set_header X-Real-IP $remote_addr;
proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
```

拿到的就是还原后的用户 ip
