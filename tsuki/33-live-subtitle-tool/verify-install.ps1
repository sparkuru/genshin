<#
.SYNOPSIS
Verify installed files, Vulkan enumeration, and optionally manually supplied models.
#>
[CmdletBinding()]
param(
    [string]$InstallDirectory,
    [switch]$FilesOnly,
    [switch]$CheckModels
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
if (-not $InstallDirectory) {
    $InstallDirectory = if ((Split-Path -Leaf $PSScriptRoot) -eq 'app') { Split-Path -Parent $PSScriptRoot } else { Join-Path $PSScriptRoot 'LiveSubtitle' }
}
$root = [IO.Path]::GetFullPath($InstallDirectory).TrimEnd('\')
$inventory = Get-Content -LiteralPath (Join-Path $root '.live-subtitle-portable.json') -Raw | ConvertFrom-Json
foreach ($entry in $inventory.files) {
    $path = [IO.Path]::GetFullPath((Join-Path $root $entry.file))
    if (-not $path.StartsWith($root + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Inventory path escapes installation directory.' }
    if ((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash -ne $entry.sha256) { throw "Installed file changed or damaged: $($entry.file)" }
}
Write-Host 'Installed program files: SHA256 verified.'
$settings = Get-Content -LiteralPath (Join-Path $root 'config\settings.json') -Raw | ConvertFrom-Json
if (-not $FilesOnly) {
    $savedVisible = $env:GGML_VK_VISIBLE_DEVICES
    try {
        Remove-Item Env:\GGML_VK_VISIBLE_DEVICES -ErrorAction SilentlyContinue
        $info = New-Object Diagnostics.ProcessStartInfo
        $info.FileName = Join-Path $root 'CrispASR\crispasr.exe'
        $info.Arguments = '--diagnostics'
        $info.WorkingDirectory = Join-Path $root 'CrispASR'
        $info.UseShellExecute = $false
        $info.CreateNoWindow = $true
        $info.RedirectStandardOutput = $true
        $info.RedirectStandardError = $true
        $process = [Diagnostics.Process]::Start($info)
        $stdout = $process.StandardOutput.ReadToEndAsync()
        $stderr = $process.StandardError.ReadToEndAsync()
        if (-not $process.WaitForExit(30000)) { $process.Kill(); throw 'CrispASR diagnostics timed out.' }
        $output = $stdout.Result + $stderr.Result
        $exitCode = $process.ExitCode
        $process.Dispose()
        [void](New-Item -ItemType Directory -Path (Join-Path $root 'logs') -Force)
        $output | Set-Content -LiteralPath (Join-Path $root 'logs\install-vulkan.log') -Encoding UTF8
        foreach ($line in ($output -split '\r?\n')) {
            if ($line -match '(?i)(version\s*:|git sha|arch\s*:|ggml backends|ggml_vulkan:|registered backends|registered devices|\] gpu|\] igpu)') { Write-Host $line }
        }
        if ($exitCode -ne 0) { throw "CrispASR diagnostics failed: $exitCode" }
        $deviceMatches = [regex]::Matches($output, 'ggml_vulkan:\s*(\d+)\s*=\s*(.+?)\s*\(')
        $gpu = @($deviceMatches | Where-Object { $_.Groups[2].Value.IndexOf($settings.gpu_name, [StringComparison]::OrdinalIgnoreCase) -ge 0 })
        if ($gpu.Count -eq 0) { throw "Configured Vulkan GPU not found: $($settings.gpu_name). Check AMD driver and config/settings.json; no CPU fallback." }
        Write-Host "Vulkan device $($gpu[0].Groups[1].Value): $($gpu[0].Groups[2].Value)"
        Write-Host 'Enumeration passed. Model GPU offload must still be checked during an actual subtitle session.'
    } finally {
        $env:GGML_VK_VISIBLE_DEVICES = $savedVisible
    }
}
$assets = Get-Content -LiteralPath (Join-Path $root 'config\assets.json') -Raw | ConvertFrom-Json
foreach ($model in $assets.models) {
    $path = Join-Path $root ('models\' + $model.file)
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) {
        if ($CheckModels) { throw "Model missing: $path" }
        Write-Host "Model not supplied: $($model.file) (no download attempted)."
    } elseif ($CheckModels) {
        if ((Get-Item -LiteralPath $path).Length -ne $model.size -or (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash -ne $model.sha256) { throw "Model checksum mismatch: $($model.file)" }
        Write-Host "Model SHA256 verified: $($model.file)"
    }
}
