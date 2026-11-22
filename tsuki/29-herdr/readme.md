
paste this

```
Help me understand and set up Herdr. Read https://herdr.dev/agent-guide.md first, then walk me through it step by step.
```

usage:

```bash
$ ./install-herdr.sh --path /home/wkyuu/cargo/bin/herdr --force
  % Total    % Received % Xferd  Average Speed   Time    Time     Time  Current
                                 Dload  Upload   Total   Spent    Left  Speed
100  3085  100  3085    0     0   9862      0 --:--:-- --:--:-- --:--:--  9887

      ,ww
     wWWWWWWW_)  herdr installer
     `WWWWWW'    herdr.dev
      II  II

  > detected linux/x86_64
  > fetching latest release manifest...
  > downloading v0.7.4...
  > installed herdr to /home/wkyuu/cargo/bin/herdr/herdr

  ! /home/wkyuu/cargo/bin/herdr is not in your PATH
  add it to your shell config:

    export PATH="/home/wkyuu/cargo/bin/herdr:$PATH"


  > ready. run 'herdr' to get started.

herdr installation complete
  Binary:  /home/wkyuu/cargo/bin/herdr/herdr
  Command: /home/wkyuu/.local/bin/herdr
```

## Manage configuration

Edit `sync.config.json` and run:

```bash
./sync.sh --force
```

The script updates the marked section of the Herdr configuration and preserves
other settings. It saves a private backup in a `herdr-config-backup-*`
directory under the system temporary directory. An existing configuration is
only changed with `--force`; an unchanged configuration can be synced without it.
The script requires Python 3.11 or newer and uses `HERDR_CONFIG_PATH`, then
`XDG_CONFIG_HOME`, then `~/.config/herdr/config.toml` to locate the config.
Symbolic-link targets are rejected.

The managed `terminal.kitty_graphics = false` applies to all programs in the
affected Herdr server. Restart the affected server or reconnect its client, then
restart Codex, to apply the change. The sync script never restarts Herdr.
