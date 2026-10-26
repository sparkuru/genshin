# -*- coding: utf-8 -*-
"""Measured media probes, resumable ASR and timestamped source frames."""

from __future__ import annotations

import csv
import importlib.metadata
import json
import math
import re
import shutil
from pathlib import Path
from typing import Any

from faster_whisper import WhisperModel
from faster_whisper.utils import download_model

from dwmt.common import Runtime, read_json, sha256, subtitles, write_json


def doctor(runtime: Runtime) -> None:
    """Exercise actual decode, OCR and DOCX generation, not just versions."""
    directory = runtime.work / 'doctor'
    directory.mkdir(exist_ok=True)
    audio, picture, document = directory / 'tone.wav', directory / 'text.png', directory / 'probe.docx'
    runtime.command(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', 'sine=frequency=440:duration=0.2', str(audio)])
    probe_result = json.loads(runtime.command(['ffprobe', '-v', 'error', '-show_format', '-of', 'json', str(audio)]))
    runtime.command(['ffmpeg', '-v', 'error', '-y', '-f', 'lavfi', '-i', 'color=white:s=640x160', '-vf', 'drawtext=text=DWMT123:x=30:y=30:fontsize=70:fontcolor=black', '-frames:v', '1', str(picture)])
    recognized = runtime.command(['tesseract', str(picture), 'stdout', '-l', 'eng', '--psm', '6'])
    source = directory / 'probe.md'
    source.write_text('# Tools probe\n\nA real generated document.\n', encoding='utf-8')
    runtime.command(['pandoc', str(source), '-o', str(document)])
    if 'DWMT123' not in recognized.replace(' ', '') or document.stat().st_size < 1000:
        raise RuntimeError('The real tools smoke probe failed')
    versions = {name: importlib.metadata.version(name) for name in ['requests', 'faster-whisper', 'ctranslate2', 'av']}
    evidence = {'packages': versions, 'ffmpeg': runtime.command(['ffmpeg', '-version']).splitlines()[0], 'tesseract': runtime.command(['tesseract', '--version']).splitlines()[0], 'pandoc': runtime.command(['pandoc', '--version']).splitlines()[0], 'actual_probes': {'audio_seconds': probe_result['format']['duration'], 'ocr_text': recognized.strip(), 'docx_bytes': document.stat().st_size}}
    write_json(runtime.bundle / 'evidence/tools.json', evidence)
    runtime.event('doctor', 'succeeded')


def probe(runtime: Runtime, number: int, force: bool = False) -> dict[str, Any]:
    """Observe actual streams before choosing audio and subtitle handling."""
    part = runtime.part(number)
    video = runtime.bundle / part['video']
    output = runtime.bundle / f'evidence/p{number:03}-ffprobe.json'

    def inspect() -> list[Path]:
        """Probe without decoding the whole source."""
        data = json.loads(runtime.command(['ffprobe', '-v', 'error', '-show_format', '-show_streams', '-of', 'json', str(video)]))
        write_json(output, data)
        return [output]

    runtime.stage(f'probe-p{number:03}', [video], {}, inspect, force)
    data = read_json(output)
    videos = [row for row in data['streams'] if row['codec_type'] == 'video' and not row.get('disposition', {}).get('attached_pic')]
    if not videos or float(data['format'].get('duration', 0)) <= 0:
        raise ValueError('No timed video stream was found')
    part.update(duration_seconds=float(data['format']['duration']), video_stream=videos[0]['index'], width=videos[0]['width'], height=videos[0]['height'], audio_streams=[{'index': row['index'], 'codec': row['codec_name'], 'tags': row.get('tags', {})} for row in data['streams'] if row['codec_type'] == 'audio'], embedded_subtitles=[{'index': row['index'], 'codec': row['codec_name'], 'tags': row.get('tags', {})} for row in data['streams'] if row['codec_type'] == 'subtitle'])
    video_start = max(0.0, float(videos[0].get('start_time', 0)) - float(data['format'].get('start_time', 0)))
    part['video_start_seconds'] = video_start
    stream_duration = videos[0].get('duration')
    part['video_end_seconds'] = min(part['duration_seconds'], video_start + float(stream_duration)) if stream_duration and stream_duration != 'N/A' else part['duration_seconds']
    if runtime.meta['source']['kind'] == 'local':
        part['subtitle_status'] = 'embedded' if part['embedded_subtitles'] else 'none'
    runtime.save_meta()
    return data


def parse_srt(path: Path, prefix: str) -> list[dict[str, Any]]:
    """Normalize FFmpeg-generated text subtitles, preserving their text."""
    pattern = r'(\d+):(\d+):(\d+)[,.](\d+)\s*-->\s*(\d+):(\d+):(\d+)[,.](\d+)'
    records = []
    for block in re.split(r'\n\s*\n', path.read_text(encoding='utf-8').strip()):
        match = re.search(pattern, block)
        if not match:
            continue
        values = [int(value) for value in match.groups()]
        start = values[0] * 3600 + values[1] * 60 + values[2] + values[3] / 1000
        end = values[4] * 3600 + values[5] * 60 + values[6] + values[7] / 1000
        text = block[match.end():].strip()
        records.append({'id': f'{prefix}-s{len(records)}', 'start': start, 'end': end, 'text': text})
    return records


def media(runtime: Runtime, number: int, audio_stream: int | None, force: bool) -> None:
    """Fully decode the source, extract selected audio and text subtitles."""
    data = probe(runtime, number)
    part = runtime.part(number)
    video = runtime.bundle / part['video']
    audio_choices = [row['index'] for row in part['audio_streams']]
    if len(audio_choices) > 1 and audio_stream is None:
        raise ValueError('Multiple audio streams: inspect FFprobe evidence and choose --audio-stream')
    selected = audio_stream if audio_stream is not None else next(iter(audio_choices), None)
    if selected is not None and selected not in audio_choices:
        raise ValueError('The selected audio stream was not observed')
    audio = runtime.work / f'audio/p{number:03}.wav'
    proof = runtime.bundle / f'evidence/p{number:03}-decode.json'

    def process() -> list[Path]:
        """Retain completion evidence only after FFmpeg reaches EOF."""
        command = ['ffmpeg', '-v', 'error', '-xerror', '-i', str(video), '-map', '0:v', '-map', '0:a?', '-f', 'null', '-']
        runtime.command(command)
        write_json(proof, {'source_sha256': sha256(video), 'command': command, 'exit_code': 0, 'decoded_to_eof': True})
        outputs = [proof]
        if selected is not None:
            runtime.command(['ffmpeg', '-v', 'error', '-y', '-i', str(video), '-map', f'0:{selected}', '-vn', '-af', 'aresample=16000:async=1:first_pts=0', '-ac', '1', '-ar', '16000', str(audio)])
            outputs.append(audio)
        return outputs

    runtime.stage(f'media-p{number:03}', [video], {'audio_stream': selected}, process, force)
    part['audio_stream'] = selected
    part['audio'] = str(audio.relative_to(runtime.work)) if selected is not None else None
    part['audio_timing'] = 'FFmpeg source-relative timestamps; aresample first_pts=0 retains leading silence.'
    tracks = [row for row in part.get('tracks', []) if row.get('kind') != 'embedded']
    for row in data['streams']:
        if row['codec_type'] != 'subtitle' or row['codec_name'] not in {'subrip', 'ass', 'ssa', 'mov_text', 'webvtt', 'text'}:
            continue
        base = runtime.bundle / f'transcripts/p{number:03}-embedded-{row["index"]}'
        runtime.command(['ffmpeg', '-v', 'error', '-y', '-i', str(video), '-map', f'0:{row["index"]}', str(base.with_suffix('.srt'))])
        segments = parse_srt(base.with_suffix('.srt'), f'embedded-p{number:03}-t{row["index"]}')
        write_json(base.with_suffix('.json'), {'kind': 'embedded', 'part': number, 'stream': row['index'], 'segments': segments})
        subtitles(base, segments)
        tracks.append({'kind': 'embedded', 'stream': row['index'], 'path': str(base.with_suffix('.json').relative_to(runtime.bundle))})
    part['tracks'] = tracks
    if Path('/inputs/reference.docx').is_file():
        shutil.copyfile('/inputs/reference.docx', runtime.work / 'reference.docx')
    runtime.save_meta()


def models(runtime: Runtime, model_name: str) -> None:
    """Fetch only a selected model in the credential-free online service."""
    directory = Path(download_model(model_name, cache_dir='/cache/huggingface'))
    record = {'model': model_name, 'snapshot': directory.name, 'model_sha256': sha256(directory / 'model.bin')}
    write_json(runtime.bundle / f'evidence/model-{model_name}.json', record)
    runtime.meta.setdefault('models', {})[model_name] = record
    runtime.save_meta()
    runtime.event('models', 'succeeded', model=model_name, snapshot=directory.name)


def asr(runtime: Runtime, number: int, model_name: str, language: str | None, chunk_seconds: int, force: bool) -> None:
    """Checkpoint complete chunks and merge their source-video timestamps."""
    part = runtime.part(number)
    if not part.get('audio') or not (runtime.work / part['audio']).is_file():
        raise ValueError('Run media first; a source without audio needs visual evidence instead of ASR')
    model_directory = Path(download_model(model_name, cache_dir='/cache/huggingface', local_files_only=True))
    model_hash = sha256(model_directory / 'model.bin')
    model = WhisperModel(str(model_directory), device='cpu', compute_type='int8', cpu_threads=8)
    audio = runtime.work / part['audio']
    audio_probe = json.loads(runtime.command(['ffprobe', '-v', 'error', '-show_format', '-of', 'json', str(audio)]))
    duration = float(audio_probe['format']['duration'])
    starts = list(range(0, math.ceil(duration), chunk_seconds))
    if len(starts) > 1 and duration - starts[-1] < 1:
        starts.pop()
    paths = []
    for index, start in enumerate(starts):
        length = (starts[index + 1] if index + 1 < len(starts) else duration) - start
        target = runtime.bundle / f'transcripts/p{number:03}-asr-chunks/chunk-{index:04}.json'

        def transcribe_chunk() -> list[Path]:
            """Retain raw engine output plus explicit global offsets."""
            clip = runtime.work / f'audio/p{number:03}-chunk.wav'
            runtime.command(['ffmpeg', '-v', 'error', '-y', '-ss', str(start), '-i', str(audio), '-t', str(length), str(clip)])
            generated, info = model.transcribe(str(clip), language=language, beam_size=5, vad_filter=length >= 1, word_timestamps=True)
            segments = []
            for segment in generated:
                raw = segment._asdict()
                raw['words'] = [word._asdict() for word in segment.words or []]
                segments.append(raw)
            write_json(target, {'part': number, 'chunk': index, 'offset_seconds': start, 'duration_seconds': length, 'language': info.language, 'raw_segments': segments})
            return [target]

        parameters = {'model': model_name, 'model_sha256': model_hash, 'language': language, 'start': start, 'length': length, 'beam_size': 5, 'vad_filter': length >= 1, 'word_timestamps': True}
        runtime.stage(f'asr-p{number:03}-c{index:04}', [audio], parameters, transcribe_chunk, force)
        paths.append(target)
    merged = []
    for path in paths:
        chunk = read_json(path)
        offset = chunk['offset_seconds']
        for raw in chunk['raw_segments']:
            words = [word | {'start': word['start'] + offset, 'end': word['end'] + offset} for word in raw.get('words', [])]
            merged.append(raw | {'id': f'asr-p{number:03}-s{len(merged)}', 'start': raw['start'] + offset, 'end': raw['end'] + offset, 'words': words, 'raw_chunk': str(path.relative_to(runtime.bundle)), 'raw_segment_id': raw['id']})
    base = runtime.bundle / f'transcripts/p{number:03}-asr'
    write_json(base.with_suffix('.json'), {'kind': 'asr', 'part': number, 'source_sha256': sha256(runtime.bundle / part['video']), 'audio_sha256': sha256(audio), 'audio_stream': part['audio_stream'], 'audio_duration_seconds': duration, 'model': model_name, 'model_snapshot': model_directory.name, 'model_sha256': model_hash, 'language': language, 'chunk_seconds': chunk_seconds, 'compute_type': 'int8', 'segments': merged, 'limitations': ['Chunk boundaries may split speech; review important boundary passages against the source.']})
    subtitles(base, merged)
    part['asr'] = str(base.with_suffix('.json').relative_to(runtime.bundle))
    runtime.save_meta()
    runtime.event(f'asr-p{number:03}', 'succeeded', segments=len(merged), chunks=len(paths))


def extract_frame(runtime: Runtime, number: int, seconds: float, target: Path, ocr: bool) -> dict[str, Any]:
    """Extract a source frame and optionally retain raw OCR boxes."""
    part = runtime.part(number)
    if not 0 <= seconds < part['duration_seconds']:
        raise ValueError('Frame time is outside the observed source duration')
    if not part.get('video_start_seconds', 0) <= seconds < part.get('video_end_seconds', part['duration_seconds']):
        raise ValueError('No video stream frame at this time; inspect the observed video interval')
    target.parent.mkdir(parents=True, exist_ok=True)
    runtime.command(['ffmpeg', '-v', 'error', '-y', '-ss', str(seconds), '-i', str(runtime.bundle / part['video']), '-map', f'0:{part["video_stream"]}', '-frames:v', '1', '-q:v', '2', str(target)])
    if not target.is_file():
        raise ValueError('No frame decoded at the requested seek; inspect actual video timing')
    record = {'part': number, 'time_seconds': seconds, 'frame': str(target.relative_to(runtime.bundle)), 'source_sha256': sha256(runtime.bundle / part['video']), 'frame_sha256': sha256(target), 'timing_precision': 'Source seek time; rounding to a video frame boundary may apply.', 'ocr': None}
    if ocr:
        tsv = runtime.command(['tesseract', str(target), 'stdout', '-l', 'chi_sim+eng', '--psm', '11', 'tsv'])
        tsv_path = target.with_suffix('.tsv')
        tsv_path.write_text(tsv, encoding='utf-8')
        boxes = [row for row in csv.DictReader(tsv.splitlines(), delimiter='\t') if row.get('text', '').strip()]
        record['ocr'] = {'engine': 'tesseract', 'languages': 'chi_sim+eng', 'text': ' '.join(row['text'] for row in boxes), 'boxes': boxes, 'tsv': str(tsv_path.relative_to(runtime.bundle))}
    return record


def frames(runtime: Runtime, number: int, interval: float, ocr: bool, force: bool) -> None:
    """Create coarse visual evidence and contact sheets, not automatic report picks."""
    part = runtime.part(number)
    if 'duration_seconds' not in part:
        raise ValueError('Run probe before extracting frames')
    video_start = part.get('video_start_seconds', 0)
    video_end = part.get('video_end_seconds', part['duration_seconds'])
    count = math.ceil((video_end - video_start) / interval)
    if count > 1000:
        raise ValueError('More than 1000 coarse frames; increase --interval and refine key moments with frame')
    source = runtime.bundle / part['video']
    directory = runtime.bundle / f'evidence/frames/p{number:03}'
    output = runtime.bundle / f'evidence/p{number:03}-frames.json'

    def sample() -> list[Path]:
        """Sample and OCR each requested source timestamp."""
        records, artifacts = [], []
        for index in range(count):
            target = directory / f'frame-{index:06}.jpg'
            record = extract_frame(runtime, number, round(video_start + index * interval, 6), target, ocr)
            records.append(record)
            artifacts.append(target)
            if ocr:
                artifacts.append(target.with_suffix('.tsv'))
        pattern = str(directory / 'contact-%03d.jpg')
        runtime.command(['ffmpeg', '-v', 'error', '-y', '-i', str(directory / 'frame-%06d.jpg'), '-frames:v', str(math.ceil(count / 16)), '-vf', 'scale=320:180:force_original_aspect_ratio=decrease,pad=320:180:(ow-iw)/2:(oh-ih)/2,drawtext=text=%{n}:x=4:y=4:fontsize=22:fontcolor=yellow:box=1:boxcolor=black,tile=4x4', '-fps_mode', 'vfr', pattern])
        artifacts.extend(sorted(directory.glob('contact-*.jpg')))
        write_json(output, {'part': number, 'sample_interval_seconds': interval, 'video_interval_seconds': [video_start, video_end], 'frames': records, 'contact_sheet_labels': 'Zero-based frame index; resolve source time through this JSON.', 'limitations': ['Sampling does not capture every transition; OCR may miss or misread text.', 'Sampling covers the observed video stream interval; audio may extend beyond it.']})
        return [output, *artifacts]

    runtime.stage(f'frames-p{number:03}', [source], {'interval': interval, 'ocr': ocr}, sample, force)
    part['frames'] = str(output.relative_to(runtime.bundle))
    runtime.save_meta()


def frame(runtime: Runtime, number: int, seconds: float, ocr: bool, force: bool) -> None:
    """Capture an agent-selected key frame directly from the original video."""
    part = runtime.part(number)
    name = f'p{number:03}-t{round(seconds * 1000):010}.jpg'
    target = runtime.bundle / 'assets' / name
    metadata = runtime.bundle / 'evidence' / (target.stem + '.json')

    def capture() -> list[Path]:
        """Keep the frame and its source identity together."""
        record = extract_frame(runtime, number, seconds, target, ocr)
        write_json(metadata, record)
        return [target, metadata, *([target.with_suffix('.tsv')] if ocr else [])]

    runtime.stage(f'frame-{target.stem}', [runtime.bundle / part['video']], {'time_seconds': seconds, 'ocr': ocr}, capture, force)
    runtime.event('frame-selected', 'succeeded', asset=str(target.relative_to(runtime.bundle)), time_seconds=seconds)
