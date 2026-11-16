# 适配范围：这套方案能用在哪些"绕 D"游戏上

结论先给：**环境使能层通用，绕过本体不通用。**

本工具包不是破解器。它只做"让 guest 里的第二个 hypervisor / 自签驱动能加载"这件事；真正骗过 Denuvo 的代码在游戏包自带的 `artifact.dll` + 对应驱动里。

---

这里的“游戏包”指本地取得的配套样本，其发行来源尚未核实，不能据此认定是游戏官方文件。

## 1. 两层结构

| 层 | 内容 | 是否可移植 |
|---|---|---|
| **环境使能层** | 关 Secure Boot、`testsigning on`、`hypervisorlaunchtype off`、VBS/HVCI/SystemGuard=0、装/启内核服务、会话与 GPU 验证 | **通用**。任何"要在系统里再挂一个 hypervisor 或加载自签驱动"的方案都吃这一套 |
| **绕过本体** | `artifact.dll` + `artifact.json`（tokens / hashes / patches）+ `Artifact_AMD\SimpleSvm.sys` / `Artifact_Intel\hyperkd.sys` | **不通用**。与 exe 哈希、Denuvo 版本、CPU 厂商、驱动签名、loader↔driver 协议全部绑定 |

本工具包的脚本只覆盖第一层。

---

## 2. 可以直接复用的部分

- 环境检查、配置、验收和回滚流程可复用；检查和启动时可指定游戏目录。
- 目标包若属于"**自带内核驱动 + 自己装服务**"形态（本作的 `artifact` 型），环境准备好后由游戏加载其配套组件。
- `testsigning` 是全局开关：任何作者自签的驱动都能加载，不挑证书主体。
- 启动脚本支持会话投递、按进程名轮询和 GPU 计数。

---

## 3. 无法直接适配、必须重做的部分

### 3.1 驱动与加载器的耦合

每个包的 loader 只认自己的设备名 / IOCTL / 导出表。本作 `artifact.dll` 找的是 `Artifact_AMD\SimpleSvm.sys`、服务名 `artifact`；换游戏就是另一套名字与协议。把本作的 `SimpleSvm.sys` 拿给别的游戏用没有意义。

### 3.2 令牌与哈希绑定

`artifact.json` 里写死了：

```json
"hashes": { "AceCombat8.exe": "27e019f2b4d5f1f3" },
"tokens": { "default": { "amd": "...", "intel": "..." } }
```

- 换 exe（打补丁、升版本）→ 哈希不匹配 → 直接失效；
- AMD / Intel 两套令牌不通用；
- 换游戏 = 整套 tokens 重算，这是包作者侧的工作，环境脚本补不了。

### 3.3 CPUID / MSR 的伪装目标不同

本作只需要"别让 Denuvo 看到 hypervisor"。其他方案可能要求：

- 把 `0x40000000` vendor 从 `KVMKVMKVM` / `VMwareVMware` 改成 `Microsoft Hv` 或清零；
- 伪造 MSR `0x40000000~0x40000002`、TSC / RDTSC 偏移；
- 改 SMBIOS / DMI（厂商、型号、序列号）、磁盘型号序列号、网卡 MAC OUI、GPU PCI ID、ACPI 表。

这些都在各包的 `patches` 段里，环境脚本一条都替代不了。

### 3.4 真·虚拟机 guest 场景（最大的坑）

本机是物理机，只解决了"Hyper-V 占用 VMX root"这一层。若游戏跑在 VMware / KVM / Hyper-V 客户机内，还需要：

- 宿主开启嵌套虚拟化：
  - Hyper-V：`Set-VMProcessor -ExposeVirtualizationExtensions $true`
  - VMware：勾选"虚拟化 Intel VT-x/EPT 或 AMD-V/RVI"
  - KVM：`nested=1` + `-cpu host`
- 否则 guest 内 `VMXON` 直接失败。`hyperhv.dll` 里现成的报错就是
  `[!] Error (%s:%d) | Err, VMX is not supported in this machine`；
- guest 内同样要关 Secure Boot（否则 `testsigning` 被固件策略锁死）；
- 即便 CPUID 位清掉，Denuvo 还会看 SMBIOS、磁盘、时序、驱动/服务残留。

### 3.5 反作弊与授权

- 带内核反作弊（EAC / BattlEye / Vanguard）的在线游戏：nested hypervisor + 清 CPUID + 测试签名属于典型封号 / 拒启特征，这类不该用。
- 正版 Denuvo 授权按硬件指纹绑定：改 CPUID / 机器指纹可能让授权失效或触发重新激活，这不是"绕过"，是"换机"。

### 3.6 机器侧硬约束

- 必须能进 BIOS 关 Secure Boot（部分 OEM 笔记本需清 key，且 BitLocker 会要恢复密钥）；
- 同一时刻只能有一个 hypervisor 占 VMX root：本作留下的 `artifact` 服务、其他游戏驱动、Hyper-V、部分反作弊驱动会互相打架；
- Windows 11 24H2 的内存完整性 / VBS 可能被更新重新打开，需要重新检查环境配置；
- AMD / Intel 两条路径使用不同驱动，必须与游戏包和 CPU 厂商匹配。

---

## 4. 判定表

| 目标包形态 | 本 kit 适配度 | 还需要什么 |
|---|---|---|
| 自带 hypervisor + loader（本作 `artifact` 型） | 高，改 `-GameDir` 即可 | 无 |
| 真正在 VM 里跑、要绕 VM 指纹 | 低 | 嵌套虚拟化 + SMBIOS/磁盘/MAC/时序一整套伪装，属于另一个工程 |
| 在线 + 内核反作弊 | 不建议 | 无（风险不可控） |
| 正版 Denuvo 授权 | 谨慎 | 改指纹可能直接废掉授权 |

---

## 5. 一句话总结

**环境准备（Secure Boot / Hyper-V / VBS / HVCI + 测试签名）可以复用；"哪个 bit 要伪装、令牌怎么算、驱动怎么和 loader 对接"这三件事每个包都不一样，本工具包替代不了。**
