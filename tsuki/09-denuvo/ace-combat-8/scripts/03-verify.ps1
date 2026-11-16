# 03-verify.ps1 —— 重启后验收
# 用法: powershell -ExecutionPolicy Bypass -File .\scripts\03-verify.ps1
# 兼容 Windows PowerShell 5.1

param(
    [string]$GameDir = 'D:\game\ac8'
)

. (Join-Path $PSScriptRoot '..\lib\00-common.ps1')

Show-Header '03-verify  重启后验收'

$cs   = Get-CimInstance Win32_ComputerSystem
$cpu  = Get-CimInstance Win32_Processor | Select-Object -First 1
$vbs  = Get-VbsStatus
$sb   = Get-SecureBootState
$ts   = Get-BcdValue 'testsigning'
$hvlt = Get-BcdValue 'hypervisorlaunchtype'
$hvci = Get-RegValue 'HKLM:\SYSTEM\CurrentControlSet\Control\DeviceGuard\Scenarios\HypervisorEnforcedCodeIntegrity' 'Enabled'
$art  = & sc.exe query artifact 2>&1 | Out-String
$artRunning = ($art -match 'RUNNING')

$checks = New-Object System.Collections.ArrayList
function Add-Check {
    param([string]$Item, $Actual, [string]$Expect, [bool]$Pass)
    [void]$global:checks.Add([pscustomobject]@{ 项目 = $Item; 实测 = [string]$Actual; 期望 = $Expect; 结果 = $(if ($Pass) { 'PASS' } else { 'FAIL' }) })
}
$global:checks = $checks

Add-Check 'Secure Boot' $sb 'Off' ($sb -eq 'Off')
Add-Check 'testsigning' $ts 'Yes' ($ts -eq 'Yes')
Add-Check 'hypervisorlaunchtype' $hvlt 'Off' ($hvlt -eq 'Off')
Add-Check 'HVCI\Enabled' $hvci '0' ($hvci -eq 0 -or $hvci -eq $null)
if ($vbs) {
    Add-Check 'VBS 状态' $vbs.VirtualizationBasedSecurityStatus '0' ($vbs.VirtualizationBasedSecurityStatus -eq 0)
}
Add-Check 'VMMonitorModeExtensions' $cpu.VMMonitorModeExtensions 'True' ($cpu.VMMonitorModeExtensions -eq $true)

# HypervisorPresent 的期望取决于 artifact 驱动是否在跑
$expectHv = 'False（玩游戏前）'
if ($artRunning) { $expectHv = 'True（artifact 已加载）' }
$hvOk = ($artRunning -and $cs.HypervisorPresent -eq $true) -or ((-not $artRunning) -and $cs.HypervisorPresent -eq $false)
Add-Check 'HypervisorPresent' $cs.HypervisorPresent $expectHv $hvOk
Add-Check 'artifact 服务' $(if ($artRunning) { 'RUNNING' } else { '未运行' }) '游戏启动后才出现' $true

$global:checks | Format-Table -AutoSize | Out-String -Width 200 | Write-Host

$fails = @($global:checks | Where-Object { $_.结果 -eq 'FAIL' })
if ($fails.Count -eq 0) {
    Write-Log '验收通过，可以启动游戏。' 'OK'
    $exe = Get-GameExe $GameDir
    if ($exe) { Write-Log ('启动: ' + $exe + '   （或运行 .\scripts\04-launch.ps1）') 'OK' }
    exit 0
} else {
    Write-Log ('有 {0} 项不达标，先处理再启动。' -f $fails.Count) 'ERR'
    exit 1
}
