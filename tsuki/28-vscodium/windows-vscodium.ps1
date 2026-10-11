#requires -Version 5.1
<#
.SYNOPSIS
Manage VSCodium installation, settings and extensions on Windows.
.EXAMPLE
.\windows-vscodium.ps1 install -Archive C:\Downloads\VSCodium-win32-x64.zip
.EXAMPLE
.\windows-vscodium.ps1 upgrade
.EXAMPLE
.\windows-vscodium.ps1 sync setting
.EXAMPLE
.\windows-vscodium.ps1 sync extension -Export
.EXAMPLE
.\windows-vscodium.ps1 update extension -Check
#>
[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [Parameter(Position = 0)]
    [ValidateSet('install', 'upgrade', 'remove', 'sync', 'update', 'help')]
    [string]$Action = 'help',
    [Parameter(Position = 1)]
    [ValidateSet('setting', 'extension')]
    [string]$Target,
    [string]$Archive,
    [string]$Path = (Join-Path $env:APPDATA 'Apps\VSCodium'),
    [switch]$Force,
    [string]$CodiumBin = $env:CODIUM_BIN,
    [string]$ExtensionFile,
    [string]$ExtensionsDir,
    [string]$UserDir,
    [switch]$Export,
    [switch]$Check
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Find-Codium {
    param([string]$RequestedPath)

    if ($RequestedPath) {
        return (Get-Command -Name $RequestedPath -CommandType Application -ErrorAction Stop).Source
    }
    $command = Get-Command -Name 'codium.cmd', 'codium' -CommandType Application -ErrorAction SilentlyContinue |
        Select-Object -First 1
    if ($command) { return $command.Source }
    $candidates = @(
        (Join-Path $env:APPDATA 'Apps\VSCodium\bin\codium.cmd'),
        (Join-Path $env:LOCALAPPDATA 'Programs\VSCodium\bin\codium.cmd'),
        (Join-Path $env:ProgramFiles 'VSCodium\bin\codium.cmd')
    )
    if (${env:ProgramFiles(x86)}) {
        $candidates += Join-Path ${env:ProgramFiles(x86)} 'VSCodium\bin\codium.cmd'
    }
    foreach ($candidate in $candidates) {
        if (Test-Path -LiteralPath $candidate -PathType Leaf) { return $candidate }
    }
    throw 'VSCodium CLI was not found. Specify -CodiumBin with the path to bin\codium.cmd.'
}

function Get-CodiumDirectories {
    param([string]$Codium)

    $installDir = Split-Path -Parent (Split-Path -Parent $Codium)
    $portableData = Join-Path $installDir 'data'
    if (Test-Path -LiteralPath $portableData -PathType Container) {
        return [pscustomobject]@{
            User = Join-Path $portableData 'user-data\User'
            Extensions = Join-Path $portableData 'extensions'
        }
    }
    $extensions = if ($env:VSCODE_EXTENSIONS) { $env:VSCODE_EXTENSIONS }
        else { Join-Path $env:USERPROFILE '.vscode-oss\extensions' }
    return [pscustomobject]@{
        User = Join-Path $env:APPDATA 'VSCodium\User'
        Extensions = $extensions
    }
}

function Read-ExtensionIds {
    param([string]$Path)

    $ids = @(Get-Content -LiteralPath $Path | ForEach-Object {
        ($_ -split '#', 2)[0].Trim()
    } | Where-Object { $_ } | Sort-Object -Unique)
    if ($ids.Count -eq 0) { throw "Extension list is empty: $Path" }
    foreach ($id in $ids) {
        if ($id -notmatch '^[A-Za-z0-9][A-Za-z0-9_-]*\.[A-Za-z0-9][A-Za-z0-9_.-]*$') {
            throw "Invalid extension ID: $id"
        }
    }
    return $ids
}

function Invoke-Codium {
    param([string]$Command, [string[]]$Arguments)

    # Windows PowerShell turns redirected native stderr into ErrorRecord objects.
    $ErrorActionPreference = 'Continue'
    $PSNativeCommandUseErrorActionPreference = $false
    $lines = @(& $Command @Arguments 2>&1)
    return [pscustomobject]@{ Lines = $lines; ExitCode = $LASTEXITCODE }
}

function Test-NewerVersion {
    param([string]$RemoteVersion, [string]$InstalledVersion)

    $pattern = '^(\d+)\.(\d+)\.(\d+)(?:-([0-9A-Za-z.-]+))?(?:\+[0-9A-Za-z.-]+)?$'
    $remote = [regex]::Match($RemoteVersion, $pattern)
    if (-not $remote.Success) { throw "Invalid remote version: $RemoteVersion" }
    if (-not $InstalledVersion) { return $true }
    $local = [regex]::Match($InstalledVersion, $pattern)
    if (-not $local.Success) { throw "Invalid installed version: $InstalledVersion" }
    for ($i = 1; $i -le 3; $i++) {
        $comparison = ([long]$remote.Groups[$i].Value).CompareTo([long]$local.Groups[$i].Value)
        if ($comparison -ne 0) { return $comparison -gt 0 }
    }
    $remotePre = $remote.Groups[4].Value
    $localPre = $local.Groups[4].Value
    if (-not $remotePre) { return [bool]$localPre }
    if (-not $localPre) { return $false }
    $remoteParts = $remotePre.Split('.')
    $localParts = $localPre.Split('.')
    for ($i = 0; $i -lt [Math]::Min($remoteParts.Count, $localParts.Count); $i++) {
        $remoteNumeric = $remoteParts[$i] -match '^\d+$'
        $localNumeric = $localParts[$i] -match '^\d+$'
        if ($remoteNumeric -and $localNumeric) {
            $comparison = ([long]$remoteParts[$i]).CompareTo([long]$localParts[$i])
        }
        elseif ($remoteNumeric -ne $localNumeric) {
            return $localNumeric
        }
        else {
            $comparison = [string]::CompareOrdinal($remoteParts[$i], $localParts[$i])
        }
        if ($comparison -ne 0) { return $comparison -gt 0 }
    }
    return $remoteParts.Count -gt $localParts.Count
}

function Get-InstalledVersions {
    if (-not (Test-Path -LiteralPath $ExtensionsDir)) { return @{} }
    $result = Invoke-Codium -Command $codium -Arguments @('--extensions-dir', $ExtensionsDir, '--list-extensions', '--show-versions')
    if ($result.ExitCode -ne 0) { throw 'Cannot read installed extension versions.' }
    $versions = @{}
    foreach ($line in $result.Lines) {
        if ($line -match '^([A-Za-z0-9_-]+\.[A-Za-z0-9_.-]+)@([^\s]+)$') {
            $versions[$Matches[1]] = $Matches[2]
        }
    }
    return $versions
}

function Get-ExtensionMetadata {
    param([string]$Url, [string]$Platform)

    try {
        return Invoke-RestMethod -Uri "$Url/$Platform/latest" -TimeoutSec 60
    }
    catch {
        # Only a missing platform package warrants falling back to universal.
        $response = $_.Exception.PSObject.Properties['Response']
        if (-not $response -or -not $response.Value -or [int]$response.Value.StatusCode -ne 404) { throw }
        return Invoke-RestMethod -Uri "$Url/universal/latest" -TimeoutSec 60
    }
}

function Test-Vsix {
    param([string]$Path, [string]$Id, [string]$Version, [string]$Platform)

    $archive = [System.IO.Compression.ZipFile]::OpenRead($Path)
    try {
        foreach ($entry in $archive.Entries) {
            if ($entry.FullName -match '(^[/\\]|(^|[/\\])\.\.([/\\]|$)|\\|:)') {
                throw "Unsafe VSIX path: $($entry.FullName)"
            }
            if ((($entry.ExternalAttributes -shr 16) -band 0xF000) -eq 0xA000) {
                throw "VSIX contains a symbolic link: $($entry.FullName)"
            }
        }
        $entries = @($archive.Entries | Where-Object { $_.FullName -ceq 'extension/package.json' })
        if ($entries.Count -ne 1) { throw 'VSIX must contain one extension/package.json.' }
        $reader = [System.IO.StreamReader]::new($entries[0].Open())
        try { $package = $reader.ReadToEnd() | ConvertFrom-Json }
        finally { $reader.Dispose() }
        if ("$($package.publisher).$($package.name)" -ine $Id -or $package.version -cne $Version) {
            throw "VSIX identity mismatch: expected $Id@$Version"
        }
        $manifestEntry = $archive.GetEntry('extension.vsixmanifest')
        if (-not $manifestEntry) { throw 'VSIX lacks extension.vsixmanifest.' }
        $reader = [System.IO.StreamReader]::new($manifestEntry.Open())
        try { [xml]$vsixManifest = $reader.ReadToEnd() }
        finally { $reader.Dispose() }
        $identity = $vsixManifest.SelectSingleNode('//*[local-name()="Identity"]')
        if (-not $identity) { throw 'VSIX lacks a manifest identity.' }
        $target = $identity.GetAttribute('TargetPlatform')
        if ($target -and $target -ne 'universal' -and $target -ne $Platform) {
            throw "VSIX targets $target instead of $Platform"
        }
    }
    finally { $archive.Dispose() }
}

function Get-ExtensionDirectories {
    param([string]$Id)

    return @(Get-ChildItem -LiteralPath $ExtensionsDir -Directory -Force | Where-Object {
        $_.Name.StartsWith("$Id-", [System.StringComparison]::OrdinalIgnoreCase)
    })
}

function Assert-SafeExtensionPath {
    param([System.IO.DirectoryInfo]$Directory)

    if ($Directory.Parent.FullName -ine $ExtensionsDir -or
        ($Directory.Attributes -band [System.IO.FileAttributes]::ReparsePoint)) {
        throw "Unsafe extension directory: $($Directory.FullName)"
    }
    $links = @(Get-ChildItem -LiteralPath $Directory.FullName -Recurse -Force -Attributes ReparsePoint)
    if ($links.Count -gt 0) { throw "Extension contains a reparse point: $($links[0].FullName)" }
}

function Install-Extension {
    param([string]$Id, [string]$Version, [string]$DownloadUrl, [string]$Platform)

    $uri = [uri]$DownloadUrl
    if ($uri.Scheme -ne 'https' -or $uri.Host -ne 'open-vsx.org' -or
        -not $uri.AbsolutePath.StartsWith('/api/')) {
        throw "Unsupported VSIX download URL for $Id"
    }
    $transactionDir = Join-Path $workDir ([guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $transactionDir | Out-Null
    $vsix = Join-Path $transactionDir 'package.vsix'
    Invoke-WebRequest -Uri $uri -OutFile $vsix -UseBasicParsing -TimeoutSec 300
    Test-Vsix -Path $vsix -Id $Id -Version $Version -Platform $Platform

    New-Item -ItemType Directory -Path $ExtensionsDir -Force | Out-Null
    $oldDirs = @(Get-ExtensionDirectories -Id $Id)
    $backupDir = Join-Path $transactionDir 'backup'
    New-Item -ItemType Directory -Path $backupDir | Out-Null
    foreach ($dir in $oldDirs) {
        Assert-SafeExtensionPath -Directory $dir
        Copy-Item -LiteralPath $dir.FullName -Destination $backupDir -Recurse -Force
    }
    $indexFiles = @('extensions.json', '.obsolete')
    foreach ($file in $indexFiles) {
        $path = Join-Path $ExtensionsDir $file
        if (Test-Path -LiteralPath $path) { Copy-Item -LiteralPath $path -Destination $backupDir }
    }
    $output = @()
    try {
        $result = Invoke-Codium -Command $codium -Arguments @('--extensions-dir', $ExtensionsDir, '--install-extension', $vsix, '--force')
        $output = $result.Lines
        $installExitCode = $result.ExitCode
        $output | ForEach-Object { Write-Host "$_" }
        if ($installExitCode -ne 0) { throw "Installation failed: $Id@$Version (exit $installExitCode)" }
        $installed = Get-InstalledVersions
        if ($installed[$Id] -cne $Version) { throw "Installed version could not be verified: $Id@$Version" }
    }
    catch {
        $failure = $_
        try {
            foreach ($dir in @(Get-ExtensionDirectories -Id $Id)) {
                Assert-SafeExtensionPath -Directory $dir
                Remove-Item -LiteralPath $dir.FullName -Recurse -Force
            }
            foreach ($dir in $oldDirs) {
                Copy-Item -LiteralPath (Join-Path $backupDir $dir.Name) -Destination $ExtensionsDir -Recurse -Force
            }
            foreach ($file in $indexFiles) {
                $path = Join-Path $ExtensionsDir $file
                $backup = Join-Path $backupDir $file
                if (Test-Path -LiteralPath $backup) { Copy-Item -LiteralPath $backup -Destination $path -Force }
                elseif (Test-Path -LiteralPath $path) { Remove-Item -LiteralPath $path -Force }
            }
        }
        catch {
            $script:preserveBackup = $true
            throw "Rollback failed for $Id; backup retained at $backupDir. $($_.Exception.Message)"
        }
        if (($output -join "`n") -match 'not compatible with (VSCodium|Visual Studio Code|VS Code)') {
            Write-Warning "Skipped $Id@${Version}: incompatible with this VSCodium; previous installation restored."
            return $false
        }
        throw $failure
    }
    Write-Host "Updated $Id to $Version"
    return $true
}

function Sync-Setting {
    try {
        if (-not $UserDir) {
            $codium = Find-Codium -RequestedPath $CodiumBin
            $UserDir = (Get-CodiumDirectories -Codium $codium).User
        }
        $files = @('settings.json', 'keybindings.json')
        foreach ($file in $files) {
            if (-not (Test-Path -LiteralPath (Join-Path $PSScriptRoot "config\$file") -PathType Leaf)) {
                throw "Configuration file was not found: $file"
            }
        }
        if ($PSCmdlet.ShouldProcess($UserDir, 'Back up existing settings and synchronize repository configuration')) {
            New-Item -ItemType Directory -Path $UserDir -Force | Out-Null
            $suffix = '.bak-' + (Get-Date -Format 'yyyyMMdd-HHmmss-fffffff')
            foreach ($file in $files) {
                $target = Join-Path $UserDir $file
                if (Test-Path -LiteralPath $target -PathType Leaf) {
                    Copy-Item -LiteralPath $target -Destination ($target + $suffix)
                }
                Copy-Item -LiteralPath (Join-Path $PSScriptRoot "config\$file") -Destination $target -Force
            }
            Write-Output "Configuration synchronized: $UserDir"
        }
    }
    catch {
        Write-Error -Message $_.Exception.Message -ErrorAction Continue
        exit 1
    }
}

function Sync-Extension {
    try {
        $codium = Find-Codium -RequestedPath $CodiumBin
        if (-not $ExtensionsDir) { $ExtensionsDir = (Get-CodiumDirectories -Codium $codium).Extensions }
        if ($Export) {
            $result = Invoke-Codium -Command $codium -Arguments @('--extensions-dir', $ExtensionsDir, '--list-extensions')
            $ids = @($result.Lines)
            if ($result.ExitCode -ne 0) { throw 'Cannot list installed extensions.' }
            $ids = @($ids | Where-Object { $_ } | Sort-Object -Unique)
            if ($ids.Count -eq 0) { throw 'Installed extension list is empty; refusing to erase the repository list.' }
            foreach ($id in $ids) {
                if ($id -notmatch '^[A-Za-z0-9_-]+\.[A-Za-z0-9_.-]+$') { throw "Invalid installed extension ID: $id" }
            }
            if ($PSCmdlet.ShouldProcess($ExtensionFile, 'Export installed extension IDs')) {
                [System.IO.File]::WriteAllText(
                    $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($ExtensionFile),
                    ($ids -join "`n") + "`n", [System.Text.UTF8Encoding]::new($false)
                )
                Write-Output "Extension list synchronized: $($ids.Count) entries"
            }
        }
        else {
            $ids = @(Read-ExtensionIds -Path $ExtensionFile)
            if ($PSCmdlet.ShouldProcess($ExtensionsDir, "Install $($ids.Count) extensions from $ExtensionFile")) {
                $installArgs = @('--extensions-dir', $ExtensionsDir)
                foreach ($id in $ids) { $installArgs += @('--install-extension', $id) }
                $result = Invoke-Codium -Command $codium -Arguments $installArgs
                $result.Lines | ForEach-Object { Write-Host "$_" }
                $installExitCode = $result.ExitCode
                $result = Invoke-Codium -Command $codium -Arguments @('--extensions-dir', $ExtensionsDir, '--list-extensions')
                $installed = @($result.Lines)
                if ($result.ExitCode -ne 0) { throw 'Cannot verify installed extensions.' }
                $missing = @($ids | Where-Object { $_ -notin $installed })
                if ($missing.Count -gt 0) { throw "Extensions are still missing: $($missing -join ', ')" }
                if ($installExitCode -ne 0) { throw "VSCodium returned exit code $installExitCode while installing extensions." }
                Write-Output "Verified: $($ids.Count)/$($ids.Count) requested extensions installed."
            }
        }
    }
    catch {
        Write-Error -Message $_.Exception.Message -ErrorAction Continue
        exit 1
    }
}

function Update-Extension {
    $codium = $null
    $workDir = $null
    $script:preserveBackup = $false
    try {
        $codium = Find-Codium -RequestedPath $CodiumBin
        $result = Invoke-Codium -Command $codium -Arguments @('--version')
        $cliVersion = @($result.Lines | Where-Object { $_ -is [string] -and $_.Trim() -in @('x64', 'arm64', 'ia32') })
        if ($result.ExitCode -ne 0 -or $cliVersion.Count -ne 1) { throw 'Cannot determine VSCodium architecture.' }
        $arch = $cliVersion[-1].Trim()
        if ($arch -notin @('x64', 'arm64', 'ia32')) { throw "Unsupported VSCodium architecture: $arch" }
        $platform = "win32-$arch"
        if (-not $ExtensionsDir) {
            $ExtensionsDir = (Get-CodiumDirectories -Codium $codium).Extensions
        }
        $ExtensionsDir = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($ExtensionsDir)
        $ExtensionsDir = $ExtensionsDir.TrimEnd('\', '/')
        if (Test-Path -LiteralPath $ExtensionsDir) {
            $extensionRoot = Get-Item -LiteralPath $ExtensionsDir
            if (-not $extensionRoot.PSIsContainer -or
                ($extensionRoot.Attributes -band [System.IO.FileAttributes]::ReparsePoint)) {
                throw "Extension directory is not a regular directory: $ExtensionsDir"
            }
        }
        $ids = @(Read-ExtensionIds -Path $ExtensionFile)
        Add-Type -AssemblyName System.IO.Compression.FileSystem
        [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
        $installed = Get-InstalledVersions
        Write-Host "VSCodium CLI: $codium"
        Write-Host "Extensions directory: $ExtensionsDir ($platform)"
        $available = 0
        $updated = 0
        $failed = 0
        $skipped = 0
        foreach ($id in $ids) {
            try {
                $parts = $id.Split('.', 2)
                $url = "https://open-vsx.org/api/$($parts[0])/$($parts[1])"
                $metadata = Get-ExtensionMetadata -Url $url -Platform $platform
                if ($metadata.namespace -ine $parts[0] -or $metadata.name -ine $parts[1] -or
                    $metadata.targetPlatform -notin @($platform, 'universal')) {
                    throw "Open VSX returned an incompatible package for $id"
                }
                $remoteVersion = [string]$metadata.version
                $localVersion = [string]$installed[$id]
                if (-not (Test-NewerVersion -RemoteVersion $remoteVersion -InstalledVersion $localVersion)) {
                    Write-Host "Current ${id}: installed $localVersion, latest $remoteVersion"
                    continue
                }
                $available++
                $displayVersion = if ($localVersion) { $localVersion } else { 'not installed' }
                Write-Host "${id}: $displayVersion -> $remoteVersion"
                if (-not $Check -and $PSCmdlet.ShouldProcess("$id@$remoteVersion in $ExtensionsDir", 'Download, validate and install VSIX')) {
                    if (-not $workDir) {
                        $workDir = Join-Path ([System.IO.Path]::GetTempPath()) ('vscodium-update-' + [guid]::NewGuid().ToString('N'))
                        New-Item -ItemType Directory -Path $workDir | Out-Null
                    }
                    if (Install-Extension -Id $id -Version $remoteVersion -DownloadUrl $metadata.files.download -Platform $platform) {
                        $updated++
                    }
                    else { $skipped++ }
                }
            }
            catch {
                Write-Warning "${id}: $($_.Exception.Message)"
                $failed++
                if ($preserveBackup) { break }
            }
        }
        Write-Host "Updates available: $available; updated: $updated; incompatible: $skipped; failed: $failed"
        if ($failed -gt 0) { exit 1 }
    }

    catch {
        Write-Error -Message $_.Exception.Message -ErrorAction Continue
        exit 1
    }
    finally {
        if ($workDir -and -not $preserveBackup) {
            $resolvedWorkDir = [System.IO.Path]::GetFullPath($workDir)
            $tempRoot = [System.IO.Path]::GetFullPath([System.IO.Path]::GetTempPath()).TrimEnd('\', '/') + [System.IO.Path]::DirectorySeparatorChar
            if ($resolvedWorkDir.StartsWith($tempRoot, [System.StringComparison]::OrdinalIgnoreCase) -and
                [System.IO.Path]::GetFileName($resolvedWorkDir).StartsWith('vscodium-update-')) {
                Remove-Item -LiteralPath $resolvedWorkDir -Recurse -Force
            }
        }
    }
}

function Assert-ApplicationPath {
    param([string]$InstallPath, [switch]$MustExist)

    $fullPath = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($InstallPath).TrimEnd('\', '/')
    $protectedPaths = @([System.IO.Path]::GetPathRoot($fullPath), $env:USERPROFILE,
        $env:APPDATA, $env:LOCALAPPDATA, $env:ProgramFiles, [System.IO.Path]::GetTempPath())
    foreach ($protected in $protectedPaths) {
        if ($protected -and $fullPath -ieq $protected.TrimEnd('\', '/')) {
            throw "Refusing to use a protected directory as the installation path: $fullPath"
        }
    }
    if (Test-Path -LiteralPath $fullPath) {
        $directory = Get-Item -LiteralPath $fullPath
        if (-not $directory.PSIsContainer -or ($directory.Attributes -band [System.IO.FileAttributes]::ReparsePoint)) {
            throw "Installation path is not a regular directory: $fullPath"
        }
        foreach ($file in @('VSCodium.exe', 'bin\codium.cmd')) {
            if (-not (Test-Path -LiteralPath (Join-Path $fullPath $file) -PathType Leaf)) {
                throw "Refusing to replace or remove an unrecognized installation: $fullPath"
            }
        }
    }
    elseif ($MustExist) { throw "VSCodium installation was not found: $fullPath" }
    return $fullPath
}

function Assert-ApplicationStopped {
    param([string]$InstallPath)

    $executable = Join-Path $InstallPath 'VSCodium.exe'
    $running = @(Get-Process -Name VSCodium -ErrorAction SilentlyContinue | Where-Object { $_.Path -ieq $executable })
    if ($running.Count -gt 0) { throw "Close VSCodium before replacing or removing this installation: $InstallPath" }
}

function Invoke-WithFileRetry {
    param([scriptblock]$Operation, [string]$Description)

    for ($attempt = 1; $attempt -le 5; $attempt++) {
        try {
            & $Operation
            return
        }
        catch {
            $exception = $_.Exception
            $busy = $false
            while ($exception) {
                if (($exception.HResult -band 0xFFFF) -in @(32, 33)) { $busy = $true; break }
                $exception = $exception.InnerException
            }
            if (-not $busy -or $attempt -eq 5) { throw }
            $target = if ($_.TargetObject) { " Target: $($_.TargetObject)." } else { '' }
            Write-Warning "File is busy while ${Description}; retry $attempt/4.$target"
            Start-Sleep -Milliseconds (250 * [int][Math]::Pow(2, $attempt - 1))
        }
    }
}

function Install-Application {
    param(
        [string]$ExpectedVersion,
        [string]$ExpectedArchitecture,
        [string]$StagingRoot = [System.IO.Path]::GetTempPath(),
        [switch]$AlreadyApproved
    )

    if (-not $Archive) { throw 'Specify -Archive with a downloaded VSCodium Windows ZIP.' }
    $archivePath = (Get-Item -LiteralPath $Archive).FullName
    $installPath = Assert-ApplicationPath -InstallPath $Path
    $exists = Test-Path -LiteralPath $installPath
    if ($exists -and -not $Force) { throw "Installation already exists: $installPath. Use -Force to replace it with a backup." }
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $zip = Invoke-WithFileRetry -Description "opening ZIP $archivePath" -Operation {
        [System.IO.Compression.ZipFile]::OpenRead($archivePath)
    }
    try {
        foreach ($entry in $zip.Entries) {
            if ($entry.FullName -match '(^[/\\]|(^|[/\\])\.\.([/\\]|$)|\\|:)' -or
                ((($entry.ExternalAttributes -shr 16) -band 0xF000) -eq 0xA000)) {
                throw "Unsafe ZIP entry: $($entry.FullName)"
            }
        }
        if (-not $zip.GetEntry('VSCodium.exe') -or -not $zip.GetEntry('bin/codium.cmd')) {
            throw 'ZIP must contain VSCodium.exe and bin/codium.cmd at its root.'
        }
        if (@($zip.Entries | Where-Object { $_.FullName -like 'data/*' }).Count -gt 0) {
            throw 'Use an application ZIP without a bundled portable data directory.'
        }
    }
    finally { $zip.Dispose() }
    if (-not $AlreadyApproved -and -not $PSCmdlet.ShouldProcess($installPath, 'Install VSCodium ZIP and preserve portable data')) { return }
    if ($exists) { Assert-ApplicationStopped -InstallPath $installPath }
    $staging = Join-Path $StagingRoot ('vscodium-install-' + [guid]::NewGuid().ToString('N'))
    $backup = $null
    $newInstallation = $false
    $stage = "extracting $archivePath into $staging"
    try {
        [System.IO.Compression.ZipFile]::ExtractToDirectory($archivePath, $staging)
        $stage = "verifying the application in $staging"
        if ($ExpectedVersion) {
            $package = Get-Content -LiteralPath (Join-Path $staging 'resources\app\package.json') -Raw | ConvertFrom-Json
            if ($package.version -cne $ExpectedVersion) { throw "ZIP contains an unexpected version: $($package.version)" }
            $result = Invoke-Codium -Command (Join-Path $staging 'bin\codium.cmd') -Arguments @('--version')
            $versions = @($result.Lines | Where-Object { $_ -is [string] -and $_.Trim() -ceq $ExpectedVersion })
            $architectures = @($result.Lines | Where-Object { $_ -is [string] -and $_.Trim() -ceq $ExpectedArchitecture })
            if ($result.ExitCode -ne 0 -or $versions.Count -ne 1 -or $architectures.Count -ne 1) {
                throw 'Downloaded VSCodium CLI failed version or architecture verification.'
            }
        }
        $oldData = Join-Path $installPath 'data'
        $stage = "copying portable data from $oldData"
        if (Test-Path -LiteralPath $oldData) {
            $links = @(Get-Item -LiteralPath $oldData | Where-Object { $_.Attributes -band [System.IO.FileAttributes]::ReparsePoint })
            $links += @(Get-ChildItem -LiteralPath $oldData -Recurse -Force -Attributes ReparsePoint)
            if ($links.Count -gt 0) { throw 'Portable data contains reparse points; refusing to copy it during replacement.' }
            Invoke-WithFileRetry -Description $stage -Operation {
                Copy-Item -LiteralPath $oldData -Destination $staging -Recurse -Force
            }
        }
        else { New-Item -ItemType Directory -Path (Join-Path $staging 'data') | Out-Null }
        $parent = Split-Path -Parent $installPath
        New-Item -ItemType Directory -Path $parent -Force | Out-Null
        if ($exists) {
            $backup = $installPath + '.bak-' + (Get-Date -Format 'yyyyMMdd-HHmmss-fffffff')
            $stage = "backing up $installPath to $backup"
            Invoke-WithFileRetry -Description $stage -Operation {
                Move-Item -LiteralPath $installPath -Destination $backup
            }
        }
        $stage = "replacing $installPath from $staging"
        Invoke-WithFileRetry -Description $stage -Operation {
            Move-Item -LiteralPath $staging -Destination $installPath
        }
        $newInstallation = $true
        if ($backup) { Write-Host "Previous installation retained: $backup" }
        Write-Host "VSCodium installed: $installPath"
        Write-Host "CLI: $(Join-Path $installPath 'bin\codium.cmd')"
    }
    catch {
        $failure = $_
        if ($backup -and -not $newInstallation -and -not (Test-Path -LiteralPath $installPath)) {
            try {
                Invoke-WithFileRetry -Description "restoring $backup to $installPath" -Operation {
                    Move-Item -LiteralPath $backup -Destination $installPath
                }
            }
            catch {
                throw [System.InvalidOperationException]::new("Installation failed while ${stage}; rollback failed. Previous installation retained at ${backup}: $($_.Exception.Message)", $failure.Exception)
            }
        }
        $target = if ($failure.TargetObject) { " Target: $($failure.TargetObject)." } else { '' }
        throw [System.InvalidOperationException]::new("Installation failed while ${stage}: $($failure.Exception.Message)$target", $failure.Exception)
    }
    finally {
        $tempRoot = [System.IO.Path]::GetFullPath($StagingRoot).TrimEnd('\', '/') + [System.IO.Path]::DirectorySeparatorChar
        $resolvedStaging = [System.IO.Path]::GetFullPath($staging)
        if (Test-Path -LiteralPath $resolvedStaging) {
            if (-not $resolvedStaging.StartsWith($tempRoot, [System.StringComparison]::OrdinalIgnoreCase) -or
                -not [System.IO.Path]::GetFileName($resolvedStaging).StartsWith('vscodium-install-')) {
                throw "Unsafe staging cleanup path: $resolvedStaging"
            }
            if ($newInstallation) { Remove-Item -LiteralPath $resolvedStaging -Recurse -Force }
            else { Write-Warning "Installation staging retained after failure: $resolvedStaging" }
        }
    }
}

function Upgrade-Application {
    $installPath = Assert-ApplicationPath -InstallPath $Path -MustExist
    $result = Invoke-Codium -Command (Join-Path $installPath 'bin\codium.cmd') -Arguments @('--version')
    $versions = @($result.Lines | Where-Object { $_ -is [string] -and $_.Trim() -match '^\d+\.\d+\.\d+$' })
    $architectures = @($result.Lines | Where-Object { $_ -is [string] -and $_.Trim() -in @('x64', 'arm64', 'ia32') })
    if ($result.ExitCode -ne 0 -or $versions.Count -ne 1 -or $architectures.Count -ne 1) {
        throw 'Cannot determine installed VSCodium version and architecture.'
    }
    $installedVersion = $versions[0].Trim()
    $arch = $architectures[0].Trim()
    [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
    $headers = @{ 'User-Agent' = 'vscodium-upgrader'; Accept = 'application/vnd.github+json' }
    $release = Invoke-RestMethod -Uri 'https://api.github.com/repos/VSCodium/vscodium/releases/latest' -Headers $headers -TimeoutSec 60
    if ($release.draft -or $release.prerelease) { throw 'GitHub returned a draft or prerelease instead of a stable release.' }
    $version = ([string]$release.tag_name).TrimStart('v')
    if (-not (Test-NewerVersion -RemoteVersion $version -InstalledVersion $installedVersion)) {
        Write-Host "VSCodium is current: installed $installedVersion, latest $version"
        return
    }
    $assetName = "VSCodium-win32-$arch-$version.zip"
    $assets = @($release.assets | Where-Object { $_.name -ceq $assetName })
    if ($assets.Count -ne 1) { throw "Latest release has no unique Windows ZIP for ${arch}: $assetName" }
    $asset = $assets[0]
    $downloadUrl = "https://github.com/VSCodium/vscodium/releases/download/$($release.tag_name)/$assetName"
    if ($asset.browser_download_url -cne $downloadUrl) { throw "Unexpected release download URL: $assetName" }
    $digest = $asset.PSObject.Properties['digest']
    $expectedHash = $null
    if ($digest -and $digest.Value -match '^sha256:([0-9a-fA-F]{64})$') { $expectedHash = $Matches[1] }
    $checksums = @($release.assets | Where-Object { $_.name -ceq ($assetName + '.sha256') })
    if (-not $expectedHash -and $checksums.Count -ne 1) { throw "Release lacks a SHA-256 checksum: $assetName" }
    if (-not $env:TEMP) { throw 'TEMP is not set.' }
    $tempRoot = [System.IO.Path]::GetFullPath($env:TEMP).TrimEnd('\', '/')
    Write-Host "VSCodium upgrade: $installedVersion -> $version ($arch)"
    if (-not $PSCmdlet.ShouldProcess($installPath, 'Download the latest stable ZIP into TEMP and replace VSCodium with a backup')) { return }
    Assert-ApplicationStopped -InstallPath $installPath
    $downloadDir = Join-Path $tempRoot ('vscodium-upgrade-' + [guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $downloadDir | Out-Null
    $upgradeCompleted = $false
    $stage = "downloading $assetName"
    try {
        $Archive = Join-Path $downloadDir $assetName
        Write-Host "Downloading $assetName into $downloadDir"
        Invoke-WithFileRetry -Description $stage -Operation {
            Invoke-WebRequest -Uri $downloadUrl -OutFile $Archive -UseBasicParsing -TimeoutSec 600
        }
        $stage = "verifying SHA-256 for $Archive"
        if (-not $expectedHash) {
            $checksumUrl = $downloadUrl + '.sha256'
            if ($checksums[0].browser_download_url -cne $checksumUrl) { throw 'Unexpected checksum download URL.' }
            $checksumFile = Join-Path $downloadDir ($assetName + '.sha256')
            Invoke-WebRequest -Uri $checksumUrl -OutFile $checksumFile -UseBasicParsing -TimeoutSec 60
            $checksum = (Get-Content -LiteralPath $checksumFile -Raw).Trim()
            if ($checksum -notmatch '^([0-9a-fA-F]{64})(?:\s+\*?([^\r\n]+))?$') { throw 'Invalid SHA-256 checksum file.' }
            $expectedHash = $Matches[1]
            if ($Matches.ContainsKey(2) -and $Matches[2] -cne $assetName) { throw 'SHA-256 checksum names a different archive.' }
        }
        $hash = Invoke-WithFileRetry -Description $stage -Operation {
            Get-FileHash -LiteralPath $Archive -Algorithm SHA256
        }
        if ($hash.Hash -ine $expectedHash) {
            throw "SHA-256 verification failed: $assetName"
        }
        $Path = $installPath
        $Force = $true
        $stage = "installing $Archive into $installPath"
        Install-Application -ExpectedVersion $version -ExpectedArchitecture $arch -StagingRoot $downloadDir -AlreadyApproved
        $upgradeCompleted = $true
        Write-Host "VSCodium upgraded to $version"
    }
    catch {
        $failure = $_
        $target = if ($failure.TargetObject) { " Target: $($failure.TargetObject)." } else { '' }
        throw [System.InvalidOperationException]::new("Upgrade failed while ${stage}: $($failure.Exception.Message)$target", $failure.Exception)
    }
    finally {
        $resolvedDownloadDir = [System.IO.Path]::GetFullPath($downloadDir)
        if ([System.IO.Path]::GetDirectoryName($resolvedDownloadDir) -ine $tempRoot -or
            -not [System.IO.Path]::GetFileName($resolvedDownloadDir).StartsWith('vscodium-upgrade-')) {
            throw "Unsafe download cleanup path: $resolvedDownloadDir"
        }
        if ($upgradeCompleted) {
            try {
                Invoke-WithFileRetry -Description "cleaning up $resolvedDownloadDir" -Operation {
                    if (Test-Path -LiteralPath $resolvedDownloadDir) {
                        Remove-Item -LiteralPath $resolvedDownloadDir -Recurse -Force
                    }
                }
            }
            catch { Write-Warning "VSCodium was upgraded, but temporary files remain at ${resolvedDownloadDir}: $($_.Exception.Message)" }
        }
        else { Write-Warning "Upgrade download retained after failure: $resolvedDownloadDir" }
    }
}

function Remove-Application {
    $installPath = Assert-ApplicationPath -InstallPath $Path -MustExist
    if ($PSCmdlet.ShouldProcess($installPath, 'Remove VSCodium from this path by moving it to a backup')) {
        Assert-ApplicationStopped -InstallPath $installPath
        $backup = $installPath + '.removed-' + (Get-Date -Format 'yyyyMMdd-HHmmss-fffffff')
        Move-Item -LiteralPath $installPath -Destination $backup
        Write-Host "VSCodium removed from $installPath; restorable backup: $backup"
    }
}

function Show-Usage {
    Write-Output @(
        'Usage: .\windows-vscodium.ps1 COMMAND [TARGET] [OPTIONS]',
        '  install -Archive FILE [-Path DIR] [-Force]',
        '  upgrade [-Path DIR]',
        '  remove [-Path DIR]',
        '  sync',
        '  sync setting [-UserDir DIR]',
        '  sync extension [-Export]',
        '  update extension [-Check]',
        '  Use -WhatIf to preview changes; Get-Help .\windows-vscodium.ps1 -Full for parameters.'
    )
}

try {
    if ($Target -and $Action -notin @('sync', 'update')) { throw 'A target is only valid for sync or update.' }
    if (-not $ExtensionFile) { $ExtensionFile = Join-Path $PSScriptRoot 'config\extension.txt' }
    if ($Check -and $Action -ne 'update') { throw '-Check is only valid for update extension.' }
    if ($Export -and ($Action -ne 'sync' -or $Target -ne 'extension')) { throw '-Export is only valid for sync extension.' }
    switch ($Action) {
        'help' { Show-Usage }
        'install' { Install-Application }
        'upgrade' { Upgrade-Application }
        'remove' { Remove-Application }
        'sync' {
            if (-not $Target -or $Target -eq 'setting') { Sync-Setting }
            if (-not $Target -or $Target -eq 'extension') { Sync-Extension }
        }
        'update' {
            if ($Target -and $Target -ne 'extension') { throw 'Only update extension is supported.' }
            Update-Extension
        }
    }
}
catch {
    Write-Error -Message $_.Exception.Message -ErrorAction Continue
    exit 1
}
