@echo off
setlocal EnableExtensions
rem ---------------------------------------------------------------
rem  Phantom Blade Zero - launcher
rem  pbz\            game payload (platform\steam\PBZ.exe)
rem  scripts\state\  bypass state and backups
rem  enable_bypass.ps1 [-Revert]  HV bypass switch
rem ---------------------------------------------------------------
set "ROOT=%~dp0"
set "GAME=%ROOT%pbz"
set "EXE=%GAME%\platform\steam\PBZ.exe"

if not exist "%EXE%" (
  echo [x] not found: "%EXE%"
  echo     check pbz\ layout, then edit EXE in this file
  pause
  exit /b 1
)
if /i "%~1"=="--check" (
  echo [ok] %EXE%
  echo [i] bypass: run enable_bypass.ps1 as admin, reboot, then this file
  exit /b 0
)

rem Denuvo/HV bypass needs: TESTSIGNING on (or F7 -> disable DSE),
rem VBS/HVCI/Credential Guard off, Windows Hypervisor off.
sc query type= driver 2>nul | findstr /i "hyper simple" >nul && (
  echo [i] hypervisor driver still registered - leftovers from a previous run
)

pushd "%GAME%\platform\steam"
start "" "%EXE%"
popd
exit /b 0
