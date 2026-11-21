"""Offline acceptance with real command receipts. Any skipped test is a failure."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import subprocess
import sys
import tempfile
import time
import zipfile
from measurement import file_hash
from schemas import read_json,validate,load_suite
from verify_report import verify

ROOT=Path(__file__).resolve().parent
RECEIPT_CASE = "C29-transient-receipt-renewal"
CACHE_CASE = "REV-TURN-CACHE-NEGATIVE-CONTROL"


def check_receipt_renewal(report):
    if (report["candidate"] != "engine:ReceiptRenewal" or report.get("exit_code", 1) != 1
            or report["total"] != 29 or len(report["results"]) != 29 or report["passed"] != 14
            or any(result["error"] is not None for result in report["results"])):
        raise ValueError("receipt-renewal did not produce a complete, error-free negative report")
    witness, = (result for result in report["results"] if result["id"] == RECEIPT_CASE)
    expected = {"step": 4, "property": "P1/P2-passive-event", "field": "active_grants",
                "before": [], "after": ["g1"]}
    if (witness["passed"] is not False or witness["mismatches"] != {}
            or witness["violations"] != [expected]
            or witness["trace"][4]["event"]["op"] != "receipt"):
        raise ValueError(f"{RECEIPT_CASE}: missing transient grant restoration at receipt")
    return {"case": RECEIPT_CASE, **expected}


def check_stale_cache(report):
    if (report["mutation"] != "cache-per-turn" or report["exit_code"] != 1
            or report["total"] != 3 or len(report["results"]) != 3
            or any(result["error"] is not None for result in report["results"])):
        raise ValueError("cache-per-turn did not produce a complete, error-free negative report")
    witness, = (result for result in report["results"] if result["id"] == CACHE_CASE)
    if (witness["passed"] is not False
            or not any(v["property"] == "stale_turn_cache" for v in witness["violations"])):
        raise ValueError(f"{CACHE_CASE}: missing stale_turn_cache violation")
    return {"case": CACHE_CASE, "property": "stale_turn_cache"}


def check_archive(archive, run, summary):
    archive = archive.resolve()
    digest = file_hash(archive)
    prefix = archive.stem
    with tempfile.TemporaryDirectory(prefix="arquia-release-") as directory:
        extracted = Path(directory)
        with zipfile.ZipFile(archive) as source:
            names = source.namelist()
            if (len(names) != len(set(names)) or not names
                    or any("\\" in name or ":" in name or ".." in PurePosixPath(name).parts
                           or not name.startswith(prefix + "/") for name in names)):
                raise ValueError("invalid release archive paths")
            source.extractall(extracted)
        packaged = extracted / prefix
        run("extracted-verify", ["verify_package.py"], cwd=packaged)
        version = (packaged / "VERSION").read_text(encoding="utf-8").strip()
        if archive.name != f"ARQUIA-EVAL-001-v{version}.zip":
            raise ValueError("archive name does not match its VERSION")
        run("extracted-unit", ["strict_unittest.py"], cwd=packaged)
        for name, args, count in (
            ("reference", ["runner.py"], 29),
            ("community", ["community_runner.py"], 34),
            ("temporal-reference", ["temporal_runner.py", "--summary"], 3),
        ):
            report = json.loads(run(f"extracted-{name}", args, cwd=packaged))
            if (report["total"] != count or len(report["results"]) != count or report["passed"] != count
                    or any(result["error"] is not None for result in report["results"])
                    or (name != "temporal-reference" and report["version"] != version)):
                raise ValueError(f"{name}: unexpected results in release archive")
        receipt = json.loads(run("extracted-receipt-renewal",
                                 ["runner.py", "--negative-control", "receipt-renewal"], 1, cwd=packaged))
        cache = json.loads(run("extracted-cache-per-turn",
                               ["temporal_runner.py", "--fault", "cache-per-turn", "--summary"], 1, cwd=packaged))
        summary["archive_negative_controls"] = {
            "receipt-renewal": check_receipt_renewal(receipt),
            "cache-per-turn": check_stale_cache(cache),
        }
        summary["archive_version"] = version
        summary["archive_source"] = json.loads((packaged / "SOURCE_IDENTITY.json").read_bytes())
        rebuilt_dir = extracted / "rebuilt"
        rebuilt = json.loads(run("extracted-rebuild", ["build_release.py", "--output", str(rebuilt_dir)], cwd=packaged))
        if rebuilt["sha256"] != digest or file_hash(rebuilt_dir / archive.name) != digest:
            raise ValueError("archive cannot reproduce its own bytes")
    summary["source_archive_sha256"] = digest


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,default=ROOT/'.checks')
    p.add_argument('--evaluator',default='unspecified');p.add_argument('--relationship',default='unspecified')
    mode=p.add_mutually_exclusive_group()
    mode.add_argument('--archive',type=Path,help='verify and test this exact release ZIP in a fresh directory')
    mode.add_argument('--isolation',action='store_true')
    a=p.parse_args();out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
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
    def check_source():
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
        from temporal_runner import MUTANTS as TEMPORAL_MUTANTS
        temporal=json.loads(run('temporal-reference',['temporal_runner.py','--summary']))
        if temporal['total']!=3 or temporal['passed']!=3 or temporal['exit_code']!=0:
            raise AssertionError('temporal reference failed')
        summary['temporal_cases']=temporal['total']
        summary['temporal_controls']={}
        for name in TEMPORAL_MUTANTS:
            data=json.loads(run('temporal-'+name,['temporal_runner.py','--fault',name,'--summary'],1))
            witnesses=[r['id'] for r in data['results'] if not r['passed'] and r['violations'] and r['error'] is None]
            if not witnesses:raise AssertionError('undetected temporal fault '+name)
            summary['temporal_controls'][name]=witnesses
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
        check_archive(Path(one['archive']), run, summary)
        if summary['source_archive_sha256']!=one['sha256']:raise AssertionError('tested archive differs from build')
        if a.isolation:
            run('isolation',['strict_unittest.py','isolation_checks','resource_checks'])
            report('isolated-example',['community_runner.py','--candidate-dir','examples','--accept-external-code'],0,ROOT/'suites/community-v1.json')
            summary['external_isolation']='executed Linux checks'
        else:summary['external_isolation']='not requested; no foreign code executed'
    try:
        if a.archive:
            check_archive(a.archive, run, summary)
        else:
            check_source()
        summary['passed']=True
    except Exception as exc:
        summary['error']=type(exc).__name__+': '+str(exc)
    summary['receipts']=receipts
    (out/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(json.dumps({k:v for k,v in summary.items() if k!='receipts'},indent=2))
    return 0 if summary['passed'] else 1

if __name__=='__main__':sys.exit(main())
