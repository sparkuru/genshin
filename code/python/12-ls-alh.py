# -*- coding: utf-8 -*-
# pip install colorama argparse

import os
import sys
import ctypes
import re
from datetime import datetime
import argparse
from colorama import Fore, Style

# Import modules based on operating system
if sys.platform != 'win32':
    import pwd
    import grp
else:
    # Create empty pwd and grp modules for Windows
    class PwdModule:
        def getpwuid(self, uid):
            class Passwd:
                def __init__(self):
                    self.pw_name = "Unknown"
            return Passwd()
    pwd = PwdModule()

    class GrpModule:
        def getgrgid(self, gid):
            class Group:
                def __init__(self):
                    self.gr_name = "Unknown"
            return Group()
    grp = GrpModule()

# Global variables
DEBUG_MODE = False
VERSION = "1.1.4"

# CLI colors
CLI_COLORS = {
    "TITLE": 7,      # Cyan - Main title
    "SUB_TITLE": 2,  # Red - Subtitle
    "CONTENT": 3,    # Green - Normal content
    "EXAMPLE": 6,    # Purple - Examples
    "WARNING": 4,    # Yellow - Warnings
    "ERROR": 2,      # Red - Errors
    "DIR": 4,        # Yellow - Directories
    "FILE": 5,       # Blue - Files
    "HIDDEN": 2,     # Red - Hidden files
}

def color(text: str, color_code: int = 0) -> str:
    """Add color to text output"""
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
    return color_table[color_code].format(text)

def debug(*args, file=None, append=True, **kwargs) -> None:
    """Print debug information with file and line number"""
    if not DEBUG_MODE:
        return
        
    import inspect
    import re
    frame = inspect.currentframe().f_back
    info = inspect.getframeinfo(frame)
    
    output = f"{color(os.path.basename(info.filename), 3)}: {color(str(info.lineno), 4)} {color('|', 7)} "
    
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

def divider(text: str = None, char: str = '=') -> None:
    """Print a divider line with optional text"""
    divider_str = char * 10
    text = text if text else 'Divider'
    print(f"{color(divider_str, CLI_COLORS['TITLE'])} {text} {color(divider_str, CLI_COLORS['TITLE'])}")

def human_readable_size(size: int, decimal_places: int = 2) -> str:
    """Convert file size to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if abs(size) < 1024.0 or unit == 'TB':
            break
        size /= 1024.0
    return f"{size:>{decimal_places + 4}.{decimal_places}f} {unit}"

def is_hidden(filepath: str) -> bool:
    """Check if a file is hidden"""
    # Windows method
    if sys.platform == 'win32':
        try:
            attrs = ctypes.windll.kernel32.GetFileAttributesW(filepath)
            assert attrs != -1
            result = bool(attrs & 2)
        except (AttributeError, AssertionError):
            result = False
        return result
    # Unix method
    else:
        return os.path.basename(filepath).startswith('.')

def get_terminal_size() -> int:
    """Get terminal width"""
    try:
        from shutil import get_terminal_size as get_size
        columns, _ = get_size()
        return columns
    except ImportError:
        return 80

def natural_sort_key(s):
    """Natural sort key function - sorts strings with numbers naturally"""
    return [int(text) if text.isdigit() else text.lower() 
            for text in re.split(r'(\d+)', s)]

class FileFormatter:
    """File formatting class for ls-alh"""
    
    def __init__(self, show_hidden=False, plain_output=False, show_owner=False):
        """Initialize formatter with options"""
        self.show_hidden = show_hidden
        self.plain_output = plain_output
        self.show_owner = show_owner
        self.can_show_owner = sys.platform != 'win32'
        
    def format_mode(self, entry) -> str:
        """Format permission mode string for entry"""
        mode = 'd' if entry.is_dir() else '-'
        mode += 'r' if os.access(entry.path, os.R_OK) else '-'
        mode += 'w' if os.access(entry.path, os.W_OK) else '-'
        mode += 'x' if os.access(entry.path, os.X_OK) else '-'
        return mode
        
    def format_size(self, entry) -> str:
        """Format size for entry"""
        if entry.is_dir():
            return ''
        return human_readable_size(entry.stat().st_size)
        
    def format_time(self, entry) -> str:
        """Format last modified time for entry"""
        info = entry.stat()
        return datetime.fromtimestamp(info.st_mtime).strftime('%Y/%m/%d %H:%M:%S')
    
    def format_owner(self, entry) -> tuple:
        """Format owner and group information"""
        if not self.show_owner or not self.can_show_owner:
            return "", ""
            
        try:
            stat_info = entry.stat()
            uid = stat_info.st_uid
            gid = stat_info.st_gid
            
            user = pwd.getpwuid(uid).pw_name
            group = grp.getgrgid(gid).gr_name
            
            return user, group
        except (ImportError, KeyError, AttributeError):
            return "", ""
        
    def get_color_for_entry(self, entry) -> tuple:
        """Get appropriate color and format for entry"""
        hidden = is_hidden(entry.path)
        
        if hidden:
            return Fore.RED, f"{entry.name} [hide]" if not self.plain_output else entry.name
        elif entry.is_dir():
            return Fore.YELLOW, entry.name
        else:
            return Fore.BLUE, entry.name
            
    def format_row(self, entry, mode_width=5, size_width=10, user_width=8, group_width=8, time_width=20, name_width=40) -> str:
        """Format a row for the entry"""
        mode = self.format_mode(entry)
        size = self.format_size(entry)
        time = self.format_time(entry)
        color_code, name = self.get_color_for_entry(entry)
        user, group = self.format_owner(entry)
        
        owner_part = f"{user:<{user_width}} {group:<{group_width}} " if self.show_owner and self.can_show_owner else ""
        
        if self.plain_output:
            base = f"{mode:<{mode_width}} {size:<{size_width}} "
            if self.show_owner and self.can_show_owner:
                base += f"{user:<{user_width}} {group:<{group_width}} "
            base += f"{time:<{time_width}} {name:<{name_width}}"
            return base
        else:
            if is_hidden(entry.path):
                base = Fore.RED + f"{mode:<{mode_width}} {size:<{size_width}} "
                if self.show_owner and self.can_show_owner:
                    base += f"{user:<{user_width}} {group:<{group_width}} "
                base += f"{time:<{time_width}} {name:<{name_width}}" + Style.RESET_ALL
                return base
            elif entry.is_dir():
                base = Fore.YELLOW + f"{mode:<{mode_width}} {size:<{size_width}} "
                if self.show_owner and self.can_show_owner:
                    base += f"{user:<{user_width}} {group:<{group_width}} "
                base += f"{time:<{time_width}} {name:<{name_width}}" + Style.RESET_ALL
                return base
            else:
                base = Fore.BLUE + f"{mode:<{mode_width}} {size:<{size_width}} "
                if self.show_owner and self.can_show_owner:
                    base += f"{user:<{user_width}} {group:<{group_width}} "
                base += f"{time:<{time_width}} {name:<{name_width}}" + Style.RESET_ALL
                return base
    
    def format_header(self, mode_width=5, size_width=10, user_width=8, group_width=8, time_width=20, name_width=40) -> str:
        """Format the header row"""
        owner_part = f"{'User':<{user_width}} {'Group':<{group_width}} " if self.show_owner and self.can_show_owner else ""
        
        if self.plain_output:
            base = f"{'Mode':<{mode_width}} {'Size':<{size_width}} "
            if self.show_owner and self.can_show_owner:
                base += f"{'User':<{user_width}} {'Group':<{group_width}} "
            base += f"{'Last Modified':<{time_width}} {'Name':<{name_width}}"
            return base
        else:
            base = Fore.GREEN + f"{'Mode':<{mode_width}} {'Size':<{size_width}} "
            if self.show_owner and self.can_show_owner:
                base += f"{'User':<{user_width}} {'Group':<{group_width}} "
            base += f"{'Last Modified':<{time_width}} {'Name':<{name_width}}" + Style.RESET_ALL
            return base
        
    def format_stats(self, total_dirs, total_files, hidden_count, total_size) -> str:
        """Format statistics output"""
        stats = [
            (f"{Fore.CYAN if not self.plain_output else ''}Dirs:{Style.RESET_ALL if not self.plain_output else ''}", total_dirs),
            (f"{Fore.BLUE if not self.plain_output else ''}Files:{Style.RESET_ALL if not self.plain_output else ''}", total_files),
            (f"{Fore.RED if not self.plain_output else ''}Hidden:{Style.RESET_ALL if not self.plain_output else ''}", hidden_count),
            (f"{Fore.GREEN if not self.plain_output else ''}Total Size:{Style.RESET_ALL if not self.plain_output else ''}", human_readable_size(total_size))
        ]
        return "\n" + " | ".join(f"{label} {value}" for label, value in stats)

class DirectoryLister:
    """Directory listing class for ls-alh"""
    
    def __init__(self, path='.', show_all=False, sort_by='name', plain_output=False, detail_level=1, show_owner=False):
        """Initialize with options"""
        self.path = path
        self.show_all = show_all
        self.sort_by = sort_by
        self.plain_output = plain_output
        self.detail_level = detail_level
        self.show_owner = show_owner
        self.formatter = FileFormatter(show_all, plain_output, show_owner)
        
        # Statistics
        self.total_files = 0
        self.total_dirs = 0
        self.total_size = 0
        self.hidden_count = 0
        
    def get_sorted_entries(self) -> list:
        """Get sorted directory entries"""
        try:
            with os.scandir(self.path) as scanner:
                entries = list(scanner)
                
                # First sort directories before files
                entries = sorted(entries, key=lambda entry: entry.is_dir(), reverse=True)
                
                # Then apply user-specified sort with natural sorting
                if self.sort_by == 'name':
                    entries = sorted(entries, key=lambda entry: natural_sort_key(entry.name))
                elif self.sort_by == 'size':
                    # Use natural sorting as secondary sort criteria
                    entries = sorted(entries, key=lambda entry: (entry.stat().st_size, natural_sort_key(entry.name)), reverse=True)
                elif self.sort_by == 'time':
                    # Use natural sorting as secondary sort criteria
                    entries = sorted(entries, key=lambda entry: (entry.stat().st_mtime, natural_sort_key(entry.name)), reverse=True)
                    
                return entries
        except PermissionError:
            if not self.plain_output:
                print(f"{Fore.RED}Error: No permission to access directory {self.path}{Style.RESET_ALL}")
            else:
                print(f"Error: No permission to access directory {self.path}")
            return []
        except FileNotFoundError:
            if not self.plain_output:
                print(f"{Fore.RED}Error: Directory {self.path} does not exist{Style.RESET_ALL}")
            else:
                print(f"Error: Directory {self.path} does not exist")
            return []
        except Exception as e:
            if not self.plain_output:
                print(f"{Fore.RED}Error: {str(e)}{Style.RESET_ALL}")
            else:
                print(f"Error: {str(e)}")
            return []
    
    def process_entry(self, entry) -> None:
        """Process and collect statistics for an entry"""
        if is_hidden(entry.path):
            self.hidden_count += 1
            if not self.show_all:
                return False
                
        if entry.is_dir():
            self.total_dirs += 1
        else:
            self.total_files += 1
            self.total_size += entry.stat().st_size
            
        return True
            
    def display_detailed_list(self, entries) -> None:
        """Display detailed list with permissions, size and time"""
        mode_width = 5
        size_width = 10
        user_width = 8
        group_width = 8
        time_width = 20
        name_width = 40
        
        # Print header
        print(self.formatter.format_header(mode_width, size_width, user_width, group_width, time_width, name_width))
        
        # Process and print entries
        for entry in entries:
            if not self.process_entry(entry):
                continue
                
            print(self.formatter.format_row(entry, mode_width, size_width, user_width, group_width, time_width, name_width))
            
    def display_simple_list(self, entries) -> None:
        """Display simple list with just names"""
        terminal_width = get_terminal_size()
        max_name_length = max([len(entry.name) for entry in entries]) + 4
        cols = max(1, terminal_width // max_name_length)
        
        row = []
        for i, entry in enumerate(entries):
            if not self.process_entry(entry):
                continue
                
            color_code, name = self.formatter.get_color_for_entry(entry)
            
            if self.plain_output:
                row.append(f"{name:<{max_name_length}}")
            else:
                row.append(f"{color_code}{name:<{max_name_length}}{Style.RESET_ALL}")
                
            if (i + 1) % cols == 0:
                print("".join(row))
                row = []
                
        if row:
            print("".join(row))
    
    def list_directory(self) -> None:
        """List directory contents"""
        entries = self.get_sorted_entries()
        
        if not entries:
            return
            
        if self.detail_level >= 1:
            self.display_detailed_list(entries)
        else:
            self.display_simple_list(entries)
            
        # Print statistics
        print(self.formatter.format_stats(
            self.total_dirs, 
            self.total_files, 
            self.hidden_count, 
            self.total_size
        ))

def create_example_text() -> str:
    """Create formatted example text for help menu"""
    script_name = os.path.basename(sys.argv[0])
    
    examples = [
        ("List current directory", ""),
        ("List all files including hidden", "-a"),
        ("List files in a specific directory", "-d /path/to/dir"),
        ("Sort files by size", "-s size"),
        ("Sort files by modification time", "-s time"),
        ("Simple display mode", "-l 0"),
        ("Show owner and group (Unix/Linux)", "-o"),
        ("Plain output (no colors)", "-p"),
        ("Debug mode", "--debug"),
    ]
    
    text = f'\n{color("Examples:", CLI_COLORS["SUB_TITLE"])}'
    
    for desc, cmd in examples:
        text += f'\n  {color(f"# {desc}", CLI_COLORS["EXAMPLE"])}'
        text += f'\n  {color(f"{script_name} {cmd}", CLI_COLORS["CONTENT"])}'
        text += '\n'
    
    notes = [
        "The -a/--all option shows hidden files",
        "The -d/--dir option specifies which directory to list",
        "The -s/--sort option can sort by name, size, or time",
        "The -l/--level option sets detail level (0=simple, 1=detailed)",
        "The -o/--owner option shows user and group (Unix/Linux only)",
        "Hidden files are displayed in red",
        "Directories are displayed in yellow",
        "Regular files are displayed in blue",
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
        f"  {color('-d, --dir', CLI_COLORS['SUB_TITLE'])} DIR      Directory to list (default: current directory)",
        f"  {color('-a, --all', CLI_COLORS['SUB_TITLE'])}          Show all files including hidden files",
        f"  {color('-s, --sort', CLI_COLORS['SUB_TITLE'])} SORT    Sort by name, size, or time (default: name)",
        f"  {color('-l, --level', CLI_COLORS['SUB_TITLE'])} LEVEL  Detail level (0=simple, 1=detailed) (default: 1)",
        f"  {color('-o, --owner', CLI_COLORS['SUB_TITLE'])}        Show owner and group information (Unix/Linux only)",
        f"  {color('-p, --plain', CLI_COLORS['SUB_TITLE'])}        Plain output (no colors)",
        f"  {color('--debug', CLI_COLORS['SUB_TITLE'])}            Enable debug mode",
        f"  {color('-v, --version', CLI_COLORS['SUB_TITLE'])}      Show program version"
    ])
    help_parts.append("")
    
    # Add examples
    help_parts.append(create_example_text())
    
    return "\n".join(help_parts)

def main():
    parser = argparse.ArgumentParser(
        description='ls-alh - Enhanced directory listing with colors and statistics',
        add_help=False
    )
    
    # Options
    parser.add_argument(
        '-h', '--help',
        action='store_true',
        help='Show this help message and exit'
    )
    parser.add_argument(
        '-d', '--dir',
        nargs='?',
        default='.',
        type=str,
        help='Directory to list (default: current directory)'
    )
    parser.add_argument(
        '-a', '--all',
        action='store_true',
        help='Show all files including hidden files'
    )
    parser.add_argument(
        '-s', '--sort',
        choices=['name', 'size', 'time'],
        default='name',
        help='Sort by name, size, or time (default: name)'
    )
    parser.add_argument(
        '-l', '--level',
        type=int,
        choices=[0, 1],
        default=1,
        help='Detail level (0=simple, 1=detailed) (default: 1)'
    )
    parser.add_argument(
        '-p', '--plain',
        action='store_true',
        help='Plain output (no colors)'
    )
    parser.add_argument(
        '-o', '--owner',
        action='store_true',
        help='Show owner and group information (Unix/Linux only)'
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
    
    # Check if owner display is supported
    if args.owner and sys.platform == 'win32':
        print(color("Warning: Owner/group display is not supported on Windows", CLI_COLORS["WARNING"]))
    
    # Run directory listing
    lister = DirectoryLister(
        path=args.dir,
        show_all=args.all,
        sort_by=args.sort,
        plain_output=args.plain,
        detail_level=args.level,
        show_owner=args.owner
    )
    
    lister.list_directory()

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
