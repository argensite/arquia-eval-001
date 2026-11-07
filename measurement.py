"""Measurement identity, not a signature or proof of evaluator independence."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
SCHEMA = 'arquia.measurement/1'


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('utf-8')


def sha(value):
    return hashlib.sha256(value).hexdigest()


def file_hash(path):
    return sha(Path(path).read_bytes())


def git_state():
    def git(*args):
        p = subprocess.run(['git', '-C', str(ROOT), *args], capture_output=True, text=True, timeout=5)
        if p.returncode:
            raise ValueError('git metadata unavailable')
        return p.stdout.strip()
    try:
        if Path(git('rev-parse', '--show-toplevel')).resolve() != ROOT:
            raise ValueError('not this repository')
        status = git('status', '--porcelain=v1', '--untracked-files=all')
        return {'commit': git('rev-parse', 'HEAD'), 'dirty': bool(status), 'status': status.splitlines()}
    except (OSError, ValueError, subprocess.TimeoutExpired):
        marker = ROOT / 'SOURCE_IDENTITY.json'
        exported = json.loads(marker.read_text()) if marker.is_file() else {}
        return {'commit': exported.get('commit'), 'dirty': None, 'status': [],
                'origin': 'archive metadata declaration' if exported else 'unavailable'}


def source_files(extra=()):
    paths = {ROOT / n for n in ('runner.py', 'verify_package.py', 'verify_report.py', 'engine.py',
                                'measurement.py', 'VERSION', 'CHECKSUMS.sha256', 'SOURCE_IDENTITY.json')}
    paths.update(Path(p).resolve() for p in extra)
    for module in list(sys.modules.values()):
        name = getattr(module, '__file__', None)
        if name:
            p = Path(name).resolve()
            if p.is_file() and p.is_relative_to(ROOT):
                paths.add(p)
    return {p.relative_to(ROOT).as_posix(): file_hash(p) for p in sorted(paths)
            if p.is_file() and p.is_relative_to(ROOT)}


def runtime_files():
    result = {}
    for name, module in sorted(list(sys.modules.items())):
        path = getattr(module, '__file__', None)
        if not path:
            continue
        p = Path(path).resolve()
        if p.is_file() and not p.is_relative_to(ROOT):
            result[name] = {'file': str(p), 'sha256': file_hash(p)}
    return result


def begin(argv, candidate, cases_path, evaluator, relationship, extra=()):
    config = {'argv': list(argv), 'candidate': candidate, 'evaluator': evaluator,
              'relationship': relationship, 'cases_sha256': file_hash(cases_path)}
    return {'schema': SCHEMA, 'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
            '_start': time.perf_counter(), 'repository': git_state(), 'configuration': config,
            'configuration_sha256': sha(canonical(config)), 'files': source_files(extra),
            'evaluator': {'declared_identity': evaluator, 'declared_relationship': relationship,
                          'independence': 'not_established', 'verified_independence_evidence': []},
            'environment': {'os': platform.system(), 'release': platform.release(),
                            'architecture': platform.machine(), 'python': platform.python_version(),
                            'implementation': platform.python_implementation(), 'executable': sys.executable,
                            'executable_sha256': file_hash(sys.executable),
                            'selected_variables': {k: os.environ.get(k) for k in ('TZ', 'PYTHONHASHSEED')}},
            'command': [sys.executable, *argv], 'runtime_modules': runtime_files()}


def finish(report, measurement, exit_code):
    measurement['duration_seconds'] = time.perf_counter() - measurement.pop('_start')
    measurement['finished_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
    measurement['exit_code'] = exit_code
    measurement['files_after'] = source_files()
    measurement['changed_during_run'] = [p for p, h in measurement['files'].items()
                                         if not (ROOT / p).is_file() or file_hash(ROOT / p) != h]
    # Add lazily imported local and runtime dependencies without dropping initial identity.
    measurement['runtime_modules_after'] = runtime_files()
    report['measurement'] = measurement
    report['report_schema'] = 'arquia.result/1'
    report['report_sha256'] = sha(canonical(report))
    return report
