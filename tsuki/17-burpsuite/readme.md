```bash
$ ./manage-burpsuite.sh uninstall -h                          
Usage:
  manage-burpsuite.sh install [--path <installation-directory>] [--force]
  manage-burpsuite.sh no-update [--path <installation-directory>] [--force]
  manage-burpsuite.sh uninstall [--path <installation-directory>]

Install Burp Suite Community, disable automatic updates, or uninstall it.

Commands:
  install       Download the official Community installer, install it, then apply no-update.
  no-update     Disable Burp automatic updates for this installation.
  uninstall     Run Burp's own unattended uninstaller; user data is preserved.

Options:
  --path <directory>  Installation directory (default: /home/wkyuu/.local/bin/burpsuite).
  --force             Replace an existing installation or managed no-update link.
  --help, -h          Show this help message.
  
$ ./manage-burpsuite.sh install     
是否安装到选中目录：/home/wkyuu/.local/bin/burpsuite [Y/n] n
installation cancelled

$ ./manage-burpsuite.sh install --path ~/cargo/bin/burpsuite
是否安装到选中目录：/home/wkyuu/cargo/bin/burpsuite [Y/n] y
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100  367M  100  367M    0     0  15.8M      0  0:00:23  0:00:23 --:--:-- 18.3M
Unpacking JRE ...
Starting Installer ...
The installation directory has been set to /home/wkyuu/cargo/bin/burpsuite.
Extracting files ...
Finishing installation ...
Burp Suite Community installation complete
Automatic Burp updates are disabled
  Launcher: /home/wkyuu/cargo/bin/burpsuite/BurpSuiteCommunity
```

