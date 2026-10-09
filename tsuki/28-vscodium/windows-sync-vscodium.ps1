[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [string]$CodiumBin = $env:CODIUM_BIN,
    [string]$ExtensionFile,
    [switch]$ExtensionsOnly
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Find-Codium {
    param([string]$RequestedPath)

    if ($RequestedPath) {
        $command = Get-Command -Name $RequestedPath -CommandType Application -ErrorAction Stop
        return $command.Source
    }

    $command = Get-Command -Name 'codium.cmd', 'codium' -CommandType Application -ErrorAction SilentlyContinue |
        Select-Object -First 1
    if ($command) {
        return $command.Source
    }

    $candidates = @(
        (Join-Path $env:APPDATA 'Apps\VSCodium\bin\codium.cmd'),
        (Join-Path $env:LOCALAPPDATA 'Programs\VSCodium\bin\codium.cmd'),
        (Join-Path $env:ProgramFiles 'VSCodium\bin\codium.cmd')
    )
    if (${env:ProgramFiles(x86)}) {
        $candidates += Join-Path ${env:ProgramFiles(x86)} 'VSCodium\bin\codium.cmd'
    }
    foreach ($candidate in $candidates) {
        if (Test-Path -LiteralPath $candidate -PathType Leaf) {
            return $candidate
        }
    }
    throw 'VSCodium CLI was not found. Specify -CodiumBin with the path to bin\codium.cmd.'
}

try {
    if (-not $ExtensionFile) {
        $ExtensionFile = Join-Path $PSScriptRoot 'config\extension.txt'
    }
    $codium = Find-Codium -RequestedPath $CodiumBin
    $extensions = @(Get-Content -LiteralPath $ExtensionFile | ForEach-Object {
        ($_ -split '#', 2)[0].Trim()
    } | Where-Object { $_ } | Sort-Object -Unique)
    if ($extensions.Count -eq 0) {
        throw "Extension list is empty: $ExtensionFile"
    }
    foreach ($extension in $extensions) {
        if ($extension -notmatch '^[A-Za-z0-9][A-Za-z0-9_-]*\.[A-Za-z0-9][A-Za-z0-9_-]*$') {
            throw "Invalid extension ID: $extension"
        }
    }

    Write-Output "VSCodium CLI: $codium"
    if (-not $ExtensionsOnly) {
        $installDir = Split-Path -Parent (Split-Path -Parent $codium)
        $portableData = Join-Path $installDir 'data'
        $userDir = Join-Path $env:APPDATA 'VSCodium\User'
        if (Test-Path -LiteralPath $portableData -PathType Container) {
            $userDir = Join-Path $portableData 'user-data\User'
        }
        $configFiles = @('settings.json', 'keybindings.json')
        foreach ($file in $configFiles) {
            $source = Join-Path $PSScriptRoot "config\$file"
            if (-not (Test-Path -LiteralPath $source -PathType Leaf)) {
                throw "Configuration file was not found: $source"
            }
        }
        if ($PSCmdlet.ShouldProcess($userDir, 'Back up existing settings and synchronize repository configuration')) {
            New-Item -ItemType Directory -Path $userDir -Force | Out-Null
            $backupSuffix = '.bak-' + (Get-Date -Format 'yyyyMMdd-HHmmss-fffffff')
            foreach ($file in $configFiles) {
                $target = Join-Path $userDir $file
                if (Test-Path -LiteralPath $target -PathType Leaf) {
                    Copy-Item -LiteralPath $target -Destination ($target + $backupSuffix)
                }
                Copy-Item -LiteralPath (Join-Path $PSScriptRoot "config\$file") -Destination $target -Force
            }
            Write-Output "Configuration synchronized: $userDir"
        }
    }

    if ($PSCmdlet.ShouldProcess($codium, "Install or update $($extensions.Count) extensions from $ExtensionFile")) {
        $installArgs = @('--force')
        foreach ($extension in $extensions) {
            $installArgs += '--install-extension'
            $installArgs += $extension
        }
        & $codium @installArgs
        $installExitCode = $LASTEXITCODE
        $installed = @(& $codium --list-extensions)
        if ($LASTEXITCODE -ne 0) {
            throw 'Cannot verify installed extensions.'
        }
        $missing = @($extensions | Where-Object { $_ -notin $installed })
        if ($missing.Count -gt 0) {
            throw "Extensions are still missing: $($missing -join ', ')"
        }
        if ($installExitCode -ne 0) {
            throw "VSCodium returned exit code $installExitCode while installing or updating extensions."
        }
        Write-Output "Verified: $($extensions.Count)/$($extensions.Count) requested extensions installed."
    }
}
catch {
    Write-Error -Message $_.Exception.Message -ErrorAction Continue
    exit 1
}
