# -*- coding: utf-8 -*-
"""Shared standard-library paths, logging, state and CLI helpers."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable


class CLIStyle:
    """Semantic terminal styles that respect non-interactive output."""

    COLORS = {'TITLE': 36, 'SUB_TITLE': 32, 'CONTENT': 37, 'WARNING': 33, 'ERROR': 31}

    @staticmethod
    def color(text: str, role: str = 'CONTENT') -> str:
        """Apply terminal color only to interactive output."""
        if os.environ.get('NO_COLOR') or not sys.stderr.isatty():
            return text
        return f'\033[1;{CLIStyle.COLORS[role]}m{text}\033[0m'


class ColoredArgumentParser(argparse.ArgumentParser):
    """Keep descriptions, sections and examples readable in terminal help."""

    def format_help(self) -> str:
        """Style the complete generated help."""
        return CLIStyle.color(super().format_help(), 'TITLE')


def utc_now() -> str:
    """Return an unambiguous timestamp."""
    return datetime.now(timezone.utc).isoformat()


def read_json(path: Path) -> Any:
    """Read a JSON artifact."""
    return json.loads(path.read_text(encoding='utf-8'))


def write_json(path: Path, value: Any) -> None:
    """Publish JSON atomically without leaving partial state files."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent, delete=False) as handle:
        temporary = Path(handle.name)
        json.dump(value, handle, ensure_ascii=False, indent=2)
        handle.write('\n')
    temporary.replace(path)


def sha256(path: Path) -> str:
    """Hash exact file bytes."""
    with path.open('rb') as handle:
        return hashlib.file_digest(handle, 'sha256').hexdigest()


def inside(root: Path, path: Path) -> Path:
    """Resolve an existing or new path within an explicit root."""
    resolved = path.resolve()
    if not resolved.is_relative_to(root.resolve()):
        raise ValueError(f'Path escapes its allowed root: {path.name}')
    return resolved


def redact(text: str) -> str:
    """Remove signed URLs and common credential fields from diagnostics."""
    text = re.sub(r'https?://[^\s<>"\x27]+', '[URL REDACTED]', text)
    return re.sub(r'(?i)(cookie|sessdata|authorization|token|password)\s*[:=][^\n]*', r'\1=[REDACTED]', text)


def timestamp(seconds: float, separator: str = ',') -> str:
    """Convert source-video seconds to subtitle time."""
    total = round(seconds * 1000)
    hours, total = divmod(total, 3600000)
    minutes, total = divmod(total, 60000)
    seconds_int, milliseconds = divmod(total, 1000)
    return f'{hours:02}:{minutes:02}:{seconds_int:02}{separator}{milliseconds:03}'


def subtitles(base: Path, segments: list[dict[str, Any]]) -> list[Path]:
    """Write SRT and VTT without changing recognized text."""
    srt, vtt = [], ['WEBVTT\n']
    for index, row in enumerate(segments, 1):
        start, end, text = row['start'], row['end'], row['text']
        srt.append(f'{index}\n{timestamp(start)} --> {timestamp(end)}\n{text}\n')
        vtt.append(f'{timestamp(start, ".")} --> {timestamp(end, ".")}\n{text}\n')
    paths = [base.with_suffix('.srt'), base.with_suffix('.vtt')]
    for path, content in zip(paths, [srt, vtt]):
        path.write_text('\n'.join(content), encoding='utf-8')
    return paths


class Runtime:
    """Own a job's container-local paths, measured events and stage cache."""

    def __init__(self, work: Path = Path('/work')) -> None:
        """Load the initialized job without consulting host configuration."""
        self.work = work.resolve()
        self.bundle = self.work / 'bundle'
        self.meta_path = self.bundle / 'meta.json'
        self.meta = read_json(self.meta_path)
        self.state_path = self.work / 'state.json'
        self.state = read_json(self.state_path) if self.state_path.exists() else {}

    def save_meta(self) -> None:
        """Persist the latest source and runtime facts."""
        self.meta['updated_at'] = utc_now()
        write_json(self.meta_path, self.meta)

    def event(self, stage: str, status: str, **details: Any) -> None:
        """Append a structured event without raw network responses."""
        record = {'time': utc_now(), 'stage': stage, 'status': status, 'image_id': self.meta.get('runtime', {}).get('image_id'), **details}
        path = self.bundle / 'logs/events.jsonl'
        with path.open('a', encoding='utf-8') as handle:
            handle.write(json.dumps(record, ensure_ascii=False) + '\n')
        print(CLIStyle.color(f'{stage}: {status}'), flush=True)

    def command(self, arguments: list[str], timeout: int = 3600) -> str:
        """Run an offline tool, retaining sanitized errors and exit status."""
        result = subprocess.run(arguments, capture_output=True, text=True, timeout=timeout)
        if result.returncode:
            self.event(arguments[0], 'failed', exit_code=result.returncode, stderr=redact(result.stderr[-4000:]))
            raise RuntimeError(f'{arguments[0]} failed with exit code {result.returncode}')
        return result.stdout

    def part(self, number: int) -> dict[str, Any]:
        """Select an actually acquired part."""
        rows = [row for row in self.meta.get('parts', []) if row['part'] == number]
        if len(rows) != 1 or not rows[0].get('video'):
            raise ValueError(f'Part {number} is not acquired')
        return rows[0]

    def stage(self, key: str, inputs: list[Path], parameters: dict[str, Any], action: Callable[[], list[Path]], force: bool = False) -> bool:
        """Reuse only matching inputs, parameters, image and output bytes."""
        fingerprint = {'inputs': {str(path.relative_to(self.work)): sha256(path) for path in inputs}, 'parameters': parameters, 'image': self.meta.get('runtime', {}).get('image_id')}
        previous = self.state.get(key, {})
        cached = previous.get('status') == 'succeeded' and previous.get('fingerprint') == fingerprint
        if cached and not force:
            valid = all(inside(self.work, self.work / name).is_file() and sha256(self.work / name) == digest for name, digest in previous.get('outputs', {}).items())
            if valid and previous.get('outputs'):
                self.event(key, 'cached')
                return False
        self.state[key] = {'status': 'running', 'started_at': utc_now(), 'fingerprint': fingerprint}
        write_json(self.state_path, self.state)
        self.event(key, 'running')
        try:
            outputs = action()
            checked = [inside(self.work, path) for path in outputs]
            hashes = {str(path.relative_to(self.work)): sha256(path) for path in checked}
        except Exception as exc:
            self.state[key].update(status='failed', error_type=type(exc).__name__, finished_at=utc_now())
            write_json(self.state_path, self.state)
            self.event(key, 'failed', error_type=type(exc).__name__)
            raise
        self.state[key].update(status='succeeded', outputs=hashes, finished_at=utc_now())
        write_json(self.state_path, self.state)
        self.meta.setdefault('stages', {})[key] = {'status': 'succeeded', 'finished_at': utc_now(), 'image_id': self.meta.get('runtime', {}).get('image_id')}
        self.save_meta()
        self.event(key, 'succeeded', files=len(hashes))
        return True
