# -*- coding: utf-8 -*-
# Thanks to https://ip-api.com for providing the API

import subprocess
import json
import argparse
import os
import sys


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
    BASE_URL = "http://ip-api.com"


def execute_curl(url):
    """Execute curl command and return response"""
    try:
        result = subprocess.run(
            ["curl", "-s", "--connect-timeout", "5", "-m", "10", url],
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            raise Exception(f"Request failed: {result.stderr}")
    except subprocess.TimeoutExpired:
        print(CLIStyle.color("\nError: Request timed out", CLIStyle.COLORS["ERROR"]))
        print(
            CLIStyle.color(
                "Please check your network connection or try again later",
                CLIStyle.COLORS["WARNING"],
            )
        )
        exit(1)
    except Exception as e:
        print(
            CLIStyle.color(
                f"\nError executing curl command: {str(e)}", CLIStyle.COLORS["ERROR"]
            )
        )
        print(
            CLIStyle.color(
                "Please make sure curl is installed and network is accessible",
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
        url = f"{Config.BASE_URL}/json"
        if self.args["ip"] != "":
            self.ip = self.args["ip"]
            url += f"/{self.ip}"
        response = execute_curl(url)
        response_json = json.loads(response)

        if response_json.get("status", "") == "success":
            print(CLIStyle.color("IP with Location:", CLIStyle.COLORS["TITLE"]))
        else:
            print(CLIStyle.color("IP Query Result:", CLIStyle.COLORS["TITLE"]))

        self.ip = response_json.get("query", self.ip)
        format_dict(response_json, indent=2, exclude_keys=[])


def format_dict(data: dict, indent=0, exclude_keys=None):
    """Format dictionary output"""
    if exclude_keys is None:
        exclude_keys = ["status", "query"]

    for key, value in data.items():
        if key in exclude_keys:
            continue
        if isinstance(value, dict):
            print(
                " " * indent + f"{CLIStyle.color(key, CLIStyle.COLORS['SUB_TITLE'])}:"
            )
            format_dict(value, indent + 4, exclude_keys)
        else:
            # 根据值的类型使用不同的颜色
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
    """Check if IP address is valid and extract it

    Args:
        ip (str): Input IP address string

    Returns:
        str: Extracted valid IP address

    Raises:
        AssertionError: When no valid IP address is found
    """
    import re

    assert re.search(r"\d+\.\d+\.\d+\.\d+", ip), "No valid IP address found"
    return re.search(r"\d+\.\d+\.\d+\.\d+", ip).group()


def main():
    script_name = os.path.basename(sys.argv[0])

    # Define examples and notes
    examples = [
        ("Check local IP", ""),
        ("Check specific IP", "-i 8.8.8.8"),
        ("Show curl command", "-c"),
        ("Output as JSON", "-f json"),
    ]

    notes = [
        "Shows IP address information",
        "Includes country/region, city, ISP",
        "Shows geographical location (lat/long)",
        "Displays timezone information",
    ]

    ap = ColoredArgumentParser(
        description=CLIStyle.color(
            "IP Address Lookup Tool - Powered by ip-api.com", CLIStyle.COLORS["TITLE"]
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=create_example_text(script_name, examples, notes),
    )

    ap.add_argument(
        "-i",
        "--ip",
        default="",
        type=str,
        metavar=CLIStyle.color("IP", CLIStyle.COLORS["CONTENT"]),
        help=CLIStyle.color("Specify IP address to lookup", CLIStyle.COLORS["CONTENT"]),
    )
    ap.add_argument(
        "-c",
        "--cmd",
        action="store_true",
        help=CLIStyle.color(
            "Show corresponding curl command", CLIStyle.COLORS["CONTENT"]
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

    if args["cmd"]:
        print(CLIStyle.color("curl command:", CLIStyle.COLORS["TITLE"]))
        print(
            CLIStyle.color(
                f"{' ' * 2}curl {Config.BASE_URL}/json/<ip>", CLIStyle.COLORS["CONTENT"]
            )
        )
        exit()

    if args["ip"]:
        args["ip"] = check_ip_and_return_str(args["ip"])

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
