# -*- coding: utf-8 -*-
# pip install toml

import os
import sys
import argparse
import toml
from typing import Dict, List, Optional, Any

# Global debug level
DEBUG_MODE = False

# Utility functions
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
    filename = clean_path(frame.f_code.co_filename)
    line_number = frame.f_lineno
    
    debug_info = f"[{filename}:{line_number}]"
    message_parts = [str(arg) for arg in args]
    
    if kwargs:
        kwargs_str = ", ".join([f"{k}={v}" for k, v in kwargs.items()])
        message_parts.append(f"({kwargs_str})")
    
    message = f"{color(debug_info, 6)} {' '.join(message_parts)}"
    
    if file:
        mode = 'a' if append else 'w'
        with open(file, mode, encoding='utf-8') as f:
            f.write(message + '\n')
    else:
        print(message)

# CLI Style class
class CLIStyle:
    """CLI tool unified style config"""
    
    COLORS = {
        "TITLE": 7,     # Cyan - Main title
        "SUB_TITLE": 2, # Red - Subtitle
        "CONTENT": 3,   # Green - Normal content
        "EXAMPLE": 7,   # Cyan - Example
        "WARNING": 4,   # Yellow - Warning
        "ERROR": 2,     # Red - Error
    }
    
    @staticmethod
    def color(text: str = "", color: int = None) -> str:
        """Unified color processing function"""
        if color is None:
            color = CLIStyle.COLORS["CONTENT"]
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

        formatter.add_text(
            CLIStyle.color("\nOptions:", CLIStyle.COLORS["TITLE"])
        )
        for action_group in self._action_groups:
            formatter.start_section(action_group.title)
            formatter.add_arguments(action_group._group_actions)
            formatter.end_section()

        if self.epilog:
            formatter.add_text(self.epilog)

        return formatter.format_help()

def create_example_text(script_name: str, examples: List[tuple], notes: Optional[List[str]] = None) -> str:
    """Create unified example text"""
    text = f"\n{CLIStyle.color('Examples:', CLIStyle.COLORS['SUB_TITLE'])}"

    for desc, cmd in examples:
        text += f"\n  {CLIStyle.color(f'# {desc}', CLIStyle.COLORS['EXAMPLE'])}"
        text += f"\n  {CLIStyle.color(f'{script_name} {cmd}', CLIStyle.COLORS['CONTENT'])}"
        text += "\n"

    if notes:
        text += f"\n{CLIStyle.color('Notes:', CLIStyle.COLORS['SUB_TITLE'])}"
        for note in notes:
            text += f"\n  {CLIStyle.color(f'- {note}', CLIStyle.COLORS['CONTENT'])}"

    return text

# Main class definitions
class TLDRParser:
    """TLDR configuration file parser"""
    
    def __init__(self, config_dir: str = None):
        """Initialize TLDR parser with configuration directory"""
        self.config_dir = config_dir or os.path.expanduser("~/.config/tldr")
        debug("Initialized TLDRParser", config_dir=self.config_dir)
    
    def find_config_file(self, command: str) -> Optional[str]:
        """
        Find configuration file for given command
        ```python
        find_config_file(
            "ip"    # Command name to search for
        )
        
        return = "/path/to/ip.tldr" or None
        ```
        """
        config_file = os.path.join(self.config_dir, f"{command}.tldr")
        debug("Looking for config file", path=config_file)
        
        if os.path.exists(config_file):
            return config_file
        
        # Also try current directory
        local_config = f"{command}.tldr"
        if os.path.exists(local_config):
            debug("Found local config file", path=local_config)
            return local_config
        
        return None
    
    def parse_config(self, config_file: str) -> Optional[Dict[str, Any]]:
        """
        Parse TLDR configuration file
        ```python
        parse_config(
            "/path/to/ip.tldr"    # Path to configuration file
        )
        
        return = {
            "meta": {...},
            "examples": [...]
        } or None
        ```
        """
        try:
            debug("Parsing config file", file=config_file)
            with open(config_file, 'r', encoding='utf-8') as f:
                config = toml.load(f)
            
            # Validate required sections
            if 'meta' not in config:
                print(CLIStyle.color(f"Error: Missing 'meta' section in {config_file}", CLIStyle.COLORS["ERROR"]))
                return None
            
            if 'examples' not in config:
                print(CLIStyle.color(f"Warning: No 'examples' section in {config_file}", CLIStyle.COLORS["WARNING"]))
                config['examples'] = []
            
            debug("Config parsed successfully", examples_count=len(config['examples']))
            return config
            
        except Exception as e:
            print(CLIStyle.color(f"Error parsing config file {config_file}: {str(e)}", CLIStyle.COLORS["ERROR"]))
            return None
    
    def format_output(self, config: Dict[str, Any]) -> str:
        """
        Format configuration data for display
        ```python
        format_output(
            {...}    # Parsed configuration dictionary
        )
        
        return = "formatted output string"
        ```
        """
        meta = config.get('meta', {})
        examples = config.get('examples', [])
        
        output = []
        
        # Header section
        name = meta.get('name', 'Unknown')
        description = meta.get('description', 'No description available')
        url = meta.get('url', '')
        
        output.append(CLIStyle.color(f"{name}: {description}", CLIStyle.COLORS["TITLE"]))
        if url:
            output.append(CLIStyle.color(f"url: {url}", CLIStyle.COLORS["CONTENT"]))
        output.append("")
        
        # Usage section
        output.append(CLIStyle.color("usage:", CLIStyle.COLORS["SUB_TITLE"]))
        output.append("")
        
        # Examples
        for i, example in enumerate(examples, 1):
            title = example.get('title', f'Example {i}')
            command = example.get('command', '')
            desc = example.get('description', '')
            
            output.append(CLIStyle.color(f"{i}. {title}", CLIStyle.COLORS["CONTENT"]))
            if desc:
                output.append(CLIStyle.color(f"   {desc}", CLIStyle.COLORS["CONTENT"]))
            output.append(CLIStyle.color(f"`{command}`", CLIStyle.COLORS["EXAMPLE"]))
            output.append("")
        
        return "\n".join(output)

class TLDRTool:
    """Main TLDR tool class"""
    
    def __init__(self, config_dir: str = None):
        """Initialize TLDR tool"""
        self.parser = TLDRParser(config_dir)
        debug("Initialized TLDRTool")
    
    def show_help(self, command: str) -> bool:
        """
        Show help for specified command
        ```python
        show_help(
            "ip"    # Command to show help for
        )
        
        return = True if successful, False otherwise
        ```
        """
        debug("Showing help for command", command=command)
        
        config_file = self.parser.find_config_file(command)
        if not config_file:
            print(CLIStyle.color(f"Error: No configuration found for command '{command}'", CLIStyle.COLORS["ERROR"]))
            print(CLIStyle.color(f"Looking for: {command}.tldr in {self.parser.config_dir} or current directory", CLIStyle.COLORS["CONTENT"]))
            return False
        
        config = self.parser.parse_config(config_file)
        if not config:
            return False
        
        output = self.parser.format_output(config)
        print(output)
        return True
    
    def list_available(self) -> None:
        """
        List all available TLDR configurations
        ```python
        list_available()
        
        return = None
        ```
        """
        debug("Listing available configurations")
        
        if not os.path.exists(self.parser.config_dir):
            print(CLIStyle.color(f"Configuration directory does not exist: {self.parser.config_dir}", CLIStyle.COLORS["WARNING"]))
            return
        
        tldr_files = [f for f in os.listdir(self.parser.config_dir) if f.endswith('.tldr')]
        
        if not tldr_files:
            print(CLIStyle.color("No TLDR configurations found", CLIStyle.COLORS["WARNING"]))
            return
        
        print(CLIStyle.color("Available TLDR configurations:", CLIStyle.COLORS["TITLE"]))
        for tldr_file in sorted(tldr_files):
            command_name = tldr_file[:-5]  # Remove .tldr extension
            print(CLIStyle.color(f"  - {command_name}", CLIStyle.COLORS["CONTENT"]))

# Main function and program entry point
def main() -> int:
    """Main program logic"""
    script_name = os.path.basename(sys.argv[0])
    
    # Define examples and notes
    examples = [
        ("Show help for ip command", "help ip"),
        ("Show help for git command", "help git"),
        ("List available configurations", "list"),
        ("Use custom config directory", "--config-dir /dir/path/to/*.tldr help ip")
    ]
    
    notes = [
        "Configuration files should be named <command>.tldr and use TOML format",
        "Default config directory is ~/.config/tldr",
        "Use --log to enable debug mode for troubleshooting"
    ]
    
    parser = ColoredArgumentParser(
        description=CLIStyle.color("TLDR - Quick command reference tool", CLIStyle.COLORS["TITLE"]),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=create_example_text(script_name, examples, notes)
    )
    
    # Add global parameters
    parser.add_argument("--log", action="store_true", help="Enable debug logging")
    parser.add_argument(
        "--config-dir", 
        type=str,
        metavar=CLIStyle.color("DIR", CLIStyle.COLORS["WARNING"]),
        help=CLIStyle.color("Custom configuration directory", CLIStyle.COLORS["CONTENT"])
    )
    
    # Add subcommands
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Help command
    help_parser = subparsers.add_parser(
        "help",
        help=CLIStyle.color("Show help for a command", CLIStyle.COLORS["CONTENT"]),
        description=CLIStyle.color(
            "Display TLDR help for specified command", 
            CLIStyle.COLORS["TITLE"]
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    help_parser.add_argument(
        "target_command",
        metavar=CLIStyle.color("COMMAND", CLIStyle.COLORS["WARNING"]),
        help=CLIStyle.color("Command to show help for", CLIStyle.COLORS["CONTENT"])
    )
    
    # List command
    list_parser = subparsers.add_parser(
        "list",
        help=CLIStyle.color("List available configurations", CLIStyle.COLORS["CONTENT"]),
        description=CLIStyle.color(
            "List all available TLDR configurations", 
            CLIStyle.COLORS["TITLE"]
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Set global debug mode
    global DEBUG_MODE
    DEBUG_MODE = args.log
    
    # Show help if no command specified
    if not args.command:
        parser.print_help()
        return 0
    
    # Main application logic in try-except block
    try:
        # Initialize TLDR tool
        tldr_tool = TLDRTool(args.config_dir)
        
        if args.command == "help":
            success = tldr_tool.show_help(args.target_command)
            return 0 if success else 1
        elif args.command == "list":
            tldr_tool.list_available()
            return 0
        else:
            print(CLIStyle.color(f"Unknown command: {args.command}", CLIStyle.COLORS["ERROR"]))
            return 1
            
    except KeyboardInterrupt:
        print(CLIStyle.color("\nOperation cancelled by user", CLIStyle.COLORS["WARNING"]))
        return 0
    except Exception as e:
        if DEBUG_MODE:
            import traceback
            traceback.print_exc()
        print(CLIStyle.color(f"\nError: {str(e)}", CLIStyle.COLORS["ERROR"]))
        return 1

if __name__ == "__main__":
    sys.exit(main())
