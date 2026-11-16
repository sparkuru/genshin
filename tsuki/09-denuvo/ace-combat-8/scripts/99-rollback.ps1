# 99-rollback.ps1 —— 按备份和脚本中的固定值回滚（不保证恢复全部原值）
# 用法（管理员）:
#   powershell -ExecutionPolicy Bypass -File .\scripts\99-rollback.ps1
#   ... -DryRun        只打印
#   ... -KeepTestSigning
# 说明:
#   1) 停掉并删除游戏自建的 artifact 服务（否则驱动会一直挂在系统里）
#   2) 关测试签名、恢复 hypervisorlaunchtype=auto
#   3) 优先用 backups\ 下最近一次备份还原 DeviceGuard / Lsa 注册表
#   4) Secure Boot 需要你自己进 BIOS 重新打开
# 兼容 Windows PowerShell 5.1

param(
    [switch]$DryRun,
    [switch]$KeepTestSigning
)

. (Join-Path $PSScriptRoot '..\lib\00-common.ps1')
$global:KitDryRun = [bool]$DryRun

Show-Header '99-rollback  回滚'
Assert-Admin

$backupDir = Get-ChildItem -Path $global:BackupRoot -Directory -ErrorAction SilentlyContinue |
             Sort-Object Name -Descending | Select-Object -First 1

if ($backupDir) { Write-Log ('使用备份: ' + $backupDir.FullName) 'INFO' }
else { Write-Log '没有找到 backups\ 备份，将按默认值回滚。' 'WARN' }

$steps = New-Object System.Collections.ArrayList

# 1) 驱动服务
[void]$steps.Add(@{ Name = '停止 artifact 服务'; Exe = 'sc.exe'; Args = @('stop', 'artifact'); IgnoreExit = $true })
[void]$steps.Add(@{ Name = '删除 artifact 服务'; Exe = 'sc.exe'; Args = @('delete', 'artifact'); IgnoreExit = $true })

# 2) 引导
if (-not $KeepTestSigning) {
    [void]$steps.Add(@{ Name = '关闭测试签名'; Exe = 'bcdedit'; Args = @('/set', 'testsigning', 'off') })
}
[void]$steps.Add(@{ Name = '恢复 hypervisorlaunchtype=auto'; Exe = 'bcdedit'; Args = @('/set', 'hypervisorlaunchtype', 'auto') })
[void]$steps.Add(@{ Name = 'vsmlaunchtype=off（原值）'; Exe = 'bcdedit'; Args = @('/set', 'vsmlaunchtype', 'off') })

# 3) 注册表
if ($backupDir) {
    $dg = Join-Path $backupDir.FullName 'DeviceGuard.reg'
    $lsa = Join-Path $backupDir.FullName 'Lsa.reg'
    if (Test-Path $dg)  { [void]$steps.Add(@{ Name = '导入 DeviceGuard.reg'; Exe = 'reg'; Args = @('import', $dg) }) }
    if (Test-Path $lsa) { [void]$steps.Add(@{ Name = '导入 Lsa.reg'; Exe = 'reg'; Args = @('import', $lsa) }) }
} else {
    [void]$steps.Add(@{ Name = '删除 EnableVirtualizationBasedSecurity'; Exe = 'reg'; Args = @('delete', 'HKLM\SYSTEM\CurrentControlSet\Control\DeviceGuard', '/v', 'EnableVirtualizationBasedSecurity', '/f'); IgnoreExit = $true })
    [void]$steps.Add(@{ Name = 'HVCI Enabled=1'; Exe = 'reg'; Args = @('add', 'HKLM\SYSTEM\CurrentControlSet\Control\DeviceGuard\Scenarios\HypervisorEnforcedCodeIntegrity', '/v', 'Enabled', '/t', 'REG_DWORD', '/d', '1', '/f') })
}

foreach ($s in $steps) {
    $r = Invoke-Cmd -Exe $s.Exe -ArgList $s.Args
    if ($r.ExitCode -ne 0 -and -not $r.DryRun -and -not $s.IgnoreExit) {
        Write-Log ('失败: ' + $s.Name + ' -> ' + $r.Output.Trim()) 'ERR'
    }
}

Write-Host ''
Write-Log '---- 回滚后状态 ----' 'STEP'
foreach ($n in @('testsigning', 'hypervisorlaunchtype', 'vsmlaunchtype')) {
    Write-Log (('{0,-22} = {1}' -f $n, (Get-BcdValue $n)))
}
Write-Log ('Secure Boot = ' + (Get-SecureBootState)) 'INFO'

Write-Host ''
Write-Log '注册表/引导已回滚。剩下两步需要人工：' 'WARN'
Write-Log '  1) BIOS 里把 Secure Boot 打开（Boot -> Secure Boot -> Restore Factory Keys / Standard）' 'WARN'
Write-Log '  2) 重启: shutdown /r /t 5' 'WARN'
Write-Log '回滚后游戏会因为驱动签名失败而无法启动，这是预期行为。' 'INFO'
exit 0
