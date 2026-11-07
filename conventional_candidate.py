"""Ordinary capability/ACL comparator; not an implementation of ARQUIA theory.

Independent of engine.Gate and of the evaluator's World.valid implementation.
It consumes only public protocol facts, never expected case outcomes.
"""
import copy


class Candidate:
    version = 'conventional-acl/1'
    def __init__(self):
        self.last = {}

    def export_state(self):
        return copy.deepcopy(self.last)

    def restore(self, state):
        self.last = copy.deepcopy(state)

    def respond(self, event, view):
        grants = view['grants']
        live = {k for k,g in grants.items() if g['active'] and g['expires_at']>view['clock'] and g['role']==view['role']}
        while True:
            removed = {k for k in live if grants[k].get('parent') and
                (grants[k]['parent'] not in live or
                 grants[grants[k]['parent']]['authority_epoch'] != grants[k]['parent_epoch'])}
            if not removed: break
            live -= removed
        commands=[]
        op=event['op']
        if op in ('ask_dispatch','ask_compensate','ask_complete'):
            gid,eid=event['grant'],event['effect'];g=grants.get(gid)
            epoch=event['authority_epoch'];scope=event.get('scope','write')
            permitted=bool(gid in live and g['authority_epoch']==epoch and g['effect']==eid and g['scope']==scope)
            existing=view['effects'].get(eid)
            if op=='ask_complete':
                parent=grants.get(g.get('parent')) if g else None
                parent_current=bool(g and (not g.get('parent') or
                    (g['parent'] in live and parent['authority_epoch']==g['parent_epoch']
                     and parent['allow_delegate'] and parent['scope']==g['scope'] and parent['effect']==g['effect'])))
                permitted=bool(existing and existing['grant']==gid and existing['authority_epoch']==epoch
                    and existing['scope']==scope and existing['phase']=='start' and existing['status']=='unresolved'
                    and (permitted or (existing['finish_exception'] and g and g['authority_epoch']==epoch
                        and g['role']==view['role'] and g['expires_at']>view['clock'] and parent_current)))
            else:
                permitted=permitted and existing is None
            if permitted:
                commands=[{'op':'complete' if op=='ask_complete' else 'dispatch','grant':gid,'effect':eid,
                    'authority_epoch':epoch,'scope':scope,'phase':event.get('phase','dispatch')}]
        self.last={'active_grants':sorted(live),'outcomes':{k:v['status'] for k,v in sorted(view['effects'].items())},
                   'incidents':view['incidents']}
        return {'commands':commands,'observed':copy.deepcopy(self.last)}


class Fault(Candidate):
    """Named, distinct synthetic faults; no external code or effects."""
    def __init__(self, fault):
        super().__init__();self.fault=fault;self.old_view=None

    def respond(self,event,view):
        remembered=copy.deepcopy(self.last)
        if self.fault=='rollback-authority' and event['op']=='restore' and self.old_view:
            view=copy.deepcopy(self.old_view)
        if event['op']=='save':self.old_view=copy.deepcopy(view)
        if self.fault=='stale-epoch' and event['op'].startswith('ask_'):
            gid=event['grant']
            if gid in view['grants']:view['grants'][gid]['authority_epoch']=event['authority_epoch']
        result=super().respond(event,view)
        if self.fault=='rollback-authority' and event['op']=='restore':
            result['observed']['active_grants']=remembered.get('active_grants',[])
        if self.fault=='receipt-authority' and event['op']=='receipt':
            result['observed']['active_grants']=sorted(view['grants'])
        if self.fault=='forged-success' and event['op']=='receipt':
            result['observed']['outcomes'][event['effect']]='committed'
        if self.fault=='hide-effect':
            result['observed']['incidents']=[]
            result['observed']['outcomes']={}
        if self.fault=='deny-all':result['commands']=[]
        if self.fault=='duplicate-dispatch' and event['op']=='ask_dispatch' and event['effect'] in view['effects']:
            result['commands']=[self.command(event)]
        if self.fault=='blind-retry' and event['op']=='recover':
            for eid,e in view['effects'].items():
                if e['status']=='unresolved':
                    result['commands'].append(self.command(dict(grant=e['grant'],effect=eid,authority_epoch=e['authority_epoch'],scope=e['scope'])))
        if self.fault=='completion-bypass' and event['op']=='ask_complete':
            result['commands']=[{**self.command(event),'op':'complete'}]
        if self.fault=='data-instruction' and event['op']=='data':
            result['commands']=[{'op':'alternate_commit','grant':'g','effect':'e','authority_epoch':1,'scope':'write'}]
        return result

    @staticmethod
    def command(event):
        return {'op':'dispatch','grant':event['grant'],'effect':event['effect'],
                'authority_epoch':event['authority_epoch'],'scope':event.get('scope','write'),'phase':'dispatch'}


FAULTS=('stale-epoch','rollback-authority','receipt-authority','forged-success','hide-effect',
        'deny-all','duplicate-dispatch','blind-retry','completion-bypass','data-instruction')
