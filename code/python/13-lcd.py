# -*- coding: utf-8 -*-
# pip install argparse

import argparse
import json
import os
import sys
from typing import List

# Global variables
DEBUG_MODE = False
VERSION = "1.1.4"

# Config file path
if os.environ.get('USERPROFILE') is not None:
    windows_user_home = os.environ.get("USERPROFILE").replace("\\", "/")
    CONFIG_FILE = f'{windows_user_home}/.lcd-path'
elif os.environ.get('HOME') is not None:
    CONFIG_FILE = f'{os.environ.get("HOME")}/.lcd-path'
else:
    CONFIG_FILE = f'{os.path.dirname(os.path.abspath(__file__))}/.lcd-path'

# CLI colors
CLI_COLORS = {
    "TITLE": 7,      # Cyan - Main title
    "SUB_TITLE": 2,  # Red - Subtitle
    "CONTENT": 3,    # Green - Normal content
    "EXAMPLE": 6,    # Purple - Examples
    "WARNING": 4,    # Yellow - Warnings
    "ERROR": 2,      # Red - Errors
    "PATH": 3,       # Green - Paths
    "NUMBER": 4,     # Yellow - Numbers
}


def color(text: str, color_code: int = 0) -> str:
    """
    Add color to text
    ```python
    color(
        text,          # Text to colorize
        color_code=0   # Color code (0-8)
    )

    return = Colorized text string
    ```
    """
    color_table = {
        0: "{}",                    # No color
        1: "\033[1;30m{}\033[0m",   # Bold black
        2: "\033[1;31m{}\033[0m",   # Bold red
        3: "\033[1;32m{}\033[0m",   # Bold green
        4: "\033[1;33m{}\033[0m",   # Bold yellow
        5: "\033[1;34m{}\033[0m",   # Bold blue
        6: "\033[1;35m{}\033[0m",   # Bold purple
        7: "\033[1;36m{}\033[0m",   # Bold cyan
        8: "\033[1;37m{}\033[0m",   # Bold white
    }
    return color_table[color_code].format(clean_path(text) if os.path.sep in text else text)


def debug(*args, file=None, append=True, **kwargs) -> None:
    """
    Print debug information with file and line number
    ```python
    debug(
        'Hello',         # Arg 1 to print
        'World',         # Arg 2 to print
        file='debug.log', # Output file path (default: None)
        append=True,     # Append to file (default: True)
        **kwargs         # Key-value pairs to print
    )
    ```
    """
    if not DEBUG_MODE:
        return
        
    import inspect
    import re
    frame = inspect.currentframe().f_back
    info = inspect.getframeinfo(frame)
    
    output = f"{color(os.path.basename(info.filename), CLI_COLORS['CONTENT'])}: {color(info.lineno, CLI_COLORS['NUMBER'])} {color('|', CLI_COLORS['TITLE'])} "
    
    for i, arg in enumerate(args):
        arg_str = str(arg)
        output += f"{color(arg_str, CLI_COLORS['ERROR'])} "
    
    for k, v in kwargs.items():
        output += f"{color(k+'=', CLI_COLORS['TITLE'])}{color(str(v), CLI_COLORS['ERROR'])} "
    
    output += '\n'
    
    if file:
        mode = 'a' if append else 'w'
        with open(file, mode) as f:
            clean_output = re.sub(r'\033\[\d+;\d+m|\033\[0m', '', output)
            f.write(clean_output)
    else:
        print(output, end='')


def divider(text: str = None, char: str = '=') -> None:
    """Print a divider line with optional text"""
    divider_str = char * 10
    text = text if text else 'Divider'
    print(f"{color(divider_str, CLI_COLORS['TITLE'])} {text} {color(divider_str, CLI_COLORS['TITLE'])}")


def clean_path(path: str) -> str:
    """Clean path string, replace backslashes with forward slashes and strip whitespace"""
    return path.replace('\\', '/').strip()


class PathManager:
    """Path Manager - Handles storage, deletion and display of paths"""
    
    def __init__(self, config_file: str):
        """Initialize the path manager"""
        self.config_file = config_file
        self.paths = self.load_paths()
        
    def load_paths(self) -> List[str]:
        """Load path list from config file"""
        if not os.path.exists(self.config_file):
            with open(self.config_file, 'w') as file:
                json.dump([], file, indent=4)
            return []
            
        try:
            with open(self.config_file, 'r') as file:
                return json.load(file)
        except json.JSONDecodeError:
            print(color(f"Config file corrupted: {self.config_file}", CLI_COLORS["ERROR"]))
            print(color("Creating new config file...", CLI_COLORS["WARNING"]))
            with open(self.config_file, 'w') as file:
                json.dump([], file, indent=4)
            return []
            
    def save_paths(self) -> None:
        """Save path list to config file"""
        with open(self.config_file, 'w') as file:
            json.dump(self.paths, file, indent=4)
            
    def add_path(self, path: str, path_color: int) -> None:
        """Add new path to the list"""
        current_dir = os.getcwd()
        path = os.path.join(current_dir, path)
        path = os.path.abspath(path)
        path = clean_path(path)
        
        if path in self.paths:
            print(f"{color('|', CLI_COLORS['TITLE'])} Path [{color(path, path_color)}] already exists.")
        else:
            self.paths.append(path)
            self.save_paths()
            print(f"{color('|', CLI_COLORS['TITLE'])} Path [{color(path, path_color)}] added.")
            
    def delete_path(self, path: str, path_color: int, num: int = 0) -> None:
        """Delete path from the list"""
        if num != 0:
            if num > len(self.paths) or num <= 0:
                print(f"{color('|', CLI_COLORS['TITLE'])} Path number [{color(str(num), CLI_COLORS['NUMBER'])}] out of range.")
                return
            path = self.paths[num - 1]
        
        if path in self.paths:
            self.paths.remove(path)
            self.save_paths()
            print(f"{color('|', CLI_COLORS['TITLE'])} Path [{color(path, path_color)}] deleted.")
        else:
            print(f"{color('|', CLI_COLORS['TITLE'])} Path [{color(path, path_color)}] doesn't exist.")
            
    def list_paths(self, path_color: int, num: int = 0) -> None:
        """List all stored paths or a specific path by number"""
        if not self.paths:
            print(f"{color('|', CLI_COLORS['TITLE'])} No stored paths.")
            return
            
        if num != 0:
            if num > len(self.paths) or num <= 0:
                print(f"{color('|', CLI_COLORS['TITLE'])} Path number [{color(str(num), CLI_COLORS['NUMBER'])}] out of range.")
                return
                
            path = self.paths[num - 1]
            abs_path = os.path.abspath(path)
            print(f"{color(abs_path, path_color)}")
            return
            
        print(f"{color('Stored paths:', CLI_COLORS['TITLE'])}")
        for i, path in enumerate(self.paths, 1):
            abs_path = os.path.abspath(path)
            exists = "✓" if os.path.exists(abs_path) else "✗"
            status_color = CLI_COLORS['CONTENT'] if os.path.exists(abs_path) else CLI_COLORS['ERROR']
            print(f"{color('|', CLI_COLORS['TITLE'])} [{color(str(i), CLI_COLORS['NUMBER'])}] {color(exists, status_color)} {color(abs_path, path_color)}")
            
    def cd_to_path(self, num: int, path_color: int) -> None:
        """Output path for use with cd command"""
        if num <= 0 or num > len(self.paths):
            print(f"{color('|', CLI_COLORS['TITLE'])} Path number [{color(str(num), CLI_COLORS['NUMBER'])}] out of range.")
            return
            
        path = self.paths[num - 1]
        if not os.path.exists(path):
            print(f"{color('|', CLI_COLORS['TITLE'])} Warning: Path [{color(path, path_color)}] doesn't exist.", file=sys.stderr)
            
        # For use with external commands, just print the raw path without color
        # This allows commands like cd $(lcd -g 2) to work properly
        print(path)
        
    def show_config(self, path_color: int) -> None:
        """Show config file information"""
        print(f"{color('Config file:', CLI_COLORS['TITLE'])} {color(self.config_file, path_color)}")
        print(json.dumps(self.paths, indent=4, ensure_ascii=False))


def create_example_text() -> str:
    """Create formatted example text for help menu"""
    script_name = os.path.basename(sys.argv[0])
    
    examples = [
        ("Add current directory", "-a"),
        ("Add specific directory", "-a path/to/dir"),
        ("Delete path", "-d path/to/dir"),
        ("Delete path by number", "-d -n 2"),
        ("List all paths", "-l"),
        ("Show path number 3", "-l -n 3"),
        ("Go to path number 2", "-g 2"),
        ("Show config file", "-c"),
        ("Debug mode", "--debug"),
        ("Plain output (no colors)", "-p"),
    ]
    
    text = f'\n{color("Examples:", CLI_COLORS["SUB_TITLE"])}'
    
    for desc, cmd in examples:
        text += f'\n  {color(f"# {desc}", CLI_COLORS["EXAMPLE"])}'
        text += f'\n  {color(f"{script_name} {cmd}", CLI_COLORS["CONTENT"])}'
        text += '\n'
    
    notes = [
        "Set up cd functionality with alias: alias lcd='cd \"$(python /path/to/lcd.py -g $1)\"'",
        "For Bash/Zsh users: alias lcd='function _lcd(){ cd \"$(python /path/to/lcd.py -g $1 2>/dev/null)\"; };_lcd'",
        "Use -n parameter to specify path number",
        "Use --debug option to enable debug mode",
        "In the path list, ✓ means path exists, ✗ means path doesn't exist",
    ]
    
    text += f'\n{color("Notes:", CLI_COLORS["SUB_TITLE"])}'
    for note in notes:
        text += f'\n  {color(f"- {note}", CLI_COLORS["CONTENT"])}'
    
    return text


def create_help_text(parser: argparse.ArgumentParser) -> str:
    """Create formatted help text for the parser"""
    help_parts = []
    
    # Add description
    if parser.description:
        help_parts.append(color(parser.description, CLI_COLORS["TITLE"]))
        help_parts.append("")
    
    # Add usage
    prog_name = parser.prog
    help_parts.append(f"{color('Usage:', CLI_COLORS['TITLE'])} {prog_name} [OPTIONS]")
    help_parts.append("")
    
    # Add options
    help_parts.append(color("Options:", CLI_COLORS["TITLE"]))
    help_parts.extend([
        f"  {color('-h, --help', CLI_COLORS['SUB_TITLE'])}         Show this help message and exit",
        f"  {color('-a, --add', CLI_COLORS['SUB_TITLE'])} [PATH]   Store path, default is current directory",
        f"  {color('-d, --delete', CLI_COLORS['SUB_TITLE'])} [PATH]  Delete path from storage, default is current directory",
        f"  {color('-n, --num', CLI_COLORS['SUB_TITLE'])} NUMBER   Specify path number to operate on",
        f"  {color('-l, --list', CLI_COLORS['SUB_TITLE'])}         List all stored paths",
        f"  {color('-g, --goto', CLI_COLORS['SUB_TITLE'])} NUMBER  Output path by number for use with cd command",
        f"  {color('-c, --config', CLI_COLORS['SUB_TITLE'])}       Show config file path",
        f"  {color('-p, --plain', CLI_COLORS['SUB_TITLE'])}        Don't show colored output",
        f"  {color('--debug', CLI_COLORS['SUB_TITLE'])}            Enable debug mode",
        f"  {color('-v, --version', CLI_COLORS['SUB_TITLE'])}      Show program version"
    ])
    help_parts.append("")
    
    # Add examples
    help_parts.append(create_example_text())
    
    return "\n".join(help_parts)


def main():
    parser = argparse.ArgumentParser(
        description='LCD - Path Manager, store and quickly access common paths',
        add_help=False
    )
    
    # Global options
    parser.add_argument(
        '-h', '--help',
        action='store_true',
        help='Show this help message and exit'
    )
    parser.add_argument(
        '-a', '--add',
        nargs='?',
        const=os.getcwd(),
        type=str,
        help='Store path, default is current directory'
    )
    parser.add_argument(
        '-d', '--delete',
        nargs='?',
        const=os.getcwd(),
        type=str,
        help='Delete path from storage, default is current directory'
    )
    parser.add_argument(
        '-n', '--num',
        type=int,
        default=0,
        help='Specify path number to operate on'
    )
    parser.add_argument(
        '-l', '--list',
        action='store_true',
        help='List all stored paths'
    )
    parser.add_argument(
        '-g', '--goto',
        type=int,
        help='Output path by number for use with cd command'
    )
    parser.add_argument(
        '-c', '--config',
        action='store_true',
        help='Show config file path'
    )
    parser.add_argument(
        '-p', '--plain',
        action='store_true',
        help="Don't show colored output"
    )
    parser.add_argument(
        '--debug',
        action='store_true',
        help='Enable debug mode'
    )
    parser.add_argument(
        '-v', '--version',
        action='version',
        version=f'%(prog)s {VERSION}',
        help='Show program version'
    )
    
    args = parser.parse_args()
    
    # Show help
    if args.help:
        print(create_help_text(parser))
        return
    
    if args.debug:
        global DEBUG_MODE
        DEBUG_MODE = True
        debug("Debug mode enabled")
    
    path_color = 0 if args.plain else CLI_COLORS['PATH']
    path_manager = PathManager(CONFIG_FILE)
    
    if any([args.add, args.delete, args.list, args.goto, args.config, args.num]):
        if args.add:
            path_manager.add_path(args.add, path_color)
        elif args.delete:
            path_manager.delete_path(args.delete, path_color, args.num)
        elif args.list or args.num:
            path_manager.list_paths(path_color, args.num)
        elif args.goto:
            path_manager.cd_to_path(args.goto, path_color)
        elif args.config:
            path_manager.show_config(path_color)
    else:
        print(create_help_text(parser))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(color("\nOperation cancelled by user", CLI_COLORS["ERROR"]))
        sys.exit(0)
    except Exception as e:
        if DEBUG_MODE:
            import traceback
            traceback.print_exc()
        print(color(f"\nError: {str(e)}", CLI_COLORS["ERROR"]))
        sys.exit(1)
