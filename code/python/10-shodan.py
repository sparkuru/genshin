# -*- coding: utf-8 -*-
# pip install shodan rich mmh3

import os
import sys
import json
import argparse
import shodan
from datetime import datetime, timezone, timedelta
from rich.console import Console
from rich.table import Table
from rich import box
from rich.panel import Panel
import threading
import time
import hashlib
import re
import base64
import mmh3
import requests
import urllib.parse
from bs4 import BeautifulSoup

# 全局日志级别
DEBUG_MODE = False

def clean_path(path):
    """清理路径，只保留文件名"""
    return os.path.basename(path)

def color(text, color_code=0):
    """为调试信息添加颜色"""
    color_table = {
        0: "{}",  # 无色
        1: "\033[1;30m{}\033[0m",  # 黑色加粗
        2: "\033[1;31m{}\033[0m",  # 红色加粗
        3: "\033[1;32m{}\033[0m",  # 绿色加粗
        4: "\033[1;33m{}\033[0m",  # 黄色加粗
        5: "\033[1;34m{}\033[0m",  # 蓝色加粗
        6: "\033[1;35m{}\033[0m",  # 紫色加粗
        7: "\033[1;36m{}\033[0m",  # 青色加粗
        8: "\033[1;37m{}\033[0m",  # 白色加粗
    }
    return color_table[color_code].format(text)

def debug(*args, file=None, append=True, **kwargs):
    """
    打印传入的参数值，并显示其在源码的文件和行号
    ```python
    debug(
        'Hello',    # 要打印的参数 1
        'World',    # 要打印的参数 2
        file='debug.log',  # 输出文件路径，默认为 None（输出到控制台）
        append=False,  # 是否追加到文件，默认为 True
        **kwargs  # 要打印的键值对参数
    )

    return = None
    ```
    """
    if not DEBUG_MODE:
        return
        
    import inspect
    frame = inspect.currentframe().f_back
    info = inspect.getframeinfo(frame)
    
    output = f"{color(clean_path(info.filename), 3)}: {color(info.lineno, 4)} {color('|', 7)} "
    
    for i, arg in enumerate(args):
        arg_str = str(arg)
        output += f"{color(arg_str, 2)} "
    
    for k, v in kwargs.items():
        output += f"{color(k+'=', 6)}{color(str(v), 2)} "
    
    output += '\n'
    
    if file:
        mode = 'a' if append else 'w'
        with open(file, mode) as f:
            clean_output = re.sub(r'\033\[\d+;\d+m|\033\[0m', '', output)
            f.write(clean_output)
    else:
        print(output, end='')

# CLI 帮助样式模板
class CLIStyle:
    """CLI 工具统一样式配置"""
    COLORS = {
        "TITLE": 7,      # 青色 - 主标题
        "SUB_TITLE": 2,  # 红色 - 子标题
        "CONTENT": 3,    # 绿色 - 普通内容
        "EXAMPLE": 7,    # 青色 - 示例
        "WARNING": 4,    # 黄色 - 警告
        "ERROR": 2,      # 红色 - 错误
    }

    @staticmethod
    def color(text: str = "", color: int = COLORS["CONTENT"]) -> str:
        """统一的颜色处理函数"""
        color_table = {
            0: "{}",  # 无色
            1: "\033[1;30m{}\033[0m",  # 黑色加粗
            2: "\033[1;31m{}\033[0m",  # 红色加粗
            3: "\033[1;32m{}\033[0m",  # 绿色加粗
            4: "\033[1;33m{}\033[0m",  # 黄色加粗
            5: "\033[1;34m{}\033[0m",  # 蓝色加粗
            6: "\033[1;35m{}\033[0m",  # 紫色加粗
            7: "\033[1;36m{}\033[0m",  # 青色加粗
            8: "\033[1;37m{}\033[0m",  # 白色加粗
        }
        return color_table[color].format(text)

class ColoredArgumentParser(argparse.ArgumentParser):
    """统一的命令行参数解析器"""
    def _format_action_invocation(self, action):
        if not action.option_strings:
            metavar, = self._metavar_formatter(action, action.dest)(1)
            return metavar
        else:
            parts = []
            if action.nargs == 0:
                parts.extend(map(lambda x: CLIStyle.color(x, CLIStyle.COLORS["SUB_TITLE"]), 
                               action.option_strings))
            else:
                default = action.dest.upper()
                args_string = self._format_args(action, default)
                for option_string in action.option_strings:
                    parts.append(CLIStyle.color(
                        f'{option_string} {args_string}', 
                        CLIStyle.COLORS["SUB_TITLE"]
                    ))
            return ', '.join(parts)

    def format_help(self):
        formatter = self._get_formatter()
        
        # 添加描述
        if self.description:
            formatter.add_text(CLIStyle.color(self.description, CLIStyle.COLORS["TITLE"]))
            
        # 添加用法
        formatter.add_usage(self.usage, self._actions, self._mutually_exclusive_groups)
        
        # 添加参数组
        formatter.add_text(CLIStyle.color("\nOptional Arguments:", CLIStyle.COLORS["TITLE"]))
        for action_group in self._action_groups:
            formatter.start_section(action_group.title)
            formatter.add_arguments(action_group._group_actions)
            formatter.end_section()
            
        # 添加示例和注释
        if self.epilog:
            formatter.add_text(self.epilog)
            
        return formatter.format_help()

def create_example_text(script_name: str, examples: list, notes: list = None) -> str:
    """创建统一的示例文本"""
    text = f'\n{CLIStyle.color("Examples:", CLIStyle.COLORS["SUB_TITLE"])}'
    
    for desc, cmd in examples:
        text += f'\n  {CLIStyle.color(f"# {desc}", CLIStyle.COLORS["EXAMPLE"])}'
        text += f'\n  {CLIStyle.color(f"{script_name} {cmd}", CLIStyle.COLORS["CONTENT"])}'
        text += '\n'
    
    if notes:
        text += f'\n{CLIStyle.color("Notes:", CLIStyle.COLORS["SUB_TITLE"])}'
        for note in notes:
            text += f'\n  {CLIStyle.color(f"- {note}", CLIStyle.COLORS["CONTENT"])}'
    
    return text

# Global variable definitions
shodan_dir_name = ".shodan"
shodan_dir_path = os.path.expanduser(f"~/{shodan_dir_name}")
shodan_config_name = "config.json"
shodan_config_path = os.path.join(shodan_dir_path, shodan_config_name)
shodan_result_dir = os.path.join(shodan_dir_path, "result")

# Global variables
is_searching = False


def show_loading_animation():
    """Display loading animation"""
    animation = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
    i = 0
    global is_searching
    start_time = time.time()
    while is_searching:
        elapsed = time.time() - start_time
        sys.stdout.write(f"\r{CLIStyle.color(f'{animation[i]} Pending... ({elapsed:.1f}s)', 6)}")
        sys.stdout.flush()
        time.sleep(0.1)
        i = (i + 1) % len(animation)
    sys.stdout.write("\r" + " " * 50 + "\r")
    sys.stdout.flush()


def truncate(text, width):
    """截断文本并添加省略号"""
    if len(text) > width:
        return text[:width-3] + "..."
    return text


class ShodanClient:
    def __init__(self):
        self.api_key = None
        self.client = None
        self.is_paid = False  # Default value
        self.load_config()

    def load_config(self):
        """Load config file, prioritize custom config, fallback to shodan cli config if not exists"""
        # First try to load custom config
        if os.path.exists(shodan_config_path):
            try:
                with open(shodan_config_path, "r") as f:
                    config = json.load(f)
                    self.api_key = config.get("api_key")
                    self.is_paid = config.get(
                        "is_paid", False
                    )  # Load is_paid status from config file
                    if self.api_key:
                        self.client = shodan.Shodan(self.api_key)
                        return
            except Exception as e:
                print(CLIStyle.color(f"Error loading config: {str(e)}", 2))

        # If custom config doesn't exist or is invalid, try loading shodan cli config
        shodan_cli_config = os.path.expanduser("~/.config/shodan/api_key")
        if os.path.exists(shodan_cli_config):
            try:
                with open(shodan_cli_config, "r") as f:
                    self.api_key = f.read().strip()
                    if self.api_key:
                        self.client = shodan.Shodan(self.api_key)
                        # Sync shodan cli config to custom config
                        self.sync_from_cli_config()
                        print(CLIStyle.color("Using API key from Shodan CLI config", 7))
            except Exception as e:
                print(CLIStyle.color(f"Error loading Shodan CLI config: {str(e)}", 2))

    def sync_from_cli_config(self):
        """Sync shodan cli config to custom config file"""
        try:
            # Test API key and get plan info
            test_client = shodan.Shodan(self.api_key)
            info = test_client.info()
            is_paid = info.get("plan", "").lower() != "dev" and info.get(
                "unlocked", False
            )

            os.makedirs(shodan_dir_path, exist_ok=True)
            config = {
                "api_key": self.api_key,
                "is_paid": is_paid,
                "plan": info.get("plan", "unknown"),
            }
            with open(shodan_config_path, "w") as f:
                json.dump(config, f, indent=4)
            print(CLIStyle.color(f"Synced API key to: {shodan_config_path}", 7))
            print(
                CLIStyle.color(
                    f"Plan type: {info.get('plan', 'unknown')} ({'Paid' if is_paid else 'Free'})",
                    7,
                )
            )

            # Update instance attributes
            self.is_paid = is_paid

        except Exception as e:
            print(CLIStyle.color(f"Error syncing config: {str(e)}", 2))

    def init_api_key(self, api_key):
        """Initialize API key"""
        try:
            # Test if API key is valid
            test_client = shodan.Shodan(api_key)
            info = test_client.info()

            # Check if this is a paid plan
            is_paid = info.get("plan", "").lower() != "dev" and info.get(
                "unlocked", False
            )

            # Ensure directory exists
            os.makedirs(shodan_dir_path, exist_ok=True)

            # Save configuration
            config = {
                "api_key": api_key,
                "is_paid": is_paid,
                "plan": info.get("plan", "unknown"),
            }
            with open(shodan_config_path, "w") as f:
                json.dump(config, f, indent=4)

            print(CLIStyle.color("API key successfully initialized!", 3))
            print(CLIStyle.color(f"Config saved to: {shodan_config_path}", 7))
            print(
                CLIStyle.color(
                    f"Plan type: {info.get('plan', 'unknown')} ({'Paid' if is_paid else 'Free'})",
                    7,
                )
            )

            self.api_key = api_key
            self.client = test_client
            self.is_paid = is_paid  # Update instance attribute

        except Exception as e:
            print(CLIStyle.color("Error initializing API key:", 2))
            print(CLIStyle.color(str(e), 2))
            sys.exit(1)

    def _get_cache_filename(self, query, page=1):
        """Generate cache filename based on query and page number"""

        # Normalize query string, handle spaces within quotes
        def normalize_query(q):
            # Protect quoted content
            protected = []

            def protect(match):
                protected.append(match.group(0))
                return f"__PROTECTED_{len(protected) - 1}__"

            # Protect content in double and single quotes
            q = re.sub(r'"[^"]*"', protect, q)
            q = re.sub(r"'[^']*'", protect, q)

            # Normalize spaces
            q = q.replace(" ", "_")

            # Restore protected content
            for i, p in enumerate(protected):
                q = q.replace(f"__PROTECTED_{i}__", p.strip("\"'"))

            return q

        # Normalize query string and include page number
        normalized_query = normalize_query(query)
        # Generate hash from normalized query and page number
        query_hash = hashlib.md5(f"{normalized_query}_page{page}".encode()).hexdigest()[
            :12
        ]
        return os.path.join(shodan_result_dir, f"result_{query_hash}.json")

    def _update_search_index(self, query, cache_file, results, page=1):
        """Update search index"""
        index_file = os.path.join(shodan_dir_path, "search-result.json")
        try:
            # Read existing index
            index_data = {}
            if os.path.exists(index_file):
                with open(index_file, "r") as f:
                    index_data = json.load(f)

            if "searches" not in index_data:
                index_data["searches"] = []

            # Clean up records of non-existent cache files
            index_data["searches"] = [
                search
                for search in index_data["searches"]
                if os.path.exists(
                    os.path.join(shodan_result_dir, search.get("result_file", ""))
                )
            ]

            # Check if query and page combination already exists
            search_key = f"{query}_page{page}"
            for search in index_data["searches"]:
                if search.get("search_key") == search_key:
                    # Update existing record
                    search.update(
                        {
                            "last_updated": datetime.now().isoformat(),
                            "total_results": results.get("total", 0),
                            "matches_count": len(results.get("matches", [])),
                        }
                    )
                    break
            else:
                # If query doesn't exist, add new record
                search_record = {
                    "query": query,
                    "search_key": search_key,
                    "page": page,
                    "created_at": datetime.now().isoformat(),
                    "last_updated": datetime.now().isoformat(),
                    "result_file": os.path.basename(cache_file),
                    "total_results": results.get("total", 0),
                    "matches_count": len(results.get("matches", [])),
                }
                index_data["searches"].insert(0, search_record)

            # Write index file
            with open(index_file, "w") as f:
                json.dump(index_data, f, indent=2)

        except Exception as e:
            print(CLIStyle.color(f"Warning: Failed to update search index: {str(e)}", 4))

    def search(self, query, page=1, no_cache=False, delete_cache=False):
        """Execute search and handle caching"""
        if not self.client:
            debug("API key not configured")
            print(CLIStyle.color("Error: API key not configured. Use 'init' command first.", 2))
            return None

        # Check paid API access for pagination
        if page > 1 and not self.is_paid:
            debug("Free API pagination limit", page=page, is_paid=self.is_paid)
            print(
                CLIStyle.color(
                    "Warning: Free API can only access the first page of results (max 100)",
                    4,
                )
            )
            page = 1

        global is_searching
        results = None

        try:
            # Check cache - now includes page number
            cache_file = self._get_cache_filename(query, page)
            debug("Cache file", cache_file=cache_file)

            # If delete_cache is specified and cache exists, delete it
            if delete_cache and os.path.exists(cache_file):
                try:
                    os.remove(cache_file)
                    print(CLIStyle.color("Deleted existing cache.", 7))
                except Exception as e:
                    print(CLIStyle.color(f"Error deleting cache: {str(e)}", 2))

            # Check if we need to perform a new search
            need_new_search = no_cache or delete_cache or not os.path.exists(cache_file)

            # For pages > 1, also check if previous page exists
            if page > 1 and not need_new_search:
                prev_cache_file = self._get_cache_filename(query, page - 1)
                if not os.path.exists(prev_cache_file):
                    print(
                        CLIStyle.color(
                            f"Previous page {page - 1} not found, performing new search...",
                            7,
                        )
                    )
                    need_new_search = True

            if need_new_search:
                # Print search information first
                offset = (page - 1) * 100
                print(
                    f"\nSearching with query: {CLIStyle.color(query, 7)}, page: {CLIStyle.color(str(page), 7)}, offset: {CLIStyle.color(str(offset), 7)}"
                )
                print()  # Add empty line

                # Start loading animation
                is_searching = True
                loading_thread = threading.Thread(target=show_loading_animation)
                loading_thread.daemon = True
                loading_thread.start()

                results = self._do_search(query, page)
                debug("Search results", total=results.get("total") if results else None, 
                      matches_count=len(results.get("matches", [])) if results and "matches" in results else 0)
                is_searching = False
                loading_thread.join()

                # Save results if search was successful
                if results and not no_cache:
                    try:
                        os.makedirs(shodan_result_dir, exist_ok=True)
                        with open(cache_file, "w") as f:
                            json.dump(results, f, indent=2)
                        self._update_search_index(query, cache_file, results, page)
                    except Exception as e:
                        print(CLIStyle.color(f"Error saving cache: {str(e)}", 2))
            else:
                # Use cached results
                try:
                    with open(cache_file, "r") as f:
                        results = json.load(f)
                        debug("Loaded from cache", cache_file=cache_file)
                        print(CLIStyle.color("Using cached results...", 7), end="")
                except Exception as e:
                    debug("Cache read error", error=str(e))
                    print(CLIStyle.color(f"Error reading cache: {str(e)}", 2))
                    # If cache read fails, perform new search
                    is_searching = True
                    loading_thread = threading.Thread(target=show_loading_animation)
                    loading_thread.daemon = True
                    loading_thread.start()
                    results = self._do_search(query, page)
                    is_searching = False
                    loading_thread.join()

            # 在处理结果之前添加更严格的验证
            if not results or not isinstance(results, dict):
                debug("Invalid results format", results=results)
                print(CLIStyle.color("搜索返回了无效的结果格式", CLIStyle.COLORS["ERROR"]))
                return None
            
            matches = results.get("matches", [])
            if not isinstance(matches, list):
                debug("Invalid matches format", matches=matches)
                print(CLIStyle.color("搜索返回了无效的匹配结果格式", CLIStyle.COLORS["ERROR"]))
                return None
            
            # 确保 total 字段存在且有效
            total = results.get("total", 0)
            if not isinstance(total, (int, float)):
                total = len(matches)

            return results

        except Exception as e:
            is_searching = False
            debug("Search error", error=str(e))
            print(CLIStyle.color(f"\n搜索过程中发生错误: {str(e)}", CLIStyle.COLORS["ERROR"]))
            return None

    def _do_search(self, query, page=1):
        """Execute actual search operation against Shodan API"""
        try:
            try:
                debug("Executing Shodan API search", query=query, page=page)
                # Use page parameter for pagination
                response = self.client.search(query, page=page)
                
                if response and "matches" in response:
                    debug("Raw response", total=response.get("total"), matches_count=len(response.get("matches", [])))
                    response["matches"] = [
                        match for match in response["matches"]
                        if match.get("ip_str", "").count(":") == 0  # IPv6 地址包含多个冒号
                    ]
                    response["total"] = len(response["matches"])
                    debug("Filtered response", total=response.get("total"), matches_count=len(response.get("matches", [])))

                if not response or "matches" not in response:
                    debug("Invalid response", response=response)
                    print(CLIStyle.color("No results found or invalid response", 2))
                    return None

                print(CLIStyle.color(f"\nGot {len(response.get('matches', []))} results", 7))
                return response

            except shodan.APIError as e:
                debug("Shodan API error", error=str(e))
                if "Search cursor timed out" in str(e):
                    print(CLIStyle.color("\nError: Search cursor timed out.", 2))
                    print(
                        CLIStyle.color(
                            "Note: Shodan API may timeout when accessing higher page numbers directly.",
                            4,
                        )
                    )
                    print(
                        CLIStyle.color(
                            "Suggestion: Start from page 1 or try a lower page number.",
                            4,
                        )
                    )
                    return None
                else:
                    raise e

        except Exception as e:
            debug("Search execution error", error=str(e))
            print(CLIStyle.color("Search error:", 2))
            print(CLIStyle.color(str(e), 2))
            return None

    def show_info(self):
        """Display Shodan API information and configuration"""
        if not self.client:
            print(CLIStyle.color("Error: API key not configured. Use 'init' command first.", 2))
            return

        try:
            info = self.client.info()
            if not info:
                print(CLIStyle.color("Error: Could not retrieve Shodan info", 2))
                return

            console = Console()

            # Display API information
            api_table = Table(
                title="Shodan API Information",
                box=box.ROUNDED,
                header_style="bold cyan",
                border_style="cyan",
            )

            api_table.add_column("Property", style="bold green")
            api_table.add_column("Value", style="yellow")

            for key, value in info.items():
                api_table.add_row(str(key), str(value))

            console.print()
            console.print(api_table)

            # Display configuration information
            config_table = Table(
                title="Configuration",
                box=box.ROUNDED,
                header_style="bold cyan",
                border_style="cyan",
            )

            config_table.add_column("Item", style="bold green")
            config_table.add_column("Value", style="yellow")

            config_table.add_row("Config Directory", shodan_dir_path)
            config_table.add_row("Config File", shodan_config_path)
            config_table.add_row("Results Directory", shodan_result_dir)
            config_table.add_row(
                "Search Index File", os.path.join(shodan_dir_path, "search-result.json")
            )

            console.print()
            console.print(config_table)
            console.print()

        except Exception as e:
            print(CLIStyle.color("Error getting info:", 2))
            print(CLIStyle.color(str(e), 2))
            return

    def get_terminal_width(self):
        """获取终端宽度"""
        try:
            import shutil
            return shutil.get_terminal_size().columns
        except:
            return 80  # 默认宽度

    def truncate(self, text, width):
        """截断文本并添加省略号"""
        if len(text) > width:
            return text[:width-3] + "..."
        return text

    def display_results(self, matches, total, limit=None):
        """根据终端宽度动态显示结果"""
        debug("Displaying results", matches_count=len(matches) if matches else 0, total=total, limit=limit)
        
        # 添加输入验证
        if not matches:
            print(CLIStyle.color("没有找到匹配的结果", CLIStyle.COLORS["ERROR"]))
            return
        
        console = Console()
        console.print()
        
        # 计算终端宽度
        term_width = self.get_terminal_width()
        debug("Terminal width", width=term_width)
        
        # 定义列配置
        # (列名, 最小宽度, 优先级[数字越小优先级越高])
        columns = [
            ("IP", 15, 1),
            ("Port", 6, 1),
            ("URL", 30, 1),
            ("Organization", 30, 2),
            ("Location", 25, 3),
            ("Timestamp (UTC+8)", 19, 4)
        ]
        
        # 创建表格
        results_table = Table(
            box=box.ROUNDED,
            header_style="bold cyan",
            border_style="cyan",
            show_lines=True,
            padding=(0, 1)
        )
        
        # 计算基础边框和padding占用的宽度
        border_width = 4  # 左右边框各2个字符
        padding_width = len(columns) * 2  # 每列左右padding各1个字符
        available_width = term_width - border_width - padding_width
        
        # 根据可用宽度决定显示哪些列
        current_width = 0
        added_columns = []
        
        # 按优先级添加列
        for priority in range(1, 5):
            for col_name, min_width, col_priority in columns:
                if col_priority == priority:
                    if current_width + min_width <= available_width:
                        results_table.add_column(col_name, style="bold green", width=min_width)
                        current_width += min_width
                        added_columns.append(col_name)
        
        # 添加数据行
        for match in matches:
            if not isinstance(match, dict):
                continue
            
            row_data = []
            for col_name, min_width, _ in columns:
                if col_name not in added_columns:
                    continue
                
                if col_name == "IP":
                    row_data.append(match.get("ip_str", "N/A"))
                elif col_name == "Port":
                    row_data.append(str(match.get("port", "N/A")))
                elif col_name == "URL":
                    ip = match.get("ip_str", "N/A")
                    port = match.get("port", "N/A")
                    protocol = "https" if port in ["443", "8443"] else "http"
                    row_data.append(f"{protocol}://{ip}:{port}")
                elif col_name == "Organization":
                    org = match.get("org")
                    # 确保 org 不为 None
                    if org is None:
                        row_data.append("N/A")
                    else:
                        org = self.truncate(str(org), 27)
                        row_data.append(org)
                elif col_name == "Location":
                    location_data = match.get("location", {})
                    country = location_data.get("country_name", "N/A")
                    city = location_data.get("city", "N/A")
                    longitude = location_data.get("longitude", "N/A")
                    latitude = location_data.get("latitude", "N/A")
                    location = f"{country}, {city}\n({latitude}°N, {longitude}°E)"
                    row_data.append(location)
                elif col_name == "Timestamp (UTC+8)":
                    timestamp = match.get("timestamp")
                    if timestamp:
                        try:
                            ts = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                            ts = ts.astimezone(timezone(timedelta(hours=8)))
                            row_data.append(ts.strftime("%Y-%m-%d %H:%M:%S"))
                        except:
                            row_data.append("N/A")
                    else:
                        row_data.append("N/A")
            
            results_table.add_row(*row_data)
        
        # 显示表格和统计信息
        console.print(results_table)
        console.print()
        
        # 显示查询信息和统计
        total_matches = len(matches)
        if limit and limit > 0:
            console.print(
                f"[grey]Total Results: {total} | Retrieved: {total_matches} | Displayed: {len(matches)} (limited by --limit)[/grey]"
            )
        else:
            console.print(
                f"[grey]Total Results: {total} | Matches Retrieved: {total_matches}[/grey]"
            )
        console.print()


def main():
    script_name = os.path.basename(sys.argv[0])
    
    # Define examples and notes
    examples = [
        ("Initialize API key", "init YOUR_API_KEY"),
        ("Basic search", "search \"apache country:cn\""),
        ("Cache control", "search \"nginx port:443\" --no-cache"),
        ("Complex query", "search 'http.favicon.hash:\"-620522584\" country:\"cn\"' --delete-cache"),
        ("Show API info", "info"),
        ("Calculate favicon hash", "hash /path/to/favicon.ico"),
        ("Calculate favicon hash from URL", "hash https://example.com/favicon.ico"),
        ("Debug mode", "search \"nginx\" --log")
    ]
    
    notes = [
        "Will automatically use API key from ~/.config/shodan/api_key if available",
        "Custom config is stored in ~/.shodan/config.json",
        "Search results are cached in ~/.shodan/result/",
        "Use --no-cache to skip cache, --delete-cache to refresh cache",
        "For complex searches, enclose the entire query in quotes",
        "Use 'hash' command to calculate favicon hash for Shodan searches",
        "Use --log to enable debug mode for troubleshooting"
    ]

    parser = ColoredArgumentParser(
        description=CLIStyle.color('Shodan CLI Tool', CLIStyle.COLORS["TITLE"]),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=create_example_text(script_name, examples, notes)
    )

    # 添加全局参数
    parser.add_argument("--log", action="store_true", help="Enable debug logging")

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # init command
    init_parser = subparsers.add_parser("init", help="Initialize API key")
    init_parser.add_argument("api_key", help="Shodan API key")

    # search command
    search_parser = subparsers.add_parser(
        "search",
        help="Search Shodan",
        description=CLIStyle.color("Search Shodan for specific terms", CLIStyle.COLORS["TITLE"]),
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
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    search_parser.add_argument(
        "query", nargs="+", help="Search query (use quotes for complex queries)"
    )
    search_parser.add_argument(
        "--page", type=int, default=1, help="Page number (Paid API only, default: 1)"
    )
    search_parser.add_argument(
        "--no-cache", action="store_true", help="Do not use or save cache"
    )
    search_parser.add_argument(
        "--delete-cache", action="store_true", help="Delete and refresh cache"
    )
    search_parser.add_argument(
        "--limit", type=int, help="Limit the number of results to display"
    )

    # info command
    subparsers.add_parser("info", help="Show Shodan API information and config")

    # hash command
    hash_parser = subparsers.add_parser(
        "hash", 
        help="Calculate favicon hash for Shodan searches",
        description=CLIStyle.color("Calculate favicon hash for Shodan searches", CLIStyle.COLORS["TITLE"]),
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
        "path_or_url", 
        help="Path to local favicon file or URL (can be website URL)"
    )

    args = parser.parse_args()

    # 设置全局调试模式
    global DEBUG_MODE
    DEBUG_MODE = args.log
    
    if DEBUG_MODE:
        print(CLIStyle.color("Debug mode enabled", CLIStyle.COLORS["CONTENT"]))

    if not args.command:
        parser.print_help()
        return

    client = ShodanClient()

    if args.command == "init":
        client.init_api_key(args.api_key)

    elif args.command == "search":
        query = " ".join(args.query)
        debug("Search query", query=query, page=args.page, no_cache=args.no_cache, delete_cache=args.delete_cache)
        
        results = client.search(
            query,
            page=args.page,
            no_cache=args.no_cache,
            delete_cache=args.delete_cache,
        )

        # Strict result validation
        if not results:
            debug("No results found", results=results)
            print(CLIStyle.color("No results found", CLIStyle.COLORS["ERROR"]))
            return

        matches = results.get("matches", [])
        debug("Matches count", count=len(matches) if matches else 0)
        
        if not matches:
            print(CLIStyle.color("No matches found", CLIStyle.COLORS["ERROR"]))
            return

        # Apply limit if specified
        total_matches = len(matches)
        if args.limit and args.limit > 0:
            matches = matches[: args.limit]

        client.display_results(matches, results.get("total", 0), args.limit)

    elif args.command == "info":
        try:
            client.show_info()
        except Exception as e:
            print(CLIStyle.color(f"Error displaying info: {str(e)}", CLIStyle.COLORS["ERROR"]))
            return

    elif args.command == "hash":
        try:
            calculate_favicon_hash(args.path_or_url)
        except Exception as e:
            print(CLIStyle.color(f"Error calculating favicon hash: {str(e)}", CLIStyle.COLORS["ERROR"]))
            return


def calculate_favicon_hash(path_or_url):
    """Calculate Shodan favicon hash from file path or URL"""
    try:
        debug("Calculating favicon hash", path_or_url=path_or_url)
        # Determine if input is a URL or file path
        is_url = path_or_url.lower().startswith(('http://', 'https://'))
        favicon_source = path_or_url  # 默认使用输入路径作为来源
        
        if is_url:
            print(CLIStyle.color(f"Downloading from URL: {path_or_url}", CLIStyle.COLORS["CONTENT"]))
            try:
                # First check if the URL directly points to a favicon
                response = requests.get(path_or_url, timeout=10)
                if response.status_code != 200:
                    debug("HTTP error", status_code=response.status_code)
                    print(CLIStyle.color(f"Error: HTTP status code {response.status_code}", CLIStyle.COLORS["ERROR"]))
                    return
                
                # Check if the content is a valid favicon
                content_type = response.headers.get('Content-Type', '').lower()
                content = response.content
                is_favicon = _is_valid_favicon_content(content_type, content)
                debug("Content validation", content_type=content_type, is_favicon=is_favicon, content_length=len(content))
                
                # If not a direct favicon URL, try to find favicon at the website
                if not is_favicon:
                    base_url = _get_base_url(path_or_url)
                    print(CLIStyle.color(f"URL is not a direct favicon. Trying to find favicon at: {base_url}", CLIStyle.COLORS["CONTENT"]))
                    
                    # Try standard favicon locations
                    favicon_paths = [
                        '/favicon.ico', 
                        '/favicon.png', 
                        '/assets/favicon.ico', 
                        '/images/favicon.ico',
                        '/static/favicon.ico',
                        '/public/favicon.ico'
                    ]
                    
                    favicon_found = False
                    for path in favicon_paths:
                        try:
                            favicon_url = urllib.parse.urljoin(base_url, path)
                            print(CLIStyle.color(f"Trying: {favicon_url}", CLIStyle.COLORS["CONTENT"]))
                            favicon_response = requests.get(favicon_url, timeout=10)
                            
                            if favicon_response.status_code == 200:
                                favicon_content_type = favicon_response.headers.get('Content-Type', '').lower()
                                if _is_valid_favicon_content(favicon_content_type, favicon_response.content):
                                    content = favicon_response.content
                                    favicon_found = True
                                    favicon_source = favicon_url  # 更新favicon来源
                                    print(CLIStyle.color(f"Found valid favicon at: {favicon_url}", CLIStyle.COLORS["CONTENT"]))
                                    break
                        except Exception as e:
                            print(CLIStyle.color(f"Error trying {path}: {str(e)}", CLIStyle.COLORS["ERROR"]))
                            continue
                    
                    # If still not found, try to parse HTML to find favicon link
                    if not favicon_found:
                        try:
                            print(CLIStyle.color("Searching for favicon link in HTML...", CLIStyle.COLORS["CONTENT"]))
                            soup = BeautifulSoup(response.content, 'html.parser')
                            
                            # Look for favicon in link tags
                            favicon_links = []
                            for link in soup.find_all('link'):
                                rel = link.get('rel', [])
                                if isinstance(rel, str):
                                    rel = [rel]
                                
                                if any(r.lower() in ['icon', 'shortcut icon'] for r in rel):
                                    href = link.get('href')
                                    if href:
                                        favicon_links.append(href)
                            
                            # Try each found favicon link
                            for href in favicon_links:
                                try:
                                    # Handle relative URLs
                                    if not href.startswith(('http://', 'https://')):
                                        href = urllib.parse.urljoin(base_url, href)
                                    
                                    print(CLIStyle.color(f"Trying HTML link: {href}", CLIStyle.COLORS["CONTENT"]))
                                    favicon_response = requests.get(href, timeout=10)
                                    
                                    if favicon_response.status_code == 200:
                                        favicon_content_type = favicon_response.headers.get('Content-Type', '').lower()
                                        if _is_valid_favicon_content(favicon_content_type, favicon_response.content):
                                            content = favicon_response.content
                                            favicon_found = True
                                            favicon_source = href  # 更新favicon来源
                                            print(CLIStyle.color(f"Found valid favicon at: {href}", CLIStyle.COLORS["CONTENT"]))
                                            break
                                except Exception as e:
                                    print(CLIStyle.color(f"Error trying HTML link {href}: {str(e)}", CLIStyle.COLORS["ERROR"]))
                                    continue
                        except ImportError:
                            print(CLIStyle.color("BeautifulSoup not installed. Skipping HTML parsing.", CLIStyle.COLORS["ERROR"]))
                        except Exception as e:
                            print(CLIStyle.color(f"Error parsing HTML: {str(e)}", CLIStyle.COLORS["ERROR"]))
                    
                    if not favicon_found:
                        print(CLIStyle.color("Error: Could not find a valid favicon at the URL or standard locations", CLIStyle.COLORS["ERROR"]))
                        print(CLIStyle.color("Please provide a direct link to a favicon file (.ico, .png)", CLIStyle.COLORS["ERROR"]))
                        return
            except Exception as e:
                print(CLIStyle.color(f"Error downloading favicon: {str(e)}", CLIStyle.COLORS["ERROR"]))
                return
        else:
            # Local file
            if not os.path.exists(path_or_url):
                print(CLIStyle.color(f"Error: File not found: {path_or_url}", CLIStyle.COLORS["ERROR"]))
                return
                
            print(CLIStyle.color(f"Reading favicon from file: {path_or_url}", CLIStyle.COLORS["CONTENT"]))
            with open(path_or_url, 'rb') as f:
                content = f.read()
            
            # Check if the file is a valid favicon
            if not _is_valid_favicon_file(path_or_url, content):
                print(CLIStyle.color("Error: The file does not appear to be a valid favicon", CLIStyle.COLORS["ERROR"]))
                print(CLIStyle.color("Please provide a valid favicon file (.ico, .png)", CLIStyle.COLORS["ERROR"]))
                return
        
        # 在计算哈希值之前显示favicon来源
        print(CLIStyle.color(f"Using favicon from: {favicon_source}", CLIStyle.COLORS["CONTENT"]))
        
        # Calculate hash using Shodan's updated method
        print(CLIStyle.color("Calculating favicon hash...", CLIStyle.COLORS["CONTENT"]))
        b64_content = base64.encodebytes(content)
        hash_value = mmh3.hash(b64_content)
        
        # Display results - simplified output without panel
        console = Console()

        console.print(f"[bold red]Favicon Hash:[/bold red] [bold green]{hash_value}[/bold green]")
        console.print(
            "[bold cyan]Example Shodan search query:[/bold cyan]", 
            f"[yellow]http.favicon.hash:\"{hash_value}\"[/yellow]"
        )
        
    except Exception as e:
        debug("Error in calculate_favicon_hash", error=str(e))
        print(CLIStyle.color(f"Error calculating hash: {str(e)}", CLIStyle.COLORS["ERROR"]))
        return

def _is_valid_favicon_content(content_type, content):
    """Check if content appears to be a valid favicon"""
    # Check content type
    valid_types = ['image/x-icon', 'image/vnd.microsoft.icon', 'image/png', 'image/ico']
    content_type_valid = any(valid_type in content_type for valid_type in valid_types)
    
    # Check file signatures
    is_ico = content.startswith(b'\x00\x00\x01\x00')  # ICO file signature
    is_png = content.startswith(b'\x89PNG\r\n\x1a\n')  # PNG file signature
    
    # A valid favicon should have either a correct content type or a valid file signature
    # Also check minimum size to avoid empty files
    if (content_type_valid or is_ico or is_png) and len(content) > 16:
        return True
    
    return False

def _is_valid_favicon_file(file_path, content):
    """Check if file appears to be a valid favicon"""
    # Check file extension
    valid_extensions = ['.ico', '.png']
    has_valid_extension = any(file_path.lower().endswith(ext) for ext in valid_extensions)
    
    # Check file signatures
    is_ico = content.startswith(b'\x00\x00\x01\x00')  # ICO file signature
    is_png = content.startswith(b'\x89PNG\r\n\x1a\n')  # PNG file signature
    
    # A valid favicon file should have both a valid extension and a valid file signature
    # Also check minimum size to avoid empty files
    if has_valid_extension and (is_ico or is_png) and len(content) > 16:
        return True
    
    return False

def _get_base_url(url):
    """Extract base URL from a given URL"""
    parsed = urllib.parse.urlparse(url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"
    return base_url


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(CLIStyle.color("\nOperation cancelled by user", CLIStyle.COLORS["ERROR"]))
        sys.exit(0)
    except Exception as e:
        if DEBUG_MODE:
            import traceback
            traceback.print_exc()
        print(CLIStyle.color(f"\nError: {str(e)}", CLIStyle.COLORS["ERROR"]))
        sys.exit(1)
