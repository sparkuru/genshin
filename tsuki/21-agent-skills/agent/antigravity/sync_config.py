"""Merge managed CLI settings and install the global Antigravity rules."""

import copy
import json
import os
from pathlib import Path
import stat
import sys
import tempfile
from typing import Any


class CLIStyle:
    """Keep sync output readable in terminals and plain in redirected output."""

    @staticmethod
    def write(message: str, *, error: bool = False) -> None:
        """Write a status or error message with optional terminal color."""
        stream = sys.stderr if error else sys.stdout
        if stream.isatty() and not os.environ.get("NO_COLOR"):
            style = "\033[1;31m" if error else "\033[0;32m"
            message = f"{style}{message}\033[0m"
        stream.write(f"{message}\n")


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Reject duplicate JSON keys before merging an existing configuration."""
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def _invalid_constant(value: str) -> None:
    """Reject nonstandard JSON constants."""
    raise ValueError(f"invalid JSON constant: {value}")


def _read_object(data: bytes, path: Path) -> dict[str, Any]:
    """Parse a JSON object without emitting its contents."""
    try:
        result = json.loads(
            data, object_pairs_hook=_unique_object, parse_constant=_invalid_constant
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        raise ValueError(f"invalid JSON in {path}: {error}") from error
    if not isinstance(result, dict):
        raise ValueError(f"JSON root must be an object: {path}")
    return result


def _merge(base: dict[str, Any], managed: dict[str, Any]) -> dict[str, Any]:
    """Replace managed leaves while retaining unrelated settings."""
    result = copy.deepcopy(base)
    for key, value in managed.items():
        if isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = _merge(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def _merge_settings(base: dict[str, Any], managed: dict[str, Any]) -> dict[str, Any]:
    """Put managed allow rules first and retain additional local rules."""
    if "permissions" not in managed:
        return _merge(base, managed)
    managed_permissions = managed["permissions"]
    if not isinstance(managed_permissions, dict):
        raise ValueError("managed permissions must be a JSON object")
    if "allow" not in managed_permissions:
        return _merge(base, managed)

    local_permissions = base.get("permissions", {})
    if not isinstance(local_permissions, dict):
        raise ValueError("local permissions must be a JSON object")
    managed_allow = managed_permissions["allow"]
    local_allow = local_permissions.get("allow", [])
    for name, rules in (("managed", managed_allow), ("local", local_allow)):
        if not isinstance(rules, list) or not all(
            isinstance(rule, str) for rule in rules
        ):
            raise ValueError(f"{name} permissions.allow must be a list of strings")

    result = _merge(base, managed)
    result["permissions"]["allow"] = list(dict.fromkeys(managed_allow + local_allow))
    return result


def _json_bytes(value: dict[str, Any]) -> bytes:
    """Render valid, stable UTF-8 JSON."""
    return (
        json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n"
    ).encode()


def _canonical(value: dict[str, Any]) -> str:
    """Compare JSON values without changing the target's formatting."""
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False)


def _snapshot(path: Path) -> tuple[str, bytes | str | None]:
    """Capture a file or link without following a link at the target path."""
    try:
        mode = path.lstat().st_mode
    except FileNotFoundError:
        return ("missing", None)
    if stat.S_ISLNK(mode):
        return ("link", os.readlink(path))
    if stat.S_ISREG(mode):
        return ("file", path.read_bytes())
    raise ValueError(f"unsupported target type: {path}")


def _write_atomic(path: Path, content: bytes) -> None:
    """Replace a file using a private temporary file in the same directory."""
    descriptor, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_name, path)
    finally:
        if os.path.exists(temp_name):
            os.unlink(temp_name)


def _backup(
    path: Path, snapshot: tuple[str, bytes | str | None], destination: Path
) -> None:
    """Preserve a replaced file or symlink inside a private backup directory."""
    kind, value = snapshot
    if kind == "file" and isinstance(value, bytes):
        _write_atomic(destination, value)
    elif kind == "link" and isinstance(value, str):
        destination.symlink_to(value)
    else:
        raise ValueError(f"cannot back up target: {path}")


def _link_matches(
    path: Path, snapshot: tuple[str, bytes | str | None], source: Path
) -> bool:
    """Check whether a target link already resolves to the desired rules file."""
    kind, value = snapshot
    return kind == "link" and isinstance(value, str) and path.resolve() == source


def _sync(source_dir: Path, target_dir: Path, dry_run: bool, force: bool) -> None:
    """Preflight, preview, and apply the selected configuration changes."""
    if not target_dir.is_absolute() or target_dir == Path("/"):
        raise ValueError("target directory must be an absolute path other than /")
    target_dir = target_dir.resolve()
    if target_dir == Path("/"):
        raise ValueError("target directory must not resolve to /")
    if target_dir == source_dir or source_dir in target_dir.parents:
        raise ValueError("target directory must be outside the source directory")

    settings_source = source_dir / "settings.managed.json"
    rules_source = (source_dir / "agents.md").resolve(strict=True)
    managed = _read_object(settings_source.read_bytes(), settings_source)
    settings_target = target_dir / "antigravity-cli" / "settings.json"
    rules_target = target_dir / "config" / "AGENTS.md"
    settings_snapshot = _snapshot(settings_target)
    rules_snapshot = _snapshot(rules_target)
    if settings_snapshot[0] == "link":
        raise ValueError(f"settings target must not be a symlink: {settings_target}")

    existing = (
        _read_object(settings_snapshot[1], settings_target)
        if isinstance(settings_snapshot[1], bytes)
        else {}
    )
    merged = _merge_settings(existing, managed)
    settings_changed = settings_snapshot[0] == "missing" or _canonical(
        merged
    ) != _canonical(existing)
    rules_changed = not _link_matches(rules_target, rules_snapshot, rules_source)
    rules_conflict = rules_changed and rules_snapshot[0] != "missing"

    CLIStyle.write(
        f"Settings: {'update' if settings_changed else 'unchanged'} {settings_target}"
    )
    CLIStyle.write(f"Managed keys: {', '.join(sorted(managed)) or '(none)'}")
    CLIStyle.write(f"Rules: {'link' if rules_changed else 'unchanged'} {rules_target}")
    if rules_conflict:
        CLIStyle.write("Existing rules require --force and will be backed up.")
    if dry_run:
        return
    if rules_conflict and not force:
        raise ValueError(
            "rules target conflicts; use --force to back it up and replace it"
        )
    if not settings_changed and not rules_changed:
        CLIStyle.write("Antigravity configuration is already synced.")
        return

    if (
        _snapshot(settings_target) != settings_snapshot
        or _snapshot(rules_target) != rules_snapshot
    ):
        raise ValueError("a target changed during synchronization; retry")
    os.umask(0o077)
    settings_target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    rules_target.parent.mkdir(mode=0o700, parents=True, exist_ok=True)

    backup_items = []
    if settings_changed and settings_snapshot[0] != "missing":
        backup_items.append((settings_target, settings_snapshot, "settings.json"))
    if rules_conflict:
        backup_items.append((rules_target, rules_snapshot, "AGENTS.md"))
    if backup_items:
        backup_dir = Path(
            tempfile.mkdtemp(prefix=".antigravity-sync-backup.", dir=target_dir)
        )
        for path, snapshot, name in backup_items:
            _backup(path, snapshot, backup_dir / name)
        CLIStyle.write(f"Backup: {backup_dir}")

    if (
        _snapshot(settings_target) != settings_snapshot
        or _snapshot(rules_target) != rules_snapshot
    ):
        raise ValueError("a target changed during synchronization; retry")
    if settings_changed:
        _write_atomic(settings_target, _json_bytes(merged))
    if rules_changed:
        if rules_conflict:
            rules_target.unlink()
        rules_target.symlink_to(rules_source)
    CLIStyle.write("Antigravity configuration synced.")


def main() -> int:
    """Run the internal sync helper invoked by sync.sh."""
    if len(sys.argv) != 5:
        CLIStyle.write("Error: invoke this helper through sync.sh", error=True)
        return 2
    source_dir = Path(sys.argv[1]).resolve(strict=True)
    target_dir = Path(sys.argv[2])
    try:
        _sync(source_dir, target_dir, sys.argv[3] == "true", sys.argv[4] == "true")
    except (OSError, ValueError) as error:
        CLIStyle.write(f"Error: {error}", error=True)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
