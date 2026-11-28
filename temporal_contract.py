"""Bounded opt-in temporal suite and response contract, independent of v0.1.0."""

DECISION_FIELDS = {
    'dispatch': {'attempt_dispatch': bool, 'authority_source': str, 'grant_version_read': int},
    'effect_boundary': {'attempt_commit': bool, 'basis': str},
    'receipt': {'receipt_retained': bool, 'receipt_status': str, 'receipt_used_as_authority': bool},
    'plan_step': {'attempt_dispatch': bool, 'planner_advance': bool,
                  'receipt_used_as_authority': bool, 'prerequisite_observed': bool,
                  'grant_version_read': int, 'world_version_read': int,
                  'world_needed': bool, 'authority_source': str},
    'wake': {'reconsidered': bool, 'grant_version_read': int, 'world_version_read': int,
             'world_needed': bool, 'decision': str, 'attempt_dispatch': bool},
}
EVENT_FIELDS = {
    'grant': {'op','epoch','grant','scope','allowed','finish_after_revoke'},
    'revoke': {'op','epoch','grant'},
    'dispatch': {'op','operation','turn','scope'},
    'effect_boundary': {'op','operation'},
    'receipt': {'op','receipt','operation','claim'},
    'plan_step': {'op','operation','receipt_ref','turn'},
    'world_update': {'op','operation','needed'},
    'wake': {'op','wake','operation'},
}
CHOICES = {
    ('dispatch','authority_source'): {'current_authority','turn_cache'},
    ('effect_boundary','basis'): {'not_dispatched','current_grant','explicit_preauthorized_finish',
                                  'stale_dispatch_grant','denied'},
    ('receipt','receipt_status'): {'corroborated','unverified_claim'},
    ('plan_step','authority_source'): {'current_authority','late_receipt'},
    ('wake','decision'): {'close_obsolete','reconsider_only','eligible_not_automatic'},
}
EXPECT_FIELDS = {'dispatch_authorizations','effect_boundary_epochs','committed_effects',
                 'blocked_effects','receipt_verification','receipt_retained',
                 'reconsideration_wakes','post_revoke_dispatches','unauthorized_dispatches',
                 'unauthorized_effects','planner_unauthorized_advances','pending_final'}


def bounded(v):
    return type(v) is str and 0 < len(v) <= 100


def check_decision(op, decision):
    schema = DECISION_FIELDS[op]
    if type(decision) is not dict or set(decision) != set(schema):
        raise ValueError(f'{op}: invalid decision fields')
    for name, expected_type in schema.items():
        value = decision[name]
        if type(value) is not expected_type:
            raise ValueError(f'{op}.{name}: invalid type')
        if expected_type is str and not bounded(value):
            raise ValueError(f'{op}.{name}: invalid bounded string')
        if expected_type is int and not 0 <= value <= 10**9:
            raise ValueError(f'{op}.{name}: invalid version')
        if (op,name) in CHOICES and value not in CHOICES[(op,name)]:
            raise ValueError(f'{op}.{name}: unknown choice')
    return decision


def check_suite(suite):
    if type(suite) is not dict or suite.get('schema') != 'arquia.adapter-revocation-candidate/1':
        raise ValueError('wrong temporal suite schema')
    cases=suite.get('cases')
    if type(cases) is not list or not 1 <= len(cases) <= 64:
        raise ValueError('expected 1..64 cases')
    ids=set()
    for case in cases:
        if type(case) is not dict or not bounded(case.get('id')) or case['id'] in ids:
            raise ValueError('duplicate or invalid case id')
        ids.add(case['id'])
        if case.get('policy') not in ('hard_stop','preauthorized_finish'):
            raise ValueError('invalid revocation policy')
        expected=case.get('expect')
        if type(expected) is not dict or not expected or set(expected)-EXPECT_FIELDS:
            raise ValueError('missing/unknown expectations')
        events=case.get('events')
        if type(events) is not list or not 1 <= len(events) <= 100:
            raise ValueError('expected 1..100 events')
        for event in events:
            if type(event) is not dict or event.get('op') not in EVENT_FIELDS:
                raise ValueError('unknown event op')
            if set(event) != EVENT_FIELDS[event['op']]:
                raise ValueError('event fields not exact')
            for name in ('grant','scope','operation','turn','wake','receipt','receipt_ref','claim'):
                if name in event and not bounded(event[name]):
                    raise ValueError('unbounded event identifier '+name)
            if 'epoch' in event and (type(event['epoch']) is not int or not 0 <= event['epoch'] <= 10**9):
                raise ValueError('bad authority epoch')
            for name in ('needed','finish_after_revoke'):
                if name in event and type(event[name]) is not bool:
                    raise ValueError('invalid boolean '+name)
            if 'allowed' in event:
                a=event['allowed']
                if type(a) is not list or not 1 <= len(a) <= 100 or any(not bounded(v) for v in a) or len(set(a))!=len(a):
                    raise ValueError('bad allowed operations')
    return suite


class IsolatedTemporalCandidate:
    """Foreign JSONL candidate executed only through existing Linux containment."""
    def __init__(self, directory, accept_external_code):
        from jsonl_adapter import JsonlCandidate
        self.adapter=JsonlCandidate(directory, accept_external_code=accept_external_code)
        self.source_hashes=self.adapter.source_hashes

    def close(self):
        self.adapter.close()

    def dispatch(self, event, view):
        return self.adapter.respond(event,view)

    def effect(self, event, view):
        return self.adapter.respond(event,view)

    def receipt(self, event, view):
        return self.adapter.respond(event,view)

    def plan(self, event, view):
        return self.adapter.respond(event,view)

    def wake(self, event, view):
        return self.adapter.respond(event,view)
