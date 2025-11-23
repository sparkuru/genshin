# -*- coding: utf-8 -*-

import os
import sys
import json
import argparse
from typing import Dict, List, Union, Any

if sys.platform == "win32":
    from colorama import init as colorama_init
    colorama_init(autoreset=True)

# Global debug level
DEBUG_MODE = False


def debug(*args, file=None, append=True, **kwargs) -> None:
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
    
    output = f"[{filename}:{line_number}]"
    if args:
        output += f" {' '.join(str(arg) for arg in args)}"
    if kwargs:
        output += f" {' '.join(f'{k}={v}' for k, v in kwargs.items())}"
    
    if file:
        mode = 'a' if append else 'w'
        with open(file, mode, encoding='utf-8') as f:
            f.write(output + '\n')
    else:
        print(output)


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


def create_example_text(script_name: str, examples: List[tuple], notes: List[str] = None) -> str:
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


class TreeGenerator:
    """Tree structure generator from JSON data"""
    
    EXAMPLE_JSON = {
        "root": [
            {
                "diy": [
                    "readme.md",
                    "unix-install-vim.sh",
                    "windows-vimrc"
                ]
            },
            "README.md",
            {
                "tutorials": [
                    "ch00_read_this_first.md",
                    "ch01_starting_vim.md",
                    "ch24_vim_runtime.md",
                    {
                        "images": [
                            "diffing-apples.png",
                            "fugitive-git.png",
                            "session-layout.png"
                        ]
                    },
                    "LICENSE",
                    "readme.md"
                ]
            },
            {
                "write": [
                    "often.md",
                    "readme.md",
                    "tcpdump.py",
                    "test.md"
                ]
            }
        ]
    }
    
    def __init__(self):
        """Initialize tree generator"""
        debug("TreeGenerator initialized")
    
    def print_tree(self, data: Union[Dict, List, str], indent: str = "", is_last: bool = True) -> None:
        """
        Recursively print tree structure
        ```python
        print_tree(
            data,           # Tree data structure (dict, list, or string)
            indent="",      # Current indentation string
            is_last=True    # Whether this is the last item in current level
        )
        
        return = None
        ```
        """
        if isinstance(data, dict):
            for idx, (key, value) in enumerate(data.items()):
                connector = "└── " if is_last and idx == len(data) - 1 else "├── "
                print(f"{indent}{connector}{key}")
                next_indent = indent + (
                    "    " if is_last and idx == len(data) - 1 else "│   "
                )
                self.print_tree(value, next_indent, is_last=(idx == len(data) - 1))
        elif isinstance(data, list):
            for idx, item in enumerate(data):
                self.print_tree(item, indent, is_last=(idx == len(data) - 1))
        else:
            connector = "└── " if is_last else "├── "
            print(f"{indent}{connector}{data}")
    
    def generate_tree_from_json(self, json_data: Dict[str, Any]) -> None:
        """
        Process root node and print directory tree
        ```python
        generate_tree_from_json(
            {"root": [...]}    # JSON data with root key
        )
        
        return = None
        ```
        """
        debug("Generating tree from JSON data", keys=list(json_data.keys()))
        
        if not json_data:
            print(CLIStyle.color("Error: Empty JSON data", CLIStyle.COLORS["ERROR"]))
            return
            
        root_key = list(json_data.keys())[0]
        print(CLIStyle.color(root_key, CLIStyle.COLORS["TITLE"]))
        self.print_tree(json_data[root_key], indent="")
    
    def create_example_file(self, filename: str = "tree-example.json") -> bool:
        """
        Create an example JSON file
        ```python
        create_example_file(
            "example.json"    # Output filename
        )
        
        return = True/False   # Success status
        ```
        """
        try:
            debug("Creating example file", filename=filename)
            with open(filename, "w", encoding="utf-8") as f:
                json.dump(self.EXAMPLE_JSON, f, indent=4, ensure_ascii=False)
            print(CLIStyle.color(f"Example file created: {filename}", CLIStyle.COLORS["CONTENT"]))
            return True
        except Exception as e:
            debug("Error creating example file", error=str(e))
            print(CLIStyle.color(f"Error creating example file: {str(e)}", CLIStyle.COLORS["ERROR"]))
            return False
    
    def load_json_file(self, filepath: str) -> Dict[str, Any]:
        """
        Load JSON data from file
        ```python
        load_json_file(
            "data.json"       # Path to JSON file
        )
        
        return = {...}        # Loaded JSON data or None on error
        ```
        """
        try:
            debug("Loading JSON file", filepath=filepath)
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            debug("JSON file loaded successfully", keys=list(data.keys()) if isinstance(data, dict) else "not_dict")
            return data
        except FileNotFoundError:
            print(CLIStyle.color(f"Error: File '{filepath}' not found", CLIStyle.COLORS["ERROR"]))
            return None
        except json.JSONDecodeError as e:
            print(CLIStyle.color(f"Error: Invalid JSON format in '{filepath}': {str(e)}", CLIStyle.COLORS["ERROR"]))
            return None
        except Exception as e:
            debug("Unexpected error loading JSON", error=str(e))
            print(CLIStyle.color(f"Error loading file '{filepath}': {str(e)}", CLIStyle.COLORS["ERROR"]))
            return None

    @staticmethod
    def get_usage_banner() -> str:
        """Get usage banner with formatting examples"""
        banner = f"""
{CLIStyle.color('JSON Structure Rules:', CLIStyle.COLORS['SUB_TITLE'])}
  {CLIStyle.color('1. Files and directories in same level:', CLIStyle.COLORS['CONTENT'])} [ file1, file2, dir1, dir2 ]
  {CLIStyle.color('2. Subdirectories:', CLIStyle.COLORS['CONTENT'])} {{ "dir1": [] }}
  {CLIStyle.color('3. Combined structure example:', CLIStyle.COLORS['CONTENT'])}

{CLIStyle.color('Example JSON:', CLIStyle.COLORS['EXAMPLE'])}
    {{
        "root": [
            {{
                "diy": [
                    "readme.md",
                    "unix-install-vim.sh", 
                    "windows-vimrc"
                ]
            }},
            "README.md",
            {{
                "tutorials": [
                    "ch00_read_this_first.md",
                    {{
                        "images": [
                            "diffing-apples.png",
                            "fugitive-git.png"
                        ]
                    }}
                ]
            }}
        ]
    }}

{CLIStyle.color('Generated Output:', CLIStyle.COLORS['EXAMPLE'])}
    root
    ├── diy
    │   ├── readme.md
    │   ├── unix-install-vim.sh
    │   └── windows-vimrc
    ├── README.md
    └── tutorials
        ├── ch00_read_this_first.md
        └── images
            ├── diffing-apples.png
            └── fugitive-git.png
        """
        return banner


def main() -> int:
    """Main program logic"""
    script_name = os.path.basename(sys.argv[0])
    
    # Define examples and notes
    examples = [
        ("Generate tree from JSON file", "-f data.json"),
        ("Show usage examples and format", "-e"),
        ("Create example JSON file", "-m"),
        ("Generate tree with debug info", "-f data.json --log")
    ]
    
    notes = [
        "JSON file must contain a single root key with array/object structure",
        "Use -m to create a template file, then modify it for your directory structure",
        "Files and directories are distinguished by their position in the JSON structure"
    ]
    
    parser = ColoredArgumentParser(
        description="Generate tree structure visualization from JSON file format",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=create_example_text(script_name, examples, notes)
    )
    
    # Add command line arguments
    parser.add_argument(
        "-f", "--filepath",
        default="tree-example.json",
        type=str,
        metavar=CLIStyle.color("PATH", CLIStyle.COLORS["WARNING"]),
        help="Path to JSON file containing tree structure"
    )
    parser.add_argument(
        "-e", "--example", 
        action="store_true",
        help="Show JSON format examples and usage"
    )
    parser.add_argument(
        "-m", "--make-example", 
        action="store_true",
        help="Generate example JSON file (tree-example.json)"
    )
    parser.add_argument(
        "--log", 
        action="store_true", 
        help="Enable debug logging"
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Set global debug mode
    global DEBUG_MODE
    DEBUG_MODE = args.log
    
    debug("Starting tree generator", args=vars(args))
    
    try:
        tree_gen = TreeGenerator()
        
        # Handle example display
        if args.example:
            print(tree_gen.get_usage_banner())
            return 0
        
        # Handle example file creation
        if args.make_example:
            success = tree_gen.create_example_file()
            return 0 if success else 1
        
        # Handle tree generation
        if not args.filepath:
            print(CLIStyle.color(
                f"Error: JSON file path required. Use '{script_name} -h' for help", 
                CLIStyle.COLORS["ERROR"]
            ))
            return 1
        
        # Load and process JSON file
        json_data = tree_gen.load_json_file(args.filepath)
        if json_data is None:
            return 1
        
        tree_gen.generate_tree_from_json(json_data)
        return 0
        
    except KeyboardInterrupt:
        print(CLIStyle.color("\nOperation cancelled by user", CLIStyle.COLORS["WARNING"]))
        return 0
    except Exception as e:
        if DEBUG_MODE:
            import traceback
            traceback.print_exc()
        print(CLIStyle.color(f"Unexpected error: {str(e)}", CLIStyle.COLORS["ERROR"]))
        return 1


if __name__ == "__main__":
    sys.exit(main())
