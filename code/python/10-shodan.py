# -*- coding: utf-8 -*-
# pip install shodan rich mmh3 requests beautifulsoup4 colorama

import argparse
import base64
import hashlib
import inspect
import json
import os
import re
import sys
import tempfile
import threading
import time
import traceback
import urllib.parse
from dataclasses import dataclass
from datetime import datetime, timezone
from getpass import getpass
from pathlib import Path
from typing import Any, TextIO

import mmh3
import requests
import shodan

try:
    from bs4 import BeautifulSoup
except ImportError:
    BeautifulSoup = None
from rich import box
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

if sys.platform == "win32":
    from colorama import init as colorama_init

    colorama_init(autoreset=True)

DEBUG_MODE = False
MAX_FAVICON_SIZE = 2 * 1024 * 1024
RAW_FIELD_ORDER = (
    "index",
    "ip",
    "port",
    "hostnames",
    "product",
    "version",
    "transport",
    "organization",
    "city",
    "country",
    "last_seen",
)


def clean_path(path: str) -> str:
    """Return only the filename component of a path."""
    return os.path.basename(path)


def color(text: Any, color_code: int = 0) -> str:
    """Apply a terminal color to debug text."""
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


def debug(
    *args: Any,
    file: str | os.PathLike[str] | None = None,
    append: bool = True,
    **kwargs: Any,
) -> None:
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

    frame = inspect.currentframe()
    caller = frame.f_back if frame else None
    info = inspect.getframeinfo(caller) if caller else None
    if info is None:
        return

    output = f"{color(clean_path(info.filename), 3)}: {color(info.lineno, 4)} {color('|', 7)} "

    for i, arg in enumerate(args):
        arg_str = str(arg)
        output += f"{color(arg_str, 2)} "

    for k, v in kwargs.items():
        output += f"{color(k + '=', 6)}{color(str(v), 2)} "

    output += "\n"

    if file:
        mode = "a" if append else "w"
        with open(file, mode, encoding="utf-8") as f:
            clean_output = re.sub(r"\033\[\d+;\d+m|\033\[0m", "", output)
            f.write(clean_output)
    else:
        print(output, end="", file=sys.stderr)


# CLI help style template
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


class ColoredArgumentParser(argparse.ArgumentParser):
    """Unified command line argument parser"""

    def _format_action_invocation(self, action: argparse.Action) -> str:
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

    def format_help(self) -> str:
        formatter = self._get_formatter()

        # Add description
        if self.description:
            formatter.add_text(
                CLIStyle.color(self.description, CLIStyle.COLORS["TITLE"])
            )

        # Add usage
        formatter.add_usage(self.usage, self._actions, self._mutually_exclusive_groups)

        # Add parameter groups
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


def create_example_text(
    script_name: str,
    examples: list[tuple[str, str]],
    notes: list[str] | None = None,
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


@dataclass(frozen=True)
class AppPaths:
    """Filesystem locations used by the tool."""

    root: Path

    @classmethod
    def default(cls: type["AppPaths"]) -> "AppPaths":
        """Return the default per-user storage locations."""
        return cls(Path.home() / ".shodan")

    @property
    def config_file(self) -> Path:
        """Return the custom configuration path."""
        return self.root / "config.json"

    @property
    def result_dir(self) -> Path:
        """Return the search result cache directory."""
        return self.root / "result"

    @property
    def index_file(self) -> Path:
        """Return the search index path."""
        return self.root / "search-result.json"

    @property
    def shodan_cli_config(self) -> Path:
        """Return the Shodan CLI API key path."""
        return Path.home() / ".config" / "shodan" / "api_key"


def show_loading_animation(stop_event: threading.Event, stream: TextIO) -> None:
    """Display a cancellable loading animation on the status stream."""
    animation = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    i = 0
    start_time = time.time()
    while not stop_event.is_set():
        elapsed = time.time() - start_time
        stream.write(
            f"\r{CLIStyle.color(f'{animation[i]} Pending... ({elapsed:.1f}s)', 6)}"
        )
        stream.flush()
        stop_event.wait(0.1)
        i = (i + 1) % len(animation)
    stream.write("\r" + " " * 50 + "\r")
    stream.flush()


def truncate(text: str, width: int) -> str:
    """Truncate text and add an ellipsis when it exceeds the width."""
    if width <= 3:
        return text[:width]
    if len(text) > width:
        return text[: width - 3] + "..."
    return text


class ShodanClient:
    def __init__(
        self,
        paths: AppPaths | None = None,
        quiet: bool = False,
    ) -> None:
        self.paths = paths or AppPaths.default()
        self.quiet = quiet
        self.api_key: str | None = None
        self.client: shodan.Shodan | None = None
        self.is_paid = False
        self._config_loaded = False
        self.last_search_page = 1

    def _emit(self, message: str = "", color_code: int = 0, *, end: str = "\n") -> None:
        """Write status text without contaminating machine-readable output."""
        stream = sys.stderr if self.quiet else sys.stdout
        print(CLIStyle.color(message, color_code), end=end, file=stream)

    def _write_json_atomic(self, path: Path, data: dict[str, Any]) -> None:
        """Write JSON through a same-directory temporary file and replace."""
        path.parent.mkdir(parents=True, exist_ok=True)
        file_descriptor, temporary_name = tempfile.mkstemp(
            prefix=f".{path.name}.",
            suffix=".tmp",
            dir=path.parent,
        )
        temporary_path = Path(temporary_name)
        try:
            with os.fdopen(file_descriptor, "w", encoding="utf-8") as output_file:
                json.dump(data, output_file, indent=2, ensure_ascii=False)
                output_file.write("\n")
            os.chmod(temporary_path, 0o600)
            os.replace(temporary_path, path)
        finally:
            temporary_path.unlink(missing_ok=True)

    def _ensure_loaded(self) -> None:
        """Load credentials only when a Shodan operation needs them."""
        if not self._config_loaded:
            self.load_config()

    def load_config(self) -> None:
        """Load the custom config, then fall back to the Shodan CLI config."""
        self._config_loaded = True

        if self.paths.config_file.is_file():
            try:
                with self.paths.config_file.open("r", encoding="utf-8") as config_file:
                    config = json.load(config_file)
                if isinstance(config, dict):
                    api_key = config.get("api_key")
                    if isinstance(api_key, str) and api_key.strip():
                        self.api_key = api_key.strip()
                        self.is_paid = bool(config.get("is_paid", False))
                        self.client = shodan.Shodan(self.api_key)
                        return
            except (OSError, json.JSONDecodeError) as error:
                self._emit(f"Error loading config: {error}", CLIStyle.COLORS["ERROR"])

        environment_key = os.environ.get("SHODAN_API_KEY", "").strip()
        if environment_key:
            self.api_key = environment_key
            self.client = shodan.Shodan(environment_key)
            return

        if not self.paths.shodan_cli_config.is_file():
            return

        try:
            api_key = self.paths.shodan_cli_config.read_text(encoding="utf-8").strip()
            if not api_key:
                return
            self.api_key = api_key
            self.client = shodan.Shodan(api_key)
            self._emit("Using API key from Shodan CLI config", CLIStyle.COLORS["TITLE"])
        except OSError as error:
            self._emit(
                f"Error loading Shodan CLI config: {error}",
                CLIStyle.COLORS["ERROR"],
            )

    def sync_from_cli_config(self) -> None:
        """Validate a CLI credential and save its plan metadata locally."""
        if not self.client or not self.api_key:
            return
        try:
            info = self.client.info()
            is_paid = self._is_paid_plan(info)
            config = {
                "api_key": self.api_key,
                "is_paid": is_paid,
                "plan": info.get("plan", "unknown"),
            }
            self._write_json_atomic(self.paths.config_file, config)
            self._emit(
                f"Synced API key to: {self.paths.config_file}",
                CLIStyle.COLORS["TITLE"],
            )
            self.is_paid = is_paid
            self._emit(
                f"Plan type: {info.get('plan', 'unknown')} ({'Paid' if is_paid else 'Free'})",
                CLIStyle.COLORS["TITLE"],
            )
        except Exception as error:
            self._emit(f"Error syncing config: {error}", CLIStyle.COLORS["ERROR"])

    @staticmethod
    def _is_paid_plan(info: dict[str, Any]) -> bool:
        """Return whether Shodan reports an unlocked non-dev plan."""
        return str(info.get("plan", "")).lower() != "dev" and bool(
            info.get("unlocked", False)
        )

    def _refresh_plan(self) -> bool:
        """Refresh plan metadata only when pagination needs it."""
        if not self.client:
            return False
        try:
            info = self.client.info()
            self.is_paid = self._is_paid_plan(info)
        except Exception as error:
            debug("Plan lookup failed", error=str(error))
            self._emit(
                f"Warning: Could not determine API plan: {error}",
                CLIStyle.COLORS["WARNING"],
            )
        return self.is_paid

    def init_api_key(self, api_key: str) -> bool:
        """Validate and persist an API key."""
        api_key = api_key.strip()
        if not api_key.strip():
            self._emit("Error: API key cannot be empty", CLIStyle.COLORS["ERROR"])
            return False
        try:
            test_client = shodan.Shodan(api_key)
            info = test_client.info()
            is_paid = self._is_paid_plan(info)
            config = {
                "api_key": api_key,
                "is_paid": is_paid,
                "plan": info.get("plan", "unknown"),
            }
            self._write_json_atomic(self.paths.config_file, config)

            self._emit("API key successfully initialized!", CLIStyle.COLORS["CONTENT"])
            self._emit(
                f"Config saved to: {self.paths.config_file}",
                CLIStyle.COLORS["TITLE"],
            )
            self._emit(
                f"Plan type: {info.get('plan', 'unknown')} ({'Paid' if is_paid else 'Free'})",
                CLIStyle.COLORS["TITLE"],
            )
            self.api_key = api_key.strip()
            self.client = test_client
            self.is_paid = is_paid  # Update instance attribute
            self._config_loaded = True
            return True
        except Exception as error:
            self._emit("Error initializing API key:", CLIStyle.COLORS["ERROR"])
            self._emit(str(error), CLIStyle.COLORS["ERROR"])
            return False

    def _get_cache_filename(
        self,
        query: str,
        page: int = 1,
        ipv4_only: bool = False,
    ) -> Path:
        """Generate a stable cache filename from the query and page."""
        cache_key = json.dumps(
            {
                "ipv4_only": ipv4_only,
                "page": page,
                "query": " ".join(query.split()),
                "version": 2,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
        query_hash = hashlib.sha256(cache_key.encode("utf-8")).hexdigest()[:16]
        return self.paths.result_dir / f"result_{query_hash}.json"

    def _update_search_index(
        self,
        query: str,
        cache_file: Path,
        results: dict[str, Any],
        page: int = 1,
        ipv4_only: bool = False,
    ) -> None:
        """Update the cache index and remove entries for deleted cache files."""
        index_file = self.paths.index_file
        try:
            index_data: dict[str, Any] = {}
            if index_file.is_file():
                with index_file.open("r", encoding="utf-8") as index_handle:
                    loaded_index = json.load(index_handle)
                if isinstance(loaded_index, dict):
                    index_data = loaded_index

            searches = index_data.get("searches", [])
            if not isinstance(searches, list):
                searches = []
            index_data["searches"] = [
                search
                for search in searches
                if isinstance(search, dict)
                and (
                    self.paths.result_dir
                    / Path(str(search.get("result_file", ""))).name
                ).is_file()
            ]

            search_key = f"{query}_page{page}_ipv4={ipv4_only}"
            for search in index_data["searches"]:
                if search.get("search_key") == search_key:
                    now = datetime.now(timezone.utc).isoformat()
                    search.update(
                        {
                            "last_updated": now,
                            "total_results": results.get("total", 0),
                            "matches_count": len(results.get("matches", [])),
                        }
                    )
                    break
            else:
                now = datetime.now(timezone.utc).isoformat()
                search_record = {
                    "query": query,
                    "search_key": search_key,
                    "page": page,
                    "created_at": now,
                    "last_updated": now,
                    "result_file": cache_file.name,
                    "total_results": results.get("total", 0),
                    "matches_count": len(results.get("matches", [])),
                }
                index_data["searches"].insert(0, search_record)

            self._write_json_atomic(index_file, index_data)
        except (OSError, json.JSONDecodeError, TypeError) as error:
            self._emit(
                f"Warning: Failed to update search index: {error}",
                CLIStyle.COLORS["WARNING"],
            )

    def _fetch_with_spinner(
        self,
        query: str,
        page: int,
        ipv4_only: bool = False,
    ) -> dict[str, Any] | None:
        """Fetch one page while keeping the spinner isolated from output."""
        stop_event = threading.Event()
        loading_thread = threading.Thread(
            target=show_loading_animation,
            args=(stop_event, sys.stderr),
            daemon=True,
        )
        loading_thread.start()
        try:
            return self._do_search(query, page, ipv4_only)
        finally:
            stop_event.set()
            loading_thread.join()

    def _save_cache(
        self,
        query: str,
        cache_file: Path,
        results: dict[str, Any],
        page: int,
        ipv4_only: bool,
    ) -> None:
        """Persist results and update the search index."""
        try:
            self._write_json_atomic(cache_file, results)
            self._update_search_index(query, cache_file, results, page, ipv4_only)
        except (OSError, TypeError) as error:
            self._emit(f"Error saving cache: {error}", CLIStyle.COLORS["ERROR"])

    def search(
        self,
        query: str,
        page: int = 1,
        no_cache: bool = False,
        delete_cache: bool = False,
        ipv4_only: bool = False,
    ) -> dict[str, Any] | None:
        """Execute a search, using a validated local cache when allowed."""
        self._ensure_loaded()
        if not self.client:
            debug("API key not configured")
            self._emit(
                "Error: API key not configured. Use 'init' command first.",
                CLIStyle.COLORS["ERROR"],
            )
            return None
        if page < 1:
            self._emit("Error: page must be at least 1", CLIStyle.COLORS["ERROR"])
            return None

        if page > 1 and not self.is_paid:
            self._refresh_plan()
        if page > 1 and not self.is_paid:
            debug("Free API pagination limit", page=page, is_paid=self.is_paid)
            self._emit(
                "Warning: Free API can only access the first page of results (max 100)",
                CLIStyle.COLORS["WARNING"],
            )
            page = 1
        self.last_search_page = page

        cache_file = self._get_cache_filename(query, page, ipv4_only)
        debug("Cache file", cache_file=cache_file)

        if delete_cache and cache_file.exists():
            try:
                cache_file.unlink()
                self._emit("Deleted existing cache.", CLIStyle.COLORS["TITLE"])
            except OSError as error:
                self._emit(f"Error deleting cache: {error}", CLIStyle.COLORS["ERROR"])

        need_new_search = no_cache or delete_cache or not cache_file.is_file()
        results: dict[str, Any] | None = None

        if need_new_search:
            offset = (page - 1) * 100
            self._emit(f"Searching with query: {query}, page: {page}, offset: {offset}")
            results = self._fetch_with_spinner(query, page, ipv4_only)
            if results and not no_cache:
                self._save_cache(query, cache_file, results, page, ipv4_only)
        else:
            try:
                with cache_file.open("r", encoding="utf-8") as cache_handle:
                    loaded_results = json.load(cache_handle)
                if isinstance(loaded_results, dict):
                    results = loaded_results
                    debug("Loaded from cache", cache_file=cache_file)
                    self._emit("Using cached results...", CLIStyle.COLORS["TITLE"])
                else:
                    raise ValueError("cache root must be an object")
            except (OSError, json.JSONDecodeError, ValueError) as error:
                debug("Cache read error", error=str(error))
                self._emit(f"Error reading cache: {error}", CLIStyle.COLORS["ERROR"])
                results = self._fetch_with_spinner(query, page, ipv4_only)
                if results and not no_cache:
                    self._save_cache(query, cache_file, results, page, ipv4_only)

        if not isinstance(results, dict):
            debug("Invalid results format", results=results)
            self._emit(
                "Search returned invalid result format",
                CLIStyle.COLORS["ERROR"],
            )
            return None

        matches = results.get("matches", [])
        if not isinstance(matches, list):
            debug("Invalid matches format", matches=matches)
            self._emit(
                "Search returned invalid matches format",
                CLIStyle.COLORS["ERROR"],
            )
            return None

        if not isinstance(results.get("total"), (int, float)):
            results["total"] = len(matches)
        return results

    def _do_search(
        self,
        query: str,
        page: int = 1,
        ipv4_only: bool = False,
    ) -> dict[str, Any] | None:
        """Execute one Shodan API search and preserve the API total."""
        if not self.client:
            return None
        try:
            debug("Executing Shodan API search", query=query, page=page)
            response = self.client.search(query, page=page)
            if not isinstance(response, dict) or not isinstance(
                response.get("matches"), list
            ):
                debug("Invalid response", response=response)
                self._emit(
                    "No results found or invalid response",
                    CLIStyle.COLORS["ERROR"],
                )
                return None

            raw_matches = response["matches"]
            valid_matches = [match for match in raw_matches if isinstance(match, dict)]
            if ipv4_only:
                valid_matches = [
                    match
                    for match in valid_matches
                    if ":" not in str(match.get("ip_str", ""))
                ]
            response["matches"] = valid_matches
            if not isinstance(response.get("total"), (int, float)):
                response["total"] = len(raw_matches)
            debug(
                "Search results",
                api_total=response.get("total"),
                matches_count=len(valid_matches),
                ipv4_only=ipv4_only,
            )
            self._emit(
                f"Got {len(valid_matches)} results",
                CLIStyle.COLORS["TITLE"],
            )
            return response
        except shodan.APIError as error:
            debug("Shodan API error", error=str(error))
            if "Search cursor timed out" in str(error):
                self._emit("Error: Search cursor timed out.", CLIStyle.COLORS["ERROR"])
                self._emit(
                    "Try page 1 or a lower page number.",
                    CLIStyle.COLORS["WARNING"],
                )
            else:
                self._emit(f"Search error: {error}", CLIStyle.COLORS["ERROR"])
            return None
        except Exception as error:
            debug("Search execution error", error=str(error))
            self._emit(f"Search error: {error}", CLIStyle.COLORS["ERROR"])
            return None

    def show_info(self) -> bool:
        """Display Shodan API information and local configuration."""
        self._ensure_loaded()
        if not self.client:
            self._emit(
                "Error: API key not configured. Use 'init' command first.",
                CLIStyle.COLORS["ERROR"],
            )
            return False

        try:
            info = self.client.info()
            if not isinstance(info, dict) or not info:
                self._emit(
                    "Error: Could not retrieve Shodan info",
                    CLIStyle.COLORS["ERROR"],
                )
                return False

            console = Console()
            api_table = Table(
                title="Shodan API Information",
                box=box.ROUNDED,
                header_style="bold cyan",
                border_style="cyan",
            )
            api_table.add_column("Property", style="bold green")
            api_table.add_column("Value", style="yellow", overflow="fold")
            for key, value in info.items():
                api_table.add_row(Text(str(key)), Text(str(value)))

            config_table = Table(
                title="Configuration",
                box=box.ROUNDED,
                header_style="bold cyan",
                border_style="cyan",
            )
            config_table.add_column("Item", style="bold green")
            config_table.add_column("Value", style="yellow", overflow="fold")
            config_table.add_row("Config Directory", Text(str(self.paths.root)))
            config_table.add_row("Config File", Text(str(self.paths.config_file)))
            config_table.add_row("Results Directory", Text(str(self.paths.result_dir)))
            config_table.add_row("Search Index File", Text(str(self.paths.index_file)))

            console.print(api_table)
            console.print(config_table)
            return True
        except Exception as error:
            self._emit(f"Error getting info: {error}", CLIStyle.COLORS["ERROR"])
            return False

    @staticmethod
    def _endpoint_text(match: dict[str, Any]) -> Text:
        """Build a readable endpoint cell."""
        ip = str(match.get("ip_str") or match.get("ip") or "N/A")
        port = match.get("port")
        if port is None:
            endpoint = ip
        elif ":" in ip and not ip.startswith("["):
            endpoint = f"[{ip}]:{port}"
        else:
            endpoint = f"{ip}:{port}"

        endpoint_text = Text(endpoint, style="bold cyan")
        hostnames = match.get("hostnames", [])
        if isinstance(hostnames, list):
            names = [str(name) for name in hostnames if name]
            if names:
                endpoint_text.append("\n" + ", ".join(names[:2]), style="dim")
        return endpoint_text

    @staticmethod
    def _service_text(match: dict[str, Any]) -> Text:
        """Build a service and transport cell."""
        service_parts = [
            str(match.get("product")) if match.get("product") else "",
            str(match.get("version")) if match.get("version") else "",
        ]
        service = " ".join(part for part in service_parts if part)
        shodan_data = match.get("_shodan", {})
        if not service and isinstance(shodan_data, dict):
            service = str(shodan_data.get("module", ""))
        transport = str(match.get("transport", ""))
        if transport:
            service = f"{service or 'Unknown'} / {transport}"
        return Text(service or "Unknown")

    @staticmethod
    def _location_text(match: dict[str, Any]) -> Text:
        """Build a country and city cell."""
        location = match.get("location", {})
        if not isinstance(location, dict):
            return Text("N/A")
        city = str(location.get("city") or "")
        country = str(
            location.get("country_name") or location.get("country_code") or ""
        )
        value = ", ".join(part for part in (city, country) if part)
        return Text(value or "N/A")

    @staticmethod
    def _timestamp_text(match: dict[str, Any]) -> Text:
        """Format a Shodan timestamp in an unambiguous UTC representation."""
        timestamp = match.get("timestamp")
        if not timestamp:
            return Text("N/A")
        try:
            parsed = datetime.fromisoformat(str(timestamp).replace("Z", "+00:00"))
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=timezone.utc)
            value = parsed.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        except ValueError:
            value = truncate(str(timestamp), 20)
        return Text(value)

    @classmethod
    def _details_text(cls, match: dict[str, Any]) -> Text:
        """Build the compact service, organization, and timestamp cell."""
        details = cls._service_text(match)
        organization = str(match.get("org") or match.get("isp") or "N/A")
        details.append("\n" + organization, style="dim")
        details.append("\n" + cls._timestamp_text(match).plain, style="dim")
        return details

    @staticmethod
    def _raw_field(value: Any) -> str:
        """Convert a value into one TSV-safe field."""
        if value is None:
            return ""
        return str(value).replace("\t", " ").replace("\r", " ").replace("\n", " ")

    @classmethod
    def _raw_hostnames(cls, match: dict[str, Any]) -> str:
        """Convert hostnames into one comma-separated TSV field."""
        hostnames = match.get("hostnames")
        if isinstance(hostnames, list):
            hostnames = ",".join(cls._raw_field(hostname) for hostname in hostnames)
        return cls._raw_field(hostnames)

    def display_raw_results(self, matches: list[dict[str, Any]]) -> None:
        """Display headerless, fixed-order TSV records for shell pipelines."""
        debug("Displaying raw results", matches_count=len(matches))
        for index, match in enumerate(matches, start=1):
            location = match.get("location")
            if not isinstance(location, dict):
                location = {}

            last_seen = match.get("last_seen")
            if last_seen is None:
                last_seen = match.get("timestamp")

            ip = match.get("ip_str") or match.get("ip")
            fields = [
                self._raw_field(index),
                self._raw_field(ip),
                self._raw_field(match.get("port")),
                self._raw_hostnames(match),
                self._raw_field(match.get("product")),
                self._raw_field(match.get("version")),
                self._raw_field(match.get("transport")),
                self._raw_field(match.get("org") or match.get("isp")),
                self._raw_field(location.get("city")),
                self._raw_field(
                    location.get("country_name") or location.get("country_code")
                ),
                self._raw_field(last_seen),
            ]
            print("\t".join(fields))

    def display_results(
        self,
        matches: list[dict[str, Any]],
        total: int | float,
        limit: int | None = None,
        query: str = "",
        page: int = 1,
        retrieved_count: int | None = None,
    ) -> None:
        """Display a summary panel and a compact, human-readable result table."""
        debug(
            "Displaying results",
            matches_count=len(matches),
            total=total,
            limit=limit,
        )
        if not matches:
            self._emit("No matching results found", CLIStyle.COLORS["ERROR"])
            return

        retrieved = retrieved_count if retrieved_count is not None else len(matches)
        console = Console()
        summary = Text()
        summary.append("Query: ", style="bold cyan")
        summary.append(query or "(not specified)")
        summary.append(f"\nPage: {page}    API total: {total}")
        if limit and retrieved > len(matches):
            summary.append(
                f"\nShowing: {len(matches)} of {retrieved} retrieved (--limit {limit})"
            )
        else:
            summary.append(f"\nShowing: {len(matches)} retrieved")
        console.print(Panel(summary, title="Search Summary", border_style="cyan"))

        results_table = Table(
            title="Results",
            box=box.ROUNDED,
            show_lines=True,
            header_style="bold cyan",
            border_style="cyan",
            expand=True,
            padding=(0, 1),
        )
        results_table.add_column("#", width=4, justify="right", style="dim")
        results_table.add_column("Endpoint", ratio=2, min_width=18, overflow="fold")
        if console.width < 110:
            results_table.add_column("Details", ratio=3, min_width=24, overflow="fold")
            results_table.add_column("Location", ratio=2, min_width=14, overflow="fold")
        else:
            results_table.add_column("Service", ratio=2, min_width=14, overflow="fold")
            results_table.add_column(
                "Organization", ratio=2, min_width=16, overflow="fold"
            )
            results_table.add_column("Location", ratio=2, min_width=14, overflow="fold")
            results_table.add_column("Last Seen", width=20, no_wrap=True)

        for index, match in enumerate(matches, start=1):
            row = [str(index), self._endpoint_text(match)]
            if console.width < 110:
                row.extend([self._details_text(match), self._location_text(match)])
            else:
                organization = str(match.get("org") or match.get("isp") or "N/A")
                row.extend(
                    [
                        self._service_text(match),
                        Text(organization),
                        self._location_text(match),
                        self._timestamp_text(match),
                    ]
                )
            results_table.add_row(*row)
        console.print(results_table)


def positive_int(value: str) -> int:
    """Parse a strictly positive integer for CLI options."""
    try:
        number = int(value)
    except ValueError as error:
        raise argparse.ArgumentTypeError("must be an integer") from error
    if number < 1:
        raise argparse.ArgumentTypeError("must be at least 1")
    return number


def main(argv: list[str] | None = None) -> int:
    """Run the command-line interface and return a process status code."""
    script_name = os.path.basename(sys.argv[0])

    # Define examples and notes
    examples = [
        ("Initialize API key", "init YOUR_API_KEY"),
        ("Basic search", 'search "apache country:cn"'),
        ("Cache control", 'search "nginx port:443" --no-cache'),
        (
            "Complex query",
            'search \'http.favicon.hash:"-620522584" country:"cn"\' --delete-cache',
        ),
        (
            "Pipe to awk",
            'search \'http.favicon.hash:"-620522584" country:"cn"\' --raw | awk {\'print "http://"$2":"$3\'}',
        ),
        ("Readable table output", 'search "apache" --format table'),
        ("JSON output", 'search "apache" --format json'),
        ("Raw TSV output for automation", 'search "apache" --raw'),
        ("Show API info", "info"),
        ("Calculate favicon hash", "hash /path/to/favicon.ico"),
        ("Calculate favicon hash from URL", "hash https://example.com/favicon.ico"),
        ("Debug mode", 'search "nginx" --log'),
    ]

    notes = [
        "SHODAN_API_KEY can provide a key without storing it in shell history",
        "Will automatically use API key from ~/.config/shodan/api_key if available",
        "Custom config is stored in ~/.shodan/config.json",
        "Search results are cached in ~/.shodan/result/",
        "Use --no-cache to skip cache, --delete-cache to refresh cache",
        "Default output is a summary panel plus a compact result table",
        f"--raw writes headerless TSV with fields: {', '.join(RAW_FIELD_ORDER)}",
        "Raw hostnames are comma-separated; missing fields remain empty",
        "Use --format json for structured JSON output",
        "Use --ipv4-only to exclude IPv6 results explicitly",
        "For complex searches, enclose the entire query in quotes",
        "Use 'hash' command to calculate favicon hash for Shodan searches",
        "Use --log to enable debug mode for troubleshooting",
    ]

    parser = ColoredArgumentParser(
        description="Shodan CLI Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=create_example_text(script_name, examples, notes),
    )

    # Add global parameters
    parser.add_argument("--log", action="store_true", help="Enable debug logging")

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # init command
    init_parser = subparsers.add_parser("init", help="Initialize API key")
    init_parser.add_argument(
        "api_key",
        nargs="?",
        help="Shodan API key; omit to use SHODAN_API_KEY or a secure prompt",
    )

    # search command
    search_parser = subparsers.add_parser(
        "search",
        help="Search Shodan",
        description="Search Shodan for specific terms",
        epilog=f"""
{CLIStyle.color("Examples:", CLIStyle.COLORS["SUB_TITLE"])}
  {CLIStyle.color("# Basic search", CLIStyle.COLORS["EXAMPLE"])}
  {script_name} search "apache country:cn"
  
  {CLIStyle.color("# Search with quotes", CLIStyle.COLORS["EXAMPLE"])}
  {script_name} search 'http.html:"hello world"'
  {script_name} search 'http.favicon.hash:"-620522584"'
  
  {CLIStyle.color("# Cache control", CLIStyle.COLORS["EXAMPLE"])}
  {script_name} search "nginx port:443" --no-cache
  {script_name} search "apache" --delete-cache
  
  {CLIStyle.color("# Pagination (Paid API only)", CLIStyle.COLORS["EXAMPLE"])}
  {script_name} search "nginx" --page 2
  {script_name} search "apache country:cn" --page 3

  {CLIStyle.color("# Limit results", CLIStyle.COLORS["EXAMPLE"])}
  {script_name} search "nginx" --limit 10
  
  {CLIStyle.color("# Headerless TSV for automation", CLIStyle.COLORS["EXAMPLE"])}
  {script_name} search "apache" --raw
  {CLIStyle.color("# Fields: index, ip, port, hostnames, product, version, transport,", CLIStyle.COLORS["CONTENT"])}
  {CLIStyle.color("#         organization, city, country, last_seen", CLIStyle.COLORS["CONTENT"])}

  {CLIStyle.color("# JSON output for scripts", CLIStyle.COLORS["EXAMPLE"])}
  {script_name} search "apache" --format json

  {CLIStyle.color("# IPv4-only search", CLIStyle.COLORS["EXAMPLE"])}
  {script_name} search "apache" --ipv4-only
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    search_parser.add_argument(
        "query", nargs="+", help="Search query (use quotes for complex queries)"
    )
    search_parser.add_argument(
        "--page",
        type=positive_int,
        default=1,
        help="Page number (Paid API only, default: 1)",
    )
    search_parser.add_argument(
        "--no-cache", action="store_true", help="Do not use or save cache"
    )
    search_parser.add_argument(
        "--delete-cache", action="store_true", help="Delete and refresh cache"
    )
    search_parser.add_argument(
        "--limit",
        type=positive_int,
        help="Limit the number of results to display",
    )
    output_group = search_parser.add_mutually_exclusive_group()
    output_group.add_argument(
        "--format",
        choices=("table", "json"),
        default="table",
        help="Output format when --raw is not selected (default: table)",
    )
    output_group.add_argument(
        "--raw",
        action="store_true",
        help=(
            "Write headerless TSV to stdout with fields: "
            + ", ".join(RAW_FIELD_ORDER)
            + "; hostnames are comma-separated"
        ),
    )
    search_parser.add_argument(
        "--ipv4-only",
        action="store_true",
        help="Exclude IPv6 results from the response",
    )
    search_parser.add_argument(
        "--log",
        action="store_true",
        default=argparse.SUPPRESS,
        help="Enable debug logging",
    )

    # info command
    subparsers.add_parser("info", help="Show Shodan API information and config")

    # hash command
    hash_parser = subparsers.add_parser(
        "hash",
        help="Calculate favicon hash for Shodan searches",
        description="Calculate favicon hash for Shodan searches",
        epilog=f"""
{CLIStyle.color("Examples:", CLIStyle.COLORS["SUB_TITLE"])}
  {CLIStyle.color("# Calculate hash from local file", CLIStyle.COLORS["EXAMPLE"])}
  {script_name} hash /path/to/favicon.ico
  
  {CLIStyle.color("# Calculate hash from URL", CLIStyle.COLORS["EXAMPLE"])}
  {script_name} hash https://example.com/favicon.ico
  
  {CLIStyle.color("# Calculate hash from website (auto-detect favicon)", CLIStyle.COLORS["EXAMPLE"])}
  {script_name} hash https://example.com

{CLIStyle.color("Notes:", CLIStyle.COLORS["SUB_TITLE"])}
  {CLIStyle.color("- For URLs, if the provided path is not a valid favicon,", CLIStyle.COLORS["CONTENT"])}
  {CLIStyle.color("  the tool will try to find favicon at standard locations", CLIStyle.COLORS["CONTENT"])}
  {CLIStyle.color("- Supported favicon formats: .ico, .png", CLIStyle.COLORS["CONTENT"])}
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    hash_parser.add_argument(
        "path_or_url", help="Path to local favicon file or URL (can be website URL)"
    )

    args = parser.parse_args(argv)

    global DEBUG_MODE
    DEBUG_MODE = args.log

    if DEBUG_MODE:
        print(
            CLIStyle.color("Debug mode enabled", CLIStyle.COLORS["CONTENT"]),
            file=sys.stderr,
        )

    if not args.command:
        parser.print_help()
        return 0

    if args.command == "init":
        client = ShodanClient()
        api_key = args.api_key or os.environ.get("SHODAN_API_KEY")
        if not api_key:
            try:
                api_key = getpass("Shodan API key: ")
            except (EOFError, KeyboardInterrupt):
                print("API key input cancelled", file=sys.stderr)
                return 1
        return 0 if client.init_api_key(api_key) else 1

    if args.command == "search":
        raw_output = args.raw
        client = ShodanClient(quiet=raw_output or args.format == "json")
        query = " ".join(args.query)
        debug(
            "Search query",
            query=query,
            page=args.page,
            no_cache=args.no_cache,
            delete_cache=args.delete_cache,
            output_format=args.format,
            raw_output=raw_output,
            ipv4_only=args.ipv4_only,
        )
        results = client.search(
            query,
            page=args.page,
            no_cache=args.no_cache,
            delete_cache=args.delete_cache,
            ipv4_only=args.ipv4_only,
        )
        if not results:
            debug("No results found", results=results)
            return 1

        matches = [
            match for match in results.get("matches", []) if isinstance(match, dict)
        ]
        debug("Matches count", count=len(matches))
        display_matches = matches[: args.limit] if args.limit else matches

        if raw_output:
            client.display_raw_results(display_matches)
        elif args.format == "json":
            output = dict(results)
            output["matches"] = display_matches
            json.dump(output, sys.stdout, indent=2, ensure_ascii=False)
            print()
        else:
            client.display_results(
                display_matches,
                results.get("total", 0),
                args.limit,
                query,
                client.last_search_page,
                len(matches),
            )
        return 0

    if args.command == "info":
        return 0 if ShodanClient().show_info() else 1

    if args.command == "hash":
        return 0 if calculate_favicon_hash(args.path_or_url) else 1

    return 2


def calculate_favicon_hash(path_or_url: str) -> bool:
    """Calculate and display the Shodan favicon hash for a file or URL."""
    try:
        debug("Calculating favicon hash", path_or_url=path_or_url)
        # Determine if input is a URL or file path
        is_url = path_or_url.lower().startswith(("http://", "https://"))
        favicon_source = path_or_url
        session = requests.Session()
        session.headers.update({"User-Agent": "shodan-cli/2.0"})

        if is_url:
            print(
                CLIStyle.color(
                    f"Downloading from URL: {path_or_url}", CLIStyle.COLORS["CONTENT"]
                )
            )
            try:
                # First check if the URL directly points to a favicon
                response = session.get(path_or_url, timeout=10)
                if response.status_code != 200:
                    debug("HTTP error", status_code=response.status_code)
                    print(
                        CLIStyle.color(
                            f"Error: HTTP status code {response.status_code}",
                            CLIStyle.COLORS["ERROR"],
                        )
                    )
                    return False

                # Check if the content is a valid favicon
                content_type = response.headers.get("Content-Type", "").lower()
                content = _read_response_content(response)
                is_favicon = _is_valid_favicon_content(content_type, content)
                debug(
                    "Content validation",
                    content_type=content_type,
                    is_favicon=is_favicon,
                    content_length=len(content),
                )

                # If not a direct favicon URL, try to find favicon at the website
                if not is_favicon:
                    base_url = _get_base_url(response.url)
                    print(
                        CLIStyle.color(
                            f"URL is not a direct favicon. Trying to find favicon at: {base_url}",
                            CLIStyle.COLORS["CONTENT"],
                        )
                    )

                    # Try standard favicon locations
                    favicon_paths = [
                        "/favicon.ico",
                        "/favicon.png",
                        "/assets/favicon.ico",
                        "/images/favicon.ico",
                        "/static/favicon.ico",
                        "/public/favicon.ico",
                    ]

                    favicon_found = False
                    for path in favicon_paths:
                        try:
                            favicon_url = urllib.parse.urljoin(base_url, path)
                            print(
                                CLIStyle.color(
                                    f"Trying: {favicon_url}", CLIStyle.COLORS["CONTENT"]
                                )
                            )
                            favicon_response = session.get(favicon_url, timeout=10)

                            if favicon_response.status_code == 200:
                                favicon_content_type = favicon_response.headers.get(
                                    "Content-Type", ""
                                ).lower()
                                favicon_content = _read_response_content(
                                    favicon_response
                                )
                                if _is_valid_favicon_content(
                                    favicon_content_type, favicon_content
                                ):
                                    content = favicon_content
                                    favicon_found = True
                                    favicon_source = (
                                        favicon_url  # Update favicon source
                                    )
                                    print(
                                        CLIStyle.color(
                                            f"Found valid favicon at: {favicon_url}",
                                            CLIStyle.COLORS["CONTENT"],
                                        )
                                    )
                                    break
                        except Exception as e:
                            print(
                                CLIStyle.color(
                                    f"Error trying {path}: {str(e)}",
                                    CLIStyle.COLORS["ERROR"],
                                )
                            )
                            continue

                    # If still not found, try to parse HTML to find favicon link
                    if not favicon_found:
                        try:
                            print(
                                CLIStyle.color(
                                    "Searching for favicon link in HTML...",
                                    CLIStyle.COLORS["CONTENT"],
                                )
                            )
                            if BeautifulSoup is None:
                                raise ImportError("beautifulsoup4 is not installed")
                            soup = BeautifulSoup(response.content, "html.parser")

                            # Look for favicon in link tags
                            favicon_links = []
                            for link in soup.find_all("link"):
                                rel = link.get("rel", [])
                                if isinstance(rel, str):
                                    rel = [rel]

                                if any(
                                    r.lower() in ["icon", "shortcut icon"] for r in rel
                                ):
                                    href = link.get("href")
                                    if href:
                                        favicon_links.append(href)

                            # Try each found favicon link
                            for href in favicon_links:
                                try:
                                    # Handle relative URLs
                                    if not href.startswith(("http://", "https://")):
                                        href = urllib.parse.urljoin(base_url, href)

                                    print(
                                        CLIStyle.color(
                                            f"Trying HTML link: {href}",
                                            CLIStyle.COLORS["CONTENT"],
                                        )
                                    )
                                    favicon_response = session.get(href, timeout=10)

                                    if favicon_response.status_code == 200:
                                        favicon_content_type = (
                                            favicon_response.headers.get(
                                                "Content-Type", ""
                                            ).lower()
                                        )
                                        favicon_content = _read_response_content(
                                            favicon_response
                                        )
                                        if _is_valid_favicon_content(
                                            favicon_content_type,
                                            favicon_content,
                                        ):
                                            content = favicon_content
                                            favicon_found = True
                                            favicon_source = (
                                                href  # Update favicon source
                                            )
                                            print(
                                                CLIStyle.color(
                                                    f"Found valid favicon at: {href}",
                                                    CLIStyle.COLORS["CONTENT"],
                                                )
                                            )
                                            break
                                except Exception as e:
                                    print(
                                        CLIStyle.color(
                                            f"Error trying HTML link {href}: {str(e)}",
                                            CLIStyle.COLORS["ERROR"],
                                        )
                                    )
                                    continue
                        except ImportError:
                            print(
                                CLIStyle.color(
                                    "BeautifulSoup not installed. Skipping HTML parsing.",
                                    CLIStyle.COLORS["ERROR"],
                                )
                            )
                        except Exception as e:
                            print(
                                CLIStyle.color(
                                    f"Error parsing HTML: {str(e)}",
                                    CLIStyle.COLORS["ERROR"],
                                )
                            )

                    if not favicon_found:
                        print(
                            CLIStyle.color(
                                "Error: Could not find a valid favicon at the URL or standard locations",
                                CLIStyle.COLORS["ERROR"],
                            )
                        )
                        print(
                            CLIStyle.color(
                                "Please provide a direct link to a favicon file (.ico, .png)",
                                CLIStyle.COLORS["ERROR"],
                            )
                        )
                        return False
            except Exception as e:
                print(
                    CLIStyle.color(
                        f"Error downloading favicon: {str(e)}", CLIStyle.COLORS["ERROR"]
                    )
                )
                return False
        else:
            # Local file
            if not os.path.exists(path_or_url):
                print(
                    CLIStyle.color(
                        f"Error: File not found: {path_or_url}",
                        CLIStyle.COLORS["ERROR"],
                    )
                )
                return False

            print(
                CLIStyle.color(
                    f"Reading favicon from file: {path_or_url}",
                    CLIStyle.COLORS["CONTENT"],
                )
            )
            with open(path_or_url, "rb") as f:
                content = f.read()

            if len(content) > MAX_FAVICON_SIZE:
                print(
                    CLIStyle.color(
                        "Error: Favicon file is too large",
                        CLIStyle.COLORS["ERROR"],
                    )
                )
                return False

            # Check if the file is a valid favicon
            if not _is_valid_favicon_file(path_or_url, content):
                print(
                    CLIStyle.color(
                        "Error: The file does not appear to be a valid favicon",
                        CLIStyle.COLORS["ERROR"],
                    )
                )
                print(
                    CLIStyle.color(
                        "Please provide a valid favicon file (.ico, .png)",
                        CLIStyle.COLORS["ERROR"],
                    )
                )
                return False

        # Display favicon source before calculating hash
        print(
            CLIStyle.color(
                f"Using favicon from: {favicon_source}", CLIStyle.COLORS["CONTENT"]
            )
        )

        # Calculate hash using Shodan's updated method
        print(CLIStyle.color("Calculating favicon hash...", CLIStyle.COLORS["CONTENT"]))
        b64_content = base64.encodebytes(content)
        hash_value = mmh3.hash(b64_content)

        # Display results - simplified output without panel
        console = Console()

        console.print(
            f"[bold red]Favicon Hash:[/bold red] [bold green]{hash_value}[/bold green]"
        )
        console.print(
            "[bold cyan]Example Shodan search query:[/bold cyan]",
            f'[yellow]http.favicon.hash:"{hash_value}"[/yellow]',
        )
        return True

    except Exception as e:
        debug("Error in calculate_favicon_hash", error=str(e))
        print(
            CLIStyle.color(
                f"Error calculating hash: {str(e)}", CLIStyle.COLORS["ERROR"]
            )
        )
        return False


def _read_response_content(response: requests.Response) -> bytes:
    """Read a response while enforcing a favicon size limit."""
    content_length = response.headers.get("Content-Length")
    if content_length and int(content_length) > MAX_FAVICON_SIZE:
        raise ValueError("favicon response is too large")
    content = response.content
    if len(content) > MAX_FAVICON_SIZE:
        raise ValueError("favicon response is too large")
    return content


def _is_valid_favicon_content(content_type: str, content: bytes) -> bool:
    """Return whether remote content has a supported favicon signature."""
    content_type = content_type.split(";", 1)[0].strip().lower()
    supported_type = content_type in {
        "",
        "application/octet-stream",
        "image/ico",
        "image/png",
        "image/vnd.microsoft.icon",
        "image/x-icon",
    }
    has_signature = content.startswith((b"\x00\x00\x01\x00", b"\x89PNG\r\n\x1a\n"))
    return len(content) > 16 and supported_type and has_signature


def _is_valid_favicon_file(file_path: str, content: bytes) -> bool:
    """Return whether a local file has a supported extension and signature."""
    valid_extension = Path(file_path).suffix.lower() in {".ico", ".png"}
    has_signature = content.startswith((b"\x00\x00\x01\x00", b"\x89PNG\r\n\x1a\n"))
    return valid_extension and len(content) > 16 and has_signature


def _get_base_url(url: str) -> str:
    """Extract and validate the origin from a URL."""
    parsed = urllib.parse.urlparse(url)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise ValueError("URL must include an http or https origin")
    return f"{parsed.scheme}://{parsed.netloc}"


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(
            CLIStyle.color("\nOperation cancelled by user", CLIStyle.COLORS["ERROR"]),
            file=sys.stderr,
        )
        sys.exit(130)
    except Exception as error:
        if DEBUG_MODE:
            traceback.print_exc()
        print(
            CLIStyle.color(f"\nError: {error}", CLIStyle.COLORS["ERROR"]),
            file=sys.stderr,
        )
        sys.exit(1)
