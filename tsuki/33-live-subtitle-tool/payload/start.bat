@echo off
setlocal
cd /d "%~dp0"
set "TEMP=%~dp0temp"
set "TMP=%~dp0temp"
set "CRISPASR_CACHE_DIR=%~dp0cache\crispasr"
start "" "%~dp0LiveSubtitle.exe" %*
endlocal
