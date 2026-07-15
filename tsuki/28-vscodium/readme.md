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

The installer creates `~/.local/bin/codium` and `~/.local/share/applications/com.vscodium.codium.desktop`. The settings and keybindings link to `~/.config/VSCodium/User/`.

Remove that installation:

```bash
./install-vscodium.sh --uninstall --path ~/cargo/bin/vscodium
```
