#!/usr/bin/env python3
"""Manage the opt-in Codex connection for the BrowserOS neo MCP proxy."""

from __future__ import annotations

import copy
import json
import os
import re
import stat
import sys
import tempfile
import tomllib
from pathlib import Path
from urllib.parse import urlsplit


DIRECT_NAME = "browseros-neo"
PROXY_NAME = "browseros-neo-autostart"
MARKER_NAME = ".browseros-neo-codex-mcp.json"
DEFAULT_ENDPOINT = "http://127.0.0.1:9010/mcp"
ENV_VARS = [
    "DISPLAY",
    "WAYLAND_DISPLAY",
    "XAUTHORITY",
    "XDG_RUNTIME_DIR",
    "DBUS_SESSION_BUS_ADDRESS",
    "XDG_SESSION_TYPE",
    "XDG_CURRENT_DESKTOP",
    "KDE_SESSION_VERSION",
    "KDE_FULL_SESSION",
    "XDG_SESSION_DESKTOP",
    "DESKTOP_SESSION",
    "GTK_IM_MODULE",
    "QT_IM_MODULE",
    "SDL_IM_MODULE",
    "GLFW_IM_MODULE",
    "XMODIFIERS",
    "INPUT_METHOD",
    "IBUS_ADDRESS",
    "LANG",
    "LANGUAGE",
    "LC_ALL",
    "LC_CTYPE",
]
KDE_SESSION_ENV_VARS = frozenset(
    {
        "KDE_SESSION_VERSION",
        "KDE_FULL_SESSION",
        "XDG_SESSION_DESKTOP",
        "DESKTOP_SESSION",
    }
)
HEADER = re.compile(r"^\s*(\[{1,2})\s*([^\[\]]+)\s*(\]{1,2})\s*(?:#.*)?(?:\r?\n)?$")


def parse_config(raw: bytes) -> dict:
    """Parse the existing configuration before changing any files."""
    try:
        return tomllib.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, tomllib.TOMLDecodeError) as exc:
        raise RuntimeError("Codex config is not valid UTF-8 TOML") from exc


def config_bytes(path: Path) -> bytes:
    """Read a regular config file while refusing to replace a symlink."""
    if path.is_symlink():
        raise RuntimeError(f"Codex config is a symlink: {path}")
    try:
        return path.read_bytes()
    except FileNotFoundError:
        return b""


def section_bounds(lines: list[str], name: str) -> tuple[int, int] | None:
    """Find one ordinary MCP server table without reformatting unrelated TOML."""
    names = {
        f"mcp_servers.{name}",
        f'mcp_servers."{name}"',
        f"mcp_servers.'{name}'",
    }
    start = None
    for index, line in enumerate(lines):
        match = HEADER.match(line)
        if not match:
            continue
        key = re.sub(r"\s*\.\s*", ".", match.group(2).strip())
        if start is not None:
            return start, index
        if match.group(1) == "[" and match.group(3) == "]" and key in names:
            start = index
    return (start, len(lines)) if start is not None else None


def set_direct_enabled(text: str, present: bool, value: bool = False) -> str:
    """Change only the direct connection's enabled field."""
    lines = text.splitlines(keepends=True)
    bounds = section_bounds(lines, DIRECT_NAME)
    if bounds is None:
        raise RuntimeError("The BrowserOS MCP entry must be an ordinary TOML table")
    start, end = bounds
    pattern = re.compile(r"^(\s*enabled\s*=\s*)(true|false)(\s*(?:#.*)?)(\r?\n)?$")
    matches = [(i, pattern.match(lines[i])) for i in range(start + 1, end)]
    matches = [(i, match) for i, match in matches if match]
    if len(matches) > 1:
        raise RuntimeError("The BrowserOS MCP enabled field is ambiguous")
    if not present:
        if matches:
            del lines[matches[0][0]]
        return "".join(lines)
    setting = "true" if value else "false"
    if matches:
        index, match = matches[0]
        assert match is not None
        lines[index] = (
            f"{match.group(1)}{setting}{match.group(3)}{match.group(4) or ''}"
        )
    else:
        lines.insert(start + 1, f"enabled = {setting}\n")
    return "".join(lines)


def remove_section(text: str, name: str) -> str:
    """Remove one recognized table while retaining all other text."""
    lines = text.splitlines(keepends=True)
    bounds = section_bounds(lines, name)
    if bounds is None:
        raise RuntimeError(f"MCP entry {name!r} must be an ordinary TOML table")
    start, end = bounds
    retained = []
    for line in lines[start + 1 : end]:
        if not line.strip() or line.lstrip().startswith("#"):
            retained.append(line)
        elif "#" in line:
            raise RuntimeError(
                f"MCP entry {name!r} contains comments that need manual review"
            )
    lines[start:end] = retained
    return "".join(lines)


def append_section(text: str, name: str, fields: dict) -> str:
    """Append one MCP table using JSON-compatible TOML scalar encodings."""
    if text and not text.endswith("\n"):
        text += "\n"
    text += f"\n[mcp_servers.{name}]\n"
    for key, value in fields.items():
        text += f"{key} = {json.dumps(value, ensure_ascii=False)}\n"
    return text


def valid_endpoint(value: object) -> bool:
    """Accept only BrowserOS's local, unauthenticated MCP endpoint."""
    if not isinstance(value, str):
        return False
    try:
        parsed = urlsplit(value)
        return bool(
            parsed.scheme == "http"
            and parsed.hostname == "127.0.0.1"
            and parsed.port
            and parsed.path == "/mcp"
            and parsed.username is None
            and parsed.password is None
            and not parsed.query
            and not parsed.fragment
        )
    except ValueError:
        return False


def desired_proxy(python: Path, proxy: Path) -> dict:
    """Build the Codex stdio entry managed by this installer."""
    return {
        "command": str(python),
        "args": [str(proxy)],
        "env_vars": ENV_VARS,
        "startup_timeout_sec": 90,
    }


def previous_proxy(python: Path, proxy: Path) -> dict:
    """Recognize the last managed configuration before KDE variables were added."""
    previous = desired_proxy(python, proxy)
    previous["env_vars"] = [
        name for name in ENV_VARS if name not in KDE_SESSION_ENV_VARS
    ]
    return previous


def read_marker(path: Path) -> dict | None:
    """Read the installer ownership record, rejecting foreign or damaged data."""
    if path.is_symlink():
        raise RuntimeError(f"Proxy ownership record is a symlink: {path}")
    try:
        marker = json.loads(path.read_text())
    except FileNotFoundError:
        return None
    except (OSError, ValueError) as exc:
        raise RuntimeError(f"Cannot read proxy ownership record: {path}") from exc
    fields = {
        "version",
        "configPath",
        "proxyPath",
        "python",
        "createdDirect",
        "createdMcpServers",
        "previousEnabled",
    }
    if (
        not isinstance(marker, dict)
        or set(marker) != fields
        or marker.get("version") != 1
        or not all(
            isinstance(marker.get(key), str) and Path(marker[key]).is_absolute()
            for key in ("configPath", "proxyPath", "python")
        )
        or not isinstance(marker.get("createdDirect"), bool)
        or not isinstance(marker.get("createdMcpServers"), bool)
        or not (
            marker.get("previousEnabled") is None
            or isinstance(marker.get("previousEnabled"), bool)
        )
        or (marker["createdDirect"] and marker["previousEnabled"] is not None)
        or (marker["createdMcpServers"] and not marker["createdDirect"])
    ):
        raise RuntimeError(f"Invalid proxy ownership record: {path}")
    return marker


def plan_enable(
    raw: bytes,
    config_path: Path,
    proxy: Path,
    legacy: Path,
    python: Path,
    marker: dict | None,
) -> tuple[bytes, dict]:
    """Plan a conflict-checked installation without changing the input config."""
    parsed = parse_config(raw)
    expected = copy.deepcopy(parsed)
    servers = parsed.get("mcp_servers", {})
    if not isinstance(servers, dict):
        raise RuntimeError("Codex mcp_servers is not a table")
    direct = servers.get(DIRECT_NAME)
    existing = servers.get(PROXY_NAME)
    desired = desired_proxy(python, proxy)
    if marker and (
        marker.get("configPath") != str(config_path)
        or marker.get("proxyPath") != str(proxy)
    ):
        raise RuntimeError(
            "The proxy is managed by a different configuration or installation"
        )
    if direct is not None and (
        not isinstance(direct, dict)
        or not valid_endpoint(direct.get("url"))
        or set(direct) - {"url", "enabled"}
        or not isinstance(direct.get("enabled", True), bool)
    ):
        raise RuntimeError(
            "The existing BrowserOS MCP entry has unsupported settings; left unchanged"
        )
    if marker is not None and (direct is None or direct.get("enabled") is not False):
        raise RuntimeError("The managed BrowserOS MCP entry was edited; left unchanged")
    if marker is not None and existing is None:
        raise RuntimeError(
            "The managed autostart MCP entry was removed; left unchanged"
        )
    if existing is not None:
        allowed = [
            desired,
            previous_proxy(python, proxy),
            desired_proxy(python, legacy),
            previous_proxy(python, legacy),
        ]
        if existing not in allowed:
            raise RuntimeError(
                "The autostart MCP name is already used by another configuration"
            )

    if marker is None:
        previous = (
            None if direct is None or "enabled" not in direct else direct["enabled"]
        )
        if (
            existing in (desired_proxy(python, legacy), previous_proxy(python, legacy))
            and previous is False
        ):
            previous = None
        marker = {
            "version": 1,
            "configPath": str(config_path),
            "proxyPath": str(proxy),
            "python": str(python),
            "createdDirect": direct is None,
            "createdMcpServers": "mcp_servers" not in parsed,
            "previousEnabled": previous,
        }
    text = raw.decode("utf-8")
    if direct is None:
        text = append_section(
            text, DIRECT_NAME, {"url": DEFAULT_ENDPOINT, "enabled": False}
        )
        expected.setdefault("mcp_servers", {})[DIRECT_NAME] = {
            "url": DEFAULT_ENDPOINT,
            "enabled": False,
        }
    else:
        if direct.get("enabled") is not False:
            text = set_direct_enabled(text, True, False)
        expected["mcp_servers"][DIRECT_NAME]["enabled"] = False
    if existing != desired:
        if existing is not None:
            text = remove_section(text, PROXY_NAME)
        text = append_section(text, PROXY_NAME, desired)
    expected.setdefault("mcp_servers", {})[PROXY_NAME] = desired
    result = text.encode("utf-8")
    if parse_config(result) != expected:
        raise RuntimeError("TOML layout cannot be changed safely; left unchanged")
    return result, marker


def plan_disable(raw: bytes, marker: dict) -> bytes:
    """Remove only the owned proxy entry and restore the original direct setting."""
    parsed = parse_config(raw)
    expected = copy.deepcopy(parsed)
    servers = parsed.get("mcp_servers", {})
    if not isinstance(servers, dict):
        raise RuntimeError("Codex mcp_servers is not a table")
    existing = servers.get(PROXY_NAME)
    proxy = Path(marker["proxyPath"])
    python = Path(marker["python"])
    if existing is not None and existing not in (
        desired_proxy(python, proxy),
        previous_proxy(python, proxy),
    ):
        raise RuntimeError("The autostart MCP entry was edited; left unchanged")
    direct = servers.get(DIRECT_NAME)
    if direct is not None and (
        not isinstance(direct, dict)
        or not valid_endpoint(direct.get("url"))
        or set(direct) - {"url", "enabled"}
        or direct.get("enabled") is not False
    ):
        raise RuntimeError("The direct BrowserOS MCP entry was edited; left unchanged")
    text = raw.decode("utf-8")
    if existing is not None:
        text = remove_section(text, PROXY_NAME)
        del expected["mcp_servers"][PROXY_NAME]
    if direct is not None and marker.get("createdDirect"):
        text = remove_section(text, DIRECT_NAME)
        del expected["mcp_servers"][DIRECT_NAME]
    elif direct is not None:
        previous = marker.get("previousEnabled")
        text = set_direct_enabled(text, previous is not None, bool(previous))
        if previous is None:
            del expected["mcp_servers"][DIRECT_NAME]["enabled"]
        else:
            expected["mcp_servers"][DIRECT_NAME]["enabled"] = previous
    if marker.get("createdMcpServers") and not expected.get("mcp_servers"):
        expected.pop("mcp_servers", None)
    result = text.encode("utf-8")
    if parse_config(result) != expected:
        raise RuntimeError("TOML layout cannot be restored safely; left unchanged")
    return result


def atomic_write(path: Path, content: bytes, previous: bytes | None = None) -> None:
    """Replace one file atomically after checking for concurrent edits."""
    path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    if path.is_symlink():
        raise RuntimeError(f"Refusing to replace a symlink: {path}")
    mode = stat.S_IMODE(path.stat().st_mode) if path.exists() else 0o600
    descriptor, temporary = tempfile.mkstemp(prefix=".browseros-mcp-", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as output:
            os.fchmod(output.fileno(), mode)
            output.write(content)
            output.flush()
            os.fsync(output.fileno())
        if previous is not None and config_bytes(path) != previous:
            raise RuntimeError(f"File changed during proxy setup: {path}")
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary):
            os.unlink(temporary)


def main() -> int:
    """Check, enable, or remove this installer's Codex integration."""
    if len(sys.argv) != 6 or sys.argv[1] not in {"check", "enable", "disable"}:
        print(
            "Usage: browseros_mcp_setup.py check|enable|disable CONFIG PROXY LEGACY PYTHON",
            file=sys.stderr,
        )
        return 2
    action = sys.argv[1]
    config_path, proxy, legacy, python = (
        Path(item).absolute() for item in sys.argv[2:]
    )
    marker_path = proxy.parent / MARKER_NAME
    try:
        raw = config_bytes(config_path)
        marker = read_marker(marker_path)
        if action == "disable":
            if marker is None:
                raise RuntimeError("The proxy has no installer ownership record")
            if marker.get("configPath") != str(config_path) or marker.get(
                "proxyPath"
            ) != str(proxy):
                raise RuntimeError(
                    "The proxy ownership record belongs to another installation"
                )
            updated = plan_disable(raw, marker)
            atomic_write(config_path, updated, raw)
            marker_path.unlink()
        else:
            updated, next_marker = plan_enable(
                raw, config_path, proxy, legacy, python, marker
            )
            if action == "enable":
                if config_bytes(config_path) != raw:
                    raise RuntimeError(
                        f"File changed during proxy setup: {config_path}"
                    )
                marker_changed = marker != next_marker
                old_marker = (
                    marker_path.read_bytes()
                    if marker_changed and marker is not None
                    else None
                )
                if marker_changed:
                    atomic_write(
                        marker_path, (json.dumps(next_marker, indent=2) + "\n").encode()
                    )
                try:
                    if updated != raw:
                        atomic_write(config_path, updated, raw)
                except Exception:
                    if marker_changed and old_marker is None:
                        marker_path.unlink()
                    elif marker_changed:
                        assert old_marker is not None
                        atomic_write(marker_path, old_marker)
                    raise
    except (OSError, RuntimeError, KeyError, TypeError) as exc:
        print(f"BrowserOS neo MCP setup failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
