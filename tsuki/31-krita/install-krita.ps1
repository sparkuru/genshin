[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)][string]$ArchivePath,
    [string]$Destination = 'D:\software\krita',
    [ValidatePattern('^[a-fA-F0-9]{64}$')]
    [string]$ExpectedSha256 = '87278594fac0267680303280e410578388d606aec5a290f2b0d009909f4254f0'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if ($env:OS -ne 'Windows_NT') {
    throw 'This script requires Windows.'
}
if (-not (Test-Path -LiteralPath $ArchivePath -PathType Leaf)) {
    throw "Krita ZIP not found: $ArchivePath"
}
$archive = Get-Item -LiteralPath $ArchivePath -Force
if (($archive.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
    throw 'Refusing to use an archive that is a reparse point.'
}
if ($archive.Extension -ine '.zip') {
    throw 'ArchivePath must point to a ZIP file.'
}
$actualSha256 = (Get-FileHash -LiteralPath $archive.FullName -Algorithm SHA256).Hash
if ($actualSha256 -ine $ExpectedSha256) {
    throw "Archive SHA-256 mismatch. Actual: $actualSha256"
}

$destinationPath = [System.IO.Path]::GetFullPath($Destination).TrimEnd('\')
if (Test-Path -LiteralPath $destinationPath) {
    throw "Destination already exists; choose an empty path instead: $destinationPath"
}
$parent = Split-Path -Path $destinationPath -Parent
if (-not (Test-Path -LiteralPath $parent -PathType Container)) {
    throw "Destination parent does not exist: $parent"
}
$parentItem = Get-Item -LiteralPath $parent -Force
if (($parentItem.Attributes -band [System.IO.FileAttributes]::ReparsePoint) -ne 0) {
    throw 'Refusing to install into a reparse-point parent directory.'
}

Add-Type -AssemblyName System.IO.Compression.FileSystem
$zip = [System.IO.Compression.ZipFile]::OpenRead($archive.FullName)
try {
    foreach ($entry in $zip.Entries) {
        $entryName = $entry.FullName.Replace('\', '/')
        if ($entryName.StartsWith('/') -or $entryName -match '(^|/)\.\.(/|$)' -or $entryName -match '^[A-Za-z]:') {
            throw "Unsafe path in ZIP: $entryName"
        }
    }
} finally {
    $zip.Dispose()
}

$stage = Join-Path $parent ('.krita-extract-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $stage | Out-Null
try {
    Expand-Archive -LiteralPath $archive.FullName -DestinationPath $stage
    $candidates = @()
    if (Test-Path -LiteralPath (Join-Path $stage 'bin\krita.exe') -PathType Leaf) {
        $candidates += $stage
    }
    foreach ($child in @(Get-ChildItem -LiteralPath $stage -Directory)) {
        if (Test-Path -LiteralPath (Join-Path $child.FullName 'bin\krita.exe') -PathType Leaf) {
            $candidates += $child.FullName
        }
    }
    if ($candidates.Count -ne 1) {
        throw "Expected one Krita portable root containing bin\krita.exe; found $($candidates.Count)."
    }
    [System.IO.Directory]::Move($candidates[0], $destinationPath)
    Write-Host "Krita portable extracted: $destinationPath"
    Write-Host "Executable: $(Join-Path $destinationPath 'bin\krita.exe')"
} finally {
    if (Test-Path -LiteralPath $stage -PathType Container) {
        Remove-Item -LiteralPath $stage -Recurse -Force
    }
}
