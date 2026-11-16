# PBZ 游戏配套组件与版本

本记录针对本地保留的游戏配套样本；它们不属于本项目脚本，且由 Git 忽略。运行环境脚本需要与实际游戏版本配套的文件。

## 组件关系

```text
PBZ.exe
  └─ winmm.dll → artifact.dll → artifact.json
                       ├─ Artifact_AMD/SimpleSvm.sys
                       ├─ Artifact_Intel/hyperkd.sys 和配套 DLL
                       └─ coldloader.dll → steamclient64.dll
```

`artifact.json` 指定目标程序和配置，AMD 与 Intel 使用不同驱动。`winmm.dll` 是配套代理文件，需与对应主程序和其他组件保持同一版本。环境脚本负责 Windows 设置和回滚，不生成这些游戏文件。

## 版本约束

本地样本的 `artifact.json` 指定目标 `PBZ.exe`，记录的目标 hash 为 `a551c95bdaf4d7a9`；该值的计算方式尚未确认，不能直接当作常见文件哈希验证。历史的 302256 构建使用不同的目标值，见 [HOST-STATE.md](HOST-STATE.md)。不同版本的主程序、配置和驱动应成套保留。

本地 `steamclient64.dll` 已与 GBE Fork 公开发行包中的文件逐字节比对一致；驱动上游与 ColdLoader 的比较结果见 [UPSTREAM-COMPARISON.md](UPSTREAM-COMPARISON.md)。

静态检查记录显示，部分驱动使用测试证书，`artifact.dll` 没有签名。游戏文件的可用性和安全性不能单凭本记录或文件名推断。

## 本地样本 SHA-256

以下是本地样本的文件哈希，不代表其他版本。`artifact.dll`、`artifact.json`、`winmm.dll` 位于 `unique/`，其余样本位于 `workspace/samples/ARTIFACT/platform/steam/`：

```text
121252d98bc0d6a2a6bba0ec8863af58203c999fa5023aa58f6c28ea38fa4229  Artifact_AMD/SimpleSvm.sys
bef24d1edb6d2be2ae21def87cb8696237fa7461f0b72fb7fdd42d599e5f41d9  artifact.dll
363dcd84d733864f1c9bafe87d6c59438b844905426fedd7a39c70d2b30cee52  Artifact_Intel/hyperevade.dll
e2c8f972d7b60f48d3efdc86f93e5b12ca3b6b078decef9fa940883640f9a569  Artifact_Intel/hyperhv.dll
437c1a18448ded371d7b7b8c05ffbf53b0e7b44d63000d8d8051c2275f511182  Artifact_Intel/hyperkd.sys
348227a093fc05b5e81e2b437b13e0655730a328e5661cd8900b54bdf5726ede  Artifact_Intel/hyperlog.dll
14fcfc080b3db77a1363c8cd5796697597f90ed861a2d9a9321cda5a69e4f1e8  Artifact_Intel/kdserial.dll
d00bd362a56bf00ff22db44604199d0b1f7af168251b2802b5566ae4ba93249b  artifact.json
4d568e8608e3dd52d251919535292c753f2586a9fdde72986937720f46b76c17  coldloader.dll
844676acebc626f22e4b10c2c143ffb3429c7d9d9213962396e1ab7c0c19150d  steamclient64.dll
1daf6203a198e233a8410959d56aadaec7ee981a9395c56d97a1dbf042318d6d  winmm.dll
```
