# -*- coding: utf-8 -*-
# pip install pillow markdown pygments playwright
# playwright install chromium

import argparse
import asyncio
import html
import importlib
import inspect
import re
import shutil
import subprocess
import sys
import tempfile
import traceback
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse


DEBUG_MODE = False


@dataclass
class RenderOptions:
    """Render options parsed from command line arguments."""

    source: str
    output: Path
    input_format: str
    output_format: str
    theme: str
    width: int
    font_size: int
    padding: int
    scale: float
    wrap: bool
    source_base_dir: Path


@dataclass
class AnsiStyle:
    """Current ANSI text style."""

    foreground: str | None = None
    background: str | None = None
    bold: bool = False

    def to_css(self) -> str:
        """Convert the style to inline CSS."""
        parts = []
        if self.foreground:
            parts.append(f"color:{self.foreground}")
        if self.background:
            parts.append(f"background-color:{self.background}")
        if self.bold:
            parts.append("font-weight:700")
        return ";".join(parts)


class CLIStyle:
    """CLI tool unified style config."""

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
        """Unified color processing function."""
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

    @staticmethod
    def print(text: str = "", color: int = COLORS["CONTENT"]) -> None:
        """Print styled terminal output."""
        print(CLIStyle.color(text, color))


class ColoredArgumentParser(argparse.ArgumentParser):
    """Argument parser with colored help output."""

    def _format_action_invocation(self, action: argparse.Action) -> str:
        """Colorize option names in help output."""
        if not action.option_strings:
            (metavar,) = self._metavar_formatter(action, action.dest)(1)
            return CLIStyle.color(metavar, CLIStyle.COLORS["CONTENT"])

        parts = []
        if action.nargs == 0:
            for option_string in action.option_strings:
                parts.append(
                    CLIStyle.color(option_string, CLIStyle.COLORS["SUB_TITLE"])
                )
            return ", ".join(parts)

        args_string = self._format_args(action, action.dest.upper())
        for option_string in action.option_strings:
            parts.append(
                CLIStyle.color(
                    f"{option_string} {args_string}",
                    CLIStyle.COLORS["SUB_TITLE"],
                )
            )
        return ", ".join(parts)

    def format_help(self) -> str:
        """Format colorized help text."""
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


def debug(*args: Any, **kwargs: Any) -> None:
    """
    Print debug details with file and line information.
    ```python
    debug("message")

    return = None
    ```
    """
    if not DEBUG_MODE:
        return
    frame = inspect.currentframe()
    caller = frame.f_back if frame else None
    location = ""
    if caller:
        location = f"{Path(caller.f_code.co_filename).name}:{caller.f_lineno}"
    print(
        CLIStyle.color(f"[DEBUG {location}]", CLIStyle.COLORS["WARNING"]),
        *args,
        file=sys.stderr,
        **kwargs,
    )


def create_example_text(
    script_name: str, examples: list[tuple[str, str]], notes: list[str] | None = None
) -> str:
    """
    Build a colorized example block for argparse epilog.
    ```python
    create_example_text("script.py", [("Render", "input.md -o out.png")])

    return = str
    ```
    """
    text = f"\n{CLIStyle.color('Examples:', CLIStyle.COLORS['SUB_TITLE'])}"
    for desc, cmd in examples:
        text += f"\n  {CLIStyle.color(f'# {desc}', CLIStyle.COLORS['EXAMPLE'])}"
        text += f"\n  {CLIStyle.color(f'{script_name} {cmd}', CLIStyle.COLORS['CONTENT'])}\n"
    if notes:
        text += f"\n{CLIStyle.color('Notes:', CLIStyle.COLORS['SUB_TITLE'])}"
        for note in notes:
            text += f"\n  {CLIStyle.color(f'- {note}', CLIStyle.COLORS['CONTENT'])}"
    return text


def load_markdown_module() -> Any | None:
    """
    Load the Markdown package when Markdown rendering is requested.
    ```python
    load_markdown_module()

    return = Any | None
    ```
    """
    try:
        return importlib.import_module("markdown")
    except ImportError:
        return None


def load_html_formatter() -> Any | None:
    """
    Load the Pygments HTML formatter when code highlighting is available.
    ```python
    load_html_formatter()

    return = Any | None
    ```
    """
    try:
        module = importlib.import_module("pygments.formatters")
    except ImportError:
        return None
    return getattr(module, "HtmlFormatter")


def find_pandoc_executable() -> str | None:
    """
    Find Pandoc for Markdown fallback rendering.
    ```python
    find_pandoc_executable()

    return = str | None
    ```
    """
    return shutil.which("pandoc")


def load_async_playwright() -> Any | None:
    """
    Load Playwright when browser rendering is requested.
    ```python
    load_async_playwright()

    return = Any | None
    ```
    """
    try:
        module = importlib.import_module("playwright.async_api")
    except ImportError:
        return None
    return getattr(module, "async_playwright")


def load_pillow_modules() -> tuple[Any, Any, Any]:
    """
    Load Pillow modules when fallback PNG rendering is requested.
    ```python
    load_pillow_modules()

    return = tuple[Any, Any, Any]
    ```
    """
    try:
        image_module = importlib.import_module("PIL.Image")
        image_draw_module = importlib.import_module("PIL.ImageDraw")
        image_font_module = importlib.import_module("PIL.ImageFont")
    except ImportError as exc:
        raise RuntimeError("Fallback PNG output requires: pip install pillow") from exc
    return image_module, image_draw_module, image_font_module


def strip_ansi(text: str) -> str:
    """
    Remove ANSI escape sequences from text.
    ```python
    strip_ansi("\\033[31mred\\033[0m")

    return = str
    ```
    """
    return re.sub(r"\x1b\[[0-9;]*m", "", text)


def get_ansi_color(code: int) -> str | None:
    """
    Map ANSI color code to hex color.
    ```python
    get_ansi_color(31)

    return = str | None
    ```
    """
    normal_colors = {
        30: "#3f4652",
        31: "#ff6b6b",
        32: "#7ee787",
        33: "#ffd166",
        34: "#79c0ff",
        35: "#d2a8ff",
        36: "#56d4dd",
        37: "#d8dee9",
    }
    bright_colors = {
        90: "#7d8590",
        91: "#ff8a8a",
        92: "#9be9a8",
        93: "#ffe08a",
        94: "#a5d6ff",
        95: "#e2c5ff",
        96: "#8be9fd",
        97: "#ffffff",
    }
    if code in normal_colors:
        return normal_colors[code]
    return bright_colors.get(code)


def get_ansi_background(code: int) -> str | None:
    """
    Map ANSI background color code to hex color.
    ```python
    get_ansi_background(41)

    return = str | None
    ```
    """
    color = get_ansi_color(code - 10)
    if color:
        return color
    return get_ansi_color(code - 60)


def apply_ansi_codes(style: AnsiStyle, codes: list[int]) -> AnsiStyle:
    """
    Apply ANSI SGR codes to the current style.
    ```python
    apply_ansi_codes(AnsiStyle(), [1, 31])

    return = AnsiStyle
    ```
    """
    current = AnsiStyle(style.foreground, style.background, style.bold)
    for code in codes:
        if code == 0:
            current = AnsiStyle()
        elif code == 1:
            current.bold = True
        elif code == 22:
            current.bold = False
        elif code == 39:
            current.foreground = None
        elif code == 49:
            current.background = None
        elif 30 <= code <= 37 or 90 <= code <= 97:
            current.foreground = get_ansi_color(code)
        elif 40 <= code <= 47 or 100 <= code <= 107:
            current.background = get_ansi_background(code)
    return current


def wrap_html_segment(text: str, style: AnsiStyle) -> str:
    """
    Escape a text segment and wrap it with a span when style is active.
    ```python
    wrap_html_segment("red", AnsiStyle(foreground="#ff0000"))

    return = str
    ```
    """
    escaped = html.escape(text)
    css = style.to_css()
    if not css:
        return escaped
    return f'<span style="{css}">{escaped}</span>'


def ansi_to_html(text: str) -> str:
    """
    Convert ANSI-colored text to escaped HTML fragments.
    ```python
    ansi_to_html("\\033[31mred\\033[0m")

    return = str
    ```
    """
    pattern = re.compile(r"\x1b\[([0-9;]*)m")
    position = 0
    style = AnsiStyle()
    parts = []

    for match in pattern.finditer(text):
        if match.start() > position:
            parts.append(wrap_html_segment(text[position : match.start()], style))
        raw_codes = match.group(1) or "0"
        codes = [int(code) for code in raw_codes.split(";") if code]
        style = apply_ansi_codes(style, codes)
        position = match.end()

    if position < len(text):
        parts.append(wrap_html_segment(text[position:], style))
    return "".join(parts)


def append_ansi_segment(
    lines: list[list[tuple[str, AnsiStyle]]], segment: str, style: AnsiStyle
) -> None:
    """
    Append a styled ANSI segment to split line runs.
    ```python
    append_ansi_segment(lines, "text", AnsiStyle())

    return = None
    ```
    """
    chunks = segment.split("\n")
    for index, chunk in enumerate(chunks):
        if chunk:
            lines[-1].append(
                (chunk, AnsiStyle(style.foreground, style.background, style.bold))
            )
        if index < len(chunks) - 1:
            lines.append([])


def ansi_to_line_runs(text: str) -> list[list[tuple[str, AnsiStyle]]]:
    """
    Convert ANSI-colored text to line-based styled runs.
    ```python
    ansi_to_line_runs("\\033[31mred\\033[0m")

    return = list[list[tuple[str, AnsiStyle]]]
    ```
    """
    pattern = re.compile(r"\x1b\[([0-9;]*)m")
    position = 0
    style = AnsiStyle()
    lines: list[list[tuple[str, AnsiStyle]]] = [[]]

    for match in pattern.finditer(text):
        if match.start() > position:
            append_ansi_segment(lines, text[position : match.start()], style)
        raw_codes = match.group(1) or "0"
        codes = [int(code) for code in raw_codes.split(";") if code]
        style = apply_ansi_codes(style, codes)
        position = match.end()

    if position < len(text):
        append_ansi_segment(lines, text[position:], style)
    return lines


def read_input(source: str) -> str:
    """
    Read input from a file path or stdin marker.
    ```python
    read_input("@-")

    return = str
    ```
    """
    if source == "@-":
        return sys.stdin.read()
    return Path(source).read_text(encoding="utf-8", errors="replace")


def detect_input_format(source: str, requested_format: str) -> str:
    """
    Detect input format when auto mode is selected.
    ```python
    detect_input_format("README.md", "auto")

    return = str
    ```
    """
    if requested_format != "auto":
        return requested_format
    if source != "@-" and Path(source).suffix.lower() in {".md", ".markdown", ".mdown"}:
        return "markdown"
    return "text"


def detect_output_format(output: Path | None, requested_format: str) -> str:
    """
    Detect output format from file extension when auto mode is selected.
    ```python
    detect_output_format(Path("out.png"), "auto")

    return = str
    ```
    """
    if requested_format != "auto":
        return requested_format
    if not output:
        return "png"
    suffix = output.suffix.lower().lstrip(".")
    if suffix in {"png", "pdf", "html"}:
        return suffix
    return "png"


def default_output_path(source: str, output_format: str) -> Path:
    """
    Build a default output path for the selected format.
    ```python
    default_output_path("README.md", "png")

    return = Path
    ```
    """
    extension = "html" if output_format == "raw-html" else output_format
    if source == "@-":
        return Path.cwd() / f"rendered.{extension}"
    filename = Path(source).with_suffix(f".{extension}").name
    return Path.cwd() / filename


def get_source_base_dir(source: str) -> Path:
    """
    Get the base directory used to resolve document-relative assets.
    ```python
    get_source_base_dir("README.md")

    return = Path
    ```
    """
    if source == "@-":
        return Path.cwd()
    return Path(source).expanduser().resolve().parent


def get_base_href(base_dir: Path) -> str:
    """
    Convert a local directory to a file URL base href.
    ```python
    get_base_href(Path.cwd())

    return = str
    ```
    """
    return base_dir.as_uri().rstrip("/") + "/"


def is_external_image_source(source: str) -> bool:
    """
    Check whether an image source should not be resolved as a local path.
    ```python
    is_external_image_source("https://example.com/a.png")

    return = bool
    ```
    """
    parsed = urlparse(source)
    return bool(parsed.scheme or parsed.netloc or source.startswith("#"))


def resolve_image_source(source: str, base_dir: Path) -> str:
    """
    Resolve a Markdown image source against the input document directory.
    ```python
    resolve_image_source("./assets/a.png", Path.cwd())

    return = str
    ```
    """
    if is_external_image_source(source):
        return source

    parsed = urlparse(source)
    image_path = Path(unquote(parsed.path))
    if not image_path.is_absolute():
        image_path = base_dir / image_path
    resolved = image_path.expanduser().resolve().as_uri()
    if parsed.query:
        return f"{resolved}?{parsed.query}"
    return resolved


def resolve_html_image_sources(body: str, base_dir: Path) -> str:
    """
    Convert local HTML image sources to absolute file URIs.
    ```python
    resolve_html_image_sources('<img src="./a.png">', Path.cwd())

    return = str
    ```
    """
    pattern = re.compile(r'(<img\b[^>]*?\bsrc\s*=\s*)(["\'])(.*?)(\2)', re.IGNORECASE)

    def replace_source(match: re.Match[str]) -> str:
        prefix = match.group(1)
        quote = match.group(2)
        source = match.group(3)
        resolved = resolve_image_source(source, base_dir)
        return f"{prefix}{quote}{html.escape(resolved, quote=True)}{quote}"

    return pattern.sub(replace_source, body)


def get_pygments_css(theme: str) -> str:
    """
    Build CSS for highlighted code blocks.
    ```python
    get_pygments_css("terminal")

    return = str
    ```
    """
    html_formatter = load_html_formatter()
    if html_formatter is None:
        return ""
    style_name = "monokai" if theme == "terminal" else "default"
    return html_formatter(style=style_name).get_style_defs(".codehilite")


def render_markdown_with_pandoc(text: str) -> str:
    """
    Convert Markdown to HTML with Pandoc when the Python package is unavailable.
    ```python
    render_markdown_with_pandoc("# Title")

    return = str
    ```
    """
    pandoc_path = find_pandoc_executable()
    if not pandoc_path:
        raise RuntimeError(
            "Markdown input requires: pip install markdown, or install pandoc"
        )
    command = [pandoc_path, "--from", "gfm", "--to", "html"]
    result = subprocess.run(
        command,
        input=text,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
        text=True,
    )
    return result.stdout


def render_markdown_body(text: str, theme: str, base_dir: Path) -> str:
    """
    Convert Markdown text to HTML body fragments.
    ```python
    render_markdown_body("# Title", "terminal", Path.cwd())

    return = str
    ```
    """
    markdown_module = load_markdown_module()
    if markdown_module is None:
        return resolve_html_image_sources(render_markdown_with_pandoc(text), base_dir)

    html_formatter = load_html_formatter()
    extension_configs: dict[str, Any] = {}
    extensions = ["extra", "sane_lists", "toc"]
    if html_formatter is not None:
        extensions.append("codehilite")
        extension_configs["codehilite"] = {
            "guess_lang": False,
            "use_pygments": True,
            "pygments_style": "monokai" if theme == "terminal" else "default",
        }
    body = markdown_module.markdown(
        text,
        extensions=extensions,
        extension_configs=extension_configs,
        output_format="html5",
    )
    return resolve_html_image_sources(body, base_dir)


def render_text_body(text: str, input_format: str, wrap: bool) -> str:
    """
    Convert plain text or ANSI text to HTML body fragments.
    ```python
    render_text_body("hello", "text", True)

    return = str
    ```
    """
    css_class = "text-output wrap" if wrap else "text-output nowrap"
    if input_format == "ansi":
        content = ansi_to_html(text)
    else:
        content = ansi_to_html(text) if "\033[" in text else html.escape(text)
    return f'<pre class="{css_class}">{content}</pre>'


def render_raw_html(text: str, input_format: str, theme: str, base_dir: Path) -> str:
    """
    Render minimal HTML without embedded style rules.
    ```python
    render_raw_html("# Title", "markdown", "terminal", Path.cwd())

    return = str
    ```
    """
    if input_format == "markdown":
        return render_markdown_body(text, theme, base_dir)
    return f"<pre>{html.escape(strip_ansi(text))}</pre>"


def get_theme_css(theme: str, options: RenderOptions) -> str:
    """
    Build document CSS for the selected theme.
    ```python
    get_theme_css("terminal", options)

    return = str
    ```
    """
    foreground = "#d8dee9"
    background = "#0d1117"
    surface = "#161b22"
    border = "#30363d"
    link = "#79c0ff"
    code_background = "#0d1117"

    if theme == "light":
        foreground = "#24292f"
        background = "#ffffff"
        surface = "#f6f8fa"
        border = "#d0d7de"
        link = "#0969da"
        code_background = "#f6f8fa"
    elif theme == "print":
        foreground = "#111111"
        background = "#ffffff"
        surface = "#ffffff"
        border = "#cccccc"
        link = "#111111"
        code_background = "#f7f7f7"

    white_space = "pre-wrap" if options.wrap else "pre"
    overflow_wrap = "break-word" if options.wrap else "normal"
    pygments_css = get_pygments_css(theme)

    return f"""
        :root {{
            color-scheme: {"dark" if theme == "terminal" else "light"};
        }}
        * {{
            box-sizing: border-box;
        }}
        body {{
            margin: 0;
            background: {background};
            color: {foreground};
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI",
                "Noto Sans CJK SC", "Noto Sans CJK", "Noto Sans",
                "Helvetica Neue", Arial, sans-serif;
            font-size: {options.font_size}px;
            line-height: 1.55;
        }}
        .page {{
            width: min({options.width}px, 100vw);
            margin: 0 auto;
            padding: {options.padding}px;
        }}
        .document {{
            max-width: {options.width - options.padding * 2}px;
        }}
        a {{
            color: {link};
        }}
        h1, h2, h3, h4, h5, h6 {{
            line-height: 1.25;
            margin: 1.25em 0 0.6em;
        }}
        h1:first-child, h2:first-child, h3:first-child {{
            margin-top: 0;
        }}
        p, ul, ol, blockquote, table, pre {{
            margin: 0 0 1em;
        }}
        blockquote {{
            border-left: 4px solid {border};
            color: {foreground};
            margin-left: 0;
            padding-left: 1em;
        }}
        code {{
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas,
                "Liberation Mono", "DejaVu Sans Mono", monospace;
            background: {code_background};
            border-radius: 4px;
            padding: 0.1em 0.35em;
        }}
        pre, .codehilite {{
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas,
                "Liberation Mono", "DejaVu Sans Mono", monospace;
            background: {surface};
            border: 1px solid {border};
            border-radius: 8px;
            overflow: auto;
            padding: 1em;
        }}
        pre code, .codehilite code {{
            background: transparent;
            padding: 0;
        }}
        .text-output {{
            font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas,
                "Liberation Mono", "DejaVu Sans Mono", monospace;
            white-space: {white_space};
            overflow-wrap: {overflow_wrap};
        }}
        .nowrap {{
            white-space: pre;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
        }}
        th, td {{
            border: 1px solid {border};
            padding: 0.45em 0.65em;
            vertical-align: top;
        }}
        th {{
            background: {surface};
        }}
        img {{
            display: block;
            height: auto;
            margin: 0.7em 0 1.3em;
            max-width: 100%;
        }}
        {pygments_css}
    """


def build_full_html(body: str, options: RenderOptions) -> str:
    """
    Wrap body fragments in a complete HTML document.
    ```python
    build_full_html("<pre>hello</pre>", options)

    return = str
    ```
    """
    css = get_theme_css(options.theme, options)
    base_href = html.escape(get_base_href(options.source_base_dir), quote=True)
    return f"""<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<base href="{base_href}">
<style>
{css}
</style>
</head>
<body>
<main class="page">
<article class="document">
{body}
</article>
</main>
</body>
</html>
"""


def build_html_document(
    text: str, input_format: str, output_format: str, options: RenderOptions
) -> str:
    """
    Convert source text to the requested HTML form.
    ```python
    build_html_document("hello", "text", "html", options)

    return = str
    ```
    """
    if output_format == "raw-html":
        return render_raw_html(text, input_format, options.theme, options.source_base_dir)
    if input_format == "markdown":
        body = render_markdown_body(text, options.theme, options.source_base_dir)
    else:
        body = render_text_body(text, input_format, options.wrap)
    return build_full_html(body, options)


def write_text_output(output: Path, content: str) -> None:
    """
    Write text output to disk.
    ```python
    write_text_output(Path("out.html"), "<html></html>")

    return = None
    ```
    """
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(content, encoding="utf-8")


async def render_with_playwright(
    html_content: str, options: RenderOptions, async_playwright: Any
) -> None:
    """
    Render HTML to PNG or PDF through Chromium.
    ```python
    await render_with_playwright("<html></html>", options, async_playwright)

    return = None
    ```
    """
    options.output.parent.mkdir(parents=True, exist_ok=True)
    temp_file = tempfile.NamedTemporaryFile(
        "w", suffix=".html", delete=False, encoding="utf-8"
    )
    temp_path = Path(temp_file.name)
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch()
        try:
            temp_file.write(html_content)
            temp_file.close()
            page = await browser.new_page(
                viewport={"width": options.width, "height": 900},
                device_scale_factor=options.scale,
            )
            await page.goto(temp_path.as_uri(), wait_until="networkidle")
            if options.output_format == "png":
                await page.screenshot(path=str(options.output), full_page=True)
            else:
                await page.pdf(
                    path=str(options.output),
                    print_background=True,
                    width=f"{options.width}px",
                )
        finally:
            await browser.close()
            temp_file.close()
            temp_path.unlink(missing_ok=True)


def find_chrome_executable() -> str | None:
    """
    Find a Chrome or Chromium executable for fallback rendering.
    ```python
    find_chrome_executable()

    return = str | None
    ```
    """
    for command in ("google-chrome", "chromium", "chromium-browser", "chrome"):
        executable = shutil.which(command)
        if executable:
            return executable
    return None


def find_monospace_font() -> str | None:
    """
    Find a common monospace font on Linux.
    ```python
    find_monospace_font()

    return = str | None
    ```
    """
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationMono-Regular.ttf",
        "/usr/share/fonts/opentype/noto/NotoSansMono-Regular.ttf",
        "/usr/share/fonts/truetype/ubuntu/UbuntuMono-R.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return candidate
    return None


def find_sans_font(bold: bool = False) -> str | None:
    """
    Find a readable sans font with CJK support.
    ```python
    find_sans_font(True)

    return = str | None
    ```
    """
    candidates = [
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
        "/usr/share/fonts/truetype/noto/NotoSans-Bold.ttf",
        "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    ]
    regular_candidates = [candidate for candidate in candidates if "Bold" not in candidate]
    selected_candidates = candidates if bold else regular_candidates
    for candidate in selected_candidates:
        if Path(candidate).exists():
            return candidate
    return None


def load_sans_font(image_font_module: Any, font_size: int, bold: bool = False) -> Any:
    """
    Load a sans font for Markdown fallback rendering.
    ```python
    load_sans_font(ImageFont, 18, True)

    return = Any
    ```
    """
    font_path = find_sans_font(bold)
    if font_path:
        return image_font_module.truetype(font_path, font_size)
    return image_font_module.load_default()


def strip_inline_markdown(text: str) -> str:
    """
    Strip simple inline Markdown marks for fallback rendering.
    ```python
    strip_inline_markdown("**title**")

    return = str
    ```
    """
    text = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    return text.strip()


def parse_markdown_image(line: str) -> tuple[str, str] | None:
    """
    Parse a Markdown image line.
    ```python
    parse_markdown_image("![alt](./a.png)")

    return = tuple[str, str] | None
    ```
    """
    match = re.match(r"!\[([^\]]*)\]\(([^)]+)\)", line.strip())
    if not match:
        return None
    return match.group(1), match.group(2)


def get_local_image_path(source: str, base_dir: Path) -> Path | None:
    """
    Convert a local image source to a filesystem path.
    ```python
    get_local_image_path("./assets/a.png", Path.cwd())

    return = Path | None
    ```
    """
    if is_external_image_source(source):
        parsed = urlparse(source)
        if parsed.scheme != "file":
            return None
        return Path(unquote(parsed.path))
    parsed = urlparse(source)
    image_path = Path(unquote(parsed.path))
    if not image_path.is_absolute():
        image_path = base_dir / image_path
    return image_path.expanduser().resolve()


def wrap_text_by_width(draw: Any, text: str, font: Any, max_width: int) -> list[str]:
    """
    Wrap text by rendered pixel width.
    ```python
    wrap_text_by_width(draw, "hello", font, 300)

    return = list[str]
    ```
    """
    lines = []
    current = ""
    for char in text:
        candidate = current + char
        if current and draw.textlength(candidate, font=font) > max_width:
            lines.append(current.rstrip())
            current = char.lstrip()
        else:
            current = candidate
    if current:
        lines.append(current.rstrip())
    return lines or [""]


def collect_markdown_fallback_blocks(text: str) -> list[dict[str, Any]]:
    """
    Collect simple Markdown blocks for Pillow fallback rendering.
    ```python
    collect_markdown_fallback_blocks("# Title")

    return = list[dict[str, Any]]
    ```
    """
    blocks: list[dict[str, Any]] = []
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line:
            blocks.append({"type": "space"})
            continue

        image = parse_markdown_image(line)
        if image:
            blocks.append({"type": "image", "alt": image[0], "source": image[1]})
            continue

        heading = re.match(r"^(#{1,6})\s+(.+)$", line)
        if heading:
            blocks.append(
                {
                    "type": "heading",
                    "level": len(heading.group(1)),
                    "text": strip_inline_markdown(heading.group(2)),
                }
            )
            continue

        block_type = "strong" if line.startswith("**") and line.endswith("**") else "text"
        blocks.append({"type": block_type, "text": strip_inline_markdown(line)})
    return blocks


def draw_markdown_text_block(
    draw: Any,
    block: dict[str, Any],
    fonts: dict[str, Any],
    x: int,
    y: int,
    max_width: int,
    color: str,
) -> int:
    """
    Draw one Markdown text block and return the next y position.
    ```python
    draw_markdown_text_block(draw, block, fonts, 0, 0, 800, "#111")

    return = int
    ```
    """
    block_type = block["type"]
    font = fonts.get(block_type, fonts["text"])
    text = str(block.get("text", ""))
    lines = wrap_text_by_width(draw, text, font, max_width)
    bbox = draw.textbbox((0, 0), "Hg", font=font)
    line_height = int((bbox[3] - bbox[1]) * 1.45)
    for line in lines:
        draw.text((x, y), line, font=font, fill=color)
        y += line_height
    if block_type == "heading":
        return y + 18
    return y + 14


def measure_markdown_blocks(
    text: str,
    options: RenderOptions,
    image_module: Any,
    image_draw_module: Any,
    fonts: dict[str, Any],
) -> tuple[list[dict[str, Any]], int]:
    """
    Measure Markdown fallback blocks before drawing.
    ```python
    measure_markdown_blocks("# Title", options, Image, ImageDraw, fonts)

    return = tuple[list[dict[str, Any]], int]
    ```
    """
    blocks = collect_markdown_fallback_blocks(text)
    probe = image_module.new("RGB", (10, 10), "#ffffff")
    draw = image_draw_module.Draw(probe)
    max_width = options.width - options.padding * 2
    height = options.padding
    for block in blocks:
        if block["type"] == "space":
            height += 12
        elif block["type"] == "image":
            image_path = get_local_image_path(str(block["source"]), options.source_base_dir)
            if image_path and image_path.exists():
                with image_module.open(image_path) as image:
                    scale = min(1.0, max_width / image.width)
                    block["size"] = (int(image.width * scale), int(image.height * scale))
                    height += block["size"][1] + 24
            else:
                block["missing"] = True
                height += 32
        else:
            before = height
            height = draw_markdown_text_block(
                draw, block, fonts, 0, height, max_width, "#111111"
            )
            block["height"] = height - before
    return blocks, height + options.padding


def render_markdown_with_pillow(text: str, options: RenderOptions) -> None:
    """
    Render simple Markdown and local images to PNG through Pillow.
    ```python
    render_markdown_with_pillow("# Title", options)

    return = None
    ```
    """
    image_module, image_draw_module, image_font_module = load_pillow_modules()
    background, surface, border, foreground = get_pillow_theme_colors(options.theme)
    fonts = {
        "heading": load_sans_font(image_font_module, 34, True),
        "strong": load_sans_font(image_font_module, 22, True),
        "text": load_sans_font(image_font_module, 20),
    }
    blocks, image_height = measure_markdown_blocks(
        text, options, image_module, image_draw_module, fonts
    )
    image = image_module.new("RGB", (options.width, image_height), background)
    draw = image_draw_module.Draw(image)
    max_width = options.width - options.padding * 2
    x = options.padding
    y = options.padding

    for block in blocks:
        if block["type"] == "space":
            y += 12
        elif block["type"] == "image":
            image_path = get_local_image_path(str(block["source"]), options.source_base_dir)
            y = render_markdown_pillow_image(
                image, image_module, image_draw_module, image_path, block, x, y, max_width, border
            )
        else:
            y = draw_markdown_text_block(
                draw, block, fonts, x, y, max_width, foreground
            )

    options.output.parent.mkdir(parents=True, exist_ok=True)
    image.save(options.output)


def render_markdown_pillow_image(
    canvas: Any,
    image_module: Any,
    image_draw_module: Any,
    image_path: Path | None,
    block: dict[str, Any],
    x: int,
    y: int,
    max_width: int,
    border: str,
) -> int:
    """
    Draw one Markdown image block in Pillow fallback rendering.
    ```python
    render_markdown_pillow_image(canvas, Image, ImageDraw, Path("a.png"), block, 0, 0, 800, "#ccc")

    return = int
    ```
    """
    if not image_path or not image_path.exists():
        return y + 32

    with image_module.open(image_path) as source_image:
        source_image = source_image.convert("RGB")
        scale = min(1.0, max_width / source_image.width)
        size = (int(source_image.width * scale), int(source_image.height * scale))
        resized = source_image.resize(size)
    canvas.paste(resized, (x, y))
    draw = image_draw_module.Draw(canvas)
    draw.rectangle([x, y, x + size[0], y + size[1]], outline=border)
    return y + size[1] + 24


def estimate_chrome_height(text: str, options: RenderOptions) -> int:
    """
    Estimate viewport height for headless Chrome screenshots.
    ```python
    estimate_chrome_height("a\\nb", options)

    return = int
    ```
    """
    line_count = max(1, text.count("\n") + 1)
    line_height = int(options.font_size * 1.65)
    estimated_height = options.padding * 2 + line_count * line_height + 160
    return max(900, min(30000, estimated_height))


def get_pillow_theme_colors(theme: str) -> tuple[str, str, str, str]:
    """
    Get colors for Pillow fallback rendering.
    ```python
    get_pillow_theme_colors("terminal")

    return = tuple[str, str, str, str]
    ```
    """
    if theme == "light":
        return "#ffffff", "#f6f8fa", "#d0d7de", "#24292f"
    if theme == "print":
        return "#ffffff", "#ffffff", "#cccccc", "#111111"
    return "#0d1117", "#161b22", "#30363d", "#d8dee9"


def load_pillow_font(image_font_module: Any, font_size: int) -> Any:
    """
    Load a monospace font for Pillow rendering.
    ```python
    load_pillow_font(ImageFont, 16)

    return = Any
    ```
    """
    font_path = find_monospace_font()
    if font_path:
        return image_font_module.truetype(font_path, font_size)
    return image_font_module.load_default()


def measure_line_width(draw: Any, line: list[tuple[str, AnsiStyle]], font: Any) -> int:
    """
    Measure a styled line for Pillow rendering.
    ```python
    measure_line_width(draw, [("text", AnsiStyle())], font)

    return = int
    ```
    """
    width = 0.0
    for segment, style in line:
        width += draw.textlength(segment, font=font)
        if style.bold:
            width += 1
    return int(width)


def render_with_pillow(text: str, options: RenderOptions) -> None:
    """
    Render plain text or ANSI text to PNG through Pillow.
    ```python
    render_with_pillow("hello", options)

    return = None
    ```
    """
    image_module, image_draw_module, image_font_module = load_pillow_modules()
    background, surface, border, foreground = get_pillow_theme_colors(options.theme)
    font = load_pillow_font(image_font_module, options.font_size)
    probe = image_module.new("RGB", (10, 10), background)
    draw = image_draw_module.Draw(probe)
    line_runs = (
        ansi_to_line_runs(text)
        if "\033[" in text
        else [[(line, AnsiStyle())] for line in text.split("\n")]
    )
    text_bbox = draw.textbbox((0, 0), "Mg", font=font)
    line_height = max(16, int((text_bbox[3] - text_bbox[1]) * 1.55))
    inner_padding = max(12, options.padding // 2)
    content_width = (
        max(measure_line_width(draw, line, font) for line in line_runs)
        if line_runs
        else 0
    )
    image_width = max(
        options.width, int(content_width) + options.padding * 2 + inner_padding * 2
    )
    image_height = (
        options.padding * 2 + inner_padding * 2 + max(1, len(line_runs)) * line_height
    )

    image = image_module.new("RGB", (image_width, image_height), background)
    draw = image_draw_module.Draw(image)
    box = [
        options.padding,
        options.padding,
        image_width - options.padding,
        image_height - options.padding,
    ]
    draw.rounded_rectangle(box, radius=8, fill=surface, outline=border, width=1)

    y = options.padding + inner_padding
    for line in line_runs:
        x = options.padding + inner_padding
        for segment, style in line:
            fill = style.foreground or foreground
            if style.background:
                segment_width = draw.textlength(segment, font=font)
                draw.rectangle(
                    [x, y, x + segment_width, y + line_height], fill=style.background
                )
            draw.text((x, y), segment, font=font, fill=fill)
            if style.bold:
                draw.text((x + 1, y), segment, font=font, fill=fill)
            x += draw.textlength(segment, font=font)
        y += line_height

    options.output.parent.mkdir(parents=True, exist_ok=True)
    image.save(options.output)


def render_with_chrome_cli(
    html_content: str, options: RenderOptions, text: str, chrome_path: str
) -> None:
    """
    Render HTML to PNG or PDF through a headless Chrome executable.
    ```python
    render_with_chrome_cli("<html></html>", options, "text", "/usr/bin/google-chrome")

    return = None
    ```
    """
    options.output.parent.mkdir(parents=True, exist_ok=True)
    temp_file = tempfile.NamedTemporaryFile(
        "w", suffix=".html", delete=False, encoding="utf-8"
    )
    temp_path = Path(temp_file.name)
    try:
        temp_file.write(html_content)
        temp_file.close()
        window_height = estimate_chrome_height(text, options)
        command = [
            chrome_path,
            "--headless=new",
            "--disable-gpu",
            "--no-sandbox",
            f"--window-size={options.width},{window_height}",
        ]
        if options.output_format == "png":
            command.append(f"--screenshot={options.output}")
        else:
            command.append(f"--print-to-pdf={options.output}")
        command.append(temp_path.as_uri())
        debug("chrome", " ".join(command))
        subprocess.run(
            command,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
    finally:
        temp_file.close()
        temp_path.unlink(missing_ok=True)


def render_browser_output(html_content: str, options: RenderOptions, text: str) -> None:
    """
    Render browser-backed output using Playwright or headless Chrome.
    ```python
    render_browser_output("<html></html>", options, "text")

    return = None
    ```
    """
    async_playwright = load_async_playwright()
    if async_playwright is not None:
        try:
            asyncio.run(render_with_playwright(html_content, options, async_playwright))
            return
        except Exception as exc:
            debug("playwright fallback failed", exc)

    chrome_path = find_chrome_executable()
    if chrome_path:
        try:
            render_with_chrome_cli(html_content, options, text, chrome_path)
            return
        except subprocess.SubprocessError as exc:
            debug("chrome fallback failed", exc)

    if options.output_format == "png" and options.input_format == "markdown":
        render_markdown_with_pillow(text, options)
        return

    if options.output_format == "png":
        render_with_pillow(text, options)
        return

    raise RuntimeError(
        "This output requires Playwright or a working Chrome: "
        "pip install playwright && playwright install chromium"
    )


def create_parser() -> argparse.ArgumentParser:
    """
    Create command line parser.
    ```python
    create_parser()

    return = argparse.ArgumentParser
    ```
    """
    script_name = Path(sys.argv[0]).name
    examples = [
        ("Render plain text to PNG", "help.txt -o help.png"),
        ("Render Markdown to PDF", "README.md -o README.pdf"),
        ("Render Markdown to styled HTML", "README.md -f html -o README.html"),
        ("Render body-only HTML", "README.md -f raw-html -o body.html"),
        ("Read command output from stdin", "@- --input-format ansi -o command.png"),
    ]
    notes = [
        "Input format auto-detects Markdown by file extension.",
        "Default output is written to the current working directory.",
        "Markdown relative image paths are resolved from the input file directory.",
        "PNG and PDF output use Playwright Chromium or headless Chrome when available.",
        "Plain text PNG can fall back to Pillow when browser rendering is unavailable.",
        "Markdown uses the markdown package first, then falls back to Pandoc.",
        "Markdown code highlighting uses Pygments when installed.",
        "Use @- to read from stdin.",
    ]
    parser = ColoredArgumentParser(
        description="Render text, ANSI terminal output, or Markdown to HTML, PNG, or PDF.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=create_example_text(script_name, examples, notes),
    )
    parser.add_argument(
        "source",
        metavar=CLIStyle.color("INPUT", CLIStyle.COLORS["CONTENT"]),
        help=CLIStyle.color(
            "Input file path, or @- for stdin", CLIStyle.COLORS["CONTENT"]
        ),
    )
    parser.add_argument(
        "-o",
        "--output",
        metavar=CLIStyle.color("PATH", CLIStyle.COLORS["CONTENT"]),
        help=CLIStyle.color(
            "Output path. Format is inferred from extension by default",
            CLIStyle.COLORS["CONTENT"],
        ),
    )
    parser.add_argument(
        "-f",
        "--format",
        choices=["auto", "png", "pdf", "html", "raw-html"],
        default="auto",
        metavar=CLIStyle.color("FORMAT", CLIStyle.COLORS["CONTENT"]),
        help=CLIStyle.color(
            "Output format: auto, png, pdf, html, raw-html", CLIStyle.COLORS["CONTENT"]
        ),
    )
    parser.add_argument(
        "--input-format",
        choices=["auto", "text", "markdown", "ansi"],
        default="auto",
        metavar=CLIStyle.color("FORMAT", CLIStyle.COLORS["CONTENT"]),
        help=CLIStyle.color(
            "Input format: auto, text, markdown, ansi", CLIStyle.COLORS["CONTENT"]
        ),
    )
    parser.add_argument(
        "--theme",
        choices=["terminal", "light", "print"],
        default="light",
        metavar=CLIStyle.color("THEME", CLIStyle.COLORS["CONTENT"]),
        help=CLIStyle.color(
            "Theme for styled HTML, PNG, and PDF", CLIStyle.COLORS["CONTENT"]
        ),
    )
    parser.add_argument(
        "--width",
        type=int,
        default=1440,
        metavar=CLIStyle.color("PX", CLIStyle.COLORS["CONTENT"]),
        help=CLIStyle.color(
            "Render viewport width in pixels", CLIStyle.COLORS["CONTENT"]
        ),
    )
    parser.add_argument(
        "--font-size",
        type=int,
        default=16,
        metavar=CLIStyle.color("PX", CLIStyle.COLORS["CONTENT"]),
        help=CLIStyle.color("Base font size in pixels", CLIStyle.COLORS["CONTENT"]),
    )
    parser.add_argument(
        "--padding",
        type=int,
        default=28,
        metavar=CLIStyle.color("PX", CLIStyle.COLORS["CONTENT"]),
        help=CLIStyle.color("Page padding in pixels", CLIStyle.COLORS["CONTENT"]),
    )
    parser.add_argument(
        "--scale",
        type=float,
        default=2.0,
        metavar=CLIStyle.color("RATIO", CLIStyle.COLORS["CONTENT"]),
        help=CLIStyle.color("PNG device scale factor", CLIStyle.COLORS["CONTENT"]),
    )
    parser.add_argument(
        "--no-wrap",
        action="store_true",
        help=CLIStyle.color("Keep long lines unwrapped", CLIStyle.COLORS["CONTENT"]),
    )
    parser.add_argument(
        "--log",
        action="store_true",
        help=CLIStyle.color("Enable debug output", CLIStyle.COLORS["CONTENT"]),
    )
    return parser


def parse_options(args: argparse.Namespace) -> RenderOptions:
    """
    Convert argparse namespace to render options.
    ```python
    parse_options(args)

    return = RenderOptions
    ```
    """
    explicit_output = Path(args.output) if args.output else None
    output_format = detect_output_format(explicit_output, args.format)
    output = explicit_output or default_output_path(args.source, output_format)
    input_format = detect_input_format(args.source, args.input_format)
    source_base_dir = get_source_base_dir(args.source)
    return RenderOptions(
        source=args.source,
        output=output,
        input_format=input_format,
        output_format=output_format,
        theme=args.theme,
        width=args.width,
        font_size=args.font_size,
        padding=args.padding,
        scale=args.scale,
        wrap=not args.no_wrap,
        source_base_dir=source_base_dir,
    )


def validate_options(options: RenderOptions) -> None:
    """
    Validate render options before output is generated.
    ```python
    validate_options(options)

    return = None
    ```
    """
    if options.width < 320:
        raise ValueError("--width must be at least 320")
    if options.font_size < 8:
        raise ValueError("--font-size must be at least 8")
    if options.padding < 0:
        raise ValueError("--padding must be zero or greater")
    if options.scale <= 0:
        raise ValueError("--scale must be greater than zero")


def run_render(options: RenderOptions) -> None:
    """
    Run the selected render pipeline.
    ```python
    run_render(options)

    return = None
    ```
    """
    validate_options(options)
    debug("options", options)
    text = read_input(options.source)
    html_content = build_html_document(
        text, options.input_format, options.output_format, options
    )
    if options.output_format in {"html", "raw-html"}:
        write_text_output(options.output, html_content)
    else:
        render_browser_output(html_content, options, text)
    CLIStyle.print(f"Wrote {options.output}", CLIStyle.COLORS["CONTENT"])


def main() -> int:
    """
    Main program logic.
    ```python
    main()

    return = int
    ```
    """
    global DEBUG_MODE
    parser = create_parser()
    args = parser.parse_args()
    DEBUG_MODE = args.log

    try:
        options = parse_options(args)
        run_render(options)
        return 0
    except FileNotFoundError as exc:
        CLIStyle.print(
            f"Error: file not found: {exc.filename}", CLIStyle.COLORS["ERROR"]
        )
        return 1
    except Exception as exc:
        if DEBUG_MODE:
            traceback.print_exc()
        CLIStyle.print(f"Error: {exc}", CLIStyle.COLORS["ERROR"])
        return 1


if __name__ == "__main__":
    sys.exit(main())
