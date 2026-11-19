"""Update the managed TOML blocks from the repository's JSON configuration."""

from dataclasses import dataclass
from datetime import date, time
import fcntl
from io import StringIO
import json
import os
from pathlib import Path
import re
import shutil
import stat
import sys
import tempfile
import tomllib
from typing import Iterator


BLOCK_START = "# THIS BLOCK WILL BE OVERWRITTEN BY SCRIPTS"
BLOCK_END = "# BLOCK END"
MANAGED_KEYS = "# Managed TOML keys: "
BARE_KEY = r"[A-Za-z0-9_-]+"
TOML_KEY = rf"""(?:{BARE_KEY}|"(?:[^"\\]|\\.)*"|'[^']*')"""
ASSIGNMENT = re.compile(
    rf"([ \t]*)(?P<key>{TOML_KEY}(?:[ \t]*\.[ \t]*{TOML_KEY})*)[ \t]*="
)
PROFILE = re.compile(r"(?:config|[A-Za-z0-9_-]+\.config)\.toml")

KeyPath = tuple[str, ...]


@dataclass
class Update:
    """An original snapshot and the proposed replacement."""

    target: Path
    original: bytes | None
    rendered: bytes
    mode: int


def _leaves(values: dict, prefix: KeyPath = ()) -> Iterator[tuple[KeyPath, object]]:
    """Walk the keys managed by a manifest object."""
    for key, value in values.items():
        path = (*prefix, key)
        if isinstance(value, dict) and value:
            yield from _leaves(value, path)
        else:
            yield path, value


def _key(path: KeyPath) -> str:
    """Encode a key path without treating dots inside keys as separators."""
    return ".".join(
        part if re.fullmatch(BARE_KEY, part) else _quote(part) for part in path
    )


def _quote(value: str) -> str:
    """Encode a TOML basic string using JSON's compatible escapes."""
    return json.dumps(value, ensure_ascii=False).replace("\x7f", r"\u007f")


def _value(value: object) -> str:
    """Encode a JSON value or a TOML value from an adopted inline table."""
    if isinstance(value, str):
        return _quote(value)
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, (int, float)):
        return repr(value)
    if isinstance(value, (date, time)):
        return value.isoformat()
    if isinstance(value, list):
        return "[" + ", ".join(_value(element) for element in value) + "]"
    if isinstance(value, dict):
        fields = ", ".join(
            f"{_key((key,))} = {_value(item)}" for key, item in value.items()
        )
        return "{ " + fields + " }" if fields else "{}"
    raise ValueError(f"TOML cannot represent a {type(value).__name__} value")


def _row(path: KeyPath, value: object, newline: str) -> str:
    """Render one complete root assignment."""
    if isinstance(value, str) and "\n" in value:
        body = newline.join(_quote(line)[1:-1] for line in value.split("\n"))
        return f'{_key(path)} = """{newline}{body}"""{newline}'
    return f"{_key(path)} = {_value(value)}{newline}"


def _merge(base: dict, override: dict) -> dict:
    """Merge TOML objects recursively and replace scalars and arrays."""
    result = dict(base)
    for key, value in override.items():
        if isinstance(result.get(key), dict) and isinstance(value, dict) and value:
            result[key] = _merge(result[key], value)
        else:
            result[key] = value
    return result


def _block(common: dict, managed: dict, notes: list[str], newline: str) -> str:
    """Generate a block using only the manifest and the file's line ending."""
    common_paths = {path for path, _ in _leaves(common)}
    groups: dict[str, list[str]] = {}
    profile_rows = []
    for path, value in _leaves(managed):
        row = _row(path, value, newline)
        if path in common_paths:
            title = "common" if len(path) == 1 else _key((path[0],))
            groups.setdefault(title, []).append(row)
        else:
            profile_rows.append(row)
    if profile_rows:
        groups["profile settings"] = profile_rows
    paths = [_key(path) for path, _ in _leaves(managed)]
    rows = [BLOCK_START + newline, MANAGED_KEYS + json.dumps(paths) + newline]
    if notes:
        rows.extend(
            f"## {line}{newline}" for note in notes for line in note.splitlines()
        )
        rows.append(newline)
    for index, (title, group_rows) in enumerate(groups.items()):
        if index:
            rows.append(newline)
        rows.append(f"## {title}{newline}")
        rows.extend(group_rows)
    rows.append(BLOCK_END + newline)
    return "".join(rows)


def _statements(source: str) -> Iterator[tuple[str, dict]]:
    """Split valid TOML at statement boundaries using the TOML parser."""
    pending = ""
    for line in StringIO(source):
        pending += line
        try:
            parsed = tomllib.loads(pending)
        except tomllib.TOMLDecodeError:
            continue
        yield pending, parsed
        pending = ""
    if pending:
        raise ValueError("Could not identify a complete TOML statement")


def _header_path(data: dict) -> KeyPath:
    """Read the path from an isolated table or array-of-tables header."""
    path = []
    while data:
        key, data = next(iter(data.items()))
        path.append(key)
        if isinstance(data, list):
            break
    return tuple(path)


def _remove(data: dict, path: KeyPath) -> None:
    """Remove a key, leaving its sibling values intact."""
    table = data
    for key in path[:-1]:
        if key not in table:
            return
        table = table[key]
        if not isinstance(table, dict):
            raise ValueError(f"Expected a table at {_key(path)}")
    table.pop(path[-1], None)


def _starts_with(path: KeyPath, prefix: KeyPath) -> bool:
    """Compare paths by key components."""
    return path[: len(prefix)] == prefix


def _overlap(left: KeyPath, right: KeyPath) -> bool:
    """Check whether either path is contained by the other."""
    return _starts_with(left, right) or _starts_with(right, left)


def _trailing_comment(statement: str, newline: str) -> str:
    """Keep an inline comment when replacing its original declaration."""
    for match in re.finditer("#", statement):
        try:
            parsed = tomllib.loads(statement[: match.start()])
        except tomllib.TOMLDecodeError:
            continue
        if parsed:
            return statement[match.start() :].rstrip("\r\n") + newline
    return ""


def _adopt(
    statements: list[tuple[str, dict]], owned: set[KeyPath], newline: str
) -> tuple[str, str]:
    """Move settings shared with dotted keys out of conflicting legacy tables."""
    root: list[str] = []
    shared: list[str] = []
    tables: list[str] = []
    destination = root
    table: KeyPath = ()
    for text, data in statements:
        significant = text.lstrip(" \t")
        if significant.startswith("["):
            table = _header_path(data)
            if any(_overlap(path, table) for path in owned):
                destination = shared
                shared.append(_trailing_comment(text, newline))
            else:
                destination = tables
                tables.append(text)
        elif match := ASSIGNMENT.match(text):
            local = _header_path(tomllib.loads(match["key"] + " = {}"))
            path = (*table, *local)
            if any(_starts_with(path, key) for key in owned):
                continue
            if any(_starts_with(key, path) for key in owned):
                destination.extend(
                    _row(key, value, newline)
                    for key, value in _leaves(data, table)
                    if not any(_overlap(key, managed) for managed in owned)
                )
                destination.append(_trailing_comment(text, newline))
            elif destination is shared:
                shared.append(f"{match[1]}{_key(table)}.{text[len(match[1]) :]}")
            else:
                destination.append(text)
        else:
            destination.append(text)
    return "".join(root + shared), "".join(tables)


def _preserve_additions(
    before: str, body: str, after: str, owned: set[KeyPath], newline: str
) -> tuple[str, str, dict]:
    """Relocate settings that Codex added inside the block after its creation."""
    statements = list(_statements(body))
    previous = set()
    for text, _ in statements:
        if text.startswith(MANAGED_KEYS):
            for key in json.loads(text.removeprefix(MANAGED_KEYS)):
                previous.add(_header_path(tomllib.loads(key + " = {}")))
    discarded = owned | previous
    preserved = tomllib.loads(before + after)
    additions = [
        _row(path, value, newline)
        for path, value in _leaves(tomllib.loads(body))
        if not any(_overlap(path, key) for key in discarded)
    ]
    if not additions:
        return before, after, preserved

    user_statements = [
        (text, data)
        for text, data in statements
        if not text.startswith((MANAGED_KEYS, "## "))
    ]
    root, tables = _adopt(user_statements, discarded, newline)
    if root.strip():
        before += root.rstrip("\r\n") + newline * 2
    if tables.strip():
        separator = newline if after.endswith(newline) else newline * 2
        after += separator + tables.lstrip("\r\n")
    return before, after, _merge(preserved, tomllib.loads("".join(additions)))


def _render(
    source: str | None,
    defaults: dict,
    common: dict,
    profile: dict,
    retired: list[str],
    notes: list[str],
) -> str:
    """Replace a marked block or adopt the managed keys from a legacy file."""
    managed = _merge(common, profile)
    original = (
        source
        if source is not None
        else "".join(_row(path, value, "\n") for path, value in _leaves(defaults))
    )
    newline = "\r\n" if "\r\n" in original else "\n"
    existing = tomllib.loads(original)
    statements = list(_statements(original))
    markers = []
    offset = 0
    for text, _ in statements:
        if (marker := text.strip(" \t\r\n")) in (BLOCK_START, BLOCK_END):
            markers.append((marker, offset, offset + len(text)))
        offset += len(text)

    owned = {path for path, _ in _leaves(managed)}
    retired_paths = {(key,) for key in retired}
    if markers:
        if [marker for marker, _, _ in markers] != [BLOCK_START, BLOCK_END]:
            raise ValueError(
                "Expected exactly one managed block with a start and an end marker"
            )
        before = original[: markers[0][1]]
        after = original[markers[1][2] :]
        body = original[markers[0][2] : markers[1][1]]
        before, after, preserved = _preserve_additions(
            before, body, after, owned | retired_paths, newline
        )
        if any(key in preserved for key in retired):
            raise ValueError(
                "A retired configuration key remains outside the managed block"
            )
    else:
        preserved = existing
        for path in owned | retired_paths:
            _remove(preserved, path)
        before, after = _adopt(statements, owned | retired_paths, newline)
        if before and not before.endswith(newline):
            before += newline
        if before and not before.endswith(newline * 2):
            before += newline
        if after and not after.startswith(newline):
            after = newline + after

    if "default_permissions" in managed and "sandbox_workspace_write" in preserved:
        raise ValueError(
            "Migrate sandbox_workspace_write before applying default_permissions"
        )
    rendered = before + _block(common, managed, notes, newline) + after
    expected = _merge(preserved, managed)
    actual = tomllib.loads(rendered)
    if json.dumps(actual, sort_keys=True, default=repr) != json.dumps(
        expected, sort_keys=True, default=repr
    ):
        raise ValueError(
            "Generated TOML would change settings outside the managed block"
        )
    return rendered


def _unique_object(pairs: list[tuple[str, object]]) -> dict:
    """Reject repeated JSON keys before one value shadows another."""
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON key {key!r}")
        result[key] = value
    return result


def _snapshot(target: Path, backup: Path) -> tuple[bytes | None, int]:
    """Keep the original bytes and mode in a private backup directory."""
    if target.is_symlink() or (target.exists() and not target.is_file()):
        raise ValueError(f"{target}: expected a regular configuration file")
    if not target.exists():
        return None, 0o600
    shutil.copy2(target, backup)
    return backup.read_bytes(), stat.S_IMODE(backup.stat().st_mode)


def _matches(target: Path, content: bytes | None, mode: int) -> bool:
    """Check that a target still matches a recorded snapshot."""
    if target.is_symlink():
        return False
    try:
        with target.open("rb") as stream:
            return (
                stream.read() == content
                and stat.S_IMODE(os.fstat(stream.fileno()).st_mode) == mode
            )
    except FileNotFoundError:
        return content is None


def _apply(updates: list[Update], directory: Path, backup: Path) -> None:
    """Stage all replacements, then atomically replace each changed file."""
    with tempfile.TemporaryDirectory(prefix=".codex-sync-", dir=directory) as name:
        stage = Path(name)
        for item in updates:
            candidate = stage / item.target.name
            candidate.write_bytes(item.rendered)
            candidate.chmod(item.mode)
        applied = []
        try:
            for item in updates:
                if not _matches(item.target, item.original, item.mode):
                    raise ValueError(f"{item.target}: changed during sync")
                os.replace(stage / item.target.name, item.target)
                applied.append(item)
        except (OSError, ValueError, KeyboardInterrupt) as error:
            failures = []
            for item in reversed(applied):
                try:
                    if not _matches(item.target, item.rendered, item.mode):
                        continue
                    if item.original is None:
                        item.target.unlink()
                    else:
                        restore = shutil.copy2(backup / item.target.name, stage)
                        os.replace(restore, item.target)
                except OSError as rollback_error:
                    failures.append(str(rollback_error))
            if failures:
                raise ValueError(
                    f"{error}. Rollback failed: {', '.join(failures)}"
                ) from error
            raise


def _sync(manifest_path: Path, directory: Path) -> None:
    """Back up the profiles and validate every output before writing any."""
    manifest = json.loads(
        manifest_path.read_text(encoding="utf-8"), object_pairs_hook=_unique_object
    )
    profiles = manifest["profiles"]
    for name in profiles:
        if not PROFILE.fullmatch(name):
            raise ValueError(f"Invalid profile filename {name!r}")
    backup = Path(tempfile.mkdtemp(prefix="codex-config-backup-"))
    sys.stdout.write(f"Configuration backups: {backup}\n")
    snapshots = {name: _snapshot(directory / name, backup / name) for name in profiles}
    updates = []
    for name, profile in profiles.items():
        original, mode = snapshots[name]
        try:
            rendered = _render(
                original.decode("utf-8") if original is not None else None,
                profile["defaults"],
                manifest["common"],
                profile["managed"],
                manifest["remove_on_migration"],
                profile.get("notes", []),
            ).encode("utf-8")
        except (UnicodeError, ValueError) as error:
            raise ValueError(f"{name}: {error}") from error
        if rendered != original:
            updates.append(Update(directory / name, original, rendered, mode))
    if updates:
        _apply(updates, directory, backup)


def main() -> int:
    """Run the TOML update while holding the Codex directory lock."""
    try:
        manifest, target = map(Path, sys.argv[1:])
        lock = os.open(target, os.O_RDONLY)
        try:
            fcntl.flock(lock, fcntl.LOCK_EX)
            _sync(manifest, target)
        finally:
            os.close(lock)
    except (OSError, AttributeError, KeyError, TypeError, ValueError) as error:
        sys.stderr.write(f"Error: {error}\n")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
