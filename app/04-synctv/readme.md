# synctv

repo：https://github.com/synctv-org/synctv.git

1. `sudo docker-compose -p 04-synctv -f /home/server/04-synctv/synctv.yml up -d` 启动后，在 log 里看默认账密 `root / root`
2. 登录到后台后
   1. 修改用户名 root，以及密码
   2. `网站设置` 中，不允许访客用户、禁止用户注册、注册需要审核
3. 个人用户的平台绑定里
   1. alist