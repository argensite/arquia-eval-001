"""Evaluator-owned serial actuator. No candidate imports and no real effects.

Commands are recorded even when unauthorized, to measure violations rather than
silently correcting the candidate. This is an observation boundary, not a sandbox.
"""
import copy


class World:
    def __init__(self):
        self.grants = {}
        self.effects = {}
        self.clock = 0
        self.role = 'operator'
        self.evidence_sequence = 0
        self.journal = []
        self.incidents = []
        self.dispatches = 0
        self.completions = 0
        self.checkpoints = {}
        self.position = -1

    def valid(self, gid, epoch=None, effect=None, scope=None, seen=None):
        g = self.grants.get(gid)
        if not g or not g['active'] or g['expires_at'] <= self.clock or g['role'] != self.role:
            return False
        if epoch is not None and epoch != g['authority_epoch']:
            return False
        if effect is not None and effect != g['effect']:
            return False
        if scope is not None and scope != g['scope']:
            return False
        seen = set() if seen is None else set(seen)
        if gid in seen:
            return False
        seen.add(gid)
        if g.get('parent'):
            p = self.grants.get(g['parent'])
            return bool(p and p['allow_delegate'] and p['scope'] == g['scope'] and p['effect'] == g['effect']
                        and self.valid(g['parent'], g['parent_epoch'], seen=seen))
        return True

    def finish_allowed(self, effect):
        g = self.grants.get(effect['grant'])
        if not (effect['finish_exception'] and g and g['authority_epoch']==effect['authority_epoch']
                and g['role']==self.role and g['expires_at']>self.clock):
            return False
        if g.get('parent'):
            parent=self.grants.get(g['parent'])
            return bool(parent and parent['allow_delegate'] and parent['scope']==g['scope']
                        and parent['effect']==g['effect']
                        and self.valid(g['parent'],g['parent_epoch'],seen={effect['grant']}))
        return True

    def event(self, event):
        self.position += 1
        op = event['op']
        if op == 'grant':
            gid = event['grant']; old = self.grants.get(gid)
            if event.get('verified', True) and (old is None or event['authority_epoch'] > old['authority_epoch']):
                g = dict(active=True, scope='write', role='operator', expires_at=1000,
                         finish_after_revoke=False, allow_delegate=False)
                g.update({k:v for k,v in event.items() if k not in ('op', 'verified')})
                if not g.get('parent') or (self.valid(g['parent'], g.get('parent_epoch'))
                    and self.grants[g['parent']]['allow_delegate']
                    and self.grants[g['parent']]['scope'] == g['scope']
                    and self.grants[g['parent']]['effect'] == g['effect']):
                    self.grants[gid] = g
        elif op == 'revoke':
            if event['grant'] in self.grants:
                self.grants[event['grant']]['active'] = False
        elif op == 'tick':
            if event['time'] < self.clock:
                raise ValueError('logical time cannot move backwards')
            self.clock = event['time']
        elif op == 'role':
            self.role = event['role']
            for g in self.grants.values():
                if g['role'] != self.role:
                    g['active'] = False
        elif op == 'external_commit':
            eid = event['effect']
            if eid not in self.effects:
                raise ValueError('external effect requires a dispatched operation')
            e = self.effects[eid]
            if e['status'] == 'committed':
                return
            allowed = self.valid(e['grant'], e['authority_epoch'], eid, e['scope']) or self.finish_allowed(e)
            e['status'] = 'committed'
            self.evidence_sequence += 1
            if not allowed:
                self.incidents.append('external_effect_after_authority_end')
            self.journal.append({'at':self.position,'type':'external_effect','effect':eid,
                                 'authorized':allowed,'effect_occurred':True,'evidence_sequence':self.evidence_sequence})
        elif op == 'abort':
            e = self.effects.get(event['effect'])
            if e and event.get('verified', False) and e['status'] == 'unresolved':
                e['status'] = 'aborted';self.evidence_sequence += 1
        elif op == 'receipt':
            # Labels, claims and later sequence numbers never change observed world state.
            self.evidence_sequence = max(self.evidence_sequence, event.get('evidence_sequence', 0))
        elif op in ('ask_dispatch','ask_complete','ask_compensate','timeout','recover','save','restore','data'):
            pass
        else:
            raise ValueError('unknown world event: ' + op)

    def view(self):
        return copy.deepcopy({'grants':self.grants,'effects':self.effects,'clock':self.clock,
                              'role':self.role,'evidence_sequence':self.evidence_sequence,
                              'incidents':sorted(set(self.incidents))})

    def execute(self, commands):
        violations = []
        for c in commands:
            eid, gid = c['effect'], c['grant']
            g, existing = self.grants.get(gid), self.effects.get(eid)
            valid = self.valid(gid,c['authority_epoch'],eid,c['scope'])
            op = c['op']
            if op == 'complete':
                valid = bool(existing and existing['phase']=='start' and existing['status']=='unresolved'
                             and existing['grant']==gid and existing['authority_epoch']==c['authority_epoch']
                             and existing['scope']==c['scope'] and (valid or self.finish_allowed(existing)))
            if op == 'alternate_commit':
                valid = False
            duplicate = bool(existing and op != 'complete')
            if not valid:
                violations.append('unauthorized_' + op)
            if duplicate:
                violations.append('duplicate_effect_attempt')
            occurred = op in ('complete','alternate_commit')
            self.journal.append({'at':self.position,'type':op,'effect':eid,'grant':gid,
                'authority_epoch':c['authority_epoch'],'evidence_sequence':self.evidence_sequence,
                'authorized':valid,'duplicate':duplicate,'effect_occurred':occurred})
            if op == 'dispatch':
                self.dispatches += 1
                if not existing:
                    self.effects[eid] = {'grant':gid,'authority_epoch':c['authority_epoch'],
                        'scope':c['scope'],'phase':c.get('phase','dispatch'),'status':'unresolved',
                        'finish_exception':bool(valid and g and c.get('phase')=='start' and g['finish_after_revoke'])}
            else:
                self.completions += 1
                if existing:
                    existing['status'] = 'committed'
                else:
                    self.effects[eid] = {'grant':gid,'authority_epoch':c['authority_epoch'],'scope':c['scope'],
                        'phase':'unobserved','status':'committed','finish_exception':False}
                self.evidence_sequence += 1
        return violations

    def snapshot(self):
        return {'active_grants':sorted(k for k in self.grants if self.valid(k)),
                'dispatches':self.dispatches,'completions':self.completions,
                'outcomes':{k:v['status'] for k,v in sorted(self.effects.items())},
                'committed_effects':sorted(k for k,v in self.effects.items() if v['status']=='committed'),
                'incidents':sorted(set(self.incidents))}
