# BrowserOS neo installer

Install [BrowserOS neo](https://github.com/browseros-ai/BrowserOS) with a managed AppImage, launcher, and desktop entry:

```sh
./install.sh install --install-path ~/apps/browseros-neo
```

Enable or update the Codex autostart proxy for an existing installation:

```sh
./install.sh proxy --install-path ~/apps/browseros-neo
```

The proxy connects to the running BrowserOS neo service when available. Otherwise, it starts the same launcher used by the desktop entry, with the same configured profile and browser state. It does not create a separate profile for Codex.

The proxy passes desktop, input-method, and locale environment variables through from the Codex process when available. Start Codex from a desktop session that provides the appropriate input-method settings if you need to type in an autostarted browser window.
