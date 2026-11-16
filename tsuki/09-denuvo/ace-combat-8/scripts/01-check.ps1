# 01-check.ps1 —— 检查系统和文件（不改系统配置，会写本地日志）
# 用法:
#   powershell -ExecutionPolicy Bypass -File .\scripts\01-check.ps1
#   powershell -ExecutionPolicy Bypass -File .\scripts\01-check.ps1 -GameDir "D:\game\ac8"
# 兼容 Windows PowerShell 5.1

param(
    [string]$GameDir = 'D:\game\ac8'
)

. (Join-Path $PSScriptRoot '..\lib\00-common.ps1')

Show-Header 'ACE8 / Denuvo 环境体检（只读）'

$os       = Get-CimInstance Win32_OperatingSystem
$cs       = Get-CimInstance Win32_ComputerSystem
$cpu      = Get-CimInstance Win32_Processor | Select-Object -First 1
$vbs      = Get-VbsStatus
$sb       = Get-SecureBootState
$ts       = Get-BcdValue 'testsigning'
$hvlt     = Get-BcdValue 'hypervisorlaunchtype'
$vsmlt    = Get-BcdValue 'vsmlaunchtype'
$loadopts = Get-BcdValue 'loadoptions'
$hvci     = Get-RegValue 'HKLM:\SYSTEM\CurrentControlSet\Control\DeviceGuard\Scenarios\HypervisorEnforcedCodeIntegrity' 'Enabled'
$vbsReg   = Get-RegValue 'HKLM:\SYSTEM\CurrentControlSet\Control\DeviceGuard' 'EnableVirtualizationBasedSecurity'
$sysguard = Get-RegValue 'HKLM:\SYSTEM\CurrentControlSet\Control\DeviceGuard\Scenarios\SystemGuard' 'Enabled'

$rows = New-Object System.Collections.ArrayList
function Add-Row {
    param([string]$Item, $Value, [string]$Hint = '')
    [void]$global:rows.Add([pscustomobject]@{ 项目 = $Item; 值 = [string]$Value; 说明 = $Hint })
}
$global:rows = $rows

Add-Row 'OS' ($os.Caption + ' ' + $os.Version)
Add-Row 'CPU' ($cpu.Name.Trim())
Add-Row 'CPU 厂商' (Get-CpuVendor)
Add-Row 'Secure Boot' $sb 'On 时必须进 BIOS 关闭，否则 testsigning 无法开启'
Add-Row 'testsigning' $ts '需要 Yes；空表示未设置'
Add-Row 'hypervisorlaunchtype' $hvlt '需要 Off'
Add-Row 'vsmlaunchtype' $vsmlt '需要 Off'
Add-Row 'loadoptions' $loadopts 'DISABLE-LSA-ISO 会关闭 LSA 隔离'
Add-Row 'HypervisorPresent' $cs.HypervisorPresent 'False = 当前没有 hypervisor 占用'
Add-Row 'VMMonitorModeExtensions' $cpu.VMMonitorModeExtensions 'True 表示 VT-x/SVM 对本系统可用'

$vbsStatusText = 'N/A'
$vbsSvcText    = 'N/A'
if ($vbs) {
    $vbsStatusText = $vbs.VirtualizationBasedSecurityStatus
    $vbsSvcText    = ($vbs.SecurityServicesRunning -join ',')
}
Add-Row 'VBS 状态 (WMI)' $vbsStatusText '0=关闭 2=运行中'
Add-Row 'VBS 服务运行 (WMI)' $vbsSvcText '1=CredentialGuard 2=HVCI'
Add-Row 'DeviceGuard\EnableVirtualizationBasedSecurity' $vbsReg '需要 0 或不存在'
Add-Row 'HVCI\Enabled' $hvci '需要 0'
Add-Row 'SystemGuard\Enabled' $sysguard '需要 0'
Add-Row 'BitLocker C:' (Get-BitLockerState) '加密开启时改动引导有恢复密钥风险'

$exe = Get-GameExe $GameDir
if ($exe) { Add-Row '游戏 exe' $exe '' } else { Add-Row '游戏 exe' '未找到' '' }

if ($exe) {
    $bin = Split-Path -Parent $exe
    Add-Row 'artifact.dll'   (Test-Path (Join-Path $bin 'artifact.dll'))
    Add-Row 'artifact.json'  (Test-Path (Join-Path $bin 'artifact.json'))
    Add-Row 'Artifact_AMD'   (Test-Path (Join-Path $bin 'Artifact_AMD\SimpleSvm.sys'))
    Add-Row 'Artifact_Intel' (Test-Path (Join-Path $bin 'Artifact_Intel\hyperkd.sys'))
}

$svcArt = & sc.exe query artifact 2>&1 | Out-String
$artState = '未知'
if ($svcArt -match 'RUNNING') { $artState = 'RUNNING' }
elseif ($svcArt -match 'STOPPED') { $artState = 'STOPPED' }
elseif ($svcArt -match '1060') { $artState = '未安装' }
Add-Row 'artifact 服务' $artState '游戏启动时自建，驱动取决于 CPU 厂商'

$global:rows | Format-Table -AutoSize | Out-String -Width 220 | Write-Host

# ---- 结论 ----
Write-Host ''
$problems = New-Object System.Collections.ArrayList

if ($sb -eq 'On') { [void]$problems.Add('Secure Boot 开启 -> 无法开启 testsigning，需要进 BIOS 关闭') }
if ($ts -ne 'Yes' -and $sb -ne 'On') { [void]$problems.Add('testsigning 未开启 -> 游戏自带 SimpleSvm.sys 会因签名校验失败拒绝加载') }
if ($hvlt -ne 'Off') { [void]$problems.Add('hypervisorlaunchtype 不是 Off -> Hyper-V 占用虚拟化，第三方 hypervisor 无法启动') }
if ($hvci -ne $null -and $hvci -ne 0) { [void]$problems.Add(('HVCI Enabled={0} -> 需要 0' -f $hvci)) }
if ($vbs -and $vbs.VirtualizationBasedSecurityStatus -ne 0) { [void]$problems.Add('VBS 仍在运行 -> 关闭 hypervisorlaunchtype 后需重启并确认 VBS=0') }

if ($problems.Count -eq 0) {
    Write-Log '环境就绪：可以直接启动游戏。' 'OK'
    if ($exe) { Write-Log ('  启动: ' + $exe) 'OK' }
    exit 0
} else {
    foreach ($p in $problems) { Write-Log $p 'WARN' }
    Write-Log '执行 .\scripts\02-apply.ps1 完成配置（需要管理员 + 已关闭 Secure Boot）。' 'INFO'
    exit 1
}
