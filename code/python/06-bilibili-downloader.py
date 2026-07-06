# -*- coding: utf-8 -*-
# pip install requests argparse

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from datetime import datetime
from functools import reduce
from hashlib import md5
import re
from pathlib import Path
import time
from typing import Any, Dict, Iterable, List, Optional, Tuple
from urllib.parse import urlencode

if sys.platform == "win32":
    from colorama import init as colorama_init

    colorama_init(autoreset=True)

import requests

DEBUG_MODE = False

DEFAULT_HEADERS: Dict[str, str] = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "en-US,en;q=0.9",
    "Origin": "https://www.bilibili.com",
    "Referer": "https://www.bilibili.com",
    "Connection": "keep-alive",
}

PLAYER_API_URL = "https://api.bilibili.com/x/player/wbi/playurl"
VIDEO_DETAIL_API_URL = "https://api.bilibili.com/x/web-interface/view"
NAV_API_URL = "https://api.bilibili.com/x/web-interface/nav"
ENV_SESSDATA_KEY = "BILIBILI_SESSDATA"
CONFIG_FILE_NAME = ".bilibili-downloader.env"
CONFIG_FILE_ENV_KEY = "BILIBILI_DOWNLOADER_ENV"
DEFAULT_VIDEO_QUALITY = 64
DEFAULT_REQUEST_TIMEOUT = 25
CHUNK_SIZE = 1024 * 1024
BV_ID_REGEX = re.compile(r"BV[0-9A-Za-z]{10}")
MIXIN_KEY_TABLE: Tuple[int, ...] = (
    46,
    47,
    18,
    2,
    53,
    8,
    23,
    32,
    15,
    50,
    10,
    31,
    58,
    3,
    45,
    35,
    27,
    43,
    5,
    49,
    33,
    9,
    42,
    19,
    29,
    28,
    14,
    39,
    12,
    38,
    41,
    13,
    37,
    48,
    7,
    16,
    24,
    55,
    40,
    61,
    26,
    17,
    0,
    1,
    60,
    51,
    30,
    4,
    22,
    25,
    54,
    21,
    56,
    59,
    6,
    63,
    57,
    62,
    11,
    36,
    20,
    34,
    44,
    52,
)


def debug(
    *args: Any, file: Optional[str] = None, append: bool = True, **kwargs: Any
) -> None:
    """
    Print debug information with optional file output.

    ```python
    debug("fetch streams", url=PLAYER_API_URL, timeout=10)
    ```
    """
    if not DEBUG_MODE:
        return

    message = " ".join(str(arg) for arg in args)
    if kwargs:
        extra = " ".join(f"{key}={value!r}" for key, value in kwargs.items())
        message = f"{message} {extra}".strip()

    if file:
        mode = "a" if append else "w"
        with open(file, mode, encoding="utf-8") as handle:
            handle.write(f"{message}\n")
        return

    print(message)


class CLIStyle:
    """
    Terminal color helper for consistent messaging.

    ```python
    CLIStyle.color("Download complete", CLIStyle.COLORS["CONTENT"])
    ```
    """

    COLORS: Dict[str, int] = {
        "TITLE": 7,
        "SUB_TITLE": 2,
        "CONTENT": 3,
        "EXAMPLE": 7,
        "WARNING": 4,
        "ERROR": 2,
    }

    COLOR_TABLE: Dict[int, str] = {
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

    @staticmethod
    def color(text: str = "", color: int = COLOR_TABLE[0]) -> str:
        """
        Apply ANSI color styling.

        ```python
        CLIStyle.color("Warning", CLIStyle.COLORS["WARNING"])
        ```
        """
        template = CLIStyle.COLOR_TABLE.get(color, CLIStyle.COLOR_TABLE[0])
        return template.format(text)


class ColoredArgumentParser(argparse.ArgumentParser):
    """
    Argument parser that highlights option strings.

    ```python
    parser = ColoredArgumentParser(description="Example")
    ```
    """

    def _format_action_invocation(self, action: argparse.Action) -> str:
        if not action.option_strings:
            (metavar,) = self._metavar_formatter(action, action.dest)(1)
            return metavar

        parts: List[str] = []
        if action.nargs == 0:
            parts.extend(
                CLIStyle.color(opt, CLIStyle.COLORS["SUB_TITLE"])
                for opt in action.option_strings
            )
        else:
            default = action.dest.upper()
            args_string = self._format_args(action, default)
            for opt in action.option_strings:
                parts.append(
                    CLIStyle.color(f"{opt} {args_string}", CLIStyle.COLORS["SUB_TITLE"])
                )

        return ", ".join(parts)


def create_example_text(script_name: str) -> str:
    """
    Build CLI examples text for the epilog section.

    ```python
    create_example_text("06-bilibili-downloader.py")
    ```
    """
    examples = [
        (
            "Save SESSDATA for later downloads",
            f"{script_name} init 'SESSDATA=YOUR_SESSDATA; bili_jct=...'",
        ),
        (
            "Download by BV id",
            f"{script_name} BV1xx",
        ),
        (
            "Download by URL",
            f"{script_name} https://www.bilibili.com/video/BV1xx",
        ),
        (
            "Download with custom path and quality",
            f"{script_name} BV1xx --quality 80 --output /tmp",
        ),
    ]
    notes = [
        f"Saved credentials are stored in {CONFIG_FILE_NAME} under the current directory by default.",
        f"Use --config or {CONFIG_FILE_ENV_KEY} to choose another credential file.",
        f"SESSDATA can also be provided through --sessdata or {ENV_SESSDATA_KEY}.",
        "Quality levels: 16 (360p), 32 (480p), 64 (720p), 80 (1080p).",
    ]

    text = f"\n{CLIStyle.color('Examples:', CLIStyle.COLORS['TITLE'])}"
    for description, command in examples:
        text += (
            f"\n  {CLIStyle.color(f'# {description}', CLIStyle.COLORS['EXAMPLE'])}"
            f"\n  {CLIStyle.color(command, CLIStyle.COLORS['CONTENT'])}\n"
        )

    text += f"\n{CLIStyle.color('Notes:', CLIStyle.COLORS['TITLE'])}"
    for note in notes:
        text += f"\n  {CLIStyle.color(f'- {note}', CLIStyle.COLORS['CONTENT'])}"

    return text


@dataclass
class VideoDetails:
    """
    Structured metadata for a Bilibili video.

    ```python
    VideoDetails(bvid="BV1xx", aid=1, cid=2, title="demo", description="", owner="user",
                 upload_time=datetime.utcnow(), stats={"view": 0})
    ```
    """

    bvid: str
    aid: int
    cid: int
    title: str
    description: str
    owner: str
    upload_time: datetime
    stats: Dict[str, int]

    def build_metadata(self, storage_path: Path) -> Dict[str, Any]:
        """
        Convert the details into a serialisable dictionary.

        ```python
        VideoDetails(...).build_metadata(Path("video.mp4"))
        ```
        """
        return {
            "id": self.bvid,
            "aid": self.aid,
            "cid": self.cid,
            "title": self.title,
            "raw_url": f"https://www.bilibili.com/video/{self.bvid}",
            "desc": self.description,
            "owner": self.owner,
            "time": {
                "work_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "upload_date": self.upload_time.strftime("%Y-%m-%d %H:%M:%S"),
            },
            "storage": str(storage_path),
            "stat": self.stats,
        }


class BilibiliClient:
    """
    Thin client around the Bilibili HTTP APIs.

    ```python
    client = BilibiliClient(sessdata="...")
    details = client.fetch_video_details("BV1xx")
    ```
    """

    def __init__(self, sessdata: str, timeout: int = DEFAULT_REQUEST_TIMEOUT) -> None:
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)
        if sessdata:
            self.session.cookies.set("SESSDATA", sessdata)
        self._wbi_keys: Optional[Tuple[str, str]] = None

    def fetch_video_details(self, bvid: str) -> VideoDetails:
        """
        Retrieve metadata for a video.

        ```python
        details = client.fetch_video_details("BV1xx")
        ```
        """
        response = self.session.get(
            VIDEO_DETAIL_API_URL,
            params={"bvid": bvid},
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        data = payload["data"]
        debug("video details fetched", bvid=bvid)
        return VideoDetails(
            bvid=bvid,
            aid=data["aid"],
            cid=data["cid"],
            title=data["title"],
            description=data["desc"],
            owner=data["owner"]["name"],
            upload_time=datetime.fromtimestamp(int(data["pubdate"])),
            stats={
                "view": data["stat"]["view"],
                "like": data["stat"]["like"],
                "reply": data["stat"]["reply"],
                "danmaku": data["stat"].get("danmaku", 0),
            },
        )

    def fetch_streams(self, bvid: str, cid: int, quality: int) -> List[Dict[str, Any]]:
        """
        Lazily fetch available stream segments for a video.

        ```python
        streams = client.fetch_streams("BV1xx", 123, 64)
        ```
        """
        signed_params = self._sign_params({"bvid": bvid, "cid": cid, "qn": quality})
        response = self.session.get(
            PLAYER_API_URL,
            params=signed_params,
            timeout=self.timeout,
        )
        response.raise_for_status()
        payload = response.json()
        debug("streams fetched", segment_count=len(payload["data"]["durl"]))
        return payload["data"]["durl"]

    def download_streams(
        self,
        streams: Iterable[Dict[str, Any]],
        target_path: Path,
        referer: str,
    ) -> None:
        """
        Download stream segments sequentially into a single file.

        ```python
        client.download_streams(streams, Path("video.mp4"), referer_url)
        ```
        """
        target_path.parent.mkdir(parents=True, exist_ok=True)
        headers = {
            **self.session.headers,
            "Referer": referer,
            "Range": "bytes=0-",
        }

        stream_entries = list(streams)

        with open(target_path, "wb") as destination:
            sizes = [
                int(stream.get("size", 0))
                for stream in stream_entries
                if stream.get("size")
            ]
            total_size = sum(sizes) if sizes else None
            downloaded = 0
            start_time = time.monotonic()
            for index, stream in enumerate(stream_entries, start=1):
                url = stream["url"]
                debug("downloading segment", index=index, url=url)
                with self.session.get(
                    url,
                    headers=headers,
                    stream=True,
                    timeout=self.timeout,
                ) as response:
                    response.raise_for_status()
                    for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
                        if chunk:
                            destination.write(chunk)
                            downloaded += len(chunk)
                            progress_line = build_progress_line(
                                downloaded, total_size, start_time
                            )
                            print(
                                "\r"
                                + CLIStyle.color(
                                    progress_line, CLIStyle.COLORS["CONTENT"]
                                ),
                                end="",
                                flush=True,
                            )
            if downloaded:
                print()

    def _sign_params(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sign request parameters with the WBI algorithm.

        ```python
        signed = client._sign_params({"bvid": "BV1xx"})
        ```
        """
        img_key, sub_key = self._retrieve_wbi_keys()
        mixin_key = self._build_mixin_key(img_key + sub_key)
        params["wts"] = int(datetime.now().timestamp())
        filtered = {
            key: "".join(ch for ch in str(value) if ch not in "!'()*")
            for key, value in params.items()
        }
        ordered = dict(sorted(filtered.items()))
        query = urlencode(ordered)
        ordered["w_rid"] = md5(f"{query}{mixin_key}".encode()).hexdigest()
        return ordered

    def _retrieve_wbi_keys(self) -> Tuple[str, str]:
        """
        Fetch and cache the latest WBI keys.

        ```python
        img_key, sub_key = client._retrieve_wbi_keys()
        ```
        """
        if self._wbi_keys:
            return self._wbi_keys

        response = self.session.get(NAV_API_URL, timeout=self.timeout)
        response.raise_for_status()
        content = response.json()
        img_url: str = content["data"]["wbi_img"]["img_url"]
        sub_url: str = content["data"]["wbi_img"]["sub_url"]
        img_key = img_url.rsplit("/", 1)[1].split(".")[0]
        sub_key = sub_url.rsplit("/", 1)[1].split(".")[0]
        self._wbi_keys = (img_key, sub_key)
        debug("wbi keys updated", img_key=img_key, sub_key=sub_key)
        return self._wbi_keys

    @staticmethod
    def _build_mixin_key(origin: str) -> str:
        """
        Shuffle characters according to MIXIN_KEY_TABLE.

        ```python
        key = BilibiliClient._build_mixin_key("abcdef")
        ```
        """
        mixin = reduce(lambda acc, idx: acc + origin[idx], MIXIN_KEY_TABLE, "")
        return mixin[:32]


def resolve_storage_path(output: Optional[str], bvid: str) -> Tuple[Path, bool]:
    """
    Resolve destination path and whether filename is explicitly provided.

    ```python
    resolve_storage_path("/tmp", "BV1xx")
    ```
    """
    if not output:
        return Path.cwd() / f"{bvid}.mp4", False

    candidate = Path(output).expanduser()
    if candidate.is_dir():
        return candidate / f"{bvid}.mp4", False

    if not candidate.suffix:
        return candidate / f"{bvid}.mp4", False

    return candidate, True


INVALID_FILENAME_CHARS = re.compile(r'[\\/:*?"<>|\r\n]')
MAX_FILENAME_LENGTH = 180


def sanitize_filename(name: str, fallback: str) -> str:
    """
    Convert title text into a filesystem friendly filename.

    ```python
    sanitize_filename("Demo: Title?", "BV1xx")
    ```
    """
    sanitized = INVALID_FILENAME_CHARS.sub("_", name)
    sanitized = re.sub(r"\s+", " ", sanitized).strip(" .")
    if not sanitized:
        sanitized = fallback
    if len(sanitized) > MAX_FILENAME_LENGTH:
        sanitized = sanitized[:MAX_FILENAME_LENGTH].rstrip(" .")
    if not sanitized:
        sanitized = fallback
    return sanitized


def handle_existing_file(path: Path) -> Optional[Path]:
    """
    Resolve filename conflicts by prompting the user.

    ```python
    handle_existing_file(Path("video.mp4"))
    ```
    """
    current_path = path
    suffix = path.suffix or ".mp4"
    while True:
        prompt = CLIStyle.color(
            f"File already exists: {current_path}\n"
            "Choose action [Y] overwrite / [r] rename / [n] cancel: ",
            CLIStyle.COLORS["WARNING"],
        )
        choice = input(prompt).strip().lower()
        if choice == "y":
            return current_path
        if choice == "n":
            return None
        if choice == "r":
            name_prompt = CLIStyle.color(
                "Enter new filename (without path): ",
                CLIStyle.COLORS["CONTENT"],
            )
            requested_name = input(name_prompt).strip()
            if not requested_name:
                print(
                    CLIStyle.color(
                        "Filename cannot be empty.",
                        CLIStyle.COLORS["ERROR"],
                    )
                )
                continue
            sanitized = sanitize_filename(requested_name, current_path.stem)
            candidate = current_path.parent / sanitized
            if not candidate.suffix:
                candidate = candidate.with_suffix(suffix)
            if candidate.exists():
                print(
                    CLIStyle.color(
                        "File already exists with that name.",
                        CLIStyle.COLORS["WARNING"],
                    )
                )
                current_path = candidate
                continue
            return candidate

        print(
            CLIStyle.color(
                "Please select Y, r, or n.",
                CLIStyle.COLORS["ERROR"],
            )
        )

    return None


def default_config_path() -> Path:
    """
    Resolve the credential file path.

    ```python
    path = default_config_path()
    ```
    """
    configured_path = os.getenv(CONFIG_FILE_ENV_KEY)
    if configured_path:
        return Path(configured_path).expanduser()
    return Path.cwd() / CONFIG_FILE_NAME


def parse_env_file(path: Path) -> Dict[str, str]:
    """
    Read simple KEY=VALUE lines from an env-style file.

    ```python
    values = parse_env_file(Path(".bilibili-downloader.env"))
    ```
    """
    if not path.exists():
        return {}

    values: Dict[str, str] = {}
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            stripped = line.strip()
            if not stripped or stripped.startswith("#") or "=" not in stripped:
                continue
            key, value = stripped.split("=", 1)
            key = key.strip()
            value = value.strip()
            if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
                if value[0] == '"':
                    try:
                        value = json.loads(value)
                    except json.JSONDecodeError:
                        value = value[1:-1]
                else:
                    value = value[1:-1]
            if key:
                values[key] = value
    return values


def escape_env_value(value: str) -> str:
    """
    Quote a value for storage in an env-style file.

    ```python
    escape_env_value("abc")
    ```
    """
    escaped = value.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'


def write_env_file(path: Path, values: Dict[str, str]) -> None:
    """
    Persist credentials into an env-style file with restricted permissions.

    ```python
    write_env_file(Path(".bilibili-downloader.env"), {"BILIBILI_SESSDATA": "XX"})
    ```
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Created by 06-bilibili-downloader.py",
        "# Keep this file private. It contains Bilibili authentication cookies.",
    ]
    for key in sorted(values):
        lines.append(f"{key}={escape_env_value(values[key])}")

    file_descriptor = os.open(
        path,
        os.O_WRONLY | os.O_CREAT | os.O_TRUNC,
        0o600,
    )
    with os.fdopen(file_descriptor, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")
    os.chmod(path, 0o600)


def resolve_config_path(cli_value: Optional[str]) -> Path:
    """
    Determine the credential file path from CLI, environment, or default.

    ```python
    resolve_config_path(None)
    ```
    """
    if cli_value:
        return Path(cli_value).expanduser()
    return default_config_path()


def extract_sessdata_from_cookie(raw_cookie: str) -> str:
    """
    Accept a full cookie header or a raw SESSDATA value.

    ```python
    extract_sessdata_from_cookie("SESSDATA=abc; bili_jct=def")
    ```
    """
    stripped_cookie = raw_cookie.strip()
    if not stripped_cookie:
        raise ValueError("Cookie value cannot be empty.")

    for item in stripped_cookie.split(";"):
        if "=" not in item:
            continue
        key, value = item.split("=", 1)
        if key.strip().upper() == "SESSDATA":
            sessdata = value.strip()
            if sessdata:
                return sessdata
            break

    if "SESSDATA=" in stripped_cookie.upper():
        raise ValueError("SESSDATA cookie is present but empty.")

    return stripped_cookie


def save_sessdata(cookie_value: str, config_path: Path) -> None:
    """
    Save SESSDATA to the configured env file.

    ```python
    save_sessdata("SESSDATA=abc", Path(".bilibili-downloader.env"))
    ```
    """
    sessdata = extract_sessdata_from_cookie(cookie_value)
    values = parse_env_file(config_path)
    values[ENV_SESSDATA_KEY] = sessdata
    write_env_file(config_path, values)


def resolve_sessdata(
    cli_value: Optional[str],
    config_path: Optional[Path] = None,
) -> str:
    """
    Determine the SESSDATA token from CLI, environment, or config file.

    ```python
    resolve_sessdata("XX", Path(".bilibili-downloader.env"))
    ```
    """
    if cli_value:
        return extract_sessdata_from_cookie(cli_value)

    env_value = os.getenv(ENV_SESSDATA_KEY)
    if env_value:
        return extract_sessdata_from_cookie(env_value)

    credential_path = config_path or default_config_path()
    config_value = parse_env_file(credential_path).get(ENV_SESSDATA_KEY)
    if config_value:
        return extract_sessdata_from_cookie(config_value)

    raise ValueError(
        "SESSDATA is required. Run `python 06-bilibili-downloader.py init "
        "'SESSDATA=...'` first, pass --sessdata, or export BILIBILI_SESSDATA."
    )


def resolve_bvid(
    cli_value: Optional[str],
    url_value: Optional[str],
    target_value: Optional[str] = None,
) -> str:
    """
    Determine the BV identifier from CLI input or URL.

    ```python
    resolve_bvid("BV1xx", None)
    resolve_bvid(None, "https://www.bilibili.com/video/BV1xx/")
    ```
    """
    provided_values = [value for value in (cli_value, url_value, target_value) if value]
    if len(provided_values) > 1:
        raise ValueError("Provide only one video target.")

    if cli_value:
        return cli_value

    if url_value:
        extracted = extract_bvid(url_value)
        if extracted:
            return extracted
        raise ValueError("Failed to parse BV id from provided --url.")

    if target_value:
        extracted = extract_bvid(target_value)
        if extracted:
            return extracted
        raise ValueError("Target must be a BV id or a Bilibili video URL.")

    raise ValueError("A BV id or Bilibili video URL must be supplied.")


def extract_bvid(url: str) -> Optional[str]:
    """
    Extract BV identifier from a Bilibili URL.

    ```python
    extract_bvid("https://www.bilibili.com/video/BV1xx?foo=bar")
    ```
    """
    match = BV_ID_REGEX.search(url)
    if match:
        return match.group(0)
    return None


def display_video_summary(details: VideoDetails, destination: Path) -> None:
    """
    Print a concise summary of the target video and download path.

    ```python
    display_video_summary(details, Path("video.mp4"))
    ```
    """
    stats = details.stats
    summary_lines = [
        f"Title: {details.title}",
        f"Owner: {details.owner}",
        f"Output: {destination}",
        f"Views: {stats.get('view', 0)}",
        f"Likes: {stats.get('like', 0)}",
        f"Comments: {stats.get('reply', 0)}",
        f"Danmaku: {stats.get('danmaku', 0)}",
    ]

    print(CLIStyle.color("Target Video", CLIStyle.COLORS["TITLE"]))
    for line in summary_lines:
        print(CLIStyle.color(f"  {line}", CLIStyle.COLORS["CONTENT"]))


def format_size(value: float) -> str:
    """
    Format byte counts into human readable text.

    ```python
    format_size(1048576)
    ```
    """
    units = ["B", "KB", "MB", "GB", "TB"]
    size = float(value)
    for unit in units:
        if size < 1024 or unit == units[-1]:
            return f"{size:.1f} {unit}"
        size /= 1024
    return f"{value} B"


def format_duration(seconds: float) -> str:
    """
    Format duration into mm:ss representation.

    ```python
    format_duration(75)
    ```
    """
    minutes = int(seconds // 60)
    remaining = int(seconds % 60)
    return f"{minutes:02d}:{remaining:02d}"


def build_progress_line(
    downloaded: int, total: Optional[int], start_time: float
) -> str:
    """
    Construct a progress line containing size, speed, and ETA.

    ```python
    build_progress_line(1024, 2048, time.monotonic())
    ```
    """
    elapsed = max(time.monotonic() - start_time, 1e-6)
    speed = downloaded / elapsed
    parts = [
        f"{format_size(downloaded)}",
    ]
    if total:
        percent = min(downloaded / total, 1.0) * 100
        parts.append(f"/ {format_size(total)} ({percent:05.1f}%)")
        remaining_bytes = max(total - downloaded, 0)
        if speed > 0:
            eta = remaining_bytes / speed
            parts.append(f"| ETA {format_duration(eta)}")
    parts.append(f"| {format_size(speed)}/s")
    return " ".join(parts)


def normalize_argv(argv: List[str]) -> List[str]:
    """
    Insert the default download command for shorthand invocations.

    ```python
    normalize_argv(["BV1xx"])
    ```
    """
    if not argv:
        return ["download"]
    if argv[0] in {"download", "init", "-h", "--help"}:
        return argv
    return ["download", *argv]


def add_download_arguments(parser: argparse.ArgumentParser) -> None:
    """
    Attach download options to a parser.

    ```python
    add_download_arguments(parser)
    ```
    """
    parser.add_argument(
        "target",
        nargs="?",
        help=CLIStyle.color(
            "Bilibili video URL or BV id; detected automatically",
            CLIStyle.COLORS["CONTENT"],
        ),
    )
    parser.add_argument(
        "--bvid",
        help=CLIStyle.color(
            "Bilibili video ID (BV...). Kept for compatibility.",
            CLIStyle.COLORS["CONTENT"],
        ),
    )
    parser.add_argument(
        "--url",
        help=CLIStyle.color(
            "Video URL. Kept for compatibility.",
            CLIStyle.COLORS["CONTENT"],
        ),
    )
    parser.add_argument(
        "--sessdata",
        help=CLIStyle.color(
            "SESSDATA value or full Cookie header; overrides saved credentials",
            CLIStyle.COLORS["CONTENT"],
        ),
    )
    parser.add_argument(
        "--config",
        help=CLIStyle.color(
            f"Credential env file path; default: ./{CONFIG_FILE_NAME}",
            CLIStyle.COLORS["CONTENT"],
        ),
    )
    parser.add_argument(
        "--output",
        help=CLIStyle.color(
            "Directory or filename for the downloaded video",
            CLIStyle.COLORS["CONTENT"],
        ),
    )
    parser.add_argument(
        "--quality",
        type=int,
        default=DEFAULT_VIDEO_QUALITY,
        choices=[16, 32, 64, 80],
        help=CLIStyle.color("Preferred quality level", CLIStyle.COLORS["CONTENT"]),
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_REQUEST_TIMEOUT,
        help=CLIStyle.color("Request timeout in seconds", CLIStyle.COLORS["CONTENT"]),
    )
    parser.add_argument(
        "--metadata",
        action="store_true",
        help=CLIStyle.color(
            "Write video metadata JSON next to the mp4 file",
            CLIStyle.COLORS["CONTENT"],
        ),
    )
    parser.add_argument(
        "--log",
        action="store_true",
        help=CLIStyle.color("Enable debug output", CLIStyle.COLORS["CONTENT"]),
    )


def parse_arguments(argv: Optional[List[str]] = None) -> argparse.Namespace:
    """
    Parse command line arguments.

    ```python
    args = parse_arguments(["BV1xx"])
    ```
    """
    script_name = Path(sys.argv[0]).name
    parser = ColoredArgumentParser(
        description=CLIStyle.color(
            "Download Bilibili videos using the authenticated WBI API.",
            CLIStyle.COLORS["TITLE"],
        ),
        epilog=create_example_text(script_name),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(
        dest="command",
        parser_class=ColoredArgumentParser,
    )
    init_parser = subparsers.add_parser(
        "init",
        help=CLIStyle.color(
            "Save Bilibili Cookie/SESSDATA", CLIStyle.COLORS["CONTENT"]
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=create_example_text(script_name),
    )
    init_parser.add_argument(
        "cookie",
        help=CLIStyle.color(
            "Full Cookie header or raw SESSDATA value",
            CLIStyle.COLORS["CONTENT"],
        ),
    )
    init_parser.add_argument(
        "--config",
        help=CLIStyle.color(
            f"Credential env file path; default: ./{CONFIG_FILE_NAME}",
            CLIStyle.COLORS["CONTENT"],
        ),
    )
    init_parser.add_argument(
        "--log",
        action="store_true",
        help=CLIStyle.color("Enable debug output", CLIStyle.COLORS["CONTENT"]),
    )

    download_parser = subparsers.add_parser(
        "download",
        help=CLIStyle.color(
            "Download a video by URL or BV id", CLIStyle.COLORS["CONTENT"]
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=create_example_text(script_name),
    )
    add_download_arguments(download_parser)

    argument_values = sys.argv[1:] if argv is None else argv
    return parser.parse_args(normalize_argv(argument_values))


def write_metadata(metadata: Dict[str, Any], target_path: Path) -> None:
    """
    Persist metadata to a JSON file adjacent to the video.

    ```python
    write_metadata({"id": "BV1xx"}, Path("video.mp4"))
    ```
    """
    metadata_path = target_path.with_suffix(".json")
    with open(metadata_path, "w", encoding="utf-8") as handle:
        json.dump(metadata, handle, ensure_ascii=False, indent=2)
    debug("metadata written", path=str(metadata_path))


def main() -> int:
    """
    Main entry point for the downloader.

    ```python
    if __name__ == "__main__":
        sys.exit(main())
    ```
    """
    args = parse_arguments()

    global DEBUG_MODE
    DEBUG_MODE = args.log

    config_path = resolve_config_path(getattr(args, "config", None))
    if args.command == "init":
        save_sessdata(args.cookie, config_path)
        print(
            CLIStyle.color(
                f"Credentials saved to {config_path}",
                CLIStyle.COLORS["CONTENT"],
            )
        )
        return 0

    bvid = resolve_bvid(args.bvid, args.url, args.target)
    sessdata = resolve_sessdata(args.sessdata, config_path)
    initial_path, explicit_filename = resolve_storage_path(args.output, bvid)

    client = BilibiliClient(sessdata=sessdata, timeout=args.timeout)
    print(
        CLIStyle.color(
            "Fetching video metadata...",
            CLIStyle.COLORS["CONTENT"],
        )
    )
    details = client.fetch_video_details(bvid)
    output_path = initial_path
    if not explicit_filename:
        safe_title = sanitize_filename(details.title, bvid)
        output_path = output_path.with_name(f"{safe_title}{output_path.suffix}")

    if output_path.exists():
        resolved_path = handle_existing_file(output_path)
        if resolved_path is None:
            print(
                CLIStyle.color(
                    "Download cancelled.",
                    CLIStyle.COLORS["WARNING"],
                )
            )
            return 0
        output_path = resolved_path

    display_video_summary(details, output_path)

    print(
        CLIStyle.color(
            "Retrieving stream information...",
            CLIStyle.COLORS["CONTENT"],
        )
    )
    streams = client.fetch_streams(details.bvid, details.cid, args.quality)
    print(
        CLIStyle.color(
            f"Segment count: {len(streams)}",
            CLIStyle.COLORS["CONTENT"],
        )
    )

    referer = f"{VIDEO_DETAIL_API_URL}?bvid={details.bvid}"
    print(
        CLIStyle.color(
            "Downloading video...",
            CLIStyle.COLORS["CONTENT"],
        )
    )
    client.download_streams(streams, output_path, referer)

    print(
        CLIStyle.color(
            f"Video saved to {output_path}",
            CLIStyle.COLORS["CONTENT"],
        )
    )

    if args.metadata:
        metadata = details.build_metadata(output_path)
        write_metadata(metadata, output_path)
        print(
            CLIStyle.color(
                f"Metadata written to {output_path.with_suffix('.json')}",
                CLIStyle.COLORS["CONTENT"],
            )
        )

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print(
            CLIStyle.color(
                "\nOperation cancelled by user",
                CLIStyle.COLORS["WARNING"],
            )
        )
        sys.exit(0)
    except Exception as exc:  # pylint: disable=broad-except
        if DEBUG_MODE:
            import traceback

            traceback.print_exc()
        print(CLIStyle.color(f"\nError: {exc}", CLIStyle.COLORS["ERROR"]))
        sys.exit(1)
