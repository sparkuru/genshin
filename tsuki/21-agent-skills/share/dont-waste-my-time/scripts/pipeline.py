#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fixed container entrypoint for video evidence and document stages."""

from __future__ import annotations

import argparse
import fcntl
import json
import math
import sys
from pathlib import Path

from dwmt import acquire, delivery, media
from dwmt.common import CLIStyle, ColoredArgumentParser, Runtime, redact


def parser() -> argparse.ArgumentParser:
    """Describe the independently runnable media stages."""
    result = ColoredArgumentParser(description=CLIStyle.color('Video evidence stages; use the host dwmt.py launcher', 'TITLE'), formatter_class=argparse.RawDescriptionHelpFormatter, epilog=CLIStyle.color('Examples:\n  pipeline.py probe --part 1\n  pipeline.py asr --part 1 --model small --language zh\n  pipeline.py frames --part 1 --interval 20 --ocr\n  pipeline.py frame --part 1 --time 42.5', 'SUB_TITLE'))
    result.add_argument('--log', action='store_true', help=CLIStyle.color('Include sanitized diagnostics', 'CONTENT'))
    sub = result.add_subparsers(dest='stage', required=True, parser_class=ColoredArgumentParser)
    for name in ['doctor', 'inspect', 'export', 'verify', 'status']:
        sub.add_parser(name, help=CLIStyle.color(f'Run {name}', 'CONTENT'))
    fetch = sub.add_parser('fetch', help=CLIStyle.color('Acquire selected original video and platform captions', 'CONTENT'))
    fetch.add_argument('--parts', default='requested', help=CLIStyle.color('requested, all, or comma-separated observed part numbers', 'CONTENT'))
    fetch.add_argument('--quality', type=int, choices=[16, 32, 64, 80], default=80, help=CLIStyle.color('Requested platform quality, not guaranteed resolution', 'CONTENT'))
    fetch.add_argument('--force', action='store_true', help=CLIStyle.color('Recompute even matching stage outputs', 'WARNING'))
    models = sub.add_parser('models', help=CLIStyle.color('Prepare the selected ASR model without cookies', 'CONTENT'))
    models.add_argument('--model', choices=['tiny', 'base', 'small', 'medium', 'large-v3'], default='small', help=CLIStyle.color('Whisper model to cache', 'CONTENT'))
    for name in ['probe', 'media', 'asr', 'frames', 'frame', 'index']:
        command = sub.add_parser(name, help=CLIStyle.color(f'Run {name} on one observed source part', 'CONTENT'))
        command.add_argument('--part', type=int, required=True, help=CLIStyle.color('Observed part number', 'CONTENT'))
        command.add_argument('--force', action='store_true', help=CLIStyle.color('Recompute matching outputs', 'WARNING'))
        if name == 'media':
            command.add_argument('--audio-stream', type=int, help=CLIStyle.color('Explicit stream index when several audio tracks exist', 'CONTENT'))
        if name == 'asr':
            command.add_argument('--model', choices=['tiny', 'base', 'small', 'medium', 'large-v3'], default='small', help=CLIStyle.color('An already cached model', 'CONTENT'))
            command.add_argument('--language', help=CLIStyle.color('Language code; omit for automatic detection', 'CONTENT'))
            command.add_argument('--chunk-seconds', type=int, default=300, help=CLIStyle.color('Checkpoint span, 10 to 1800 seconds', 'CONTENT'))
        if name == 'frames':
            command.add_argument('--interval', type=float, default=20, help=CLIStyle.color('Coarse sample interval in seconds', 'CONTENT'))
            command.add_argument('--ocr', action='store_true', help=CLIStyle.color('Retain Tesseract text, boxes and raw TSV', 'CONTENT'))
        if name == 'frame':
            command.add_argument('--time', type=float, required=True, help=CLIStyle.color('Source-video time in seconds', 'CONTENT'))
            command.add_argument('--ocr', action='store_true', help=CLIStyle.color('Retain OCR for this exact selected frame', 'CONTENT'))
        if name == 'index':
            group = command.add_mutually_exclusive_group()
            group.add_argument('--track', help=CLIStyle.color('Bundle-relative observed normalized track path', 'CONTENT'))
            group.add_argument('--visual-only', action='store_true', help=CLIStyle.color('Use visual samples for a justified source without usable speech', 'CONTENT'))
    return result


def dispatch(runtime: Runtime, args: argparse.Namespace) -> None:
    """Call only the selected fixed pipeline stage."""
    if args.stage == 'doctor':
        media.doctor(runtime)
    elif args.stage == 'inspect':
        acquire.inspect_source(runtime)
    elif args.stage == 'fetch':
        if runtime.meta['source']['kind'] == 'local':
            acquire.fetch_local(runtime, args.force)
        else:
            acquire.fetch_bilibili(runtime, args.parts, args.quality, args.force)
    elif args.stage == 'models':
        media.models(runtime, args.model)
    elif args.stage == 'probe':
        media.probe(runtime, args.part, args.force)
    elif args.stage == 'media':
        media.media(runtime, args.part, args.audio_stream, args.force)
    elif args.stage == 'asr':
        if not 10 <= args.chunk_seconds <= 1800:
            raise ValueError('ASR chunk length must be 10 to 1800 seconds')
        media.asr(runtime, args.part, args.model, args.language, args.chunk_seconds, args.force)
    elif args.stage == 'frames':
        if not math.isfinite(args.interval) or args.interval <= 0:
            raise ValueError('Frame interval must be a finite positive number')
        media.frames(runtime, args.part, args.interval, args.ocr, args.force)
    elif args.stage == 'frame':
        media.frame(runtime, args.part, args.time, args.ocr, args.force)
    elif args.stage == 'index':
        delivery.index(runtime, args.part, args.track, args.visual_only)
    elif args.stage == 'export':
        delivery.export(runtime)
    elif args.stage == 'verify':
        delivery.verify(runtime)
    else:
        print(CLIStyle.color(json.dumps(runtime.meta, ensure_ascii=False, indent=2)))


def main() -> int:
    """Serialize state changes; a state file alone never proves a live job."""
    args = parser().parse_args()
    with Path('/work/.pipeline.lock').open('a') as handle:
        fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        runtime = Runtime()
        dispatch(runtime, args)
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except BlockingIOError:
        print(CLIStyle.color('A stage is already running. Inspect the same job container before retrying.', 'WARNING'), file=sys.stderr)
        sys.exit(2)
    except FileNotFoundError as exc:
        detail = exc.filename or redact(str(exc))
        print(CLIStyle.color(f'Missing evidence, cached model or executable: {detail}', 'ERROR'), file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        label = f'Error [{type(exc).__name__}]' if '--log' in sys.argv else 'Error'
        print(CLIStyle.color(f'{label}: {redact(str(exc))}', 'ERROR'), file=sys.stderr)
        sys.exit(1)
