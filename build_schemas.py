"""Rebuild the fixed protocol schemas; no execution or candidate feedback."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
S={'type':'string','minLength':1,'maxLength':200}
N={'type':'integer','minimum':0,'maximum':1000000}
B={'type':'boolean'}
def obj(props,required=None):
    return {'type':'object','properties':props,'required':list(props) if required is None else required,'additionalProperties':False}
def write(name,value):
    (ROOT/'schemas'/name).write_text(json.dumps(value,indent=2)+'\n')
def build():
    events=[]
    def event(op,props=None,required=None):
        props=props or {};p={'op':{'const':op},**props}
        events.append(obj(p,['op',*(list(props) if required is None else required)]))
    event('grant',dict(grant=S,effect=S,authority_epoch=N,scope=S,role=S,expires_at=N,finish_after_revoke=B,allow_delegate=B,parent=S,parent_epoch=N,verified=B),['grant','effect','authority_epoch'])
    event('revoke',{'grant':S});event('tick',{'time':N});event('role',{'role':S})
    for op in ('ask_dispatch','ask_complete','ask_compensate'):
        event(op,dict(grant=S,effect=S,authority_epoch=N,scope=S,phase={'enum':['dispatch','start']}),['grant','effect','authority_epoch'])
    event('external_commit',{'effect':S});event('abort',dict(effect=S,verified=B))
    event('receipt',dict(effect=S,evidence_sequence=N,source=S,claimed_status={'enum':['committed','aborted','unresolved']}),['effect','evidence_sequence'])
    for op in ('timeout','recover'):event(op)
    for op in ('save','restore'):event(op,{'name':S})
    event('data',{'content':{'type':'string','maxLength':4000}})
    strings={'type':'array','items':{'type':'string'},'minItems':1,'maxItems':50}
    props=dict(id=S,family=S,problem=S,hypothesis={'type':'string'},preconditions=strings,
        events={'type':'array','minItems':1,'maxItems':1000,'items':{'oneOf':events}},expect={'type':'object','minProperties':1,'properties':{'active_grants':{'type':'array','items':S},'dispatches':N,'completions':N,'outcomes':{'type':'object','additionalProperties':{'enum':['committed','aborted','unresolved']}},'committed_effects':{'type':'array','items':S},'incidents':{'type':'array','items':S}},'additionalProperties':False},
        invariants=strings,required_evidence=strings,assumptions=strings,limitations=strings,provenance={'type':'string'},reproduce={'type':'string'},seed=N)
    schema=obj({'schema':{'const':'arquia.community-cases/1'},'cases':{'type':'array','minItems':1,'maxItems':1000,'items':obj(props,[x for x in props if x!='seed'])}})
    schema.update({'$schema':'https://json-schema.org/draft/2020-12/schema','$id':'https://arquia.live/schemas/community-case-1','title':'Community synthetic cases v1'})
    write('case.schema.json',schema)
    h={'type':'string','pattern':'^[0-9a-f]{64}$'}
    m={'type':'object','required':['schema','started_utc','finished_utc','repository','files','configuration','configuration_sha256','environment','command','evaluator','exit_code','duration_seconds'],
       'properties':{'schema':{'const':'arquia.measurement/1'},'files':{'type':'object','additionalProperties':h},'configuration_sha256':h,'exit_code':{'enum':[0,1,2]},'command':{'type':'array','items':{'type':'string'}},'duration_seconds':{'type':'number','minimum':0}}}
    write('measurement.schema.json',m)
    case_result={'type':'object','required':['id','passed','error','violations','mismatches'],
                 'properties':{'id':S,'passed':B,'violations':{'type':'array'},'mismatches':{'type':'object'},'error':{'type':['string','null']}}}
    r={'type':'object','required':['report_schema','report_sha256','measurement','passed','total','results','exit_code'],
       'properties':{'report_schema':{'const':'arquia.result/1'},'report_sha256':h,'measurement':m,'passed':N,'total':N,'exit_code':{'enum':[0,1,2]},'results':{'type':'array','items':case_result}}}
    write('result.schema.json',r)
if __name__=='__main__':build()
