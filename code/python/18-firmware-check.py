# -*- coding: utf-8 -*-
# pip install argparse
# refer thanks: https://github.com/craigz28/firmwalker.git

import os
import sys
import json
import subprocess
import threading
import time
from typing import List, Dict, Optional, Any
from pathlib import Path
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
import argparse

# Global debug level
DEBUG_MODE = False


# Utility functions
def clean_path(path: str) -> str:
    """Clean path, keep only filename"""
    return os.path.basename(path)


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
    filename = clean_path(frame.f_code.co_filename)
    line_number = frame.f_lineno

    debug_info = f"[{filename}:{line_number}]"
    message_parts = [str(arg) for arg in args]

    if kwargs:
        kwarg_parts = [f"{k}={v}" for k, v in kwargs.items()]
        message_parts.extend(kwarg_parts)

    full_message = f"{debug_info} {' '.join(message_parts)}"

    if file:
        mode = "a" if append else "w"
        with open(file, mode, encoding="utf-8") as f:
            f.write(f"{full_message}\n")
    else:
        print(CLIStyle.color(full_message, CLIStyle.COLORS["WARNING"]))


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


def create_example_text(script_name: str, examples: list, notes: list = None) -> str:
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


# Global loading animation control
is_scanning = False


def show_loading_animation() -> None:
    """Display loading animation"""
    animation = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    i = 0
    global is_scanning
    start_time = time.time()
    while is_scanning:
        elapsed = time.time() - start_time
        sys.stdout.write(
            f"\r{CLIStyle.color(f'{animation[i]} Scanning... ({elapsed:.1f}s)', CLIStyle.COLORS['WARNING'])}"
        )
        sys.stdout.flush()
        time.sleep(0.1)
        i = (i + 1) % len(animation)
    sys.stdout.write("\r" + " " * 50 + "\r")
    sys.stdout.flush()


def confirm_action(prompt: str, default: bool = False) -> bool:
    """Ask user for confirmation before proceeding with action"""
    suffix = " [Y/n]" if default else " [y/N]"
    response = (
        input(CLIStyle.color(f"{prompt}{suffix}: ", CLIStyle.COLORS["CONTENT"]))
        .strip()
        .lower()
    )

    if not response:
        return default

    return response[0] == "y"


def safe_write_file(filepath: str, content: str, overwrite: bool = False) -> bool:
    """Safely write content to file, with checks to prevent accidental overwrites"""
    if os.path.exists(filepath) and not overwrite:
        print(
            CLIStyle.color(
                f"Warning: File already exists: {filepath}", CLIStyle.COLORS["WARNING"]
            )
        )
        if not confirm_action("Overwrite?", default=False):
            return False

    try:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    except Exception as e:
        print(CLIStyle.color(f"Error writing file: {str(e)}", CLIStyle.COLORS["ERROR"]))
        return False


def normalize_path(path: str) -> str:
    """Normalize path for cross-platform compatibility"""
    abs_path = os.path.abspath(path)

    if sys.platform.startswith("win"):
        # Additional Windows-specific handling if needed
        pass

    return abs_path


@dataclass
class ScanResult:
    """Scanning result data structure"""

    category: str
    pattern: str
    file_path: str
    content: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class Scanner(ABC):
    """Abstract base class for security scanners"""

    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.results: List[ScanResult] = []

    @abstractmethod
    def scan(self, firmware_dir: Path) -> List[ScanResult]:
        """
        Execute scanning operation
        ```python
        scan(
            Path("/path/to/firmware")    # Firmware directory path
        )

        return = [ScanResult(...), ...]  # List of scan results
        ```
        """
        pass

    def get_results(self) -> List[ScanResult]:
        """
        Get scanning results
        ```python
        get_results()

        return = [ScanResult(...), ...]  # List of scan results
        ```
        """
        return self.results


class FilePatternScanner(Scanner):
    """File pattern scanner for searching specific filename patterns"""

    def __init__(self, name: str, patterns: List[str], description: str = ""):
        super().__init__(name, description)
        self.patterns = patterns
        debug("FilePatternScanner initialized", name=name, patterns_count=len(patterns))

    def scan(self, firmware_dir: Path) -> List[ScanResult]:
        """
        Scan files matching specified patterns
        ```python
        scan(
            Path("/path/to/firmware")    # Firmware directory path
        )

        return = [ScanResult(...), ...]  # List of matching files
        ```
        """
        self.results = []
        debug(
            "Starting file pattern scan", scanner=self.name, directory=str(firmware_dir)
        )

        for pattern in self.patterns:
            try:
                for file_path in firmware_dir.rglob(pattern):
                    if file_path.is_file():
                        relative_path = file_path.relative_to(firmware_dir)
                        result = ScanResult(
                            category=self.name,
                            pattern=pattern,
                            file_path=str(relative_path),
                        )
                        self.results.append(result)
                        debug("Found file", pattern=pattern, file=str(relative_path))
            except Exception as e:
                debug("Error scanning pattern", pattern=pattern, error=str(e))

        debug(
            "File pattern scan completed",
            scanner=self.name,
            results_count=len(self.results),
        )
        return self.results


class ContentPatternScanner(Scanner):
    """Content pattern scanner for searching specific patterns within file contents"""

    def __init__(self, name: str, patterns: List[str], description: str = ""):
        super().__init__(name, description)
        self.patterns = patterns
        debug(
            "ContentPatternScanner initialized", name=name, patterns_count=len(patterns)
        )

    def scan(self, firmware_dir: Path) -> List[ScanResult]:
        """
        Search for patterns within file contents
        ```python
        scan(
            Path("/path/to/firmware")    # Firmware directory path
        )

        return = [ScanResult(...), ...]  # List of files containing patterns
        ```
        """
        self.results = []
        debug(
            "Starting content pattern scan",
            scanner=self.name,
            directory=str(firmware_dir),
        )

        for pattern in self.patterns:
            try:
                cmd = ["grep", "-lsirnw", str(firmware_dir), "-e", pattern]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

                for file_path in result.stdout.strip().split("\n"):
                    if file_path and file_path != str(firmware_dir):
                        try:
                            relative_path = Path(file_path).relative_to(firmware_dir)
                            scan_result = ScanResult(
                                category=self.name,
                                pattern=pattern,
                                file_path=str(relative_path),
                            )
                            self.results.append(scan_result)
                            debug(
                                "Found content match",
                                pattern=pattern,
                                file=str(relative_path),
                            )
                        except ValueError:
                            # Skip files outside firmware directory
                            continue
            except (
                subprocess.TimeoutExpired,
                subprocess.SubprocessError,
                ValueError,
            ) as e:
                debug("Error searching pattern", pattern=pattern, error=str(e))

        debug(
            "Content pattern scan completed",
            scanner=self.name,
            results_count=len(self.results),
        )
        return self.results


class RegexScanner(Scanner):
    """Regex scanner for searching content using regular expressions"""

    def __init__(self, name: str, regex_patterns: List[str], description: str = ""):
        super().__init__(name, description)
        self.raw_patterns = regex_patterns
        debug("RegexScanner initialized", name=name, patterns_count=len(regex_patterns))

    def scan(self, firmware_dir: Path) -> List[ScanResult]:
        """
        Search content using regular expressions
        ```python
        scan(
            Path("/path/to/firmware")    # Firmware directory path
        )

        return = [ScanResult(...), ...]  # List of regex matches
        ```
        """
        self.results = []
        debug("Starting regex scan", scanner=self.name, directory=str(firmware_dir))

        for pattern in self.raw_patterns:
            try:
                cmd = [
                    "grep",
                    "-sRIEho",
                    pattern,
                    "--exclude-dir=dev",
                    str(firmware_dir),
                ]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

                matches = (
                    set(result.stdout.strip().split("\n"))
                    if result.stdout.strip()
                    else set()
                )
                for match in matches:
                    if match:
                        scan_result = ScanResult(
                            category=self.name,
                            pattern=pattern,
                            file_path="",
                            content=match,
                        )
                        self.results.append(scan_result)
                        debug("Found regex match", pattern=pattern, content=match[:50])
            except (subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
                debug("Error in regex search", pattern=pattern, error=str(e))

        debug(
            "Regex scan completed", scanner=self.name, results_count=len(self.results)
        )
        return self.results


class HashScanner(Scanner):
    """Hash scanner for detecting password hashes"""

    def __init__(self):
        super().__init__("Password Hashes", "Search for Unix-MD5 password hashes")
        debug("HashScanner initialized")

    def scan(self, firmware_dir: Path) -> List[ScanResult]:
        """
        Search for MD5 password hashes
        ```python
        scan(
            Path("/path/to/firmware")    # Firmware directory path
        )

        return = [ScanResult(...), ...]  # List of found hashes
        ```
        """
        self.results = []
        debug("Starting hash scan", directory=str(firmware_dir))

        try:
            cmd = ["grep", "-sRIEho", r"\$1\$\w{8}\S{23}", str(firmware_dir)]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

            hashes = (
                set(result.stdout.strip().split("\n"))
                if result.stdout.strip()
                else set()
            )
            for hash_value in hashes:
                if hash_value:
                    scan_result = ScanResult(
                        category=self.name,
                        pattern="Unix-MD5 Hash",
                        file_path="",
                        content=hash_value,
                    )
                    self.results.append(scan_result)
                    debug("Found hash", hash=hash_value[:20] + "...")
        except (subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
            debug("Error searching hashes", error=str(e))

        debug("Hash scan completed", results_count=len(self.results))
        return self.results


class SSLCertificateScanner(Scanner):
    """SSL certificate scanner with optional Shodan API integration"""

    def __init__(self, enable_shodan: bool = False):
        super().__init__("SSL Certificates", "Analyze SSL certificate files")
        self.enable_shodan = enable_shodan
        debug("SSLCertificateScanner initialized", enable_shodan=enable_shodan)

    def scan(self, firmware_dir: Path) -> List[ScanResult]:
        """
        Scan SSL certificates
        ```python
        scan(
            Path("/path/to/firmware")    # Firmware directory path
        )

        return = [ScanResult(...), ...]  # List of certificate analysis results
        ```
        """
        self.results = []
        debug("Starting SSL certificate scan", directory=str(firmware_dir))

        cert_patterns = ["*.pem", "*.crt", "*.cer"]
        for pattern in cert_patterns:
            for cert_file in firmware_dir.rglob(pattern):
                if cert_file.is_file():
                    try:
                        relative_path = cert_file.relative_to(firmware_dir)

                        cmd = [
                            "openssl",
                            "x509",
                            "-in",
                            str(cert_file),
                            "-serial",
                            "-noout",
                        ]
                        result = subprocess.run(
                            cmd, capture_output=True, text=True, timeout=30
                        )

                        if result.returncode == 0:
                            serial_no = result.stdout.strip()
                            scan_result = ScanResult(
                                category=self.name,
                                pattern=pattern,
                                file_path=str(relative_path),
                                metadata={"serial": serial_no},
                            )

                            if self.enable_shodan and serial_no:
                                try:
                                    shodan_result = self._query_shodan(serial_no)
                                    scan_result.metadata["shodan"] = shodan_result
                                except Exception as e:
                                    scan_result.metadata["shodan_error"] = str(e)

                            self.results.append(scan_result)
                            debug(
                                "Analyzed certificate",
                                file=str(relative_path),
                                serial=serial_no[:20],
                            )

                    except (subprocess.TimeoutExpired, subprocess.SubprocessError) as e:
                        debug(
                            "Error analyzing certificate",
                            file=str(cert_file),
                            error=str(e),
                        )

        debug("SSL certificate scan completed", results_count=len(self.results))
        return self.results

    def _query_shodan(self, serial_no: str) -> Dict[str, Any]:
        """
        Query Shodan API for certificate information
        ```python
        _query_shodan(
            "serial=ABC123..."    # Certificate serial number
        )

        return = {"count": 5, "query": "ssl.cert.serial:ABC123"}  # Shodan query results
        ```
        """
        try:
            serial_format = f"ssl.cert.serial:{serial_no.split('=')[-1]}"
            cmd = ["shodan", "count", serial_format]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)

            if result.returncode == 0:
                count = int(result.stdout.strip())
                debug("Shodan query successful", query=serial_format, count=count)
                return {"count": count, "query": serial_format}
            else:
                debug("Shodan query failed", error=result.stderr)
                return {"error": "Shodan query failed"}
        except Exception as e:
            debug("Shodan query error", error=str(e))
            return {"error": str(e)}


class DirectoryScanner(Scanner):
    """Directory scanner for listing important directory contents"""

    def __init__(self, directories: List[str]):
        super().__init__("Directory Listings", "List important directory contents")
        self.directories = directories
        debug("DirectoryScanner initialized", directories_count=len(directories))

    def scan(self, firmware_dir: Path) -> List[ScanResult]:
        """
        Scan specified directories
        ```python
        scan(
            Path("/path/to/firmware")    # Firmware directory path
        )

        return = [ScanResult(...), ...]  # List of directory contents
        ```
        """
        self.results = []
        debug("Starting directory scan", directory=str(firmware_dir))

        for dir_path in self.directories:
            target_dir = firmware_dir / dir_path
            if target_dir.exists() and target_dir.is_dir():
                try:
                    files = list(target_dir.iterdir())
                    file_list = [f.name for f in files]

                    scan_result = ScanResult(
                        category=self.name,
                        pattern=dir_path,
                        file_path=dir_path,
                        content=", ".join(file_list),
                        metadata={"file_count": len(files)},
                    )
                    self.results.append(scan_result)
                    debug("Scanned directory", path=dir_path, file_count=len(files))
                except PermissionError:
                    debug("Permission denied", directory=str(target_dir))

        debug("Directory scan completed", results_count=len(self.results))
        return self.results


class FirmwareSecurityScanner:
    """Main firmware security scanner class"""

    def __init__(
        self, firmware_dir: str, output_file: str = "firmware_scan_results.json"
    ):
        self.firmware_dir = Path(normalize_path(firmware_dir))
        self.output_file = output_file
        self.scanners: List[Scanner] = []
        self.all_results: List[ScanResult] = []

        if not self.firmware_dir.exists():
            raise FileNotFoundError(
                f"Firmware directory does not exist: {firmware_dir}"
            )

        debug(
            "FirmwareSecurityScanner initialized",
            firmware_dir=str(self.firmware_dir),
            output_file=output_file,
        )
        self._init_default_scanners()

    def _init_default_scanners(self) -> None:
        """
        Initialize default scanners
        ```python
        _init_default_scanners()

        return = None
        ```
        """
        debug("Initializing default scanners")

        # Password files scanner
        password_patterns = ["passwd", "shadow", "*.psk"]
        self.add_scanner(
            FilePatternScanner(
                "Password Files", password_patterns, "Search for password related files"
            )
        )

        # SSL files scanner
        ssl_patterns = ["*.crt", "*.pem", "*.cer", "*.p7b", "*.p12", "*.key"]
        self.add_scanner(
            FilePatternScanner(
                "SSL Files", ssl_patterns, "Search for SSL related files"
            )
        )

        # SSH files scanner
        ssh_patterns = ["*ssh*", "*rsa*", "*dsa*", "authorized_keys", "known_hosts"]
        self.add_scanner(
            FilePatternScanner(
                "SSH Files", ssh_patterns, "Search for SSH related files"
            )
        )

        # Configuration files scanner
        config_patterns = ["*.conf", "*.cfg", "*.ini", "*.xml"]
        self.add_scanner(
            FilePatternScanner(
                "Config Files", config_patterns, "Search for configuration files"
            )
        )

        # Database files scanner
        db_patterns = ["*.db", "*.sqlite", "*.sql"]
        self.add_scanner(
            FilePatternScanner(
                "Database Files", db_patterns, "Search for database files"
            )
        )

        # Script files scanner
        script_patterns = ["*.sh", "*.py", "*.pl", "*.php"]
        self.add_scanner(
            FilePatternScanner(
                "Script Files", script_patterns, "Search for script files"
            )
        )

        # Binary files scanner
        binary_patterns = ["*.bin"]
        self.add_scanner(
            FilePatternScanner("Binary Files", binary_patterns, "Search for .bin files")
        )

        # Important binaries scanner
        important_binaries = [
            "ssh",
            "sshd",
            "scp",
            "sftp",
            "tftp",
            "dropbear",
            "busybox",
            "telnet",
            "telnetd",
            "openssl",
        ]
        self.add_scanner(
            FilePatternScanner(
                "Important Binaries",
                important_binaries,
                "Search for important binary programs",
            )
        )

        # Web servers scanner
        webserver_patterns = ["httpd", "nginx", "apache", "lighttpd", "thttpd"]
        self.add_scanner(
            FilePatternScanner(
                "Web Servers", webserver_patterns, "Search for web servers"
            )
        )

        # Sensitive keywords scanner
        sensitive_patterns = [
            "upgrade",
            "admin",
            "root",
            "password",
            "passwd",
            "pwd",
            "dropbear",
            "ssl",
            "private key",
            "telnet",
            "secret",
            "pgp",
            "gpg",
            "token",
            "api key",
            "oauth",
        ]
        self.add_scanner(
            ContentPatternScanner(
                "Sensitive Keywords",
                sensitive_patterns,
                "Search for sensitive keywords in files",
            )
        )

        # IP addresses scanner
        ip_regex = [
            r"\b(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b"
        ]
        self.add_scanner(
            RegexScanner("IP Addresses", ip_regex, "Search for IP addresses")
        )

        # URLs scanner
        url_regex = [r'(http|https)://[^/"]+']
        self.add_scanner(RegexScanner("URLs", url_regex, "Search for URLs"))

        # Email addresses scanner
        email_regex = [r"([[:alnum:]_.-]+@[[:alnum:]_.-]+?\.[[:alpha:].]{2,6})"]
        self.add_scanner(
            RegexScanner("Email Addresses", email_regex, "Search for email addresses")
        )

        # Password hashes scanner
        self.add_scanner(HashScanner())

        # SSL certificates scanner
        self.add_scanner(SSLCertificateScanner())

        # Directory scanner
        important_dirs = ["etc/ssl", "etc", "var", "tmp"]
        self.add_scanner(DirectoryScanner(important_dirs))

        debug("Default scanners initialized", scanner_count=len(self.scanners))

    def add_scanner(self, scanner: Scanner) -> None:
        """
        Add a scanner to the scanner list
        ```python
        add_scanner(
            Scanner()    # Scanner instance
        )

        return = None
        ```
        """
        self.scanners.append(scanner)
        debug("Scanner added", scanner_name=scanner.name)

    def remove_scanner(self, scanner_name: str) -> None:
        """
        Remove a scanner by name
        ```python
        remove_scanner(
            "Scanner Name"    # Name of scanner to remove
        )

        return = None
        ```
        """
        initial_count = len(self.scanners)
        self.scanners = [s for s in self.scanners if s.name != scanner_name]
        removed_count = initial_count - len(self.scanners)
        debug("Scanner removed", scanner_name=scanner_name, removed_count=removed_count)

    def run_scan(self) -> Dict[str, Any]:
        """
        Run all scanners and generate report
        ```python
        run_scan()

        return = {
            "scan_info": {...},      # Scan metadata
            "scanner_summary": {...}, # Scanner summaries
            "results": [...]         # Detailed results
        }
        ```
        """
        print(
            CLIStyle.color(
                f"Starting firmware security scan: {self.firmware_dir}",
                CLIStyle.COLORS["TITLE"],
            )
        )
        print(
            CLIStyle.color(
                f"Scanner count: {len(self.scanners)}", CLIStyle.COLORS["CONTENT"]
            )
        )

        scan_start_time = datetime.now()
        self.all_results = []

        # Start loading animation
        global is_scanning
        is_scanning = True
        loading_thread = threading.Thread(target=show_loading_animation)
        loading_thread.daemon = True
        loading_thread.start()

        try:
            for scanner in self.scanners:
                debug("Running scanner", scanner_name=scanner.name)
                try:
                    results = scanner.scan(self.firmware_dir)
                    self.all_results.extend(results)
                    debug(
                        "Scanner completed",
                        scanner_name=scanner.name,
                        results_count=len(results),
                    )
                except Exception as e:
                    debug("Scanner error", scanner_name=scanner.name, error=str(e))
                    print(
                        CLIStyle.color(
                            f"Error in scanner '{scanner.name}': {str(e)}",
                            CLIStyle.COLORS["ERROR"],
                        )
                    )
        finally:
            # Stop animation
            is_scanning = False
            loading_thread.join()

        scan_end_time = datetime.now()
        scan_duration = (scan_end_time - scan_start_time).total_seconds()

        # Generate report
        report = {
            "scan_info": {
                "firmware_directory": str(self.firmware_dir),
                "scan_start_time": scan_start_time.isoformat(),
                "scan_end_time": scan_end_time.isoformat(),
                "scan_duration_seconds": scan_duration,
                "total_scanners": len(self.scanners),
                "total_results": len(self.all_results),
            },
            "scanner_summary": {},
            "results": [],
        }

        # Group results by scanner
        for scanner in self.scanners:
            scanner_results = [
                r for r in self.all_results if r.category == scanner.name
            ]
            report["scanner_summary"][scanner.name] = {
                "description": scanner.description,
                "result_count": len(scanner_results),
            }

        # Add detailed results
        for result in self.all_results:
            report["results"].append(
                {
                    "category": result.category,
                    "pattern": result.pattern,
                    "file_path": result.file_path,
                    "content": result.content,
                    "metadata": result.metadata,
                }
            )

        debug(
            "Scan completed",
            duration=scan_duration,
            total_results=len(self.all_results),
        )
        return report

    def save_report(self, report: Dict[str, Any], format_type: str = "json") -> bool:
        """
        Save scan report to file
        ```python
        save_report(
            {"scan_info": ...},    # Report data
            "json"                # Format type: "json" or "text"
        )

        return = True  # Success status
        ```
        """
        try:
            if format_type == "json":
                content = json.dumps(report, ensure_ascii=False, indent=2)
                if safe_write_file(self.output_file, content, overwrite=True):
                    print(
                        CLIStyle.color(
                            f"Report saved to: {self.output_file}",
                            CLIStyle.COLORS["CONTENT"],
                        )
                    )
                    debug("JSON report saved", file=self.output_file)
                    return True
            elif format_type == "text":
                text_file = self.output_file.replace(".json", ".txt")
                content = self._generate_text_report(report)
                if safe_write_file(text_file, content, overwrite=True):
                    print(
                        CLIStyle.color(
                            f"Report saved to: {text_file}", CLIStyle.COLORS["CONTENT"]
                        )
                    )
                    debug("Text report saved", file=text_file)
                    return True
            return False
        except Exception as e:
            print(
                CLIStyle.color(
                    f"Error saving report: {str(e)}", CLIStyle.COLORS["ERROR"]
                )
            )
            debug("Error saving report", error=str(e))
            return False

    def _generate_text_report(self, report: Dict[str, Any]) -> str:
        """
        Generate text format report
        ```python
        _generate_text_report(
            {"scan_info": ...}    # Report data
        )

        return = "text report content"  # Formatted text report
        ```
        """
        lines = []
        lines.append("=== Firmware Security Scan Report ===\n")
        lines.append(f"Scan Directory: {report['scan_info']['firmware_directory']}")
        lines.append(f"Scan Time: {report['scan_info']['scan_start_time']}")
        lines.append(
            f"Scan Duration: {report['scan_info']['scan_duration_seconds']:.2f} seconds"
        )
        lines.append(f"Total Results: {report['scan_info']['total_results']}\n")

        for category, summary in report["scanner_summary"].items():
            lines.append(f"=== {category} ({summary['result_count']} results) ===")
            category_results = [
                r for r in report["results"] if r["category"] == category
            ]
            for result in category_results:
                lines.append(f"Pattern: {result['pattern']}")
                if result["file_path"]:
                    lines.append(f"File: {result['file_path']}")
                if result["content"]:
                    lines.append(f"Content: {result['content']}")
                if result["metadata"]:
                    lines.append(f"Metadata: {result['metadata']}")
                lines.append("-" * 50)
            lines.append("")

        return "\n".join(lines)

    def get_summary(self) -> Dict[str, int]:
        """
        Get scan results summary
        ```python
        get_summary()

        return = {"Scanner Name": 5, ...}  # Results count by category
        ```
        """
        summary = {}
        for result in self.all_results:
            category = result.category
            summary[category] = summary.get(category, 0) + 1
        debug(
            "Summary generated",
            categories=len(summary),
            total_results=len(self.all_results),
        )
        return summary


def main() -> int:
    """Main program logic"""
    script_name = os.path.basename(sys.argv[0])

    examples = [
        ("Basic firmware scan", "/path/to/firmware/rootfs"),
        ("Specify output file", "/path/to/firmware/rootfs -o my_scan.json"),
        ("Output text format", "/path/to/firmware/rootfs -f text"),
        ("Enable Shodan queries", "/path/to/firmware/rootfs --enable-shodan"),
        ("Debug mode", "/path/to/firmware/rootfs --log"),
    ]

    notes = [
        "Requires standard Unix tools: grep, find, openssl",
        "Shodan queries require shodan CLI to be installed and configured",
        "Use --log to enable debug mode for troubleshooting",
        "Large firmware images may take several minutes to scan",
    ]

    parser = ColoredArgumentParser(
        description=CLIStyle.color(
            "iot firmware scanner",
            CLIStyle.COLORS["TITLE"],
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=create_example_text(script_name, examples, notes),
    )

    parser.add_argument(
        "firmware_dir",
        help=CLIStyle.color(
            "Path to firmware root filesystem", CLIStyle.COLORS["CONTENT"]
        ),
    )
    parser.add_argument(
        "-o",
        "--output",
        default="firmware_scan_results.json",
        metavar=CLIStyle.color("FILE", CLIStyle.COLORS["WARNING"]),
        help=CLIStyle.color(
            "Output filename (default: firmware_scan_results.json)",
            CLIStyle.COLORS["CONTENT"],
        ),
    )
    parser.add_argument(
        "-f",
        "--format",
        choices=["json", "text"],
        default="json",
        metavar=CLIStyle.color("FORMAT", CLIStyle.COLORS["WARNING"]),
        help=CLIStyle.color(
            "Output format (default: json)", CLIStyle.COLORS["CONTENT"]
        ),
    )
    parser.add_argument(
        "--enable-shodan",
        action="store_true",
        help=CLIStyle.color(
            "Enable Shodan API queries (requires shodan CLI)",
            CLIStyle.COLORS["CONTENT"],
        ),
    )
    parser.add_argument(
        "--log",
        action="store_true",
        help=CLIStyle.color("Enable debug logging", CLIStyle.COLORS["CONTENT"]),
    )

    args = parser.parse_args()

    global DEBUG_MODE
    DEBUG_MODE = args.log

    try:
        debug(
            "Starting firmware security scanner",
            firmware_dir=args.firmware_dir,
            output=args.output,
            format=args.format,
        )

        scanner = FirmwareSecurityScanner(args.firmware_dir, args.output)

        if args.enable_shodan:
            scanner.remove_scanner("SSL Certificates")
            scanner.add_scanner(SSLCertificateScanner(enable_shodan=True))
            debug("Shodan integration enabled")

        report = scanner.run_scan()

        if not scanner.save_report(report, args.format):
            return 1

        summary = scanner.get_summary()
        print(CLIStyle.color("\n=== Scan Complete ===", CLIStyle.COLORS["TITLE"]))
        print(
            CLIStyle.color(
                f"Total items found: {len(scanner.all_results)}",
                CLIStyle.COLORS["CONTENT"],
            )
        )
        print(CLIStyle.color("\nResults by category:", CLIStyle.COLORS["SUB_TITLE"]))
        for category, count in summary.items():
            print(CLIStyle.color(f"  {category}: {count}", CLIStyle.COLORS["CONTENT"]))

        debug("Main function completed successfully")
        return 0

    except FileNotFoundError as e:
        print(CLIStyle.color(f"Error: {str(e)}", CLIStyle.COLORS["ERROR"]))
        debug("File not found error", error=str(e))
        return 1
    except PermissionError as e:
        print(
            CLIStyle.color(
                f"Error: Permission denied - {str(e)}", CLIStyle.COLORS["ERROR"]
            )
        )
        debug("Permission error", error=str(e))
        return 1
    except KeyboardInterrupt:
        print(
            CLIStyle.color("\nOperation cancelled by user", CLIStyle.COLORS["WARNING"])
        )
        debug("Operation cancelled by user")
        return 0
    except Exception as e:
        if DEBUG_MODE:
            import traceback

            traceback.print_exc()
        print(CLIStyle.color(f"Error: {str(e)}", CLIStyle.COLORS["ERROR"]))
        debug("Unexpected error", error=str(e))
        return 1


if __name__ == "__main__":
    sys.exit(main())
