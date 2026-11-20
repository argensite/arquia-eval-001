"""Project-shipped independent JSONL temporal candidate example; no evaluator imports."""
import json
import sys


def permitted(view, op, scope='write'):
    grant=view['active_grant']
    return bool(grant and grant['epoch']==view['permission_epoch']
                and grant['scope']==scope and op in grant['allowed'])


def respond(request):
    event=request['event'];view=request['context'];op=event['op']
    state=request['checkpoint'] or {'receipts':{}}
    if op=='dispatch':
        allowed=permitted(view,event['operation'],event['scope'])
        decision={'attempt_dispatch':allowed,'authority_source':'current_authority',
                  'grant_version_read':view['permission_epoch']}
    elif op=='effect_boundary':
        item=view['operations'].get(event['operation'])
        live=bool(item and permitted(view,event['operation'],item['scope']))
        preauthorized=bool(item and view['policy']=='preauthorized_finish' and
            item['finish_exception'] and item['authorized_at_dispatch'] and
            item['scope']=='write' and view['active_grant'] is None and
            view['permission_epoch']==item['dispatch_grant_version']+1 and
            item['status']=='in_flight')
        decision={'attempt_commit':bool(live or preauthorized),
                  'basis':'current_grant' if live else 'explicit_preauthorized_finish' if preauthorized
                  else 'denied' if item else 'not_dispatched'}
    elif op=='receipt':
        status=('corroborated' if event['operation'] in view['committed_effects']
                else 'unverified_claim')
        state['receipts'][event['receipt']]={'operation':event['operation'],'status':status}
        decision={'receipt_retained':True,'receipt_status':status,'receipt_used_as_authority':False}
    elif op=='plan_step':
        receipt=state['receipts'].get(event['receipt_ref'])
        prerequisite=bool(receipt and receipt['status']=='corroborated')
        fact=bool(view['needed'].get(event['operation'],False))
        attempt=bool(prerequisite and fact and permitted(view,event['operation']))
        decision={'attempt_dispatch':attempt,'planner_advance':attempt,
                  'receipt_used_as_authority':False,'prerequisite_observed':prerequisite,
                  'grant_version_read':view['permission_epoch'],
                  'world_version_read':view['world_version'],'world_needed':fact,
                  'authority_source':'current_authority'}
    elif op=='wake':
        needed=bool(view['needed'].get(event['operation'],False))
        decision={'reconsidered':True,'grant_version_read':view['permission_epoch'],
                  'world_version_read':view['world_version'],'world_needed':needed,
                  'decision':'close_obsolete' if not needed else
                  'eligible_not_automatic' if permitted(view,event['operation']) else 'reconsider_only',
                  'attempt_dispatch':False}
    else:
        raise ValueError('unknown temporal operation')
    return decision,state


def main():
    raw=sys.stdin.buffer.readline(262145)
    if not raw.endswith(b'\n') or len(raw)>262144:raise ValueError('invalid request size')
    request=json.loads(raw)
    if request['protocol']!='arquia.io/1':raise ValueError('unsupported transport')
    decision,state=respond(request)
    response={'protocol':'arquia.io/1','id':request['id'],
              'candidate':{'name':'temporal-conventional-example','version':'1'},
              'response':decision,'checkpoint':state}
    sys.stdout.write(json.dumps(response,separators=(',',':'))+'\n')


if __name__=='__main__':main()
