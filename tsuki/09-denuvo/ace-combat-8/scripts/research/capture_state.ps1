$ErrorActionPreference='Continue'
$d='D:\game\backup\ac8'
New-Item -ItemType Directory -Force -Path $d | Out-Null
Set-Location $d
cmd /c "bcdedit /enum {current} > bcd_before.txt 2>&1"
cmd /c "bcdedit /enum {bootmgr} >> bcd_before.txt 2>&1"
cmd /c "reg export ""HKLM\SYSTEM\CurrentControlSet\Control\DeviceGuard"" dg_before.reg /y" | Out-Null
cmd /c "reg export ""HKLM\SYSTEM\CurrentControlSet\Control\Lsa"" lsa_before.reg /y" | Out-Null
cmd /c "reg export ""HKLM\SOFTWARE\Policies\Microsoft\Windows Defender"" defpol_before.reg /y" | Out-Null
cmd /c "systeminfo > sysinfo_before.txt 2>&1"
Get-CimInstance Win32_ComputerSystem | Select-Object Manufacturer,Model,HypervisorPresent,NumberOfLogicalProcessors | Format-List | Out-File -Encoding utf8 cs_before.txt
Get-CimInstance -Namespace root\Microsoft\Windows\DeviceGuard -ClassName Win32_DeviceGuard | Format-List * | Out-File -Encoding utf8 dg_status_before.txt
Get-CimInstance Win32_Processor | Select-Object Name,VirtualizationFirmwareEnabled,VMMonitorModeExtensions,SecondLevelAddressTranslationExtensions | Format-List | Out-File -Encoding utf8 cpu_before.txt
sc.exe query artifact | Out-File -Encoding utf8 svc_before.txt
Write-Output "CAPTURED"; Get-ChildItem $d | Select-Object Name,Length | Format-Table -AutoSize
