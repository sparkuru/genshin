@echo off
setlocal
cd /d "%~dp0"
set "TEMP=%~dp0temp"
set "TMP=%~dp0temp"
set "CRISPASR_CACHE_DIR=%~dp0cache\crispasr"
"%SystemRoot%\System32\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy Bypass -File "%~dp0app\debug-launch.ps1" %*
echo.
echo Live Subtitle exited. Logs: "%~dp0logs"
pause
endlocal
