[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$SnapshotPath,
    [Parameter(Mandatory = $true)][string]$RollbackDirectory,
    [string]$LocalDataPath = $env:LOCALAPPDATA,
    [string]$RoamingDataPath = $env:APPDATA,
    [switch]$RestoreWindowsPen,
    [switch]$Apply
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Get-SnapshotFile {
    param([string]$Root, [string]$RelativePath)

    if ([string]::IsNullOrWhiteSpace($RelativePath) -or
        $RelativePath -match '(^|/)\.\.(/|$)' -or
        $RelativePath.StartsWith('/') -or $RelativePath.Contains('\') -or
        $RelativePath -match '^[A-Za-z]:') {
        throw "Invalid snapshot path: $RelativePath"
    }
    $fullPath = [System.IO.Path]::GetFullPath((Join-Path $Root $RelativePath.Replace('/', '\')))
    if (-not $fullPath.StartsWith($Root.TrimEnd('\') + '\', [StringComparison]::OrdinalIgnoreCase)) {
        throw "Snapshot path escapes its root: $RelativePath"
    }
    return $fullPath
}

if ($env:OS -ne 'Windows_NT') {
    throw 'This script requires Windows.'
}
if ($Apply -and (Get-Process -Name krita -ErrorAction SilentlyContinue)) {
    throw 'Save your work and close every Krita process before restoring.'
}
foreach ($path in @($SnapshotPath, $LocalDataPath, $RoamingDataPath)) {
    if (-not (Test-Path -LiteralPath $path -PathType Container)) {
        throw "Directory not found: $path"
    }
    if (((Get-Item -LiteralPath $path -Force).Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
        throw "Refusing a reparse-point directory: $path"
    }
}

$snapshot = [System.IO.Path]::GetFullPath($SnapshotPath).TrimEnd('\')
$rollback = [System.IO.Path]::GetFullPath($RollbackDirectory).TrimEnd('\')
if (Test-Path -LiteralPath $rollback) {
    throw "Rollback directory already exists: $rollback"
}
$rollbackParent = Split-Path -Path $rollback -Parent
if (-not (Test-Path -LiteralPath $rollbackParent -PathType Container)) {
    throw "Rollback parent does not exist: $rollbackParent"
}
$targetResources = Join-Path $RoamingDataPath 'krita'
foreach ($protected in @($snapshot, $targetResources)) {
    $protectedFull = [System.IO.Path]::GetFullPath($protected).TrimEnd('\')
    if ($rollback.Equals($protectedFull, [StringComparison]::OrdinalIgnoreCase) -or
        $rollback.StartsWith($protectedFull + '\', [StringComparison]::OrdinalIgnoreCase)) {
        throw 'Rollback directory must be outside the snapshot and Krita resources.'
    }
}

$manifestPath = Join-Path $snapshot 'manifest.json'
if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) {
    throw 'Snapshot manifest.json is missing.'
}
$manifest = Get-Content -LiteralPath $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
if ($manifest.schema -ne 1) {
    throw "Unsupported snapshot schema: $($manifest.schema)"
}
$listed = @{}
foreach ($entry in @($manifest.files)) {
    $relative = [string]$entry.path
    if ($listed.ContainsKey($relative)) {
        throw "Duplicate snapshot entry: $relative"
    }
    $listed[$relative] = $true
    $file = Get-SnapshotFile -Root $snapshot -RelativePath $relative
    if (-not (Test-Path -LiteralPath $file -PathType Leaf)) {
        throw "Snapshot file missing: $relative"
    }
    $item = Get-Item -LiteralPath $file -Force
    if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
        throw "Snapshot file is a reparse point: $relative"
    }
    if ($item.Length -ne [long]$entry.bytes -or
        (Get-FileHash -LiteralPath $file -Algorithm SHA256).Hash -ine [string]$entry.sha256) {
        throw "Snapshot verification failed: $relative"
    }
}
$prefix = $snapshot + '\'
$actual = @(Get-ChildItem -LiteralPath $snapshot -Recurse -File -Force | Where-Object { $_.FullName -ine $manifestPath })
foreach ($file in $actual) {
    $relative = $file.FullName.Substring($prefix.Length).Replace('\', '/')
    if (-not $listed.ContainsKey($relative)) {
        throw "Unexpected file in snapshot: $relative"
    }
}
if ($actual.Count -ne $listed.Count) {
    throw 'Snapshot file count does not match the manifest.'
}
foreach ($required in @('krita/local/kritarc', 'krita/local/kritadisplayrc', 'wacom/Wacom.wacomprefs', 'system/settings.json')) {
    if (-not $listed.ContainsKey($required)) {
        throw "Required snapshot file missing: $required"
    }
}
$sourceResources = Join-Path $snapshot 'krita\resources'
if (-not (Test-Path -LiteralPath $sourceResources -PathType Container)) {
    throw 'The Krita resources directory is missing from the snapshot.'
}
if (((Get-Item -LiteralPath $sourceResources -Force).Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
    throw 'The snapshot resources directory is a reparse point.'
}
$links = @(Get-ChildItem -LiteralPath $sourceResources -Recurse -Force | Where-Object {
    ($_.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0
})
if ($links.Count -ne 0) {
    throw 'The snapshot resources contain a reparse point.'
}
$metadata = Get-Content -LiteralPath (Join-Path $snapshot 'system\settings.json') -Raw -Encoding UTF8 | ConvertFrom-Json

Write-Host "Verified snapshot: $snapshot ($($listed.Count) files)"
Write-Host "Krita config target: $LocalDataPath"
Write-Host "Krita resources target: $targetResources"
Write-Host "Rollback directory: $rollback"
Write-Host "Original Krita executable: $($metadata.kritaExecutable)"
Write-Host "Saved Windows pen HoldMode: $($metadata.windowsPenHoldMode)"
Write-Host 'Wacom preferences must be restored separately with Wacom PrefUtil.'
if (-not $Apply) {
    Write-Host 'Preview only. Add -Apply to restore Krita settings and resources.'
    return
}

$localNames = @('kritarc', 'kritadisplayrc', 'kritaopenglrc')
$priorPresence = @{}
foreach ($name in $localNames) {
    $target = Join-Path $LocalDataPath $name
    if (Test-Path -LiteralPath $target) {
        $item = Get-Item -LiteralPath $target -Force
        if ($item.PSIsContainer -or ($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
            throw "Refusing unexpected target: $target"
        }
    }
    $priorPresence[$name] = Test-Path -LiteralPath $target -PathType Leaf
}
if (Test-Path -LiteralPath $targetResources) {
    $item = Get-Item -LiteralPath $targetResources -Force
    if (-not $item.PSIsContainer -or ($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
        throw "Refusing unexpected resources target: $targetResources"
    }
}

New-Item -ItemType Directory -Path $rollback | Out-Null
$rollbackLocal = Join-Path $rollback 'local'
New-Item -ItemType Directory -Path $rollbackLocal | Out-Null
foreach ($name in $localNames) {
    if ($priorPresence[$name]) {
        Copy-Item -LiteralPath (Join-Path $LocalDataPath $name) -Destination (Join-Path $rollbackLocal $name)
    }
}
$priorPresence | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $rollback 'local-presence.json') -Encoding UTF8

$guid = [guid]::NewGuid().ToString('N')
$stage = Join-Path $RoamingDataPath ('.krita-restore-' + $guid)
$previous = Join-Path $RoamingDataPath ('.krita-before-restore-' + $guid)
$previousMoved = $false
$newResourcesInstalled = $false
$localChanged = $false
$penChanged = $false
$penPath = 'HKCU:\Software\Microsoft\Wisp\Pen\SysEventParameters'
$oldHold = $null
$oldHoldPresent = $false
[ordered]@{ previousResources = if (Test-Path -LiteralPath $targetResources -PathType Container) { $previous } else { $null } } |
    ConvertTo-Json | Set-Content -LiteralPath (Join-Path $rollback 'resources.json') -Encoding UTF8

try {
    Copy-Item -LiteralPath $sourceResources -Destination $stage -Recurse -Force
    if (Test-Path -LiteralPath $targetResources -PathType Container) {
        [System.IO.Directory]::Move($targetResources, $previous)
        $previousMoved = $true
    }
    [System.IO.Directory]::Move($stage, $targetResources)
    $newResourcesInstalled = $true
    $localChanged = $true
    foreach ($name in $localNames) {
        $source = Join-Path (Join-Path $snapshot 'krita\local') $name
        $target = Join-Path $LocalDataPath $name
        if (Test-Path -LiteralPath $source -PathType Leaf) {
            Copy-Item -LiteralPath $source -Destination $target -Force
        } elseif (Test-Path -LiteralPath $target -PathType Leaf) {
            Remove-Item -LiteralPath $target -Force
        }
    }
    if ($RestoreWindowsPen -and $null -ne $metadata.windowsPenHoldMode) {
        $key = [Microsoft.Win32.Registry]::CurrentUser.OpenSubKey('Software\Microsoft\Wisp\Pen\SysEventParameters')
        if ($null -ne $key) {
            try {
                $oldHoldPresent = @($key.GetValueNames()) -contains 'HoldMode'
                $oldHold = $key.GetValue('HoldMode', $null)
            } finally {
                $key.Dispose()
            }
        }
        [ordered]@{ present = $oldHoldPresent; value = $oldHold } | ConvertTo-Json |
            Set-Content -LiteralPath (Join-Path $rollback 'windows-pen.json') -Encoding UTF8
        if (-not (Test-Path -LiteralPath $penPath)) {
            New-Item -Path $penPath -Force | Out-Null
        }
        $penChanged = $true
        New-ItemProperty -Path $penPath -Name HoldMode -Value ([int]$metadata.windowsPenHoldMode) -PropertyType DWord -Force | Out-Null
    }
} catch {
    $failure = $_
    if ($penChanged) {
        if ($oldHoldPresent) {
            New-ItemProperty -Path $penPath -Name HoldMode -Value ([int]$oldHold) -PropertyType DWord -Force | Out-Null
        } else {
            Remove-ItemProperty -Path $penPath -Name HoldMode -ErrorAction SilentlyContinue
        }
    }
    if ($localChanged) {
        foreach ($name in $localNames) {
            $target = Join-Path $LocalDataPath $name
            if ($priorPresence[$name]) {
                Copy-Item -LiteralPath (Join-Path $rollbackLocal $name) -Destination $target -Force
            } elseif (Test-Path -LiteralPath $target -PathType Leaf) {
                Remove-Item -LiteralPath $target -Force
            }
        }
    }
    if ($newResourcesInstalled -and (Test-Path -LiteralPath $targetResources -PathType Container)) {
        Remove-Item -LiteralPath $targetResources -Recurse -Force
    }
    if ($previousMoved -and (Test-Path -LiteralPath $previous -PathType Container)) {
        [System.IO.Directory]::Move($previous, $targetResources)
    }
    throw $failure
} finally {
    if (Test-Path -LiteralPath $stage -PathType Container) {
        Remove-Item -LiteralPath $stage -Recurse -Force
    }
}

Write-Host 'Krita settings and resources restored.'
Write-Host "Local configuration rollback: $rollback"
if ($previousMoved) { Write-Host "Previous resources retained at: $previous" }
Write-Host "Restore Wacom separately from: $(Join-Path $snapshot 'wacom\Wacom.wacomprefs')"
