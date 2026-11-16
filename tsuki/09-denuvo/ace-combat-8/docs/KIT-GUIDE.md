# denuvo-kit —— AceCombat8 环境准备工具包

一套用于准备配套 hypervisor 驱动所需 Windows 环境的脚本。回滚脚本存在下文所述的限制。

> 本工具包负责系统环境配置、检查、启动和回滚；`artifact.dll` 与对应驱动需自行准备，其发行来源尚未核实。

---

## 目录

目录结构与所需文件见 [方案说明](../readme.md)。

## 快速开始

游戏目录默认为示例路径 `D:\game\ac8`，可用 `-GameDir` 覆盖。
本工具包的快照保存在 `workspace/backups/`；`scripts/research/` 中的独立脚本使用示例目录 `D:\game\backup\ac8`，两套备份不可混用。

先以**管理员** PowerShell 打开 `scripts` 目录。

```powershell
# 0) 检查系统和文件；会写入本地日志
powershell -ExecutionPolicy Bypass -File .\01-check.ps1

# 1) 若 Secure Boot = On：按下面“BIOS”一节先关掉，再继续
# 2) 应用配置（会先备份，最后询问是否重启）
powershell -ExecutionPolicy Bypass -File .\02-apply.ps1

# 3) 重启后验收
powershell -ExecutionPolicy Bypass -File .\03-verify.ps1

# 4) 启动（直接双击 exe 也一样）
powershell -ExecutionPolicy Bypass -File .\04-launch.ps1
```

脚本配置的环境：

| 项 | 值 | 说明 |
|---|---|---|
| `bcdedit /set hypervisorlaunchtype off` | Off | 释放 VMX/SVM，供游戏自带 hypervisor 接管 |
| `bcdedit /set vsmlaunchtype off` | Off | 关 VSM |
| `DeviceGuard\EnableVirtualizationBasedSecurity` | 0 | 关 VBS |
| `HVCI\Enabled` | 0 | 关内存完整性 |
| `SystemGuard\Enabled` | 0 | 关 System Guard |
| `bcdedit /set testsigning on` | Yes | 允许加载测试签名驱动（游戏自带的 `SimpleSvm.sys`） |

不动的项：Defender、`loadoptions`、BitLocker、网络栈。

## BIOS（Secure Boot）

`testsigning` 在 Secure Boot 开启时会被固件策略锁死，报：

```
The value is protected by Secure Boot policy and cannot be modified or deleted.
```

以下是历史使用的 Gigabyte B650M AORUS PRO AX（FB3）固件记录，其他设备的设置方式可能不同：

1. 重启按 `Del` 进 BIOS；
2. `Boot` → `Secure Boot` → `Secure Boot Mode` 改为 `Custom`；
3. `Delete all Secure Boot Keys`（或 `Restore Factory Keys` 后切到 `Setup Mode`）；
4. `F10` 保存退出；
5. 进系统后 `Confirm-SecureBootUEFI` 应为 `False`。

不玩时想恢复：BIOS 里 `Restore Factory Keys`（或把模式改回 `Standard`），再跑 `99-rollback.ps1`。

## 参数

```powershell
# 只打印将执行的命令，不改系统
.\02-apply.ps1 -DryRun

# 不需要加载自签驱动时跳过测试签名
.\02-apply.ps1 -SkipTestSigning

# BitLocker 已加密时需确认
.\02-apply.ps1 -Force

# 自定义游戏目录
.\01-check.ps1 -GameDir "D:\game\ac8"
.\04-launch.ps1 -GameDir "D:\game\ac8" -WaitSeconds 90

# 回滚但保留测试签名
.\99-rollback.ps1 -KeepTestSigning
```

## 适用范围（先说清楚）

本工具包只做**环境使能**，不是破解器：

- ✅ 可复用：关 Secure Boot / Hyper-V / VBS / HVCI、开测试签名、装启内核服务、会话与 GPU 验证。
- ❌ 不可复用：驱动与 loader 的协议、`artifact.json` 里的令牌与 exe 哈希、各包自己的 CPUID / MSR / SMBIOS 伪装。
- ⚠️ 真·虚拟机 guest：还要求宿主开启嵌套虚拟化，否则驱动会以 `VMX is not supported in this machine` 失败。
- ⚠️ 在线 + 内核反作弊、正版 Denuvo 授权：不适合，风险不可控。

细节和判定表见 [`COMPATIBILITY.md`](COMPATIBILITY.md)。

## 预期现象

- 配置后 `HypervisorPresent` 先变 `False`（重启完成、未跑游戏时）。
- 启动游戏后 `artifact` 服务出现并 `RUNNING`，`HypervisorPresent` 变 `True`（这是游戏自带的 hypervisor，正常）。
- 进程内存会从 ~10 MB 涨到数 GB，GPU 3D 有 40%+ 占用，即为正在渲染。

## 回滚

```powershell
powershell -ExecutionPolicy Bypass -File .\99-rollback.ps1
```

脚本停/删 `artifact` 服务，将 BCD 中的 `testsigning`、`hypervisorlaunchtype`、`vsmlaunchtype` 设为脚本内的值，并在有备份时导入 DeviceGuard/Lsa 注册表。BCD 不按备份原值恢复；注册表导入也不保证删除新增值，错误可能只打印而不使脚本失败。应结合运行前快照逐项核对，Secure Boot 需自行恢复。

回滚后游戏会因驱动签名失败而无法启动，属预期。

## 已验证环境 / 结果

| 项 | 值 |
|---|---|
| OS | Windows 11 26100 |
| 主板 / CPU | Gigabyte B650M AORUS PRO AX / Ryzen 9 7950X |
| 显卡 | 独显（`luid_0x00000000_0x00017938`） |
| 结果 | `artifact` 服务 RUNNING；GPU 3D 48~50%；内存 8→19 GB；134 线程；画面正常可玩 |

## 安全提示

- 测试签名是**全局**降级：任何测试签名驱动都能进内核。只在游玩期间开启。
- 环境脚本不安装或生成配套驱动；`artifact` 服务由游戏自己创建，重启即消失。
- `loadoptions DISABLE-LSA-ISO` 若存在（历史遗留）会削弱 LSA 隔离，不需要时清掉：`bcdedit /deletevalue loadoptions`。
