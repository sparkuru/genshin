$OutputEncoding = [console]::InputEncoding = [console]::OutputEncoding = New-Object System.Text.UTF8Encoding    # english use utf-8
$OutputEncoding = [console]::InputEncoding = [console]::OutputEncoding = [System.Text.Encoding]::GetEncoding(936)   # chinese change to utf-8 handly

$lang_base_path = "d:/lang"
$bin_base_path = "d:/bin"
$software_base_path = "d:/software"
$sec_base_path = "d:/sec"
$project_base_path = "d:/project"

# app export
###################### lang ######################
$GRADLEPATH = "$lang_base_path/java/gradle-8.7/bin"
$MINGW64PATH = "$lang_base_path/mingw64/bin"
$NODEJSPATH = "$lang_base_path/node"

$env:PATH += "$GRADLEPATH;" + `
"$MINGW64PATH;" + `
"$NODEJSPATH;"

$env:PIP_DOWNLOAD_CACHE = "$lang_base_path/python/pip-cache"

###################### bin ######################
$BTOPPATH = "$bin_base_path/btop4win"
$FDPATH = "$bin_base_path/fd"
$FFMPEGPATH = "$bin_base_path/ffmpeg"
$FZFPATH = "$bin_base_path/fzf"
$GITPATH = "$bin_base_path/git/cmd"
$NMAPPATH = "$bin_base_path/nmap"
$RIPGREPPATH = "$bin_base_path/ripgrep"
$TREEPATH = "$bin_base_path/tree/bin"
$VIMPATH = "$bin_base_path/vim/vim90"

$env:PATH += "$BTOPPATH;" + `
"$FDPATH;" + `
"$FFMPEGPATH;" + `
"$FZFPATH;" + `
"$GITPATH;" + `
"$NMAPPATH;" + `
"$RIPGREPPATH;" + `
"$TREEPATH;" + `
"$VIMPATH;"

$env:GIT_EDITOR = "$VIMPATH/vim.exe"
$env:FZF_DEFAULT_COMMAND = "rg --files"
$env:FZF_DEFAULT_OPTS="-m --height 40% --reverse --border --ansi"

###################### software ######################
$NOTEPAD4PATH = "$software_base_path/notepad4"
$POTPLAYERPATH = "$software_base_path/potplayer"
$SUMATRAPATH = "$software_base_path/sumatra-pdf"
$TYPORAPATH = "$software_base_path/typora"
$XNVIEWPATH = "$software_base_path/xnview"

$env:PATH += "$NOTEPAD4PATH;" + `
"$POTPLAYERPATH;" + `
"$SUMATRAPATH;" + `
"$TYPORAPATH;" + `
"$XNVIEWPATH;"

Set-Alias play PotPlayerMini64
Set-Alias np Notepad4
Set-Alias pdf sumatrapdf
Set-Alias img xnviewmp

###################### sec ######################
$ADBPATH = "$sec_base_path/android/android-platform-tool"
$BURPSUITEPATH = "$sec_base_path/burpsuite"
$FRIDAPATH = "$sec_base_path/frida"
$IDAPATH = "$sec_base_path/ida"
$JADXPATH = "$sec_base_path/jadx"
$MOBAXTERMPATH = "$sec_base_path/mobaxterm-portable"
$WINHEXPATH = "$sec_base_path/winhex"
$WIRESHARKPATH = "$sec_base_path/wireshark"

$env:PATH += "$ADBPATH;" + `
"$BURPSUITEPATH;" + `
"$FRIDAPATH;" + `
"$IDAPATH;" + `
"$JADXPATH;" + `
"$MOBAXTERMPATH;" + `
"$WINHEXPATH;" + `
"$WIRESHARKPATH;"

Set-Alias ida ida64
Set-Alias moba mobaxterm
Set-Alias winhex xwforensics64
Set-Alias wireshark WiresharkPortable64

# proxy export
$proxy_host = "127.0.0.1"
$proxy_port = "1080"
$env:http_proxy="http://${proxy_host}:${proxy_port}"
$env:https_proxy="http://${proxy_host}:${proxy_port}"

# cancle native alias
Remove-Item Alias:ls

# Alias diy
Set-Alias touch ni
Set-Alias grep findstr
Set-Alias p ipython
Set-Alias mgmt compmgmt.msc
Set-Alias reg regedit

# diy script
function poweroff { Stop-Computer }
function reboot { Restart-Computer }

$project_genshin_path = "$project_base_path/04-flyMe2theStar/03-genshin"
function password { python $project_genshin_path/code/python/08-password-generator.py $args }
function rename { python $project_genshin_path/code/python/14-interact-rename.py $args}
function encrypt { python $project_genshin_path/code/python/02-ez-encrypt.py $args }
function cx { python $project_genshin_path/code/python/09-ip-status.py $args }
function ftp { python $project_genshin_path/code/python/16-fast-ftp-server.py $args }
function l { python $project_genshin_path/code/python/12-ls-alh.py $args --level 0 }
function ls { python $project_genshin_path/code/python/12-ls-alh.py $args --level 0  }
function ll { python $project_genshin_path/code/python/12-ls-alh.py $args }
function la { python $project_genshin_path/code/python/12-ls-alh.py $args --all }
function lt { python $project_genshin_path/code/python/12-ls-alh.py $args -s time }
function lss { python $project_genshin_path/code/python/12-ls-alh.py $args -s size }

function genshin { ssh genshin-wkyuu }
function pve { ssh pve-wkyuu }
function schale { ssh schale-wkyuu }

function hash { certutil -hashfile $args }
function tree { & "$TREEPATH/tree.exe" -N -h $args }
function geek { & "$bin_base_path/geek.exe" }
function env { Start-Process powershell "-Command & {rundll32 sysdm.cpl,EditEnvironmentVariables}" -Verb RunAs }
function magnet { echo magnet:?xt=urn:btih:$args }
function code { & $software_base_path/visual-studio-code/binary/Code.exe --extensions-dir "$software_base_path/visual-studio-code/extension" $args }
function rmrf { Remove-Item -Recurse -Force $args }
function xpath {
    $convertedPath = $args -replace '\\', '/'
    Write-Host $convertedPath -ForegroundColor Yellow
}
function exp { 
    if ($args[0]) {
        $convertedPath = $args[0] -replace '/', '\'
        & explorer $convertedPath
    } else {
        & explorer .
    }
}
function print_old_dir {
    $old_dir = Get-Location
    Write-Host "old pwd > $old_dir" -ForegroundColor Blue
}
function home {
    & print_old_dir
    $home_path = "c:/users/wkyuu/desktop"
    Set-Location -Path $home_path
}
function tmp {
    & print_old_dir
    $tmp_path = "e:/"
    if (Test-Path $tmp_path) {
        $path = Join-Path -Path $tmp_path -ChildPath "tmp"
        if (-Not (Test-Path $path)) {
            New-Item -ItemType Directory -Path $path
        }
        Set-Location -Path $path
    } else {
        $tmp_path = "d:/"   
        if (Test-Path $tmp_path) {
            $path = Join-Path -Path $tmp_path -ChildPath "tmp"
            if (-Not (Test-Path $path)) {
                New-Item -ItemType Directory -Path $path
            }
            Set-Location -Path $path
        } else {
            Write-Host "no tmp path found" -ForegroundColor Red
        }
    }
}
function lcd {
    $script_path = "$project_genshin_path/code/python/13-lcd.py"
    
    if ($args[0] -eq "cd" -and $args[1]) {
        $targetDir = python $script_path -pn $args[1] | Select-String -Pattern '([A-Za-z]:\/[^\r\n]+)' | ForEach-Object { $_.Matches[0].Value }
        Set-Location $targetDir
    } elseif ($args[0] -eq "l") {
        python $script_path -l
    } elseif ($args[0] -eq "d" -and $args[1]) {
        python $script_path -d -n $args[1]
    } elseif ($args[0] -eq "a" -and $args[1]) {
        python $script_path -a $args[1]
    } else {
        python $script_path $args
    }
}
# wsl
function kali {
    $shell = New-Object -ComObject WScript.Shell
    $running = Get-WmiObject Win32_Process | Where-Object { $_.Name -eq "wsl.exe" } | Select-Object -ExpandProperty CommandLine
    if ($running -like "*kali*") {
        wsl --distribution kali
    } else {
        $shell.Run("wsl --distribution kali", 0)
        Write-Host "Starting AMD 14900k + Windows 11 instance in background." -ForegroundColor Yellow
    }
}
function kalidown {
    $running = Get-WmiObject Win32_Process | Where-Object { $_.Name -eq "wsl.exe" } | Select-Object -ExpandProperty CommandLine
    if ($running -like "*kali*") {
        wsl --shutdown kali
        Write-Host "shutting down AMD 14900k + Windows 11 instance." -ForegroundColor Yellow
        $service = Get-Service -Name "WSLKaliService" -ErrorAction SilentlyContinue
        if ($service) {
            Stop-Service -Name "WSLKaliService"
            Write-Host "WSL Kali service stopped." -ForegroundColor Yellow
        }
    } else {
        Write-Host "no AMD 14900k + Windows 11 instance running, type kali to start one." -ForegroundColor Yellow
    }
}
function k {
    $running = Get-WmiObject Win32_Process | Where-Object { $_.Name -eq "wsl.exe" } | Select-Object -ExpandProperty CommandLine
    if ($running -like "*kali*") {
        wsl zsh -l -c "~/.genshin/call-bridge.sh $args"
    } else {
        & kali
        Write-Host "run you cmd after kali started." -ForegroundColor Yellow
    }
}
# frida
function frida {
    if ($env:VIRTUAL_ENV -and (python -c "import sys; print(sys.prefix == sys.base_prefix)")) {
        & "$FRIDAPATH/venv-frida/Scripts/frida.exe" $args
    } else {
        $currentPath = Get-Location
        Set-Location -Path $FRIDAPATH
        & "./venv-frida/Scripts/Activate"
        Write-Host "`n------------------------------------------------" -ForegroundColor Yellow
        Write-Host " Activated Frida venv environment | $FRIDAPATH" -ForegroundColor Yellow
        Write-Host " Type 'deactivate' to exit" -ForegroundColor Yellow
        Write-Host "------------------------------------------------`n" -ForegroundColor Yellow
        Set-Location -Path $currentPath
    }
}