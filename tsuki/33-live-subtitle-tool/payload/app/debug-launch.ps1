param([switch]$SelfTest)
$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
$logPath = Join-Path $root 'logs\live-subtitle.log'
$settings = Get-Content -LiteralPath (Join-Path $root 'config\settings.json') -Raw | ConvertFrom-Json
Write-Host "Live Subtitle Tool v2.1 Portable | Vulkan | $($settings.gpu_name)"
Write-Host "Configuration: $(Join-Path $root 'config\settings.json')"
Write-Host "Live log: $logPath"
$offset = 0L
if (Test-Path -LiteralPath $logPath) { $offset = (Get-Item -LiteralPath $logPath).Length }
if ($SelfTest) {
    $process = Start-Process -FilePath (Join-Path $root 'LiveSubtitle.exe') -ArgumentList '--self-test' -WorkingDirectory $root -WindowStyle Hidden -PassThru
} else {
    $process = Start-Process -FilePath (Join-Path $root 'LiveSubtitle.exe') -WorkingDirectory $root -WindowStyle Hidden -PassThru
}
$reader = $null
try {
    while (-not $process.HasExited) {
        if ($null -eq $reader -and (Test-Path -LiteralPath $logPath)) {
            $stream = [IO.File]::Open($logPath, [IO.FileMode]::Open, [IO.FileAccess]::Read, [IO.FileShare]::ReadWrite)
            if ($stream.Length -ge $offset) { [void]$stream.Seek($offset, [IO.SeekOrigin]::Begin) }
            $reader = New-Object IO.StreamReader($stream, [Text.Encoding]::UTF8)
        }
        if ($null -ne $reader) {
            while ($null -ne ($line = $reader.ReadLine())) {
                if ($line -match '(?i)(^20\d\d-|vulkan|offloaded|buffer size|error|warning|initiali)') { Write-Host $line }
            }
        }
        Start-Sleep -Milliseconds 200
        $process.Refresh()
    }
    if ($null -ne $reader) {
        while ($null -ne ($line = $reader.ReadLine())) {
            if ($line -match '(?i)(^20\d\d-|vulkan|offloaded|buffer size|error|warning|initiali)') { Write-Host $line }
        }
    }
    Write-Host "Exit code: $($process.ExitCode)"
} finally {
    if ($null -ne $reader) { $reader.Dispose() }
}
