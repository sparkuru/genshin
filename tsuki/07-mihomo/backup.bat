@echo off
setlocal enabledelayedexpansion

REM ANSI colors (Windows 10+)
for /f %%a in ('echo prompt $E^| cmd /q /c') do set "ESC=%%a"
set "green=%ESC%[0;32m"
set "yellow=%ESC%[33m"
set "red=%ESC%[31m"
set "nc=%ESC%[0m"

REM Script directory (no trailing backslash)
set "workdir=%~dp0"
if "!workdir:~-1!"=="\" set "workdir=!workdir:~0,-1!"

REM Walk up to find 03-genshin
set "current_dir=%workdir%"
set "genshin_dir_path="
set "target_dir_name=03-genshin"

:find_loop
for %%F in ("!current_dir!") do set "base_name=%%~nxF"
if "!base_name!"=="!target_dir_name!" (
    set "genshin_dir_path=!current_dir!"
    goto :found_genshin
)
for %%F in ("!current_dir!") do set "parent=%%~dpF"
if "!parent:~-1!"=="\" set "parent=!parent:~0,-1!"
if "!parent!"=="!current_dir!" goto :not_found
set "current_dir=!parent!"
goto :find_loop

:not_found
echo %target_dir_name% directory not found
exit /b 1

:found_genshin
set "encrypt_script_path=!genshin_dir_path!\code\python\02-ez-encrypt.py"
set "salt_path=!genshin_dir_path!\paimon"

REM Detect mihomo-party location
if exist "D:\software\mihomo-party" (
    set "src_file_path=D:\software\mihomo-party\data\profiles\192281f8f10.yaml"
) else (
    echo !red!mihomo-party not found!nc!
    exit /b 1
)

set "target_file_path=!workdir!\magic.yaml"
set "src_file_dir=\path\to\src\file\dir"
set "target_file_dir=\path\to\target\file\dir"

echo workdir: !green!!workdir!!nc!
echo genshin_dir_path: !green!!genshin_dir_path!!nc!

REM Parse arguments
set "encrypt_key="
set "operation="

:parse_args
if "%~1"=="" goto :end_parse
if "%~1"=="-k"      ( set "encrypt_key=%~2" & shift & shift & goto :parse_args )
if "%~1"=="--key"   ( set "encrypt_key=%~2" & shift & shift & goto :parse_args )
if "%~1"=="enc"     ( set "operation=enc"   & shift & goto :parse_args )
if "%~1"=="dec"     ( set "operation=dec"   & shift & goto :parse_args )
if "%~1"=="show"    ( set "operation=show"  & shift & goto :parse_args )
echo Unknown option: %~1
echo usage: %~nx0 {enc^|dec^|show} [-k^|--key ^<key^>]
exit /b 1

:end_parse
if "!operation!"=="" (
    echo usage: %~nx0 {enc^|dec^|show} [-k^|--key ^<key^>]
    exit /b 1
)

if "!operation!"=="enc"  goto :do_encrypt
if "!operation!"=="dec"  goto :do_decrypt
if "!operation!"=="show" goto :do_show
goto :eof

:do_encrypt
if "!encrypt_key!"=="" (
    python "!encrypt_script_path!" -i "!src_file_path!" -o "!target_file_path!" -s "!salt_path!" enc
) else (
    python "!encrypt_script_path!" -i "!src_file_path!" -o "!target_file_path!" -s "!salt_path!" -k "!encrypt_key!" enc
)
goto :eof

:do_decrypt
if "!encrypt_key!"=="" (
    python "!encrypt_script_path!" -i "!target_file_path!" -o "!src_file_path!" dec
) else (
    python "!encrypt_script_path!" -i "!target_file_path!" -o "!src_file_path!" -k "!encrypt_key!" dec
)
goto :eof

:do_show
echo encrypt_script_path: !green!!encrypt_script_path!!nc!
echo salt_path:           !green!!salt_path!!nc!
echo src_file_path:       !green!!src_file_path!!nc!
echo target_file_path:    !green!!target_file_path!!nc!
echo src_file_dir:        !green!!src_file_dir!!nc!
echo target_file_dir:     !green!!target_file_dir!!nc!
if "!encrypt_key!"=="" (
    echo encrypt_key:         !yellow!(not specified)!nc!
) else (
    echo encrypt_key:         !green!!encrypt_key!!nc!
)
goto :eof
