# -*- coding: utf-8 -*-
# pip install watchdog rich psutil

import os
import sys
import time
import argparse
from typing import Optional, List, Dict

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler
    from rich.console import Console
    from rich.text import Text
    import psutil
except ImportError as e:
    print(f"Missing required packages: {e}")
    print("Please install with: pip install watchdog rich psutil")
    sys.exit(1)

DEBUG_MODE = False


def get_process_info_for_file(
    filepath: str, event_type: str = "UNKNOWN"
) -> Optional[Dict[str, str]]:
    """
    Get process information for a file operation
    Uses multiple methods to find the most likely responsible process
    """
    debug(f"Getting process info for: {filepath}, event: {event_type}")
    import subprocess

    if event_type in ["CREATED", "MODIFIED", "DELETED"]:
        try:
            debug("Trying recent process detection")
            dir_path = (
                os.path.dirname(filepath) if not os.path.isdir(filepath) else filepath
            )
            filename = os.path.basename(filepath)

            recent_candidates = []
            current_time = time.time()

            for proc in psutil.process_iter(
                ["pid", "name", "exe", "cmdline", "create_time"]
            ):
                try:
                    proc_info = proc.info
                    if current_time - proc_info.get("create_time", 0) > 30:
                        continue

                    cmdline = proc_info.get("cmdline", [])
                    if not cmdline:
                        continue

                    cmdline_str = " ".join(cmdline)

                    # Check if process command line contains the directory or filename
                    if (
                        dir_path in cmdline_str
                        or filename in cmdline_str
                        or filepath in cmdline_str
                    ):
                        recent_candidates.append(
                            {
                                "pid": str(proc_info["pid"]),
                                "name": proc_info["name"],
                                "path": proc_info.get("exe", "Unknown"),
                                "cmdline": cmdline_str,
                                "create_time": proc_info.get("create_time", 0),
                            }
                        )

                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue

            # Return the most recent candidate
            if recent_candidates:
                # Sort by creation time, most recent first
                recent_candidates.sort(key=lambda x: x["create_time"], reverse=True)
                debug(f"Found recent process candidate: {recent_candidates[0]}")
                return recent_candidates[0]

        except Exception as e:
            debug(f"Recent process detection failed: {e}")

    # Method 2: Try lsof for active file handles
    try:
        debug("Trying lsof method")
        result = subprocess.run(
            ["lsof", "-F", "pcn", filepath], capture_output=True, text=True, timeout=1
        )

        if result.returncode == 0 and result.stdout.strip():
            lines = result.stdout.strip().split("\n")
            debug(f"lsof output: {lines}")
            processes = []

            current_process = {}
            for line in lines:
                if line.startswith("p"):
                    if current_process:
                        processes.append(current_process)
                    current_process = {"pid": line[1:]}
                elif line.startswith("c") and current_process:
                    current_process["name"] = line[1:]
                elif line.startswith("n") and current_process:
                    current_process["path"] = line[1:]

            if current_process:
                processes.append(current_process)

            if processes:
                debug(f"Found process via lsof: {processes[0]}")
                return processes[0]

    except (
        subprocess.TimeoutExpired,
        subprocess.CalledProcessError,
        FileNotFoundError,
    ) as e:
        debug(f"lsof method failed: {e}")

    # Method 3: Try to find processes working in the same directory
    try:
        debug("Trying directory-based process detection")
        dir_path = (
            os.path.dirname(filepath) if not os.path.isdir(filepath) else filepath
        )

        for proc in psutil.process_iter(["pid", "name", "exe", "cmdline", "cwd"]):
            try:
                proc_info = proc.info

                # Check if process is working in the same directory
                if proc_info.get("cwd") == dir_path:
                    debug(f"Found process working in same directory: {proc_info}")
                    return {
                        "pid": str(proc_info["pid"]),
                        "name": proc_info["name"],
                        "path": proc_info.get("exe", "Unknown"),
                        "cmdline": " ".join(proc_info.get("cmdline", [])),
                    }

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

    except Exception as e:
        debug(f"Directory-based detection failed: {e}")

    # Method 4: Look for common file operation tools
    try:
        debug("Trying common tools detection")
        common_tools = [
            "cp",
            "mv",
            "rm",
            "mkdir",
            "rmdir",
            "touch",
            "nano",
            "vim",
            "gedit",
            "kate",
            "code",
            "subl",
        ]

        for proc in psutil.process_iter(["pid", "name", "exe", "cmdline"]):
            try:
                proc_info = proc.info
                proc_name = proc_info.get("name", "").lower()

                # Check if it's a common file operation tool
                if any(tool in proc_name for tool in common_tools):
                    cmdline = proc_info.get("cmdline", [])
                    if cmdline and (
                        filepath in " ".join(cmdline)
                        or os.path.dirname(filepath) in " ".join(cmdline)
                    ):
                        debug(f"Found common tool: {proc_info}")
                        return {
                            "pid": str(proc_info["pid"]),
                            "name": proc_info["name"],
                            "path": proc_info.get("exe", "Unknown"),
                            "cmdline": " ".join(cmdline),
                        }

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

    except Exception as e:
        debug(f"Common tools detection failed: {e}")

    debug("No process information found")
    return None


def get_file_info(filepath: str) -> Dict[str, str]:
    """
    Get detailed file information
    """
    info = {}
    try:
        stat = os.stat(filepath)
        info["size"] = f"{stat.st_size} bytes"
        info["permissions"] = oct(stat.st_mode)[-3:]
        info["modified"] = time.strftime(
            "%Y-%m-%d %H:%M:%S", time.localtime(stat.st_mtime)
        )
        info["accessed"] = time.strftime(
            "%Y-%m-%d %H:%M:%S", time.localtime(stat.st_atime)
        )

        # Get owner information
        try:
            import pwd

            info["owner"] = pwd.getpwuid(stat.st_uid).pw_name
        except ImportError:
            info["owner"] = str(stat.st_uid)

    except OSError:
        info["error"] = "Unable to read file info"

    return info


def clean_path(path: str) -> str:
    """Clean path, keep only filename"""
    return os.path.basename(path)


def color(text: str, color_code: int = 0) -> str:
    """Add color to debug info"""
    color_table = {
        0: "{}",  # No color
        1: "\033[1;30m{}\033[0m",  # Black bold
        2: "\033[1;31m{}\033[0m",  # Red bold
        3: "\033[1;32m{}\033[0m",  # Green bold
        4: "\033[1;33m{}\033[0m",  # Yellow bold
        5: "\033[1;34m{}\033[0m",  # Blue bold
        6: "\033[1;35m{}\033[0m",  # Purple bold
        7: "\033[1;36m{}\033[0m",  # Cyan bold
        8: "\033[1;37m{}\033[0m",  # White bold
    }
    return color_table[color_code].format(text)


def debug(*args, file: Optional[str] = None, append: bool = True, **kwargs) -> None:
    """
    Print the arguments with their file and line number
    ```python
    debug(
        'Hello',    # Parameter 1
        'World',    # Parameter 2
        file='debug.log',  # Output file path, default is None (output to console)
        append=False,  # Whether to append to file, default is True
        **kwargs  # Key-value parameters
    )

    return = None
    ```
    """
    if not DEBUG_MODE:
        return

    import inspect

    frame = inspect.currentframe().f_back
    filename = os.path.basename(frame.f_code.co_filename)
    line_number = frame.f_lineno

    message = f"[{filename}:{line_number}] " + " ".join(str(arg) for arg in args)

    if kwargs:
        message += " " + " ".join(f"{k}={v}" for k, v in kwargs.items())

    if file:
        mode = "a" if append else "w"
        try:
            with open(file, mode, encoding="utf-8") as f:
                f.write(message + "\n")
        except Exception as e:
            print(f"Debug file write error: {e}")
    else:
        print(color(message, 4))  # Yellow for debug


# CLI Style class
class CLIStyle:
    """CLI tool unified style config"""

    COLORS = {
        "TITLE": 7,  # Cyan - Main title
        "SUB_TITLE": 2,  # Red - Subtitle
        "CONTENT": 3,  # Green - Normal content
        "EXAMPLE": 7,  # Cyan - Example
        "WARNING": 4,  # Yellow - Warning
        "ERROR": 2,  # Red - Error
    }

    @staticmethod
    def color(text: str = "", color: int = COLORS["CONTENT"]) -> str:
        """Unified color processing function"""
        color_table = {
            0: "{}",  # No color
            1: "\033[1;30m{}\033[0m",  # Black bold
            2: "\033[1;31m{}\033[0m",  # Red bold
            3: "\033[1;32m{}\033[0m",  # Green bold
            4: "\033[1;33m{}\033[0m",  # Yellow bold
            5: "\033[1;34m{}\033[0m",  # Blue bold
            6: "\033[1;35m{}\033[0m",  # Purple bold
            7: "\033[1;36m{}\033[0m",  # Cyan bold
            8: "\033[1;37m{}\033[0m",  # White bold
        }
        return color_table[color].format(text)


# Custom argument parser for consistent CLI style
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

        if self.description:
            formatter.add_text(
                CLIStyle.color(self.description, CLIStyle.COLORS["TITLE"])
            )

        formatter.add_usage(self.usage, self._actions, self._mutually_exclusive_groups)

        formatter.add_text(CLIStyle.color("\nOptions:", CLIStyle.COLORS["TITLE"]))
        for action_group in self._action_groups:
            formatter.start_section(action_group.title)
            formatter.add_arguments(action_group._group_actions)
            formatter.end_section()

        if self.epilog:
            formatter.add_text(self.epilog)

        return formatter.format_help()


class PathEventHandler(FileSystemEventHandler):
    """Handle file system events"""

    def __init__(
        self,
        console: Console,
        watch_path: str,
        recursive: bool = False,
        verbose: bool = False,
    ):
        self.console = console
        self.watch_path = watch_path
        self.recursive = recursive
        self.verbose = verbose
        self.event_count = 0

    def on_created(self, event) -> None:
        """Handle file/directory creation"""
        self._handle_event(event, "CREATED", 3)  # Green

    def on_deleted(self, event) -> None:
        """Handle file/directory deletion"""
        self._handle_event(event, "DELETED", 2)  # Red

    def on_modified(self, event) -> None:
        """Handle file/directory modification"""
        if not event.is_directory:  # Only show file modifications to avoid spam
            self._handle_event(event, "MODIFIED", 4)  # Yellow

    def on_moved(self, event) -> None:
        """Handle file/directory move"""
        self._handle_event(event, "MOVED", 6)  # Purple

    def _handle_event(self, event, event_type: str, color_code: int) -> None:
        """Handle and display file system events"""
        try:
            current_time = time.strftime("%H:%M:%S")
            self.event_count += 1

            # Get relative path
            try:
                rel_path = os.path.relpath(event.src_path, self.watch_path)
            except ValueError:
                rel_path = event.src_path

            # Determine if it's a file or directory
            item_type = "DIR" if event.is_directory else "FILE"

            # Map color codes to Rich colors
            color_map = {
                2: "red",  # Red for DELETED
                3: "green",  # Green for CREATED
                4: "yellow",  # Yellow for MODIFIED
                5: "blue",  # Blue for MOVED
                6: "magenta",  # Magenta for MOVED
            }

            # Create Rich Text object for better color handling
            text = Text()

            # Time (yellow)
            text.append(f"[{current_time}] ", style="yellow")

            # Type (green)
            text.append(f"[{item_type}] ", style="green")

            # Event type with appropriate color
            rich_color = color_map.get(color_code, "cyan")
            text.append(f"[{event_type}] ", style=rich_color)

            # Path (green)
            text.append(rel_path, style="green")

            # Handle move events with destination
            if hasattr(event, "dest_path") and event.dest_path:
                try:
                    dest_rel_path = os.path.relpath(event.dest_path, self.watch_path)
                except ValueError:
                    dest_rel_path = event.dest_path
                text.append(f" -> {dest_rel_path}", style="green")

            self.console.print(text)

            # Get process information
            process_info = None
            if self.verbose:
                process_info = get_process_info_for_file(event.src_path, event_type)
                debug(f"Process info for {event.src_path}: {process_info}")

            # Display process information if available
            if process_info:
                proc_text = Text()
                proc_text.append("  └─ Process: ", style="cyan")
                proc_text.append(
                    f"PID={process_info.get('pid', 'Unknown')} ", style="magenta"
                )
                proc_text.append(
                    f"Name={process_info.get('name', 'Unknown')} ", style="magenta"
                )
                if process_info.get("path") and process_info["path"] != "Unknown":
                    proc_text.append(f"Path={process_info['path']}", style="magenta")
                self.console.print(proc_text)

                # Show command line if verbose and available
                if self.verbose and process_info.get("cmdline"):
                    cmd_text = Text()
                    cmd_text.append("    └─ Command: ", style="dim cyan")
                    cmd_text.append(process_info["cmdline"], style="dim white")
                    self.console.print(cmd_text)
            elif self.verbose:
                # Show that we tried to find process info but couldn't
                proc_text = Text()
                proc_text.append("  └─ Process: ", style="cyan")
                proc_text.append("No process information available", style="dim yellow")
                self.console.print(proc_text)

            # Display detailed file information if verbose
            if self.verbose and not event.is_directory:
                file_info = get_file_info(event.src_path)
                if "error" not in file_info:
                    info_text = Text()
                    info_text.append("  └─ Details: ", style="cyan")
                    details = []
                    if file_info.get("size"):
                        details.append(f"Size={file_info['size']}")
                    if file_info.get("permissions"):
                        details.append(f"Perm={file_info['permissions']}")
                    if file_info.get("owner"):
                        details.append(f"Owner={file_info['owner']}")
                    if file_info.get("modified"):
                        details.append(f"Modified={file_info['modified']}")
                    if details:
                        info_text.append(", ".join(details), style="dim white")
                        self.console.print(info_text)
                    else:
                        info_text.append(
                            "Unable to read file details", style="dim yellow"
                        )
                        self.console.print(info_text)
                else:
                    info_text = Text()
                    info_text.append("  └─ Details: ", style="cyan")
                    info_text.append("Unable to read file details", style="dim yellow")
                    self.console.print(info_text)

            debug(f"Event #{self.event_count}: {event_type} {rel_path}")

        except Exception as e:
            debug(f"Error handling event: {str(e)}")


class PathWatcher:
    """Main path watcher class"""

    def __init__(self, watch_path: str, recursive: bool = False, verbose: bool = False):
        self.watch_path = os.path.abspath(watch_path)
        self.recursive = recursive
        self.verbose = verbose
        self.observer = Observer()
        self.console = Console()
        self.is_watching = False

    def validate_path(self) -> bool:
        """Validate the watch path exists"""
        if not os.path.exists(self.watch_path):
            print(
                CLIStyle.color(
                    f"Error: Path does not exist: {self.watch_path}",
                    CLIStyle.COLORS["ERROR"],
                )
            )
            return False
        return True

    def _show_inotify_limit_help(self) -> None:
        """Display helpful information when inotify limit is reached"""
        self.console.print()
        self.console.print("🚨 File System Monitoring Error", style="bold red")
        self.console.print("=" * 50, style="red")

        self.console.print()
        self.console.print("🔧 Inotify Instance Limit Reached", style="bold red")
        self.console.print()
        self.console.print(
            "This error occurs when monitoring too many directories recursively. "
            "Linux limits the number of inotify instances per user."
        )

        self.console.print()
        self.console.print("📍 TEMPORARY SOLUTION:", style="bold yellow")
        self.console.print(
            "   sudo sysctl -w fs.inotify.max_user_instances=1024", style="green"
        )
        self.console.print("   (This change lasts until reboot)", style="yellow")

        self.console.print()
        self.console.print("📍 PERMANENT SOLUTION:", style="bold yellow")
        self.console.print(
            "   echo 'fs.inotify.max_user_instances=1024' | sudo tee -a /etc/sysctl.conf",
            style="green",
        )
        self.console.print(
            "   sudo sysctl -p  # Apply changes immediately", style="green"
        )
        self.console.print("   (This change persists after reboot)", style="yellow")

        self.console.print()
        self.console.print("💡 ALTERNATIVE SOLUTIONS:", style="bold cyan")
        self.console.print(
            "   • Monitor specific subdirectories instead of the entire tree",
            style="white",
        )
        self.console.print(
            "   • Use non-recursive monitoring: remove the -r flag", style="white"
        )
        self.console.print(
            "   • Check current limits: sysctl fs.inotify.max_user_instances",
            style="white",
        )

        # Current status
        self.console.print()
        self.console.print("📊 CURRENT SYSTEM STATUS:", style="bold magenta")
        try:
            import subprocess

            result = subprocess.run(
                ["sysctl", "fs.inotify.max_user_instances"],
                capture_output=True,
                text=True,
            )
            if result.returncode == 0:
                current_limit = result.stdout.strip().split("=")[1]
                self.console.print(f"   Current limit: {current_limit}", style="white")
            else:
                self.console.print("   Unable to check current limit", style="red")
        except Exception:
            self.console.print("   Unable to check current limit", style="red")

        self.console.print()

    def start_watching(self) -> None:
        """Start watching the path"""
        if not self.validate_path():
            return

        # Create event handler
        event_handler = PathEventHandler(
            self.console, self.watch_path, self.recursive, self.verbose
        )

        # Schedule the observer
        try:
            self.observer.schedule(
                event_handler, self.watch_path, recursive=self.recursive
            )
            self.observer.start()
        except OSError as e:
            if "inotify" in str(e).lower() and "instance limit" in str(e).lower():
                self._show_inotify_limit_help()
                return
            else:
                raise

        # Display watch information
        path_type = "directory" if os.path.isdir(self.watch_path) else "file"

        self.console.print()
        self.console.print("Path Watcher Started", style="bold cyan")
        self.console.print("-" * 30, style="cyan")
        self.console.print()
        self.console.print(f"Watching {path_type}: {self.watch_path}", style="green")
        self.console.print(f"Recursive: {str(self.recursive)}", style="green")
        self.console.print(f"Verbose: {str(self.verbose)}", style="green")
        self.console.print("Press Ctrl+C to stop watching", style="yellow")

        debug(
            f"Started watching: {self.watch_path}, recursive: {self.recursive}, verbose: {self.verbose}"
        )

        try:
            self.is_watching = True
            while self.is_watching:
                time.sleep(0.1)
        except KeyboardInterrupt:
            self.stop_watching()
        except Exception as e:
            error_msg = str(e).lower()
            if "inotify" in error_msg and "instance limit" in error_msg:
                self._show_inotify_limit_help()
            else:
                print(
                    CLIStyle.color(
                        f"Error during watching: {str(e)}", CLIStyle.COLORS["ERROR"]
                    )
                )
                debug(f"Watch error: {str(e)}")
            self.stop_watching()

    def stop_watching(self) -> None:
        """Stop watching the path"""
        self.is_watching = False
        if self.observer:
            self.observer.stop()
            self.observer.join()

        print(CLIStyle.color("\nStopped watching path", CLIStyle.COLORS["WARNING"]))
        debug("Stopped watching")


def create_example_text(
    script_name: str, examples: List[tuple], notes: Optional[List[str]] = None
) -> str:
    """Create unified example text"""
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


def main() -> int:
    """Main program logic"""
    script_name = os.path.basename(sys.argv[0])

    # Define examples and notes
    examples = [
        ("Watch a single file", "/path/to/file.txt"),
        ("Watch a directory", "/path/to/directory"),
        ("Watch directory recursively", "-r /path/to/directory"),
        ("Watch with verbose details", "-v /path/to/directory"),
        ("Watch with debug logging", "--log -r /tmp"),
        ("Full verbose monitoring", "-v -r --log /var/log"),
    ]

    notes = [
        "Monitor file system events including creation, deletion, modification, and moves",
        "Use -r for recursive monitoring of directories",
        "Use -v for verbose mode (shows process info and file details)",
        "Verbose mode automatically attempts to find related processes",
        "Press Ctrl+C to stop watching",
        "Use --log to enable debug logging for troubleshooting",
    ]

    parser = ColoredArgumentParser(
        description=CLIStyle.color(
            "Path Watcher - Monitor file system changes", CLIStyle.COLORS["TITLE"]
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=create_example_text(script_name, examples, notes),
    )

    # Add command line arguments
    parser.add_argument(
        "path",
        help=CLIStyle.color(
            "Path to watch (file or directory)", CLIStyle.COLORS["CONTENT"]
        ),
    )

    parser.add_argument(
        "-r",
        "--recursive",
        action="store_true",
        help=CLIStyle.color(
            "Recursively watch directories", CLIStyle.COLORS["CONTENT"]
        ),
    )

    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help=CLIStyle.color(
            "Enable verbose mode (show process info and file details)",
            CLIStyle.COLORS["CONTENT"],
        ),
    )

    parser.add_argument(
        "--log",
        action="store_true",
        help=CLIStyle.color("Enable debug logging", CLIStyle.COLORS["CONTENT"]),
    )

    # Parse arguments
    args = parser.parse_args()

    # Set global debug mode
    global DEBUG_MODE
    DEBUG_MODE = args.log

    debug(
        f"Arguments parsed: path={args.path}, recursive={args.recursive}, verbose={args.verbose}"
    )

    # Main application logic in try-except block
    try:
        # Validate path
        watch_path = args.path
        if not os.path.exists(watch_path):
            print(
                CLIStyle.color(
                    f"Error: Path does not exist: {watch_path}",
                    CLIStyle.COLORS["ERROR"],
                )
            )
            return 1

        # Create and start watcher
        watcher = PathWatcher(watch_path, args.recursive, args.verbose)
        watcher.start_watching()

        return 0

    except KeyboardInterrupt:
        print(
            CLIStyle.color("\nOperation cancelled by user", CLIStyle.COLORS["WARNING"])
        )
        return 0
    except Exception as e:
        if DEBUG_MODE:
            import traceback

            traceback.print_exc()
        print(CLIStyle.color(f"\nError: {str(e)}", CLIStyle.COLORS["ERROR"]))
        return 1


if __name__ == "__main__":
    sys.exit(main())
