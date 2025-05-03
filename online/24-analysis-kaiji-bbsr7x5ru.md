文件样本：`https://ftp.majo.im/zERQQoejOt/amd64.7z`，密码：`0vOyWvMK1JeMBpg`

微步分析报告：https://s.threatbook.com/report/file/95f835c426f237daec91ae6694b720a5e9eafdf89c4748123134c3b771877ffa

md5：179c5fc118e2cdab3673b902e4dc2981

## 清除

ssh 弱口令 -> `/tmp/amd64` -> `chkrootkit` 发现



`/etc/profile.d/gateway.sh` 招笑了





### 进程

1. 

### 文件

1. `/etc/init.d` 下所有文件，都会带 `/lib/system.mark`，所以必须重装
2. `/etc/crontab -> /.mod`，不可见
3. `/etc/init.d/dns-udp4 -> /boot/system.pub`，不可见
4. `/etc/profile.d/bash.cfg.sh -> /etc/profile.d/bash.cfg`，不可见
5. `/usr/lib/systemd/system/quotaon.service -> /sbin/quotaon`
6. `/etc/profile.d/gateway.sh`

## refer

1. 通用 Linux kernel rootkit 开发导论，https://mp.weixin.qq.com/s/5k3fLsxSlIUeRPKiWHhU0Q