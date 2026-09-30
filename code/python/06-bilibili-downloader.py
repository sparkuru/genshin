# -*- coding: utf-8 -*-
# pip install requests argparse

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import traceback
from dataclasses import dataclass
from datetime import datetime
from functools import reduce
from hashlib import md5
import re
from pathlib import Path
import time
from typing import Any, BinaryIO, Dict, Iterable, List, Optional, Tuple
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
ENV_COOKIE_KEY = "BILIBILI_COOKIE"
CONFIG_FILE_NAME = ".bilibili-downloader.env"
CONFIG_FILE_ENV_KEY = "BILIBILI_DOWNLOADER_ENV"
DEFAULT_VIDEO_QUALITY = 64
DEFAULT_REQUEST_TIMEOUT = 25
DEFAULT_RETRIES = 4
DEFAULT_RETRY_DELAY = 2.0
RANGE_SIZE = 1024 * 1024
CHUNK_SIZE = 256 * 1024
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
        "Interrupted downloads keep .part files and resume automatically on rerun.",
        "Use --resume for an old incomplete mp4; select the same video and quality.",
        "init preserves the full browser Cookie when supplied, including device cookies.",
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


class BilibiliRiskControlError(RuntimeError):
    """A request was rejected by Bilibili's risk-control system."""


class BilibiliClient:
    """
    Thin client around the Bilibili HTTP APIs.

    ```python
    client = BilibiliClient(sessdata="...")
    details = client.fetch_video_details("BV1xx")
    ```
    """

    def __init__(
        self,
        sessdata: str,
        timeout: int = DEFAULT_REQUEST_TIMEOUT,
        retries: int = DEFAULT_RETRIES,
        retry_delay: float = DEFAULT_RETRY_DELAY,
        cookie: str = "",
    ) -> None:
        if timeout <= 0 or retries < 0 or retry_delay < 0:
            raise ValueError(
                "Timeout must be positive; retries and retry delay cannot be negative."
            )
        self.timeout = timeout
        self.retries = retries
        self.retry_delay = retry_delay
        self.session = requests.Session()
        self.session.headers.update(DEFAULT_HEADERS)
        for name, value in parse_cookie_header(cookie).items():
            self.session.cookies.set(name, value, domain=".bilibili.com", path="/")
        if sessdata:
            self.session.cookies.set(
                "SESSDATA", sessdata, domain=".bilibili.com", path="/"
            )
        self._wbi_keys: Optional[Tuple[str, str]] = None

    def _wait_before_retry(
        self, attempt: int, reason: str, response: Optional[requests.Response] = None
    ) -> None:
        """Back off between retries, respecting a bounded Retry-After delay."""
        delay = min(self.retry_delay * 2 ** (attempt - 1), 30.0)
        if response is not None and response.status_code in {412, 429}:
            delay = max(delay, 5.0)
        if response is not None:
            retry_after = response.headers.get("Retry-After", "")
            if retry_after.isdigit():
                delay = max(delay, min(float(retry_after), 60.0))
        print(
            CLIStyle.color(
                f"\n{reason}; retry {attempt}/{self.retries} in {delay:g}s...",
                CLIStyle.COLORS["WARNING"],
            )
        )
        time.sleep(delay)

    def _refresh_site_cookies(self) -> None:
        """Let the website supply session cookies after a risk-control response."""
        try:
            with self.session.get(
                "https://www.bilibili.com/",
                headers={"Accept": "text/html"},
                timeout=min(self.timeout, 10),
                stream=True,
            ) as response:
                response.raise_for_status()
        except requests.RequestException:
            debug("Website cookie refresh was unavailable")

    def _request_json(
        self,
        url: str,
        params: Optional[Dict[str, Any]] = None,
        allow_logged_out: bool = False,
        retry_risk_control: bool = True,
    ) -> Dict[str, Any]:
        """Retry transient API failures and report API error codes explicitly."""
        for attempt in range(self.retries + 1):
            response = None
            try:
                response = self.session.get(url, params=params, timeout=self.timeout)
                response.raise_for_status()
                payload = response.json()
                code = payload.get("code", 0)
                if code in {-352, -412, -509}:
                    raise requests.HTTPError(
                        "Bilibili API request was rate limited", response=response
                    )
                if code != 0 and not (allow_logged_out and code == -101):
                    raise RuntimeError(
                        f"Bilibili API error {code}: {payload.get('message', 'unknown error')}"
                    )
                if not isinstance(payload.get("data"), dict):
                    raise RuntimeError("Bilibili API returned no usable data.")
                return payload
            except (
                requests.ConnectionError,
                requests.Timeout,
                requests.exceptions.ChunkedEncodingError,
                requests.HTTPError,
            ) as exc:
                status = response.status_code if response is not None else None
                retryable = status is None or status in {
                    200,
                    408,
                    412,
                    429,
                    500,
                    502,
                    503,
                    504,
                }
                if not retryable:
                    raise
                risk_control = status == 412 or (
                    status == 200 and isinstance(exc, requests.HTTPError)
                )
                if attempt == self.retries or (risk_control and not retry_risk_control):
                    if risk_control:
                        raise BilibiliRiskControlError(
                            "Bilibili rejected the request after retries (risk control). "
                            "Wait before trying again and refresh the full browser Cookie with init. "
                            "An IP restriction cannot be fixed by download retries."
                        ) from exc
                    raise
                if attempt == 0 and status in {200, 412}:
                    self._refresh_site_cookies()
                self._wait_before_retry(
                    attempt + 1,
                    f"API request failed ({status or type(exc).__name__})",
                    response,
                )
            finally:
                if response is not None:
                    response.close()
        raise RuntimeError("API retry budget exhausted.")

    def fetch_video_details(self, bvid: str) -> VideoDetails:
        """
        Retrieve metadata for a video.

        ```python
        details = client.fetch_video_details("BV1xx")
        ```
        """
        self.session.headers["Referer"] = f"https://www.bilibili.com/video/{bvid}/"
        try:
            payload = self._request_json(
                VIDEO_DETAIL_API_URL, {"bvid": bvid}, retry_risk_control=False
            )
            data = payload["data"]
        except BilibiliRiskControlError:
            print(
                CLIStyle.color(
                    "Metadata API was rejected; reading metadata from the video page...",
                    CLIStyle.COLORS["WARNING"],
                )
            )
            data = self._fetch_video_page_data(bvid)
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

    def _fetch_video_page_data(self, bvid: str) -> Dict[str, Any]:
        """Read public page metadata when the view API is unavailable."""
        with self.session.get(
            f"https://www.bilibili.com/video/{bvid}/", timeout=self.timeout
        ) as response:
            response.raise_for_status()
            match = re.search(r"window\.__INITIAL_STATE__\s*=\s*", response.text)
            if not match:
                raise BilibiliRiskControlError(
                    "Metadata API was rejected and the video page has no embedded metadata. "
                    "Wait before trying again or refresh the full browser Cookie with init."
                )
            state, _ = json.JSONDecoder().raw_decode(
                response.text[match.end() :].lstrip()
            )
        data = state.get("videoData")
        if not isinstance(data, dict) or data.get("bvid") != bvid:
            raise RuntimeError(
                "Video page metadata does not match the requested BV id."
            )
        return data

    def fetch_streams(self, bvid: str, cid: int, quality: int) -> List[Dict[str, Any]]:
        """
        Lazily fetch available stream segments for a video.

        ```python
        streams = client.fetch_streams("BV1xx", 123, 64)
        ```
        """
        signed_params = self._sign_params({"bvid": bvid, "cid": cid, "qn": quality})
        payload = self._request_json(PLAYER_API_URL, signed_params)
        streams = payload["data"].get("durl")
        if not streams:
            raise RuntimeError(
                "Bilibili returned no downloadable segments for this quality."
            )
        debug("streams fetched", segment_count=len(streams))
        return streams

    def download_streams(
        self,
        streams: Iterable[Dict[str, Any]],
        target_path: Path,
        referer: str,
        resume: bool = False,
        identity: str = "",
    ) -> None:
        """Keep validated partial data and publish the file only after completion."""
        entries = list(streams)
        sizes = [int(entry.get("size", 0)) for entry in entries]
        if not entries or any(size <= 0 for size in sizes):
            raise RuntimeError(
                "Stream metadata must include a positive size for every segment."
            )
        total_size = sum(sizes)
        target_path.parent.mkdir(parents=True, exist_ok=True)
        partial_path = target_path.with_name(target_path.name + ".part")
        state_path = partial_path.with_name(partial_path.name + ".json")
        state = {"identity": identity, "sizes": sizes}
        if partial_path.exists():
            if not state_path.exists() or json.loads(state_path.read_text()) != state:
                raise RuntimeError(
                    f"Partial download does not match this video/quality: {partial_path}"
                )
        else:
            if resume and target_path.exists():
                if target_path.stat().st_size > total_size:
                    raise RuntimeError(
                        "Existing file is larger than the selected stream; cannot resume."
                    )
                shutil.copyfile(target_path, partial_path)
            else:
                partial_path.touch()
            state_path.write_text(json.dumps(state), encoding="utf-8")
        initial_size = partial_path.stat().st_size
        if initial_size > total_size:
            raise RuntimeError(
                "Partial file is larger than the selected stream; cannot resume."
            )
        if initial_size:
            print(
                CLIStyle.color(
                    f"Resuming from {format_size(initial_size)}",
                    CLIStyle.COLORS["CONTENT"],
                )
            )
        start_time = time.monotonic()
        segment_start = 0
        with partial_path.open("r+b") as destination:
            destination.seek(0, os.SEEK_END)
            for entry, size in zip(entries, sizes):
                if destination.tell() < segment_start + size:
                    self._download_segment(
                        destination,
                        entry,
                        segment_start,
                        size,
                        referer,
                        total_size,
                        start_time,
                        initial_size,
                    )
                segment_start += size
            if destination.tell() != total_size:
                raise RuntimeError(
                    "Downloaded size does not match the selected stream."
                )
        os.replace(partial_path, target_path)
        state_path.unlink()
        print(CLIStyle.color(""))

    def _download_segment(
        self,
        destination: BinaryIO,
        entry: Dict[str, Any],
        segment_start: int,
        size: int,
        referer: str,
        total_size: int,
        start_time: float,
        initial_size: int,
    ) -> None:
        """Fetch bounded byte ranges, retrying from the last byte written."""
        urls = list(dict.fromkeys([entry["url"], *(entry.get("backup_url") or [])]))
        failures = 0
        while destination.tell() < segment_start + size:
            offset = destination.tell() - segment_start
            end = min(offset + RANGE_SIZE, size) - 1
            response = None
            try:
                response = self.session.get(
                    urls[failures % len(urls)],
                    headers={
                        "Referer": referer,
                        "Range": f"bytes={offset}-{end}",
                        "Accept-Encoding": "identity",
                    },
                    stream=True,
                    timeout=self.timeout,
                )
                response.raise_for_status()
                expected = self._validate_range(response, offset, end, size)
                if response.status_code == 200:
                    # A server ignoring Range must never append a full response to a suffix.
                    destination.seek(segment_start)
                    destination.truncate()
                self._write_response(
                    response,
                    destination,
                    expected,
                    total_size,
                    start_time,
                    initial_size,
                )
            except (
                requests.ConnectionError,
                requests.Timeout,
                requests.exceptions.ChunkedEncodingError,
                requests.HTTPError,
            ) as exc:
                status = response.status_code if response is not None else None
                retryable = status is None or status in {
                    200,
                    206,
                    403,
                    408,
                    412,
                    416,
                    429,
                    500,
                    502,
                    503,
                    504,
                }
                if not retryable or failures >= self.retries:
                    raise RuntimeError(
                        f"Download failed; partial data is preserved. Rerun to resume. "
                        f"Last failure: {type(exc).__name__} (HTTP {status or 'unavailable'})."
                    ) from exc
                failures += 1
                self._wait_before_retry(
                    failures,
                    f"Stream interrupted at {format_size(destination.tell())}",
                    response,
                )
            finally:
                if response is not None:
                    response.close()

    @staticmethod
    def _validate_range(
        response: requests.Response, offset: int, end: int, size: int
    ) -> int:
        """Reject mismatched range responses before writing any bytes."""
        if response.headers.get("Content-Encoding", "identity").lower() != "identity":
            raise RuntimeError(
                "Server returned compressed data for a byte-range download."
            )
        if response.status_code == 200:
            length = response.headers.get("Content-Length")
            if length is not None and int(length) != size:
                raise RuntimeError("Full stream response size does not match metadata.")
            return size
        if response.status_code != 206:
            raise RuntimeError(f"Unexpected stream status: {response.status_code}")
        match = re.fullmatch(
            r"bytes (\d+)-(\d+)/(\d+)", response.headers.get("Content-Range", "")
        )
        if not match:
            raise RuntimeError(
                "Missing or invalid Content-Range; partial file was preserved."
            )
        actual_start, actual_end, actual_size = map(int, match.groups())
        if (
            actual_start != offset
            or not offset <= actual_end <= end
            or actual_size != size
        ):
            raise RuntimeError(
                "Content-Range does not match the requested stream; partial file was preserved."
            )
        expected = actual_end - actual_start + 1
        length = response.headers.get("Content-Length")
        if length is not None and int(length) != expected:
            raise RuntimeError("Content-Length does not match Content-Range.")
        return expected

    @staticmethod
    def _write_response(
        response: requests.Response,
        destination: BinaryIO,
        expected: int,
        total_size: int,
        start_time: float,
        initial_size: int,
    ) -> None:
        """Verify each response length, including clean but premature EOFs."""
        received = 0
        for chunk in response.iter_content(chunk_size=CHUNK_SIZE):
            if not chunk:
                continue
            if received + len(chunk) > expected:
                raise RuntimeError(
                    "Stream response contains more data than its declared range."
                )
            destination.write(chunk)
            received += len(chunk)
            progress = build_progress_line(
                destination.tell(), total_size, start_time, initial_size
            )
            print(
                "\r" + CLIStyle.color(progress, CLIStyle.COLORS["CONTENT"]),
                end="",
                flush=True,
            )
        if received != expected:
            raise requests.exceptions.ChunkedEncodingError(
                f"Incomplete response: received {received} of {expected} bytes"
            )

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

        content = self._request_json(NAV_API_URL, allow_logged_out=True)
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
    if "SESSDATA" in parse_cookie_header(cookie_value):
        values[ENV_COOKIE_KEY] = cookie_value.strip()
    else:
        values.pop(ENV_COOKIE_KEY, None)
    write_env_file(config_path, values)


def parse_cookie_header(raw_cookie: str) -> Dict[str, str]:
    """Parse browser Cookie pairs without exposing their values in logs."""
    values: Dict[str, str] = {}
    for item in raw_cookie.split(";"):
        if "=" in item:
            name, value = item.strip().split("=", 1)
            if name and value:
                values[name] = value
    return values


def resolve_cookie(cli_value: Optional[str], config_path: Path) -> str:
    """Use full Cookie values only from the selected credential source."""
    if cli_value:
        return cli_value if "SESSDATA" in parse_cookie_header(cli_value) else ""
    if os.getenv(ENV_SESSDATA_KEY):
        return ""
    env_cookie = os.getenv(ENV_COOKIE_KEY)
    if env_cookie:
        return env_cookie
    return parse_env_file(config_path).get(ENV_COOKIE_KEY, "")


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

    env_cookie = os.getenv(ENV_COOKIE_KEY)
    if env_cookie:
        return extract_sessdata_from_cookie(env_cookie)

    credential_path = config_path or default_config_path()
    config_values = parse_env_file(credential_path)
    config_value = config_values.get(ENV_SESSDATA_KEY) or config_values.get(
        ENV_COOKIE_KEY
    )
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
    downloaded: int,
    total: Optional[int],
    start_time: float,
    initial_downloaded: int = 0,
) -> str:
    """
    Construct a progress line containing size, speed, and ETA.

    ```python
    build_progress_line(1024, 2048, time.monotonic())
    ```
    """
    elapsed = max(time.monotonic() - start_time, 1e-6)
    speed = max(downloaded - initial_downloaded, 0) / elapsed
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
        "--retries",
        type=int,
        default=DEFAULT_RETRIES,
        help=CLIStyle.color(
            "Retry count after a network failure (default: 4)",
            CLIStyle.COLORS["CONTENT"],
        ),
    )
    parser.add_argument(
        "--retry-delay",
        type=float,
        default=DEFAULT_RETRY_DELAY,
        help=CLIStyle.color(
            "Initial retry delay in seconds (default: 2)", CLIStyle.COLORS["CONTENT"]
        ),
    )
    parser.add_argument(
        "--resume",
        action="store_true",
        help=CLIStyle.color(
            "Resume an existing mp4 from an older interrupted download",
            CLIStyle.COLORS["CONTENT"],
        ),
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

    client = BilibiliClient(
        sessdata=sessdata,
        timeout=args.timeout,
        retries=args.retries,
        retry_delay=args.retry_delay,
        cookie=resolve_cookie(args.sessdata, config_path),
    )
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

    if output_path.exists() and not args.resume:
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

    referer = f"https://www.bilibili.com/video/{details.bvid}/"
    print(
        CLIStyle.color(
            "Downloading video...",
            CLIStyle.COLORS["CONTENT"],
        )
    )
    client.download_streams(
        streams,
        output_path,
        referer,
        resume=args.resume,
        identity=f"{details.bvid}:{details.cid}:{args.quality}",
    )

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
            traceback.print_exc()
        print(CLIStyle.color(f"\nError: {exc}", CLIStyle.COLORS["ERROR"]))
        sys.exit(1)
