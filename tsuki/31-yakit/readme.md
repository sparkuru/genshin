# Yakit

Install the latest Linux AppImage into a directory chosen by the user:

```bash
./install-yakit.sh --path $HOME/.local/yakit
```

The installer detects the host architecture, reads the latest Yakit version
from the official OSS mirror, downloads the matching AppImage, extracts it,
and links the adjusted `yakit.desktop` into
`~/.local/share/applications/`. The desktop entry launches the extracted
`AppRun` through a generated launcher so Yakit keeps the AppImage runtime
environment.

The generated launcher uses `$XDG_DATA_HOME/yakit` when `XDG_DATA_HOME` is an
absolute path, otherwise `$HOME/.local/share/yakit`, as both its working
directory and `YAKIT_HOME`. This keeps relative runtime directories such as
`yakit-project` and `build` out of the home-directory root. Set `YAKIT_HOME`
before launching `yakit-launcher` to override the default location. Reinstall
with `--force` to update an existing installation.

Use a specific release or a local AppImage when testing:

```bash
./install-yakit.sh --path $HOME/.local/yakit --version 1.4.8-0825
./install-yakit.sh --appimage /tmp/yakit-1.4.8-0825.AppImage --path $HOME/.local/yakit --force
```

Remove the installation and its managed desktop link:

```bash
./install-yakit.sh --uninstall --path $HOME/.local/yakit
```

Project: https://github.com/yaklang/yakit

---

```bash
$ ./install-yakit.sh --path ~/cargo/bin/yakit --force
Downloading Yakit 1.4.8-0825 (amd64)
  URL: https://oss-qn.yaklang.com/yak/1.4.8-0825/Yakit-1.4.8-0825-linux-amd64.AppImage
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100  232M  100  232M    0     0  34.1M      0  0:00:06  0:00:06 --:--:-- 33.9M

Yakit installation complete
Installed locations
  Yakit directory: /home/wkyuu/cargo/bin/yakit
  Desktop entry:  /home/wkyuu/.local/share/applications/yakit.desktop
```
