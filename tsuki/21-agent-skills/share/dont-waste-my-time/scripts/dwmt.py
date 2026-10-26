#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Initialize private jobs and dispatch all media work through Compose."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from dwmt.common import CLIStyle, ColoredArgumentParser, inside, read_json, redact, utc_now, write_json


def skill_root() -> Path:
    """Locate the complete trusted skill, independent of current directory."""
    return Path(__file__).resolve().parents[1]


def tmp_path(path: Path) -> Path:
    """Keep runtime state outside the installation and within /tmp."""
    return inside(Path('/tmp'), path.expanduser())


def load_job(path: str) -> tuple[Path, dict[str, Any]]:
    """Validate a private, current-user job root before dispatch."""
    root = tmp_path(Path(path))
    if root.stat().st_uid != os.getuid() or root.stat().st_mode & 0o077:
        raise ValueError('The job directory must be current-user owned and mode 0700')
    job = read_json(root / 'job.json')
    if job.get('schema_version') != 1 or not re.fullmatch(r'[a-f0-9]{16}', job.get('id', '')):
        raise ValueError('Invalid job identity')
    if Path(job['root']) != root:
        raise ValueError('The job root differs from its recorded location')
    return root, job


def private_copy(source: Path, target: Path) -> None:
    """Copy one explicit user file without shell evaluation."""
    if not source.is_file():
        raise FileNotFoundError(f'Missing input file: {source.name}')
    shutil.copyfile(source, target)
    target.chmod(0o600)


def initialize(args: argparse.Namespace) -> dict[str, Any]:
    """Create a private cookie template and a separate deliverable tree."""
    source = {'kind': 'local'}
    if args.url:
        parsed = urlparse(args.url)
        if parsed.scheme != 'https' or parsed.hostname not in {'www.bilibili.com', 'bilibili.com', 'm.bilibili.com'} or parsed.username:
            raise ValueError('This version accepts local videos or HTTPS Bilibili video URLs')
        if not re.search(r'BV[0-9A-Za-z]{10}', parsed.path):
            raise ValueError('A Bilibili BV video URL is required')
        if any(key not in {'p', 't', 'spm_id_from'} for key in re.findall(r'(?:^|&)([^=]+)=', parsed.query)):
            raise ValueError('Remove tracking or credential query parameters from the video URL')
        source = {'kind': 'bilibili', 'url': args.url}
    root = Path(tempfile.mkdtemp(prefix='dont-waste-my-time.', dir='/tmp'))
    root.chmod(0o700)
    for name in ['input', 'work', 'work/audio', 'work/bundle/video', 'work/bundle/markdown', 'work/bundle/docx', 'work/bundle/assets', 'work/bundle/transcripts', 'work/bundle/evidence', 'work/bundle/logs']:
        (root / name).mkdir(parents=True, exist_ok=True)
    credentials = root / 'credentials.env'
    shutil.copyfile(skill_root() / 'assets/credentials.env.example', credentials)
    credentials.chmod(0o600)
    if args.cookie_file:
        private_copy(Path(args.cookie_file).expanduser(), credentials)
    if args.video:
        video = Path(args.video).expanduser().resolve(strict=True)
        extension = video.suffix.lower()
        if extension not in {'.mp4', '.mkv', '.mov', '.webm', '.flv', '.avi', '.m4v'}:
            raise ValueError('Unsupported local video extension')
        private_copy(video, root / 'input' / f'source{extension}')
        source['input_file'] = f'source{extension}'
        source['original_name'] = video.name
    if args.reference_docx:
        private_copy(Path(args.reference_docx).expanduser(), root / 'input/reference.docx')
    cache = tmp_path(Path(args.cache)) if args.cache else Path(f'/tmp/dwmt-model-cache-{os.getuid()}')
    if cache == Path('/tmp').resolve():
        raise ValueError('Use a dedicated model cache, not the entire /tmp directory')
    cache.mkdir(parents=True, exist_ok=True, mode=0o700)
    if cache.stat().st_uid != os.getuid():
        raise ValueError('The model cache must be owned by the current user')
    job_id = os.urandom(8).hex()
    job = {'schema_version': 1, 'id': job_id, 'root': str(root), 'cache': str(cache), 'source': source, 'created_at': utc_now()}
    write_json(root / 'job.json', job)
    meta = {'schema_version': 1, 'job_id': job_id, 'source': source, 'created_at': utc_now(), 'parts': [], 'stages': {}, 'status': 'initialized', 'limitations': []}
    write_json(root / 'work/bundle/meta.json', meta)
    shutil.copyfile(skill_root() / 'assets/report.css', root / 'work/bundle/assets/report.css')
    return {'job': str(root), 'credentials_file': str(credentials), 'credentials_required': source['kind'] == 'bilibili' and not args.cookie_file, 'bundle': str(root / 'work/bundle'), 'next': 'Fill either BILIBILI_COOKIE or BILIBILI_SESSDATA as explained in the private template, then confirm completion; never paste credentials into chat.' if source['kind'] == 'bilibili' and not args.cookie_file else 'Run prepare, then inspect or local fetch.'}


def image_tag() -> str:
    """Bind the tools tag to the actual shipped recipe and implementation."""
    digest = hashlib.sha256()
    root = skill_root()
    paths = [root / '.dockerignore', *sorted((root / 'docker').rglob('*')), *sorted((root / 'scripts').rglob('*')), *sorted((root / 'assets').rglob('*'))]
    for path in paths:
        if path.is_file() and '__pycache__' not in path.parts and path.suffix != '.pyc':
            digest.update(str(path.relative_to(root)).encode())
            digest.update(path.read_bytes())
    return f'dont-waste-my-time:tools-{digest.hexdigest()[:16]}'


def environment(root: Path, job: dict[str, Any], immutable: bool = True) -> dict[str, str]:
    """Pass paths and identity to Compose, never cookie values."""
    meta = read_json(root / 'work/bundle/meta.json')
    image = meta.get('runtime', {}).get('image_id') if immutable else None
    return {**os.environ, 'DWMT_IMAGE': image or image_tag(), 'DWMT_UID': str(os.getuid()), 'DWMT_GID': str(os.getgid()), 'DWMT_JOB_ID': job['id'], 'DWMT_WORK_DIR': str(root / 'work'), 'DWMT_INPUT_DIR': str(root / 'input'), 'DWMT_CACHE_DIR': str(tmp_path(Path(job['cache']))), 'DWMT_CREDENTIAL_FILE': str(root / 'credentials.env')}


def compose_command(root: Path, job: dict[str, Any]) -> list[str]:
    """Select only the shipped Compose project and its exact job identity."""
    return ['docker', 'compose', '--ansi', 'never', '--env-file', '/dev/null', '--project-name', f'dwmt-{job["id"]}', '--project-directory', str(skill_root()), '-f', str(skill_root() / 'compose.yaml')]


def execute(arguments: list[str], root: Path, env: dict[str, str], log_name: str, timeout: int | None = None) -> subprocess.CompletedProcess[str]:
    """Persist bounded, sanitized host-dispatch output under /tmp."""
    log = root / 'work' / f'dispatch-{log_name}' if log_name in {'verify.log', 'status.log', 'endpoint.log'} else root / 'work/bundle/logs' / log_name
    if timeout is not None:
        result = subprocess.run(arguments, env=env, capture_output=True, text=True, timeout=timeout)
    else:
        with log.open('a', encoding='utf-8') as handle:
            handle.write(f'\n[{utc_now()}] started\n')
            with subprocess.Popen(arguments, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True) as process:
                captured = []
                for line in process.stdout:
                    cleaned = redact(line)
                    captured.append(cleaned)
                    handle.write(cleaned)
                    handle.flush()
                    print(CLIStyle.color(cleaned), end='', flush=True)
                result = subprocess.CompletedProcess(arguments, process.wait(), ''.join(captured), '')
    with log.open('a', encoding='utf-8') as handle:
        handle.write(f'\n[{utc_now()}] exit={result.returncode}\n')
        if timeout is not None:
            handle.write(redact(result.stdout + result.stderr))
    if result.stdout and timeout is not None:
        print(CLIStyle.color(redact(result.stdout[-12000:])) , end='', flush=True)
    if result.returncode:
        raise RuntimeError(f'Command failed (exit {result.returncode}); inspect {log}')
    return result


def docker_endpoint(root: Path, env: dict[str, str], log_name: str) -> str:
    """Check the actual client binding before every bind-mount operation."""
    if env.get('DOCKER_HOST') and not env.get('DOCKER_CONTEXT'):
        endpoint = env['DOCKER_HOST']
    else:
        context = [env['DOCKER_CONTEXT']] if env.get('DOCKER_CONTEXT') else []
        observed = execute(['docker', 'context', 'inspect', *context, '--format', '{{.Endpoints.docker.Host}}'], root, env, log_name, 30)
        endpoint = observed.stdout.strip()
    if not endpoint.startswith('unix://'):
        raise ValueError('This launcher supports a local Unix Docker endpoint; do not mount local job paths through a remote context')
    return endpoint


def prepare(root: Path, job: dict[str, Any]) -> dict[str, Any]:
    """Reuse a healthy image; build missing tools and perform real smoke probes."""
    if not shutil.which('docker'):
        raise RuntimeError('Docker is missing; host installation needs a separately authorized method')
    meta_path = root / 'work/bundle/meta.json'
    meta = read_json(meta_path)
    meta['status'] = 'working'
    write_json(meta_path, meta)
    (root / 'work/bundle/manifest.json').unlink(missing_ok=True)
    env = environment(root, job, immutable=False)
    tag = env['DWMT_IMAGE']
    endpoint = docker_endpoint(root, env, 'prepare.log')
    execute(['docker', 'version', '--format', '{{.Server.Version}}'], root, env, 'prepare.log', 30)
    base = compose_command(root, job)
    execute(base + ['config', '--quiet'], root, env, 'prepare.log', 30)
    inspection = subprocess.run(['docker', 'image', 'inspect', tag, '--format', '{{.Id}}'], env=env, capture_output=True, text=True, timeout=30)
    if inspection.returncode:
        execute(base + ['build', 'processor'], root, env, 'build.log')
    result = execute(['docker', 'image', 'inspect', tag, '--format', '{{.Id}}'], root, env, 'prepare.log', 30)
    image_id = result.stdout.strip()
    meta = read_json(meta_path)
    if tag != image_tag():
        raise RuntimeError('The skill changed during the build; run prepare again for the current recipe')
    meta['status'] = 'working'
    (root / 'work/bundle/manifest.json').unlink(missing_ok=True)
    meta['runtime'] = {'image_tag': tag, 'image_id': image_id, 'docker_endpoint': endpoint, 'prepared_at': utc_now()}
    write_json(meta_path, meta)
    execute(base + ['run', '--rm', '--no-deps', 'processor', 'doctor'], root, environment(root, job), 'prepare.log')
    return {'job': str(root), 'image_id': image_id, 'tools': 'verified', 'model': 'prepare only if selected for ASR'}


def check_credentials(root: Path) -> None:
    """Check file ownership and nonempty data fields without showing them."""
    path = root / 'credentials.env'
    info = path.lstat()
    if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise ValueError('The credentials file must be a regular current-user file with mode 0600')
    values = []
    for line in path.read_text(encoding='utf-8').splitlines():
        if line.startswith(('BILIBILI_COOKIE=', 'BILIBILI_SESSDATA=')):
            values.append(line.split('=', 1)[1].strip().strip('\"\x27'))
    if not any(values):
        raise ValueError(f'Credentials required. Fill {path}, then confirm; do not send cookies in chat')


def dispatch(root: Path, job: dict[str, Any], arguments: list[str]) -> dict[str, Any]:
    """Choose the service by stage; callers cannot select a shell entrypoint."""
    if arguments and arguments[0] == '--':
        arguments = arguments[1:]
    allowed = {'doctor', 'inspect', 'fetch', 'models', 'probe', 'media', 'asr', 'frames', 'frame', 'index', 'export', 'verify', 'status'}
    if not arguments or arguments[0] not in allowed:
        raise ValueError(f'Choose a container stage: {", ".join(sorted(allowed))}')
    stage = arguments[0]
    runtime = read_json(root / 'work/bundle/meta.json').get('runtime', {})
    if runtime.get('image_tag') != image_tag():
        raise ValueError('Tools are unprepared or the recipe changed; run prepare')
    service = 'processor'
    if stage in {'inspect', 'fetch'} and job['source']['kind'] == 'bilibili':
        check_credentials(root)
        service = 'fetch'
    if stage == 'models':
        service = 'models'
    env = environment(root, job)
    endpoint = docker_endpoint(root, env, 'endpoint.log')
    if endpoint != runtime.get('docker_endpoint'):
        raise ValueError('The Docker endpoint changed; run prepare for the selected local daemon')
    meta_path = root / 'work/bundle/meta.json'
    meta = read_json(meta_path)
    if stage != 'status' and meta.get('status') == 'verified':
        meta['status'] = 'working'
        write_json(meta_path, meta)
        (root / 'work/bundle/manifest.json').unlink(missing_ok=True)
    command = compose_command(root, job) + ['run', '--rm', '--no-deps', '--label', f'io.dwmt.stage={stage}', service, *arguments]
    execute(command, root, env, f'{stage}.log')
    return {'stage': stage, 'bundle': str(root / 'work/bundle')}


def status(root: Path, job: dict[str, Any]) -> dict[str, Any]:
    """Distinguish recorded state from observed live Docker containers."""
    states = read_json(root / 'work/state.json') if (root / 'work/state.json').exists() else {}
    observed: dict[str, Any] = {'verified': False}
    if shutil.which('docker'):
        result = subprocess.run(['docker', 'ps', '--filter', f'label=io.dwmt.job={job["id"]}', '--format', '{{json .}}'], capture_output=True, text=True, timeout=15)
        if result.returncode == 0:
            observed = {'verified': True, 'containers': [json.loads(line) for line in result.stdout.splitlines()]}
    return {'job': str(root), 'recorded_stages': states, 'live_docker_observation': observed, 'bundle': str(root / 'work/bundle')}


def parser() -> argparse.ArgumentParser:
    """Expose initialization and fixed container operations."""
    result = ColoredArgumentParser(description=CLIStyle.color('Private video-to-document jobs through Docker Compose', 'TITLE'), epilog=CLIStyle.color('Examples:\n  python scripts/dwmt.py init --url https://www.bilibili.com/video/BV1dpn86hEHZ/\n  python scripts/dwmt.py prepare --job /tmp/dont-waste-my-time.JOB\n  python scripts/dwmt.py run --job /tmp/dont-waste-my-time.JOB -- media --part 1', 'SUB_TITLE'), formatter_class=argparse.RawDescriptionHelpFormatter)
    result.add_argument('--log', action='store_true', help=CLIStyle.color('Show a sanitized error type', 'CONTENT'))
    sub = result.add_subparsers(dest='command', required=True, parser_class=ColoredArgumentParser)
    init = sub.add_parser('init', help=CLIStyle.color('Create a private /tmp job and cookie template', 'CONTENT'))
    inputs = init.add_mutually_exclusive_group(required=True)
    inputs.add_argument('--url', help=CLIStyle.color('HTTPS Bilibili BV video URL', 'CONTENT'))
    inputs.add_argument('--video', help=CLIStyle.color('Explicit local video path', 'CONTENT'))
    init.add_argument('--cookie-file', help=CLIStyle.color('Explicit existing .env file to privately copy', 'CONTENT'))
    init.add_argument('--cache', help=CLIStyle.color('Model cache directory under /tmp', 'CONTENT'))
    init.add_argument('--reference-docx', help=CLIStyle.color('Optional user-provided Pandoc reference DOCX', 'CONTENT'))
    for name in ['prepare', 'run', 'status']:
        command = sub.add_parser(name, help=CLIStyle.color(f'{name.capitalize()} an initialized job', 'CONTENT'))
        command.add_argument('--job', required=True, help=CLIStyle.color('Private /tmp job root', 'CONTENT'))
        if name == 'run':
            command.add_argument('arguments', nargs=argparse.REMAINDER, help=CLIStyle.color('Container stage and arguments after --', 'CONTENT'))
    return result


def main() -> int:
    """Run only host filesystem initialization and Docker orchestration."""
    os.umask(0o077)
    args = parser().parse_args()
    if args.command == 'init':
        value = initialize(args)
    else:
        root, job = load_job(args.job)
        if args.command == 'prepare':
            value = prepare(root, job)
        elif args.command == 'run':
            value = dispatch(root, job, args.arguments)
        else:
            value = status(root, job)
    print(CLIStyle.color(json.dumps(value, ensure_ascii=False, indent=2)))
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except FileNotFoundError as exc:
        detail = exc.filename or redact(str(exc))
        print(CLIStyle.color(f'Error: missing file or executable: {detail}', 'ERROR'), file=sys.stderr)
        sys.exit(1)
    except Exception as exc:
        label = f'Error [{type(exc).__name__}]' if '--log' in sys.argv else 'Error'
        print(CLIStyle.color(f'{label}: {redact(str(exc))}', 'ERROR'), file=sys.stderr)
        sys.exit(1)
