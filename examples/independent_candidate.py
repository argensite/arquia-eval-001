"""Standalone JSONL candidate. No ARQUIA or evaluator imports, inheritance or libraries.

Implements a conventional capability policy independently for community/1.
Not an independently evaluated third-party artifact: authored for this project.
"""
import json
import sys


def answer(message):
    event=message['event'];facts=message['context'];grants=facts['grants'];world=facts['effects']
    def eligible(identifier,visited=()):
        if identifier in visited or identifier not in grants:return False
        token=grants[identifier]
        if not token['active'] or token['role']!=facts['role'] or token['expires_at']<=facts['clock']:return False
        parent=token.get('parent')
        if parent:
            if parent not in grants or not grants[parent]['allow_delegate']:return False
            if grants[parent]['authority_epoch']!=token['parent_epoch']:return False
            if grants[parent]['effect']!=token['effect'] or grants[parent]['scope']!=token['scope']:return False
            return eligible(parent,visited+(identifier,))
        return True
    active=sorted(k for k in grants if eligible(k))
    decisions=[]
    if event['op'] in ('ask_dispatch','ask_complete','ask_compensate'):
        ident=event['grant'];effect=event['effect'];epoch=event['authority_epoch'];scope=event.get('scope','write')
        token=grants.get(ident,{});prior=world.get(effect)
        allowed=(ident in active and token['authority_epoch']==epoch and token['effect']==effect and token['scope']==scope)
        if event['op']=='ask_complete':
            parent=token.get('parent');issuer=grants.get(parent,{})
            parent_current=not parent or (eligible(parent) and issuer.get('authority_epoch')==token['parent_epoch']
                and issuer.get('allow_delegate') and issuer.get('scope')==token['scope'] and issuer.get('effect')==token['effect'])
            exception=(prior and prior['finish_exception'] and token.get('authority_epoch')==epoch
                       and token['role']==facts['role'] and token['expires_at']>facts['clock'] and parent_current)
            allowed=bool(prior and prior['grant']==ident and prior['authority_epoch']==epoch and prior['scope']==scope
                         and prior['phase']=='start' and prior['status']=='unresolved' and (allowed or exception))
        else:allowed=allowed and prior is None
        if allowed:
            decisions.append(dict(op='complete' if event['op']=='ask_complete' else 'dispatch',grant=ident,effect=effect,
                                  authority_epoch=epoch,scope=scope,phase=event.get('phase','dispatch')))
    return {'protocol':'arquia.io/1','id':message['id'],'candidate':{'name':'independent-conventional','version':'1'},
            'response':{'commands':decisions,'observed':{'active_grants':active,
                'outcomes':{k:v['status'] for k,v in sorted(world.items())},'incidents':facts['incidents']}},
            'checkpoint':{}}


def main():
    line=sys.stdin.buffer.readline(262145)
    if len(line)>262144 or not line.endswith(b'\n'):return 2
    request=json.loads(line)
    if request['protocol']!='arquia.io/1':return 2
    sys.stdout.write(json.dumps(answer(request),separators=(',',':'))+'\n');sys.stdout.flush()
    return 0

if __name__=='__main__':sys.exit(main())
