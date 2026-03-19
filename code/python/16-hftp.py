# -*- coding: utf-8 -*-
# pip install ifaddr colorama legacy-cgi

import argparse
import atexit
import base64
import http.server
import html
import io
import inspect
import ipaddress
import mimetypes
import os
import re
import shutil
import signal
import socket
import socketserver
import subprocess
import sys
import threading
import time
import traceback
import webbrowser
from typing import List, Optional, Tuple
from urllib.parse import parse_qs, quote, unquote, urlparse

import cgi
import ifaddr

if sys.platform == "win32":
    from colorama import init as colorama_init

    colorama_init(autoreset=True)

DEBUG_MODE = False
BATCH_MODE = False
SERVER_INSTANCE = None
DEFAULT_PORT = 7888
EXIT_EVENT = threading.Event()
LOCAL_IPS = set()

FAVICON_ICO_BASE64 = "AAABAAIAEBAAAAEAIABoBAAAJgAAACAgAAABACAAqBAAAI4EAAAoAAAAEAAAACAAAAABACAAAAAAAAAEAAAAAAAAAAAAAAAAAAAAAAAA/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////+7u7v/h4eH/4eHh/+Hh4f/h4eH/4eHh/+Hh4f/h4eH/4eHh/+Hh4f/h4eH/4eHh/+Hh4f/h4eH/6enp//39/f///////////87Ozv89PT3/HR0d/x4eHv8eHh7/Hh4e/x4eHv8eHh7/Hh4e/x4eHv8eHh7/HR0d/ysrK/+oqKj///////////+IiIj/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/UlJS//v7+///////gICA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/0pKSv/5+fn//////4CAgP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/SkpK//n5+f//////gICA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/0pKSv/5+fn//////4CAgP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP9KSkr/+fn5//////+AgID/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/0pKSv/5+fn//////4CAgP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP9MTEz/+vr6//////+Dg4P/AAAA/wAAAP8AAAD/AAAA/wEBAf8FBQX/BQUF/wUFBf8FBQX/BQUF/wUFBf8FBQX/BQUF/wUFBf8LCwv/iYmJ////////////t7e3/xkZGf8EBAT/BQUF/wcHB/9iYmL/tra2/7a2tv+2trb/tra2/7a2tv+2trb/xMTE//T09P////////////v7+//Pz8//tra2/7a2tv+7u7v/7+/v/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////wAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAoAAAAIAAAAEAAAAABACAAAAAAAAAQAAAAAAAAAAAAAAAAAAAAAAAA///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////7+/v/6urq/+Pj4//j4+P/4+Pj/+Pj4//j4+P/4+Pj/+Pj4//j4+P/4+Pj/+Pj4//j4+P/4+Pj/+Pj4//j4+P/4+Pj/+Pj4//j4+P/4+Pj/+Pj4//j4+P/4+Pj/+Pj4//j4+P/5OTk//Pz8//+/v7/////////////////////////////////5+fn/3t7e/8vLy//Gxsb/xwcHP8cHBz/HBwc/xwcHP8cHBz/HBwc/xwcHP8cHBz/HBwc/xwcHP8cHBz/HBwc/xwcHP8cHBz/HBwc/xwcHP8fHx//TU1N/7W1tf/9/f3///////////////////////39/f96enr/AQEB/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/JSUl/9TU1P//////////////////////6urq/zAwMP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/CAgL/lJSU///////////////////////j4+P/HBwc/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/4CAgP//////////////////////4+Pj/xwcHP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/gICA///////////////////////j4+P/HBwc/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/+AgID//////////////////////+Pj4/8cHBz/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/4CAgP//////////////////////4+Pj/xwcHP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/4ODg///////////////////////4+Pj/xwcHP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8MDAz/sbGx///////////////////////k5OT/Hx8f/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/CwsL/2FhYf/w8PD///////////////////////Pz8/9OTk7/AAAA/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/wAAAP8BAQH/RkZG/4GBgf+AgID/f39//39/f/9/f3//f39//39/f/9/f3//f39//39/f/9/f3//f39//4ODg/+xsbH/8PDw/////////////////////////////////7W1tf8kJCT/AwMD/wAAAP8AAAD/AAAA/wAAAP8AAAD/AAAA/09PT//k5OT//////////////////////////////////////////////////////////////////////////////////////////////////////////////////f39/9TU1P+Tk5P/f39//39/f/9/f3//f39//39/f/+JiYn/4+Pj/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////wAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
FAVICON_ICO_BYTES = base64.b64decode(FAVICON_ICO_BASE64)


class NewFileTracker:
    """Track files created or uploaded during the current server session.

    A file is considered "new" if:
    - It was explicitly registered (uploaded via this server), or
    - Its mtime is >= the server start time (externally added while running).

    Uses os.path.realpath for cross-platform path normalization (Windows included).
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._registered: set = set()
        self._start_time: float = time.time()

    def register(self, filepath: str) -> None:
        with self._lock:
            self._registered.add(os.path.realpath(filepath))

    def remove(self, filepath: str) -> None:
        with self._lock:
            self._registered.discard(os.path.realpath(filepath))

    def is_new(self, filepath: str) -> bool:
        real = os.path.realpath(filepath)
        with self._lock:
            if real in self._registered:
                return True
        try:
            return os.path.getmtime(filepath) >= self._start_time
        except OSError:
            return False


NEW_FILE_TRACKER = NewFileTracker()

TEXT_EXTENSIONS = {
    ".txt",
    ".md",
    ".markdown",
    ".rst",
    ".log",
    ".ini",
    ".cfg",
    ".conf",
    ".json",
    ".xml",
    ".yaml",
    ".yml",
    ".toml",
    ".py",
    ".js",
    ".ts",
    ".jsx",
    ".tsx",
    ".css",
    ".scss",
    ".less",
    ".html",
    ".htm",
    ".c",
    ".cpp",
    ".h",
    ".hpp",
    ".java",
    ".go",
    ".rs",
    ".rb",
    ".php",
    ".pl",
    ".lua",
    ".sh",
    ".bash",
    ".zsh",
    ".fish",
    ".ps1",
    ".bat",
    ".cmd",
    ".sql",
    ".r",
    ".m",
    ".swift",
    ".kt",
    ".scala",
    ".clj",
    ".hs",
    ".ex",
    ".exs",
    ".vue",
    ".svelte",
    ".astro",
    ".env",
    ".gitignore",
    ".dockerignore",
    ".editorconfig",
    ".csv",
    ".tsv",
    "Makefile",
    "Dockerfile",
    "Vagrantfile",
    "Jenkinsfile",
    "Rakefile",
}

TEXT_MIME_PREFIXES = (
    "text/",
    "application/json",
    "application/xml",
    "application/javascript",
)

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".gif",
    ".bmp",
    ".webp",
    ".svg",
    ".ico",
    ".tiff",
    ".tif",
    ".avif",
}

VIDEO_EXTENSIONS = {
    ".mp4",
    ".webm",
    ".ogg",
    ".ogv",
    ".mov",
    ".m4v",
    ".3gp",
    ".3g2",
}

VIDEO_MIME_TYPES = {
    ".mp4": "video/mp4",
    ".m4v": "video/mp4",
    ".webm": "video/webm",
    ".ogg": "video/ogg",
    ".ogv": "video/ogg",
    ".mov": "video/quicktime",
    ".3gp": "video/3gpp",
    ".3g2": "video/3gpp2",
}


def is_text_file(filepath: str) -> bool:
    """Check if a file is a text file that can be previewed"""
    basename = os.path.basename(filepath)
    ext = os.path.splitext(filepath)[1].lower()

    if basename in TEXT_EXTENSIONS or ext in TEXT_EXTENSIONS:
        return True

    mime_type, _ = mimetypes.guess_type(filepath)
    if mime_type and any(mime_type.startswith(prefix) for prefix in TEXT_MIME_PREFIXES):
        return True

    return False


def is_image_file(filepath: str) -> bool:
    """Check if a file is an image that can be previewed inline."""
    ext = os.path.splitext(filepath)[1].lower()
    return ext in IMAGE_EXTENSIONS


def is_video_file(filepath: str) -> bool:
    """Check if a file is a browser-playable video."""
    ext = os.path.splitext(filepath)[1].lower()
    return ext in VIDEO_EXTENSIONS


def get_syntax_language(filepath: str) -> str:
    """Get syntax highlighting language based on file extension"""
    ext = os.path.splitext(filepath)[1].lower()
    lang_map = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".jsx": "jsx",
        ".tsx": "tsx",
        ".json": "json",
        ".html": "html",
        ".htm": "html",
        ".css": "css",
        ".xml": "xml",
        ".yaml": "yaml",
        ".yml": "yaml",
        ".md": "markdown",
        ".markdown": "markdown",
        ".sh": "bash",
        ".bash": "bash",
        ".zsh": "bash",
        ".sql": "sql",
        ".c": "c",
        ".cpp": "cpp",
        ".h": "c",
        ".hpp": "cpp",
        ".java": "java",
        ".go": "go",
        ".rs": "rust",
        ".rb": "ruby",
        ".php": "php",
        ".lua": "lua",
        ".swift": "swift",
        ".kt": "kotlin",
        ".r": "r",
        ".toml": "toml",
        ".ini": "ini",
        ".conf": "ini",
    }
    return lang_map.get(ext, "plaintext")


class CLIStyle:
    """CLI tool unified style config"""

    COLORS = {
        "TITLE": 7,
        "SUB_TITLE": 2,
        "CONTENT": 3,
        "EXAMPLE": 7,
        "WARNING": 4,
        "ERROR": 2,
        "SUCCESS": 3,
    }

    @staticmethod
    def color(text: str = "", color: int = None) -> str:
        """Unified color processing function"""
        if color is None:
            color = CLIStyle.COLORS["CONTENT"]
        color_table = {
            0: "{}",
            1: "\033[1;30m{}\033[0m",
            2: "\033[1;31m{}\033[0m",
            3: "\033[1;32m{}\033[0m",
            4: "\033[1;33m{}\033[0m",
            5: "\033[1;34m{}\033[0m",
            6: "\033[1;35m{}\033[0m",
            7: "\033[1;36m{}\033[0m",
            8: "\033[1;37m{}\033[0m",
        }
        return color_table[color].format(text)


def debug(*args, file: Optional[str] = None, append: bool = True, **kwargs) -> None:
    """Print debug information with source file and line number."""
    if not DEBUG_MODE:
        return

    frame = inspect.currentframe().f_back
    info = inspect.getframeinfo(frame)

    file_name = os.path.basename(info.filename)
    output = f"{CLIStyle.color(file_name, CLIStyle.COLORS['SUCCESS'])}: {CLIStyle.color(str(info.lineno), CLIStyle.COLORS['WARNING'])} {CLIStyle.color('|', CLIStyle.COLORS['TITLE'])} "

    for i, arg in enumerate(args):
        arg_str = str(arg)
        output += f"{CLIStyle.color(arg_str, CLIStyle.COLORS['SUB_TITLE'])} "

    for k, v in kwargs.items():
        output += f"{CLIStyle.color(k + '=', 6)}{CLIStyle.color(str(v), CLIStyle.COLORS['SUB_TITLE'])} "

    output += "\n"

    if file:
        mode = "a" if append else "w"
        with open(file, mode) as f:
            clean_output = re.sub(r"\033\[\d+;\d+m|\033\[0m", "", output)
            f.write(clean_output)
    else:
        print(output, end="")


def access_log(
    handler: "EnhancedHTTPRequestHandler",
    action: str,
    status: str,
    path: Optional[str] = None,
) -> None:
    """Log upload/delete/modify/view/download to stdout: IP, time, action, status (and optional path)."""
    ip = get_request_ip(handler)
    ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    try:
        status_int = int(status)
    except (TypeError, ValueError):
        status_int = None

    if status_int is None:
        status_color = CLIStyle.COLORS["WARNING"]
    elif 200 <= status_int <= 299:
        status_color = CLIStyle.COLORS["SUCCESS"]
    elif 300 <= status_int <= 399:
        status_color = CLIStyle.COLORS["TITLE"]
    elif 400 <= status_int <= 499:
        status_color = CLIStyle.COLORS["WARNING"]
    else:
        status_color = CLIStyle.COLORS["ERROR"]

    action_color_map = {
        "upload": CLIStyle.COLORS["SUCCESS"],
        "modify": CLIStyle.COLORS["WARNING"],
        "delete": CLIStyle.COLORS["ERROR"],
        "view": CLIStyle.COLORS["TITLE"],
        "download": 5,
    }
    action_color = action_color_map.get(action, CLIStyle.COLORS["CONTENT"])

    parts = [
        CLIStyle.color(ts, 1),
        CLIStyle.color(ip, 6),
        CLIStyle.color(action, action_color),
        CLIStyle.color(status, status_color),
    ]
    if path:
        parts.append(CLIStyle.color(path, CLIStyle.COLORS["SUB_TITLE"]))
    print(" ".join(parts), flush=True)


def _extract_ip(value: str) -> Optional[str]:
    raw = value.strip()
    if not raw or raw.lower() == "unknown":
        return None

    raw = raw.strip('"')

    if raw.lower().startswith("for="):
        raw = raw.split("=", 1)[1].strip()
        raw = raw.strip('"')

    if raw.startswith("[") and "]" in raw:
        raw = raw[1 : raw.index("]")]

    # Handle "IPv4:port" forms
    if raw.count(":") == 1 and "." in raw:
        raw = raw.split(":", 1)[0]

    try:
        return str(ipaddress.ip_address(raw))
    except ValueError:
        return None


def get_request_ip(handler: http.server.BaseHTTPRequestHandler) -> str:
    local_ips = LOCAL_IPS or set()

    fallback = "?"
    if handler.client_address:
        candidate = _extract_ip(handler.client_address[0])
        if candidate:
            fallback = candidate

    candidates: List[str] = []
    try:
        xff = handler.headers.get("X-Forwarded-For")
        if xff:
            candidates.extend([p.strip() for p in xff.split(",") if p.strip()])
    except Exception:
        pass

    for header_name in (
        "X-Real-IP",
        "CF-Connecting-IP",
        "True-Client-IP",
        "X-Client-IP",
    ):
        try:
            v = handler.headers.get(header_name)
            if v:
                candidates.append(v)
        except Exception:
            pass

    try:
        forwarded = handler.headers.get("Forwarded")
        if forwarded:
            for m in re.finditer(r"for=([^;,\s]+)", forwarded, flags=re.IGNORECASE):
                candidates.append(m.group(1))
    except Exception:
        pass

    # Prefer a non-local (server-interface) IP; scan from right to left to handle
    # both "left=client" and "right=client" proxy conventions.
    for raw in reversed(candidates):
        ip = _extract_ip(raw)
        if not ip:
            continue
        if ip in local_ips:
            continue
        return ip

    for raw in candidates:
        ip = _extract_ip(raw)
        if ip:
            return ip

    return fallback


def emergency_exit():
    """Force process termination with extreme prejudice"""
    debug("Emergency exit called")
    global SERVER_INSTANCE
    if SERVER_INSTANCE:
        try:
            SERVER_INSTANCE.socket.close()
        except Exception:
            pass
    try:
        print(CLIStyle.color("Server stopped", CLIStyle.COLORS["SUCCESS"]))
    except Exception:
        # Avoid reentrant stdout errors during signal/shutdown
        pass
    # os._exit bypasses cleanup but guarantees termination on all platforms
    os._exit(0)


def force_exit_after(seconds: int = 2):
    """Schedule a forced exit after specified seconds"""
    debug(f"Scheduling forced exit in {seconds} seconds")
    time.sleep(seconds)
    emergency_exit()


def divider(title: str = "", width: int = 80, char: str = "-") -> str:
    """Create a divider with optional centered title."""
    if not title:
        return char * width

    side_width = (width - len(title) - 2) // 2
    if side_width <= 0:
        return title

    return f"{char * side_width} {title} {char * side_width}"


def get_all_ips() -> List[str]:
    """Get all local non-loopback IPv4 addresses."""
    ips = []
    adapters = ifaddr.get_adapters()
    for adapter in adapters:
        for ip in adapter.ips:
            if ip.is_IPv4 and ip.ip != "127.0.0.1":
                if ip.ip not in ips:
                    ips.append(ip.ip)
    return ips


def confirm_action(prompt: str) -> bool:
    """Request user confirmation, auto-confirms in batch mode."""
    if BATCH_MODE:
        debug(f"Batch mode: auto-confirming: {prompt}")
        print(
            CLIStyle.color(
                f"{prompt} (auto-yes in batch mode)", CLIStyle.COLORS["CONTENT"]
            )
        )
        return True
    response = input(f"{prompt} (y/n): ").lower().strip()
    return response in ("y", "yes")


def signal_handler(sig, frame):
    """Handle interrupt signals for graceful shutdown."""
    print(CLIStyle.color("\nShutting down server...", CLIStyle.COLORS["WARNING"]))
    threading.Thread(target=force_exit_after, args=(1,), daemon=True).start()

    try:
        global SERVER_INSTANCE, EXIT_EVENT
        EXIT_EVENT.set()
        if SERVER_INSTANCE:
            debug("Signal handler shutting down server")
            SERVER_INSTANCE.running = False
    except Exception as e:
        debug("Error in signal handler", error=str(e))

    emergency_exit()


def get_process_using_port(port: int) -> Optional[Tuple[str, str]]:
    """Find process occupying specified port, returns (pid, command) or None."""
    try:
        try:
            result = subprocess.run(
                ["lsof", "-i", f":{port}", "-t"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0 and result.stdout.strip():
                pid = result.stdout.strip().split("\n")[0]
                cmd_result = subprocess.run(
                    ["ps", "-p", pid, "-o", "comm="],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )
                if cmd_result.returncode == 0:
                    command = cmd_result.stdout.strip()
                    return (pid, command)
                return (pid, "unknown")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        # Fallback: netstat
        try:
            result = subprocess.run(
                ["netstat", "-tlnp"], capture_output=True, text=True, timeout=5
            )
            if result.returncode == 0:
                for line in result.stdout.split("\n"):
                    if f":{port} " in line and "LISTEN" in line:
                        parts = line.split()
                        if len(parts) > 6 and "/" in parts[6]:
                            pid_info = parts[6].split("/")
                            if len(pid_info) >= 2:
                                return (pid_info[0], pid_info[1])
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

        # Fallback: ss
        try:
            result = subprocess.run(
                ["ss", "-tlnp", f"sport = :{port}"],
                capture_output=True,
                text=True,
                timeout=5,
            )
            if result.returncode == 0:
                for line in result.stdout.split("\n"):
                    if f":{port} " in line:
                        if "users:" in line:
                            users_part = line.split("users:")[1]
                            if "pid=" in users_part:
                                pid = (
                                    users_part.split("pid=")[1]
                                    .split(",")[0]
                                    .split(")")[0]
                                )
                                if '"' in users_part:
                                    command = users_part.split('"')[1]
                                    return (pid, command)
                                return (pid, "unknown")
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass

    except Exception as e:
        debug("Error finding process using port", error=str(e))

    return None


def kill_process_by_pid(pid: str) -> bool:
    """Force terminate process by PID, returns True on success."""
    try:
        subprocess.run(["kill", pid], capture_output=True, text=True, timeout=5)
        time.sleep(1)

        check_result = subprocess.run(
            ["kill", "-0", pid], capture_output=True, text=True, timeout=5
        )
        if check_result.returncode != 0:
            return True

        # Graceful kill failed, force terminate
        force_result = subprocess.run(
            ["kill", "-9", pid], capture_output=True, text=True, timeout=5
        )

        return force_result.returncode == 0

    except Exception as e:
        debug("Error killing process", pid=pid, error=str(e))
        return False


class ColoredArgumentParser(argparse.ArgumentParser):
    """Unified command line argument parser"""

    def _format_action_invocation(self, action):
        if not action.option_strings:
            (metavar,) = self._metavar_formatter(action, action.dest)(1)
            return metavar
        else:
            parts = []
            if action.nargs == 0:
                parts.extend(
                    map(
                        lambda x: CLIStyle.color(x, CLIStyle.COLORS["SUB_TITLE"]),
                        action.option_strings,
                    )
                )
            else:
                default = action.dest.upper()
                args_string = self._format_args(action, default)
                for option_string in action.option_strings:
                    parts.append(
                        CLIStyle.color(
                            f"{option_string} {args_string}",
                            CLIStyle.COLORS["SUB_TITLE"],
                        )
                    )
            return ", ".join(parts)

    def format_help(self):
        formatter = self._get_formatter()

        # Add description
        if self.description:
            formatter.add_text(
                CLIStyle.color(self.description, CLIStyle.COLORS["TITLE"])
            )

        # Add usage
        formatter.add_usage(self.usage, self._actions, self._mutually_exclusive_groups)

        # Add argument groups
        formatter.add_text(
            CLIStyle.color("\nOptional Arguments:", CLIStyle.COLORS["TITLE"])
        )
        for action_group in self._action_groups:
            formatter.start_section(action_group.title)
            formatter.add_arguments(action_group._group_actions)
            formatter.end_section()

        # Add examples and notes
        if self.epilog:
            formatter.add_text(self.epilog)

        return formatter.format_help()


class EnhancedHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Enhanced HTTP request handler with file upload and download support"""

    def do_GET(self) -> None:
        """Handle GET requests with preview and Range support."""
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)
        if parsed.path == "/favicon.ico":
            try:
                self.send_response(200)
                self.send_header("Content-Type", "image/x-icon")
                self.send_header("Content-Length", str(len(FAVICON_ICO_BYTES)))
                self.end_headers()
                self.wfile.write(FAVICON_ICO_BYTES)
            except (BrokenPipeError, ConnectionResetError):
                # Client may cancel favicon request; avoid noisy stack traces.
                pass
            return
        path = self._translate_path_for_read(parsed.path)

        if os.path.isfile(path):
            if query.get("preview", ["0"])[0] == "1":
                access_log(self, "view", "200", path)
                if is_text_file(path):
                    self.serve_text_preview(path)
                elif is_image_file(path):
                    self.serve_image_preview(path)
                elif is_video_file(path):
                    self.serve_video_preview(path)
                else:
                    self._serve_ranged(path)
            else:
                self._serve_ranged(path, log_action="download")
        elif os.path.isdir(path):
            if not parsed.path.endswith("/"):
                location = parsed.path + "/"
                if parsed.query:
                    location += "?" + parsed.query
                self.send_response(301)
                self.send_header("Location", location)
                self.end_headers()
                return

            self.path = parsed.path
            f = self.list_directory(path)
            if f:
                try:
                    shutil.copyfileobj(f, self.wfile)
                except (BrokenPipeError, ConnectionResetError):
                    pass
                finally:
                    f.close()
        else:
            self.path = parsed.path
            super().do_GET()

    def _serve_ranged(self, filepath: str, log_action: Optional[str] = None) -> None:
        """Serve a file with HTTP Range request support. log_action: 'download' or None (no log)."""
        try:
            file_size = os.path.getsize(filepath)
        except OSError:
            if log_action:
                access_log(self, log_action, "404", filepath)
            self.send_error(404, "File not found")
            return

        mime_type, _ = mimetypes.guess_type(filepath)
        if not mime_type:
            mime_type = "application/octet-stream"
        if mime_type.startswith("text/") and "charset" not in mime_type:
            mime_type += "; charset=utf-8"

        range_header = self.headers.get("Range")
        if not range_header:
            self.send_response(200)
            if log_action:
                access_log(self, log_action, "200", filepath)
            self.send_header("Content-Type", mime_type)
            self.send_header("Content-Length", str(file_size))
            self.send_header("Accept-Ranges", "bytes")
            self.end_headers()
            try:
                with open(filepath, "rb") as f:
                    shutil.copyfileobj(f, self.wfile)
            except (BrokenPipeError, ConnectionResetError):
                pass
            return

        try:
            spec = range_header.replace("bytes=", "")
            start_str, end_str = spec.split("-", 1)
            start = int(start_str) if start_str else 0
            end = int(end_str) if end_str else file_size - 1
        except (ValueError, AttributeError):
            if log_action:
                access_log(self, log_action, "416", filepath)
            self.send_error(416, "Range Not Satisfiable")
            return

        end = min(end, file_size - 1)
        if start < 0 or start > end or start >= file_size:
            if log_action:
                access_log(self, log_action, "416", filepath)
            self.send_response(416)
            self.send_header("Content-Range", f"bytes */{file_size}")
            self.end_headers()
            return

        length = end - start + 1
        self.send_response(206)
        if log_action:
            access_log(self, log_action, "206", filepath)
        self.send_header("Content-Type", mime_type)
        self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
        self.send_header("Content-Length", str(length))
        self.send_header("Accept-Ranges", "bytes")
        self.end_headers()

        try:
            with open(filepath, "rb") as f:
                f.seek(start)
                remaining = length
                chunk = 64 * 1024
                while remaining > 0:
                    data = f.read(min(chunk, remaining))
                    if not data:
                        break
                    self.wfile.write(data)
                    remaining -= len(data)
        except (BrokenPipeError, ConnectionResetError):
            pass

    def serve_text_preview(self, filepath: str) -> None:
        """Serve a text file with syntax highlighting preview"""
        try:
            with open(filepath, "r", encoding="utf-8", errors="replace") as f:
                content = f.read()
        except Exception as e:
            self.send_error(500, f"Cannot read file: {str(e)}")
            return

        filename = os.path.basename(filepath)
        file_size = self._format_size(os.path.getsize(filepath))
        language = get_syntax_language(filepath)
        line_count = content.count("\n") + 1
        escaped_content = html.escape(content)

        html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(filename)} - Preview</title>
<script>
(function() {{
    const t = localStorage.getItem('hftp-theme') || 'light';
    document.documentElement.setAttribute('data-theme', t);
}})();
</script>
<link rel="stylesheet" id="hljs-theme" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github.min.css">
<script>
(function() {{
    const t = localStorage.getItem('hftp-theme');
    if (t === 'dark') {{
        document.getElementById('hljs-theme').href =
            'https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github-dark.min.css';
    }}
}})();
</script>
<style>
:root {{
    --bg-primary: #ffffff;
    --bg-secondary: #f6f8fa;
    --bg-tertiary: #eaeef2;
    --border-color: #d0d7de;
    --text-primary: #1f2328;
    --text-secondary: #656d76;
    --accent-blue: #0969da;
    --accent-green: #1a7f37;
    --hover-bg: rgba(208, 215, 222, 0.32);
}}
[data-theme="dark"] {{
    --bg-primary: #0d1117;
    --bg-secondary: #161b22;
    --bg-tertiary: #21262d;
    --border-color: #30363d;
    --text-primary: #c9d1d9;
    --text-secondary: #8b949e;
    --accent-blue: #58a6ff;
    --accent-green: #3fb950;
    --hover-bg: rgba(48, 54, 61, 0.5);
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
html {{ font-size: 18px; }}
body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
    background: var(--bg-primary);
    color: var(--text-primary);
    line-height: 1.6;
    transition: background 0.3s, color 0.3s;
}}
.container {{
    max-width: 1600px;
    margin: 0 auto;
    padding: 1.5rem;
}}
.toolbar {{
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 8px 8px 0 0;
    padding: 0.75rem 1rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 0.75rem;
}}
.file-info {{
    display: flex;
    align-items: center;
    gap: 1rem;
    flex-wrap: wrap;
}}
.file-info h1 {{
    font-size: 1rem;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}}
.file-meta {{
    display: flex;
    gap: 1rem;
    font-size: 0.8rem;
    color: var(--text-secondary);
}}
.file-meta span {{
    display: flex;
    align-items: center;
    gap: 0.25rem;
}}
.toolbar-actions {{
    display: flex;
    gap: 0.5rem;
}}
.btn {{
    padding: 0.4rem 0.75rem;
    font-size: 0.8rem;
    font-weight: 500;
    border: 1px solid var(--border-color);
    border-radius: 6px;
    background: var(--bg-tertiary);
    color: var(--text-primary);
    cursor: pointer;
    text-decoration: none;
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
    transition: all 0.15s;
}}
.btn:hover {{
    background: var(--hover-bg);
}}
.btn-primary {{
    background: var(--accent-green);
    border-color: var(--accent-green);
    color: #fff;
}}
.btn-primary:hover {{
    opacity: 0.9;
}}
.code-container {{
    border: 1px solid var(--border-color);
    border-top: none;
    border-radius: 0 0 8px 8px;
    overflow: hidden;
}}
.code-wrapper {{
    display: flex;
    overflow-x: auto;
}}
.line-numbers {{
    background: var(--bg-tertiary);
    padding: 1rem 0;
    text-align: right;
    user-select: none;
    border-right: 1px solid var(--border-color);
    flex-shrink: 0;
}}
.line-numbers span {{
    display: block;
    padding: 0 0.75rem;
    font-family: 'SF Mono', 'Fira Code', Consolas, monospace;
    font-size: 0.85rem;
    line-height: 1.6;
    color: var(--text-secondary);
}}
pre {{
    margin: 0;
    padding: 1rem;
    background: var(--bg-secondary);
    overflow-x: auto;
    flex: 1;
}}
pre code {{
    font-family: 'SF Mono', 'Fira Code', Consolas, monospace;
    font-size: 0.85rem;
    line-height: 1.6;
    background: transparent !important;
}}
.hljs {{ background: transparent !important; }}

/* Toast */
.toast {{
    position: fixed;
    bottom: 1.5rem;
    right: 1.5rem;
    padding: 0.75rem 1.25rem;
    background: var(--accent-green);
    color: #fff;
    border-radius: 6px;
    font-size: 0.9rem;
    opacity: 0;
    transform: translateY(20px);
    transition: all 0.3s;
    z-index: 1000;
}}
.toast.show {{
    opacity: 1;
    transform: translateY(0);
}}

@media (max-width: 768px) {{
    html {{ font-size: 16px; }}
    .toolbar {{
        flex-direction: column;
        align-items: flex-start;
    }}
    .file-meta {{
        flex-wrap: wrap;
    }}
}}
</style>
</head>
<body>
<div class="container">
    <div class="toolbar">
        <div class="file-info">
            <h1>📄 {html.escape(filename)}</h1>
            <div class="file-meta">
                <span>📏 {file_size}</span>
                <span>📝 {line_count} lines</span>
                <span>💻 {language}</span>
            </div>
        </div>
        <div class="toolbar-actions">
            <a href="./" class="btn">← Back</a>
            <button class="btn" onclick="toggleTheme()"><span id="themeIcon">🌙</span></button>
            <button class="btn" onclick="copyContent()">📋 Copy</button>
            <a href="{quote(os.path.basename(filepath))}" class="btn btn-primary" download>⬇️ Download</a>
        </div>
    </div>
    <div class="code-container">
        <div class="code-wrapper">
            <div class="line-numbers" id="lineNumbers"></div>
            <pre><code class="language-{language}" id="codeContent">{escaped_content}</code></pre>
        </div>
    </div>
</div>
<div class="toast" id="toast">Copied to clipboard!</div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/highlight.min.js"></script>
<script>
document.addEventListener('DOMContentLoaded', function() {{
    initTheme();
    hljs.highlightAll();
    
    const code = document.getElementById('codeContent');
    const lineNumbers = document.getElementById('lineNumbers');
    const lines = code.textContent.split('\\n');
    
    for (let i = 1; i <= lines.length; i++) {{
        const span = document.createElement('span');
        span.textContent = i;
        lineNumbers.appendChild(span);
    }}
}});

function copyContent() {{
    const code = document.getElementById('codeContent');
    navigator.clipboard.writeText(code.textContent).then(function() {{
        const toast = document.getElementById('toast');
        toast.classList.add('show');
        setTimeout(() => toast.classList.remove('show'), 2000);
    }});
}}

function initTheme() {{
    const saved = localStorage.getItem('hftp-theme');
    const theme = saved || 'light';
    applyTheme(theme);
}}

function toggleTheme() {{
    const current = document.documentElement.getAttribute('data-theme') || 'light';
    const next = current === 'dark' ? 'light' : 'dark';
    applyTheme(next);
    localStorage.setItem('hftp-theme', next);
}}

function applyTheme(theme) {{
    document.documentElement.setAttribute('data-theme', theme);
    document.getElementById('themeIcon').textContent = theme === 'dark' ? '☀️' : '🌙';
    const hljsTheme = document.getElementById('hljs-theme');
    hljsTheme.href = theme === 'dark' 
        ? 'https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github-dark.min.css'
        : 'https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github.min.css';
}}
</script>
</body>
</html>'''

        encoded = html_content.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def serve_image_preview(self, filepath: str) -> None:
        """Serve an image file with an inline preview page."""
        filename = os.path.basename(filepath)
        file_size = self._format_size(os.path.getsize(filepath))
        ext = os.path.splitext(filename)[1].lower()
        img_url = quote(filename)

        html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(filename)} - Preview</title>
<script>(function(){{const t=localStorage.getItem('hftp-theme')||'light';document.documentElement.setAttribute('data-theme',t);}})();</script>
<style>
:root {{
    --bg-primary: #ffffff;
    --bg-secondary: #f6f8fa;
    --bg-tertiary: #eaeef2;
    --border-color: #d0d7de;
    --text-primary: #1f2328;
    --text-secondary: #656d76;
    --accent-green: #1a7f37;
    --hover-bg: rgba(208, 215, 222, 0.32);
    --checker-a: #c8c8c8;
    --checker-b: #f0f0f0;
}}
[data-theme="dark"] {{
    --bg-primary: #0d1117;
    --bg-secondary: #161b22;
    --bg-tertiary: #21262d;
    --border-color: #30363d;
    --text-primary: #c9d1d9;
    --text-secondary: #8b949e;
    --accent-green: #3fb950;
    --hover-bg: rgba(48, 54, 61, 0.5);
    --checker-a: #3a3a3a;
    --checker-b: #2a2a2a;
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
html {{ font-size: 18px; }}
body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
    background: var(--bg-primary);
    color: var(--text-primary);
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    transition: background 0.3s, color 0.3s;
}}
.container {{
    max-width: 1400px;
    margin: 0 auto;
    padding: 1.5rem;
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 1rem;
}}
.toolbar {{
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 0.75rem 1rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 0.75rem;
}}
.file-info {{ display: flex; align-items: center; gap: 1rem; flex-wrap: wrap; }}
.file-info h1 {{ font-size: 1rem; font-weight: 600; }}
.file-meta {{
    display: flex;
    gap: 1rem;
    font-size: 0.8rem;
    color: var(--text-secondary);
}}
.toolbar-actions {{ display: flex; gap: 0.5rem; align-items: center; }}
.btn {{
    padding: 0.4rem 0.75rem;
    font-size: 0.8rem;
    font-weight: 500;
    border: 1px solid var(--border-color);
    border-radius: 6px;
    background: var(--bg-tertiary);
    color: var(--text-primary);
    cursor: pointer;
    text-decoration: none;
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
    transition: all 0.15s;
    user-select: none;
}}
.btn:hover {{ background: var(--hover-bg); }}
.btn-primary {{
    background: var(--accent-green);
    border-color: var(--accent-green);
    color: #fff;
}}
.btn-primary:hover {{ opacity: 0.9; }}
.zoom-controls {{
    display: flex;
    align-items: center;
    gap: 0.25rem;
    background: var(--bg-tertiary);
    border: 1px solid var(--border-color);
    border-radius: 6px;
    padding: 0.2rem 0.4rem;
}}
.zoom-btn {{
    width: 1.6rem;
    height: 1.6rem;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1rem;
    font-weight: 600;
    border: none;
    border-radius: 4px;
    background: transparent;
    color: var(--text-primary);
    cursor: pointer;
    transition: background 0.15s;
    line-height: 1;
}}
.zoom-btn:hover {{ background: var(--hover-bg); }}
.zoom-label {{
    font-size: 0.75rem;
    min-width: 3rem;
    text-align: center;
    color: var(--text-secondary);
    font-variant-numeric: tabular-nums;
}}
.image-container {{
    border: 1px solid var(--border-color);
    border-radius: 8px;
    overflow: hidden;
    display: flex;
    justify-content: center;
    align-items: center;
    background-image: linear-gradient(45deg, var(--checker-a) 25%, transparent 25%),
                      linear-gradient(-45deg, var(--checker-a) 25%, transparent 25%),
                      linear-gradient(45deg, transparent 75%, var(--checker-a) 75%),
                      linear-gradient(-45deg, transparent 75%, var(--checker-a) 75%);
    background-size: 20px 20px;
    background-position: 0 0, 0 10px, 10px -10px, -10px 0px;
    background-color: var(--checker-b);
    min-height: 200px;
    height: 80vh;
    cursor: grab;
    position: relative;
}}
.image-container.dragging {{ cursor: grabbing; }}
.image-container img {{
    max-width: 100%;
    max-height: 100%;
    object-fit: contain;
    display: block;
    transform-origin: center center;
    transition: transform 0.05s ease-out;
    pointer-events: none;
    user-select: none;
    -webkit-user-drag: none;
}}
@media (max-width: 768px) {{
    html {{ font-size: 16px; }}
    .toolbar {{ flex-direction: column; align-items: flex-start; }}
}}
</style>
</head>
<body>
<div class="container">
    <div class="toolbar">
        <div class="file-info">
            <h1>🖼️ {html.escape(filename)}</h1>
            <div class="file-meta">
                <span>📏 {file_size}</span>
                <span>🎨 {ext.lstrip(".").upper()}</span>
            </div>
        </div>
        <div class="toolbar-actions">
            <div class="zoom-controls">
                <button class="zoom-btn" onclick="zoomBy(1/1.25)" title="Zoom out">−</button>
                <span class="zoom-label" id="zoomLabel">100%</span>
                <button class="zoom-btn" onclick="zoomBy(1.25)" title="Zoom in">+</button>
                <button class="zoom-btn" onclick="resetZoom()" title="Reset (double-click image)">⟲</button>
            </div>
            <a href="./" class="btn">← Back</a>
            <button class="btn" onclick="toggleTheme()"><span id="themeIcon">🌙</span></button>
            <a href="{img_url}" class="btn btn-primary" download>⬇️ Download</a>
        </div>
    </div>
    <div class="image-container" id="imgContainer">
        <img src="{img_url}" alt="{html.escape(filename)}" id="previewImg"
             onload="onImageLoad(this)">
    </div>
</div>
<script>
let scale = 1, tx = 0, ty = 0;
let dragging = false, lastX = 0, lastY = 0;
let pinchDist = 0;
const MIN_SCALE = 0.05, MAX_SCALE = 20;

const img = document.getElementById('previewImg');
const container = document.getElementById('imgContainer');
const zoomLabel = document.getElementById('zoomLabel');

function applyTransform(animate) {{
    img.style.transition = animate ? 'transform 0.2s ease-out' : 'none';
    img.style.transform = `translate(${{tx}}px, ${{ty}}px) scale(${{scale}})`;
    zoomLabel.textContent = Math.round(scale * 100) + '%';
}}

function zoomAt(cx, cy, factor) {{
    const newScale = Math.max(MIN_SCALE, Math.min(MAX_SCALE, scale * factor));
    const ratio = newScale / scale;
    tx = cx - ratio * (cx - tx);
    ty = cy - ratio * (cy - ty);
    scale = newScale;
    applyTransform(false);
}}

function zoomBy(factor) {{
    zoomAt(0, 0, factor);
    applyTransform(true);
}}

function resetZoom() {{
    scale = 1; tx = 0; ty = 0;
    applyTransform(true);
}}

container.addEventListener('wheel', (e) => {{
    e.preventDefault();
    const rect = container.getBoundingClientRect();
    const cx = e.clientX - rect.left - rect.width / 2;
    const cy = e.clientY - rect.top - rect.height / 2;
    zoomAt(cx, cy, e.deltaY < 0 ? 1.12 : 1 / 1.12);
}}, {{ passive: false }});

container.addEventListener('mousedown', (e) => {{
    dragging = true;
    lastX = e.clientX; lastY = e.clientY;
    container.classList.add('dragging');
}});

document.addEventListener('mousemove', (e) => {{
    if (!dragging) return;
    tx += e.clientX - lastX;
    ty += e.clientY - lastY;
    lastX = e.clientX; lastY = e.clientY;
    applyTransform(false);
}});

document.addEventListener('mouseup', () => {{
    dragging = false;
    container.classList.remove('dragging');
}});

container.addEventListener('dblclick', resetZoom);

container.addEventListener('touchstart', (e) => {{
    if (e.touches.length === 2) {{
        pinchDist = Math.hypot(
            e.touches[0].clientX - e.touches[1].clientX,
            e.touches[0].clientY - e.touches[1].clientY
        );
    }} else if (e.touches.length === 1) {{
        dragging = true;
        lastX = e.touches[0].clientX;
        lastY = e.touches[0].clientY;
    }}
}}, {{ passive: true }});

container.addEventListener('touchmove', (e) => {{
    e.preventDefault();
    if (e.touches.length === 2) {{
        const dist = Math.hypot(
            e.touches[0].clientX - e.touches[1].clientX,
            e.touches[0].clientY - e.touches[1].clientY
        );
        const rect = container.getBoundingClientRect();
        const cx = (e.touches[0].clientX + e.touches[1].clientX) / 2 - rect.left - rect.width / 2;
        const cy = (e.touches[0].clientY + e.touches[1].clientY) / 2 - rect.top - rect.height / 2;
        zoomAt(cx, cy, dist / pinchDist);
        pinchDist = dist;
    }} else if (e.touches.length === 1 && dragging) {{
        tx += e.touches[0].clientX - lastX;
        ty += e.touches[0].clientY - lastY;
        lastX = e.touches[0].clientX;
        lastY = e.touches[0].clientY;
        applyTransform(false);
    }}
}}, {{ passive: false }});

container.addEventListener('touchend', () => {{ dragging = false; }});

function onImageLoad(img) {{
    const meta = document.querySelector('.file-meta');
    const span = document.createElement('span');
    span.textContent = '📐 ' + img.naturalWidth + ' × ' + img.naturalHeight;
    meta.appendChild(span);
}}

function initTheme() {{
    const saved = localStorage.getItem('hftp-theme') || 'light';
    applyTheme(saved);
}}

function toggleTheme() {{
    const current = document.documentElement.getAttribute('data-theme') || 'light';
    const next = current === 'dark' ? 'light' : 'dark';
    applyTheme(next);
    localStorage.setItem('hftp-theme', next);
}}

function applyTheme(theme) {{
    document.documentElement.setAttribute('data-theme', theme);
    document.getElementById('themeIcon').textContent = theme === 'dark' ? '☀️' : '🌙';
}}

initTheme();
setupSorting();
</script>
</body>
</html>'''

        encoded = html_content.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def serve_video_preview(self, filepath: str) -> None:
        """Serve a browser-native video player preview page."""
        filename = os.path.basename(filepath)
        file_size = self._format_size(os.path.getsize(filepath))
        ext = os.path.splitext(filename)[1].lower()
        mime_type = VIDEO_MIME_TYPES.get(ext, "video/mp4")
        video_url = quote(filename)

        html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(filename)} - Preview</title>
<script>(function(){{const t=localStorage.getItem('hftp-theme')||'light';document.documentElement.setAttribute('data-theme',t);}})();</script>
<style>
:root {{
    --bg-primary: #ffffff;
    --bg-secondary: #f6f8fa;
    --bg-tertiary: #eaeef2;
    --border-color: #d0d7de;
    --text-primary: #1f2328;
    --text-secondary: #656d76;
    --accent-green: #1a7f37;
    --hover-bg: rgba(208, 215, 222, 0.32);
}}
[data-theme="dark"] {{
    --bg-primary: #0d1117;
    --bg-secondary: #161b22;
    --bg-tertiary: #21262d;
    --border-color: #30363d;
    --text-primary: #c9d1d9;
    --text-secondary: #8b949e;
    --accent-green: #3fb950;
    --hover-bg: rgba(48, 54, 61, 0.5);
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
html {{ font-size: 18px; }}
body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
    background: var(--bg-primary);
    color: var(--text-primary);
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    transition: background 0.3s, color 0.3s;
}}
.container {{
    max-width: 1400px;
    margin: 0 auto;
    padding: 1.5rem;
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 1rem;
}}
.toolbar {{
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 0.75rem 1rem;
    display: flex;
    justify-content: space-between;
    align-items: center;
    flex-wrap: wrap;
    gap: 0.75rem;
}}
.file-info {{ display: flex; align-items: center; gap: 1rem; flex-wrap: wrap; }}
.file-info h1 {{ font-size: 1rem; font-weight: 600; }}
.file-meta {{
    display: flex;
    gap: 1rem;
    font-size: 0.8rem;
    color: var(--text-secondary);
}}
.toolbar-actions {{ display: flex; gap: 0.5rem; }}
.btn {{
    padding: 0.4rem 0.75rem;
    font-size: 0.8rem;
    font-weight: 500;
    border: 1px solid var(--border-color);
    border-radius: 6px;
    background: var(--bg-tertiary);
    color: var(--text-primary);
    cursor: pointer;
    text-decoration: none;
    display: inline-flex;
    align-items: center;
    gap: 0.25rem;
    transition: all 0.15s;
}}
.btn:hover {{ background: var(--hover-bg); }}
.btn-primary {{
    background: var(--accent-green);
    border-color: var(--accent-green);
    color: #fff;
}}
.btn-primary:hover {{ opacity: 0.9; }}
.video-container {{
    border: 1px solid var(--border-color);
    border-radius: 8px;
    overflow: hidden;
    background: #000;
    display: flex;
    justify-content: center;
    align-items: center;
}}
video {{
    width: 100%;
    max-height: 80vh;
    display: block;
    outline: none;
}}
@media (max-width: 768px) {{
    html {{ font-size: 16px; }}
    .toolbar {{ flex-direction: column; align-items: flex-start; }}
}}
</style>
</head>
<body>
<div class="container">
    <div class="toolbar">
        <div class="file-info">
            <h1>🎬 {html.escape(filename)}</h1>
            <div class="file-meta">
                <span>📏 {file_size}</span>
                <span>🎞️ {ext.lstrip(".").upper()}</span>
                <span id="durInfo"></span>
            </div>
        </div>
        <div class="toolbar-actions">
            <a href="./" class="btn">← Back</a>
            <button class="btn" onclick="toggleTheme()"><span id="themeIcon">🌙</span></button>
            <a href="{video_url}" class="btn btn-primary" download>⬇️ Download</a>
        </div>
    </div>
    <div class="video-container">
        <video controls preload="metadata" id="videoPlayer">
            <source src="{video_url}" type="{mime_type}">
        </video>
    </div>
</div>
<script>
function initTheme() {{
    const saved = localStorage.getItem('hftp-theme') || 'light';
    applyTheme(saved);
}}

function toggleTheme() {{
    const current = document.documentElement.getAttribute('data-theme') || 'light';
    const next = current === 'dark' ? 'light' : 'dark';
    applyTheme(next);
    localStorage.setItem('hftp-theme', next);
}}

function applyTheme(theme) {{
    document.documentElement.setAttribute('data-theme', theme);
    document.getElementById('themeIcon').textContent = theme === 'dark' ? '☀️' : '🌙';
}}

document.getElementById('videoPlayer').addEventListener('loadedmetadata', function() {{
    const dur = this.duration;
    if (isFinite(dur)) {{
        const h = Math.floor(dur / 3600);
        const m = Math.floor((dur % 3600) / 60);
        const s = Math.floor(dur % 60);
        const parts = h > 0 ? [h, m, s] : [m, s];
        const fmt = parts.map((v, i) => (i > 0 ? String(v).padStart(2, '0') : v)).join(':');
        document.getElementById('durInfo').textContent = '⏱ ' + fmt;
    }}
    const w = this.videoWidth, h = this.videoHeight;
    if (w && h) {{
        document.querySelector('.file-meta').innerHTML +=
            '<span>📐 ' + w + ' × ' + h + '</span>';
    }}
}});

initTheme();
</script>
</body>
</html>'''

        encoded = html_content.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        self.wfile.write(encoded)

    def do_PUT(self) -> None:
        """Handle PUT requests for file uploads"""
        path = self.translate_path(self.path)
        if path.endswith("/"):
            access_log(self, "upload", "400")
            self.send_error(400, "Cannot PUT to directory")
            return

        existed = os.path.exists(path)
        action = "modify" if existed else "upload"
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            length = int(self.headers["Content-Length"])
            with open(path, "wb") as f:
                f.write(self.rfile.read(length))

            NEW_FILE_TRACKER.register(path)
            self.send_response(201)
            self.end_headers()
            access_log(self, action, "201", path)
            debug("File uploaded via PUT", path=path)
        except Exception as e:
            access_log(self, action, "500", path)
            debug("PUT error", error=str(e))
            self.send_error(500, str(e))

    def translate_path(self, path: str) -> str:
        """Convert URL path to filesystem path, constrained to server root."""
        path = unquote(path)
        path = path.lstrip("/")
        root = self.server.root_dir
        joined = os.path.join(root, path)
        resolved = os.path.realpath(joined)

        if resolved == root:
            return resolved

        try:
            common = os.path.commonpath([resolved, root])
        except ValueError:
            common = None

        if common == root:
            return resolved

        current = joined
        while True:
            if os.path.islink(current):
                return resolved
            parent = os.path.dirname(current)
            if parent == current or not parent.startswith(root):
                break
            current = parent

        return root

    def _translate_path_for_read(self, url_path: str) -> str:
        """
        Convert URL path to filesystem path for read-only operations.

        This translation blocks '..' traversal but intentionally does not resolve symlinks.
        It enables serving symlink entries that point outside the server root while keeping
        URL-path traversal constrained to the root.
        """
        path = unquote(url_path)
        path = path.split("?", 1)[0].split("#", 1)[0]
        path = path.lstrip("/")
        root = self.server.root_dir

        normalized = os.path.normpath(path)
        if normalized in (".", ""):
            return root
        if normalized.startswith("..") or os.path.isabs(normalized):
            return root
        return os.path.join(root, normalized)

    def _fs_path_to_url_path(self, fs_path: str, trailing_slash: bool = False) -> str:
        """Convert filesystem path under root to URL path (avoids symlink duplication)."""
        root = self.server.root_dir
        try:
            rel = os.path.relpath(fs_path, root)
        except ValueError:
            return "/"
        if rel == "." or rel.startswith(".."):
            return "/"
        parts = rel.replace(os.sep, "/").split("/")
        parts = [p for p in parts if p]
        url = "/" + "/".join(quote(p) for p in parts)
        if trailing_slash and os.path.isdir(fs_path):
            url += "/"
        return url

    def log_message(self, format, *args):
        """Override to reduce console noise"""
        if DEBUG_MODE:
            super().log_message(format, *args)

    def list_directory(self, path: str) -> Optional[io.BytesIO]:
        """Generate directory listing HTML page"""
        try:
            file_list = os.listdir(path)
        except OSError:
            self.send_error(404, "No permission to list directory")
            return None

        entries: list[tuple[str, bool]] = []
        for name in file_list:
            fullname = os.path.join(path, name)
            is_dir = os.path.isdir(fullname)
            entries.append((name, is_dir))

        entries.sort(key=lambda item: item[0].lower())

        displaypath = unquote(self.path)
        enc = sys.getfilesystemencoding()
        title = f"Directory: {displaypath}"

        html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="{enc}">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<script>(function(){{const t=localStorage.getItem('hftp-theme')||'light';document.documentElement.setAttribute('data-theme',t);}})();</script>
<style>
:root {{
    --bg-primary: #ffffff;
    --bg-secondary: #f6f8fa;
    --bg-tertiary: #eaeef2;
    --border-color: #d0d7de;
    --text-primary: #1f2328;
    --text-secondary: #656d76;
    --accent-blue: #0969da;
    --accent-green: #1a7f37;
    --accent-yellow: #9a6700;
    --accent-purple: #8250df;
    --accent-red: #cf222e;
    --hover-bg: rgba(208, 215, 222, 0.32);
}}
[data-theme="dark"] {{
    --bg-primary: #0d1117;
    --bg-secondary: #161b22;
    --bg-tertiary: #21262d;
    --border-color: #30363d;
    --text-primary: #c9d1d9;
    --text-secondary: #8b949e;
    --accent-blue: #58a6ff;
    --accent-green: #3fb950;
    --accent-yellow: #d29922;
    --accent-purple: #a371f7;
    --accent-red: #f85149;
    --hover-bg: rgba(48, 54, 61, 0.5);
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
html {{ font-size: 18px; }}
body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Noto Sans', Helvetica, Arial, sans-serif;
    background: var(--bg-primary);
    color: var(--text-primary);
    line-height: 1.6;
    min-height: 100vh;
    transition: background 0.3s, color 0.3s;
}}
.container {{
    max-width: 1400px;
    margin: 0 auto;
    padding: 1.5rem;
}}
header {{
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 1rem 1.25rem;
    margin-bottom: 1rem;
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    flex-wrap: wrap;
    gap: 1rem;
}}
.header-left {{
    flex: 1;
}}
header h1 {{
    font-size: 1.25rem;
    font-weight: 600;
    color: var(--text-primary);
    display: flex;
    align-items: center;
    gap: 0.5rem;
}}
.breadcrumb {{
    margin-top: 0.5rem;
    font-size: 0.875rem;
    color: var(--text-secondary);
}}
.breadcrumb a {{
    color: var(--accent-blue);
    text-decoration: none;
}}
.breadcrumb a:hover {{ text-decoration: underline; }}

/* Theme Toggle */
.theme-toggle {{
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem 0.75rem;
    background: var(--bg-tertiary);
    border: 1px solid var(--border-color);
    border-radius: 6px;
    cursor: pointer;
    font-size: 0.875rem;
    color: var(--text-primary);
    transition: all 0.2s;
}}
.theme-toggle:hover {{ background: var(--hover-bg); }}
.theme-toggle .icon {{ font-size: 1rem; }}

/* Upload Section */
.upload-section {{
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 1.25rem;
    margin-bottom: 1rem;
}}
.upload-title {{
    font-size: 0.9rem;
    font-weight: 600;
    margin-bottom: 0.75rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}}
.upload-title .icon {{ color: var(--accent-green); }}
.upload-zone {{
    border: 2px dashed var(--border-color);
    border-radius: 8px;
    padding: 2rem;
    text-align: center;
    transition: all 0.2s;
    cursor: pointer;
}}
.upload-zone:hover, .upload-zone.dragover {{
    border-color: var(--accent-blue);
    background: var(--hover-bg);
}}
.upload-zone input[type="file"] {{ display: none; }}
.upload-zone p {{
    color: var(--text-secondary);
    font-size: 0.9rem;
    margin-bottom: 0.75rem;
}}
.upload-zone .btn {{
    display: inline-block;
    padding: 0.5rem 1rem;
    background: var(--accent-green);
    color: #fff;
    border: none;
    border-radius: 6px;
    font-size: 0.9rem;
    font-weight: 500;
    cursor: pointer;
    transition: opacity 0.2s;
}}
.upload-zone .btn:hover {{ opacity: 0.9; }}

/* Progress Bar */
.progress-container {{
    display: none;
    margin-top: 1rem;
}}
.progress-container.active {{ display: block; }}
.progress-info {{
    display: flex;
    justify-content: space-between;
    font-size: 0.8rem;
    color: var(--text-secondary);
    margin-bottom: 0.5rem;
}}
.progress-bar {{
    height: 0.5rem;
    background: var(--bg-tertiary);
    border-radius: 4px;
    overflow: hidden;
}}
.progress-fill {{
    height: 100%;
    background: linear-gradient(90deg, var(--accent-blue), var(--accent-green));
    width: 0%;
    transition: width 0.3s;
    border-radius: 4px;
}}
.progress-stats {{
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 0.75rem;
    margin-top: 0.75rem;
}}
.stat-item {{
    background: var(--bg-tertiary);
    padding: 0.75rem;
    border-radius: 6px;
    text-align: center;
}}
.stat-label {{
    font-size: 0.7rem;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}
.stat-value {{
    font-size: 1rem;
    font-weight: 600;
    margin-top: 0.25rem;
    color: var(--accent-blue);
}}

/* File List */
.file-list {{
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    overflow: hidden;
}}
.file-list-header {{
    display: grid;
    grid-template-columns: 1fr 6rem 11rem 12rem;
    padding: 0.75rem 1rem;
    background: var(--bg-tertiary);
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    border-bottom: 1px solid var(--border-color);
}}
.file-list-header-cell {{
    display: inline-flex;
    align-items: center;
    gap: 0.3rem;
    background: transparent;
    border: none;
    padding: 0;
    margin: 0;
    font: inherit;
    color: inherit;
    cursor: pointer;
    text-align: left;
}}
.file-list-header-cell .sort-indicator {{
    font-size: 0.7rem;
}}
.file-list-header-cell.active {{
    color: var(--accent-blue);
}}
.file-list-header {{
    display: grid;
    grid-template-columns: 1fr 6rem 11rem 12rem;
    padding: 0.75rem 1rem;
    background: var(--bg-tertiary);
    font-size: 0.75rem;
    font-weight: 600;
    color: var(--text-secondary);
    text-transform: uppercase;
    letter-spacing: 0.5px;
    border-bottom: 1px solid var(--border-color);
}}
.file-item {{
    display: grid;
    grid-template-columns: 1fr 6rem 11rem 12rem;
    padding: 0.75rem 1rem;
    border-bottom: 1px solid var(--border-color);
    transition: background 0.15s;
}}
.file-item:last-child {{ border-bottom: none; }}
.file-item:hover {{ background: var(--hover-bg); }}
.file-name {{
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
}}
.file-name a:not(.preview-badge) {{
    color: var(--accent-blue);
    text-decoration: none;
    font-weight: 500;
    font-size: 0.95rem;
}}
.file-name a:not(.preview-badge):hover {{ text-decoration: underline; }}
.file-size, .file-date {{
    color: var(--text-secondary);
    font-size: 0.85rem;
    display: flex;
    align-items: center;
}}
.preview-badge {{
    font-size: 0.6rem;
    font-weight: 600;
    letter-spacing: 0.03em;
    color: var(--accent-green);
    border: 1px solid var(--accent-green);
    padding: 0.1rem 0.35rem;
    border-radius: 3px;
    margin-left: 0.4rem;
    text-decoration: none;
    vertical-align: middle;
    display: inline-block;
    line-height: 1;
    opacity: 0.85;
    transition: all 0.15s;
}}
.preview-badge:hover {{
    background: var(--accent-green);
    color: #fff;
    opacity: 1;
}}
.new-badge {{
    font-size: 0.6rem;
    font-weight: 600;
    letter-spacing: 0.03em;
    color: var(--accent-red);
    border: 1px solid var(--accent-red);
    padding: 0.1rem 0.35rem;
    border-radius: 3px;
    margin-left: 0.4rem;
    vertical-align: middle;
    display: inline-block;
    line-height: 1;
    opacity: 0.85;
    pointer-events: none;
}}
.folder-badge {{
    font-size: 0.6rem;
    font-weight: 600;
    letter-spacing: 0.03em;
    color: var(--accent-yellow);
    border: 1px solid var(--accent-yellow);
    padding: 0.1rem 0.35rem;
    border-radius: 3px;
    margin-left: 0.4rem;
    vertical-align: middle;
    display: inline-block;
    line-height: 1;
    opacity: 0.85;
    pointer-events: none;
}}
.file-actions {{
    display: flex;
    align-items: center;
    gap: 0.4rem;
    padding-right: 0.5rem;
}}
.action-btn {{
    padding: 0.25rem 0.5rem;
    font-size: 0.75rem;
    border: 1px solid var(--border-color);
    border-radius: 4px;
    background: var(--bg-tertiary);
    color: var(--text-primary);
    cursor: pointer;
    text-decoration: none;
    transition: all 0.15s;
    display: inline-flex;
    align-items: center;
    gap: 0.2rem;
}}
.action-btn:hover {{
    background: var(--hover-bg);
    border-color: var(--accent-blue);
}}
.action-btn.delete {{
    color: var(--accent-red);
}}
.action-btn.delete:hover {{
    background: var(--accent-red);
    color: #fff;
    border-color: var(--accent-red);
}}

/* Modal */
.modal-overlay {{
    display: none;
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: rgba(0,0,0,0.5);
    z-index: 1000;
    justify-content: center;
    align-items: center;
}}
.modal-overlay.show {{ display: flex; }}
.modal {{
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 1.5rem;
    max-width: 400px;
    width: 90%;
}}
.modal h3 {{
    margin-bottom: 1rem;
    color: var(--accent-red);
}}
.modal p {{
    margin-bottom: 1rem;
    color: var(--text-secondary);
    word-break: break-all;
}}
.modal-actions {{
    display: flex;
    gap: 0.5rem;
    justify-content: flex-end;
}}
.modal-btn {{
    padding: 0.5rem 1rem;
    border-radius: 6px;
    border: 1px solid var(--border-color);
    cursor: pointer;
    font-size: 0.85rem;
    font-weight: 500;
}}
.modal-btn.cancel {{
    background: var(--bg-tertiary);
    color: var(--text-primary);
}}
.modal-btn.confirm {{
    background: var(--accent-red);
    color: #fff;
    border-color: var(--accent-red);
}}
.modal-btn:hover {{ opacity: 0.9; }}

/* Empty State */
.empty-state {{
    padding: 3rem;
    text-align: center;
    color: var(--text-secondary);
}}

/* Footer */
footer {{
    margin-top: 1.5rem;
    padding: 1rem;
    text-align: center;
    font-size: 0.75rem;
    color: var(--text-secondary);
}}

/* Responsive */
@media (max-width: 768px) {{
    html {{ font-size: 16px; }}
    .file-item {{
        grid-template-columns: 1fr;
        gap: 0.25rem;
    }}
    .file-size, .file-date {{
        font-size: 0.8rem;
        padding-left: 1.85rem;
    }}
    .file-actions {{
        padding-left: 1.85rem;
        margin-top: 0.25rem;
    }}
    .progress-stats {{
        grid-template-columns: repeat(2, 1fr);
    }}
}}
</style>
</head>
<body>
<div class="container">
    <header>
        <div class="header-left">
            <h1>File Server</h1>
            <div class="breadcrumb">{self._generate_breadcrumb(displaypath)}</div>
        </div>
        <button class="theme-toggle" onclick="toggleTheme()">
            <span id="themeText">Dark</span>
        </button>
    </header>

    <div class="upload-section">
        <div class="upload-title">Upload File</div>
        <div class="upload-zone" id="uploadZone">
            <input type="file" id="fileInput" name="file" multiple>
            <p>Drag & drop, click to browse, or press Ctrl+V to paste from clipboard</p>
            <button type="button" class="btn" onclick="document.getElementById('fileInput').click()">Select File(s)</button>
        </div>
        <div style="display:flex;flex-direction:column;gap:6px;margin-top:4px;">
            <div style="display:flex;align-items:center;background:var(--bg-secondary);border:1px solid var(--border-color);border-radius:6px;overflow:hidden;">
                <code id="cmdCurlPut" style="flex:1;padding:6px 10px;font-family:'SF Mono','Fira Code',Consolas,monospace;font-size:0.8em;white-space:nowrap;overflow-x:auto;background:transparent;"></code>
                <button onclick="copyCmd(this, window.__hftpCmds.curlPut)" style="flex-shrink:0;padding:4px 8px;background:transparent;border:none;border-left:1px solid var(--border-color);cursor:pointer;color:var(--text-muted);font-size:0.75em;" title="Copy">⎘</button>
            </div>
            <div style="display:flex;align-items:center;background:var(--bg-secondary);border:1px solid var(--border-color);border-radius:6px;overflow:hidden;">
                <code id="cmdCurlPutBinary" style="flex:1;padding:6px 10px;font-family:'SF Mono','Fira Code',Consolas,monospace;font-size:0.8em;white-space:nowrap;overflow-x:auto;background:transparent;"></code>
                <button onclick="copyCmd(this, window.__hftpCmds.curlPutBinary)" style="flex-shrink:0;padding:4px 8px;background:transparent;border:none;border-left:1px solid var(--border-color);cursor:pointer;color:var(--text-muted);font-size:0.75em;" title="Copy">⎘</button>
            </div>
            <div style="display:flex;align-items:center;background:var(--bg-secondary);border:1px solid var(--border-color);border-radius:6px;overflow:hidden;">
                <code id="cmdWgetPut" style="flex:1;padding:6px 10px;font-family:'SF Mono','Fira Code',Consolas,monospace;font-size:0.8em;white-space:nowrap;overflow-x:auto;background:transparent;"></code>
                <button onclick="copyCmd(this, window.__hftpCmds.wgetPut)" style="flex-shrink:0;padding:4px 8px;background:transparent;border:none;border-left:1px solid var(--border-color);cursor:pointer;color:var(--text-muted);font-size:0.75em;" title="Copy">⎘</button>
            </div>
        </div>
        <div class="progress-container" id="progressContainer">
            <div class="progress-info">
                <span id="fileName">-</span>
                <span id="progressPercent">0%</span>
            </div>
            <div class="progress-bar">
                <div class="progress-fill" id="progressFill"></div>
            </div>
            <div class="progress-stats">
                <div class="stat-item">
                    <div class="stat-label">Total Size</div>
                    <div class="stat-value" id="totalSize">-</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Uploaded</div>
                    <div class="stat-value" id="uploadedSize">-</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Speed</div>
                    <div class="stat-value" id="uploadSpeed">-</div>
                </div>
                <div class="stat-item">
                    <div class="stat-label">Remaining</div>
                    <div class="stat-value" id="timeRemaining">-</div>
                </div>
            </div>
        </div>
    </div>

        <div class="file-list">
        <div class="file-list-header">
            <button type="button" class="file-list-header-cell sortable" data-sort-key="name">
                <span>Name</span><span class="sort-indicator" data-key="name"></span>
            </button>
            <button type="button" class="file-list-header-cell sortable" data-sort-key="size">
                <span>Size</span><span class="sort-indicator" data-key="size"></span>
            </button>
            <button type="button" class="file-list-header-cell sortable" data-sort-key="mtime">
                <span>Modified</span><span class="sort-indicator" data-key="mtime"></span>
            </button>
            <span>Actions</span>
        </div>
        <div id="fileListBody">
'''

        root = self.server.root_dir
        if os.path.normpath(path.rstrip(os.sep)) != os.path.normpath(
            root.rstrip(os.sep)
        ):
            try:
                parent_fs = os.path.dirname(path)
                parent_rel = os.path.relpath(parent_fs, root)
                if parent_rel.startswith("..") or parent_rel == "..":
                    parent_url = "/"
                else:
                    parent_url = self._fs_path_to_url_path(
                        parent_fs, trailing_slash=True
                    )
            except ValueError:
                parent_url = "/"
            html_content += f"""
        <div class="file-item" data-name=".." data-size="0" data-mtime="0" data-type="dir" data-up="1">
            <div class="file-name">
                <a href="{parent_url}">..</a>
                <span class="folder-badge">DIR</span>
            </div>
            <div class="file-size">-</div>
            <div class="file-date">-</div>
            <div class="file-actions"></div>
        </div>
"""

        has_entries = False
        for name, is_dir in entries:
            fullname = os.path.join(path, name)
            try:
                mtime_ts = os.path.getmtime(fullname)
                mtime = time.strftime("%Y-%m-%d %H:%M", time.localtime(mtime_ts))
            except OSError:
                mtime_ts = 0.0
                mtime = "-"

            if is_dir:
                dir_url = self._fs_path_to_url_path(fullname, trailing_slash=True)
                escaped_name = html.escape(name).replace("'", "\\'")
                dir_url_attr = dir_url.replace("\\", "\\\\").replace("'", "\\'")
                html_content += f'''
        <div class="file-item" data-name="{html.escape(name)}" data-size="0" data-mtime="{mtime_ts}" data-type="dir">
            <div class="file-name">
                <a href="{dir_url}">{html.escape(name)}</a>
                <span class="folder-badge">DIR</span>
            </div>
            <div class="file-size">-</div>
            <div class="file-date">{mtime}</div>
            <div class="file-actions">
                <button class="action-btn delete" onclick="confirmDelete('{dir_url_attr}', true, '{escaped_name}/')">Delete</button>
            </div>
        </div>
'''
            else:
                try:
                    size = os.path.getsize(fullname)
                    size_str = self._format_size(size)
                except OSError:
                    size = 0
                    size_str = "-"

                icon, icon_class = self._get_file_icon(name)
                is_previewable = (
                    is_text_file(fullname)
                    or is_image_file(fullname)
                    or is_video_file(fullname)
                )
                file_url = self._fs_path_to_url_path(fullname, trailing_slash=False)
                preview_badge = (
                    f'<a class="preview-badge" href="{file_url}?preview=1">VIEW</a>'
                    if is_previewable
                    else ""
                )
                new_badge = (
                    '<span class="new-badge">NEW</span>'
                    if NEW_FILE_TRACKER.is_new(fullname)
                    else ""
                )
                escaped_name = html.escape(name).replace("'", "\\'")
                file_url_attr = file_url.replace("\\", "\\\\").replace("'", "\\'")

                html_content += f'''
        <div class="file-item" data-name="{html.escape(name)}" data-size="{size}" data-mtime="{mtime_ts}" data-type="file">
            <div class="file-name">
                <a href="{file_url}" target="_blank" rel="noopener noreferrer">{html.escape(name)}</a>{preview_badge}{new_badge}
            </div>
            <div class="file-size">{size_str}</div>
            <div class="file-date">{mtime}</div>
            <div class="file-actions">
                <a href="{file_url}" class="action-btn" download>Download</a>
                <button class="action-btn delete" onclick="confirmDelete('{file_url_attr}', false, '{escaped_name}')">Delete</button>
            </div>
        </div>
'''

            has_entries = True

        if not has_entries:
            html_content += """
        <div class="empty-state">
            <p>📭 This directory is empty</p>
        </div>
"""

        html_content += """
    </div>
    <footer>FAST FILE TRANSFER SERVER by HTTP</footer>
</div>

<div class="modal-overlay" id="deleteModal">
    <div class="modal">
        <h3>⚠️ Confirm Delete</h3>
        <p>Are you sure you want to delete <strong id="deleteFileName"></strong>?</p>
        <p style="font-size: 0.8rem; color: var(--accent-red);" id="deleteDirWarning"></p>
        <div class="modal-actions">
            <button class="modal-btn cancel" onclick="closeDeleteModal()">Cancel</button>
            <button class="modal-btn confirm" onclick="executeDelete()">Delete</button>
        </div>
    </div>
</div>

<script>
var uploadZone = document.getElementById('uploadZone');
var fileInput = document.getElementById('fileInput');
var progressContainer = document.getElementById('progressContainer');

function formatBytes(bytes) {
    if (bytes === 0) return '0 B';
    var k = 1024;
    var sizes = ['B', 'KB', 'MB', 'GB'];
    var i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function formatTime(seconds) {
    if (!isFinite(seconds) || seconds < 0) return '-';
    if (seconds < 60) return Math.round(seconds) + 's';
    if (seconds < 3600) return Math.round(seconds / 60) + 'm ' + Math.round(seconds % 60) + 's';
    return Math.floor(seconds / 3600) + 'h ' + Math.round((seconds % 3600) / 60) + 'm';
}

var currentSortKey = 'name';
var currentSortDir = 'asc';

function applySort() {
    var container = document.getElementById('fileListBody');
    if (!container) return;
    var nodeList = container.getElementsByClassName('file-item');
    if (!nodeList || nodeList.length === 0) return;

    var upItem = null;
    var items = [];
    for (var idx = 0; idx < nodeList.length; idx += 1) {
        var el = nodeList[idx];
        if (el.getAttribute('data-up') === '1') {
            upItem = el;
        } else {
            items.push(el);
        }
    }

    items.sort(function(a, b) {
        var typeA = a.getAttribute('data-type') || 'file';
        var typeB = b.getAttribute('data-type') || 'file';

        if (typeA !== typeB) {
            return typeA === 'dir' ? -1 : 1;
        }

        if (currentSortKey === 'name') {
            var nameA = (a.getAttribute('data-name') || '').toLowerCase();
            var nameB = (b.getAttribute('data-name') || '').toLowerCase();
            if (nameA < nameB) return currentSortDir === 'asc' ? -1 : 1;
            if (nameA > nameB) return currentSortDir === 'asc' ? 1 : -1;
            return 0;
        }

        if (currentSortKey === 'size') {
            var sizeA = parseFloat(a.getAttribute('data-size') || '0');
            var sizeB = parseFloat(b.getAttribute('data-size') || '0');
            if (sizeA === sizeB) return 0;
            return currentSortDir === 'asc' ? sizeA - sizeB : sizeB - sizeA;
        }

        if (currentSortKey === 'mtime') {
            var mA = parseFloat(a.getAttribute('data-mtime') || '0');
            var mB = parseFloat(b.getAttribute('data-mtime') || '0');
            if (mA === mB) return 0;
            return currentSortDir === 'asc' ? mA - mB : mB - mA;
        }

        return 0;
    });

    container.innerHTML = '';
    if (upItem) {
        container.appendChild(upItem);
    }
    for (var i = 0; i < items.length; i += 1) {
        container.appendChild(items[i]);
    }

    var headers = document.getElementsByClassName('file-list-header-cell');
    for (var j = 0; j < headers.length; j += 1) {
        var btn = headers[j];
        var key = btn.getAttribute('data-sort-key');
        var indicator = btn.querySelector('.sort-indicator');
        if (key === currentSortKey) {
            btn.classList.add('active');
            if (indicator) {
                indicator.textContent = currentSortDir === 'asc' ? '▲' : '▼';
            }
        } else {
            btn.classList.remove('active');
            if (indicator) {
                indicator.textContent = '';
            }
        }
    }
}

function setupSorting() {
    var headers = document.getElementsByClassName('file-list-header-cell');
    for (var i = 0; i < headers.length; i += 1) {
        headers[i].addEventListener('click', function() {
            var key = this.getAttribute('data-sort-key');
            if (!key) return;
            if (currentSortKey === key) {
                currentSortDir = currentSortDir === 'asc' ? 'desc' : 'asc';
            } else {
                currentSortKey = key;
                currentSortDir = 'asc';
            }
            applySort();
        });
    }
    applySort();
}

function updateProgressForFile(file, index, total, percent, loaded, totalSize, speed, remaining) {
    progressContainer.classList.add('active');
    document.getElementById('fileName').textContent = total > 1
        ? (index + 1) + '/' + total + ' ' + file.name
        : file.name;
    document.getElementById('progressFill').style.width = percent + '%';
    document.getElementById('progressPercent').textContent = percent + '%';
    document.getElementById('uploadedSize').textContent = formatBytes(loaded);
    document.getElementById('totalSize').textContent = formatBytes(totalSize);
    document.getElementById('uploadSpeed').textContent = speed;
    document.getElementById('timeRemaining').textContent = remaining;
}

function uploadOneFile(file, index, total, basePath) {
    return new Promise(function(resolve, reject) {
        const xhr = new XMLHttpRequest();
        const formData = new FormData();
        formData.append('file', file);

        let lastLoaded = 0;
        let lastTime = Date.now();

        xhr.upload.addEventListener('progress', function(e) {
            if (e.lengthComputable) {
                const percent = Math.round((e.loaded / e.total) * 100);
                const now = Date.now();
                const timeDiff = (now - lastTime) / 1000;
                let speed = '-';
                let remaining = '-';
                if (timeDiff >= 0.25) {
                    const byteDiff = e.loaded - lastLoaded;
                    speed = formatBytes(byteDiff / timeDiff) + '/s';
                    const left = e.total - e.loaded;
                    remaining = formatTime(byteDiff > 0 ? left / (byteDiff / timeDiff) : 0);
                    lastLoaded = e.loaded;
                    lastTime = now;
                }
                updateProgressForFile(file, index, total, percent, e.loaded, e.total, speed, remaining);
            }
        });

        xhr.addEventListener('load', function() {
            if (xhr.status === 200) {
                resolve();
            } else {
                reject(new Error(file.name + ': ' + xhr.statusText));
            }
        });

        xhr.addEventListener('error', function() {
            reject(new Error(file.name + ': network error'));
        });

        xhr.open('POST', basePath, true);
        xhr.send(formData);
    });
}

function uploadFiles(files) {
    if (!files || files.length === 0) return;
    const basePath = (window.location.pathname || '/').replace(/\\/$/, '') + '/';
    const total = files.length;
    let done = 0;

    function next() {
        if (done >= total) {
            document.getElementById('progressPercent').textContent = 'Complete!';
            document.getElementById('uploadSpeed').textContent = '-';
            document.getElementById('timeRemaining').textContent = '0s';
            setTimeout(function() { location.reload(); }, 800);
            return;
        }
        const file = files[done];
        updateProgressForFile(file, done, total, 0, 0, file.size, '-', '-');
        uploadOneFile(file, done, total, basePath)
            .then(function() {
                done++;
                next();
            })
            .catch(function(err) {
                alert('Upload failed: ' + err.message);
                done++;
                next();
            });
    }
    next();
}

uploadZone.addEventListener('dragover', function(e) {
    e.preventDefault();
    uploadZone.classList.add('dragover');
});

uploadZone.addEventListener('dragleave', function(e) {
    e.preventDefault();
    uploadZone.classList.remove('dragover');
});

uploadZone.addEventListener('drop', function(e) {
    e.preventDefault();
    uploadZone.classList.remove('dragover');
    const files = e.dataTransfer.files;
    if (files.length > 0) uploadFiles(Array.from(files));
});

document.addEventListener('paste', function(e) {
    if (!e.clipboardData || !e.clipboardData.items) {
        return;
    }
    var items = e.clipboardData.items;
    var files = [];
    var ts = Date.now();
    for (var i = 0; i < items.length; i += 1) {
        var item = items[i];
        if (item.kind === 'file') {
            var file = item.getAsFile();
            if (file) {
                var name = file.name || '';
                var dotIndex = name.lastIndexOf('.');
                var base = dotIndex > 0 ? name.slice(0, dotIndex) : name;
                var ext = dotIndex > 0 ? name.slice(dotIndex) : '';

                if (base === 'image' && (ext === '.png' || ext === '.jpg' || ext === '.jpeg')) {
                    var newName = base + '-' + ts + '-' + i + ext;
                    if (typeof File === 'function') {
                        files.push(new File([file], newName, { type: file.type }));
                    } else {
                        file.name = newName;
                        files.push(file);
                    }
                } else {
                    files.push(file);
                }
            }
        }
    }
    if (files.length > 0) {
        e.preventDefault();
        uploadFiles(files);
    }
});

fileInput.addEventListener('change', function(e) {
    const files = e.target.files;
    if (files && files.length > 0) uploadFiles(Array.from(files));
    e.target.value = '';
});

// Theme toggle
function initTheme() {
    const saved = localStorage.getItem('hftp-theme');
    const theme = saved || 'light';
    document.documentElement.setAttribute('data-theme', theme);
    updateThemeButton(theme);
}

function toggleTheme() {
    const current = document.documentElement.getAttribute('data-theme') || 'light';
    const next = current === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    localStorage.setItem('hftp-theme', next);
    updateThemeButton(next);
}

function updateThemeButton(theme) {
    document.getElementById('themeText').textContent = theme === 'dark' ? 'Light theme' : 'Dark theme';
}

initTheme();
setupSorting();

// Delete functionality
let deleteTarget = '';
let deleteIsDir = false;

function confirmDelete(deleteUrl, isDir, displayName) {
    deleteTarget = deleteUrl;
    deleteIsDir = isDir;
    document.getElementById('deleteFileName').textContent = displayName || deleteUrl;
    document.getElementById('deleteDirWarning').textContent = isDir 
        ? 'This will delete the folder and all its contents!' 
        : '';
    document.getElementById('deleteModal').classList.add('show');
}

function closeDeleteModal() {
    document.getElementById('deleteModal').classList.remove('show');
    deleteTarget = '';
    deleteIsDir = false;
}

function executeDelete() {
    if (!deleteTarget) return;
    
    const xhr = new XMLHttpRequest();
    xhr.open('DELETE', deleteTarget, true);
    
    xhr.onload = function() {
        if (xhr.status === 200 || xhr.status === 204) {
            location.reload();
        } else {
            alert('Delete failed: ' + xhr.statusText);
            closeDeleteModal();
        }
    };
    
    xhr.onerror = function() {
        alert('Delete error occurred');
        closeDeleteModal();
    };
    
    xhr.send();
}

document.getElementById('deleteModal').addEventListener('click', function(e) {
    if (e.target === this) closeDeleteModal();
});

function initUploadCliExamples() {
    const base = window.location.origin.replace(/\\/+$/, '');
    const path = (window.location.pathname || '/').replace(/\\/+$/, '') + '/file.txt';
    const target = base + path;

    window.__hftpCmds = {
        curlPut: `curl -T file.txt ${target}`,
        curlPutBinary: `curl -X PUT --data-binary @file.txt ${target}`,
        wgetPut: `wget --method=PUT --body-file=file.txt ${target}`
    };

    const el1 = document.getElementById('cmdCurlPut');
    const el2 = document.getElementById('cmdCurlPutBinary');
    const el3 = document.getElementById('cmdWgetPut');
    if (el1) el1.textContent = window.__hftpCmds.curlPut;
    if (el2) el2.textContent = window.__hftpCmds.curlPutBinary;
    if (el3) el3.textContent = window.__hftpCmds.wgetPut;
}

function copyCmd(btn, text) {
    const finish = () => {
        const orig = btn.textContent;
        btn.textContent = '✓';
        btn.style.color = 'var(--accent-green)';
        setTimeout(() => { btn.textContent = orig; btn.style.color = ''; }, 1500);
    };
    if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(text).then(finish).catch(() => fallbackCopy(text, finish));
    } else {
        fallbackCopy(text, finish);
    }
}

function fallbackCopy(text, cb) {
    const ta = document.createElement('textarea');
    ta.value = text;
    ta.style.cssText = 'position:fixed;opacity:0';
    document.body.appendChild(ta);
    ta.select();
    document.execCommand('copy');
    document.body.removeChild(ta);
    cb();
}

// Initialize dynamic upload CLI examples on load
initUploadCliExamples();
</script>
</body>
</html>"""

        encoded = html_content.encode(enc, "surrogateescape")

        f = io.BytesIO()
        f.write(encoded)
        f.seek(0)

        self.send_response(200)
        self.send_header("Content-type", f"text/html; charset={enc}")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        return f

    def _generate_breadcrumb(self, path: str) -> str:
        """Generate breadcrumb navigation HTML"""
        if path == "/":
            return '<a href="/">Home</a>'

        parts = path.strip("/").split("/")
        breadcrumb = '<a href="/">Home</a>'
        current_path = ""
        for part in parts:
            if part:
                current_path += "/" + part
                breadcrumb += f' / <a href="{current_path}/">{html.escape(part)}</a>'
        return breadcrumb

    def _format_size(self, size: int) -> str:
        """Format file size to human readable string"""
        if size < 1024:
            return f"{size} B"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} KB"
        elif size < 1024 * 1024 * 1024:
            return f"{size / (1024 * 1024):.1f} MB"
        else:
            return f"{size / (1024 * 1024 * 1024):.2f} GB"

    def _get_file_icon(self, name: str) -> Tuple[str, str]:
        """Get file icon and CSS class based on file extension"""
        ext = os.path.splitext(name)[1].lower()

        text_exts = {
            ".txt",
            ".md",
            ".json",
            ".xml",
            ".yaml",
            ".yml",
            ".ini",
            ".cfg",
            ".conf",
            ".log",
        }
        code_exts = {
            ".py",
            ".js",
            ".ts",
            ".jsx",
            ".tsx",
            ".css",
            ".html",
            ".c",
            ".cpp",
            ".h",
            ".java",
            ".go",
            ".rs",
            ".rb",
            ".php",
            ".sh",
        }
        image_exts = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp", ".ico"}
        archive_exts = {".zip", ".tar", ".gz", ".bz2", ".xz", ".7z", ".rar"}

        if ext in text_exts:
            return "📄", "text"
        elif ext in code_exts:
            return "📝", "text"
        elif ext in image_exts:
            return "🖼️", "image"
        elif ext in archive_exts:
            return "📦", "archive"
        else:
            return "📄", "file"

    def _translate_path_no_follow(self, url_path: str) -> Optional[str]:
        """Resolve URL path to filesystem path under root without following symlinks.

        Returns None if the path escapes root. Used for DELETE so we remove only
        the symlink (or real file), never the link target.
        """
        path = unquote(url_path).lstrip("/")
        root = self.server.root_dir
        joined = os.path.normpath(os.path.join(root, path))
        root_abs = os.path.abspath(root)
        resolved_abs = os.path.abspath(joined)
        if resolved_abs != root_abs and not resolved_abs.startswith(root_abs + os.sep):
            return None
        return joined

    def do_DELETE(self) -> None:
        """Handle DELETE requests: remove only the requested path (symlink or file), never the link target."""
        path = self._translate_path_no_follow(self.path)
        if path is None:
            access_log(self, "delete", "403", self.path)
            self.send_error(403, "Forbidden")
            return

        if not os.path.lexists(path):
            access_log(self, "delete", "404", path)
            self.send_error(404, "File not found")
            return

        try:
            if os.path.islink(path):
                os.remove(path)
                debug("Symlink removed", path=path)
            elif os.path.isdir(path):
                shutil.rmtree(path)
                debug("Directory deleted", path=path)
            else:
                NEW_FILE_TRACKER.remove(path)
                os.remove(path)
                debug("File deleted", path=path)

            self.send_response(204)
            self.end_headers()
            access_log(self, "delete", "204", path)
        except PermissionError:
            access_log(self, "delete", "403", path)
            self.send_error(403, "Permission denied")
        except Exception as e:
            access_log(self, "delete", "500", path)
            debug("DELETE error", error=str(e))
            self.send_error(500, str(e))

    def do_POST(self) -> None:
        """Handle POST requests for file uploads via multiple methods

        Supported upload methods:
          - multipart/form-data: browser upload, curl -F "file=@path"
          - application/x-www-form-urlencoded: wget --post-data="data=<base64>&filename=name"
          - raw body: curl --data-binary @path -H "Content-Type: application/octet-stream"
        """
        content_type = self.headers.get("Content-Type", "")
        try:
            if "multipart/form-data" in content_type:
                self._handle_multipart_upload()
            elif "application/x-www-form-urlencoded" in content_type:
                self._handle_urlencoded_upload()
            else:
                self._handle_raw_upload()
        except Exception as e:
            access_log(self, "upload", "500")
            debug("POST error", error=str(e))
            self.send_error(500, str(e))

    def _resolve_upload_path(self, filename: str = None) -> str:
        """Resolve upload destination from URL path and optional filename

        Priority: provided filename > query param ?filename= > URL path basename > generated name
        """
        parsed = urlparse(self.path)
        fs_path = self.translate_path(parsed.path)

        if os.path.isdir(fs_path) or fs_path.endswith(os.sep):
            if not filename:
                query = parse_qs(parsed.query)
                filename = query.get("filename", [None])[0]
            if not filename:
                filename = f"upload_{int(time.time())}"
            return os.path.join(fs_path, os.path.basename(filename))
        return fs_path

    def _send_cli_response(self, filepath: str, existed: bool = False) -> None:
        """Send plain text response for CLI uploads"""
        fn = os.path.basename(filepath)
        size_str = self._format_size(os.path.getsize(filepath))
        status = "replaced" if existed else "uploaded"

        self.send_response(200)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.end_headers()
        self.wfile.write(f"OK {status} {fn} ({size_str})\n".encode("utf-8"))

    def _handle_multipart_upload(self) -> None:
        """Handle multipart/form-data uploads (browser, curl -F)"""
        form = cgi.FieldStorage(
            fp=self.rfile,
            headers=self.headers,
            environ={
                "REQUEST_METHOD": "POST",
                "CONTENT_TYPE": self.headers["Content-Type"],
            },
        )

        fileitem = form["file"]
        if not fileitem.filename:
            access_log(self, "upload", "400")
            self.send_error(400, "No file uploaded")
            return

        fn = os.path.basename(fileitem.filename)
        save_path = self._resolve_upload_path(fn)
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        file_exists = os.path.exists(save_path)

        with open(save_path, "wb") as f:
            f.write(fileitem.file.read())

        NEW_FILE_TRACKER.register(save_path)
        action = "modify" if file_exists else "upload"
        access_log(self, action, "200", save_path)
        debug(
            "File uploaded via multipart",
            path=save_path,
            size=os.path.getsize(save_path),
        )
        self._send_html_upload_response(fn, save_path, file_exists)

    def _handle_urlencoded_upload(self) -> None:
        """Handle URL-encoded uploads with base64 data (wget --post-data)

        Expected POST body: data=<base64_content>&filename=<optional_name>
        """
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            access_log(self, "upload", "400")
            self.send_error(400, "Empty request body")
            return

        body = self.rfile.read(length).decode("utf-8", errors="replace")
        params = parse_qs(body)

        data_field = params.get("data", [None])[0]
        if not data_field:
            access_log(self, "upload", "400")
            self.send_error(400, "Missing 'data' field in POST body")
            return

        file_content = base64.b64decode(data_field)
        filename = params.get("filename", [None])[0]
        save_path = self._resolve_upload_path(filename)
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        file_exists = os.path.exists(save_path)

        with open(save_path, "wb") as f:
            f.write(file_content)

        NEW_FILE_TRACKER.register(save_path)
        action = "modify" if file_exists else "upload"
        access_log(self, action, "200", save_path)
        debug(
            "File uploaded via urlencoded",
            path=save_path,
            size=os.path.getsize(save_path),
        )
        self._send_cli_response(save_path, file_exists)

    def _handle_raw_upload(self) -> None:
        """Handle raw binary body uploads (curl --data-binary, etc.)

        Target filename resolved from URL path or ?filename= query param.
        """
        length = int(self.headers.get("Content-Length", 0))
        if length == 0:
            access_log(self, "upload", "400")
            self.send_error(400, "Empty request body")
            return

        save_path = self._resolve_upload_path()
        os.makedirs(os.path.dirname(save_path), exist_ok=True)
        file_exists = os.path.exists(save_path)

        with open(save_path, "wb") as f:
            f.write(self.rfile.read(length))

        NEW_FILE_TRACKER.register(save_path)
        action = "modify" if file_exists else "upload"
        access_log(self, action, "200", save_path)
        debug(
            "File uploaded via raw body",
            path=save_path,
            size=os.path.getsize(save_path),
        )
        self._send_cli_response(save_path, file_exists)

    def _send_html_upload_response(
        self, filename: str, filepath: str, file_exists: bool
    ) -> None:
        """Send HTML upload success response for browser clients"""
        status = "replaced" if file_exists else "uploaded"
        size_str = self._format_size(os.path.getsize(filepath))
        fn_escaped = html.escape(filename)

        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=utf-8")
        self.end_headers()

        response_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Upload Complete</title>
<style>
:root {{
    --bg-primary: #ffffff;
    --bg-secondary: #f6f8fa;
    --border-color: #d0d7de;
    --text-primary: #1f2328;
    --text-secondary: #656d76;
    --accent-green: #1a7f37;
}}
[data-theme="dark"] {{
    --bg-primary: #0d1117;
    --bg-secondary: #161b22;
    --border-color: #30363d;
    --text-primary: #c9d1d9;
    --text-secondary: #8b949e;
    --accent-green: #3fb950;
}}
html {{ font-size: 18px; }}
body {{
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Helvetica, Arial, sans-serif;
    background: var(--bg-primary);
    color: var(--text-primary);
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 100vh;
    margin: 0;
    transition: background 0.3s, color 0.3s;
}}
.card {{
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 12px;
    padding: 2.5rem;
    text-align: center;
    max-width: 26rem;
}}
.icon {{ font-size: 3rem; margin-bottom: 1rem; }}
h2 {{ margin: 0 0 1rem 0; color: var(--accent-green); font-size: 1.25rem; }}
.info {{ color: var(--text-secondary); margin: 0.5rem 0; font-size: 0.95rem; }}
.btn {{
    display: inline-block;
    margin-top: 1.5rem;
    padding: 0.6rem 1.25rem;
    background: var(--accent-green);
    color: #fff;
    text-decoration: none;
    border-radius: 6px;
    font-weight: 500;
    font-size: 0.9rem;
}}
.btn:hover {{ opacity: 0.9; }}
</style>
</head>
<body>
<script>
const theme = localStorage.getItem('hftp-theme') || 'light';
document.documentElement.setAttribute('data-theme', theme);
</script>
<div class="card">
    <div class="icon">✅</div>
    <h2>File {status} successfully!</h2>
    <p class="info">📄 {fn_escaped}</p>
    <p class="info">📏 {size_str}</p>
    <a href="./" class="btn">Return to directory</a>
</div>
</body>
</html>"""
        self.wfile.write(response_html.encode("utf-8"))


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """Threaded TCP server supporting multiple client connections"""

    allow_reuse_address = True
    daemon_threads = True

    def __init__(self, server_address, RequestHandlerClass, root_dir: str):
        super().__init__(server_address, RequestHandlerClass)
        self.running = True
        self.timeout = 0.1
        self.root_dir = os.path.realpath(root_dir)

    def shutdown(self) -> None:
        """Safely shutdown the server"""
        debug("Server shutdown method called")
        self.running = False

        try:
            super().shutdown()
        except Exception:
            debug("Error in server shutdown")

        debug("Server shutdown completed")


def run_server(server: ThreadedTCPServer) -> None:
    """Run server request loop in a separate thread."""
    debug("Starting server thread")
    try:
        while server.running and not EXIT_EVENT.is_set():
            try:
                server.handle_request()
            except Exception as e:
                debug("Error in handle_request", error=str(e))
                if not server.running or EXIT_EVENT.is_set():
                    break
    except Exception as e:
        debug("Server thread exception", error=str(e))
    finally:
        debug("Server thread exiting")


def create_example_text(
    script_name: str, examples: List[Tuple[str, str]], notes: Optional[List[str]] = None
) -> str:
    """Create formatted example text for CLI help output."""
    text = f"\n{CLIStyle.color('Examples:', CLIStyle.COLORS['SUB_TITLE'])}"

    for desc, cmd in examples:
        text += f"\n  {CLIStyle.color(f'# {desc}', CLIStyle.COLORS['EXAMPLE'])}"
        text += (
            f"\n  {CLIStyle.color(f'{script_name} {cmd}', CLIStyle.COLORS['CONTENT'])}"
        )
        text += "\n"

    if notes:
        text += f"\n{CLIStyle.color('Notes:', CLIStyle.COLORS['SUB_TITLE'])}"
        for note in notes:
            text += f"\n  {CLIStyle.color(f'- {note}', CLIStyle.COLORS['CONTENT'])}"

    return text


def safe_port_check(port: int) -> bool:
    """Check if port is available for binding."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(("", port))
            return True
    except OSError:
        return False


def ensure_available_port(requested_port: int) -> Optional[int]:
    """Ensure a usable port, optionally freeing or suggesting an alternative."""
    if safe_port_check(requested_port):
        return requested_port

    print(
        CLIStyle.color(
            f"Error: Port {requested_port} is already in use!", CLIStyle.COLORS["ERROR"]
        )
    )

    process_info = get_process_using_port(requested_port)
    if process_info:
        pid, command = process_info
        print(
            CLIStyle.color(
                f"Occupying process: PID {pid} - {command}",
                CLIStyle.COLORS["WARNING"],
            )
        )

        if confirm_action("Force close the process occupying this port?"):
            print(
                CLIStyle.color(
                    "Attempting to close process...", CLIStyle.COLORS["CONTENT"]
                )
            )
            if kill_process_by_pid(pid):
                print(
                    CLIStyle.color(
                        f"Process {pid} successfully closed",
                        CLIStyle.COLORS["SUCCESS"],
                    )
                )
                time.sleep(1)
                if safe_port_check(requested_port):
                    print(
                        CLIStyle.color(
                            f"Port {requested_port} is now available",
                            CLIStyle.COLORS["SUCCESS"],
                        )
                    )
                    return requested_port

                print(
                    CLIStyle.color(
                        "Port still occupied, may need more time to release",
                        CLIStyle.COLORS["WARNING"],
                    )
                )
                time.sleep(2)
                if safe_port_check(requested_port):
                    print(
                        CLIStyle.color(
                            f"Port {requested_port} is now available",
                            CLIStyle.COLORS["SUCCESS"],
                        )
                    )
                    return requested_port
                print(
                    CLIStyle.color(
                        "Port release failed, will suggest using alternative port",
                        CLIStyle.COLORS["ERROR"],
                    )
                )
            else:
                print(
                    CLIStyle.color(
                        f"Unable to close process {pid}, may lack permissions",
                        CLIStyle.COLORS["ERROR"],
                    )
                )
        else:
            print(
                CLIStyle.color(
                    "User chose not to close the occupying process",
                    CLIStyle.COLORS["CONTENT"],
                )
            )
    else:
        print(
            CLIStyle.color(
                "Unable to determine process occupying the port",
                CLIStyle.COLORS["WARNING"],
            )
        )

    port_suggestion = requested_port + 1
    while (
        not safe_port_check(port_suggestion) and port_suggestion < requested_port + 10
    ):
        port_suggestion += 1

    if not safe_port_check(port_suggestion):
        print(CLIStyle.color("Server startup cancelled", CLIStyle.COLORS["ERROR"]))
        return None

    print(
        CLIStyle.color(
            f"Suggest using port {port_suggestion} instead",
            CLIStyle.COLORS["CONTENT"],
        )
    )
    if confirm_action("Would you like to use the suggested port?"):
        return port_suggestion

    print(CLIStyle.color("Server startup cancelled", CLIStyle.COLORS["ERROR"]))
    return None


def handle_generate_service(port: int) -> int:
    """Generate systemd service file in current directory and exit.

    return = exit code
    """
    script_path = os.path.abspath(sys.argv[0])
    work_dir = os.getcwd()
    service_content = generate_systemd_service(port, work_dir, script_path)

    output_file = os.path.join(work_dir, "hftp.service")
    try:
        with open(output_file, "w") as f:
            f.write(service_content)

        print(
            CLIStyle.color(
                "Systemd service file generated successfully!",
                CLIStyle.COLORS["SUCCESS"],
            )
        )
        print(f"Output path: {CLIStyle.color(output_file, CLIStyle.COLORS['CONTENT'])}")
        print()
        print(CLIStyle.color("Installation steps:", CLIStyle.COLORS["TITLE"]))
        print(
            f"  1. {CLIStyle.color('sudo ln -sf hftp.service /etc/systemd/system/', CLIStyle.COLORS['CONTENT'])}"
        )
        print(
            f"  2. {CLIStyle.color('sudo systemctl daemon-reload', CLIStyle.COLORS['CONTENT'])}"
        )
        print(
            f"  3. {CLIStyle.color('sudo systemctl enable hftp.service', CLIStyle.COLORS['CONTENT'])}"
        )
        print(
            f"  4. {CLIStyle.color('sudo systemctl start hftp.service', CLIStyle.COLORS['CONTENT'])}"
        )
        print()
        print(CLIStyle.color("Service management:", CLIStyle.COLORS["TITLE"]))
        print(
            f"  - Status: {CLIStyle.color('sudo systemctl status hftp.service', CLIStyle.COLORS['CONTENT'])}"
        )
        print(
            f"  - Logs:   {CLIStyle.color('sudo journalctl -u hftp.service -f', CLIStyle.COLORS['CONTENT'])}"
        )
        return 0
    except Exception as e:
        print(
            CLIStyle.color(
                f"Error generating service file: {str(e)}", CLIStyle.COLORS["ERROR"]
            )
        )
        if DEBUG_MODE:
            traceback.print_exc()
        return 1


def generate_systemd_service(port: int, work_dir: str, script_path: str) -> str:
    """Generate systemd service file content."""
    service_content = f"""[Unit]
Description=FAST FILE TRANSFER SERVER by HTTP
After=network.target

[Service]
Type=simple
User={os.getenv("USER", "root")}
WorkingDirectory={work_dir}
ExecStart={sys.executable} {script_path} --port {port} --batch
ExecReload=/usr/bin/pkill -HUP $MAINPID
ExecStop=/usr/bin/pkill -TERM $MAINPID
Restart=on-failure
RestartSec=5s
StandardOutput=journal
StandardError=journal
StartLimitIntervalSec=300
StartLimitBurst=5
TimeoutStartSec=30s
TimeoutStopSec=10s
Environment="PYTHONUNBUFFERED=1"

[Install]
WantedBy=multi-user.target
"""
    return service_content


def display_server_info(ips: List[str], port: int, root_dir: str) -> None:
    """Display server access URLs and connection info."""
    print(divider("Server Information", 60, "="))
    print(
        f"Server started at port: {CLIStyle.color(str(port), CLIStyle.COLORS['CONTENT'])}"
    )
    print(f"Serving directory: {CLIStyle.color(root_dir, CLIStyle.COLORS['CONTENT'])}")
    if ips:
        print(CLIStyle.color("Available URLs:", CLIStyle.COLORS["TITLE"]))
        for ip in ips:
            url = f"http://{ip}:{port}"
            print(f"  {CLIStyle.color(url, CLIStyle.COLORS['CONTENT'])}")
        print(
            f"  {CLIStyle.color(f'http://localhost:{port}', CLIStyle.COLORS['CONTENT'])}"
        )
    else:
        print(
            f"{CLIStyle.color('No network interfaces found. Try:', CLIStyle.COLORS['WARNING'])}"
        )
        print(
            f"  {CLIStyle.color(f'http://localhost:{port}', CLIStyle.COLORS['CONTENT'])}"
        )
    print(divider("", 60, "="))
    print(
        f"Press {CLIStyle.color('Ctrl+C', CLIStyle.COLORS['WARNING'])} to stop server\n"
    )


def main() -> int:
    """Main entry point for the HTTP file server."""
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    script_name = os.path.basename(sys.argv[0])

    examples = [
        ("Basic usage (serve current directory)", ""),
        ("Custom port", "--port 8080"),
        ("Serve a specific directory (e.g. project or docs)", "--root /path/to/dir"),
        ("Serve current dir with --root", "--root ."),
        ("Debug mode", "--debug"),
        ("Batch mode (auto-confirm)", "--batch"),
        ("Generate systemd service file", "--generate-service --port 8080"),
        ("Quick start with preview", "--port 8000 --preview"),
    ]

    notes = [
        "Files are served from the specified root directory (default: current directory)",
        "Use --root to change the server root directory",
        "Uploads are allowed by default",
        "Use a browser to access the server and view/upload files",
        "Debug mode shows detailed logs for troubleshooting",
        "Batch mode auto-confirms all prompts (useful for systemd services)",
        "Generate service file creates hftp.service in current directory with installation steps",
        "When port is occupied, you can choose to force close the process or use alternative port",
    ]

    parser = ColoredArgumentParser(
        description=CLIStyle.color("Fast HTTP File Server", CLIStyle.COLORS["TITLE"]),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=create_example_text(script_name, examples, notes),
    )

    parser.add_argument(
        "-p",
        "--port",
        type=int,
        default=DEFAULT_PORT,
        help=f"Specify server port (default: {DEFAULT_PORT})",
    )
    parser.add_argument(
        "-r",
        "--root",
        type=str,
        help="Specify root directory to serve (default: current directory)",
    )
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug mode")
    parser.add_argument(
        "-b",
        "--batch",
        action="store_true",
        help="Batch mode: auto-confirm all prompts (for non-interactive environments)",
    )
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Open server URL in browser after starting",
    )
    parser.add_argument(
        "--generate-service",
        action="store_true",
        help="Generate systemd service file in current directory and exit",
    )

    args = parser.parse_args()

    root_dir = os.path.realpath(args.root) if args.root else os.getcwd()
    if not os.path.isdir(root_dir):
        print(
            CLIStyle.color(
                f"Error: Root directory '{root_dir}' does not exist or is not a directory",
                CLIStyle.COLORS["ERROR"],
            )
        )
        return 1

    global DEBUG_MODE, BATCH_MODE
    DEBUG_MODE = args.debug
    BATCH_MODE = args.batch

    if DEBUG_MODE:
        print(CLIStyle.color("Debug mode enabled", CLIStyle.COLORS["WARNING"]))
        debug("Starting server", port=args.port)

    if BATCH_MODE:
        print(CLIStyle.color("Batch mode enabled", CLIStyle.COLORS["WARNING"]))
        debug("Batch mode: all prompts will be auto-confirmed")

    if args.generate_service:
        return handle_generate_service(args.port)

    selected_port = ensure_available_port(args.port)
    if selected_port is None:
        return 1
    args.port = selected_port

    ips = get_all_ips()
    global LOCAL_IPS
    LOCAL_IPS = set(ips) | {"127.0.0.1", "::1"}
    debug("Available IPs", ips=ips)

    try:
        display_server_info(ips, args.port, root_dir)
        atexit.register(
            lambda: print(
                CLIStyle.color("Server fully stopped", CLIStyle.COLORS["SUCCESS"])
            )
        )

        global SERVER_INSTANCE
        SERVER_INSTANCE = ThreadedTCPServer(
            ("0.0.0.0", args.port), EnhancedHTTPRequestHandler, root_dir
        )

        server_thread = threading.Thread(
            target=run_server, args=(SERVER_INSTANCE,), daemon=True
        )
        server_thread.start()

        if args.preview:
            url = f"http://localhost:{args.port}"
            print(
                CLIStyle.color(f"Opening browser at {url}", CLIStyle.COLORS["CONTENT"])
            )
            webbrowser.open(url)

        while SERVER_INSTANCE.running and not EXIT_EVENT.is_set():
            time.sleep(0.05)

    except Exception as e:
        debug("Server error", error=str(e))
        print(CLIStyle.color(f"Error: {str(e)}", CLIStyle.COLORS["ERROR"]))
        if DEBUG_MODE:
            traceback.print_exc()
        emergency_exit()


if __name__ == "__main__":
    sys.exit(main())
