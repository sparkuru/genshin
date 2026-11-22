# Krita + Wacom（Windows）

保存本机已经验证过的配置：Krita 5.3.3 便携版、Wacom 6.4.15-1、Intuos BT M（CTL-6100WL，USB `VID_056A&PID_0378`）。安装包不放在本目录，按下面的官方链接自行获取。

## 当前配置

- Krita 程序：`D:\software\krita\bin\krita.exe`；数位板软件接口为 **Windows Ink / Windows 8+ Pointer**。
- Wacom 的 **Krita 专用配置**：Windows Ink 开启；靠笔尖的侧键为中键（拖动画布），另一个为擦除（按住擦除，松开返回画笔）。笔尖双击距离已关闭。
- Windows「笔和触控」中的“按住进行右键单击”已关闭，备份时 `HoldMode=3`。
- `WTabletServicePro` 为手动启动，USB 数位板到达时自动启动；未配置拔出时停止。该触发器是按上述设备 ID 定制的，换型号需要重新检查。
- Krita 与 Wacom 的应用专用配置都保存了程序路径。恢复到不同路径时，需在 Wacom 数位板属性中重新为新的 `krita.exe` 建立应用配置，并复查上述侧键和 Windows Ink。

## 下载和便携版部署

| 软件 | 官方下载 | 本次使用的 SHA-256 |
| --- | --- | --- |
| Krita 5.3.3 Windows x64 ZIP | [KDE 直链](https://download.kde.org/Attic/krita/5.3.3/krita-x64-5.3.3.zip) · [官方校验信息](https://download.kde.org/Attic/krita/5.3.3/krita-x64-5.3.3.zip?mirrorlist) | `87278594fac0267680303280e410578388d606aec5a290f2b0d009909f4254f0` |
| Wacom 6.4.15-1 Windows 驱动 | [Wacom 直链](https://cdn.wacom.com/u/productsupport/drivers/win/professional/WacomTablet_6.4.15-1.exe) · [版本说明与机型](https://cdn.wacom.com/u/productsupport/drivers/win/professional/releasenotes/Windows_6.4.15.html) | `05e639d68af2f411e9df5c98205fa3e66636eb6a271bbe408c36af4c40efd01c` |

Wacom 的签名发布者为 Wacom Co., Ltd.；可以在 PowerShell 中校验：

```powershell
Get-FileHash 'E:\download\WacomTablet_6.4.15-1.exe' -Algorithm SHA256
Get-AuthenticodeSignature 'E:\download\WacomTablet_6.4.15-1.exe' | Format-List Status, SignerCertificate
```

下载 ZIP 后，将本目录复制到 Windows，在 PowerShell 中执行：

```powershell
.\install-krita.ps1 -ArchivePath 'E:\download\krita-x64-5.3.3.zip'
```

脚本校验 ZIP 哈希，将程序解压到 `D:\software\krita`，不改系统 PATH、不创建快捷方式。父目录需先存在；目标若已存在则拒绝覆盖。要使用其他路径，可加 `-Destination 'E:\software\krita'`，恢复 Wacom 后应重新关联该路径。程序本身是便携版，但用户配置仍保存在 Windows 用户目录，需另行备份。

Wacom 驱动不能像 Krita 一样免安装：在 Windows 上运行下载到本地的签名安装程序，按提示完成安装并重启。已检查过该包包含驱动文件和 Wacom Center 组件；**没有进行断网安装实测**，因此不保证安装过程中的所有步骤都无需联网。安装驱动需要管理员权限，并会写入 Windows 系统位置。

## 备份位置和范围

`snapshots/x/` 导出实际快照，包含：

- `krita/local/`：`kritarc`、`kritadisplayrc`，以及存在时的 `kritaopenglrc`。
- `krita/resources/`：`%APPDATA%\krita` 用户资源和资源数据库，包括笔刷、预设和工作区等；不包括 `.kra` 画作。
- `wacom/Wacom.wacomprefs`：通过 Wacom 官方工具导出的当前用户配置，包含 Krita 应用关联、侧键、双击和 Windows Ink 设置。
- `system/settings.json` 和 `system/wacom-trigger.txt`：Windows 笔设置与服务触发器记录。
- `manifest.json`：逐文件大小和 SHA-256，恢复脚本先验证后执行。

快照包含本机路径、软件使用信息和用户资源，体积约 100 MB

## 恢复到 Windows

把所需 `snapshots/x/` 复制到 Windows；安装对应的 Krita 和 Wacom 驱动，连接数位板，并保存画作、完全退出 Krita。

1. 打开 `C:\Program Files\Tablet\Wacom\PrefUtil.exe`，先在“我的首选项”下备份目标机现有的 Wacom 设置。然后选择“恢复”，选择快照中的 `wacom\Wacom.wacomprefs`。恢复会重启 Wacom 的用户驱动进程；这是 Wacom 官方支持的恢复方式。
2. 在本目录运行恢复预览，再确认路径无误后实际恢复。回滚目录必须不存在，父目录须已存在：

```powershell
.\restore-config.ps1 -SnapshotPath '.\snapshots\x' -RollbackDirectory 'E:\tmp\krita-before-restore' -RestoreWindowsPen
.\restore-config.ps1 -SnapshotPath '.\snapshots\x' -RollbackDirectory 'E:\tmp\krita-before-restore' -RestoreWindowsPen -Apply
```

脚本校验清单后恢复 Krita 设置和整个资源目录，并按需恢复 Windows 笔的 `HoldMode`。旧的配置文件保存在指定回滚目录的 `local/`；旧资源目录会原地改名，确切位置记录在回滚目录的 `resources.json`。恢复失败时脚本尝试撤销已经完成的 Krita 改动。Windows 笔设置如未立即生效，可注销或重启后检查。

3. 如需恢复 USB 按需启动，在**管理员 PowerShell** 中先预览，再应用：

```powershell
.\wacom-usb-trigger.ps1
.\wacom-usb-trigger.ps1 -Apply
```

它仅接受没有触发器或已存在同一触发器的服务；如果已有其他触发器则拒绝覆盖。它不会重启服务，也不添加拔出时停止的触发器。可用 `sc.exe qtriggerinfo WTabletServicePro` 和 `Get-Service WTabletServicePro` 核对。

4. 重新打开 Krita，测试小圈和笔压、侧键拖动画布、按住擦除及松开恢复画笔。如果数位板插入之前 Krita 已经打开而未收到笔压，保存画作并重新打开 Krita。

如不恢复 Windows 注册表设置，也可按 `Win+R`，运行 `control /name Microsoft.PenAndTouch`，在“笔选项 → 按住 → 设置”中取消“启用按住进行右键单击”。
