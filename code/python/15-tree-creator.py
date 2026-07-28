# -*- coding: utf-8 -*-

import argparse
import os
import re
import sys
from dataclasses import dataclass, field

if sys.platform == "win32":
    from colorama import init as colorama_init

    colorama_init(autoreset=True)

DEBUG_MODE = False
INDENT_SIZE = 2


class CLIStyle:
    """CLI tool unified style configuration."""

    COLORS = {
        "TITLE": 7,
        "SUB_TITLE": 2,
        "CONTENT": 3,
        "EXAMPLE": 7,
        "WARNING": 4,
        "ERROR": 2,
    }

    @staticmethod
    def color(text: str = "", color: int = COLORS["CONTENT"]) -> str:
        """Apply a semantic terminal color to text."""
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
    """Argument parser with colored help output."""

    def _format_action_invocation(self, action: argparse.Action) -> str:
        if not action.option_strings:
            metavar = self._format_args(action, action.dest.upper())
            return CLIStyle.color(metavar, CLIStyle.COLORS["WARNING"])

        if action.nargs == 0:
            return ", ".join(
                CLIStyle.color(option, CLIStyle.COLORS["SUB_TITLE"])
                for option in action.option_strings
            )

        argument = self._format_args(action, action.dest.upper())
        return ", ".join(
            CLIStyle.color(
                f"{option} {argument}", CLIStyle.COLORS["SUB_TITLE"]
            )
            for option in action.option_strings
        )

    def format_help(self) -> str:
        formatter = self._get_formatter()
        if self.description:
            formatter.add_text(CLIStyle.color(self.description, CLIStyle.COLORS["TITLE"]))
        formatter.add_usage(self.usage, self._actions, self._mutually_exclusive_groups)
        formatter.add_text(CLIStyle.color("\nOptions:", CLIStyle.COLORS["TITLE"]))
        for action_group in self._action_groups:
            formatter.start_section(action_group.title)
            formatter.add_arguments(action_group._group_actions)
            formatter.end_section()
        if self.epilog:
            formatter.add_text(self.epilog)
        return formatter.format_help()


def debug(message: str) -> None:
    """Print a diagnostic message when debug logging is enabled."""
    if DEBUG_MODE:
        print(
            CLIStyle.color(f"Debug: {message}", CLIStyle.COLORS["WARNING"]),
            file=sys.stderr,
        )


def get_example_definition() -> str:
    """Return the standard indentation-file example."""
    return """my-project/
  README.md
  src/
    main.py
    utils/
      format.py
  tests/
    test_main.py
"""


def create_example_text(script_name: str) -> str:
    """Create colored command examples for the help text."""
    examples = [
        ("Render an indentation file", "project.tree"),
        ("Create the default template", "--init"),
        ("Create a named template", "--init docs.tree"),
        ("Convert a rendered tree back to a definition", "--from-tree result.tree > project.tree"),
        ("Print input rules", "--example"),
    ]
    text = f"\n{CLIStyle.color('Examples:', CLIStyle.COLORS['SUB_TITLE'])}"
    for description, command in examples:
        text += f"\n  {CLIStyle.color(f'# {description}', CLIStyle.COLORS['EXAMPLE'])}"
        text += f"\n  {CLIStyle.color(f'{script_name} {command}', CLIStyle.COLORS['CONTENT'])}\n"
    text += f"\n{CLIStyle.color('Notes:', CLIStyle.COLORS['SUB_TITLE'])}"
    text += f"\n  {CLIStyle.color('- Indentation files use spaces only, two spaces per level.', CLIStyle.COLORS['CONTENT'])}"
    text += f"\n  {CLIStyle.color('- A trailing slash marks a directory.', CLIStyle.COLORS['CONTENT'])}"
    text += f"\n  {CLIStyle.color('- A non-directory entry with children is a collapsed node.', CLIStyle.COLORS['CONTENT'])}"
    text += f"\n\n{CLIStyle.color('Definition example:', CLIStyle.COLORS['SUB_TITLE'])}"
    text += f"\n{CLIStyle.color(get_example_definition().rstrip(), CLIStyle.COLORS['EXAMPLE'])}"
    return text


@dataclass
class TreeNode:
    """A file or directory entry in a tree."""

    name: str
    is_directory: bool
    children: list["TreeNode"] = field(default_factory=list)


class TreeParseError(ValueError):
    """Raised when a tree definition is invalid."""


class TreeGenerator:
    """Render directory trees from indentation definitions."""

    EXAMPLE_TEXT = get_example_definition()
    ANSI_ESCAPE_PATTERN = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")

    def parse_indentation_text(self, content: str) -> TreeNode:
        """Parse a two-space indentation tree definition."""
        root: TreeNode | None = None
        stack: list[TreeNode] = []

        for line_number, raw_line in enumerate(content.splitlines(), start=1):
            if not raw_line.strip():
                continue
            if "\t" in raw_line:
                raise TreeParseError(f"Line {line_number}: tabs are not allowed; use spaces.")

            indent = len(raw_line) - len(raw_line.lstrip(" "))
            if indent % INDENT_SIZE:
                raise TreeParseError(
                    f"Line {line_number}: indentation must be a multiple of {INDENT_SIZE} spaces."
                )

            level = indent // INDENT_SIZE
            entry = raw_line[indent:].rstrip()
            node = self._create_node(entry, line_number)
            if root is None:
                if level:
                    raise TreeParseError(f"Line {line_number}: the root cannot be indented.")
                if not node.is_directory:
                    raise TreeParseError(f"Line {line_number}: the root must be a directory ending in '/'.")
                root = node
                stack = [node]
                continue

            if level == 0:
                raise TreeParseError(f"Line {line_number}: only one root directory is allowed.")
            if level > len(stack):
                raise TreeParseError(f"Line {line_number}: indentation skips a directory level.")

            stack = stack[:level]
            parent = stack[-1]
            parent.children.append(node)
            stack.append(node)

        if root is None:
            raise TreeParseError("The tree definition is empty.")
        return root

    @staticmethod
    def _create_node(entry: str, line_number: int) -> TreeNode:
        """Create a tree node from one non-indented entry."""
        if not entry:
            raise TreeParseError(f"Line {line_number}: entry name cannot be empty.")
        is_directory = entry.endswith("/")
        name = entry[:-1] if is_directory else entry
        if not name:
            raise TreeParseError(f"Line {line_number}: directory name cannot be empty.")
        return TreeNode(name=name, is_directory=is_directory)

    def load_tree_file(self, filepath: str) -> TreeNode:
        """Load an indentation tree definition."""
        content = self._read_file(filepath)
        debug(f"Loading tree definition from {filepath}")
        return self.parse_indentation_text(content)

    def parse_rendered_tree(self, content: str) -> TreeNode:
        """Parse a tree rendered with standard branch characters."""
        lines = self._clean_rendered_lines(content)
        if not lines:
            raise TreeParseError("The rendered tree is empty.")

        root_line_number, root_text = lines[0]
        if root_text.startswith(("├── ", "└── ")):
            raise TreeParseError(f"Line {root_line_number}: the root must not have a branch prefix.")
        root_name = root_text[:-1] if root_text.endswith("/") else root_text
        if not root_name:
            raise TreeParseError(f"Line {root_line_number}: root name cannot be empty.")

        root = TreeNode(name=root_name, is_directory=True)
        stack = [root]
        for line_number, line in lines[1:]:
            match = re.fullmatch(
                r"(?P<prefix>(?:(?:│ {3})| {4})*)(?:├── |└── )(?P<entry>.+)",
                line,
            )
            if not match:
                raise TreeParseError(f"Line {line_number}: invalid tree branch format.")

            level = 1 + len(match.group("prefix")) // 4
            if level > len(stack):
                raise TreeParseError(f"Line {line_number}: tree branch skips a directory level.")

            stack = stack[:level]
            node = self._create_node(match.group("entry"), line_number)
            stack[-1].children.append(node)
            stack.append(node)
        return root

    def load_rendered_tree_file(self, filepath: str) -> TreeNode:
        """Load a previously rendered tree result."""
        content = self._read_file(filepath)
        debug(f"Loading rendered tree from {filepath}")
        return self.parse_rendered_tree(content)

    @staticmethod
    def _read_file(filepath: str) -> str:
        """Read a UTF-8 text file with user-friendly errors."""
        try:
            with open(filepath, encoding="utf-8") as file:
                return file.read()
        except FileNotFoundError as error:
            raise TreeParseError(f"File '{filepath}' was not found.") from error
        except OSError as error:
            raise TreeParseError(f"Could not read '{filepath}': {error}.") from error

    def _clean_rendered_lines(self, content: str) -> list[tuple[int, str]]:
        """Remove ANSI colors and blank lines from rendered tree text."""
        lines = []
        for line_number, raw_line in enumerate(content.splitlines(), start=1):
            line = self.ANSI_ESCAPE_PATTERN.sub("", raw_line).rstrip()
            if line.strip():
                lines.append((line_number, line))
        return lines

    def render(self, root: TreeNode) -> None:
        """Print a tree using standard branch characters."""
        print(CLIStyle.color(root.name, CLIStyle.COLORS["TITLE"]))
        for index, node in enumerate(root.children):
            self._render_node(node, "", index == len(root.children) - 1)

    def _render_node(self, node: TreeNode, prefix: str, is_last: bool) -> None:
        """Print one node and its descendants."""
        connector = "└── " if is_last else "├── "
        suffix = "/" if node.is_directory else ""
        print(CLIStyle.color(f"{prefix}{connector}{node.name}{suffix}"))
        if not node.is_directory:
            return
        child_prefix = prefix + ("    " if is_last else "│   ")
        for index, child in enumerate(node.children):
            self._render_node(child, child_prefix, index == len(node.children) - 1)

    def to_indentation_text(self, root: TreeNode) -> str:
        """Convert a tree into its plain indentation definition."""
        lines: list[str] = []
        self._append_indentation_lines(root, 0, lines)
        return "\n".join(lines) + "\n"

    def _append_indentation_lines(
        self, node: TreeNode, level: int, lines: list[str]
    ) -> None:
        """Append one node and descendants in indentation syntax."""
        suffix = "/" if node.is_directory else ""
        lines.append(f"{' ' * INDENT_SIZE * level}{node.name}{suffix}")
        for child in node.children:
            self._append_indentation_lines(child, level + 1, lines)

    def create_example_file(self, filepath: str) -> None:
        """Write an editable indentation-file example."""
        with open(filepath, "x", encoding="utf-8") as file:
            file.write(self.EXAMPLE_TEXT)

    @classmethod
    def format_rules(cls) -> str:
        """Return the input grammar and an example definition."""
        return "\n".join(
            [
                CLIStyle.color("Indentation format:", CLIStyle.COLORS["SUB_TITLE"]),
                CLIStyle.color("  1. Use spaces only; tabs are rejected.", CLIStyle.COLORS["CONTENT"]),
                CLIStyle.color("  2. Each level is exactly two spaces deeper.", CLIStyle.COLORS["CONTENT"]),
                CLIStyle.color("  3. Directories end with '/'; other entries are files.", CLIStyle.COLORS["CONTENT"]),
                CLIStyle.color("  4. An entry without '/' that has children is rendered as collapsed.", CLIStyle.COLORS["CONTENT"]),
                "",
                CLIStyle.color("Example:", CLIStyle.COLORS["EXAMPLE"]),
                cls.EXAMPLE_TEXT.rstrip(),
            ]
        )


def main() -> int:
    """Parse arguments and render a tree definition."""
    script_name = os.path.basename(sys.argv[0])
    parser = ColoredArgumentParser(
        description="Render a directory tree from a simple indentation file.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=create_example_text(script_name),
    )
    parser.add_argument(
        "source",
        nargs="?",
        metavar=CLIStyle.color("FILE", CLIStyle.COLORS["WARNING"]),
        help=CLIStyle.color("Indentation file to render."),
    )
    action_group = parser.add_mutually_exclusive_group()
    action_group.add_argument(
        "--example",
        action="store_true",
        help=CLIStyle.color("Show indentation rules and an example."),
    )
    action_group.add_argument(
        "--init",
        nargs="?",
        const="project.tree",
        metavar=CLIStyle.color("FILE", CLIStyle.COLORS["WARNING"]),
        help=CLIStyle.color("Create an editable example file; default: project.tree."),
    )
    parser.add_argument(
        "--log",
        action="store_true",
        help=CLIStyle.color("Enable diagnostic output."),
    )
    parser.add_argument(
        "--from-tree",
        metavar=CLIStyle.color("FILE", CLIStyle.COLORS["WARNING"]),
        help=CLIStyle.color("Convert a rendered tree file to indentation text."),
    )
    args = parser.parse_args()

    global DEBUG_MODE
    DEBUG_MODE = args.log
    generator = TreeGenerator()

    try:
        if args.example:
            print(generator.format_rules())
            return 0
        if args.init:
            generator.create_example_file(args.init)
            print(CLIStyle.color(f"Example file created: {args.init}"))
            return 0
        if args.from_tree:
            if args.source:
                parser.error("FILE cannot be used with --from-tree.")
            sys.stdout.write(
                generator.to_indentation_text(
                    generator.load_rendered_tree_file(args.from_tree)
                )
            )
            return 0
        if not args.source:
            parser.print_help()
            return 0

        generator.render(generator.load_tree_file(args.source))
        return 0
    except FileExistsError:
        print(CLIStyle.color(f"Error: '{args.init}' already exists.", CLIStyle.COLORS["ERROR"]))
        return 1
    except TreeParseError as error:
        print(CLIStyle.color(f"Error: {error}", CLIStyle.COLORS["ERROR"]))
        return 1
    except KeyboardInterrupt:
        print(CLIStyle.color("\nOperation cancelled.", CLIStyle.COLORS["WARNING"]))
        return 0
    except Exception as error:
        print(CLIStyle.color(f"Unexpected error: {error}", CLIStyle.COLORS["ERROR"]))
        return 1


if __name__ == "__main__":
    sys.exit(main())
