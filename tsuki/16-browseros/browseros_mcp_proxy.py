#!/usr/bin/env python3
"""Start BrowserOS neo when needed and relay MCP stdio to its local HTTP server."""

from __future__ import annotations

import fcntl
import http.client
import json
import os
import stat
import subprocess
import sys
import time
import tomllib
import uuid
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from urllib.parse import urlsplit

import anyio
import httpx
from anyio.abc import TaskGroup
from anyio.streams.memory import MemoryObjectReceiveStream, MemoryObjectSendStream
from mcp.client.streamable_http import streamable_http_client
from mcp.server.stdio import stdio_server
from mcp.shared.message import SessionMessage
from mcp.types import (
    JSONRPCError,
    JSONRPCMessage,
    JSONRPCNotification,
    JSONRPCRequest,
    JSONRPCResponse,
)


STARTUP_TIMEOUT_SECONDS = 60.0
READY_POLL_SECONDS = 0.5
HEALTH_TIMEOUT_SECONDS = 1.0
HEARTBEAT_INTERVAL_SECONDS = 60.0
HEARTBEAT_TIMEOUT_SECONDS = 15.0
MARKER_NAME = ".browseros-neo-codex-mcp.json"


def installed_config_path() -> Path | None:
    """Find the Codex config recorded by the installation that owns this proxy."""
    script = Path(__file__).resolve()
    marker_path = script.parent / MARKER_NAME
    try:
        marker = json.loads(marker_path.read_text())
    except FileNotFoundError:
        return None
    except (OSError, ValueError) as exc:
        raise RuntimeError("Cannot read the BrowserOS proxy ownership record") from exc
    if (
        not isinstance(marker, dict)
        or marker.get("version") != 1
        or marker.get("proxyPath") != str(script)
        or not isinstance(marker.get("configPath"), str)
        or not Path(marker["configPath"]).is_absolute()
    ):
        raise RuntimeError("The BrowserOS proxy ownership record is invalid")
    return Path(marker["configPath"])


def read_endpoint() -> str:
    """Read the BrowserOS-managed endpoint, including any port changes."""
    config_path = installed_config_path() or Path.home() / ".codex" / "config.toml"
    try:
        with config_path.open("rb") as config_file:
            config = tomllib.load(config_file)
        endpoint = config["mcp_servers"]["browseros-neo"]["url"]
    except (OSError, KeyError, TypeError, tomllib.TOMLDecodeError) as exc:
        raise RuntimeError(
            "Cannot read the BrowserOS neo MCP URL from Codex config"
        ) from exc

    if not isinstance(endpoint, str):
        raise RuntimeError("The BrowserOS neo MCP URL must be a string")
    parsed = urlsplit(endpoint)
    try:
        port = parsed.port
    except ValueError as exc:
        raise RuntimeError("The BrowserOS neo MCP URL has an invalid port") from exc
    if (
        parsed.scheme != "http"
        or parsed.hostname != "127.0.0.1"
        or port is None
        or parsed.path != "/mcp"
        or parsed.username is not None
        or parsed.password is not None
        or parsed.query
        or parsed.fragment
    ):
        raise RuntimeError(
            "The BrowserOS neo MCP URL must be http://127.0.0.1:<port>/mcp"
        )
    return endpoint


def server_ready(endpoint: str) -> bool:
    """Check the BrowserOS readiness endpoint without using proxy environment settings."""
    parsed = urlsplit(endpoint)
    connection = http.client.HTTPConnection(
        parsed.hostname, parsed.port, timeout=HEALTH_TIMEOUT_SECONDS
    )
    try:
        connection.request("GET", "/system/ready")
        response = connection.getresponse()
        payload = response.read(8193)
    except (ConnectionError, OSError, http.client.HTTPException):
        return False
    finally:
        connection.close()

    try:
        report = json.loads(payload)
        connected = report["browser"]["connected"]
    except (ValueError, KeyError, TypeError) as exc:
        raise RuntimeError(
            "The MCP port is occupied by an unrecognized HTTP service"
        ) from exc
    if response.status == 200 and report.get("status") == "ok" and connected is True:
        return True
    if response.status == 503 and connected is False:
        return False
    raise RuntimeError(
        "The MCP port returned an unexpected BrowserOS readiness response"
    )


@asynccontextmanager
async def relay_context(
    endpoint: str,
    http_client: httpx.AsyncClient,
) -> AsyncIterator[
    tuple[
        MemoryObjectReceiveStream[SessionMessage | Exception],
        MemoryObjectSendStream[SessionMessage],
    ]
]:
    """Keep one upstream HTTP session for the lifetime of a downstream MCP session."""
    async with streamable_http_client(
        endpoint, http_client=http_client, terminate_on_close=False
    ) as (
        read_stream,
        write_stream,
        get_session_id,
    ):
        try:
            yield read_stream, write_stream
        finally:
            session_id = get_session_id()
            if session_id:
                try:
                    response = await http_client.delete(
                        endpoint, headers={"mcp-session-id": session_id}, timeout=5.0
                    )
                    if not response.is_success and response.status_code != 405:
                        print(
                            f"BrowserOS neo session cleanup returned HTTP {response.status_code}",
                            file=sys.stderr,
                        )
                except httpx.HTTPError as exc:
                    print(
                        f"BrowserOS neo session cleanup failed: {exc}", file=sys.stderr
                    )


@asynccontextmanager
async def local_http_client() -> AsyncIterator[httpx.AsyncClient]:
    """Keep BrowserOS traffic on loopback and permit long-lived MCP streams."""
    timeout = httpx.Timeout(connect=5.0, read=None, write=30.0, pool=30.0)
    async with httpx.AsyncClient(
        timeout=timeout, trust_env=False, follow_redirects=False
    ) as client:
        yield client


def lock_path() -> Path:
    """Select a private per-user location shared by concurrent proxy processes."""
    runtime_dir = os.environ.get("XDG_RUNTIME_DIR")
    directory = Path(runtime_dir) if runtime_dir else Path.home() / ".browseros-neo"
    directory.mkdir(mode=0o700, parents=True, exist_ok=True)
    directory_stat = directory.stat()
    if directory_stat.st_uid != os.getuid() or directory_stat.st_mode & 0o077:
        raise RuntimeError(
            f"BrowserOS startup lock directory is not private: {directory}"
        )
    return directory / "browseros-neo-mcp-autostart.lock"


def ensure_browser() -> str:
    """Start the browser once, then wait until its MCP service can reach it."""
    endpoint = read_endpoint()
    if server_ready(endpoint):
        return endpoint

    path = lock_path()
    flags = os.O_CREAT | os.O_RDWR | os.O_CLOEXEC | os.O_NOFOLLOW
    descriptor = os.open(path, flags, 0o600)
    with os.fdopen(descriptor, "r+") as lock_file:
        lock_stat = os.fstat(lock_file.fileno())
        if (
            not stat.S_ISREG(lock_stat.st_mode)
            or lock_stat.st_uid != os.getuid()
            or lock_stat.st_mode & 0o077
        ):
            raise RuntimeError(
                f"BrowserOS startup lock is not a private regular file: {path}"
            )
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        endpoint = read_endpoint()
        if server_ready(endpoint):
            return endpoint
        desktop = os.environ.get("XDG_CURRENT_DESKTOP", "").split(":", 1)[0].strip()
        kde_version = os.environ.get("KDE_SESSION_VERSION", "")
        # Chromium otherwise selects the KDE4 wallet and may lose access to saved data.
        if desktop == "KDE" and kde_version not in {"4", "5", "6"}:
            raise RuntimeError(
                "Cannot safely start BrowserOS neo: KDE_SESSION_VERSION is missing "
                "or invalid. Start Neo from the desktop or start Codex from a "
                "complete KDE session."
            )
        if installed_config_path() is None:
            launcher = Path.home() / ".local" / "bin" / "browseros-neo"
        else:
            launcher = Path(__file__).resolve().with_name("browseros-neo")
        if not launcher.is_file() or not os.access(launcher, os.X_OK):
            raise RuntimeError(
                f"BrowserOS neo launcher is missing or not executable: {launcher}"
            )
        if not os.environ.get("DISPLAY") and not os.environ.get("WAYLAND_DISPLAY"):
            raise RuntimeError(
                "Cannot start BrowserOS neo without a graphical desktop session"
            )
        print(
            "Starting BrowserOS neo and waiting for its MCP service...", file=sys.stderr
        )
        try:
            process = subprocess.Popen(
                [str(launcher)],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True,
            )
        except OSError as exc:
            raise RuntimeError(f"Could not start BrowserOS neo: {exc}") from exc

        deadline = time.monotonic() + STARTUP_TIMEOUT_SECONDS
        last_readiness_error: RuntimeError | None = None
        while time.monotonic() < deadline:
            endpoint = read_endpoint()
            try:
                if server_ready(endpoint):
                    return endpoint
                last_readiness_error = None
            except RuntimeError as exc:
                last_readiness_error = exc
            if process.poll() not in (None, 0):
                raise RuntimeError(
                    f"BrowserOS neo exited with status {process.returncode}"
                )
            time.sleep(READY_POLL_SECONDS)
    if last_readiness_error is not None:
        raise RuntimeError(
            f"BrowserOS neo did not become ready within 60 seconds: {last_readiness_error}"
        ) from last_readiness_error
    raise RuntimeError("BrowserOS neo did not become ready within 60 seconds")


class RelayState:
    """Track the proxy's private heartbeat without exposing it to the MCP host."""

    def __init__(self) -> None:
        self.initialized = anyio.Event()
        self.heartbeat_id: str | None = None
        self.heartbeat_done: anyio.Event | None = None
        self.heartbeat_error: JSONRPCError | None = None


async def forward_downstream(
    source: MemoryObjectReceiveStream[SessionMessage | Exception],
    destination: MemoryObjectSendStream[SessionMessage],
    task_group: TaskGroup,
    state: RelayState,
) -> None:
    """Forward host messages and start heartbeats after MCP initialization."""
    try:
        async for message in source:
            if isinstance(message, Exception):
                raise message
            await destination.send(message)
            root = message.message.root
            if (
                isinstance(root, JSONRPCNotification)
                and root.method == "notifications/initialized"
            ):
                state.initialized.set()
    finally:
        task_group.cancel_scope.cancel()


async def forward_upstream(
    source: MemoryObjectReceiveStream[SessionMessage | Exception],
    destination: MemoryObjectSendStream[SessionMessage],
    task_group: TaskGroup,
    state: RelayState,
) -> None:
    """Forward server messages while consuming the proxy's own ping replies."""
    try:
        async for message in source:
            if isinstance(message, Exception):
                raise message
            root = message.message.root
            if (
                isinstance(root, (JSONRPCResponse, JSONRPCError))
                and root.id == state.heartbeat_id
            ):
                if isinstance(root, JSONRPCError):
                    state.heartbeat_error = root
                if state.heartbeat_done is not None:
                    state.heartbeat_done.set()
                continue
            if (
                isinstance(root, JSONRPCError)
                and root.error.code == 32600
                and root.error.message == "Session terminated"
            ):
                error = root.error.model_copy(
                    update={
                        "message": (
                            "BrowserOS MCP session expired; the browser may still be running. "
                            "No operation was retried. Establish a new MCP connection and check "
                            "the browser target and tab group before continuing."
                        )
                    }
                )
                root = root.model_copy(update={"error": error})
                message = SessionMessage(
                    JSONRPCMessage(root), metadata=message.metadata
                )
            await destination.send(message)
    finally:
        task_group.cancel_scope.cancel()


async def keep_session_alive(
    destination: MemoryObjectSendStream[SessionMessage], state: RelayState
) -> None:
    """Prevent an idle upstream MCP session from expiring."""
    await state.initialized.wait()
    while True:
        await anyio.sleep(HEARTBEAT_INTERVAL_SECONDS)
        state.heartbeat_id = f"browseros-proxy-ping-{uuid.uuid4().hex}"
        state.heartbeat_done = anyio.Event()
        state.heartbeat_error = None
        ping = JSONRPCRequest(jsonrpc="2.0", id=state.heartbeat_id, method="ping")
        await destination.send(SessionMessage(JSONRPCMessage(ping)))
        with anyio.move_on_after(HEARTBEAT_TIMEOUT_SECONDS) as timeout:
            await state.heartbeat_done.wait()
        if timeout.cancel_called:
            print("BrowserOS neo MCP heartbeat timed out", file=sys.stderr)
            await state.heartbeat_done.wait()
        if state.heartbeat_error is not None:
            print(
                "BrowserOS neo MCP heartbeat failed; a new connection may be required",
                file=sys.stderr,
            )
            return
        state.heartbeat_id = None
        state.heartbeat_done = None


async def run_proxy(endpoint: str) -> None:
    """Relay MCP messages and keep the upstream session active."""
    async with (
        stdio_server() as (stdin_stream, stdout_stream),
        local_http_client() as client,
    ):
        async with relay_context(endpoint, client) as (upstream_read, upstream_write):
            async with anyio.create_task_group() as group:
                state = RelayState()
                group.start_soon(
                    forward_downstream, stdin_stream, upstream_write, group, state
                )
                group.start_soon(
                    forward_upstream, upstream_read, stdout_stream, group, state
                )
                group.start_soon(keep_session_alive, upstream_write, state)


def main() -> int:
    """Start the BrowserOS bridge and report startup failures to the MCP host."""
    try:
        endpoint = ensure_browser()
        anyio.run(run_proxy, endpoint)
    except (Exception, KeyboardInterrupt) as exc:
        print(f"BrowserOS neo MCP proxy failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
