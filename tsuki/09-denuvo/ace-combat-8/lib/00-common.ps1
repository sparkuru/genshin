# 00-common.ps1 —— 公共函数（被其它脚本 dot-source）
# 兼容 Windows PowerShell 5.1 / PowerShell 7+
# 此公共脚本位于 lib\；$PSScriptRoot 指向 lib\，父目录是方案根目录。

$global:KitRoot  = Split-Path -Parent $PSScriptRoot
$global:BackupRoot = Join-Path $global:KitRoot 'workspace\backups'
$global:LogRoot    = Join-Path $global:KitRoot 'workspace\logs'
$global:KitDryRun     = $false

foreach ($d in @($global:BackupRoot, $global:LogRoot)) {
    if (-not (Test-Path $d)) { New-Item -ItemType Directory -Path $d -Force | Out-Null }
}

$global:LogFile = Join-Path $global:LogRoot ('run-' + (Get-Date -Format 'yyyyMMdd-HHmmss') + '.log')

function Write-Log {
    param(
        [Parameter(Mandatory = $true)][string]$Message,
        [ValidateSet('INFO', 'OK', 'WARN', 'ERR', 'STEP')][string]$Level = 'INFO'
    )
    $map = @{ INFO = 'Cyan'; OK = 'Green'; WARN = 'Yellow'; ERR = 'Red'; STEP = 'Magenta' }
    Write-Host ('[{0}] {1}' -f $Level, $Message) -ForegroundColor $map[$Level]
    try { Add-Content -Path $global:LogFile -Value ('[{0}] [{1}] {2}' -f (Get-Date -Format 'HH:mm:ss'), $Level, $Message) -Encoding UTF8 } catch { }
}

function Test-Admin {
    $id = [Security.Principal.WindowsIdentity]::GetCurrent()
    $p  = New-Object Security.Principal.WindowsPrincipal($id)
    return $p.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Assert-Admin {
    if (-not (Test-Admin)) {
        Write-Log '需要管理员权限。请右键 PowerShell -> 以管理员身份运行，再执行本脚本。' 'ERR'
        exit 5
    }
}

# 执行一条命令（DryRun 时只打印）
function Invoke-Cmd {
    param(
        [Parameter(Mandatory = $true)][string]$Exe,
        [string[]]$ArgList = @()
    )
    $line = ('{0} {1}' -f $Exe, ($ArgList -join ' '))
    if ($global:KitDryRun) {
        Write-Log ('[DryRun] ' + $line) 'WARN'
        return [pscustomobject]@{ ExitCode = 0; Output = ''; DryRun = $true }
    }
    Write-Log ('执行: ' + $line) 'STEP'
    $out = & $Exe @ArgList 2>&1 | Out-String
    return [pscustomobject]@{ ExitCode = $LASTEXITCODE; Output = $out; DryRun = $false }
}

function Get-SecureBootState {
    try {
        if (Confirm-SecureBootUEFI) { return 'On' } else { return 'Off' }
    } catch {
        return 'UnknownOrLegacyBIOS'
    }
}

function Get-BcdCurrent {
    $out = & bcdedit /enum '{current}' 2>&1 | Out-String
    return $out
}

function Get-BcdValue {
    param([Parameter(Mandatory = $true)][string]$Name)
    $text = Get-BcdCurrent
    $m = [regex]::Match($text, ('(?im)^\s*' + [regex]::Escape($Name) + '\s+(\S+)\s*$'))
    if ($m.Success) { return $m.Groups[1].Value } else { return $null }
}

function Get-RegValue {
    param(
        [Parameter(Mandatory = $true)][string]$Path,
        [Parameter(Mandatory = $true)][string]$Name
    )
    try {
        $item = Get-ItemProperty -Path $Path -Name $Name -ErrorAction Stop
        return $item.$Name
    } catch {
        return $null
    }
}

function Get-CpuVendor {
    $p = (Get-CimInstance Win32_Processor -ErrorAction SilentlyContinue | Select-Object -First 1)
    if (-not $p) { return 'Unknown' }
    if ($p.Manufacturer -match 'AMD') { return 'AMD' }
    if ($p.Manufacturer -match 'Intel') { return 'Intel' }
    if ($p.Name -match 'AMD') { return 'AMD' }
    if ($p.Name -match 'Intel') { return 'Intel' }
    return 'Unknown'
}

function Get-VbsStatus {
    try {
        return Get-CimInstance -Namespace root\Microsoft\Windows\DeviceGuard -ClassName Win32_DeviceGuard -ErrorAction Stop
    } catch {
        return $null
    }
}

function Get-BitLockerState {
    try {
        $v = Get-BitLockerVolume -MountPoint 'C:' -ErrorAction Stop
        return ('{0} / protection={1} / {2}%' -f $v.VolumeStatus, $v.ProtectionStatus, $v.EncryptionPercentage)
    } catch {
        try {
            $raw = (& manage-bde -status C: 2>&1 | Out-String)
            if ($raw -match '转换状态|Conversion Status') {
                $line = ($raw -split "`r?`n" | Where-Object { $_ -match '转换状态|Conversion Status' } | Select-Object -First 1)
                return $line.Trim()
            }
            return 'Unavailable'
        } catch { return 'Unavailable' }
    }
}

function Get-GameExe {
    param([string]$GameDir)
    if (-not $GameDir) { $GameDir = 'D:\game\ac8' }
    $candidates = @(
        (Join-Path $GameDir 'Game\Binaries\Win64\AceCombat8.exe'),
        (Join-Path $GameDir 'AceCombat8.exe')
    )
    foreach ($c in $candidates) { if (Test-Path $c) { return $c } }
    $found = Get-ChildItem -Path $GameDir -Recurse -Filter 'AceCombat8.exe' -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($found) { return $found.FullName }
    return $null
}

function Backup-State {
    param([string]$Tag = 'before')
    $dir = Join-Path $global:BackupRoot ((Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + $Tag)
    New-Item -ItemType Directory -Path $dir -Force | Out-Null

    $bcd = Get-BcdCurrent
    Set-Content -Path (Join-Path $dir 'bcd-current.txt') -Value $bcd -Encoding UTF8
    Set-Content -Path (Join-Path $dir 'meta.txt') -Value @(
        ('time      = ' + (Get-Date -Format 'yyyy-MM-dd HH:mm:ss')),
        ('computer  = ' + $env:COMPUTERNAME),
        ('secureboot= ' + (Get-SecureBootState)),
        ('cpu       = ' + (Get-CpuVendor)),
        ('psversion = ' + $PSVersionTable.PSVersion.ToString())
    ) -Encoding UTF8

    $exports = @(
        @('HKLM\SYSTEM\CurrentControlSet\Control\DeviceGuard', 'DeviceGuard.reg'),
        @('HKLM\SYSTEM\CurrentControlSet\Control\Lsa', 'Lsa.reg'),
        @('HKLM\SOFTWARE\Policies\Microsoft\Windows Defender', 'DefenderPolicy.reg')
    )
    foreach ($e in $exports) {
        $target = Join-Path $dir $e[1]
        & reg export $e[0] $target /y *> $null
    }

    Write-Log ('备份完成: ' + $dir) 'OK'
    return $dir
}

function Show-Header {
    param([string]$Title)
    Write-Host ''
    Write-Host ('=' * 68) -ForegroundColor DarkGray
    Write-Host ('  ' + $Title) -ForegroundColor White
    Write-Host ('=' * 68) -ForegroundColor DarkGray
    Write-Log ('=== ' + $Title) 'STEP'
}
