# Temporary collaboration account toolkit

This directory contains a small break-glass toolkit for creating a temporary
SSH account and removing every resource created by the toolkit.

## Quick start

Make the scripts executable once:

```bash
chmod +x {add-user,remove-user,status}.sh
```

Create a temporary account and let the script generate an Ed25519 key pair:

```bash
sudo add-user.sh \
  --private-key-file /secure/path/collab.ed25519 \
  --ttl 8h
```

When `--pubkey-file` is omitted, the key pair is generated before account
provisioning. If the script is launched through standard `sudo`, it uses
`SUDO_USER`/`SUDO_UID` to keep the generated files owned by the invoking user.
The private key is written with mode `600`, the public key is written next to it
as `collab.ed25519.pub`, and the command prints both file paths without
printing the private key contents. If `--private-key-file` is omitted, the
default private-key path is `/tmp/<account>.ed25519`; use an explicit path when
the private key must survive a reboot or a temporary-directory cleanup.

Alternatively, create a temporary account with one explicitly supplied public
key:

```bash
sudo add-user.sh \
  --pubkey-file /path/to/collaborator.pub \
  --ttl 8h
```

The command generates a unique `collab-*` account, locks its password, installs
only that public key, and schedules automatic removal through a persistent
systemd timer. The default account has no sudo access.

For a genuine break-glass session where full root access is required, opt in
explicitly:

```bash
sudo add-user.sh \
  --pubkey-file /path/to/collaborator.pub \
  --ttl 2h \
  --full-root \
  --confirm-full-root
```

Check the account and its revoke timer:

```bash
sudo status.sh
```

Revoke it before the timer fires. The account name is printed by
`add-user.sh`:

```bash
sudo remove-user.sh \
  --name collab-YYYYMMDD-HHMMSS-XXXX
```

Use `--yes` only for an already reviewed account name or automation. The
automatic timer invokes the remover with `--yes --auto`.

## Safety properties

- Existing users, groups, home directories, SSH key files, and sudoers files
  are never overwritten.
- Each account has a dedicated primary group and a generated or explicitly
  chosen `collab-*` name, making sessions distinguishable in logs.
- The public key file must contain exactly one supported SSH public key. The
  toolkit never copies the caller's complete `authorized_keys` file. Generated
  private keys are written only to the requested output path with mode `600`;
  private key contents are never stored in toolkit state.
- Account lifetimes are limited to 5 minutes through 30 days. Automatic revoke
  is enabled by default and uses an enabled, persistent systemd timer plus the
  account's own expiry date as a fallback.
- Full root access is disabled by default. `--full-root` plus
  `--confirm-full-root` creates a temporary `sudoers.d` rule with
  `NOPASSWD:ALL`; revoke removes that rule before deleting the account.
- State is kept in `/var/lib/mtf-aid`, owned by root with mode `700`; individual
  state files use mode `600`. The state records the exact paths and IDs needed
  for safe cleanup.
- Revocation locks the account, disables and removes its systemd units, stops
  sessions, ends processes, removes the managed sudoers rule, deletes the
  account and home, removes the dedicated group when it has no other users,
  and verifies the result.

## Requirements and limitations

The target host should provide the standard Linux `useradd`, `userdel`,
`usermod`, `groupadd`, `groupdel`, `chage`, `ssh-keygen`, and `sudo`
utilities. Full root mode additionally requires `visudo`; automatic revoke
requires a running systemd system manager and `systemctl`.

Do not place a generated private key inside this repository or commit it to
version control.

The SSH daemon's existing `AllowUsers`, authentication, firewall, and network
policy still apply. The toolkit does not modify `sshd_config` or restart SSH.

`--no-auto-revoke` is available for hosts without systemd, but it deliberately
removes the automatic safety net. In that mode, run `remove-user.sh` yourself.
The first automatic account also installs a root-owned remover copy under
`/var/lib/mtf-aid`; this keeps the timer independent from later edits to this
working tree. Keep the target host's systemd manager running until all timers
have fired.

Removing the account can revoke access created by this toolkit, but it cannot
undo changes a collaborator already made while holding root privileges. Keep
the host's normal audit and system logs intact. A generated private key is
local credential material and is intentionally not removed by `remove-user.sh`;
delete it manually after confirming that the collaboration session is over.
