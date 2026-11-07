"""Verify a measurement against local bytes without executing a candidate."""
import argparse
import json
from pathlib import Path
import sys
from measurement import canonical, file_hash, sha
from verify_package import safe_file


def verify(report, root, cases=None):
    from schemas import validate, read_json
    validate(report, read_json(Path(__file__).resolve().parent/'schemas/result.schema.json'))
    body = dict(report)
    expected = body.pop('report_sha256')
    if sha(canonical(body)) != expected:
        raise ValueError('report payload digest mismatch')
    m = report['measurement']
    if m['schema'] != 'arquia.measurement/1' or report['report_schema'] != 'arquia.result/1':
        raise ValueError('unknown report schema')
    if sha(canonical(m['configuration'])) != m['configuration_sha256']:
        raise ValueError('configuration digest mismatch')
    required = {'runner.py', 'verify_package.py', 'verify_report.py', 'engine.py', 'measurement.py', 'VERSION'}
    if not required <= m['files'].keys() or m['changed_during_run']:
        raise ValueError('missing or changed measurement instruments')
    for name, digest in {**m['files_after'], **m['files']}.items():
        if file_hash(safe_file(root, name)) != digest:
            raise ValueError('measurement file mismatch: ' + name)
    if cases is not None and file_hash(cases) != m['configuration']['cases_sha256']:
        raise ValueError('case digest mismatch')
    if report['total'] != len(report['results']) or report['passed'] != sum(r['passed'] for r in report['results']):
        raise ValueError('inconsistent result counts')
    if report['exit_code'] != (0 if report['passed']==report['total'] and report['total']>0 else 1):
        raise ValueError('exit code does not match cases')
    if m['exit_code'] != report['exit_code']:
        raise ValueError('inconsistent exit code')
    return {'verified': 'payload and supplied local bytes', 'authenticity': 'not_established',
            'runtime_dependencies': 'recorded; not independently verified',
            'external_cases': 'verified' if cases else 'supply --cases to verify input bytes'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('report', type=Path)
    p.add_argument('--root', type=Path, default=Path(__file__).resolve().parent)
    p.add_argument('--cases', type=Path)
    args = p.parse_args()
    try:
        print(json.dumps(verify(json.loads(args.report.read_text(encoding='utf-8-sig')), args.root, args.cases), indent=2))
        return 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print('Invalid measurement: ' + str(exc), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
