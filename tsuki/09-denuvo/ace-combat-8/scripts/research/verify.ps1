$ErrorActionPreference='Continue'
Write-Output "== ComputerSystem"; Get-CimInstance Win32_ComputerSystem | Select-Object HypervisorPresent | Format-List
Write-Output "== CPU"; Get-CimInstance Win32_Processor | Select-Object VirtualizationFirmwareEnabled,VMMonitorModeExtensions,SecondLevelAddressTranslationExtensions | Format-List
Write-Output "== DeviceGuard"; Get-CimInstance -Namespace root\Microsoft\Windows\DeviceGuard -ClassName Win32_DeviceGuard | Select-Object VirtualizationBasedSecurityStatus,SecurityServicesConfigured,SecurityServicesRunning | Format-List
Write-Output "== bcd"; cmd /c "bcdedit /enum {current}" | Select-String -Pattern "testsigning|hypervisorlaunchtype|vsmlaunchtype|loadoptions"
Write-Output "== systeminfo hyperv"; cmd /c "systeminfo" | Select-String -Pattern "Hyper-V|虚拟机监控程序|hypervisor" -Context 0,4
Write-Output "== svc"; sc.exe query artifact
