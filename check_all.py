"""Offline acceptance with real command receipts. Any skipped test is a failure."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import unittest
import zipfile
from measurement import file_hash
from schemas import read_json,validate,load_suite
from verify_report import verify

ROOT=Path(__file__).resolve().parent


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,default=ROOT/'.checks')
    p.add_argument('--evaluator',default='unspecified');p.add_argument('--relationship',default='unspecified')
    p.add_argument('--isolation',action='store_true');a=p.parse_args();out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
    receipts=[];summary={'schema':'arquia.acceptance/1','passed':False,'evaluator_declared':a.evaluator,'relationship_declared':a.relationship,'independence_verified':False}
    def run(name,args,expected=0,cwd=ROOT):
        if args and Path(args[0]).name in ('runner.py','community_runner.py'):
            args=[*args,'--evaluator',a.evaluator,'--relationship',a.relationship]
        start=time.perf_counter();command=[sys.executable,*args]
        try:
            r=subprocess.run(command,cwd=cwd,capture_output=True,timeout=60,env={**os.environ,'PYTHONDONTWRITEBYTECODE':'1'})
            stdout,stderr,code=r.stdout,r.stderr,r.returncode
        except subprocess.TimeoutExpired as exc:
            stdout,stderr,code=exc.stdout or b'',exc.stderr or b'',None
        (out/(name+'.stdout')).write_bytes(stdout);(out/(name+'.stderr')).write_bytes(stderr)
        receipt={'name':name,'command':command,'cwd':str(cwd),'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
                 'actual_exit_code':code,'expected_exit_code':expected,'seconds':time.perf_counter()-start,
                 'stdout_sha256':hashlib.sha256(stdout).hexdigest(),'stderr_sha256':hashlib.sha256(stderr).hexdigest()}
        (out/(name+'.receipt.json')).write_text(json.dumps(receipt,indent=2)+'\n');receipts.append(receipt)
        if code!=expected:raise AssertionError(f'{name}: exit {code}, expected {expected}; see receipt')
        return stdout
    try:
        lock=read_json(ROOT/'historical-lock.json')
        for name,digest in lock['files'].items():
            if file_hash(ROOT/name)!=digest:raise AssertionError('historical file changed: '+name)
        summary['historical_files_preserved']=len(lock['files'])
        run('package-integrity',['verify_package.py'])
        # Run through a strict test runner that rejects skipped/expected-failure suites.
        run('unit',['strict_unittest.py'])
        run('original-unit',['-m','unittest','discover','-v'],cwd=ROOT/'original')
        schema=read_json(ROOT/'schemas/result.schema.json')
        def report(name,args,expected,cases):
            data=json.loads(run(name,args,expected));validate(data,schema);verify(data,ROOT,cases)
            if any(r['error'] for r in data['results']):raise AssertionError(name+': execution error is not fault sensitivity')
            return data
        reference=report('historical',['runner.py'],0,ROOT/'cases.json')
        summary['historical_cases']=reference['total']
        from runner import MUTANTS
        summary['historical_controls']={}
        for name in MUTANTS:
            data=report('historical-'+name,['runner.py','--negative-control',name],1,ROOT/'cases.json')
            if data['passed']==data['total']:raise AssertionError('undetected '+name)
            summary['historical_controls'][name]={'passed':data['passed'],'total':data['total'],'exit':1}
        community=report('community',['community_runner.py'],0,ROOT/'suites/community-v1.json')
        summary['community_cases']=community['total']
        summary['community_controls']={}
        from community_runner import evaluate
        from conventional_candidate import Fault,FAULTS,Candidate
        suite=load_suite(ROOT/'suites/community-v1.json')
        # A control must have a non-error witness of its intended bad behavior.
        for fault in FAULTS:
            data=json.loads(run('community-'+fault,['community_runner.py','--fault',fault],1))
            validate(data,schema);verify(data,ROOT,ROOT/'suites/community-v1.json')
            witnesses=[r['id'] for r in data['results'] if not r['passed'] and r['error'] is None]
            if not witnesses:raise AssertionError('no non-error witness for '+fault)
            summary['community_controls'][fault]={'witnesses':witnesses,'inconclusive':sum(bool(r['error']) for r in data['results'])}
        report('independent-example',['community_runner.py','--example-jsonl'],0,ROOT/'suites/community-v1.json')
        from build_community_cases import build,generate
        if suite['cases']!=build():raise AssertionError('community declarations drift')
        if generate(42)!=generate(42):raise AssertionError('seed drift')
        generated=generate(42)
        if not all(r['passed'] for r in evaluate(Candidate,generated)):raise AssertionError('generated sequence failure')
        (out/'generated-seed-42.json').write_text(json.dumps({'schema':'arquia.community-cases/1','cases':generated},indent=2)+'\n')
        summary['generated_cases']=len(generated);summary['seed']=42
        second=report('community-repeat',['community_runner.py'],0,ROOT/'suites/community-v1.json')
        if community['results']!=second['results']:raise AssertionError('case-result reproducibility failed')
        run('human-report',['render_report.py',str(out/'community.stdout'),'--output',str(out/'community.md')])
        if 'Cannot conclude' not in (out/'community.md').read_text():raise AssertionError('missing report limits')
        one=json.loads(run('build-one',['build_release.py','--output',str(out/'build-one')]))
        two=json.loads(run('build-two',['build_release.py','--output',str(out/'build-two')]))
        if one['sha256']!=two['sha256']:raise AssertionError('package bytes not reproducible')
        extracted=out/'extracted';extracted.mkdir(exist_ok=True)
        with zipfile.ZipFile(one['archive']) as z:
            if any(Path(n).is_absolute() or '..' in Path(n).parts for n in z.namelist()):raise AssertionError('unsafe package path')
            z.extractall(extracted)
        packaged=extracted/('ARQUIA-EVAL-001-v'+(ROOT/'VERSION').read_text().strip())
        run('extracted-verify',['verify_package.py'],cwd=packaged)
        run('extracted-reference',['runner.py'],cwd=packaged)
        run('extracted-community',['community_runner.py'],cwd=packaged)
        rebuilt=json.loads(run('extracted-rebuild',['build_release.py','--output',str(out/'rebuilt')],cwd=packaged))
        if rebuilt['sha256']!=one['sha256']:raise AssertionError('archive cannot reproduce its own bytes')
        summary['source_archive_sha256']=one['sha256']
        if a.isolation:
            run('isolation',['strict_unittest.py','isolation_checks','resource_checks'])
            report('isolated-example',['community_runner.py','--candidate-dir','examples','--accept-external-code'],0,ROOT/'suites/community-v1.json')
            summary['external_isolation']='executed Linux checks'
        else:summary['external_isolation']='not requested; no foreign code executed'
        summary['passed']=True
    except Exception as exc:
        summary['error']=type(exc).__name__+': '+str(exc)
    summary['receipts']=receipts
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k!='receipts'},indent=2))
    return 0 if summary['passed'] else 1

if __name__=='__main__':sys.exit(main())
