# VSCodium

Install the supplied VSCodium archive:

```bash
./install-vscodium.sh --archive /tmp/tmp/VSCodium-linux-x64-1.126.04524.tar.gz --path ~/cargo/bin/vscodium
```

Link the repository-managed settings and keybindings:

```bash
./link-config.sh
```

Install the extensions listed in `config/extensions.txt`:

```bash
./install-extensions.sh
```

Refresh `config/extensions.txt` from the extensions currently installed in VSCodium:

```bash
./sync-extensions.sh
```

Check or update the Linux VSCodium extensions listed in `config/extension.txt`:

```bash
./config/update-extensions.sh --check
./config/update-extensions.sh
```

`config/extension.txt` is the source of truth for which extensions to check. A normal run synchronizes `config/extension.json` with that list, preserving known URLs and versions, removing deleted IDs, and adding new IDs; `--check` leaves the JSON file untouched. A `null` version means the extension was not found locally when it was added. The updater checks installed versions in `~/.vscode-oss/extensions`, validates each downloaded VSIX in a temporary directory, and restores the previous extension and index if installation fails. If VSCodium rejects an incompatible version, the updater asks whether to skip it (`[Y/n]`, default yes) and continues; noninteractive runs skip it automatically. Use `--extensions-dir DIR` for a different extension directory. An extension missing from Open VSX is reported and skipped; the command exits with an error after checking the rest.

The installer creates `~/.local/bin/codium` and `~/.local/share/applications/com.vscodium.codium.desktop`. The settings and keybindings link to `~/.config/VSCodium/User/`.

Remove that installation:

```bash
./install-vscodium.sh --uninstall --path ~/cargo/bin/vscodium
```
