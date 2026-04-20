# -*- coding: utf-8 -*-
# pip install colorama requests
# Thanks to https://ipapi.co for providing the API

import json
import argparse
import os
import sys
import requests

if sys.platform == "win32":
    from colorama import init as colorama_init

    colorama_init(autoreset=True)


# CLI Style Template
class CLIStyle:
    """CLI Tool Style Configuration"""

    COLORS = {
        "TITLE": 7,  # Cyan - Main Title
        "SUB_TITLE": 2,  # Red - Subtitle
        "CONTENT": 3,  # Green - Content
        "EXAMPLE": 7,  # Cyan - Examples
        "WARNING": 4,  # Yellow - Warnings
        "ERROR": 2,  # Red - Errors
    }

    @staticmethod
    def color(text: str = "", color: int = COLORS["CONTENT"]) -> str:
        """Unified color function"""
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

        formatter.add_text(
            CLIStyle.color("\nOptional Arguments:", CLIStyle.COLORS["TITLE"])
        )
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


class Config:
    BASE_URL = "https://ipapi.co"


def execute_request(url, timeout=5):
    """Execute HTTP request and return response text"""
    try:
        response = requests.get(
            url,
            timeout=(min(timeout, 5), max(timeout, 10)),
            headers={
                "Accept": "application/json",
                "User-Agent": "ip-status.py/1.0 (+requests)",
            },
        )
        response.raise_for_status()
        return response.text.strip()
    except requests.Timeout:
        print(CLIStyle.color("\nError: Request timed out", CLIStyle.COLORS["ERROR"]))
        print(
            CLIStyle.color(
                "Please check your network connection or try again later",
                CLIStyle.COLORS["WARNING"],
            )
        )
        exit(1)
    except requests.RequestException as e:
        print(
            CLIStyle.color(
                f"\nError requesting API: {str(e)}", CLIStyle.COLORS["ERROR"]
            )
        )
        print(
            CLIStyle.color(
                "Please make sure requests is installed and network is accessible",
                CLIStyle.COLORS["WARNING"],
            )
        )
        exit(1)


class IPRSSClient:
    def __init__(self, args):
        self.ip = ""
        self.args = args

    def get_ip_with_location(self):
        """Get public IP address with location details"""
        if self.args["ip"] != "":
            self.ip = self.args["ip"]
            url = f"{Config.BASE_URL}/{self.ip}/json/"
        else:
            url = f"{Config.BASE_URL}/json/"
        response = execute_request(url, timeout=self.args["timeout"])
        response_json = json.loads(response)

        if response_json.get("ip"):
            print(CLIStyle.color("IP with Location:", CLIStyle.COLORS["TITLE"]))
        else:
            print(CLIStyle.color("IP Query Result:", CLIStyle.COLORS["TITLE"]))

        self.ip = response_json.get("ip", self.ip)
        format_dict(response_json, indent=2, exclude_keys=[])


def format_dict(data: dict, indent=0, exclude_keys=None):
    """Format dictionary output"""
    if exclude_keys is None:
        exclude_keys = []

    for key, value in data.items():
        if key in exclude_keys:
            continue
        if isinstance(value, dict):
            print(
                " " * indent + f"{CLIStyle.color(key, CLIStyle.COLORS['SUB_TITLE'])}:"
            )
            format_dict(value, indent + 4, exclude_keys)
        else:
            if isinstance(value, bool):
                value_color = CLIStyle.COLORS["WARNING"]
            elif isinstance(value, (int, float)):
                value_color = CLIStyle.COLORS["EXAMPLE"]
            else:
                value_color = CLIStyle.COLORS["CONTENT"]

            print(
                " " * indent
                + f"{CLIStyle.color(key, CLIStyle.COLORS['SUB_TITLE'])}: {CLIStyle.color(str(value), value_color)}"
            )


def check_ip_and_return_str(ip: str) -> str:
    """Check if IP address is valid and extract it, or resolve domain

    Args:
        ip (str): Input IP address string or domain name

    Returns:
        str: Extracted valid IP address

    Raises:
        AssertionError: When no valid IP address is found
    """
    import re
    import socket

    ip_match = re.search(r"\d+\.\d+\.\d+\.\d+", ip)
    if ip_match:
        return ip_match.group()

    domain = re.sub(r"^(https?://)?", "", ip)
    domain = re.sub(r"[:/].*$", "", domain)

    try:
        resolved_ip = socket.gethostbyname(domain)
        print(
            CLIStyle.color(
                f"Resolved {domain} -> {resolved_ip}", CLIStyle.COLORS["WARNING"]
            )
        )
        return resolved_ip
    except socket.gaierror:
        raise AssertionError(f"Cannot resolve domain or find valid IP: {domain}")


def main():
    script_name = os.path.basename(sys.argv[0])

    examples = [
        ("Check your own IP", ""),
        ("Check specific IP", "8.8.8.8"),
        ("Show request URL", "-c"),
        ("Output as JSON", "-f json"),
    ]

    notes = [
        "Shows IP address information",
        "Includes country/region, city, ISP",
        "Shows geographical location (lat/long)",
        "Displays timezone information",
        "Use position argument for specific IP lookup",
    ]

    ap = ColoredArgumentParser(
        description=CLIStyle.color(
            "IP Address Lookup Tool - Powered by ipapi.co", CLIStyle.COLORS["TITLE"]
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=create_example_text(script_name, examples, notes),
    )

    ap.add_argument(
        "ip",
        nargs="?",
        type=str,
        metavar=CLIStyle.color("IP", CLIStyle.COLORS["CONTENT"]),
        help=CLIStyle.color("Specify IP address to lookup", CLIStyle.COLORS["CONTENT"]),
    )
    ap.add_argument(
        "-c",
        "--cmd",
        action="store_true",
        help=CLIStyle.color(
            "Show corresponding request URL", CLIStyle.COLORS["CONTENT"]
        ),
    )
    ap.add_argument(
        "-f",
        "--format",
        choices=["text", "json", "csv"],
        default="text",
        help=CLIStyle.color(
            "Specify output format (default: text)", CLIStyle.COLORS["CONTENT"]
        ),
    )
    ap.add_argument(
        "-t",
        "--timeout",
        type=int,
        default=5,
        metavar=CLIStyle.color("SECONDS", CLIStyle.COLORS["CONTENT"]),
        help=CLIStyle.color(
            "Set request timeout (default: 5s)", CLIStyle.COLORS["CONTENT"]
        ),
    )

    args = vars(ap.parse_args())

    if args["ip"]:
        args["ip"] = check_ip_and_return_str(args["ip"])
    else:
        args["ip"] = ""

    if args["cmd"]:
        print(CLIStyle.color("Request URL:", CLIStyle.COLORS["TITLE"]))
        if args["ip"]:
            print(
                CLIStyle.color(
                    f"{' ' * 2}{Config.BASE_URL}/{args['ip']}/json/",
                    CLIStyle.COLORS["CONTENT"],
                )
            )
        else:
            print(
                CLIStyle.color(
                    f"{' ' * 2}{Config.BASE_URL}/json/", CLIStyle.COLORS["CONTENT"]
                )
            )
        exit()

    client = IPRSSClient(args)
    client.get_ip_with_location()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(CLIStyle.color("\nOperation cancelled by user", CLIStyle.COLORS["ERROR"]))
        sys.exit(0)
    except Exception as e:
        print(CLIStyle.color(f"\nError: {str(e)}", CLIStyle.COLORS["ERROR"]))
        sys.exit(1)
