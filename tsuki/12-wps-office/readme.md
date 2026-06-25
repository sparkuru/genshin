download url：https://mirrors.aliyun.com/ubuntukylin/pool/partner/wps-office_12.1.0.17881_amd64.deb

`./clean.sh` 脚本，作用是 **尽可能去掉一切与云服务相关的服务**，只保留最纯粹的 word、ppt、excel 编辑、查看体验，使用后大概率无法正常登陆

将 `clean.sh` 放到 `/opt/kingsoft/wps-office` 下：`sudo ln -sfn /path/to/clean.sh /opt/kingsoft/wps-office/clean.sh`

恢复的方式是删除掉 `$HOME/.config/Kingsoft`（会删掉所有用户配置），然后重装

```
/usr/bin/et
/usr/bin/wpp
/usr/bin/wps
/usr/bin/wpspdf
```

