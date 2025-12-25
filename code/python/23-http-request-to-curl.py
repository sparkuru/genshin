# -*- coding: utf-8 -*-

import sys
import re
import os
import argparse

DEBUG_MODE = False

class CLIStyle:
    COLORS = {
        "TITLE": 7,
        "SUB_TITLE": 2,
        "CONTENT": 3,
        "EXAMPLE": 7,
        "WARNING": 4,
        "ERROR": 2,
    }
    
    @staticmethod
    def color(text: str = "", color: int = 3) -> str:
        color_table = {
            0: "{}",
            1: "\033[1;30m{}\033[0m",
            2: "\033[1;31m{}\033[0m",
            3: "\033[1;32m{}\033[0m",
            4: "\033[1;33m{}\033[0m",
            5: "\033[1;34m{}\033[0m",
            6: "\033[1;35m{}\033[0m",
            7: "\033[1;36m{}\033[0m",
            8: "\033[1;37m{}\033[0m",
        }
        return color_table[color].format(text)


class ColoredArgumentParser(argparse.ArgumentParser):
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


def create_example_text(script_name: str, examples: list, notes: list = None) -> str:
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


def parse_http_request(request_text: str) -> dict:
    """
    Parse HTTP request text into structured data
    ```python
    parse_http_request(
        "GET /api/test HTTP/1.1\\nHost: example.com\\n..."
    )
    
    return = {
        "method": "GET",
        "url": "https://example.com/api/test",
        "headers": {"Host": "example.com", ...},
        "body": ""
    }
    ```
    """
    lines = request_text.strip().split('\n')
    
    if not lines:
        return None
    
    first_line = lines[0].strip()
    match = re.match(r'(\w+)\s+(.+?)\s+HTTP', first_line)
    if not match:
        return None
    
    method = match.group(1)
    path = match.group(2)
    
    headers = {}
    body_start = None
    
    for i, line in enumerate(lines[1:], 1):
        if not line.strip():
            body_start = i + 1
            break
        
        if ':' in line:
            key, value = line.split(':', 1)
            headers[key.strip()] = value.strip()
    
    body = ''
    if body_start and body_start < len(lines):
        body = '\n'.join(lines[body_start:]).strip()
    
    host = headers.get('Host', '')
    protocol = 'https' if 'https' in headers.get('Referer', '').lower() else 'http'
    url = f"{protocol}://{host}{path}"
    
    return {
        'method': method,
        'url': url,
        'headers': headers,
        'body': body
    }


def to_curl(parsed_request: dict, insecure: bool = False, single_line: bool = False) -> str:
    """
    Convert parsed request to curl command
    ```python
    to_curl({
        "method": "GET",
        "url": "https://example.com/api/test",
        "headers": {"Cookie": "token=abc"},
        "body": ""
    }, insecure=True, single_line=False)
    
    return = "curl -X GET -k -H \"Cookie: token=abc\" \"https://example.com/api/test\""
    ```
    """
    if not parsed_request:
        return None
    
    curl_parts = ['curl']
    
    curl_parts.append(f"-X {parsed_request['method']}")
    
    if insecure:
        curl_parts.append('-k')
    
    skip_headers = {'Host', 'Content-Length'}
    for key, value in parsed_request['headers'].items():
        if key not in skip_headers:
            escaped_value = value.replace('"', '\\"')
            curl_parts.append(f'-H "{key}: {escaped_value}"')
    
    if parsed_request['body']:
        escaped_body = parsed_request['body'].replace("'", "'\\''")
        curl_parts.append(f"--data '{escaped_body}'")
    
    curl_parts.append(f'"{parsed_request["url"]}"')
    
    if single_line:
        return ' '.join(curl_parts)
    else:
        return ' \\\n  '.join(curl_parts)


def read_input(input_file: str = None) -> str:
    """
    Read request text from file or stdin
    ```python
    read_input("/tmp/request.txt")
    return = "GET /api/test HTTP/1.1\\n..."
    ```
    """
    if input_file:
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            print(CLIStyle.color(f"Error: File '{input_file}' not found", CLIStyle.COLORS["ERROR"]))
            sys.exit(1)
        except PermissionError:
            print(CLIStyle.color(f"Error: No permission to read '{input_file}'", CLIStyle.COLORS["ERROR"]))
            sys.exit(1)
    else:
        if sys.stdin.isatty():
            print(CLIStyle.color("Paste HTTP request below (press Ctrl+D when done):", CLIStyle.COLORS["CONTENT"]))
        return sys.stdin.read()


def main() -> int:
    script_name = os.path.basename(sys.argv[0])
    
    examples = [
        ("Convert from file", "/tmp/request.txt"),
        ("Skip SSL verification (for self-signed certs)", "-k /tmp/request.txt"),
        ("Output as single line", "-s /tmp/request.txt"),
        ("Combine options", "-k -s /tmp/request.txt"),
        ("Interactive input (paste and press Ctrl+D)", ""),
        ("Redirect from file", "< request.txt"),
        ("Pipe from clipboard", f"(xclip -o | {script_name})"),
    ]
    
    notes = [
        "Input should be raw HTTP request (from Burp Suite, browser DevTools, etc.)",
        "Protocol (http/https) is detected from Referer header",
        "Use -k flag to add --insecure to curl (skip SSL verification)",
        "Use -s flag to output single line format (default: multi-line)",
        "When using stdin: paste content then press Ctrl+D to finish"
    ]
    
    parser = ColoredArgumentParser(
        description=CLIStyle.color("Convert HTTP request to curl command", CLIStyle.COLORS["TITLE"]),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=create_example_text(script_name, examples, notes)
    )
    
    parser.add_argument(
        "input_file",
        nargs='?',
        help="Input file containing HTTP request (stdin if not provided)"
    )
    
    parser.add_argument(
        "-k", "--insecure",
        action="store_true",
        help="Add -k flag to skip SSL certificate verification"
    )
    
    parser.add_argument(
        "-s", "--single-line",
        action="store_true",
        help="Output curl command in single line (default: multi-line)"
    )
    
    parser.add_argument("--log", action="store_true", help="Enable debug logging")
    
    args = parser.parse_args()
    
    global DEBUG_MODE
    DEBUG_MODE = args.log
    
    try:
        request_text = read_input(args.input_file)
        
        parsed = parse_http_request(request_text)
        
        if not parsed:
            print(CLIStyle.color("Error: Invalid request format", CLIStyle.COLORS["ERROR"]))
            return 1
        
        curl_cmd = to_curl(parsed, insecure=args.insecure, single_line=args.single_line)
        
        if curl_cmd:
            print(curl_cmd)
            return 0
        else:
            print(CLIStyle.color("Error: Failed to convert to curl", CLIStyle.COLORS["ERROR"]))
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
