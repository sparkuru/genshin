download url：https://mirrors.aliyun.com/ubuntukylin/pool/partner/wps-office_12.1.0.17881_amd64.deb

```bash
#!/bin/bash

wpspath="/opt/kingsoft/wps-office/office6"
wcsbin="$wpspath/wpscloudsrv"

mv $wcsbin "$wcsbin.shit"
sudo echo "#!/bin/bash\nexit 0" > $wcsbin
```

`./clean.sh` 脚本，作用是 **尽可能去掉一切与云服务相关的服务**，只保留最纯粹的 word、ppt、excel 编辑、查看体验，使用后大概率无法正常登陆

恢复的方式是删除掉 `$HOME/.config/kingsoft`（会删掉所有用户配置），然后重装