# -*- coding: utf-8 -*-
# pip install ifaddr colorama

import argparse
import http.server
import socketserver
import os
import sys
import io
import cgi
import html
import threading
import socket
import time
import atexit
from typing import List, Optional, Tuple
from urllib.parse import unquote, quote
import ifaddr
import signal

# Global variables and constants
DEBUG_MODE = False
CLI_COLORS = {
    "TITLE": 7,  # Cyan - Main title
    "SUB_TITLE": 2,  # Red - Subtitle
    "CONTENT": 3,  # Green - Normal content
    "EXAMPLE": 7,  # Cyan - Example
    "WARNING": 4,  # Yellow - Warning
    "ERROR": 2,  # Red - Error
    "SUCCESS": 3,  # Green - Success
}

# Global server instance for signal handling
SERVER_INSTANCE = None
EXIT_EVENT = threading.Event()


# Utility functions
def color(text: str, color_code: int = 3) -> str:
    """
    Add color to text
    ```python
    color(
        "Hello World",     # Text to color
        CLI_COLORS["TITLE"]    # Color code, default is green
    )

    return = "\033[1;32m{}\033[0m".format(text)
    ```
    """
    color_table = {
        0: "{}",  # No color
        1: "\033[1;30m{}\033[0m",  # Bold black
        2: "\033[1;31m{}\033[0m",  # Bold red
        3: "\033[1;32m{}\033[0m",  # Bold green
        4: "\033[1;33m{}\033[0m",  # Bold yellow
        5: "\033[1;34m{}\033[0m",  # Bold blue
        6: "\033[1;35m{}\033[0m",  # Bold purple
        7: "\033[1;36m{}\033[0m",  # Bold cyan
        8: "\033[1;37m{}\033[0m",  # Bold white
    }
    return color_table[color_code].format(text)


def debug(*args, file: Optional[str] = None, append: bool = True, **kwargs) -> None:
    """
    Print debug information with source file and line number
    ```python
    debug(
        'Hello',    # Parameter 1 to print
        'World',    # Parameter 2 to print
        file='debug.log',  # Output file path, default is None (console output)
        append=False,  # Whether to append to file, default is True
        **kwargs  # Key-value parameters to print
    )

    return = None
    ```
    """
    if not DEBUG_MODE:
        return

    import inspect
    import re

    frame = inspect.currentframe().f_back
    info = inspect.getframeinfo(frame)

    file_name = os.path.basename(info.filename)
    output = f"{color(file_name, 3)}: {color(str(info.lineno), 4)} {color('|', 7)} "

    for i, arg in enumerate(args):
        arg_str = str(arg)
        output += f"{color(arg_str, 2)} "

    for k, v in kwargs.items():
        output += f"{color(k + '=', 6)}{color(str(v), 2)} "

    output += "\n"

    if file:
        mode = "a" if append else "w"
        with open(file, mode) as f:
            clean_output = re.sub(r"\033\[\d+;\d+m|\033\[0m", "", output)
            f.write(clean_output)
    else:
        print(output, end="")


def emergency_exit():
    """
    Force process termination with extreme prejudice
    """
    debug("Emergency exit called")
    print(color("Server stopped", CLI_COLORS["SUCCESS"]))
    # On Windows, use os._exit which doesn't clean up resources but ensures termination
    os._exit(0)


def force_exit_after(seconds: int = 2):
    """
    Schedule a forced exit after specified seconds
    """
    debug(f"Scheduling forced exit in {seconds} seconds")
    time.sleep(seconds)
    emergency_exit()


def divider(title: str = "", width: int = 80, char: str = "-") -> str:
    """
    Create a divider with optional title
    ```python
    divider(
        "Section Title",  # Center title, default is empty
        80,              # Total divider width, default is 80
        "-"              # Divider character, default is "-"
    )

    return = "---- Section Title ----"  # Formatted divider
    ```
    """
    if not title:
        return char * width

    side_width = (width - len(title) - 2) // 2
    if side_width <= 0:
        return title

    return f"{char * side_width} {title} {char * side_width}"


def get_all_ips() -> List[str]:
    """
    Get all local non-loopback IPv4 addresses
    ```python
    get_all_ips()

    return = ["192.168.1.100", "10.0.0.5"]  # List of all local IPv4 addresses
    ```
    """
    ips = []
    adapters = ifaddr.get_adapters()
    for adapter in adapters:
        for ip in adapter.ips:
            if ip.is_IPv4 and ip.ip != "127.0.0.1":
                if ip.ip not in ips:
                    ips.append(ip.ip)
    return ips


def confirm_action(prompt: str) -> bool:
    """
    Request user confirmation for an action
    ```python
    confirm_action(
        "Do you want to proceed?"  # Confirmation prompt
    )

    return = True  # Returns True if user confirms, False otherwise
    ```
    """
    response = input(f"{prompt} (y/n): ").lower().strip()
    return response == "y" or response == "yes"


def signal_handler(sig, frame):
    """
    Handle interrupt signals
    ```python
    signal_handler(
        signal.SIGINT,  # Signal received
        frame           # Current stack frame
    )

    return = None
    ```
    """
    print(color("\nShutting down server...", CLI_COLORS["WARNING"]))
    # Immediately start a thread that will force exit after a short delay
    threading.Thread(target=force_exit_after, args=(1,), daemon=True).start()

    # Try to clean up, but don't rely on it
    try:
        global SERVER_INSTANCE, EXIT_EVENT
        EXIT_EVENT.set()
        if SERVER_INSTANCE:
            debug("Signal handler shutting down server")
            SERVER_INSTANCE.running = False
    except Exception as e:
        debug("Error in signal handler", error=str(e))

    # Don't wait for the delayed exit - try to exit now
    emergency_exit()


# Class definitions
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
                        lambda x: color(x, CLI_COLORS["SUB_TITLE"]),
                        action.option_strings,
                    )
                )
            else:
                default = action.dest.upper()
                args_string = self._format_args(action, default)
                for option_string in action.option_strings:
                    parts.append(
                        color(
                            f"{option_string} {args_string}",
                            CLI_COLORS["SUB_TITLE"],
                        )
                    )
            return ", ".join(parts)

    def format_help(self):
        formatter = self._get_formatter()

        # Add description
        if self.description:
            formatter.add_text(color(self.description, CLI_COLORS["TITLE"]))

        # Add usage
        formatter.add_usage(self.usage, self._actions, self._mutually_exclusive_groups)

        # Add argument groups
        formatter.add_text(color("\nOptional Arguments:", CLI_COLORS["TITLE"]))
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

        file_list.sort(key=lambda a: a.lower())
        r = []
        displaypath = unquote(self.path)
        enc = sys.getfilesystemencoding()
        title = f"Directory Listing: {displaypath}"

        # Add upload form
        r.append("<!DOCTYPE HTML>")
        r.append("<html>\n<head>")
        r.append(f'<meta charset="{enc}">')
        r.append(f"<title>{title}</title>")
        r.append("<style>")
        r.append("body { font-family: Arial, sans-serif; margin: 20px; }")
        r.append("h1 { color: #333; }")
        r.append("hr { border: 1px solid #ddd; }")
        r.append("form { margin: 20px 0; }")
        r.append(
            "input[type=submit] { padding: 5px 15px; background: #4CAF50; color: white; border: none; cursor: pointer; }"
        )
        r.append("ul { list-style: none; padding: 0; }")
        r.append("li { margin: 5px 0; }")
        r.append("a { text-decoration: none; color: #2196F3; }")
        r.append("a:hover { text-decoration: underline; }")
        r.append("</style>\n</head>")
        r.append(f"<body>\n<h1>{title}</h1>")
        r.append("<hr>\n")
        r.append('<form ENCTYPE="multipart/form-data" method="post">')
        r.append('<input name="file" type="file"/>')
        r.append('<input type="submit" value="Upload File"/>')
        r.append("</form>")
        r.append("<hr>\n<ul>")

        for name in file_list:
            fullname = os.path.join(path, name)
            displayname = linkname = name

            # Display file size and modification date
            file_size = ""
            file_date = ""
            if os.path.isfile(fullname):
                file_size = os.path.getsize(fullname)
                if file_size < 1024:
                    file_size = f"{file_size} B"
                elif file_size < 1024 * 1024:
                    file_size = f"{file_size / 1024:.1f} KB"
                else:
                    file_size = f"{file_size / (1024 * 1024):.1f} MB"

                file_date = time.strftime(
                    "%Y-%m-%d %H:%M:%S", time.localtime(os.path.getmtime(fullname))
                )
                file_info = f" - {file_size}, {file_date}"
            else:
                file_info = ""

            if os.path.isdir(fullname):
                displayname = name + "/"
                linkname = name + "/"
                file_info = " - Directory"
            if os.path.islink(fullname):
                displayname = name + "@"
                file_info = " - Symlink"

            r.append(
                f'<li><a href="{quote(linkname)}">{html.escape(displayname)}</a>{file_info}</li>'
            )

        r.append("</ul>\n<hr>\n</body>\n</html>")
        encoded = "\n".join(r).encode(enc, "surrogateescape")

        f = io.BytesIO()
        f.write(encoded)
        f.seek(0)

        self.send_response(200)
        self.send_header("Content-type", f"text/html; charset={enc}")
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        return f

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
                path = self.translate_path(fn)

                # Check if file already exists
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
                self.wfile.write(
                    f'<html><body style="font-family: Arial, sans-serif; margin: 20px;">'
                    f'<h2 style="color: green;">File successfully {status}!</h2>'
                    f"<p>File: {html.escape(fn)}</p>"
                    f"<p>Size: {os.path.getsize(path)} bytes</p>"
                    f'<p><a href="/" style="color: #2196F3;">Return to index</a></p>'
                    f"</body></html>".encode("utf-8")
                )
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
        # Set a short timeout to avoid blocking in handle_request
        self.timeout = 0.1

    def shutdown(self) -> None:
        """Safely shutdown the server"""
        debug("Server shutdown method called")
        self.running = False

        try:
            super().shutdown()
        except:
            debug("Error in server shutdown")

        debug("Server shutdown completed")


def run_server(server: ThreadedTCPServer) -> None:
    """
    Run server in a separate thread
    ```python
    run_server(
        server  # ThreadedTCPServer instance
    )

    return = None
    ```
    """
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
    """
    Create unified example text
    ```python
    create_example_text(
        "server.py",             # Script name
        [                        # Examples list, each example is a (description, command) tuple
            ("Start server", "--port 8080"),
            ("Debug mode", "--port 8080 --debug")
        ],
        ["Note 1", "Note 2"]     # Optional notes list
    )

    return = "formatted text with examples and notes"
    ```
    """
    text = f"\n{color('Examples:', CLI_COLORS['SUB_TITLE'])}"

    for desc, cmd in examples:
        text += f"\n  {color(f'# {desc}', CLI_COLORS['EXAMPLE'])}"
        text += f"\n  {color(f'{script_name} {cmd}', CLI_COLORS['CONTENT'])}"
        text += "\n"

    if notes:
        text += f"\n{color('Notes:', CLI_COLORS['SUB_TITLE'])}"
        for note in notes:
            text += f"\n  {color(f'- {note}', CLI_COLORS['CONTENT'])}"

    return text


def safe_port_check(port: int) -> bool:
    """
    Check if port is available
    ```python
    safe_port_check(
        8080  # Port number to check
    )

    return = True  # Returns True if port is available, False otherwise
    ```
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(("", port))
            return True
    except:
        return False


def display_server_info(ips: List[str], port: int) -> None:
    """
    Display server access information
    ```python
    display_server_info(
        ["192.168.1.100", "10.0.0.5"],  # IP address list
        8080                            # Port number
    )

    return = None
    ```
    """
    print(divider("Server Information", 60, "="))
    print(f"Server started at port: {color(str(port), CLI_COLORS['CONTENT'])}")
    if ips:
        print("Available URLs:")
        for ip in ips:
            url = f"http://{ip}:{port}"
            print(f"  {color(url, CLI_COLORS['CONTENT'])}")
        print(f"  {color(f'http://localhost:{port}', CLI_COLORS['CONTENT'])}")
    else:
        print(f"{color('No network interfaces found. Try:', CLI_COLORS['WARNING'])}")
        print(f"  {color(f'http://localhost:{port}', CLI_COLORS['CONTENT'])}")
    print(divider("", 60, "="))
    print(f"Press {color('Ctrl+C', CLI_COLORS['WARNING'])} to stop server\n")


def main() -> None:
    """Main function to handle command line arguments and start server"""
    # Register emergency exit for atexit
    atexit.register(lambda: print(color("Server fully stopped", CLI_COLORS["SUCCESS"])))

    # Register signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    script_name = os.path.basename(sys.argv[0])

    # Define examples and notes
    examples = [
        ("Basic usage", ""),
        ("Custom port", "--port 8080"),
        ("Debug mode", "--debug"),
        ("Quick start with preview", "--port 8000 --preview"),
    ]

    notes = [
        "Files will be served from the current directory",
        "Uploads are allowed by default",
        "Use a browser to access the server and view/upload files",
        "Debug mode shows detailed logs for troubleshooting",
    ]

    parser = ColoredArgumentParser(
        description=color("Fast HTTP File Server", CLI_COLORS["TITLE"]),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=create_example_text(script_name, examples, notes),
    )

    parser.add_argument(
        "-p",
        "--port",
        type=int,
        default=1024,
        help="Specify server port (default: 1024)",
    )
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug mode")
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Open server URL in browser after starting",
    )

    args = parser.parse_args()

    # Set global debug mode
    global DEBUG_MODE
    DEBUG_MODE = args.debug

    if DEBUG_MODE:
        print(color("Debug mode enabled", CLI_COLORS["WARNING"]))
        debug("Starting server", port=args.port)

    # Check if port is available
    if not safe_port_check(args.port):
        print(color(f"Error: Port {args.port} is already in use!", CLI_COLORS["ERROR"]))
        port_suggestion = args.port + 1
        while not safe_port_check(port_suggestion) and port_suggestion < args.port + 10:
            port_suggestion += 1

        if safe_port_check(port_suggestion):
            print(
                color(
                    f"Try using port {port_suggestion} instead.", CLI_COLORS["CONTENT"]
                )
            )
            if confirm_action("Would you like to use this port instead?"):
                args.port = port_suggestion
            else:
                print(color("Server startup aborted", CLI_COLORS["ERROR"]))
                return
        else:
            print(color("Server startup aborted", CLI_COLORS["ERROR"]))
            return

    # Get all available IP addresses
    ips = get_all_ips()
    debug("Available IPs", ips=ips)

    try:
        # Display server information
        display_server_info(ips, args.port)

        # Create server
        global SERVER_INSTANCE
        SERVER_INSTANCE = ThreadedTCPServer(
            ("0.0.0.0", args.port), EnhancedHTTPRequestHandler
        )

        # Run server in a new thread
        server_thread = threading.Thread(
            target=run_server, args=(SERVER_INSTANCE,), daemon=True
        )
        server_thread.start()

        # If needed, automatically open browser
        if args.preview:
            import webbrowser

            url = f"http://localhost:{args.port}"
            print(color(f"Opening browser at {url}", CLI_COLORS["CONTENT"]))
            webbrowser.open(url)

        # The main thread now just waits - signal handler will handle Ctrl+C
        # We use a shorter sleep interval for better responsiveness
        try:
            while SERVER_INSTANCE.running and not EXIT_EVENT.is_set():
                time.sleep(0.05)
        except KeyboardInterrupt:
            # Direct handling of keyboard interrupt
            print(color("\nShutting down server directly...", CLI_COLORS["WARNING"]))
            emergency_exit()

    except Exception as e:
        debug("Server error", error=str(e))
        print(color(f"Error: {str(e)}", CLI_COLORS["ERROR"]))
        if DEBUG_MODE:
            import traceback

            traceback.print_exc()
        emergency_exit()


if __name__ == "__main__":
    main()
