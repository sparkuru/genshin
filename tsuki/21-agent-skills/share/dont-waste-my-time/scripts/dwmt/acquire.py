# -*- coding: utf-8 -*-
"""Acquire Bilibili or explicitly staged local video with subtitle inventory."""

from __future__ import annotations

import contextlib
import io
import re
import shutil
from pathlib import Path
from typing import Any
from urllib.parse import parse_qs, urlparse

from dwmt import bilibili_client
from dwmt.common import Runtime, read_json, redact, sha256, subtitles, utc_now, write_json


class SafeLog(io.TextIOBase):
    """Capture the trusted downloader's progress without signed URLs."""

    def __init__(self, path: Path) -> None:
        """Open an acquisition-only log."""
        self.handle = path.open('a', encoding='utf-8')

    def write(self, text: str) -> int:
        """Sanitize each progress write."""
        self.handle.write(redact(text).replace('\r', '\n'))
        self.handle.flush()
        return len(text)

    def close(self) -> None:
        """Close the retained log."""
        self.handle.close()
        super().close()


def client() -> bilibili_client.BilibiliClient:
    """Read data-only credentials only inside the acquisition service."""
    config = Path('/run/secrets/source.env')
    values = bilibili_client.parse_env_file(config)
    if not (values.get('BILIBILI_COOKIE') or values.get('BILIBILI_SESSDATA')):
        raise ValueError('Fill the private credentials.env before network acquisition')
    return bilibili_client.BilibiliClient(sessdata=bilibili_client.resolve_sessdata(None, config), cookie=bilibili_client.resolve_cookie(None, config), timeout=25, retries=2)


def player_tracks(connection: bilibili_client.BilibiliClient, bvid: str, cid: int) -> list[dict[str, Any]]:
    """Obtain subtitle availability without retaining player tokens."""
    params = connection._sign_params({'bvid': bvid, 'cid': cid})
    player = connection._request_json('https://api.bilibili.com/x/player/wbi/v2', params)['data']
    return player.get('subtitle', {}).get('subtitles', [])


def safe_tracks(tracks: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Keep subtitle identity and origin type, never temporary URLs."""
    return [{key: row.get(key) for key in ['id', 'lan', 'lan_doc', 'ai_type', 'ai_status']} | {'track_index': index} for index, row in enumerate(tracks)]


def inspect_source(runtime: Runtime) -> None:
    """Inspect all source parts; distinguish no captions from API failure."""
    source = runtime.meta['source']
    if source['kind'] != 'bilibili':
        raise ValueError('For local input run fetch, then inspect meta.json and FFprobe evidence')
    bvid = re.search(r'BV[0-9A-Za-z]{10}', source['url']).group()
    log = SafeLog(runtime.bundle / 'logs/acquisition.log')
    try:
        with contextlib.redirect_stdout(log):
            connection = client()
            try:
                data = connection._request_json(bilibili_client.VIDEO_DETAIL_API_URL, {'bvid': bvid}, retry_risk_control=False)['data']
            except bilibili_client.BilibiliRiskControlError:
                data = connection._fetch_video_page_data(bvid)
        pages = data.get('pages') or [{'page': 1, 'cid': data['cid'], 'part': data['title'], 'duration': data.get('duration')}]
        records = []
        for page in pages:
            record = {key: page.get(key) for key in ['page', 'cid', 'part', 'duration', 'dimension']}
            try:
                with contextlib.redirect_stdout(log):
                    tracks = player_tracks(connection, bvid, page['cid'])
                record['subtitles'] = {'status': 'available' if tracks else 'none', 'tracks': safe_tracks(tracks)}
            except Exception as exc:
                record['subtitles'] = {'status': 'error', 'error_type': type(exc).__name__, 'tracks': []}
            records.append(record)
        inventory = {'provider': 'bilibili', 'bvid': bvid, 'aid': data.get('aid'), 'title': data['title'], 'description': data.get('desc', ''), 'owner': {key: data.get('owner', {}).get(key) for key in ['name', 'mid']}, 'published_unix': data.get('pubdate'), 'inspected_at': utc_now(), 'pages': records}
        write_json(runtime.bundle / 'evidence/source-inventory.json', inventory)
        runtime.meta['inventory'] = inventory
        runtime.save_meta()
        runtime.event('inspect', 'succeeded', parts=len(records), subtitle_states=[row['subtitles']['status'] for row in records])
    except Exception as exc:
        runtime.event('inspect', 'failed', error_type=type(exc).__name__)
        raise RuntimeError(f'Bilibili inspection failed ({type(exc).__name__}); inspect acquisition.log, distinguish authentication, network and risk control') from None
    finally:
        log.close()


def selected_parts(runtime: Runtime, selection: str) -> list[int]:
    """Honor an explicit URL part, otherwise include all observed parts."""
    pages = runtime.meta['inventory']['pages']
    known = {int(row['page']) for row in pages}
    query = parse_qs(urlparse(runtime.meta['source'].get('url', '')).query)
    if selection == 'requested':
        selection = query.get('p', ['all'])[0]
    result = sorted(known) if selection == 'all' else [int(item) for item in selection.split(',')]
    if not result or len(set(result)) != len(result) or not set(result) <= known:
        raise ValueError('Part selection must contain distinct observed source part numbers')
    return result


def archive_tracks(runtime: Runtime, connection: bilibili_client.BilibiliClient, bvid: str, page: dict[str, Any]) -> list[dict[str, Any]]:
    """Preserve raw captions and separate normalized subtitle artifacts."""
    records = []
    tracks = player_tracks(connection, bvid, page['cid'])
    for index, track in enumerate(tracks):
        url = track['subtitle_url']
        url = 'https:' + url if url.startswith('//') else url
        parsed = urlparse(url)
        hostname = parsed.hostname or ''
        if parsed.scheme != 'https' or parsed.username or not any(hostname == domain or hostname.endswith('.' + domain) for domain in ['hdslb.com', 'bilibili.com']):
            raise ValueError('Unexpected platform subtitle destination')
        response = connection.session.get(url, timeout=30)
        response.raise_for_status()
        raw = response.json()
        base = runtime.bundle / f'transcripts/p{page["page"]:03}-platform-{index}'
        write_json(base.with_suffix('.raw.json'), raw)
        segments = [{'id': f'platform-p{page["page"]:03}-t{index}-s{number}', 'start': row['from'], 'end': row['to'], 'text': row['content']} for number, row in enumerate(raw['body'])]
        normalized = {'kind': 'platform', 'part': page['page'], 'track': safe_tracks([track])[0], 'segments': segments}
        write_json(base.with_suffix('.json'), normalized)
        subtitles(base, segments)
        records.append({'path': str(base.with_suffix('.json').relative_to(runtime.bundle)), **safe_tracks([track])[0], 'track_index': index})
    return records


def fetch_bilibili(runtime: Runtime, selection: str, quality: int, force: bool) -> None:
    """Download selected source parts without silently truncating a multipart video."""
    if 'inventory' not in runtime.meta:
        raise ValueError('Run inspect and review the source inventory before fetch')
    selected = selected_parts(runtime, selection)
    inventory = runtime.meta['inventory']
    connection = client()
    log = SafeLog(runtime.bundle / 'logs/acquisition.log')
    try:
        for number in selected:
            page = next(row for row in inventory['pages'] if row['page'] == number)
            destination = runtime.bundle / f'video/part-{number:03}.mp4'
            record = {'part': number, 'title': page['part'], 'video': str(destination.relative_to(runtime.bundle)), 'cid': page['cid'], 'requested_quality': quality, 'source_subtitles': page['subtitles']}

            def download_part() -> list[Path]:
                """Keep downloader range checkpoints until the source is complete."""
                with contextlib.redirect_stdout(log):
                    streams = connection.fetch_streams(inventory['bvid'], page['cid'], quality)
                    connection.download_streams(streams, destination, f'https://www.bilibili.com/video/{inventory["bvid"]}/', identity=f'{inventory["bvid"]}:{page["cid"]}:{quality}')
                return [destination]

            runtime.stage(f'fetch-p{number:03}', [], {'bvid': inventory['bvid'], 'part': number, 'cid': page['cid'], 'quality': quality}, download_part, force)
            try:
                with contextlib.redirect_stdout(log):
                    record['tracks'] = archive_tracks(runtime, connection, inventory['bvid'], page)
                record['subtitle_status'] = 'available' if record['tracks'] else 'none'
            except Exception as exc:
                record.update(tracks=[], subtitle_status='error', subtitle_error_type=type(exc).__name__)
                runtime.event(f'subtitles-p{number:03}', 'failed', error_type=type(exc).__name__)
            record['sha256'] = sha256(destination)
            previous = next((row for row in runtime.meta['parts'] if row['part'] == number), {})
            runtime.meta['parts'] = [row for row in runtime.meta['parts'] if row['part'] != number] + [{**previous, **record}]
            runtime.save_meta()
        runtime.meta['selected_parts'] = selected
        runtime.meta['unselected_parts'] = [row['page'] for row in inventory['pages'] if row['page'] not in selected]
        runtime.save_meta()
    except Exception as exc:
        raise RuntimeError(f'Bilibili acquisition failed ({type(exc).__name__}); retained range checkpoints and sanitized logs') from None
    finally:
        log.close()


def fetch_local(runtime: Runtime, force: bool) -> None:
    """Copy one staged video; embedded subtitle detection follows in media."""
    source = runtime.meta['source']
    incoming = Path('/inputs') / source['input_file']
    target = runtime.bundle / ('video/part-001' + incoming.suffix)

    def copy_video() -> list[Path]:
        """Retain the source bytes without remuxing or transcoding."""
        shutil.copyfile(incoming, target)
        return [target]

    runtime.stage('fetch-p001', [], {'input_sha256': sha256(incoming)}, copy_video, force)
    runtime.meta['parts'] = [{**next(iter(runtime.meta.get('parts', [])), {}), 'part': 1, 'title': source['original_name'], 'video': str(target.relative_to(runtime.bundle)), 'sha256': sha256(target), 'tracks': []}]
    runtime.meta['selected_parts'] = [1]
    runtime.meta['unselected_parts'] = []
    if Path('/inputs/reference.docx').is_file():
        target_reference = runtime.work / 'reference.docx'
        shutil.copyfile('/inputs/reference.docx', target_reference)
    runtime.save_meta()
