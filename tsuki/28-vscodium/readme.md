# VSCodium

Two entrypoints share the core commands: `unix-vscodium.sh` is the Unix implementation (currently Linux); `windows-vscodium.ps1` adapts it to Windows and also supports `upgrade`. Configuration and extension lists stay in `config/`.

| Command | Behavior |
| --- | --- |
| `install` | Install VSCodium from a supplied platform archive |
| `upgrade` (Windows) | Download the latest stable VSCodium ZIP into `%TEMP%` and replace the installed application |
| `remove` | Remove the selected VSCodium installation |
| `sync` | Synchronize settings and extensions |
| `sync setting` | Synchronize `settings.json` and `keybindings.json` |
| `sync extension` | Install extensions listed in `config/extension.txt` |
| `sync extension --export` / `-Export` | Refresh the list from installed extensions |
| `update extension` | Check Open VSX and manually install newer or missing extensions |

Unix usage:

```bash
bash ./unix-vscodium.sh install --archive /tmp/VSCodium-linux-x64.tar.gz --path ~/cargo/bin/vscodium
bash ./unix-vscodium.sh sync
bash ./unix-vscodium.sh sync setting
bash ./unix-vscodium.sh sync extension --export
bash ./unix-vscodium.sh update extension --check
bash ./unix-vscodium.sh update extension
bash ./unix-vscodium.sh remove --path ~/cargo/bin/vscodium
```

The Linux installer creates `~/.local/bin/codium` and a desktop entry. `sync setting` links repository files into `~/.config/VSCodium/User/` and refuses to replace existing regular files. Use `CODIUM_BIN` to select another CLI. The updater defaults to `~/.vscode-oss/extensions`; use `--extensions-dir DIR` to override it.

Windows usage (PowerShell 5.1 or newer):

```powershell
.\windows-vscodium.ps1 install -Archive C:\Downloads\VSCodium-win32-x64.zip
.\windows-vscodium.ps1 upgrade
.\windows-vscodium.ps1 sync
.\windows-vscodium.ps1 sync setting
.\windows-vscodium.ps1 sync extension -Export
.\windows-vscodium.ps1 update extension -Check
.\windows-vscodium.ps1 update extension
.\windows-vscodium.ps1 remove -Path C:\Apps\VSCodium
```

Windows installation uses a supplied ZIP and defaults to `%APPDATA%\Apps\VSCodium` in portable mode. Use `-Path` for another installation directory. `install -Force` retains the old installation as a timestamped backup and copies its portable data into the replacement. `remove` moves the installation to a timestamped backup; move that backup back to its original path to restore it. Close that installation before replacing or removing it.

Windows `upgrade` uses the [official VSCodium GitHub releases](https://github.com/VSCodium/vscodium/releases/latest) and defaults to the same `%APPDATA%\Apps\VSCodium` directory. It detects the installed application's architecture, downloads the matching ZIP into a unique `%TEMP%\vscodium-upgrade-*` directory, verifies SHA-256, extracts and verifies the new application there, and then replaces the installation. Portable settings and extensions in `data` are preserved, the old installation is retained as a timestamped backup, and temporary downloads are cleaned up after success. File operations retry Windows sharing and lock violations up to four times with short delays. Failures report the operation and target, and retain the download and staging directories for diagnosis or a manual `install -Archive ZIP -Force` retry. A cleanup failure after successful replacement produces a warning rather than reporting that the upgrade failed. If the installed version is already current or newer, it skips the download. Close VSCodium before running `upgrade`; use `upgrade -WhatIf` to preview the available upgrade without downloading or replacing files.

Windows `sync setting` copies configuration with timestamped backups. CLI lookup and portable-directory detection are shared with extension synchronization and updates. Use `-CodiumBin 'C:\path\to\VSCodium\bin\codium.cmd'` to select an installation, `-UserDir DIR` for a settings directory, or `-ExtensionsDir DIR` for an extension directory. `-WhatIf` previews changes.

The supplied settings disable automatic extension updates (`extensions.autoUpdate: "off"`, `extensions.autoCheckUpdates: false`). Run `update extension` to update manually. Both platforms compare actual installed versions, validate VSIX identity, verify the installed version, and restore previous extension files and the index if installation fails. Incompatible versions are skipped. Unavailable extensions are reported while the remaining entries are checked, with exit code 1 when any are unavailable. Windows also continues past other per-extension failures; Linux stops if installation fails. Updates never downgrade installed versions. Reload VSCodium after updating.

The Windows updater selects `win32-x64`, `win32-arm64`, or `win32-ia32` packages according to VSCodium's architecture, falling back to universal packages when the requested platform is absent. It also validates the VSIX target platform. Portable installations use `data/extensions`; standard installations use `~/.vscode-oss/extensions` or `VSCODE_EXTENSIONS`.

`config/extension.txt` is the source of truth. The Linux updater reconciles `config/extension.json` with that list, preserving known URLs and versions, removing deleted IDs, and adding new IDs; `--check` leaves it untouched. The Windows updater leaves the shared Linux version manifest untouched.
