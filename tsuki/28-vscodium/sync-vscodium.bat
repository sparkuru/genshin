@echo off
setlocal EnableExtensions EnableDelayedExpansion

if not defined HOME set "HOME=%USERPROFILE%"

set "REPO_ROOT=%~dp0"
set "TARGET_ROOT=%HOME%\AppData\Roaming\Apps\VSCodium"
set "USER_DIR=%TARGET_ROOT%\data\user-data\User"
set "EXTENSIONS_DIR=%TARGET_ROOT%\data\extensions"
set "CODIUM_BIN=%TARGET_ROOT%\bin\codium.cmd"
set "EXTENSION_FILE=%REPO_ROOT%config\extension.txt"

if not exist "%TARGET_ROOT%\VSCodium.exe" (

	echo Error: VSCodium was not found at "%TARGET_ROOT%".

	exit /b 1
)

if not exist "%EXTENSION_FILE%" (

	echo Error: Extension list was not found at "%EXTENSION_FILE%".

	exit /b 1
)

if not exist "%CODIUM_BIN%" (

	echo Error: VSCodium CLI was not found at "%CODIUM_BIN%".

	exit /b 1
)

if not exist "%USER_DIR%" mkdir "%USER_DIR%"
if errorlevel 1 exit /b 1

if not exist "%EXTENSIONS_DIR%" mkdir "%EXTENSIONS_DIR%"
if errorlevel 1 exit /b 1

copy /Y "%REPO_ROOT%config\settings.json" "%USER_DIR%\settings.json" >nul
if errorlevel 1 exit /b 1

copy /Y "%REPO_ROOT%config\keybindings.json" "%USER_DIR%\keybindings.json" >nul
if errorlevel 1 exit /b 1

set "INSTALLED_EXTENSIONS= "
for /f "usebackq delims=" %%E in (`call "%CODIUM_BIN%" --user-data-dir "%TARGET_ROOT%\data\user-data" --extensions-dir "%EXTENSIONS_DIR%" --list-extensions`) do set "INSTALLED_EXTENSIONS=!INSTALLED_EXTENSIONS!%%E "

set "INSTALL_FAILED=0"
for /f "usebackq tokens=* delims=" %%E in ("%EXTENSION_FILE%") do (

	for /f "tokens=1 delims=#" %%I in ("%%E") do (

		echo(!INSTALLED_EXTENSIONS!| findstr /I /L /C:" %%I " >nul

		if errorlevel 1 (

			call "%CODIUM_BIN%" --user-data-dir "%TARGET_ROOT%\data\user-data" --extensions-dir "%EXTENSIONS_DIR%" --install-extension "%%I"

			if errorlevel 1 set "INSTALL_FAILED=1"
		)
	)
)

if "%INSTALL_FAILED%"=="1" (

	echo Configuration synchronized, but one or more extensions could not be installed.

	exit /b 1
)

echo VSCodium configuration and extensions synchronized to "%TARGET_ROOT%".
