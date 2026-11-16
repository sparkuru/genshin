$ErrorActionPreference='Continue'
$exe='D:\game\ac8\Game\Binaries\Win64\AceCombat8.exe'
$wd='D:\game\ac8\Game\Binaries\Win64'
$p=Start-Process -FilePath $exe -WorkingDirectory $wd -PassThru
Write-Output "started pid=$($p.Id) at $(Get-Date -Format HH:mm:ss)"
for($i=0;$i -lt 30;$i++){
  Start-Sleep -Seconds 2
  $p.Refresh()
  if($p.HasExited){ Write-Output "+$($i*2+2)s EXITED code=$($p.ExitCode)"; break }
  $w=(Get-Process -Id $p.Id -ErrorAction SilentlyContinue).MainWindowTitle
  $m=[math]::Round((Get-Process -Id $p.Id -ErrorAction SilentlyContinue).WorkingSet64/1MB)
  Write-Output "+$($i*2+2)s alive mem=${m}MB title='$w'"
}
Get-Process -Name AceCombat8 -ErrorAction SilentlyContinue | Select-Object Id,MainWindowTitle,Responding,@{n='RAM_MB';e={[math]::Round($_.WorkingSet64/1MB)}} | Format-List
Write-Output "== windows"; Get-Process | Where-Object {$_.MainWindowTitle -ne ''} | Select-Object ProcessName,MainWindowTitle | Format-Table -AutoSize
Write-Output "== wer"; Get-WinEvent -FilterHashtable @{LogName='Application';StartTime=(Get-Date).AddMinutes(-3)} -ErrorAction SilentlyContinue | Select-Object TimeCreated,ProviderName,LevelDisplayName,@{n='M';e={$_.Message.Substring(0,[Math]::Min(200,$_.Message.Length))}} | Format-List
Write-Output DONE
