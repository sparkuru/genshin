# -*- coding: utf-8 -*-
"""Evidence alignment, report export and mechanical delivery checks."""

from __future__ import annotations

import json
import math
import re
import zipfile
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlparse
from xml.etree import ElementTree

from dwmt.common import CLIStyle, Runtime, inside, read_json, sha256, timestamp, utc_now, write_json


def index(runtime: Runtime, number: int, track: str | None, visual_only: bool) -> None:
    """Associate independent evidence without claiming nearest frames are simultaneous."""
    part = runtime.part(number)
    asr = read_json(runtime.bundle / part['asr'])['segments'] if part.get('asr') else []
    frames = read_json(runtime.bundle / part['frames'])['frames'] if part.get('frames') else []
    if visual_only:
        anchor = [{'id': f'visual-p{number:03}-f{position}', 'start': row['time_seconds'], 'end': frames[position + 1]['time_seconds'] if position + 1 < len(frames) else part['duration_seconds'], 'text': (row.get('ocr') or {}).get('text', '')} for position, row in enumerate(frames)]
        chosen = None
    else:
        choices = [row['path'] for row in part.get('tracks', [])]
        if track:
            chosen = str(inside(runtime.bundle, runtime.bundle / track).relative_to(runtime.bundle))
            if chosen not in [*choices, part.get('asr')]:
                raise ValueError('Choose an observed subtitle or ASR track')
        elif len(choices) == 1:
            chosen = choices[0]
        elif not choices and part.get('asr'):
            chosen = part['asr']
        else:
            raise ValueError('Inspect track quality, then select --track; use --visual-only only for a justified visual report')
        anchor = read_json(runtime.bundle / chosen)['segments']
    if not anchor:
        raise ValueError('The selected evidence anchor is empty')
    rows = []
    for segment in anchor:
        overlapping = [row['id'] for row in asr if row['start'] < segment['end'] and row['end'] > segment['start']]
        nearest = min(frames, key=lambda row: abs(row['time_seconds'] - segment['start'])) if frames else None
        rows.append(segment | {'part': number, 'asr_segment_ids': overlapping, 'nearest_frame': nearest['frame'] if nearest else None, 'nearest_frame_seconds': nearest['time_seconds'] if nearest else None})
    output = runtime.bundle / f'evidence/p{number:03}-timeline.json'
    write_json(output, {'part': number, 'time_origin': part['video'], 'source_sha256': sha256(runtime.bundle / part['video']), 'anchor_track': chosen, 'anchor_sha256': sha256(runtime.bundle / chosen) if chosen else None, 'asr_sha256': sha256(runtime.bundle / part['asr']) if part.get('asr') else None, 'frames_sha256': sha256(runtime.bundle / part['frames']) if part.get('frames') else None, 'visual_only': visual_only, 'rows': rows})
    timed = runtime.bundle / f'transcripts/p{number:03}-timed.md'
    lines = [f'# Timed evidence: part {number}\n', 'Unedited selected evidence; machine output is not a human transcription.\n']
    for row in rows:
        lines.append(f'[{timestamp(row["start"], ".")}]({"../" + part["video"] + "#t=" + str(row["start"])}) {row["text"]}  ')
    timed.write_text('\n'.join(lines), encoding='utf-8')
    part.update(timeline=str(output.relative_to(runtime.bundle)), anchor_track=chosen, visual_only=visual_only)
    runtime.save_meta()
    runtime.event(f'index-p{number:03}', 'succeeded', rows=len(rows))


def report_ast(runtime: Runtime) -> tuple[Path, dict[str, Any]]:
    """Parse report resources with Pandoc rather than Markdown regexes."""
    path = runtime.bundle / 'markdown/report.md'
    if not path.is_file() or len(path.read_text(encoding='utf-8').strip()) < 100:
        raise ValueError('Write the agent-composed markdown/report.md before export')
    ast = json.loads(runtime.command(['pandoc', str(path), '-f', 'markdown', '-t', 'json']))
    return path, ast


def nodes(value: Any, kind: str) -> list[dict[str, Any]]:
    """Collect Pandoc nodes recursively."""
    if isinstance(value, list):
        return [node for item in value for node in nodes(item, kind)]
    if isinstance(value, dict):
        result = [value] if value.get('t') == kind else []
        return result + [node for item in value.values() for node in nodes(item, kind)]
    return []


def resource(runtime: Runtime, report: Path, target: str, image: bool) -> Path | None:
    """Reject embedded resources outside the bundle or remote screenshot substitutes."""
    parsed = urlparse(target)
    if parsed.scheme in {'http', 'https'} and not image:
        return None
    if parsed.scheme or parsed.netloc or Path(unquote(parsed.path)).is_absolute():
        raise ValueError('Use bundle-relative resources; report images must be local source screenshots')
    path = inside(runtime.bundle, report.parent / unquote(parsed.path))
    if parsed.path and not path.is_file():
        raise FileNotFoundError(f'Broken report resource: {target}')
    if image and (not path.is_relative_to(runtime.bundle / 'assets') or path.suffix.lower() not in {'.jpg', '.jpeg', '.png'}):
        raise ValueError('Report screenshots must be JPG/PNG files under assets/')
    return path


def check_resources(runtime: Runtime, report: Path, ast: dict[str, Any]) -> list[Path]:
    """Verify local links and source-time fragments before exporting."""
    images = [resource(runtime, report, row['c'][-1][0], True) for row in nodes(ast, 'Image')]
    for row in nodes(ast, 'Link'):
        target = row['c'][-1][0]
        path = resource(runtime, report, target, False)
        fragment = urlparse(target).fragment
        if path and fragment.startswith('t='):
            parts = [part for part in runtime.meta['parts'] if runtime.bundle / part['video'] == path]
            seconds = float(fragment[2:].split(',')[0])
            if not parts or not 0 <= seconds <= parts[0]['duration_seconds']:
                raise ValueError('A report video time link is outside its source part')
    return images


def export(runtime: Runtime) -> None:
    """Export reviewed Markdown through Pandoc, retaining source fingerprints."""
    report, ast = report_ast(runtime)
    images = check_resources(runtime, report, ast)
    title = next(iter(report.read_text(encoding='utf-8').splitlines()), '').lstrip('# ').strip()
    css = runtime.bundle / 'assets/report.css'
    docx = runtime.bundle / 'docx/report.docx'
    html = runtime.bundle / 'report.html'
    reference = runtime.work / 'reference.docx'
    command = ['pandoc', str(report), '-f', 'markdown', '-t', 'docx', '--resource-path', str(report.parent), '-o', str(docx)]
    if reference.is_file():
        command += ['--reference-doc', str(reference)]
    runtime.command(command)
    runtime.command(['pandoc', str(report), '-f', 'markdown', '-t', 'html5', '--resource-path', str(report.parent), '--standalone', '--embed-resources', '--css', str(css), '--metadata', f'pagetitle={title}', '-o', str(html)])
    html_text = html.read_text(encoding='utf-8')
    html_text = re.sub(r'(href=["\x27])\.\./(?!\.\./)', r'\1', html_text)
    html.write_text(html_text, encoding='utf-8')
    runtime.meta['export'] = {'markdown_sha256': sha256(report), 'css_sha256': sha256(css), 'docx_sha256': sha256(docx), 'html_sha256': sha256(html), 'images': len(images), 'reference_docx_sha256': sha256(reference) if reference.is_file() else None, 'exported_at': utc_now()}
    runtime.save_meta()
    runtime.event('export', 'succeeded', images=len(images))


def require(condition: bool, message: str) -> None:
    """Stop on a failed artifact invariant."""
    if not condition:
        raise ValueError(message)


def validate_times(rows: list[dict[str, Any]], duration: float, allow_empty: bool = False) -> None:
    """Check finite, ordered segment and word bounds against actual media."""
    require(bool(rows) or allow_empty, 'An expected timed track is empty')
    for row in rows:
        start, end = row['start'], row['end']
        require(isinstance(start, (float, int)) and isinstance(end, (float, int)), 'Timestamps must be numeric')
        require(math.isfinite(start) and math.isfinite(end) and 0 <= start <= end <= duration + 0.25, 'A timestamp is outside source duration')
        for word in row.get('words', []):
            require(0 <= word['start'] <= word['end'] <= duration + 0.25, 'A word timestamp is outside source duration')


def coverage(rows: list[dict[str, Any]], duration: float) -> None:
    """Require the editorial review to account for omitted as well as included time."""
    validate_times(rows, duration)
    reached = 0.0
    for row in sorted(rows, key=lambda item: item['start']):
        require(row['start'] <= reached + 0.25, 'Editorial coverage has an unexplained time gap')
        require(row.get('topic') and row.get('reason') and row.get('treatment') in {'included', 'condensed', 'omitted'}, 'Coverage needs a topic, treatment and reason')
        reached = max(reached, row['end'])
    require(reached >= duration - 0.25, 'Editorial coverage does not reach the selected part ending')


def text_values(value: Any) -> list[str]:
    """Collect literal strings from a source evidence JSON."""
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        return [text for item in value for text in text_values(item)]
    if isinstance(value, dict):
        return [text for item in value.values() for text in text_values(item)]
    return []


def editorial_review(runtime: Runtime, images: list[Path], report: str) -> dict[str, Any]:
    """Check the presence and traceability of agent decisions, not their truth."""
    review = read_json(runtime.bundle / 'evidence/editorial-review.json')
    require(bool(review.get('intent')) and bool(review.get('scope')) and review.get('reviewed_by') == 'agent', 'Record the original intent, scope and agent review')
    decisions = review.get('parts', [])
    require({row['part'] for row in decisions} == set(runtime.meta['selected_parts']), 'Review every selected part')
    for decision in decisions:
        part = runtime.part(decision['part'])
        assessment = decision['subtitle_assessment']
        require(assessment.get('observed_status') == part['subtitle_status'] and bool(assessment.get('reason')), 'Subtitle decisions must match the actual availability state')
        require(assessment.get('chosen_track') == part.get('anchor_track'), 'The editorial chosen track differs from the actual timeline anchor')
        for name in ['asr', 'visuals']:
            require(decision[name].get('decision') in {'run', 'skip'} and bool(decision[name].get('reason')), f'Record an explicit {name} decision and reason')
        if decision['asr']['decision'] == 'run':
            require(bool(part.get('asr')), 'ASR was requested in the review but no ASR was produced')
        if decision['visuals']['decision'] == 'run':
            require(bool(part.get('frames')), 'Visual review needs a coarse frame inventory')
        coverage(decision['coverage'], part['duration_seconds'])
    figures = review.get('figures', [])
    require(len(figures) == len(images), 'Review every report image exactly once')
    require({row['asset'] for row in figures} == {str(path.relative_to(runtime.bundle)) for path in images}, 'Report images and reviewed figures differ')
    for row in figures:
        asset = inside(runtime.bundle, runtime.bundle / row['asset'])
        evidence = read_json(runtime.bundle / 'evidence' / (asset.stem + '.json'))
        part = runtime.part(row['part'])
        require(row.get('visually_reviewed') is True and bool(row.get('purpose')) and bool(row.get('caption')), 'Each image needs visual review, a caption and an explanatory purpose')
        require(evidence['part'] == row['part'] and evidence['time_seconds'] == row['time_seconds'], 'Figure time differs from actual extraction evidence')
        require(evidence['frame_sha256'] == sha256(asset) and evidence['source_sha256'] == sha256(runtime.bundle / part['video']), 'A figure or its source changed after extraction')
        require(row['caption'] in report, 'The reviewed figure caption is absent from the final Markdown')
    for edit in review.get('edits', []):
        validate_times([edit], runtime.part(edit['part'])['duration_seconds'])
        require(all(edit.get(key) for key in ['id', 'original', 'processed', 'reason', 'source']), 'An edit lacks its original, processed text or source')
        source = inside(runtime.bundle, runtime.bundle / edit['source'])
        data = read_json(source)
        if edit.get('segment_ids'):
            segments = {row['id']: row for row in data['segments']}
            require(set(edit['segment_ids']) <= set(segments), 'An edit refers to unknown source segment IDs')
            original = ''.join(segments[key]['text'] for key in edit['segment_ids'])
        else:
            original = '\n'.join(text_values(data))
        normalize = lambda text: re.sub(r'\s+', '', text)
        require(normalize(edit['original']) in normalize(original), 'An edit original cannot be found in its cited raw evidence')
        if edit.get('material', True):
            require(edit['original'] in report and edit['processed'] in report and edit['id'] in report, 'Material edits need original and processed wording plus an ID in the final report')
    return review


def audit(runtime: Runtime) -> dict[str, Any]:
    """Inspect actual media proofs, timelines, editorial record and exports."""
    report_path, ast = report_ast(runtime)
    report = report_path.read_text(encoding='utf-8')
    images = check_resources(runtime, report_path, ast)
    selected = runtime.meta.get('selected_parts', [])
    require(bool(selected), 'No acquired source parts were selected')
    facts = []
    for number in selected:
        part = runtime.part(number)
        video = runtime.bundle / part['video']
        require(sha256(video) == part['sha256'], 'The original acquired video bytes changed')
        actual = json.loads(runtime.command(['ffprobe', '-v', 'error', '-show_format', '-of', 'json', str(video)]))
        require(abs(float(actual['format']['duration']) - part['duration_seconds']) < 0.05, 'Recorded duration differs from the current actual media')
        proof = read_json(runtime.bundle / f'evidence/p{number:03}-decode.json')
        require(proof['source_sha256'] == sha256(video) and proof['exit_code'] == 0 and proof['decoded_to_eof'], 'Full source decoding was not proven')
        require(bool(part.get('timeline')), 'A selected part has no synchronized evidence timeline')
        timeline = read_json(runtime.bundle / part['timeline'])
        require(timeline['source_sha256'] == sha256(video), 'The timeline source changed; index again')
        require(timeline['anchor_sha256'] == (sha256(runtime.bundle / part['anchor_track']) if part.get('anchor_track') else None), 'The anchor track changed; index again')
        require(timeline['asr_sha256'] == (sha256(runtime.bundle / part['asr']) if part.get('asr') else None), 'ASR changed after indexing; index again')
        require(timeline['frames_sha256'] == (sha256(runtime.bundle / part['frames']) if part.get('frames') else None), 'Frame inventory changed after indexing; index again')
        validate_times(timeline['rows'], part['duration_seconds'])
        asr_rows = read_json(runtime.bundle / part['asr'])['segments'] if part.get('asr') else []
        if part.get('asr'):
            validate_times(asr_rows, part['duration_seconds'], allow_empty=True)
            asr_data = read_json(runtime.bundle / part['asr'])
            require(asr_data['source_sha256'] == sha256(video) and asr_data['audio_stream'] == part['audio_stream'], 'ASR uses a different video or audio stream')
            require(asr_data['audio_sha256'] == sha256(runtime.work / part['audio']), 'Audio changed after ASR; transcribe again')
        identifiers = {row['id'] for row in asr_rows}
        for row in timeline['rows']:
            require(set(row['asr_segment_ids']) <= identifiers, 'Timeline refers to an absent ASR segment')
            if row['nearest_frame']:
                require((runtime.bundle / row['nearest_frame']).is_file(), 'Timeline refers to a missing frame')
        for track in part.get('tracks', []):
            validate_times(read_json(runtime.bundle / track['path'])['segments'], part['duration_seconds'], allow_empty=True)
        frame_rows = read_json(runtime.bundle / part['frames'])['frames'] if part.get('frames') else []
        for row in frame_rows:
            require(0 <= row['time_seconds'] < part['duration_seconds'], 'A sampled frame time is out of range')
            require(sha256(runtime.bundle / row['frame']) == row['frame_sha256'], 'A sampled frame changed')
        facts.append({'part': number, 'duration_seconds': part['duration_seconds'], 'timeline_rows': len(timeline['rows']), 'asr_segments': len(asr_rows), 'sampled_frames': len(frame_rows), 'subtitle_status': part['subtitle_status']})
    review = editorial_review(runtime, images, report)
    exported = runtime.meta.get('export', {})
    require(exported.get('markdown_sha256') == sha256(report_path), 'The report changed after export; export again')
    require(exported.get('css_sha256') == sha256(runtime.bundle / 'assets/report.css'), 'The stylesheet changed after export')
    docx, html = runtime.bundle / 'docx/report.docx', runtime.bundle / 'report.html'
    require(exported.get('docx_sha256') == sha256(docx) and exported.get('html_sha256') == sha256(html), 'An exported document changed')
    with zipfile.ZipFile(docx) as document:
        require(document.testzip() is None, 'DOCX ZIP integrity failed')
        xml = ElementTree.fromstring(document.read('word/document.xml'))
        pictures = xml.findall('.//{http://schemas.openxmlformats.org/drawingml/2006/main}blip')
        require(len(pictures) == len(images), 'DOCX image count differs from Markdown')
    require(len(re.findall(r'<img[^>]+src="data:image/', html.read_text(encoding='utf-8'))) == len(images), 'HTML did not embed every report image')
    for path in runtime.bundle.rglob('*'):
        require(not path.is_symlink(), 'Do not deliver bundle symlinks')
        require(path.suffix not in {'.env', '.part'} and path.name != 'credentials.env', 'The bundle contains credentials or unfinished downloads')
    return {'parts': facts, 'report_images': len(images), 'editorial_record_present': True, 'material_edits': sum(row.get('material', True) for row in review.get('edits', [])), 'limitations': review.get('limitations', []), 'verification_scope': 'Mechanical integrity and review traceability. Agent attestation does not prove transcription accuracy, factual truth or semantic completeness.'}


def verify(runtime: Runtime) -> None:
    """Seal a bundle only after checking actual outputs; never hash a moving log."""
    manifest = runtime.bundle / 'manifest.json'
    manifest.unlink(missing_ok=True)
    try:
        result = audit(runtime)
    except Exception as exc:
        runtime.meta['status'] = 'incomplete'
        runtime.save_meta()
        write_json(runtime.bundle / 'evidence/validation.json', {'status': 'failed', 'checked_at': utc_now(), 'error': str(exc)})
        runtime.event('verify', 'failed', error_type=type(exc).__name__)
        raise
    runtime.event('verify', 'succeeded')
    runtime.meta['status'] = 'verified'
    runtime.save_meta()
    write_json(runtime.bundle / 'evidence/validation.json', {'status': 'passed', 'checked_at': utc_now(), **result})
    records = [{'file': str(path.relative_to(runtime.bundle)), 'bytes': path.stat().st_size, 'sha256': sha256(path)} for path in sorted(runtime.bundle.rglob('*')) if path.is_file() and path != manifest]
    write_json(manifest, {'algorithm': 'sha256', 'files': records})
    print(CLIStyle.color(json.dumps({'status': 'verified', 'files': len(records), 'bundle': str(runtime.bundle)}, indent=2)))
