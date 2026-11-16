$ErrorActionPreference='Continue'
$exe='D:\game\ac8\Game\Binaries\Win64\AceCombat8.exe'
$wd='D:\game\ac8\Game\Binaries\Win64'
$p=Start-Process -FilePath $exe -WorkingDirectory $wd -PassThru
$t0=Get-Date; $peak=0
for($i=0;$i -lt 120;$i++){
  Start-Sleep -Seconds 2
  $p.Refresh()
  if($p.HasExited){ break }
  $m=[math]::Round((Get-Process -Id $p.Id -ErrorAction SilentlyContinue).WorkingSet64/1MB)
  if($m -gt $peak){$peak=$m}
}
$dur=((Get-Date)-$t0).TotalSeconds
Write-Output "duration=${dur}s peakMem=${peak}MB exited=$($p.HasExited) code=$($p.ExitCode)"
Write-Output "== app log"; Get-WinEvent -FilterHashtable @{LogName='Application';StartTime=(Get-Date).AddMinutes(-6)} -ErrorAction SilentlyContinue | Where-Object {$_.Message -match 'AceCombat8|artifact|d3d12|KERNELBASE|0xc000'} | Select-Object TimeCreated,ProviderName,Id,@{n='M';e={$_.Message.Substring(0,[Math]::Min(500,$_.Message.Length))}} | Format-List
Write-Output "== crash dirs"; Get-ChildItem "$env:LOCALAPPDATA\CrashReportClient","$env:LOCALAPPDATA\ACZero","$env:LOCALAPPDATA\AceCombat8","D:\game\ac8\Game\Saved","D:\game\ac8\ACZero\Saved" -Recurse -ErrorAction SilentlyContinue | Where-Object {$_.LastWriteTime -gt (Get-Date).AddMinutes(-6)} | Select-Object FullName,Length,LastWriteTime | Format-Table -AutoSize
Write-Output DONE
