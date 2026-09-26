<#
.SYNOPSIS
Install the audited Windows x64 Vulkan bundle without downloading models.
.EXAMPLE
.\install-live-subtitle.ps1 -InstallDirectory 'D:\software\live-subtitle'
.EXAMPLE
.\install-live-subtitle.ps1 -InstallDirectory 'E:\LiveSubtitle' -CacheDirectory 'E:\downloads' -Offline
#>
[CmdletBinding()]
param(
    [string]$InstallDirectory = (Join-Path $PSScriptRoot 'LiveSubtitle'),
    [string]$CacheDirectory,
    [string]$GpuName = 'AMD Radeon RX 9070 XT',
    [switch]$Offline,
    [switch]$Plan
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$manifest = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'assets.json') -Raw | ConvertFrom-Json
$target = [IO.Path]::GetFullPath($InstallDirectory).TrimEnd('\')
$stage = $null
$oldTemp = $env:TEMP
$oldTmp = $env:TMP

function Assert-Digest([string]$Path, [string]$Expected) {
    if ((Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash -ne $Expected) {
        throw "SHA256 mismatch: $Path. Do not bypass this check; re-audit changed upstream files."
    }
}

function Assert-Signer([string]$Path, [string]$Publisher) {
    $signature = Get-AuthenticodeSignature -LiteralPath $Path
    if ($signature.Status -ne 'Valid' -or $signature.SignerCertificate.Subject -notmatch $Publisher) {
        throw "Authenticode verification failed: $Path ($($signature.Status))"
    }
}

function Get-Asset($Asset, [string]$Destination) {
    $local = if ($CacheDirectory) { Join-Path $CacheDirectory $Asset.file } else { $null }
    if ($local -and (Test-Path -LiteralPath $local -PathType Leaf)) {
        Assert-Digest $local $Asset.sha256
        Copy-Item -LiteralPath $local -Destination $Destination
    } else {
        if ($Offline) { throw "Offline cache missing: $($Asset.file)" }
        Write-Host "Downloading $($Asset.id) $($Asset.version) from $($Asset.url)"
        $partial = $Destination + '.partial'
        & curl.exe --fail --location --proto '=https' --proto-redir '=https' --retry 3 --connect-timeout 20 --max-time 600 --output $partial $Asset.url
        if ($LASTEXITCODE -ne 0) { throw "Download failed: $($Asset.file)" }
        Assert-Digest $partial $Asset.sha256
        Move-Item -LiteralPath $partial -Destination $Destination
    }
    Assert-Digest $Destination $Asset.sha256
}

function Remove-Stage([string]$Path) {
    $resolved = [IO.Path]::GetFullPath($Path)
    $parent = Split-Path -Parent $target
    if ((Split-Path -Parent $resolved) -ne $parent -or (Split-Path -Leaf $resolved) -notmatch '^\.live-subtitle-install-[a-f0-9]{32}$') {
        throw "Refusing cleanup outside the installation staging directory: $resolved"
    }
    if (Test-Path -LiteralPath $resolved) { Remove-Item -LiteralPath $resolved -Recurse -Force }
}

try {
    if (-not [Environment]::Is64BitOperatingSystem -or -not [Environment]::Is64BitProcess) {
        throw 'Use 64-bit Windows PowerShell on Windows 10/11 x64.'
    }
    if ([Environment]::OSVersion.Version.Major -lt 10) { throw 'Windows 10 or later is required.' }
    if ($env:PROCESSOR_ARCHITECTURE -ne 'AMD64') { throw 'The audited bundle requires an x64 processor.' }
    if ($target -eq [IO.Path]::GetPathRoot($target).TrimEnd('\') -or $target -match '[\x00-\x1f%!]') {
        throw 'Choose a directory below a drive root without control characters, % or !.'
    }
    if ($target.StartsWith('\\')) { throw 'Install to a local drive, then copy the complete folder between PCs.' }
    foreach ($protected in @($env:SystemRoot, $env:ProgramFiles, ${env:ProgramFiles(x86)}, $env:APPDATA, $env:LOCALAPPDATA)) {
        if ($protected -and ($target -eq $protected -or $target.StartsWith($protected.TrimEnd('\') + '\', [StringComparison]::OrdinalIgnoreCase))) {
            throw "Choose a portable directory outside $protected"
        }
    }
    $ancestor = $target
    while ($ancestor) {
        if ((Test-Path -LiteralPath $ancestor) -and ((Get-Item -LiteralPath $ancestor).Attributes -band [IO.FileAttributes]::ReparsePoint)) {
            throw "Installation paths through junctions/symlinks are unsupported: $ancestor"
        }
        $ancestor = Split-Path -Parent $ancestor
    }
    if ($CacheDirectory) { $CacheDirectory = [IO.Path]::GetFullPath($CacheDirectory) }
    Write-Host "Live Subtitle portable installer $($manifest.package_version) | Vulkan"
    Write-Host "Destination: $target"
    Write-Host "GPU name: $GpuName"
    Write-Host 'Models: manual placement only; this installer contains no model downloader.'
    if ($Plan) {
        $manifest.software | Select-Object id, version, file, url | Format-Table -Wrap
        Write-Host 'Plan only: no downloads or installation.'
        exit 0
    }
    if (Test-Path -LiteralPath $target) {
        if (-not (Test-Path -LiteralPath $target -PathType Container)) { throw 'Destination is not a directory.' }
        if ((Get-Item -LiteralPath $target).Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'Destination must not be a junction or symlink.' }
        $markerPath = Join-Path $target '.live-subtitle-portable.json'
        if (Test-Path -LiteralPath $markerPath) {
            $marker = Get-Content -LiteralPath $markerPath -Raw | ConvertFrom-Json
            if ($marker.package_version -ne $manifest.package_version) { throw 'Another installer version owns this directory. Install the new version into a new directory.' }
            & (Join-Path $PSScriptRoot 'verify-install.ps1') -InstallDirectory $target -FilesOnly
            if (-not $?) { throw 'Existing installation failed verification.' }
            Write-Host 'Existing managed installation verified; settings and models preserved. No downloads.'
            exit 0
        }
        if (@(Get-ChildItem -LiteralPath $target -Force).Count -gt 0) { throw 'Destination is not empty or managed by this installer. Choose a new directory.' }
    }
    if ($Offline -and -not $CacheDirectory) { throw '-Offline requires -CacheDirectory.' }
    if (-not $Offline) { [void](Get-Command curl.exe -ErrorAction Stop) }
    $parent = Split-Path -Parent $target
    [void](New-Item -ItemType Directory -Path $parent -Force)
    $stage = Join-Path $parent ('.live-subtitle-install-' + [guid]::NewGuid().ToString('N'))
    [void](New-Item -ItemType Directory -Path $stage)
    foreach ($directory in @('app\upstream', 'CrispASR', 'models', 'config', 'cache\downloads', 'logs', 'temp')) {
        [void](New-Item -ItemType Directory -Path (Join-Path $stage $directory) -Force)
    }
    $env:TEMP = Join-Path $stage 'temp'
    $env:TMP = $env:TEMP
    foreach ($asset in $manifest.software) {
        Get-Asset $asset (Join-Path $stage ('cache\downloads\' + $asset.file))
    }
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'payload\app') -Destination $stage -Recurse -Force
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'payload\start.bat') -Destination $stage
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'payload\start-debug.bat') -Destination $stage
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'assets.json') -Destination (Join-Path $stage 'config\assets.json')
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'INSTALL.md') -Destination $stage
    $settings = Get-Content -LiteralPath (Join-Path $PSScriptRoot 'payload\config\settings.json') -Raw | ConvertFrom-Json
    $settings.gpu_name = $GpuName
    $settings | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $stage 'config\settings.json') -Encoding UTF8
    Copy-Item -LiteralPath (Join-Path $stage 'cache\downloads\live_subtitle.exe') -Destination $stage
    Expand-Archive -LiteralPath (Join-Path $stage 'cache\downloads\crispasr-windows-x86_64-vulkan.zip') -DestinationPath (Join-Path $stage 'temp\crispasr')
    $crispFolder = Join-Path $stage 'temp\crispasr\crispasr-windows-x86_64-vulkan'
    if (-not (Test-Path -LiteralPath (Join-Path $crispFolder 'crispasr.exe'))) { throw 'Unexpected CrispASR archive layout; re-audit the release.' }
    Get-ChildItem -LiteralPath $crispFolder | Copy-Item -Destination (Join-Path $stage 'CrispASR') -Recurse
    $buildPython = Join-Path $stage 'temp\build-python'
    Expand-Archive -LiteralPath (Join-Path $stage 'cache\downloads\python-3.11.9-embed-amd64.zip') -DestinationPath $buildPython
    $python = Join-Path $buildPython 'python.exe'
    Assert-Signer $python 'Python Software Foundation'
    $redist = Join-Path $stage 'cache\downloads\vc_redist.x64.exe'
    Assert-Signer $redist 'Microsoft Corporation'
    & $python -I -B (Join-Path $PSScriptRoot 'tools\extract-msvc.py') $redist (Join-Path $stage 'temp\msvc') (Join-Path $stage 'CrispASR')
    if ($LASTEXITCODE -ne 0) { throw 'App-local Microsoft runtime extraction failed; no installer was executed.' }
    foreach ($dll in Get-ChildItem -LiteralPath (Join-Path $stage 'CrispASR') -Filter '*140*.dll') { Assert-Signer $dll.FullName 'Microsoft Corporation' }
    & $python -I -B (Join-Path $stage 'app\build-portable.py') $stage
    if ($LASTEXITCODE -ne 0) { throw 'Portable executable adaptation failed.' }
    Copy-Item -LiteralPath (Join-Path $PSScriptRoot 'verify-install.ps1') -Destination (Join-Path $stage 'app\verify-install.ps1')
    $files = @()
    foreach ($folder in @('app', 'CrispASR')) {
        foreach ($file in Get-ChildItem -LiteralPath (Join-Path $stage $folder) -File -Recurse) {
            $files += @{ file = $file.FullName.Substring($stage.Length + 1); sha256 = (Get-FileHash -LiteralPath $file.FullName -Algorithm SHA256).Hash }
        }
    }
    foreach ($name in @('LiveSubtitle.exe','live_subtitle.exe','start.bat','start-debug.bat','config\assets.json')) {
        $files += @{ file = $name; sha256 = (Get-FileHash -LiteralPath (Join-Path $stage $name) -Algorithm SHA256).Hash }
    }
    @{package_version = $manifest.package_version; files = $files} | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath (Join-Path $stage '.live-subtitle-portable.json') -Encoding UTF8
    & (Join-Path $PSScriptRoot 'verify-install.ps1') -InstallDirectory $stage
    if (-not $?) { throw 'Installation verification failed.' }
    $tempRoot = [IO.Path]::GetFullPath((Join-Path $stage 'temp'))
    if (-not $tempRoot.StartsWith($stage + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Invalid staging temp path.' }
    Get-ChildItem -LiteralPath $tempRoot -Force | Remove-Item -Recurse -Force
    if (Test-Path -LiteralPath $target) {
        if (@(Get-ChildItem -LiteralPath $target -Force).Count -gt 0) { throw 'Destination changed during installation; refusing to overwrite it.' }
        Remove-Item -LiteralPath $target
    }
    Move-Item -LiteralPath $stage -Destination $target
    $stage = $null
    Write-Host "Installed: $target"
    Write-Host 'Place the two named GGUF files in models, run app\verify-install.ps1 -CheckModels, then start.bat.'
} catch {
    Write-Error $_ -ErrorAction Continue
    exit 1
} finally {
    $env:TEMP = $oldTemp
    $env:TMP = $oldTmp
    if ($stage) { Remove-Stage $stage }
}
