# VSCodium

`unix-vscodium.sh` is the Unix implementation (currently Linux); `windows-vscodium.ps1` adapts installation and extension management to Windows and also supports `upgrade`. Configuration and extension lists stay in `config/`.

| Command | Behavior |
| --- | --- |
| `install` | Install VSCodium from a supplied platform archive |
| `upgrade` (Windows) | Download the latest stable VSCodium ZIP into `%TEMP%` and replace the installed application |
| `remove` | Remove the selected VSCodium installation |
| `local sync` | Synchronize settings, keybindings, and extensions from repository to local |
| `repo sync` | Synchronize settings, keybindings, and extensions from local to repository |
| `local sync settings` / `repo sync settings` | Synchronize only `settings.json` in the selected direction |
| `local sync keybindings` / `repo sync keybindings` | Synchronize only `keybindings.json` in the selected direction |
| `local sync extensions` | Install extensions listed in `config/extensions.txt` |
| `repo sync extensions` | Replace `config/extensions.txt` with sorted, unique installed extension IDs |
| `sync` / `sync setting` (Windows legacy aliases) | Synchronize everything / settings and keybindings from repository to local |
| `sync extension` / `sync extension -Export` (Windows legacy aliases) | Install extensions / export installed IDs |
| `update extensions` | Check Open VSX and manually install newer or missing extensions (Windows also accepts `update extension`) |

Unix usage:

```bash
bash ./unix-vscodium.sh install --archive /tmp/VSCodium-linux-x64.tar.gz --path ~/cargo/bin/vscodium

# repo into local
bash ./unix-vscodium.sh local sync
bash ./unix-vscodium.sh local sync settings
bash ./unix-vscodium.sh local sync extensions

# local into repo
bash ./unix-vscodium.sh repo sync
bash ./unix-vscodium.sh repo sync extensions
bash ./unix-vscodium.sh repo sync keybindings

bash ./unix-vscodium.sh update extensions --check
bash ./unix-vscodium.sh update extensions

bash ./unix-vscodium.sh remove --path ~/cargo/bin/vscodium
```

The Linux installer creates `~/.local/bin/codium` and a desktop entry. `local sync` links settings and keybindings from the current repository into `${XDG_CONFIG_HOME:-~/.config}/VSCodium/User/`. `repo sync` copies local files into the current repository, dereferencing source links and replacing destination links rather than writing through them. Existing matching local links are left in place; repository links are materialized before linking local files to prevent cycles. Replaced files and links are retained as `/tmp/vscodium-<filename>.backup.*`, and each backup path is printed. Each settings target is independent. Extension installation keeps additional local extensions; exporting replaces the repository list, including with an empty list when none are installed. Use `CODIUM_BIN` to select another CLI. The updater defaults to `~/.vscode-oss/extensions`; use `--extensions-dir DIR` to override it.

Windows usage (PowerShell 5.1 or newer):

```powershell
.\windows-vscodium.ps1 install -Archive C:\Downloads\VSCodium-win32-x64.zip
.\windows-vscodium.ps1 upgrade
.\windows-vscodium.ps1 local sync
.\windows-vscodium.ps1 local sync settings
.\windows-vscodium.ps1 local sync settings -Link
.\windows-vscodium.ps1 local sync extensions
.\windows-vscodium.ps1 repo sync
.\windows-vscodium.ps1 repo sync keybindings
.\windows-vscodium.ps1 repo sync extensions
.\windows-vscodium.ps1 update extensions -Check
.\windows-vscodium.ps1 update extensions
.\windows-vscodium.ps1 remove -Path C:\Apps\VSCodium
```

Windows installation uses a supplied ZIP and defaults to `%APPDATA%\Apps\VSCodium` in portable mode. Use `-Path` for another installation directory. `install -Force` retains the old installation as a timestamped backup and copies its portable data into the replacement. `remove` moves the installation to a timestamped backup; move that backup back to its original path to restore it. Close that installation before replacing or removing it.

Windows `upgrade` uses the [official VSCodium GitHub releases](https://github.com/VSCodium/vscodium/releases/latest) and defaults to the same `%APPDATA%\Apps\VSCodium` directory. It detects the installed application's architecture, downloads the matching ZIP into a unique `%TEMP%\vscodium-upgrade-*` directory, verifies SHA-256, extracts and verifies the new application there, and then replaces the installation. Portable settings and extensions in `data` are preserved, the old installation is retained as a timestamped backup, and temporary downloads are cleaned up after success. File operations retry Windows sharing and lock violations up to four times with short delays. Failures report the operation and target, and retain the download and staging directories for diagnosis or a manual `install -Archive ZIP -Force` retry. A cleanup failure after successful replacement produces a warning rather than reporting that the upgrade failed. If the installed version is already current or newer, it skips the download. Close VSCodium before running `upgrade`; use `upgrade -WhatIf` to preview the available upgrade without downloading or replacing files.

Windows uses the same `local sync` / `repo sync` commands and independent targets as Unix. By default, `local sync` copies settings and keybindings from the repository into regular local files, and `repo sync` copies local content into regular repository files. These copies require no symbolic link creation privileges. Existing destination links are backed up and replaced rather than written through, so running the default `local sync` also converts previously linked local settings into independent files. Replaced files and links are moved to unique `%TEMP%\vscodium-<filename>.backup.*` paths, which are printed. Unchanged regular files are left in place.

Add `-Link` to `local sync`, `local sync settings`, or `local sync keybindings` to share repository configuration through symbolic links instead. This mode requires PowerShell 7 with Windows Developer Mode enabled, or an administrator PowerShell session (see [New-Item symbolic link requirements](https://learn.microsoft.com/en-us/powershell/module/microsoft.powershell.management/new-item#example-7-create-a-symbolic-link-to-a-file-or-folder)). Changes through local links affect repository files immediately, and moving or deleting the repository breaks those links. Link creation is staged before replacing existing local files, so a privilege failure preserves the originals. Repository source links are materialized first to prevent cycles, and matching local links are left in place. `-Link` is rejected for repository exports and extension-only targets.

Windows extension synchronization retains additional local extensions, leaves already installed IDs in place (including private extensions), and attempts every missing ID; an empty list is valid. If the CLI explicitly reports that an extension was not found in the configured gallery, synchronization warns and skips it without failing, noting that a private extension may need manual VSIX installation. Other installation errors and verification failures still result in exit code 1 after the remaining IDs are attempted. The final summary reports installed and skipped counts. Exporting writes sorted, unique IDs, including an empty file when none are installed, and backs up a changed repository list. The old `sync`, `sync setting`, and `sync extension [-Export]` commands remain aliases for these behaviors; `sync` and `sync setting` also accept `-Link`.

CLI lookup and portable-directory detection are shared with extension synchronization and updates. Use `-CodiumBin 'C:\path\to\VSCodium\bin\codium.cmd'` to select an installation, `-UserDir DIR` for a settings directory, or `-ExtensionsDir DIR` for an extension directory. `-WhatIf` previews changes without writing files or installing extensions.

The supplied settings disable automatic extension updates (`extensions.autoUpdate: "off"`, `extensions.autoCheckUpdates: false`). Run `update extensions` on Unix or `update extension` on Windows to update manually. Both platforms compare actual installed versions, validate VSIX identity, verify the installed version, and restore previous extension files and the index if installation fails. Incompatible versions are skipped. Unavailable extensions are reported while the remaining entries are checked, with exit code 1 when any are unavailable. Windows also continues past other per-extension failures; Linux stops if installation fails. Updates never downgrade installed versions. Reload VSCodium after updating.

The Windows updater selects `win32-x64`, `win32-arm64`, or `win32-ia32` packages according to VSCodium's architecture, falling back to universal packages when the requested platform is absent. It also validates the VSIX target platform. Portable installations use `data/extensions`; standard installations use `~/.vscode-oss/extensions` or `VSCODE_EXTENSIONS`.

`config/extensions.txt` is the source of truth. The Linux updater reconciles `config/extensions.json` with that list, preserving known URLs and versions, removing deleted IDs, and adding new IDs; `--check` leaves it untouched. The Windows updater leaves the shared Linux version manifest untouched.
