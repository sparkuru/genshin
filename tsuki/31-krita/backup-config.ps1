[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$Destination,
    [Parameter(Mandatory = $true)][string]$WacomBackupFile,
    [string]$LocalDataPath = $env:LOCALAPPDATA,
    [string]$RoamingDataPath = $env:APPDATA,
    [string]$KritaExePath = 'D:\software\krita\bin\krita.exe'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Assert-NoReparsePoint {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [switch]$Recursive
    )

    $item = Get-Item -LiteralPath $Path -Force
    if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
        throw "Refusing to copy a reparse point: $Path"
    }
    if ($Recursive -and $item.PSIsContainer) {
        $link = Get-ChildItem -LiteralPath $Path -Recurse -Force |
            Where-Object { ($_.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0 } |
            Select-Object -First 1
        if ($null -ne $link) {
            throw "Refusing to copy a resource tree containing a reparse point: $($link.FullName)"
        }
    }
}

if ($env:OS -ne 'Windows_NT') {
    throw 'This script requires Windows.'
}
if (Get-Process -Name krita -ErrorAction SilentlyContinue) {
    throw 'Save your work and close every Krita process before backing up.'
}
if (-not (Test-Path -LiteralPath $WacomBackupFile -PathType Leaf)) {
    throw "The Wacom Preferences Utility backup is missing: $WacomBackupFile"
}
if ([System.IO.Path]::GetExtension($WacomBackupFile) -ine '.wacomprefs') {
    throw 'WacomBackupFile must be a full .wacomprefs export.'
}
if ((Get-Item -LiteralPath $WacomBackupFile).Length -le 0) {
    throw 'The Wacom preferences export is empty.'
}
Assert-NoReparsePoint -Path $WacomBackupFile

$destinationPath = [System.IO.Path]::GetFullPath($Destination).TrimEnd('\')
if (Test-Path -LiteralPath $destinationPath) {
    throw "Destination already exists: $destinationPath"
}
$parent = Split-Path -Path $destinationPath -Parent
if (-not (Test-Path -LiteralPath $parent -PathType Container)) {
    throw "Destination parent does not exist: $parent"
}
Assert-NoReparsePoint -Path $parent
$stage = Join-Path $parent ('.krita-backup-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $stage | Out-Null

try {
    $localTarget = Join-Path $stage 'krita\local'
    $resourcesTarget = Join-Path $stage 'krita\resources'
    $wacomTarget = Join-Path $stage 'wacom'
    $systemTarget = Join-Path $stage 'system'
    foreach ($directory in @($localTarget, $wacomTarget, $systemTarget)) {
        New-Item -ItemType Directory -Path $directory -Force | Out-Null
    }

    foreach ($name in @('kritarc', 'kritadisplayrc', 'kritaopenglrc')) {
        $source = Join-Path $LocalDataPath $name
        if (Test-Path -LiteralPath $source -PathType Leaf) {
            Assert-NoReparsePoint -Path $source
            Copy-Item -LiteralPath $source -Destination (Join-Path $localTarget $name)
        }
    }
    foreach ($name in @('kritarc', 'kritadisplayrc')) {
        if (-not (Test-Path -LiteralPath (Join-Path $localTarget $name) -PathType Leaf)) {
            throw "Required Krita configuration is missing: $name"
        }
    }

    $resources = Join-Path $RoamingDataPath 'krita'
    if (-not (Test-Path -LiteralPath $resources -PathType Container)) {
        throw "Krita resources directory is missing: $resources"
    }
    Assert-NoReparsePoint -Path $resources -Recursive
    Copy-Item -LiteralPath $resources -Destination $resourcesTarget -Recurse -Force
    Copy-Item -LiteralPath $WacomBackupFile -Destination (Join-Path $wacomTarget 'Wacom.wacomprefs')

    $holdMode = $null
    $penKey = [Microsoft.Win32.Registry]::CurrentUser.OpenSubKey('Software\Microsoft\Wisp\Pen\SysEventParameters')
    if ($null -ne $penKey) {
        try {
            $holdMode = $penKey.GetValue('HoldMode', $null)
        } finally {
            $penKey.Dispose()
        }
    }
    $metadata = [ordered]@{
        schema = 1
        createdUtc = [DateTime]::UtcNow.ToString('o')
        kritaExecutable = $KritaExePath
        windowsPenHoldMode = $holdMode
        wacomServiceName = 'WTabletServicePro'
    }
    $metadata | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $systemTarget 'settings.json') -Encoding UTF8
    $sc = Get-Command sc.exe -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($null -ne $sc) {
        $trigger = & $sc.Source qtriggerinfo WTabletServicePro 2>&1
        if ($LASTEXITCODE -eq 0) {
            $trigger | Out-File -LiteralPath (Join-Path $systemTarget 'wacom-trigger.txt') -Encoding UTF8
        }
    }

    $stagePrefix = $stage.TrimEnd('\') + '\'
    $files = @(
        Get-ChildItem -LiteralPath $stage -Recurse -File -Force | Sort-Object FullName | ForEach-Object {
            [ordered]@{
                path = $_.FullName.Substring($stagePrefix.Length).Replace('\', '/')
                bytes = $_.Length
                sha256 = (Get-FileHash -LiteralPath $_.FullName -Algorithm SHA256).Hash.ToLowerInvariant()
            }
        }
    )
    [ordered]@{ schema = 1; files = $files } | ConvertTo-Json -Depth 5 |
        Set-Content -LiteralPath (Join-Path $stage 'manifest.json') -Encoding UTF8

    [System.IO.Directory]::Move($stage, $destinationPath)
    Write-Host "Backup created: $destinationPath"
    Write-Host "Files: $($files.Count)"
} finally {
    if (Test-Path -LiteralPath $stage -PathType Container) {
        Remove-Item -LiteralPath $stage -Recurse -Force
    }
}
