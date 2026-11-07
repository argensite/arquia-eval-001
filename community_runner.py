"""Evaluate community/1 cases at an evaluator-owned synthetic effect boundary."""
import argparse
import copy
import json
from pathlib import Path
import sys
import measurement
from conventional_candidate import Candidate, Fault, FAULTS
from synthetic_world import World

ROOT=Path(__file__).resolve().parent


def evaluate(factory,cases):
    results=[]
    for case in cases:
        world=World();trace=[];violations=[];error=None;checkpoints={};candidate=None
        try:
            candidate=factory()
            for index,event in enumerate(case['events']):
                world.event(event)
                if event['op']=='save': checkpoints[event['name']]=copy.deepcopy(candidate.export_state())
                if event['op'] in ('recover','restore'):
                    state=(checkpoints.get(event.get('name'),{}) if event['op']=='restore' else candidate.export_state())
                    candidate=factory();candidate.restore(copy.deepcopy(state))
                # Only immutable JSON copies cross the candidate boundary.
                view=world.view()
                response=candidate.respond(copy.deepcopy(event),copy.deepcopy(view))
                validate_response(response)
                expected=world.snapshot()
                for key in ('active_grants','outcomes','incidents'):
                    if response['observed'][key]!=expected[key]:
                        violations.append({'step':index,'property':'observation_'+key,
                            'expected':expected[key],'actual':response['observed'][key]})
                if event['op'] not in ('ask_dispatch','ask_complete','ask_compensate') and response['commands']:
                    violations.append({'step':index,'property':'passive_event_action'})
                for name in world.execute(response['commands']):
                    violations.append({'step':index,'property':name})
                trace.append({'step':index,'event':copy.deepcopy(event),'response':copy.deepcopy(response),
                              'world':world.snapshot(),'evidence_sequence':world.evidence_sequence,
                              'transport':copy.deepcopy(candidate.transcript[-1]) if getattr(candidate,'transcript',[]) else None})
            actual=world.snapshot()
            mismatches={k:{'expected':v,'actual':actual.get(k)} for k,v in case['expect'].items() if actual.get(k)!=v}
        except Exception as exc:
            error=type(exc).__name__+': '+str(exc);actual=world.snapshot();mismatches={}
        finally:
            if candidate is not None and hasattr(candidate,'close'): candidate.close()
        effects=[x for x in world.journal if x['effect_occurred']]
        bad=[x for x in effects if not x['authorized'] or x.get('duplicate')]
        results.append({'id':case['id'],'passed':not (violations or mismatches or error),'error':error,
            'mismatches':mismatches,'violations':violations,'actual':actual,'trace':trace,'effect_ledger':world.journal,
            'consequences':{'observed_effects':len(effects),'unauthorized_effects':len(bad),
                            'prevention_demonstrated':False if bad else None},
            'evidence_sufficient':'synthetic_boundary_only' if not error else 'inconclusive',
            'property':case.get('problem',case['id']),'hypothesis':case.get('hypothesis','unspecified'),
            'expected':case['expect'],'limitations':case.get('limitations',[]),
            'reproduce':case.get('reproduce','run this case file with community_runner.py')} )
    return results


def validate_response(response):
    if not isinstance(response,dict) or set(response)!= {'commands','observed'}:
        raise ValueError('response must have exactly commands and observed')
    commands=response['commands'];observed=response['observed']
    if not isinstance(commands,list) or len(commands)>8 or not isinstance(observed,dict):
        raise ValueError('response bounds/type')
    if set(observed)!= {'active_grants','outcomes','incidents'}:
        raise ValueError('observation fields')
    if not isinstance(observed['active_grants'],list) or not isinstance(observed['incidents'],list) or not isinstance(observed['outcomes'],dict):
        raise ValueError('observation types')
    for c in commands:
        if not isinstance(c,dict) or set(c)-{'op','grant','effect','authority_epoch','scope','phase'}:
            raise ValueError('unknown command fields')
        if c.get('op') not in ('dispatch','complete','alternate_commit') or type(c.get('authority_epoch')) is not int:
            raise ValueError('command operation/epoch')
        if 'phase' in c and c['phase'] not in ('dispatch','start'):
            raise ValueError('command phase')
        if any(not isinstance(c.get(k),str) or not c[k] or len(c[k])>200 for k in ('grant','effect','scope')):
            raise ValueError('command identity')


def main(argv=None):
    if hasattr(sys.stdout, "reconfigure"): sys.stdout.reconfigure(encoding="utf-8")
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--cases',type=Path,default=ROOT/'suites/community-v1.json')
    p.add_argument('--fault',choices=FAULTS)
    p.add_argument('--example-jsonl',action='store_true',help='Run the shipped independent example')
    p.add_argument('--candidate-dir',type=Path,help='External candidate manifest directory')
    p.add_argument('--accept-external-code',action='store_true',help='Explicitly accept execution with required Linux bubblewrap isolation')
    p.add_argument('--evaluator',default='unspecified');p.add_argument('--relationship',default='unspecified')
    p.add_argument('--markdown',type=Path)
    args=p.parse_args(argv)
    from schemas import load_suite
    suite=load_suite(args.cases)
    factory=(lambda:Fault(args.fault)) if args.fault else Candidate
    identity='conventional-acl/1' if not args.fault else 'deliberate-fault:'+args.fault
    candidate_sources={};isolation='same process; trusted project source only'
    if sum(bool(x) for x in (args.fault,args.example_jsonl,args.candidate_dir))>1:p.error('choose one candidate')
    if args.example_jsonl or args.candidate_dir:
        from jsonl_adapter import JsonlCandidate
        factory=lambda:JsonlCandidate(args.candidate_dir,accept_external_code=args.accept_external_code,trusted_example=args.example_jsonl)
        check=factory();candidate_sources=check.source_hashes;identity=check.manifest['name']+'/'+check.manifest['version'];check.close()
        def factory():
            obj=JsonlCandidate(args.candidate_dir,accept_external_code=args.accept_external_code,trusted_example=args.example_jsonl)
            if obj.source_hashes!=candidate_sources:raise ValueError('candidate files changed between cases')
            return obj
        isolation='shipped example subprocess; not isolated' if args.example_jsonl else 'Linux bubblewrap namespaces, restricted mounts, no host network'

    m=measurement.begin(['community_runner.py',*(sys.argv[1:] if argv is None else argv)],identity,args.cases,
                        args.evaluator,args.relationship,extra=[ROOT/'synthetic_world.py',ROOT/'schemas.py',args.cases])
    results=evaluate(factory,suite['cases']);code=0 if all(r['passed'] for r in results) else 1
    report={'protocol':'ARQUIA-EVAL-001','version':(ROOT/'VERSION').read_text().strip(),
        'suite':suite['schema'],'candidate':identity,'candidate_version':identity,'candidate_sources':candidate_sources,'isolation':isolation,
        'passed':sum(r['passed'] for r in results),'total':len(results),'results':results,'exit_code':code,
        'evidence_type':'local_synthetic_execution','observability':'evaluator_owned_synthetic_ledger',
        'evidence_available':['commands and simulated effects at declared boundary'],
        'evidence_missing':['real effects','cryptographic witnesses','independent evaluator identity'],
        'metrics':{'contract_passed':sum(r['passed'] for r in results),
                   'inconclusive_cases':sum(bool(r['error']) for r in results),
                   'observed_unauthorized_effects':sum(r['consequences']['unauthorized_effects'] for r in results)},
        'limitations':['No universal safety score','Only listed synthetic routes are observed',
                       'Ordinary ACL comparator; no incremental ARQUIA advantage established']}
    measurement.finish(report,m,code)
    if args.markdown:
        from render_report import render
        args.markdown.write_text(render(report),encoding='utf-8')
    print(json.dumps(report,indent=2,ensure_ascii=False));return code


if __name__=='__main__':sys.exit(main())
