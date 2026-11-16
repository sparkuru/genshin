$ErrorActionPreference='Continue'
$exe='D:\game\ac8\Game\Binaries\Win64\AceCombat8.exe'
$wd='D:\game\ac8\Game\Binaries\Win64'
Write-Output "== launching $exe"
$t0=Get-Date
$p=Start-Process -FilePath $exe -WorkingDirectory $wd -PassThru
Start-Sleep -Seconds 20
$p.Refresh()
Write-Output "pid=$($p.Id) hasExited=$($p.HasExited) exit=$($p.ExitCode)"
Get-Process -Name AceCombat8 -ErrorAction SilentlyContinue | Select-Object Id,ProcessName,MainWindowTitle,Responding,@{n='RAM_MB';e={[math]::Round($_.WorkingSet64/1MB)}} | Format-List
Start-Sleep -Seconds 20
$p.Refresh()
Write-Output "after 40s: hasExited=$($p.HasExited)"
Get-Process -Name AceCombat8 -ErrorAction SilentlyContinue | Select-Object Id,MainWindowTitle,Responding,@{n='RAM_MB';e={[math]::Round($_.WorkingSet64/1MB)}} | Format-List
Write-Output "== child processes"
Get-CimInstance Win32_Process | Where-Object {$_.ParentProcessId -eq $p.Id -or $_.Name -match 'EasyAnti|start_protected'} | Select-Object Name,ProcessId,CommandLine | Format-List
Write-Output "== event log (last 5 min)"
Get-WinEvent -FilterHashtable @{LogName='Application';StartTime=(Get-Date).AddMinutes(-5)} -ErrorAction SilentlyContinue | Where-Object {$_.Message -match 'AceCombat|Denuvo|EasyAnti|0xc000|0xe'} | Select-Object TimeCreated,ProviderName,LevelDisplayName,@{n='Msg';e={$_.Message.Substring(0,[Math]::Min(300,$_.Message.Length))}} | Format-List
Write-Output "LAUNCH_DONE"
