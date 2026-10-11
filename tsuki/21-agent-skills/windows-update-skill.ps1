#Requires -Version 5.1
<#
.SYNOPSIS
Synchronizes Windows skill copies for Claude, Codex, and OpenCode.
.DESCRIPTION
Replaces same-name skills with complete copies, including removal of stale files.
A manifest tracks copied skills for cleanup after upstream renames or deletions.
Unrelated skills are preserved. Existing junctions are replaced with copies.
Like update-skill.sh, show refreshes base skills before listing them.
.EXAMPLE
.\windows-update-skill.ps1
.EXAMPLE
.\windows-update-skill.ps1 show
#>
[CmdletBinding()]
param(
    [Parameter(Position = 0)]
    [ValidateSet('sync', 'show')]
    [string]$Operation = 'sync'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

if ($env:OS -ne 'Windows_NT') {
    throw 'This script requires Windows.'
}

$sourceDirectory = $PSScriptRoot
$baseSkillDirectory = Join-Path $sourceDirectory 'base\windows'
$baseRepositoryPath = [System.IO.Path]::GetFullPath((Join-Path $sourceDirectory '..\..\..\..'))
$baseSkillPath = Join-Path $baseRepositoryPath '21-geass\skills'
$userProfilePath = $env:USERPROFILE
if ([string]::IsNullOrWhiteSpace($userProfilePath)) {
    throw 'USERPROFILE is not set.'
}
$targetDirectories = @(
    (Join-Path $userProfilePath '.claude\skills')
    (Join-Path $userProfilePath '.codex\skills')
    (Join-Path $userProfilePath '.config\opencode\skills')
)
$manifestName = '.windows-update-skill.json'
$colorEnabled = [string]::IsNullOrEmpty($env:NO_COLOR) -and -not [Console]::IsOutputRedirected

function Write-Status {
    param([string]$Message, [ConsoleColor]$Color = 'Gray')

    if ($colorEnabled) {
        Write-Host $Message -ForegroundColor $Color
    }
    else {
        Write-Host $Message
    }
}

function Get-DisplayPath {
    param([string]$Path)

    if ($Path -ieq $userProfilePath) { return '~' }
    $prefix = $userProfilePath.TrimEnd('\') + '\'
    if ($Path.StartsWith($prefix, [StringComparison]::OrdinalIgnoreCase)) {
        return '~\' + $Path.Substring($prefix.Length)
    }
    return $Path
}

function Test-Link {
    param([System.IO.FileSystemInfo]$Entry)

    return $Entry.LinkType -in @('Junction', 'SymbolicLink')
}

function Get-LinkDestination {
    param([System.IO.FileSystemInfo]$Entry)

    $targets = @($Entry.Target)
    if ($targets.Count -eq 0 -or [string]::IsNullOrEmpty($targets[0])) {
        throw "Cannot read link target: $($Entry.FullName)"
    }
    $destination = [string]$targets[0]
    if (-not [System.IO.Path]::IsPathRooted($destination)) {
        if ($Entry -is [System.IO.DirectoryInfo]) {
            $destination = Join-Path $Entry.Parent.FullName ([string]$targets[0])
        }
        else {
            $destination = Join-Path $Entry.DirectoryName $destination
        }
    }
    return [System.IO.Path]::GetFullPath($destination).TrimEnd('\')
}

function Remove-EntryTree {
    param([System.IO.FileSystemInfo]$Entry)

    # Never traverse destination links when deleting an old copy.
    if (Test-Link $Entry) {
        if ($Entry -is [System.IO.DirectoryInfo]) {
            [System.IO.Directory]::Delete($Entry.FullName, $false)
        }
        else {
            [System.IO.File]::Delete($Entry.FullName)
        }
        return
    }
    if ($Entry.PSIsContainer) {
        foreach ($child in Get-ChildItem -LiteralPath $Entry.FullName -Force) {
            Remove-EntryTree $child
        }
    }
    Remove-Item -LiteralPath $Entry.FullName -Force
}

function Remove-SkillEntry {
    param([System.IO.FileSystemInfo]$Entry, [string]$ParentDirectory)

    $expectedParent = [System.IO.Path]::GetFullPath($ParentDirectory).TrimEnd('\')
    $actualParent = [System.IO.Path]::GetDirectoryName($Entry.FullName).TrimEnd('\')
    if ($actualParent -ine $expectedParent) {
        throw "Refusing to remove an entry outside the skill directory: $($Entry.FullName)"
    }

    Remove-EntryTree $Entry
    Write-Status "remove: $(Get-DisplayPath $Entry.FullName)" Red
}

function Get-ManagedNames {
    param([string]$Directory)

    $manifestPath = Join-Path $Directory $manifestName
    if (-not (Test-Path -LiteralPath $manifestPath)) { return }
    $manifest = Get-Content -LiteralPath $manifestPath -Raw -Encoding UTF8 | ConvertFrom-Json
    foreach ($name in $manifest.skills) {
        if ([string]::IsNullOrWhiteSpace($name) -or $name -in @('.', '..', $manifestName) -or
            $name.IndexOfAny([System.IO.Path]::GetInvalidFileNameChars()) -ge 0) {
            throw "Invalid skill name in manifest: $manifestPath"
        }
        [string]$name
    }
}

function Copy-SkillTree {
    param(
        [string]$Source,
        [string]$Destination,
        [System.Collections.Generic.HashSet[string]]$Ancestors
    )

    $sourceEntry = Get-Item -LiteralPath $Source -Force
    $identity = $sourceEntry.FullName
    if (Test-Link $sourceEntry) { $identity = Get-LinkDestination $sourceEntry }
    if (-not $Ancestors.Add($identity)) {
        throw "Directory link cycle in skill source: $Source"
    }
    try {
        [System.IO.Directory]::CreateDirectory($Destination) | Out-Null
        foreach ($entry in Get-ChildItem -LiteralPath $Source -Force) {
            $copyPath = Join-Path $Destination $entry.Name
            if ($entry.PSIsContainer) {
                Copy-SkillTree $entry.FullName $copyPath $Ancestors
            }
            else {
                [System.IO.File]::Copy($entry.FullName, $copyPath, $true)
                [System.IO.File]::SetLastWriteTimeUtc($copyPath, $entry.LastWriteTimeUtc)
            }
        }
    }
    finally {
        $Ancestors.Remove($identity) | Out-Null
    }
}

function Sync-SkillCopy {
    param([string]$Directory, [string]$Name, [string]$Source)

    $destination = [System.IO.Path]::GetFullPath((Join-Path $Directory $Name))
    $sourcePath = [System.IO.Path]::GetFullPath($Source)
    if ($sourcePath -ieq $destination -or
        $sourcePath.StartsWith($destination + '\', [StringComparison]::OrdinalIgnoreCase)) {
        throw "Skill destination contains its source: $destination"
    }

    $stagingPath = Join-Path $Directory ('.windows-update-skill-' + [Guid]::NewGuid().ToString('N'))
    $ancestors = New-Object 'System.Collections.Generic.HashSet[string]' ([StringComparer]::OrdinalIgnoreCase)
    try {
        Copy-SkillTree $Source $stagingPath $ancestors
        $existing = Get-Item -LiteralPath $destination -Force -ErrorAction SilentlyContinue
        if ($null -ne $existing) {
            Remove-SkillEntry $existing $Directory
        }
        [System.IO.Directory]::Move($stagingPath, $destination)
        Write-Status "sync: $(Get-DisplayPath $destination)" Green
    }
    finally {
        $staging = Get-Item -LiteralPath $stagingPath -Force -ErrorAction SilentlyContinue
        if ($null -ne $staging) { Remove-SkillEntry $staging $Directory }
    }
}

function Sync-SkillDirectory {
    param([string]$Directory, [string[]]$Sources, [switch]$OwnsDirectory)

    [System.IO.Directory]::CreateDirectory($Directory) | Out-Null
    $previousNames = @(Get-ManagedNames $Directory)
    $skillsByName = @{}
    foreach ($source in $Sources) {
        $skillsByName[(Split-Path -Leaf $source)] = $source
    }
    $wantedNames = @($skillsByName.Keys | Sort-Object)
    foreach ($name in $wantedNames) {
        Sync-SkillCopy $Directory $name $skillsByName[$name]
    }
    foreach ($entry in Get-ChildItem -LiteralPath $Directory -Force) {
        if ($entry.Name -ieq $manifestName -or $entry.Name -in $wantedNames) { continue }
        if ($OwnsDirectory -or $entry.Name -in $previousNames -or (Test-Link $entry)) {
            Remove-SkillEntry $entry $Directory
        }
    }
    $manifestPath = Join-Path $Directory $manifestName
    $manifest = @{ skills = @($wantedNames) } | ConvertTo-Json
    [System.IO.File]::WriteAllText($manifestPath, $manifest, (New-Object System.Text.UTF8Encoding($false)))
}

function Sync-BaseSkills {
    if (-not (Test-Path -LiteralPath $baseSkillPath -PathType Container)) {
        throw "Base skill directory not found: $baseSkillPath"
    }
    $sources = @(Get-ChildItem -LiteralPath $baseSkillPath -Directory |
        Sort-Object Name | ForEach-Object { $_.FullName })
    Sync-SkillDirectory $baseSkillDirectory $sources -OwnsDirectory
}

function Get-SkillDirectories {
    param([string]$Root, [switch]$FollowLinks, [switch]$ExcludeBase)

    $pending = New-Object 'System.Collections.Generic.Stack[string]'
    $visited = New-Object 'System.Collections.Generic.HashSet[string]' ([StringComparer]::OrdinalIgnoreCase)
    $pending.Push($Root)
    while ($pending.Count -gt 0) {
        $path = $pending.Pop()
        $directory = Get-Item -LiteralPath $path -Force
        $identity = $directory.FullName
        if (Test-Link $directory) {
            $identity = Get-LinkDestination $directory
        }
        if (-not $visited.Add($identity)) { continue }

        $entries = @(Get-ChildItem -LiteralPath $path -Force)
        $skillFiles = @($entries | Where-Object {
            -not $_.PSIsContainer -and $_.Name -ieq 'SKILL.md' -and
            ($FollowLinks -or -not (Test-Link $_))
        })
        if ($skillFiles.Count -gt 0) {
            $path
        }
        foreach ($entry in $entries) {
            if (-not $entry.PSIsContainer) { continue }
            if ($ExcludeBase -and $entry.FullName -ieq (Join-Path $sourceDirectory 'base')) { continue }
            if ((Test-Link $entry) -and -not $FollowLinks) { continue }
            if (-not (Test-Path -LiteralPath $entry.FullName -PathType Container)) { continue }
            $pending.Push($entry.FullName)
        }
    }
}

function Get-AllSkills {
    $paths = @(
        Get-SkillDirectories $sourceDirectory -ExcludeBase
        Get-SkillDirectories $baseSkillDirectory -FollowLinks
    )
    return $paths | Sort-Object -Unique
}

function Show-SkillDirectory {
    param([string]$Directory)

    Get-ChildItem -LiteralPath $Directory -Force |
        Select-Object Mode, Name |
        Format-Table -AutoSize | Out-Host
}

Write-Status "workdir: $(Get-DisplayPath $sourceDirectory)" Green
Write-Status 'platform: windows' Green

if ($Operation -eq 'sync') {
    Write-Status "==> $(Get-DisplayPath $baseSkillDirectory)" Cyan
}
Sync-BaseSkills
$skills = @(Get-AllSkills)

if ($Operation -eq 'show') {
    Write-Status "src_dir: $(Get-DisplayPath $sourceDirectory)" Green
    Write-Status "base_skill_path: $(Get-DisplayPath $baseSkillPath)" Green
    Write-Status 'target_dirs:'
    foreach ($targetDirectory in $targetDirectories) {
        Write-Status "  - $(Get-DisplayPath $targetDirectory)" Green
    }
    Write-Status 'skills:'
    foreach ($skill in $skills) {
        Write-Status "  - $(Get-DisplayPath $skill)" Magenta
    }
    return
}

Show-SkillDirectory $baseSkillDirectory
foreach ($targetDirectory in $targetDirectories) {
    Write-Status "==> $(Get-DisplayPath $targetDirectory)" Cyan
    Sync-SkillDirectory $targetDirectory $skills
    Show-SkillDirectory $targetDirectory
}
