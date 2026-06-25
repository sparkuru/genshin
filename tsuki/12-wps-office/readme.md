download url：https://mirrors.aliyun.com/ubuntukylin/pool/partner/wps-office_12.1.0.17881_amd64.deb

`./clean.sh` 脚本，作用是

1. **尽可能去掉一切与云服务相关的服务**，只保留最纯粹的 word、ppt、excel 编辑、查看体验，使用后大概率无法正常登陆
2. 清除掉 wps-office 创建的各种隐私跟踪文件（包括最近打开的文件、备份的文件目录信息等）

---

也可以使用本地安装版本（便携版），使用 `--install-dir /path/to/install-dir` 自动创建应用目录

```bash
$ ./install-wps-office-green.sh -h
Usage: install-wps-office-green.sh [--url <deb-url>] [--deb <path>] [--install-dir <dir>] [--force]
                                                                                                           
$ ./install-wps-office-green.sh --install-dir /home/wkyuu/cargo/bin/wps-office
[i] Downloading WPS deb: https://mirrors.aliyun.com/ubuntukylin/pool/partner/wps-office_12.1.0.17881_amd64.deb
###################################################################################################################### 100.0%
[i] Extracting deb: /tmp/install-wps-office/work.YMx3AWMtQa/wps-office_12.1.0.17881_amd64.deb
[i] Copying WPS program files.
[i] Copying icons and fonts.
[i] Generating desktop entries.
[i] Generating clean helper.
[i] Purging portable office6.
[i] Cleaning WPS Office at /home/wkyuu/cargo/bin/wps-office/office6
[i] Cloud server stubs prepared: 1
[i] Cloud libraries disabled: 2
[i] Rogue binaries disabled: 5
[i] Rogue addons disabled: 67
[i] Plugin registry lines: 24 -> 4
[i] WPS Office clean finished.
[i] Generating target-machine installer.
[i] Generating uninstall helper.
[i] Portable WPS is ready: /home/wkyuu/cargo/bin/wps-office

Register .desktop links now? (y/N) y	# register .desktop file in `~/.local/share/applications/wps-office-*.desktop`
Enable privacy mode and clean WPS user data after each exit? (y/N) y	# clean wps RecentFile and BackupFile after every exit wps
qtpaths: could not find a Qt installation of ''
qtpaths: could not find a Qt installation of ''
qtpaths: could not find a Qt installation of ''
qtpaths: could not find a Qt installation of ''
qtpaths: could not find a Qt installation of ''
qtpaths: could not find a Qt installation of ''
qtpaths: could not find a Qt installation of ''
qtpaths: could not find a Qt installation of ''
qtpaths: could not find a Qt installation of ''
qtpaths: could not find a Qt installation of ''
qtpaths: could not find a Qt installation of ''
qtpaths: could not find a Qt installation of ''
qtpaths: could not find a Qt installation of ''
qtpaths: could not find a Qt installation of ''
qtpaths: could not find a Qt installation of ''
qtpaths: could not find a Qt installation of ''
qtpaths: could not find a Qt installation of ''
qtpaths: could not find a Qt installation of ''
qtpaths: could not find a Qt installation of ''
qtpaths: could not find a Qt installation of ''
qtpaths: could not find a Qt installation of ''
qtpaths: could not find a Qt installation of ''
[i] Cleaning WPS Office at /home/wkyuu/cargo/bin/wps-office/office6
[i] Cloud server stubs prepared: 0
[i] Cloud libraries disabled: 0
[i] Rogue binaries disabled: 0
[i] Rogue addons disabled: 0
[i] Plugin registry lines: 0 -> 0
[i] WPS Office clean finished.
[i] WPS portable desktop entries installed.
[i] Run /home/wkyuu/cargo/bin/wps-office/install-local.sh again any time to change desktop, bin link, or privacy-mode choices.
[i] Portable directory: /home/wkyuu/cargo/bin/wps-office
```

`install-local.sh` 会自动生成 `uninstall.sh`，该卸载脚本会清掉与当前 portable 有关的一切内容，但保存用户配置与 `~/document` 下的文件