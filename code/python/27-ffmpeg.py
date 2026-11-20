# -*- coding: utf-8 -*-
# pip install ffmpeg-python
"""Convert video clips to GIF or move MP4 metadata to the beginning."""

import argparse
import os
import re
import shlex
import shutil
import stat
import sys
import tempfile
import traceback
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, BinaryIO

try:
    import ffmpeg
except ImportError:
    ffmpeg = None


DEBUG_MODE = False


class CLIStyle:
    """Terminal colors shared by help and status messages."""

    COLORS = {"TITLE": 7, "SUB_TITLE": 2, "CONTENT": 3, "EXAMPLE": 7, "ERROR": 2}

    @staticmethod
    def color(text: str, color: int = 3) -> str:
        """Return text wrapped in an ANSI color."""
        return f"\033[1;3{color - 1}m{text}\033[0m" if color else text


class ColoredHelpFormatter(argparse.RawDescriptionHelpFormatter):
    """Color argument names and descriptions."""

    def _format_action_invocation(self, action: argparse.Action) -> str:
        """Color an argument's help invocation."""
        return CLIStyle.color(super()._format_action_invocation(action), 2)

    def _format_action(self, action: argparse.Action) -> str:
        """Color an argument's description."""
        original_help = action.help
        if original_help:
            action.help = CLIStyle.color(original_help, 3)
        try:
            return super()._format_action(action)
        finally:
            action.help = original_help


class ColoredArgumentParser(argparse.ArgumentParser):
    """Display colorized descriptions and section titles."""

    def format_help(self) -> str:
        """Format the parser's help with semantic colors."""
        formatter = self._get_formatter()
        if self.description:
            formatter.add_text(CLIStyle.color(self.description, 7))
        formatter.add_usage(self.usage, self._actions, self._mutually_exclusive_groups)
        for group in self._action_groups:
            formatter.start_section(CLIStyle.color(group.title, 7))
            formatter.add_arguments(group._group_actions)
            formatter.end_section()
        if self.epilog:
            formatter.add_text(self.epilog)
        return formatter.format_help()


def examples(items: list[str], notes: list[str]) -> str:
    """Create a colorized examples and notes block."""
    lines = [CLIStyle.color("Examples:", 2)]
    lines.extend(CLIStyle.color(f"  {item}", 7) for item in items)
    lines.append(CLIStyle.color("\nNotes:", 2))
    lines.extend(CLIStyle.color(f"  - {note}", 3) for note in notes)
    return "\n".join(lines)


def parse_time(value: str) -> Decimal:
    """Parse nonnegative seconds or HH:MM:SS[.fraction] as exact seconds."""
    if not re.fullmatch(r"(?:\d+:\d{2}:)?\d+(?:\.\d+)?", value):
        raise argparse.ArgumentTypeError("Use seconds or HH:MM:SS[.fraction].")
    parts = value.split(":")
    try:
        if len(parts) == 1:
            return Decimal(parts[0])
        hours, minutes, seconds = int(parts[0]), int(parts[1]), Decimal(parts[2])
        if minutes >= 60 or seconds >= 60:
            raise argparse.ArgumentTypeError("Minutes and seconds must be below 60.")
        return Decimal(hours * 3600 + minutes * 60) + seconds
    except (InvalidOperation, ValueError) as exc:
        raise argparse.ArgumentTypeError("Invalid timestamp.") from exc


def build_parser() -> argparse.ArgumentParser:
    """Build the command-line parser."""
    name = Path(sys.argv[0]).name
    common = {"formatter_class": ColoredHelpFormatter}
    parser = ColoredArgumentParser(
        description="Convert video to GIF or optimize MP4 for progressive playback.",
        epilog=examples(
            [f"{name} gif -s 1.25 -e 3.75 input.mp4 output.gif", f"{name} mp4 moov input.mp4"],
            ["Requires ffmpeg-python and the ffmpeg executable."],
        ),
        **common,
    )
    parser.add_argument("--log", action="store_true", help="Show the FFmpeg command and debug errors")
    commands = parser.add_subparsers(dest="function", metavar="FUNCTION", required=True)
    gif = commands.add_parser(
        "gif", help="Convert video to GIF", description="Convert a video or an accurately selected interval to GIF.",
        epilog=examples(
            [f"{name} gif -s 00:00:01.250 -e 00:00:03.750 input.mp4 output.gif"],
            ["Start is inclusive and end is exclusive; both are positions in the source.",
             "GIF timing is limited by source frames and GIF's 0.01-second resolution."],
        ), **common,
    )
    gif.add_argument("-s", "--start", type=parse_time, default=Decimal(0), metavar="TIME", help="Start position (default: 0)")
    gif.add_argument("-e", "--end", type=parse_time, metavar="TIME", help="End position in the source")
    gif.add_argument("src_file", metavar="SRC_FILE", help="Input video")
    gif.add_argument("target_file", metavar="TARGET_FILE", help="New GIF file")
    mp4 = commands.add_parser(
        "mp4", help="Process MP4 files", description="Process MP4 files without re-encoding.",
        epilog=examples(
            [f"{name} mp4 moov input.mp4"],
            ["Files with moov before media data are skipped.",
             "The source is replaced only after FFmpeg succeeds."],
        ), **common,
    )
    mp4_actions = mp4.add_subparsers(dest="mp4_action", metavar="ACTION", required=True)
    moov = mp4_actions.add_parser(
        "moov", help="Move MP4 metadata to the front",
        description="Move MP4 moov metadata before media data without re-encoding.",
        epilog=examples(
            [f"{name} mp4 moov input.mp4"],
            ["Files with moov before media data are skipped.",
             "The source is replaced only after FFmpeg succeeds."],
        ), **common,
    )
    moov.add_argument("src_file", metavar="MP4_FILE", help="MP4 file to update in place")
    return parser


def read_box(file: BinaryIO, position: int, end: int) -> tuple[bytes, int, int] | None:
    """Read and validate a box header within the given boundary."""
    if position + 8 > end:
        return None
    file.seek(position)
    header = file.read(8)
    if len(header) != 8:
        return None
    box_size = int.from_bytes(header[:4], "big")
    header_size = 8
    if box_size == 1:
        extended_size = file.read(8)
        if len(extended_size) != 8:
            return None
        box_size = int.from_bytes(extended_size, "big")
        header_size = 16
    elif box_size == 0:
        box_size = end - position
    if box_size < header_size or box_size > end - position:
        return None
    return header[4:], position + header_size, position + box_size


def moov_is_unfragmented(file: BinaryIO, position: int, end: int) -> bool:
    """Detect the movie-extends box that marks a fragmented MP4."""
    while position < end:
        child = read_box(file, position, end)
        if child is None or child[0] == b"mvex":
            return False
        position = child[2]
    return True


def moov_precedes_media(source: Path) -> bool:
    """Check for a complete front-loaded moov before the first media box."""
    file_size = source.stat().st_size
    position = 0
    found_moov = False
    with source.open("rb") as file:
        while position < file_size:
            box = read_box(file, position, file_size)
            if box is None:
                return False
            kind, content_start, box_end = box
            if kind == b"moov":
                found_moov = moov_is_unfragmented(file, content_start, box_end)
            elif kind == b"moof":
                return False
            elif kind == b"mdat":
                return found_moov
            position = box_end
    return False


def convert(args: argparse.Namespace) -> None:
    """Convert via a temporary file and publish the result after success."""
    source = Path(args.src_file).resolve(strict=True)
    if not source.is_file():
        raise ValueError(f"Input is not a regular file: {source}")
    in_place = args.function == "mp4"
    if in_place and moov_precedes_media(source):
        print(CLIStyle.color(f"Already optimized; skipped: {source}", 3))
        return
    if ffmpeg is None:
        raise RuntimeError("Missing ffmpeg-python; install it with: pip install ffmpeg-python")
    if not hasattr(ffmpeg, "input"):
        raise RuntimeError("Incorrect ffmpeg package; install ffmpeg-python, not ffmpeg.")
    if shutil.which("ffmpeg") is None:
        raise FileNotFoundError("The ffmpeg executable was not found in PATH.")

    if in_place:
        target = source
    else:
        target = Path(args.target_file).absolute()
        if target.exists() or target.is_symlink():
            raise FileExistsError(f"Output already exists: {target}")
    if args.function == "gif" and args.end is not None and args.end <= args.start:
        raise ValueError("End must be greater than start.")

    original_stat = source.stat()
    descriptor, temporary_name = tempfile.mkstemp(prefix=f".{target.name}.", suffix=".tmp", dir=target.parent)
    os.close(descriptor)
    temporary = Path(temporary_name)
    try:
        source_stream = ffmpeg.input(str(source))
        if args.function == "gif":
            options: dict[str, Any] = {"start": str(args.start)}
            if args.end is not None:
                options["end"] = str(args.end)
            video = source_stream.video.filter("trim", **options).filter("setpts", "PTS-STARTPTS")
            command = ffmpeg.output(video, str(temporary), format="gif", fps_mode="passthrough")
        else:
            command = ffmpeg.output(source_stream, str(temporary), format="mp4", map="0", c="copy", movflags="+faststart")
        command = command.global_args("-hide_banner", "-loglevel", "error", "-nostdin").overwrite_output()
        if DEBUG_MODE:
            print(CLIStyle.color(shlex.join(ffmpeg.compile(command)), 7), file=sys.stderr)
        try:
            ffmpeg.run(command)
        except ffmpeg.Error as exc:
            raise RuntimeError("FFmpeg failed; output was not replaced.") from exc
        if temporary.stat().st_size == 0:
            raise RuntimeError("FFmpeg produced an empty output; check the selected interval.")
        if in_place:
            current_stat = source.stat()
            if (current_stat.st_dev, current_stat.st_ino, current_stat.st_size, current_stat.st_mtime_ns) != (
                original_stat.st_dev, original_stat.st_ino, original_stat.st_size, original_stat.st_mtime_ns
            ):
                raise RuntimeError("Source changed during conversion; it was not replaced.")
            temporary.chmod(stat.S_IMODE(original_stat.st_mode))
            os.replace(temporary, target)
        else:
            os.link(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)
    print(CLIStyle.color(f"Created: {target}", 3))


def main() -> int:
    """Parse arguments and run the requested conversion."""
    global DEBUG_MODE
    args = build_parser().parse_args()
    DEBUG_MODE = args.log
    try:
        convert(args)
    except Exception as exc:
        if DEBUG_MODE:
            traceback.print_exc()
        print(CLIStyle.color(f"Error: {exc}", 2), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
