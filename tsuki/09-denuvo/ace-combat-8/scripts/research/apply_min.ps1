$ErrorActionPreference='Continue'
Write-Output "== [1] bcdedit hypervisorlaunchtype off"
bcdedit /set hypervisorlaunchtype off
Write-Output "== [2] bcdedit vsmlaunchtype off"
bcdedit /set vsmlaunchtype off
Write-Output "== [3] VBS off"
reg add "HKLM\SYSTEM\CurrentControlSet\Control\DeviceGuard" /v EnableVirtualizationBasedSecurity /t REG_DWORD /d 0 /f
Write-Output "== [4] HVCI off"
reg add "HKLM\SYSTEM\CurrentControlSet\Control\DeviceGuard\Scenarios\HypervisorEnforcedCodeIntegrity" /v Enabled /t REG_DWORD /d 0 /f
Write-Output "== [5] SystemGuard off"
reg add "HKLM\SYSTEM\CurrentControlSet\Control\DeviceGuard\Scenarios\SystemGuard" /v Enabled /t REG_DWORD /d 0 /f
Write-Output "== [6] result"
cmd /c "bcdedit /enum {current}" | Select-String -Pattern "hypervisorlaunchtype|vsmlaunchtype|loadoptions|testsigning"
reg query "HKLM\SYSTEM\CurrentControlSet\Control\DeviceGuard" /v EnableVirtualizationBasedSecurity
reg query "HKLM\SYSTEM\CurrentControlSet\Control\DeviceGuard\Scenarios\HypervisorEnforcedCodeIntegrity" /v Enabled
Write-Output "APPLIED"
