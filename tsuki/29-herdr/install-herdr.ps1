#requires -Version 5.1

<#!
.SYNOPSIS
Install Herdr into one explicit, user-owned directory.

.DESCRIPTION
The official Herdr installer is downloaded to a temporary directory and run
with HERDR_HOME and -InstallDir contained below InstallRoot. Only the current
user's PATH is changed; machine-wide locations are not used.

.EXAMPLE
.\install-herdr.ps1

.EXAMPLE
.\install-herdr.ps1 -InstallRoot 'C:\Tools\Herdr' -Channel stable

.EXAMPLE
.\install-herdr.ps1 -Uninstall

.EXAMPLE
.\install-herdr.ps1 -Uninstall -Force
#>

[CmdletBinding(SupportsShouldProcess = $true, ConfirmImpact = 'High')]
param(
    [ValidateSet('stable', 'preview')]
    [string]$Channel = 'stable',

    [string]$InstallRoot,

    [ValidateRange(1, 10)]
    [int]$Retain = 3,

    [switch]$Uninstall,

    [switch]$Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

$InstallerUrl = 'https://herdr.dev/install.ps1'
$MarkerName = '.herdr-wrapper.json'
$MarkerManagedBy = 'install-herdr.ps1'

function Normalize-Path {
    param([Parameter(Mandatory)][string]$Path)

    $fullPath = [System.IO.Path]::GetFullPath($Path)
    $pathRoot = [System.IO.Path]::GetPathRoot($fullPath)
    if ($fullPath.Equals($pathRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
        return $pathRoot
    }

    return $fullPath.TrimEnd('\')
}

function Test-PathUnderRoot {
    param(
        [Parameter(Mandatory)][string]$Path,
        [Parameter(Mandatory)][string]$Root
    )

    $normalizedPath = Normalize-Path $Path
    $normalizedRoot = Normalize-Path $Root
    $rootPrefix = if ($normalizedRoot.EndsWith('\')) {
        $normalizedRoot
    } else {
        "$normalizedRoot\"
    }

    return $normalizedPath.Equals($normalizedRoot, [System.StringComparison]::OrdinalIgnoreCase) -or
        $normalizedPath.StartsWith($rootPrefix, [System.StringComparison]::OrdinalIgnoreCase)
}

function Assert-RegularDirectory {
    param([Parameter(Mandatory)][string]$Path)

    if (-not (Test-Path -LiteralPath $Path -PathType Container)) {
        throw "Expected a directory: $Path"
    }

    $item = Get-Item -LiteralPath $Path -Force
    if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
        throw "Refusing to use a reparse-point directory as the installation root: $Path"
    }
}

function Read-Marker {
    param(
        [Parameter(Mandatory)][string]$Root,
        [switch]$Require
    )

    $markerPath = Join-Path $Root $MarkerName
    if (-not (Test-Path -LiteralPath $markerPath -PathType Leaf)) {
        if ($Require) {
            throw "Refusing to manage an unmarked directory: $Root"
        }
        return $null
    }

    try {
        $marker = Get-Content -LiteralPath $markerPath -Raw | ConvertFrom-Json
    } catch {
        throw "The Herdr wrapper marker is invalid: $markerPath"
    }

    $markerItem = Get-Item -LiteralPath $markerPath -Force
    if (($markerItem.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0 -or
        $markerItem.PSIsContainer) {
        throw "Refusing to use an unexpected marker path: $markerPath"
    }

    if ([int]$marker.schema -ne 1 -or [string]$marker.managedBy -ne $MarkerManagedBy) {
        throw "The directory is not managed by this installer: $Root"
    }

    if (-not ([string]$marker.installRoot).Equals(
            (Normalize-Path $Root),
            [System.StringComparison]::OrdinalIgnoreCase
        )) {
        throw "The Herdr wrapper marker points at a different installation root: $markerPath"
    }

    return $marker
}

function New-Marker {
    param(
        [Parameter(Mandatory)][string]$Root,
        [Parameter(Mandatory)][string]$HerdrHome,
        [Parameter(Mandatory)][string]$VisibleBin,
        [Parameter(Mandatory)][string]$ReleasesDir,
        [Parameter(Mandatory)][string]$CurrentDir
    )

    $marker = [ordered]@{
        schema      = 1
        managedBy   = $MarkerManagedBy
        installRoot = Normalize-Path $Root
        herdrHome   = Normalize-Path $HerdrHome
        visibleBin  = Normalize-Path $VisibleBin
        releasesDir = Normalize-Path $ReleasesDir
        currentDir  = Normalize-Path $CurrentDir
    }

    $markerPath = Join-Path $Root $MarkerName
    if (Test-Path -LiteralPath $markerPath) {
        $existingMarker = Get-Item -LiteralPath $markerPath -Force
        if (($existingMarker.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0 -or
            $existingMarker.PSIsContainer) {
            throw "Refusing to overwrite an unexpected marker path: $markerPath"
        }
    }

    $marker | ConvertTo-Json | Set-Content -LiteralPath $markerPath -Encoding UTF8
}

function Get-InstallationLayout {
    param([Parameter(Mandatory)][string]$Root)

    $herdrHome = Join-Path $Root 'data'
    $standaloneRoot = Join-Path $herdrHome 'packages\standalone'

    return [PSCustomObject]@{
        Root        = Normalize-Path $Root
        HerdrHome   = Normalize-Path $herdrHome
        VisibleBin  = Normalize-Path (Join-Path $Root 'bin')
        ReleasesDir = Normalize-Path (Join-Path $standaloneRoot 'releases')
        CurrentDir  = Normalize-Path (Join-Path $standaloneRoot 'current')
        MarkerPath  = Normalize-Path (Join-Path $Root $MarkerName)
    }
}

function Get-CurlPath {
    $curl = Get-Command curl.exe -CommandType Application -ErrorAction SilentlyContinue |
        Select-Object -First 1
    if ($null -eq $curl) {
        throw 'curl.exe is required. It is included with supported Windows versions.'
    }

    return $curl.Source
}

function Download-Installer {
    param(
        [Parameter(Mandatory)][string]$Destination,
        [Parameter(Mandatory)][string]$CurlPath
    )

    $arguments = @(
        '--fail',
        '--silent',
        '--show-error',
        '--location',
        '--connect-timeout', '30',
        '--speed-limit', '1024',
        '--speed-time', '30',
        '--proto', '=https',
        '--tlsv1.2',
        '--output', $Destination,
        '--', $InstallerUrl
    )

    $output = & $CurlPath @arguments 2>&1
    if ($LASTEXITCODE -ne 0) {
        $detail = ($output | ForEach-Object { $_.ToString() }) -join [Environment]::NewLine
        throw "Failed to download $InstallerUrl (curl exit code $LASTEXITCODE). $detail"
    }
}

function Publish-EnvironmentChange {
    if (-not ('HerdrWrapper.EnvironmentNativeMethods' -as [type])) {
        Add-Type -Namespace HerdrWrapper -Name EnvironmentNativeMethods -MemberDefinition @'
[System.Runtime.InteropServices.DllImport("user32.dll", SetLastError = true, CharSet = System.Runtime.InteropServices.CharSet.Unicode)]
public static extern System.IntPtr SendMessageTimeout(
    System.IntPtr hWnd,
    uint message,
    System.UIntPtr wParam,
    string lParam,
    uint flags,
    uint timeout,
    out System.UIntPtr result);
'@
    }

    $result = [UIntPtr]::Zero
    [HerdrWrapper.EnvironmentNativeMethods]::SendMessageTimeout(
        [IntPtr]0xffff,
        0x1a,
        [UIntPtr]::Zero,
        'Environment',
        0x0002,
        1000,
        [ref]$result
    ) | Out-Null
}

function Normalize-PathEntry {
    param([AllowNull()][string]$Value)

    if ([string]::IsNullOrWhiteSpace($Value)) {
        return ''
    }

    $expanded = [Environment]::ExpandEnvironmentVariables($Value.Trim().Trim('"'))
    try {
        return (Normalize-Path $expanded)
    } catch {
        return $expanded.TrimEnd('\')
    }
}

function Remove-ManagedPathEntries {
    param(
        [Parameter(Mandatory)][string[]]$ExactEntries,
        [Parameter(Mandatory)][string]$ReleaseParent
    )

    $environmentKey = [Microsoft.Win32.Registry]::CurrentUser.OpenSubKey('Environment', $true)
    if ($null -eq $environmentKey) {
        return $false
    }

    $changed = $false
    try {
        $options = [Microsoft.Win32.RegistryValueOptions]::DoNotExpandEnvironmentNames
        $pathValue = $environmentKey.GetValue('Path', $null, $options)
        if ($null -eq $pathValue) {
            return $false
        }

        $pathKind = $environmentKey.GetValueKind('Path')
        $exact = @($ExactEntries | ForEach-Object { Normalize-PathEntry $_ })
        $releaseParentNormalized = Normalize-PathEntry $ReleaseParent
        $remaining = @(
            ([string]$pathValue).Split(';', [System.StringSplitOptions]::RemoveEmptyEntries) |
                Where-Object {
                    $normalized = Normalize-PathEntry $_
                    $parent = ''
                    try {
                        $parent = Normalize-PathEntry ([System.IO.Path]::GetDirectoryName($normalized))
                    } catch {
                        $parent = ''
                    }

                    $normalized -notin $exact -and $parent -ine $releaseParentNormalized
                }
        )
        $newPathValue = $remaining -join ';'
        if ($newPathValue -cne [string]$pathValue) {
            $environmentKey.SetValue('Path', $newPathValue, $pathKind)
            $changed = $true
        }
    } finally {
        $environmentKey.Dispose()
    }

    if ($changed) {
        Publish-EnvironmentChange
    }

    return $changed
}

function Remove-ManagedItem {
    param([Parameter(Mandatory)][string]$Path)

    if (-not (Test-Path -LiteralPath $Path)) {
        return
    }

    $item = Get-Item -LiteralPath $Path -Force
    if (($item.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
        if ($item.LinkType -ne 'Junction') {
            throw "Refusing to remove an unexpected reparse point: $Path"
        }

        [System.IO.Directory]::Delete($Path, $false)
        return
    }

    if ($item.PSIsContainer) {
        Remove-Item -LiteralPath $Path -Recurse -Force
    } else {
        Remove-Item -LiteralPath $Path -Force
    }
}

function Install-Herdr {
    param([Parameter(Mandatory)][PSCustomObject]$Layout)

    if (Test-Path -LiteralPath $Layout.Root) {
        Assert-RegularDirectory $Layout.Root
        if (Test-Path -LiteralPath (Join-Path $Layout.Root $MarkerName)) {
            $null = Read-Marker -Root $Layout.Root -Require
        } elseif ((@(Get-ChildItem -LiteralPath $Layout.Root -Force)).Count -ne 0) {
            throw "Refusing to manage a non-empty, unmarked directory: $($Layout.Root)"
        }
    } else {
        New-Item -ItemType Directory -Path $Layout.Root -Force | Out-Null
    }

    New-Marker `
        -Root $Layout.Root `
        -HerdrHome $Layout.HerdrHome `
        -VisibleBin $Layout.VisibleBin `
        -ReleasesDir $Layout.ReleasesDir `
        -CurrentDir $Layout.CurrentDir

    $tempDir = Join-Path ([System.IO.Path]::GetTempPath()) (
        'herdr-wrapper-' + [Guid]::NewGuid().ToString('N')
    )
    $installerPath = Join-Path $tempDir 'install.ps1'
    New-Item -ItemType Directory -Path $tempDir -Force | Out-Null

    try {
        $curlPath = Get-CurlPath
        Write-Host "Downloading Herdr installer from $InstallerUrl"
        Download-Installer -Destination $installerPath -CurlPath $curlPath

        $powershell = Get-Command powershell.exe -CommandType Application -ErrorAction SilentlyContinue |
            Select-Object -First 1
        if ($null -eq $powershell) {
            throw 'powershell.exe is required to run the official Herdr installer.'
        }

        $oldHerdrHome = [Environment]::GetEnvironmentVariable('HERDR_HOME', 'Process')
        try {
            $env:HERDR_HOME = $Layout.HerdrHome
            $childArguments = @(
                '-NoLogo',
                '-NoProfile',
                '-NonInteractive',
                '-ExecutionPolicy', 'Bypass',
                '-File', $installerPath,
                '-Channel', $Channel,
                '-InstallDir', $Layout.VisibleBin,
                '-Retain', [string]$Retain
            )

            Write-Host "Installing into $($Layout.Root)"
            & $powershell.Source @childArguments
            $exitCode = $LASTEXITCODE
            if ($exitCode -ne 0) {
                throw "The official Herdr installer failed with exit code $exitCode."
            }
        } finally {
            [Environment]::SetEnvironmentVariable('HERDR_HOME', $oldHerdrHome, 'Process')
        }

        $installedExecutable = Join-Path $Layout.CurrentDir 'herdr.exe'
        if (-not (Test-Path -LiteralPath $installedExecutable -PathType Leaf)) {
            throw "The installer completed but did not produce $installedExecutable"
        }

        & $installedExecutable '--version'
        if ($LASTEXITCODE -ne 0) {
            throw "Installed Herdr failed its version check: $installedExecutable"
        }

        Write-Host ''
        Write-Host 'Herdr installed successfully.'
        Write-Host "  Managed root: $($Layout.Root)"
        Write-Host "  Binary:       $installedExecutable"
        Write-Host "  Command bin:  $($Layout.VisibleBin)"
        Write-Host '  Open a new PowerShell window before running: herdr'
    } finally {
        if (Test-Path -LiteralPath $tempDir) {
            Remove-Item -LiteralPath $tempDir -Recurse -Force -ErrorAction SilentlyContinue
        }
    }
}

function Uninstall-Herdr {
    param([Parameter(Mandatory)][PSCustomObject]$Layout)

    if (-not (Test-Path -LiteralPath $Layout.Root)) {
        Write-Host "Nothing to uninstall: $($Layout.Root)"
        return
    }

    Assert-RegularDirectory $Layout.Root
    $null = Read-Marker -Root $Layout.Root -Require

    if (-not $Force -and -not $PSCmdlet.ShouldProcess(
            $Layout.Root,
            'remove the Herdr-managed files and user PATH entries'
        )) {
        return
    }

    Remove-ManagedPathEntries `
        -ExactEntries @($Layout.VisibleBin, $Layout.CurrentDir) `
        -ReleaseParent $Layout.ReleasesDir | Out-Null

    Remove-ManagedItem -Path $Layout.VisibleBin
    Remove-ManagedItem -Path $Layout.CurrentDir
    Remove-ManagedItem -Path $Layout.HerdrHome
    Remove-ManagedItem -Path $Layout.MarkerPath

    if (Test-Path -LiteralPath $Layout.Root) {
        $remaining = @(Get-ChildItem -LiteralPath $Layout.Root -Force)
        if ($remaining.Count -eq 0) {
            Remove-Item -LiteralPath $Layout.Root -Force
        } else {
            $names = ($remaining | ForEach-Object { $_.Name }) -join ', '
            Write-Warning "Kept $($Layout.Root) because it contains unmanaged entries: $names"
        }
    }

    Write-Host 'Herdr uninstalled from the managed root.'
    Write-Host 'Open a new PowerShell window to receive the updated user PATH.'
}

if ($env:OS -ne 'Windows_NT') {
    throw 'This script supports Windows only.'
}

if ([string]::IsNullOrWhiteSpace($InstallRoot)) {
    if ([string]::IsNullOrWhiteSpace($env:LOCALAPPDATA)) {
        throw 'LOCALAPPDATA is not set; pass -InstallRoot explicitly.'
    }

    $InstallRoot = Join-Path $env:LOCALAPPDATA 'Herdr-managed'
}

$layout = Get-InstallationLayout -Root $InstallRoot
$filesystemRoot = Normalize-Path ([System.IO.Path]::GetPathRoot($layout.Root))
if ($layout.Root.Equals($filesystemRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw 'Refusing to use a filesystem root as the installation root.'
}

if (-not (Test-PathUnderRoot -Path $layout.HerdrHome -Root $layout.Root) -or
    -not (Test-PathUnderRoot -Path $layout.VisibleBin -Root $layout.Root)) {
    throw 'The computed Herdr paths are outside the installation root.'
}

if ($Uninstall) {
    Uninstall-Herdr -Layout $layout
} else {
    Install-Herdr -Layout $layout
}
