<#
  Phantom Blade Zero - HV bypass switch

  Enable  : disables everything that keeps the ARTIFACT hypervisor from loading
            (Windows Hypervisor, VSM, VBS, HVCI, Credential Guard, KVA shadow,
            AVX-512 exposure) and turns on TESTSIGNING so the test-signed
            hyperkd.sys / SimpleSvm.sys can load.  Reboot required.

  Revert  : attempts to restore values recorded in its own backup file.
            Reboot required; recorded values may be incomplete after a failure.

  Original BCD and registry values are recorded in the solution workspace
  when run from its scripts directory, or in <root>\scripts\state when
  deployed to the game root.

  Run elevated.  -WhatIf only prints the plan.
#>
[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [switch]$Revert,
    [switch]$Force,
    [string]$StateDir
)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $StateDir) {
    $StateDir = Join-Path $root 'scripts\state'
    if ((Split-Path -Leaf $root) -ieq 'scripts') {
        $projectRoot = Split-Path -Parent $root
        $projectManifest = Join-Path $projectRoot 'artifacts.json'
        if (Test-Path -LiteralPath $projectManifest -PathType Leaf) {
            $StateDir = Join-Path $projectRoot 'workspace\state'
        }
    }
}
$stamp  = Get-Date -Format 'yyyyMMdd-HHmmss'
$stateFile = Join-Path $StateDir ("bypass-{0}.json" -f $stamp)

function Test-Admin {
    $id = [Security.Principal.WindowsIdentity]::GetCurrent()
    (New-Object Security.Principal.WindowsPrincipal $id).IsInRole(
        [Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Elevate {
    $psi = @{
        FilePath     = 'powershell.exe'
        Verb         = 'RunAs'
        ArgumentList = @('-NoProfile','-ExecutionPolicy','Bypass','-File',"`"$PSCommandPath`"") + $args
    }
    Start-Process @psi
}

if (-not (Test-Admin)) {
    if ($WhatIfPreference) {
        Write-Host '[x] run -WhatIf from an elevated PowerShell to read the complete state'
        exit 1
    }
    Write-Host '[i] requesting elevation...'
    $forwardArgs = @()
    if ($Revert) { $forwardArgs += '-Revert' }
    if ($Force) { $forwardArgs += '-Force' }
    if ($PSBoundParameters.ContainsKey('StateDir')) {
        $forwardStateDir = $ExecutionContext.SessionState.Path.GetUnresolvedProviderPathFromPSPath($StateDir)
        if ($forwardStateDir.EndsWith('\')) { $forwardStateDir += '.' }
        $forwardArgs += @('-StateDir', ('"{0}"' -f $forwardStateDir))
    }
    Elevate @forwardArgs
    exit
}

if (-not $WhatIfPreference) {
    [void][IO.Directory]::CreateDirectory($StateDir)
    [void][IO.Directory]::CreateDirectory((Join-Path $StateDir 'backup'))
}

function Reg-Root([string]$path) {
    $hive, $sub = $path -split '\\', 2
    $root = switch ($hive.ToUpper()) {
        'HKLM' { [Microsoft.Win32.Registry]::LocalMachine }
        'HKCU' { [Microsoft.Win32.Registry]::CurrentUser }
        default { throw "unsupported hive: $hive" }
    }
    [pscustomobject]@{ Root = $root; Sub = $sub }
}

function Reg-Get([string]$path, [string]$name) {
    $r = Reg-Root $path
    $k = $r.Root.OpenSubKey($r.Sub)
    if (-not $k) { return $null }
    try {
        if ($k.GetValueNames() -notcontains $name) { return $null }
        [pscustomobject]@{ Value = $k.GetValue($name); Kind = $k.GetValueKind($name).ToString() }
    } finally { $k.Close() }
}

function Reg-Set([string]$path, [string]$name, $value, [string]$kind = 'DWord') {
    if ($WhatIfPreference) { Write-Verbose "whatif: reg set $path\$name = $value"; return }
    $r = Reg-Root $path
    $k = $r.Root.CreateSubKey($r.Sub)
    try { $k.SetValue($name, $value, [Microsoft.Win32.RegistryValueKind]::$kind) } finally { $k.Close() }
}

function Reg-Del([string]$path, [string]$name) {
    if ($WhatIfPreference) { Write-Verbose "whatif: reg del $path\$name"; return }
    $r = Reg-Root $path
    $k = $r.Root.OpenSubKey($r.Sub, $true)
    if (-not $k) { return }
    try { $k.DeleteValue($name, $false) } finally { $k.Close() }
}

function Bcd-Get([string]$setting) {
    $out = & bcdedit /enum '{current}' 2>$null
    foreach ($line in $out) {
        if ($line -match "^\s*$([regex]::Escape($setting))\s+(\S+)") { return $Matches[1] }
    }
    return $null
}

function Bcd-Del([string]$setting) {
    & bcdedit /deletevalue '{current}' $setting 2>$null | Out-Null
}

function Bcd-Set([string]$setting, [string]$value) {
    & bcdedit /set '{current}' $setting $value | Out-Null
    if ($LASTEXITCODE -ne 0) { throw "bcdedit /set $setting $value failed ($LASTEXITCODE)" }
}

# ---------------------------------------------------------------- collect plan
$changes = New-Object System.Collections.Generic.List[object]
function Plan([string]$what, [scriptblock]$do) { $changes.Add([pscustomobject]@{ What = $what; Do = $do }) }

# 1. Windows Hypervisor (must be off or the ARTIFACT VMM cannot take VMX/SVM root)
$hv = Bcd-Get 'hypervisorlaunchtype'
if ($hv -and $hv -notmatch '^off$') {
    Plan "bcdedit hypervisorlaunchtype: $hv -> off" { Bcd-Set 'hypervisorlaunchtype' 'off' }
}

# 2. Virtual Secure Mode
$vsm = Bcd-Get 'vsmlaunchtype'
if ($vsm -and $vsm -match '^(auto|on)$') {
    Plan "bcdedit vsmlaunchtype: $vsm -> Off" { Bcd-Set 'vsmlaunchtype' 'Off' }
}

# 3. VBS / HVCI / Credential Guard registry
$dg  = 'HKLM\SYSTEM\CurrentControlSet\Control\DeviceGuard'
$dgs = "$dg\Scenarios"
$hvci = "$dgs\HypervisorEnforcedCodeIntegrity"
$cg   = "$dgs\CredentialGuard"
$lsa  = 'HKLM\SYSTEM\CurrentControlSet\Control\Lsa'

foreach ($pair in @(
    @{ Path = $dg;   Name = 'EnableVirtualizationBasedSecurity' },
    @{ Path = $hvci; Name = 'Enabled' },
    @{ Path = $lsa;  Name = 'LsaCfgFlags' }
)) {
    $cur = Reg-Get $pair.Path $pair.Name
    $shown = if ($cur) { "$($cur.Value)" } else { '(absent)' }
    if (-not $cur -or "$($cur.Value)" -ne '0') {
        $p = $pair.Path; $n = $pair.Name
        Plan "registry $p\$n = $shown -> 0" ({ Reg-Set $p $n 0 }.GetNewClosure())
    }
}
$sg = "$dgs\SystemGuard"
$sgv = Reg-Get $sg 'Enabled'
if ($sgv -and "$($sgv.Value)" -ne '0') {
    Plan "registry $sg\Enabled = $($sgv.Value) -> 0" ({ Reg-Set $sg 'Enabled' 0 }.GetNewClosure())
}
$rpsf = Reg-Get $dg 'RequirePlatformSecurityFeatures'
if ($rpsf) {
    Plan "registry $dg\RequirePlatformSecurityFeatures = $($rpsf.Value) -> delete" ({ Reg-Del $dg 'RequirePlatformSecurityFeatures' }.GetNewClosure())
}
$cgv = Reg-Get $cg 'Enabled'
if ($cgv -and "$($cgv.Value)" -ne '0') {
    Plan "registry $cg\Enabled = $($cgv.Value) -> 0" ({ Reg-Set $cg 'Enabled' 0 }.GetNewClosure())
}

# 4. KVA shadow override (conflicts with the syscall hook)
$mm = 'HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Memory Management'
$fso  = Reg-Get $mm 'FeatureSettingsOverride'
$fsom = Reg-Get $mm 'FeatureSettingsOverrideMask'
if (-not ($fso -and "$($fso.Value)" -eq '2' -and $fsom -and "$($fsom.Value)" -eq '3')) {
    Plan 'registry Memory Management\FeatureSettingsOverride = 2 / Mask = 3' {
        Reg-Set $mm 'FeatureSettingsOverride' 2
        Reg-Set $mm 'FeatureSettingsOverrideMask' 3
    }
}

# 5. Remove AVX-512 exposure for the session.
$xsave = Bcd-Get 'xsaveremovefeature'
$xsaveWant = [uint64]::Parse('18446744073709551608')   # 0xFFFFFFFFFFFFFFF8
$xsaveCur = $null
if ($xsave) {
    try { $xsaveCur = [uint64]$xsave } catch {
        try { $xsaveCur = [Convert]::ToUInt64(($xsave -replace '^0x',''), 16) } catch { $xsaveCur = $null }
    }
}
if ($xsaveCur -ne $xsaveWant) {
    Plan "bcdedit xsaveremovefeature: $xsave -> 0xFFFFFFFFFFFFFFF8" {
        Bcd-Set 'xsaveremovefeature' '0xFFFFFFFFFFFFFFF8'
    }
}

# 6. DSE: TESTSIGNING when Secure Boot is off, otherwise one-time F7 route
$sb = $null
try { $sb = Confirm-SecureBootUEFI } catch { $sb = $null }
$mode = ''
if ($sb -eq $false -or $null -eq $sb) {
    # Secure Boot off -> permanent TESTSIGNING, no boot menu detour
    $mode = 'TESTSIGNING'
    if ((Bcd-Get 'testsigning') -notmatch '^Yes$') {
        Plan 'bcdedit testsigning on (Secure Boot off -> permanent test signing)' { Bcd-Set 'testsigning' 'on' }
    }
    if (Bcd-Get 'onetimeadvancedoptions') {
        Plan 'bcdedit /deletevalue onetimeadvancedoptions (no longer needed)' { Bcd-Del 'onetimeadvancedoptions' }
    }
    if ((Bcd-Get 'bootmenupolicy') -ne 'Standard') {
        Plan 'bcdedit bootmenupolicy Standard' { Bcd-Set 'bootmenupolicy' 'Standard' }
    }
} else {
    # Secure Boot on -> testsigning is locked by firmware policy, one-shot F7 route
    $mode = 'F7'
    if ((Bcd-Get 'onetimeadvancedoptions') -notmatch '^Yes$') {
        Plan 'bcdedit onetimeadvancedoptions on (Secure Boot on -> F7 at boot)' { Bcd-Set 'onetimeadvancedoptions' 'on' }
    }
    if ((Bcd-Get 'bootmenupolicy') -ne 'Standard') {
        Plan 'bcdedit bootmenupolicy Standard' { Bcd-Set 'bootmenupolicy' 'Standard' }
    }
}

# 7. BitLocker: suspend for one reboot so the F7 route does not ask for the key
try {
    $bl = Get-BitLockerVolume -MountPoint $env:SystemDrive -ErrorAction Stop
    if ($bl.ProtectionStatus -eq 'On') {
        Plan "BitLocker on $env:SystemDrive -> suspend one reboot" {
            Suspend-BitLocker -MountPoint $env:SystemDrive -RebootCount 1 | Out-Null
        }
    }
} catch { }

# ------------------------------------------------------------------- revert path
if ($Revert) {
    $latest = Get-ChildItem -LiteralPath $StateDir -Filter 'bypass-*.json' -File |
              Sort-Object LastWriteTime -Descending | Select-Object -First 1
    if (-not $latest) { Write-Host '[x] no bypass-*.json state file found'; exit 1 }
    $state = Get-Content -LiteralPath $latest.FullName -Raw | ConvertFrom-Json
    Write-Host "[i] reverting from $($latest.Name)"
    foreach ($r in $state.Records) {
        if ($PSCmdlet.ShouldProcess($r.Target, "restore $($r.Name) = $($r.OldValue)")) {
            if ($r.Kind -eq 'Bcd') {
                if ($r.OldValue) { & bcdedit /set '{current}' $r.Name $r.OldValue | Out-Null }
                else { & bcdedit /deletevalue '{current}' $r.Name 2>$null | Out-Null }
            } elseif ($null -eq $r.OldValue) {
                Reg-Del $r.Target $r.Name
            } else {
                Reg-Set $r.Target $r.Name $r.OldValue $r.Kind
            }
        }
    }
    if ($WhatIfPreference) { Write-Host '[i] revert preview only - no changes made' }
    else { Write-Host '[ok] reverted - reboot to apply' }
    exit 0
}

# ---------------------------------------------------------------------- execute
if ($changes.Count -eq 0) {
    Write-Host '[ok] nothing to change - bypass prerequisites already in place'
    exit 0
}

if ($WhatIfPreference) {
    foreach ($c in $changes) { [void]$PSCmdlet.ShouldProcess($c.What, 'apply') }
    Write-Host '[i] preview only - no changes or state files written'
    exit 0
}

$records = New-Object System.Collections.Generic.List[object]

# snapshot before touching anything (missing keys are not an error)
function Snapshot([string]$label, [scriptblock]$run) {
    $prev = $ErrorActionPreference
    $ErrorActionPreference = 'Continue'
    try { & $run } catch { Write-Host ("[w] snapshot {0}: {1}" -f $label, $_.Exception.Message) }
    $ErrorActionPreference = $prev
}
$bdir = Join-Path $StateDir 'backup'
Snapshot 'bcd'          { & bcdedit /enum all 2>$null | Set-Content -LiteralPath (Join-Path $bdir ("bcd-{0}.txt" -f $stamp)) }
Snapshot 'deviceguard'  { & reg export 'HKLM\SYSTEM\CurrentControlSet\Control\DeviceGuard' (Join-Path $bdir ("deviceguard-{0}.reg" -f $stamp)) /y 2>$null | Out-Null }
Snapshot 'lsa'          { & reg export 'HKLM\SYSTEM\CurrentControlSet\Control\Lsa' (Join-Path $bdir ("lsa-{0}.reg" -f $stamp)) /y 2>$null | Out-Null }

# Record original values for -Revert.
function Rec-Bcd([string]$name) {
    $old = Bcd-Get $name
    $records.Add([pscustomobject]@{ Kind = 'Bcd'; Target = '{current}'; Name = $name; OldValue = $old })
}
function Rec-Reg([string]$path, [string]$name) {
    $old = Reg-Get $path $name
    $records.Add([pscustomobject]@{
        Kind = if ($old) { "$($old.Kind)" } else { 'DWord' }
        Target = $path; Name = $name; OldValue = if ($old) { $old.Value } else { $null }
    })
}

Rec-Bcd 'hypervisorlaunchtype'
Rec-Bcd 'vsmlaunchtype'
Rec-Bcd 'xsaveremovefeature'
Rec-Bcd 'testsigning'
Rec-Bcd 'onetimeadvancedoptions'
Rec-Bcd 'bootmenupolicy'
Rec-Reg $dg   'EnableVirtualizationBasedSecurity'
Rec-Reg $dg   'RequirePlatformSecurityFeatures'
Rec-Reg $hvci 'Enabled'
Rec-Reg $sg   'Enabled'
Rec-Reg $lsa  'LsaCfgFlags'
Rec-Reg $cg   'Enabled'
Rec-Reg $mm   'FeatureSettingsOverride'
Rec-Reg $mm   'FeatureSettingsOverrideMask'

foreach ($c in $changes) {
    if ($PSCmdlet.ShouldProcess($c.What, 'apply')) {
        try   { & $c.Do; Write-Host ("[+] {0}" -f $c.What) }
        catch { Write-Host ("[x] {0} -> {1}" -f $c.What, $_.Exception.Message) }
    }
}

[pscustomobject]@{ Timestamp = $stamp; Root = $root; Records = $records } |
    ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $stateFile -Encoding UTF8

Write-Host ''
Write-Host "[i] state: $stateFile"
Write-Host "[i] DSE route: $mode"
Write-Host '[!] REBOOT now. Bypass is active only after the reboot.'
if ($mode -eq 'F7') {
    Write-Host '[!] Secure Boot is ON: testsigning is locked by firmware.'
    Write-Host '    Either disable Secure Boot in BIOS (permanent TESTSIGNING), or press F7 at the boot menu now.'
    Write-Host '    onetimeadvancedoptions is one-shot - re-arm it before every boot with:'
    Write-Host '        bcdedit /set {current} onetimeadvancedoptions on'
} else {
    Write-Host '[ok] Secure Boot off: TESTSIGNING stays on until -Revert.'
}
Write-Host '[i] after playing: run  enable_bypass.ps1 -Revert  and reboot.'
