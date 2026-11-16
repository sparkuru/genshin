$ErrorActionPreference='Continue'
$exe='D:\game\ac8\Game\Binaries\Win64\AceCombat8.exe'
$wd='D:\game\ac8\Game\Binaries\Win64'
$out='D:\game\backup\ac8\game_out.txt'
$err='D:\game\backup\ac8\game_err.txt'
$p=Start-Process -FilePath $exe -WorkingDirectory $wd -RedirectStandardOutput $out -RedirectStandardError $err -PassThru -NoNewWindow
Start-Sleep -Seconds 12
$p.Refresh()
Write-Output "exit=$($p.ExitCode) hasExited=$($p.HasExited)"
Write-Output "== stdout"; if (Test-Path $out) { Get-Content $out -Raw }
Write-Output "== stderr"; if (Test-Path $err) { Get-Content $err -Raw }
Write-Output "== SCM events"; Get-WinEvent -FilterHashtable @{LogName='System';StartTime=(Get-Date).AddMinutes(-3)} -ErrorAction SilentlyContinue | Where-Object {$_.ProviderName -match 'Service Control' -or $_.Message -match 'artifact|SimpleSvm'} | Select-Object TimeCreated,ProviderName,@{n='M';e={$_.Message.Substring(0,[Math]::Min(260,$_.Message.Length))}} | Format-List
Write-Output "== services"; Get-Service | Where-Object {$_.Name -match 'artifact|SimpleSvm'} | Select-Object Name,Status | Format-Table
Write-Output "== sc qc artifact"; sc.exe qc artifact
Write-Output DONE
