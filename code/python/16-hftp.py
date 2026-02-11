# -*- coding: utf-8 -*-
# pip install ifaddr colorama legacy-cgi

import argparse
import atexit
import http.server
import html
import io
import mimetypes
import os
import shutil
import signal
import socket
import socketserver
import subprocess
import sys
import threading
import time
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

    import inspect
    import re

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


def emergency_exit():
    """Force process termination with extreme prejudice"""
    debug("Emergency exit called")
    print(CLIStyle.color("Server stopped", CLIStyle.COLORS["SUCCESS"]))
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
        """Handle GET requests with text file preview support"""
        parsed = urlparse(self.path)
        query = parse_qs(parsed.query)
        path = self.translate_path(parsed.path)

        if (
            os.path.isfile(path)
            and query.get("preview", ["0"])[0] == "1"
            and is_text_file(path)
        ):
            self.serve_text_preview(path)
        else:
            self.path = parsed.path
            super().do_GET()

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
<link rel="stylesheet" id="hljs-theme" href="https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github.min.css">
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

    def do_PUT(self) -> None:
        """Handle PUT requests for file uploads"""
        path = self.translate_path(self.path)
        if path.endswith("/"):
            self.send_error(400, "Cannot PUT to directory")
            return

        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            length = int(self.headers["Content-Length"])
            with open(path, "wb") as f:
                f.write(self.rfile.read(length))

            self.send_response(201)
            self.end_headers()
            debug("File uploaded via PUT", path=path)
        except Exception as e:
            debug("PUT error", error=str(e))
            self.send_error(500, str(e))

    def translate_path(self, path: str) -> str:
        """Convert URL path to filesystem path"""
        path = unquote(path)
        path = path.lstrip("/")
        return os.path.join(os.getcwd(), path)

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

        dirs = []
        files = []
        for name in file_list:
            fullname = os.path.join(path, name)
            if os.path.isdir(fullname):
                dirs.append(name)
            else:
                files.append(name)

        dirs.sort(key=lambda a: a.lower())
        files.sort(key=lambda a: a.lower())

        displaypath = unquote(self.path)
        enc = sys.getfilesystemencoding()
        title = f"Directory: {displaypath}"

        html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="{enc}">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
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
header h1 .icon {{ color: var(--accent-blue); }}
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
    grid-template-columns: 1fr 6rem 11rem 7rem;
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
    grid-template-columns: 1fr 6rem 11rem 7rem;
    padding: 0.75rem 1rem;
    border-bottom: 1px solid var(--border-color);
    transition: background 0.15s;
}}
.file-item:last-child {{ border-bottom: none; }}
.file-item:hover {{ background: var(--hover-bg); }}
.file-name {{
    display: flex;
    align-items: center;
    gap: 0.6rem;
}}
.file-name a {{
    color: var(--accent-blue);
    text-decoration: none;
    font-weight: 500;
    font-size: 0.95rem;
}}
.file-name a:hover {{ text-decoration: underline; }}
.file-icon {{
    width: 1.25rem;
    text-align: center;
    flex-shrink: 0;
    font-size: 1.1rem;
}}
.file-icon.folder {{ color: var(--accent-yellow); }}
.file-icon.file {{ color: var(--text-secondary); }}
.file-icon.text {{ color: var(--accent-green); }}
.file-icon.image {{ color: var(--accent-purple); }}
.file-icon.archive {{ color: var(--accent-red); }}
.file-size, .file-date {{
    color: var(--text-secondary);
    font-size: 0.85rem;
    display: flex;
    align-items: center;
}}
.preview-badge {{
    font-size: 0.65rem;
    background: var(--accent-green);
    color: #fff;
    padding: 0.15rem 0.4rem;
    border-radius: 10px;
    margin-left: 0.5rem;
}}
.file-actions {{
    display: flex;
    align-items: center;
    gap: 0.4rem;
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
    .file-list-header {{ display: none; }}
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
            <h1><span class="icon">📁</span> File Server</h1>
            <div class="breadcrumb">{self._generate_breadcrumb(displaypath)}</div>
        </div>
        <button class="theme-toggle" onclick="toggleTheme()">
            <span class="icon" id="themeIcon">🌙</span>
            <span id="themeText">Dark</span>
        </button>
    </header>

    <div class="upload-section">
        <div class="upload-title"><span class="icon">⬆️</span> Upload File</div>
        <div class="upload-zone" id="uploadZone">
            <input type="file" id="fileInput" name="file">
            <p>Drag & drop files here or click to browse</p>
            <button type="button" class="btn" onclick="document.getElementById('fileInput').click()">Select File</button>
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
            <span>Name</span>
            <span>Size</span>
            <span>Modified</span>
            <span>Actions</span>
        </div>
'''

        if displaypath != "/":
            html_content += """
        <div class="file-item">
            <div class="file-name">
                <span class="file-icon folder">📂</span>
                <a href="../">..</a>
            </div>
            <div class="file-size">-</div>
            <div class="file-date">-</div>
            <div class="file-actions"></div>
        </div>
"""

        for name in dirs:
            fullname = os.path.join(path, name)
            try:
                mtime = time.strftime(
                    "%Y-%m-%d %H:%M", time.localtime(os.path.getmtime(fullname))
                )
            except OSError:
                mtime = "-"

            escaped_name = html.escape(name).replace("'", "\\'")
            html_content += f'''
        <div class="file-item">
            <div class="file-name">
                <span class="file-icon folder">📁</span>
                <a href="{quote(name)}/">{html.escape(name)}</a>
            </div>
            <div class="file-size">-</div>
            <div class="file-date">{mtime}</div>
            <div class="file-actions">
                <button class="action-btn delete" onclick="confirmDelete('{escaped_name}/', true)">🗑️</button>
            </div>
        </div>
'''

        for name in files:
            fullname = os.path.join(path, name)
            try:
                size = os.path.getsize(fullname)
                size_str = self._format_size(size)
                mtime = time.strftime(
                    "%Y-%m-%d %H:%M", time.localtime(os.path.getmtime(fullname))
                )
            except OSError:
                size_str = "-"
                mtime = "-"

            icon, icon_class = self._get_file_icon(name)
            is_previewable = is_text_file(fullname)
            preview_badge = (
                '<span class="preview-badge">VIEW</span>' if is_previewable else ""
            )
            link_url = f"{quote(name)}?preview=1" if is_previewable else quote(name)
            escaped_name = html.escape(name).replace("'", "\\'")

            html_content += f'''
        <div class="file-item">
            <div class="file-name">
                <span class="file-icon {icon_class}">{icon}</span>
                <a href="{link_url}">{html.escape(name)}</a>{preview_badge}
            </div>
            <div class="file-size">{size_str}</div>
            <div class="file-date">{mtime}</div>
            <div class="file-actions">
                <a href="{quote(name)}" class="action-btn" download>⬇️</a>
                <button class="action-btn delete" onclick="confirmDelete('{escaped_name}', false)">🗑️</button>
            </div>
        </div>
'''

        if not dirs and not files:
            html_content += """
        <div class="empty-state">
            <p>📭 This directory is empty</p>
        </div>
"""

        html_content += """
    </div>
    <footer>HTTP File Transfer Protocol Server</footer>
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
const uploadZone = document.getElementById('uploadZone');
const fileInput = document.getElementById('fileInput');
const progressContainer = document.getElementById('progressContainer');

function formatBytes(bytes) {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

function formatTime(seconds) {
    if (!isFinite(seconds) || seconds < 0) return '-';
    if (seconds < 60) return Math.round(seconds) + 's';
    if (seconds < 3600) return Math.round(seconds / 60) + 'm ' + Math.round(seconds % 60) + 's';
    return Math.floor(seconds / 3600) + 'h ' + Math.round((seconds % 3600) / 60) + 'm';
}

function uploadFile(file) {
    const xhr = new XMLHttpRequest();
    const formData = new FormData();
    formData.append('file', file);

    progressContainer.classList.add('active');
    document.getElementById('fileName').textContent = file.name;
    document.getElementById('totalSize').textContent = formatBytes(file.size);

    let startTime = Date.now();
    let lastLoaded = 0;
    let lastTime = startTime;

    xhr.upload.addEventListener('progress', function(e) {
        if (e.lengthComputable) {
            const percent = Math.round((e.loaded / e.total) * 100);
            document.getElementById('progressFill').style.width = percent + '%';
            document.getElementById('progressPercent').textContent = percent + '%';
            document.getElementById('uploadedSize').textContent = formatBytes(e.loaded);

            const now = Date.now();
            const timeDiff = (now - lastTime) / 1000;
            if (timeDiff >= 0.5) {
                const byteDiff = e.loaded - lastLoaded;
                const speed = byteDiff / timeDiff;
                document.getElementById('uploadSpeed').textContent = formatBytes(speed) + '/s';

                const remaining = e.total - e.loaded;
                const timeRemaining = speed > 0 ? remaining / speed : 0;
                document.getElementById('timeRemaining').textContent = formatTime(timeRemaining);

                lastLoaded = e.loaded;
                lastTime = now;
            }
        }
    });

    xhr.addEventListener('load', function() {
        if (xhr.status === 200) {
            document.getElementById('progressPercent').textContent = 'Complete!';
            document.getElementById('uploadSpeed').textContent = '-';
            document.getElementById('timeRemaining').textContent = '0s';
            setTimeout(() => location.reload(), 1000);
        } else {
            alert('Upload failed: ' + xhr.statusText);
        }
    });

    xhr.addEventListener('error', function() {
        alert('Upload error occurred');
    });

    xhr.open('POST', window.location.pathname, true);
    xhr.send(formData);
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
    if (files.length > 0) uploadFile(files[0]);
});

fileInput.addEventListener('change', function(e) {
    if (e.target.files.length > 0) uploadFile(e.target.files[0]);
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
    document.getElementById('themeIcon').textContent = theme === 'dark' ? '☀️' : '🌙';
    document.getElementById('themeText').textContent = theme === 'dark' ? 'Light' : 'Dark';
}

initTheme();

// Delete functionality
let deleteTarget = '';
let deleteIsDir = false;

function confirmDelete(name, isDir) {
    deleteTarget = name;
    deleteIsDir = isDir;
    document.getElementById('deleteFileName').textContent = name;
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
    xhr.open('DELETE', window.location.pathname + encodeURIComponent(deleteTarget.replace(/\\/$/, '')), true);
    
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

    def do_DELETE(self) -> None:
        """Handle DELETE requests for file/folder deletion"""
        path = self.translate_path(self.path)

        if not os.path.exists(path):
            self.send_error(404, "File not found")
            return

        try:
            if os.path.isdir(path):
                shutil.rmtree(path)
                debug("Directory deleted", path=path)
            else:
                os.remove(path)
                debug("File deleted", path=path)

            self.send_response(204)
            self.end_headers()
        except PermissionError:
            self.send_error(403, "Permission denied")
        except Exception as e:
            debug("DELETE error", error=str(e))
            self.send_error(500, str(e))

    def do_POST(self) -> None:
        """Handle POST requests for form file uploads"""
        try:
            form = cgi.FieldStorage(
                fp=self.rfile,
                headers=self.headers,
                environ={
                    "REQUEST_METHOD": "POST",
                    "CONTENT_TYPE": self.headers["Content-Type"],
                },
            )

            fileitem = form["file"]
            if fileitem.filename:
                fn = os.path.basename(fileitem.filename)
                current_dir = self.translate_path(self.path)
                path = os.path.join(current_dir, fn)

                file_exists = os.path.exists(path)
                if file_exists:
                    debug("File already exists", path=path)

                with open(path, "wb") as f:
                    f.write(fileitem.file.read())

                debug("File uploaded via POST", path=path, size=os.path.getsize(path))

                self.send_response(200)
                self.send_header("Content-type", "text/html; charset=utf-8")
                self.end_headers()

                status = "replaced" if file_exists else "uploaded"
                size_str = self._format_size(os.path.getsize(path))
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
    <p class="info">📄 {html.escape(fn)}</p>
    <p class="info">📏 {size_str}</p>
    <a href="./" class="btn">Return to directory</a>
</div>
</body>
</html>"""
                self.wfile.write(response_html.encode("utf-8"))
            else:
                debug("No file in upload")
                self.send_error(400, "No file uploaded")
        except Exception as e:
            debug("POST error", error=str(e))
            self.send_error(500, str(e))


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    """Threaded TCP server supporting multiple client connections"""

    allow_reuse_address = True
    daemon_threads = True

    def __init__(self, server_address, RequestHandlerClass):
        super().__init__(server_address, RequestHandlerClass)
        self.running = True
        self.timeout = 0.1

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
            s.bind(("", port))
            return True
    except OSError:
        return False


def generate_systemd_service(port: int, work_dir: str, script_path: str) -> str:
    """Generate systemd service file content."""
    service_content = f"""[Unit]
Description=HTTP File Transfer Protocol Server
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


def display_server_info(ips: List[str], port: int) -> None:
    """Display server access URLs and connection info."""
    print(divider("Server Information", 60, "="))
    print(
        f"Server started at port: {CLIStyle.color(str(port), CLIStyle.COLORS['CONTENT'])}"
    )
    if ips:
        print("Available URLs:")
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
        ("Basic usage", ""),
        ("Custom port", "--port 8080"),
        ("Debug mode", "--debug"),
        ("Batch mode (auto-confirm)", "--batch"),
        ("Generate systemd service file", "--generate-service --port 8080"),
        ("Quick start with preview", "--port 8000 --preview"),
    ]

    notes = [
        "Files will be served from the current directory",
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
        script_path = os.path.abspath(sys.argv[0])
        work_dir = os.getcwd()
        service_content = generate_systemd_service(args.port, work_dir, script_path)

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
            print(
                f"Output path: {CLIStyle.color(output_file, CLIStyle.COLORS['CONTENT'])}"
            )
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
                import traceback

                traceback.print_exc()
            return 1

    if not safe_port_check(args.port):
        print(
            CLIStyle.color(
                f"Error: Port {args.port} is already in use!", CLIStyle.COLORS["ERROR"]
            )
        )

        process_info = get_process_using_port(args.port)
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
                    if safe_port_check(args.port):
                        print(
                            CLIStyle.color(
                                f"Port {args.port} is now available",
                                CLIStyle.COLORS["SUCCESS"],
                            )
                        )
                    else:
                        print(
                            CLIStyle.color(
                                "Port still occupied, may need more time to release",
                                CLIStyle.COLORS["WARNING"],
                            )
                        )
                        time.sleep(2)
                        if not safe_port_check(args.port):
                            print(
                                CLIStyle.color(
                                    "Port release failed, will suggest using alternative port",
                                    CLIStyle.COLORS["ERROR"],
                                )
                            )
                        else:
                            print(
                                CLIStyle.color(
                                    f"Port {args.port} is now available",
                                    CLIStyle.COLORS["SUCCESS"],
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

        if not safe_port_check(args.port):
            port_suggestion = args.port + 1
            while (
                not safe_port_check(port_suggestion)
                and port_suggestion < args.port + 10
            ):
                port_suggestion += 1

            if safe_port_check(port_suggestion):
                print(
                    CLIStyle.color(
                        f"Suggest using port {port_suggestion} instead",
                        CLIStyle.COLORS["CONTENT"],
                    )
                )
                if confirm_action("Would you like to use the suggested port?"):
                    args.port = port_suggestion
                else:
                    print(
                        CLIStyle.color(
                            "Server startup cancelled", CLIStyle.COLORS["ERROR"]
                        )
                    )
                    return 1
            else:
                print(
                    CLIStyle.color("Server startup cancelled", CLIStyle.COLORS["ERROR"])
                )
                return 1

    ips = get_all_ips()
    debug("Available IPs", ips=ips)

    try:
        display_server_info(ips, args.port)
        atexit.register(
            lambda: print(
                CLIStyle.color("Server fully stopped", CLIStyle.COLORS["SUCCESS"])
            )
        )

        global SERVER_INSTANCE
        SERVER_INSTANCE = ThreadedTCPServer(
            ("0.0.0.0", args.port), EnhancedHTTPRequestHandler
        )

        server_thread = threading.Thread(
            target=run_server, args=(SERVER_INSTANCE,), daemon=True
        )
        server_thread.start()

        if args.preview:
            import webbrowser

            url = f"http://localhost:{args.port}"
            print(
                CLIStyle.color(f"Opening browser at {url}", CLIStyle.COLORS["CONTENT"])
            )
            webbrowser.open(url)

        try:
            while SERVER_INSTANCE.running and not EXIT_EVENT.is_set():
                time.sleep(0.05)
        except KeyboardInterrupt:
            print(
                CLIStyle.color(
                    "\nShutting down server directly...", CLIStyle.COLORS["WARNING"]
                )
            )
            emergency_exit()

    except Exception as e:
        debug("Server error", error=str(e))
        print(CLIStyle.color(f"Error: {str(e)}", CLIStyle.COLORS["ERROR"]))
        if DEBUG_MODE:
            import traceback

            traceback.print_exc()
        emergency_exit()


if __name__ == "__main__":
    sys.exit(main())
