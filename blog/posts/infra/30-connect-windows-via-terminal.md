---
title: "Connect to windows via terminal"
description: "introduce openssh server and winrm in windows."
date: "2026-09-12T17:15:43+08:00"
tags: []
draft: true
layout: "post"
slug: "connect-to-windows-via-terminal"
---

# Connect to windows via terminal

Need a ctrl tunnel like ssh? Then try WinRM

But honestly, on `Windows 10+`, you can just use the built-in OpenSSH Server.

I'd recommend that over WinRM.

## OpenSSH Server

Enable openssh server service and check the status, run the following cmds in powershell 6+ (with priv).

```powershell
# enable openssh server
$ Add-WindowsCapability -Online -Name OpenSSH.Server~~~~0.0.1.0 -Verbose
VERBOSE: 目标映像版本 10.0.26100.9445

Path          :
Online        : True
RestartNeeded : False
$ Start-Service sshd
$ Set-Service -Name sshd -StartupType Automatic

# (option) if you lagging in install, then try the offline way, https://github.com/PowerShell/Win32-OpenSSH.git
$ wget -O openssh.msi https://github.com/PowerShell/Win32-OpenSSH/releases/download/10.0.0.0p2-Preview/OpenSSH-Win64-v10.0.0.0.msi
$ msiexec /i ".\openssh.msi" ADDLOCAL=Server
```

Put your public key in `$HOME/.ssh/authorized_keys`, just like you normally would with an OpenSSH server on Unix.

However, if your account is a member of the `Administrators` group,

windows OpenSSH uses (refer to `C:\ProgramData\ssh\sshd_config:L87,L88`)

`C:\ProgramData\ssh\administrators_authorized_keys`

instead of

`~/.ssh/authorized_keys`

so put the key there instead.

Then try `ssh user@host`.

Default shell for openssh in windows is `cmd.exe`, change it to powershell via

```powershell
# findout your powershell execute path
$ $pwshPath = (Get-Command pwsh.exe -ErrorAction Stop).Source
# ensure reg string doesn't exist
$ New-Item -Path "HKLM:\SOFTWARE\OpenSSH" -Force | Out-Null

# append to reg
$ New-ItemProperty -Path "HKLM:\SOFTWARE\OpenSSH" -Name "DefaultShell" -Value $pwshPath -PropertyType String -Force
DefaultShell : C:\Program Files\PowerShell\7\pwsh.exe
PSPath       : Microsoft.PowerShell.Core\Registry::HKEY_LOCAL_MACHINE\SOFTWARE\OpenSSH
PSParentPath : Microsoft.PowerShell.Core\Registry::HKEY_LOCAL_MACHINE\SOFTWARE
PSChildName  : OpenSSH
PSDrive      : HKLM
PSProvider   : Microsoft.PowerShell.Core\Registry

# restart and check
$ Restart-Service sshd
$ Get-ItemProperty "HKLM:\SOFTWARE\OpenSSH" -Name DefaultShell
DefaultShell : C:\Program Files\PowerShell\7\pwsh.exe
PSPath       : Microsoft.PowerShell.Core\Registry::HKEY_LOCAL_MACHINE\SOFTWARE\OpenSSH
PSParentPath : Microsoft.PowerShell.Core\Registry::HKEY_LOCAL_MACHINE\SOFTWARE
PSChildName  : OpenSSH
PSDrive      : HKLM
PSProvider   : Microsoft.PowerShell.Core\Registry
```

If you are prefer to `cmd.exe`, recover with `Remove-ItemProperty -Path "HKLM:\SOFTWARE\OpenSSH" -Name "DefaultShell"`

## WinRM

To enable WinRM, run the following cmds in powershell 6+ (with priv).

### <center> enable winrm service and check the status </center>

```powershell
# enable winrm
$ Enable-PSRemoting -Force
WARNING: PowerShell remoting has been enabled only for PowerShell 6+ configurations and does not affect Windows PowerShell remoting configurations. Run this cmdlet in Windows PowerShell to affect all PowerShell remoting configurations.
在此计算机上设置了 WinRM 以接收请求。
在此计算机上设置了 WinRM 以进行远程管理。

# check winrm service
$ Get-Service WinRM
Status   Name               DisplayName
------   ----               -----------
Running  WinRM              Windows Remote Management (WS-Managem…

# check winrm status and config
$ winrm enumerate winrm/config/listener
Listener
    Address = *
    Transport = HTTP
    Port = 5985
    Hostname
    Enabled = true
    URLPrefix = wsman
    CertificateThumbprint
    ListeningOn = 127.0.0.1, 192.168.9.2, ...

# a local test in winrm service
$ Test-WSMan localhost
wsmid           : http://schemas.dmtf.org/wbem/wsman/identity/1/wsmanidentity.xsd
ProtocolVersion : http://schemas.dmtf.org/wbem/wsman/1/wsman.xsd
ProductVendor   : Microsoft Corporation
ProductVersion  : OS: 0.0.0 SP: 0.0 Stack: 3.0
```

check the connection in another device

```bash
$ nc -vz 192.168.9.2 5985
Connection to 192.168.9.2 5985 port [tcp/*] succeeded!
```

### <center> activate your account </center>

```powershell

# check your computer name and user
$ whoami
vxworks-dev\wkyuu

$ $env:COMPUTERNAME
VXWORKS-DEV

$ Get-LocalUser -Name wkyuu
Name  Enabled Description
----  ------- -----------
wkyuu True

# append yourself into the group
$ Get-LocalGroupMember "Remote Management Users"
$ Add-LocalGroupMember -Group "Remote Management Users" -Member "wkyuu"
$ Get-LocalGroupMember "Remote Management Users"
ObjectClass Name              PrincipalSource
----------- ----              ---------------
用户        VXWORKS-DEV\wkyuu MicrosoftAccount

```

### <center> connect to your windows </center>

Defaultly, the login password is NOT your Windows PIN (the password thar your use to log in when Windows starts up), it should be your Microsoft account password.

if you don't want to user you Microsoft account password, there are two way to replace the task.

#### <center> create a winrmuser to login </center>

```powershell
# create a windows localuser
$ $pwd = Read-Host "*************" -AsSecureString
*************:
$ $pwd
System.Security.SecureString

$ New-LocalUser -Name "winrmuser" -Password $pwd -Description "WinRM service account"
Name      Enabled Description
----      ------- -----------
winrmuser True    WinRM service account

# append it to the remote group
$ Add-LocalGroupMember -Group "Remote Management Users" -Member "winrmuser"
$ Get-LocalGroupMember "Remote Management Users"
ObjectClass Name                  PrincipalSource
----------- ----                  ---------------
用户        VXWORKS-DEV\winrmuser Local
用户        VXWORKS-DEV\wkyuu     MicrosoftAccount
```

then use the following info in `winrm.py`

```python
HOST = "192.168.9.2"
SESSION_URL = f"http://{HOST}:5985/wsman"
ACCOUNT = r"vxworks-dev\winrmuser"
PASSWORD = "****************"
```

#### <center> use PEM like ssh authorized_keys </center>

complex, refer to [Authentication for Remote Connections](https://learn.microsoft.com/en-us/windows/win32/winrm/authentication-for-remote-connections)

#### <center> try the script </center>

run `pip install winrm` to install the packages. then try the testing script.

```python
import winrm

HOST = "192.168.9.2"
SESSION_URL = f"http://{HOST}:5985/wsman"
ACCOUNT = r"vxworks-dev\wkyuu"
PASSWORD = "****************"

session = winrm.Session(
  SESSION_URL,
  auth=(ACCOUNT, PASSWORD),
  transport="ntlm",
)

result = session.run_cmd("whoami")

print(result.status_code)
print(result.std_out.decode("utf-8", errors="replace"))
print(result.std_err.decode("utf-8", errors="replace"))
```

### Disable the WinRM

You can use OpenSSH server in `Windows 10+`, ssh is better.

disable the WinRM via following cmds

```powershell
$ Stop-Service -Name WinRM
$ Set-Service -Name WinRM -StartupType Disabled
$ Get-NetFirewallRule -Name "WINRM*" Disable-NetFirewallRule


# check disable status
$ Get-Service WinRM
Status   Name               DisplayName
------   ----               -----------
Stopped  WinRM              Windows Remote Management (WS-Managem…
$ Get-NetTCPConnection -LocalPort 5985 -ErrorAction SilentlyContinue

# delete winrmuser account
$ Get-LocalUser -Name "winrmuser" -ErrorAction SilentlyContinue
Name      Enabled Description
----      ------- -----------
winrmuser True    WinRM service account
$ Remove-LocalUser -Name "winrmuser"
$ Get-LocalUser -Name "winrmuser" -ErrorAction SilentlyContinue
```

## refer

1. [Microsoft: Enable-PSRemoting](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.core/enable-psremoting?view=powershell-7.5)
2. [diyan/pywinrm](https://github.com/diyan/pywinrm.git)