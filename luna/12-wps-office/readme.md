download url：https://mirrors.aliyun.com/ubuntukylin/pool/partner/wps-office_12.1.0.17881_amd64.deb

```bash
#!/bin/bash

path="/opt/kingsoft/wps-office/office6"
wcsbin="$path/wpscloudsrv"

mv $wcsbin "$wcsbin.shit"
sudo echo "#!/bin/bash\nexit 0" > $wcsbin
```

