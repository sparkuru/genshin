# -*- coding: utf-8 -*-

import os
import sys
import hashlib
import base64
import argparse
import subprocess
from time import time
from typing import Optional, Tuple, List

# Global debug level
DEBUG_MODE = False

# Constants
DEFAULT_PASSWORD_LENGTH = 15
DEFAULT_SALT_FILE = "salt"
DEFAULT_CHAR_SET = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-#."


class CLIStyle:
    """CLI tool unified style config"""

    COLORS = {
        "TITLE": 7,  # Cyan - Main title
        "SUB_TITLE": 2,  # Red - Subtitle
        "CONTENT": 3,  # Green - Normal content
        "EXAMPLE": 7,  # Cyan - Example
        "WARNING": 4,  # Yellow - Warning
        "ERROR": 2,  # Red - Error
        "PASSWORD": 3,  # Green - Password
        "LENGTH": 4,  # Yellow - Length
        "KEY": 5,  # Purple - Key
        "SALT": 6,  # Cyan - Salt
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
            5: "\033[1;35m{}\033[0m",  # Purple bold
            6: "\033[1;36m{}\033[0m",  # Cyan bold
            7: "\033[1;37m{}\033[0m",  # White bold
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

        for action_group in self._action_groups:
            formatter.start_section(action_group.title)
            formatter.add_arguments(action_group._group_actions)
            formatter.end_section()

        if self.epilog:
            formatter.add_text(self.epilog)

        return formatter.format_help()


def debug(*args, file=None, append=True, **kwargs) -> None:
    """
    Print debug information with file and line number
    ```python
    debug(
        'Hello',    # Parameter 1
        'World',    # Parameter 2
        file='debug.log',  # Output file path
        append=False,  # Whether to append to file
        **kwargs  # Key-value parameters
    )
    ```
    """
    if not DEBUG_MODE:
        return

    import inspect

    frame = inspect.currentframe().f_back
    file_name = os.path.basename(frame.f_code.co_filename)
    line_no = frame.f_lineno

    message = f"[{file_name}:{line_no}] {' '.join(str(arg) for arg in args)}"
    if kwargs:
        message += f" {kwargs}"

    if file:
        mode = "a" if append else "w"
        with open(file, mode, encoding="utf-8") as f:
            f.write(message + "\n")
    else:
        print(message)


def get_system_uuid() -> str:
    """
    Get system UUID based on platform
    ```python
    uuid = get_system_uuid()

    return = "123e4567-e89b-12d3-a456-426614174000"  # Example UUID
    ```
    """
    try:
        if sys.platform == "win32":
            cmd = "wmic csproduct get UUID"
            uuid = subprocess.check_output(cmd).decode().split("\n")[1].strip()
        elif sys.platform == "linux":
            cmd = "cat /proc/sys/kernel/random/uuid"
            uuid = subprocess.check_output(cmd, shell=True).decode().strip()
        else:
            raise Exception("Unsupported OS")
        return uuid
    except Exception as e:
        debug("Error obtaining system UUID", error=str(e))
        print(CLIStyle.color(f"Error: {str(e)}", CLIStyle.COLORS["ERROR"]))
        sys.exit(1)


def safe_read_salt(salt_file: str) -> Optional[str]:
    """
    Safely read salt from file
    ```python
    salt = safe_read_salt("salt.txt")

    return = "abc123"  # Salt value or None if error
    ```
    """
    try:
        if os.path.exists(salt_file):
            with open(salt_file, "r", encoding="utf-8") as file:
                salt = file.read().strip()
                if salt:
                    return salt
    except Exception as e:
        debug("Error reading salt file", file=salt_file, error=str(e))
    return None


def safe_write_salt(salt_file: str, salt: str) -> bool:
    """
    Safely write salt to file
    ```python
    success = safe_write_salt("salt.txt", "abc123")

    return = True  # Success or False if error
    ```
    """
    try:
        with open(salt_file, "w", encoding="utf-8") as file:
            file.write(salt)
        return True
    except Exception as e:
        debug("Error writing salt file", file=salt_file, error=str(e))
        return False


def generate_salt(uuid: str, key: str) -> str:
    """
    Generate salt from UUID and key
    ```python
    salt = generate_salt("uuid", "key")

    return = "abc123"  # Generated salt
    ```
    """
    salt_sha256_obj = hashlib.sha256(uuid.encode())
    salt_sha256_obj.update(key.encode())
    return salt_sha256_obj.hexdigest()[:16]


def get_salt(uuid: str, key: str, salt_file: str = DEFAULT_SALT_FILE) -> str:
    """
    Get or generate salt
    ```python
    salt = get_salt("uuid", "key", "salt.txt")

    return = "abc123"  # Salt value
    ```
    """
    salt = safe_read_salt(salt_file)
    if salt is not None:
        return salt

    salt = generate_salt(uuid, key)
    if not safe_write_salt(salt_file, salt):
        print(
            CLIStyle.color(
                "Warning: Failed to save salt file", CLIStyle.COLORS["WARNING"]
            )
        )
    return salt


def generate_password(
    seed: str,
    length: int,
    salt_file: Optional[str] = None,
    char_set: Optional[str] = None,
    must_contain: Optional[str] = None,
) -> str:
    """
    Generate password using seed and salt
    ```python
    password = generate_password("seed", 15, "salt.txt", "abc123")

    return = "aB3#xY7"  # Generated password
    ```
    """
    if salt_file is not None:
        system_uuid = get_system_uuid()
        salt = get_salt(system_uuid, seed, salt_file)
        salt = base64.b64encode(salt.encode()).decode("utf-8")
    else:
        salt = seed

    # Ensure must_contain characters are in the character set
    if must_contain:
        if char_set:
            # Add missing required characters to the character set
            missing_chars = [c for c in must_contain if c not in char_set]
            if missing_chars:
                char_set += "".join(missing_chars)
        else:
            # If no custom character set, add required characters to default set
            char_set = DEFAULT_CHAR_SET
            missing_chars = [c for c in must_contain if c not in char_set]
            if missing_chars:
                char_set += "".join(missing_chars)
    else:
        # If no must_contain, use provided char_set or default
        char_set = char_set if char_set else DEFAULT_CHAR_SET

    # Generate a deterministic sequence of passwords until we find one with all required characters
    attempt = 0
    while True:
        password = ""
        current_seed = f"{seed}_{attempt}"  # Use attempt as part of the seed
        valid_chars = char_set
        char_set_length = len(valid_chars)

        # Debug output for character set
        if DEBUG_MODE:
            debug(f"Using character set: {valid_chars}")

        while len(password) < length:
            # Generate hash
            hash_bytes = hashlib.sha256(current_seed.encode()).digest()
            hash_bytes = hashlib.pbkdf2_hmac("sha256", hash_bytes, salt.encode(), 10000)

            # Convert hash bytes to indices in our character set
            for byte in hash_bytes:
                if len(password) >= length:
                    break
                # Use modulo to get an index within our character set
                index = byte % char_set_length
                password += valid_chars[index]

            current_seed = hash_bytes.hex()

        # Check if password contains all required characters
        if must_contain:
            if all(char in password for char in must_contain):
                return password
            if DEBUG_MODE:
                debug(f"Attempt {attempt + 1}: Password missing required characters")
        else:
            return password

        attempt += 1
        if attempt >= 1000:  # Increased max attempts since we're deterministic now
            raise ValueError(
                "Failed to generate password with required characters after maximum attempts"
            )


def create_example_text(
    script_name: str, examples: List[Tuple[str, str]], notes: List[str] = None
) -> str:
    """
    Create unified example text
    ```python
    text = create_example_text("script.py", [("desc", "cmd")], ["note"])

    return = "Examples:\n  # desc\n  script.py cmd\n\nNotes:\n  - note"
    ```
    """
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


def main() -> int:
    """
    Main program entry point
    ```python
    exit_code = main()

    return = 0  # Success or non-zero for error
    ```
    """
    script_name = os.path.basename(sys.argv[0])

    # Define examples and notes
    examples = [
        ("Generate password with default settings", "-k mykey"),
        ("Generate password with custom length", "-k mykey -l 20"),
        ("Generate password with custom salt file", "-k mykey -s custom_salt.txt"),
        ("Generate password with custom character set", "-k mykey --char abc123"),
        (
            "Generate password with custom character set and append",
            "-k mykey --charset_append '!@#$%^&*'",
        ),
    ]

    notes = [
        "If no key is provided, current timestamp will be used",
        "An example key combination can be: '<ip/domain:[port]>/<username>', like '192.168.1.100:3306/root'",
        "Salt file will be created if it doesn't exist",
        "Use --log to enable debug mode for troubleshooting",
        "Use --charset_append to add additional characters to the default character set",
        "Use --must to ensure password contains specific characters",
    ]

    parser = ColoredArgumentParser(
        description=CLIStyle.color("Password Generator Tool", CLIStyle.COLORS["TITLE"]),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=create_example_text(script_name, examples, notes),
    )

    parser.add_argument(
        "-k",
        "--key",
        type=str,
        metavar=CLIStyle.color("KEY", CLIStyle.COLORS["WARNING"]),
        help=CLIStyle.color("Seed for password generation", CLIStyle.COLORS["CONTENT"]),
    )
    parser.add_argument(
        "-l",
        "--length",
        type=int,
        default=DEFAULT_PASSWORD_LENGTH,
        metavar=CLIStyle.color("LENGTH", CLIStyle.COLORS["WARNING"]),
        help=CLIStyle.color(
            f"Password length (default: {DEFAULT_PASSWORD_LENGTH})",
            CLIStyle.COLORS["CONTENT"],
        ),
    )
    parser.add_argument(
        "-s",
        "--salt",
        type=str,
        default=None,
        metavar=CLIStyle.color("SALT", CLIStyle.COLORS["WARNING"]),
        help=CLIStyle.color(
            "Specify salt file path (default: salt)", CLIStyle.COLORS["CONTENT"]
        ),
    )
    parser.add_argument(
        "--char",
        type=str,
        default=None,
        metavar=CLIStyle.color("CHAR", CLIStyle.COLORS["WARNING"]),
        help=CLIStyle.color(
            "Specify character set for password generation", CLIStyle.COLORS["CONTENT"]
        ),
    )
    parser.add_argument(
        "--charset_append",
        type=str,
        default=None,
        metavar=CLIStyle.color("APPEND_CHARS", CLIStyle.COLORS["WARNING"]),
        help=CLIStyle.color(
            "Append additional characters to the default character set",
            CLIStyle.COLORS["CONTENT"],
        ),
    )
    parser.add_argument(
        "--must",
        type=str,
        default=None,
        metavar=CLIStyle.color("REQUIRED_CHARS", CLIStyle.COLORS["WARNING"]),
        help=CLIStyle.color(
            "Ensure password contains these characters",
            CLIStyle.COLORS["CONTENT"],
        ),
    )
    parser.add_argument(
        "--log",
        action="store_true",
        help=CLIStyle.color("Enable debug logging", CLIStyle.COLORS["CONTENT"]),
    )

    args = parser.parse_args()

    # Set global debug mode
    global DEBUG_MODE
    DEBUG_MODE = args.log

    try:
        # Generate password
        key_seed = args.key if args.key else str(time())

        # Handle character set
        char_set = args.char
        if args.charset_append:
            if char_set:
                char_set = char_set + args.charset_append
            else:
                char_set = DEFAULT_CHAR_SET + args.charset_append
            # Remove duplicates while preserving order
            char_set = "".join(dict.fromkeys(char_set))
            if DEBUG_MODE:
                debug(f"Final character set: {char_set}")

        password = generate_password(
            key_seed, args.length, args.salt, char_set, args.must
        )

        # Display results
        print("Generated password with:")
        print(f"| password: {CLIStyle.color(password, CLIStyle.COLORS['PASSWORD'])}")
        print(
            f"| length: {CLIStyle.color(str(len(password)), CLIStyle.COLORS['LENGTH'])}"
        )
        print(f"| key: {CLIStyle.color(key_seed, CLIStyle.COLORS['KEY'])}")
        print(
            f"| salt_file: {CLIStyle.color(args.salt if args.salt else 'None', CLIStyle.COLORS['SALT'])}"
        )

        return 0

    except KeyboardInterrupt:
        print(
            CLIStyle.color("\nOperation cancelled by user", CLIStyle.COLORS["WARNING"])
        )
        return 0
    except Exception as e:
        if DEBUG_MODE:
            import traceback

            traceback.print_exc()
        print(CLIStyle.color(f"\nError: {str(e)}", CLIStyle.COLORS["ERROR"]))
        return 1


if __name__ == "__main__":
    sys.exit(main())
