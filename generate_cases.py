"""Deterministic sequence generator and violation-preserving 1-minimizer."""
import argparse
import copy
import json
from pathlib import Path
from build_community_cases import generate
from community_runner import evaluate
from conventional_candidate import Fault, FAULTS
from measurement import canonical, sha
from schemas import load_suite


def minimize(factory,case,property_name):
    def reproduces(candidate):
        r=evaluate(factory,[candidate])[0]
        return r['error'] is None and any(v['property']==property_name for v in r['violations'])
    result=copy.deepcopy(case)
    if not reproduces(result):raise ValueError('requested violation is not reproduced')
    changed=True
    while changed:
        changed=False
        for i in range(len(result['events'])):
            trial=copy.deepcopy(result);del trial['events'][i]
            if trial['events'] and reproduces(trial):
                result=trial;changed=True;break
    return {'schema':'arquia.counterexample/1','original_case_sha256':sha(canonical(case)),
            'seed':case.get('seed'),'preserved_violation':property_name,
            'minimality':'1-minimal by single event deletion, not globally shortest',
            'expectations':'Unchanged predeclared criteria; minimization preserves the named invariant violation, not final-count mismatches',
            'case':result,'result':evaluate(factory,[result])[0]}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--seed',type=int,default=20261107);p.add_argument('--count',type=int,default=32)
    p.add_argument('--output',type=Path,required=True)
    p.add_argument('--minimize',type=Path);p.add_argument('--case-id');p.add_argument('--fault',choices=FAULTS)
    p.add_argument('--property')
    a=p.parse_args()
    if a.minimize:
        if not (a.fault and a.property and a.case_id):p.error('minimize requires --fault --property --case-id')
        found=[c for c in load_suite(a.minimize)['cases'] if c['id']==a.case_id]
        if len(found)!=1:p.error('unknown case ID')
        value=minimize(lambda:Fault(a.fault),found[0],a.property)
    else:
        if not 0<=a.seed<=1000000 or not 1<=a.count<=1000:p.error('seed 0..1000000, count 1..1000')
        value={'schema':'arquia.community-cases/1','cases':generate(a.seed,a.count)}
    with a.output.open('x',encoding='utf-8') as out:out.write(json.dumps(value,indent=2)+'\n')

if __name__=='__main__':main()
