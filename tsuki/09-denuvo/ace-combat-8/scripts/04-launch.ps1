# 04-launch.ps1 —— 启动游戏（自动处理 SSH/服务会话下 GUI 不显示的问题）
# 用法:
#   powershell -ExecutionPolicy Bypass -File .\scripts\04-launch.ps1
#   ... -GameDir "D:\game\ac8" -WaitSeconds 90
# 说明:
#   * 会话 0（SSH/服务）里启动的进程会随会话断开被杀，且窗口不在可见桌面 -> 用计划任务投到 console
#   * 游戏可能"自举"：第一个进程加载驱动/保护后会再拉一个自己，旧的退出属正常
#     所以健康检查按"名字"轮询，而不是盯住某个 PID
# 兼容 Windows PowerShell 5.1

param(
    [string]$GameDir = 'D:\game\ac8',
    [int]$WaitSeconds = 60
)

. (Join-Path $PSScriptRoot '..\lib\00-common.ps1')

Show-Header '04-launch  启动游戏'

$exe = Get-GameExe $GameDir
if (-not $exe) {
    Write-Log ('未找到游戏 exe，检查 -GameDir: ' + $GameDir) 'ERR'
    exit 1
}
$bin  = Split-Path -Parent $exe
$name = [IO.Path]::GetFileNameWithoutExtension($exe)
Write-Log ('游戏: ' + $exe) 'INFO'

$before = @(Get-Process -Name $name -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Id)
if ($before.Count -gt 0) { Write-Log ('启动前已有实例: ' + ($before -join ',')) 'WARN' }

$mySession = (Get-Process -Id $PID).SessionId
Write-Log ('当前会话: ' + $mySession) 'INFO'

if ($mySession -ne 0) {
    Start-Process -FilePath $exe -WorkingDirectory $bin
    Write-Log '已在当前桌面启动。' 'OK'
} else {
    Write-Log '当前是服务/SSH 会话，改用计划任务投递到 console 会话。' 'WARN'
    $wrapper = Join-Path $env:TEMP 'denuvo-kit-launch.cmd'
    $content = '@echo off' + "`r`n" + ('cd /d "{0}"' -f $bin) + "`r`n" + ('start "" "{0}"' -f (Split-Path -Leaf $exe))
    Set-Content -Path $wrapper -Value $content -Encoding ASCII

    $taskName = 'DenuvoKitLaunch'
    & schtasks /create /tn $taskName /tr $wrapper /sc ONCE /st 23:59 /it /f | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Log '创建计划任务失败（需要管理员？）。也可以直接在桌面上双击 exe。' 'ERR'
        exit 2
    }
    & schtasks /run /tn $taskName | Out-Null
    Write-Log '计划任务已触发。' 'INFO'
    Start-Sleep -Seconds 8
    & schtasks /delete /tn $taskName /f | Out-Null
}

# 按进程名轮询：游戏可能自举重启，不要盯单个 PID
$maxMem = 0
$seen   = New-Object System.Collections.ArrayList
$deadline = (Get-Date).AddSeconds($WaitSeconds)
while ((Get-Date) -lt $deadline) {
    Start-Sleep -Seconds 5
    $procs = @(Get-Process -Name $name -ErrorAction SilentlyContinue)
    foreach ($pr in $procs) { if (-not $seen.Contains($pr.Id)) { [void]$seen.Add($pr.Id) } }
    if ($procs.Count -gt 0) {
        $m = [math]::Round((($procs | Measure-Object WorkingSet64 -Maximum).Maximum) / 1MB)
        if ($m -gt $maxMem) { $maxMem = $m }
        Write-Log ('  运行中: PID ' + (($procs | ForEach-Object { $_.Id }) -join ',') + ('  mem(MB)=' + $m))
    }
}

$alive = @(Get-Process -Name $name -ErrorAction SilentlyContinue)
if ($alive.Count -eq 0) {
    Write-Log ('没有存活实例（历史 PID: ' + ($seen -join ',') + '）。先查系统日志：') 'ERR'
    Write-Log '  Get-WinEvent -FilterHashtable @{LogName="System";StartTime=(Get-Date).AddMinutes(-3)} | Where-Object {$_.Message -match "artifact"}' 'INFO'
    exit 3
}

Write-Log ('存活: PID ' + (($alive | ForEach-Object { $_.Id }) -join ',') + ('  峰值内存 ' + $maxMem + ' MB')) 'OK'

# GPU 使用率（判断是否真的在渲染）
try {
    $ids = ($alive | ForEach-Object { 'pid_' + $_.Id + '_' }) -join '|'
    $samples = (Get-Counter '\GPU Engine(*)\Utilization Percentage' -ErrorAction Stop).CounterSamples |
               Where-Object { $_.InstanceName -match $ids -and $_.CookedValue -gt 1 }
    if ($samples) {
        foreach ($s in $samples | Select-Object -First 4) {
            Write-Log ('  GPU {0} = {1:N1}%' -f $s.InstanceName, $s.CookedValue)
        }
        Write-Log 'GPU 有占用 = 正在渲染。' 'OK'
    } else {
        Write-Log '未采到 GPU 用量（可能还在初始化，或性能计数器被禁用）。' 'WARN'
    }
} catch {
    Write-Log ('GPU 计数不可用: ' + $_.Exception.Message) 'WARN'
}

exit 0
