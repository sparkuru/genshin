<#
  Reshape the existing game installation into

    phantom-blade-zero\
      pbz\                  game payload (ProjectPBZ, platform, ...)
      scripts\state\        bypass state and backups
      enable_bypass.ps1
      start.bat

  Only known game entries are moved; unrelated files are left in place.
  -WhatIf prints the plan.
#>
[CmdletBinding(SupportsShouldProcess = $true)]
param(
    [string]$Root = 'D:\game\pbz'
)

$ErrorActionPreference = 'Stop'
$pbz     = Join-Path $Root 'pbz'
$scripts = Join-Path $Root 'scripts'

if (Get-Process PBZ -ErrorAction SilentlyContinue) {
    throw 'game is still running - close it before reorganizing'
}

New-Item -ItemType Directory -Force -Path $pbz, $scripts | Out-Null
New-Item -ItemType Directory -Force -Path (Join-Path $scripts 'state') | Out-Null

# Move only known game payload entries; leave other existing files in place.
$payloadNames = @('ProjectPBZ', 'platform', 'Engine', 'steam', 'steam_api64.dll')

Write-Host "[i] moving payload -> $pbz"
Get-ChildItem -LiteralPath $Root -Force | Where-Object { $payloadNames -contains $_.Name } | ForEach-Object {
    $dest = Join-Path $pbz $_.Name
    if ($PSCmdlet.ShouldProcess($_.FullName, "move -> $dest")) {
        Move-Item -LiteralPath $_.FullName -Destination $dest -Force
        Write-Host ("    {0}" -f $_.Name)
    }
}

# report what actually landed
$exe = Join-Path $pbz 'platform\steam\PBZ.exe'
Write-Host ''
Write-Host "[i] PBZ.exe: $(if (Test-Path -LiteralPath $exe) { 'OK  ' + $exe } else { 'MISSING' })"
$aj = Join-Path $pbz 'platform\steam\artifact.json'
if (Test-Path -LiteralPath $aj) {
    $j = Get-Content -LiteralPath $aj -Raw | ConvertFrom-Json
    Write-Host ("[i] artifact targets: {0}" -f ($j.targets -join ', '))
}
Write-Host ''
Get-ChildItem -LiteralPath $Root -Force | ForEach-Object { "{0}`t{1}" -f $_.Mode, $_.Name }
