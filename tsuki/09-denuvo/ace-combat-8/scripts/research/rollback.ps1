$ErrorActionPreference='Continue'
$d='D:\game\backup\ac8'
Write-Output "== restore bcd"
bcdedit /set hypervisorlaunchtype auto
bcdedit /set vsmlaunchtype off
Write-Output "== delete added value"
reg delete "HKLM\SYSTEM\CurrentControlSet\Control\DeviceGuard" /v EnableVirtualizationBasedSecurity /f
Write-Output "== import original DeviceGuard"
reg import "$d\dg_before.reg"
Write-Output "== import original Lsa"
reg import "$d\lsa_before.reg"
cmd /c "bcdedit /enum {current}" | Select-String -Pattern "hypervisorlaunchtype|vsmlaunchtype"
reg query "HKLM\SYSTEM\CurrentControlSet\Control\DeviceGuard\Scenarios\HypervisorEnforcedCodeIntegrity" /v Enabled
Write-Output "ROLLED BACK (reboot required)"
