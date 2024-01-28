# ddns-go

repo：https://github.com/jeessy2/ddns-go.git

1. 注册一个 [dynadot](https://www.dynadot.com) 的域名（注意是 com）

2. `sudo docker-compose -p 01-ddns-go -f /home/server/01-ddns-go/ddns-go.yml up -d`

3. 访问 `http://localhost:9420` 开始配置 ddns-go，[参照](https://www.dynadot.com/zh/community/help/question/set-up-DNS)

   1. 默认账密是 `admin@example.com / changeme`

   2. 在域名的 `DNS 设置` 里选择 `Dynadot DNS`，记录类型随便填一个 `A: xxx.xxx.xxx.xxx`，打开下边的 `动态 DNS`，复制 `动态 DNS 密码`

   3. 在 ddns-go 里选择 `Dynadot`，`password` 项就是刚才的 `动态 DNS 密码`；IPv4 的 Domains 里配置两条：

      ```bash
      example.com
      *.example.com
      ```

   4. 记得修改 ddns-go 下面 Others 项里的账密

4. 等几分钟后，使用 `nslookup example.com` 来测试，也可以直接访问 `8.8.8.8` 来查询