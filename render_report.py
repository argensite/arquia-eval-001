"""Readable evidence without a global safety score; JSON remains authoritative."""
import argparse
import json
from pathlib import Path


def cell(value):
    return str(value).replace('|','\\|').replace('\n',' ')


def render(report):
    m=report['measurement']
    lines=[f"# Evaluation: {report['candidate']}",'',
        f"Contract matches: {report['passed']}/{report['total']}. Exit: {report['exit_code']}.",
        f"Observability: {report.get('observability','unspecified')}.",
        f"Evaluator: {m['evaluator']['declared_identity']}; declared relationship: {m['evaluator']['declared_relationship']}.",
        'Independence: not established by this instrument. Results are not safety certification.',
        f"Elapsed: {m['duration_seconds']:.6f} seconds (measured wall time; not a general cost estimate).",'',
        '| Case | Contract | Violations | Actual effects / unauthorized | Evidence |',
        '| --- | --- | --- | --- | --- |']
    for r in report['results']:
        c=r.get('consequences',{})
        lines.append(f"| {cell(r['id'])} | {'matches' if r['passed'] else 'FAIL'} | {len(r['violations'])} | {c.get('observed_effects','unknown')} / {c.get('unauthorized_effects','unknown')} | {cell(r.get('evidence_sufficient','candidate snapshots only'))} |")
    for r in report['results']:
        lines += ['',f"## {r['id']}",'',
            'Property: '+r.get('property',r['id']),
            'Acceptable behavior: '+r.get('hypothesis','Match the historical expectations and temporal invariant.'),
            'Expected: `'+json.dumps(r.get('expected',{}),ensure_ascii=False,sort_keys=True)+'`.',
            'Observed: `'+json.dumps(r['actual'],ensure_ascii=False,sort_keys=True)+'`.',
            'Violation: '+('yes' if r['violations'] or r['mismatches'] else 'none detected')+'.',
            'Error / inconclusive reason: '+str(r['error'])+'.',
            'Consequences: '+json.dumps(r.get('consequences',{'actual_effects':'not independently observed'}),sort_keys=True)+'.',
            'Evidence: '+r.get('evidence_sufficient','Candidate snapshots; no independent effect boundary')+'.',
            'Reproduce: '+r.get('reproduce','Use the recorded command and exact vector/instrument hashes')+'.',
            'Cannot conclude: production safety, absence of damage, complete adversarial coverage, or validity of ARQUIA/0-1-2-3.']
    lines += ['', '## Reproduction identity','', '`'+json.dumps(m['command'],ensure_ascii=False)+'`',
        'Git: `'+json.dumps(m['repository'],ensure_ascii=False,sort_keys=True)+'`',
        'Payload SHA-256: `'+report['report_sha256']+'` (byte identity, not authorship).',
        'Keep the complete JSON report, source files, stdout/stderr and process exit receipt.','']
    return '\n'.join(lines)


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('report',type=Path);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    a.output.write_text(render(json.loads(a.report.read_text(encoding='utf-8'))),encoding='utf-8')
if __name__=='__main__':main()
