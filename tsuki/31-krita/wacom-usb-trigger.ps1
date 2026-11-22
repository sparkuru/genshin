[CmdletBinding()]
param([switch]$Apply)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

$serviceName = 'WTabletServicePro'
$interfaceGuid = 'a5dcbf10-6530-11d2-901f-00c04fb951ed'
$deviceId = 'USB\VID_056A&PID_0378'
$triggerRoot = "HKLM:\SYSTEM\CurrentControlSet\Services\$serviceName\TriggerInfo"

function Get-TriggerState {
    if (-not (Test-Path -LiteralPath $triggerRoot)) { return 'Missing' }
    $triggerKeys = @(Get-ChildItem -LiteralPath $triggerRoot)
    if ($triggerKeys.Count -eq 0) { return 'Missing' }
    if ($triggerKeys.Count -ne 1) { return 'Other' }

    $key = $triggerKeys[0]
    $values = Get-ItemProperty -LiteralPath $key.PSPath
    $names = @($key.Property)
    foreach ($name in @('Type', 'Action', 'Guid', 'Data0', 'DataType0')) {
        if ($names -notcontains $name) { return 'Other' }
    }
    $dataNames = @($names | Where-Object { $_ -match '^(Data|DataType)\d+$' })
    if ($dataNames.Count -ne 2 -or $values.Type -ne 1 -or $values.Action -ne 1 -or $values.DataType0 -ne 2) {
        return 'Other'
    }
    try {
        $actualGuid = ([guid]::new([byte[]]$values.Guid)).ToString()
        $actualDeviceId = [Text.Encoding]::Unicode.GetString([byte[]]$values.Data0).TrimEnd([char]0)
    } catch {
        return 'Other'
    }
    if ($actualGuid -ieq $interfaceGuid -and $actualDeviceId -ieq $deviceId) { return 'Expected' }
    return 'Other'
}

if ($env:OS -ne 'Windows_NT') { throw 'This script requires Windows.' }
$service = Get-Service -Name $serviceName -ErrorAction Stop
$state = Get-TriggerState
if ($state -eq 'Other') {
    throw 'Other Wacom service triggers are present. Refusing to replace them; inspect sc.exe qtriggerinfo first.'
}
Write-Host "Wacom trigger: $state; service start type: $($service.StartType); state: $($service.Status)"
if ($state -eq 'Expected' -and $service.StartType -eq 'Manual') {
    Write-Host 'The requested service configuration is already present.'
    return
}
if (-not $Apply) {
    Write-Host 'Preview only. Run from an elevated PowerShell with -Apply to configure it.'
    return
}
$identity = [Security.Principal.WindowsIdentity]::GetCurrent()
$principal = New-Object Security.Principal.WindowsPrincipal($identity)
if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'Run this script in an elevated PowerShell window.'
}

if ($state -eq 'Missing') {
    $trigger = "start/device/$interfaceGuid/$deviceId"
    & sc.exe triggerinfo $serviceName $trigger
    if ($LASTEXITCODE -ne 0) { throw "Could not add the device-arrival trigger: sc exit $LASTEXITCODE" }
    if ((Get-TriggerState) -ne 'Expected') { throw 'The created device trigger did not verify.' }
}
if ($service.StartType -ne 'Manual') {
    & sc.exe config $serviceName 'start=' 'demand'
    if ($LASTEXITCODE -ne 0) { throw "The trigger exists, but changing startup to Manual failed: sc exit $LASTEXITCODE" }
}
$service.Refresh()
if ((Get-TriggerState) -ne 'Expected' -or $service.StartType -ne 'Manual') {
    throw 'The service configuration did not verify.'
}
Write-Host 'USB arrival starts the Wacom service; no stop trigger was added.'
