# 02-apply.ps1 —— 最小化配置：关 Hyper-V/VBS/HVCI + 开测试签名
# 用法（管理员 PowerShell）:
#   powershell -ExecutionPolicy Bypass -File .\scripts\02-apply.ps1
#   ... -DryRun           不执行配置命令；仍会写日志和备份
#   ... -SkipTestSigning  不改 testsigning（如果不需要加载自签驱动）
#   ... -Force            跳过 BitLocker 风险确认
# 兼容 Windows PowerShell 5.1

param(
    [switch]$DryRun,
    [switch]$SkipTestSigning,
    [switch]$Force
)

. (Join-Path $PSScriptRoot '..\lib\00-common.ps1')
$global:KitDryRun = [bool]$DryRun

Show-Header '02-apply  最小化配置（关 Hyper-V/VBS/HVCI + 开测试签名）'

Assert-Admin

$sb = Get-SecureBootState
Write-Log ('Secure Boot = ' + $sb) 'INFO'
if ($sb -eq 'On' -and -not $SkipTestSigning) {
    Write-Log 'Secure Boot 处于开启状态，testsigning 会被固件策略锁死，脚本无法继续。' 'ERR'
    Write-Host ''
    Write-Host '请在 BIOS 里关闭 Secure Boot（Gigabyte B650M AORUS PRO AX / FB3）：' -ForegroundColor Yellow
    Write-Host '  1) 重启按 Del 进 BIOS' -ForegroundColor Yellow
    Write-Host '  2) Boot 页 -> Secure Boot -> Secure Boot Mode 改为 Custom' -ForegroundColor Yellow
    Write-Host '  3) Delete all Secure Boot Keys（或 Restore Factory Keys 后切到 Setup Mode）' -ForegroundColor Yellow
    Write-Host '  4) F10 保存退出，进系统后执行: Confirm-SecureBootUEFI  应为 False' -ForegroundColor Yellow
    Write-Host '  5) 重新运行本脚本' -ForegroundColor Yellow
    exit 2
}

$bl = Get-BitLockerState
Write-Log ('BitLocker C: ' + $bl) 'INFO'
if ($bl -match 'On|Encryption in Progress|加密进行中|Fully Encrypted|完全加密' -and -not $Force) {
    Write-Log 'BitLocker 处于开启/加密中，改动引导配置可能触发恢复密钥提示。确认无误后加 -Force 重跑。' 'ERR'
    exit 3
}

$backupDir = Backup-State 'apply'

$steps = @(
    @{ Name = '关闭 Hypervisor (hypervisorlaunchtype off)'; Exe = 'bcdedit'; Args = @('/set', 'hypervisorlaunchtype', 'off') },
    @{ Name = '关闭 VSM (vsmlaunchtype off)';              Exe = 'bcdedit'; Args = @('/set', 'vsmlaunchtype', 'off') },
    @{ Name = 'VBS 注册表 = 0';                            Exe = 'reg';     Args = @('add', 'HKLM\SYSTEM\CurrentControlSet\Control\DeviceGuard', '/v', 'EnableVirtualizationBasedSecurity', '/t', 'REG_DWORD', '/d', '0', '/f') },
    @{ Name = 'HVCI 注册表 = 0';                           Exe = 'reg';     Args = @('add', 'HKLM\SYSTEM\CurrentControlSet\Control\DeviceGuard\Scenarios\HypervisorEnforcedCodeIntegrity', '/v', 'Enabled', '/t', 'REG_DWORD', '/d', '0', '/f') },
    @{ Name = 'SystemGuard 注册表 = 0';                    Exe = 'reg';     Args = @('add', 'HKLM\SYSTEM\CurrentControlSet\Control\DeviceGuard\Scenarios\SystemGuard', '/v', 'Enabled', '/t', 'REG_DWORD', '/d', '0', '/f') }
)

if (-not $SkipTestSigning) {
    $steps += @{ Name = '开启测试签名 (testsigning on)'; Exe = 'bcdedit'; Args = @('/set', 'testsigning', 'on') }
}

$failed = New-Object System.Collections.ArrayList
foreach ($s in $steps) {
    $r = Invoke-Cmd -Exe $s.Exe -ArgList $s.Args
    if ($r.ExitCode -ne 0 -and -not $r.DryRun) {
        Write-Log ('失败: ' + $s.Name + ' -> ' + $r.Output.Trim()) 'ERR'
        [void]$failed.Add($s.Name)
    } elseif (-not $r.DryRun) {
        Write-Log ('OK: ' + $s.Name) 'OK'
    }
}

Write-Host ''
Write-Log '---- 应用后状态 ----' 'STEP'
foreach ($n in @('testsigning', 'hypervisorlaunchtype', 'vsmlaunchtype', 'loadoptions')) {
    Write-Log (('{0,-22} = {1}' -f $n, (Get-BcdValue $n)))
}
Write-Log ('备份目录: ' + $backupDir) 'INFO'

if ($failed.Count -gt 0) {
    Write-Log ('有 {0} 项失败，请检查上一条错误。' -f $failed.Count) 'ERR'
    exit 4
}

Write-Host ''
Write-Log '配置完成。必须重启一次才生效。' 'OK'
Write-Log '重启后执行: powershell -ExecutionPolicy Bypass -File .\scripts\03-verify.ps1' 'INFO'
if (-not $global:KitDryRun) {
    Write-Host ''
    $ans = Read-Host '现在重启？(y/N)'
    if ($ans -eq 'y' -or $ans -eq 'Y') {
        Write-Log '5 秒后重启...' 'WARN'
        & shutdown /r /t 5
    }
}
exit 0
