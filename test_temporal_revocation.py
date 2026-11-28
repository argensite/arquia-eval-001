"""Deterministic reference and mutation sensitivity checks; no external I/O."""
import copy
import json
from pathlib import Path
import sys
import subprocess
import unittest

from temporal_runner import FIXTURE, MUTANTS, run_suite, check_suite, check_decision, run_case


class TemporalRevocationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads(Path(FIXTURE).read_text(encoding='utf-8'))
        cls.report = run_suite()
        cls.cases = {r['id']:r for r in cls.report['results']}

    def test_all_three_proposed_reference_contracts(self):
        self.assertEqual(self.report['total'],3)
        self.assertEqual(self.report['passed'],3)
        self.assertEqual(self.report['exit_code'],0)
        self.assertTrue(all(not x['violations'] and not x['error'] for x in self.cases.values()))

    def test_two_call_dispatch_and_effect_permission_epochs(self):
        for ident in ('REV-2CALL-HARD-STOP','REV-2CALL-PREAUTHORIZED-FINISH'):
            case=self.cases[ident]
            self.assertEqual(case['actual']['dispatch_authorizations'],{'A':1,'B':1})
            self.assertEqual(case['actual']['effect_boundary_epochs'],{'A':1,'B':2})
            self.assertEqual([(x['grant_version_at_dispatch'],x['permission_version_at_effect_boundary'])
                              for x in case['effect_boundary_ledger']],[(1,1),(1,2)])

    def test_hard_stop_vs_explicitly_preauthorized_finish(self):
        blocked=self.cases['REV-2CALL-HARD-STOP']
        allowed=self.cases['REV-2CALL-PREAUTHORIZED-FINISH']
        self.assertEqual(blocked['actual']['committed_effects'],['A'])
        self.assertEqual(blocked['actual']['blocked_effects'],['B'])
        self.assertFalse(blocked['effect_boundary_ledger'][1]['effect_authorized_under_contract'])
        self.assertEqual(allowed['actual']['committed_effects'],['A','B'])
        self.assertFalse(allowed['effect_boundary_ledger'][1]['current_grant_valid_at_effect_boundary'])
        self.assertTrue(allowed['effect_boundary_ledger'][1]['preauthorized_finish_exception'])

    def test_late_receipts_are_retained_without_renewed_authority(self):
        for ident in ('REV-2CALL-HARD-STOP','REV-2CALL-PREAUTHORIZED-FINISH'):
            case=self.cases[ident]
            self.assertEqual(case['actual']['receipt_retained'],['r-A','r-B'])
            self.assertEqual(case['actual']['post_revoke_dispatches'],0)
            self.assertEqual(case['actual']['planner_unauthorized_advances'],0)
            self.assertFalse(case['planner'][0]['attempt_dispatch'])
            self.assertFalse(case['planner'][0]['receipt_used_as_authority'])
            self.assertFalse(case['planner'][0]['planner_advance'])
            self.assertTrue(case['planner'][0]['prerequisite_observed'])
        self.assertEqual(self.cases['REV-2CALL-HARD-STOP']['receipts']['r-B']
                         ['verification_against_actuator_ledger'],'unverified_claim')

    def test_wakes_use_fresh_permissions_and_world_facts_without_forced_execution(self):
        for ident in ('REV-2CALL-HARD-STOP','REV-2CALL-PREAUTHORIZED-FINISH'):
            r=self.cases[ident]
            self.assertEqual([w['wake'] for w in r['wakes']],['W1','W2'])
            self.assertEqual([w['permission_version_read'] for w in r['wakes']],[2,3])
            self.assertEqual([w['world_version_read'] for w in r['wakes']],[0,1])
            self.assertTrue(all(w['reconsidered'] and not w['executed'] for w in r['wakes']))
            self.assertEqual(r['wakes'][-1]['decision'],'close_obsolete')
            self.assertEqual(r['actual']['pending_final'],'closed_obsolete')

    def test_same_turn_revocation_disallows_second_dispatch(self):
        r=self.cases['REV-TURN-CACHE-NEGATIVE-CONTROL']
        self.assertEqual([x['attempted'] for x in r['dispatch_ledger']],[True,False])
        self.assertEqual([x['permission_epoch_at_dispatch'] for x in r['dispatch_ledger']],[1,2])
        self.assertEqual([x['candidate_grant_version_read'] for x in r['dispatch_ledger']],[1,2])
        self.assertEqual(r['actual']['unauthorized_dispatches'],0)

    def test_each_deliberate_fault_is_detected_by_its_specific_signal(self):
        properties={
            'cache-per-turn': 'stale_turn_cache',
            'dispatch-only': 'unauthorized_effect',
            'receipt-renewal': 'late_receipt_used_as_authority',
            'receipt-as-precondition': 'unauthorized_planner_advance',
            'wake-cache': 'wake_stale_authority',
            'wake-stale-world': 'wake_stale_world_facts',
            'drop-late-receipt': 'late_receipt_not_retained',
        }
        self.assertEqual(set(properties),set(MUTANTS))
        for mutant,signal in properties.items():
            with self.subTest(mutant=mutant):
                r=run_suite(mutant=mutant)
                self.assertEqual(r['exit_code'],1)
                self.assertLess(r['passed'],r['total'])
                found={v['property'] for x in r['results'] for v in x['violations']}
                self.assertIn(signal,found)
                self.assertTrue(all(x['error'] is None for x in r['results']))

    def test_reproducible_exact_run(self):
        self.assertEqual(run_suite(),run_suite())

    def test_contract_rejects_invalid_inputs_and_claims(self):
        for bad in (
            {**self.fixture, 'cases':[]},
            {**self.fixture, 'cases':[dict(self.fixture['cases'][0],policy='unknown')]},
            {**self.fixture, 'cases':[dict(self.fixture['cases'][0],events=[{'op':'dispatch','operation':'A','scope':'write','turn':'T','extra':1}])]},
        ):
            with self.assertRaises(ValueError):check_suite(bad)
        with self.assertRaises(ValueError):check_decision('dispatch', {
            'attempt_dispatch':1,'authority_source':'current_authority','grant_version_read':1})
        with self.assertRaises(ValueError):check_decision('wake', {'reconsidered':True})

    def test_cli_exit_status_and_structured_faults(self):
        script=Path(__file__).with_name('temporal_runner.py')
        good=subprocess.run([sys.executable,str(script),'--summary'],capture_output=True,text=True,timeout=15)
        self.assertEqual(good.returncode,0,good.stderr)
        self.assertEqual(json.loads(good.stdout)['passed'],3)
        for mutant in MUTANTS:
            with self.subTest(mutant=mutant):
                bad=subprocess.run([sys.executable,str(script),'--fault',mutant,'--summary'],capture_output=True,text=True,timeout=15)
                self.assertEqual(bad.returncode,1,bad.stderr)
                data=json.loads(bad.stdout)
                self.assertTrue(any(r['violations'] and r['error'] is None for r in data['results']))
        malformed=subprocess.run([sys.executable,str(script),'--candidate-dir','examples/temporal'],capture_output=True,text=True,timeout=15)
        self.assertEqual(malformed.returncode,2)
        self.assertIn('external code disabled',malformed.stderr)

    def test_plan_step_without_actual_dispatch_is_not_progress(self):
        from temporal_runner import Candidate
        class FalseProgress(Candidate):
            def plan(self,event,view):
                response=super().plan(event,view)
                response['planner_advance']=True
                return response
        case=self.fixture['cases'][0]
        result=run_case(case,factory=FalseProgress)
        self.assertFalse(result['passed'])
        self.assertIn('planner_advance_without_dispatch', {v['property'] for v in result['violations']})

    def test_jsonl_example_interoperates_without_evaluator_imports(self):
        example=Path(__file__).with_name('examples')/'temporal'/'temporal_candidate.py'
        class TrustedProjectExample:
            def __init__(self):self.sequence=0;self.checkpoint={}
            def close(self):pass
            def call(self,event,view):
                self.sequence+=1
                req={'protocol':'arquia.io/1','id':self.sequence,'event':event,
                     'context':view,'checkpoint':self.checkpoint}
                completed=subprocess.run([sys.executable,'-I',str(example)],
                    input=json.dumps(req)+'\n',capture_output=True,text=True,timeout=2)
                if completed.returncode:raise ValueError(completed.stderr)
                msg=json.loads(completed.stdout)
                if msg['id']!=self.sequence or msg['protocol']!='arquia.io/1':raise ValueError('envelope mismatch')
                self.checkpoint=msg['checkpoint']
                return msg['response']
            dispatch=effect=receipt=plan=wake=call
        results=[run_case(case,factory=TrustedProjectExample) for case in self.fixture['cases']]
        self.assertTrue(all(r['passed'] for r in results),[(r['id'],r['violations'],r['error']) for r in results])

        for scope, revocation_epoch, replace_first, expected_finish in (
            ("write", 4, False, True),
            ("read", 2, False, True),
            ("write", 3, True, False),
        ):
            grant = {"op": "grant", "epoch": 1, "grant": "g", "scope": scope,
                     "allowed": ["A"], "finish_after_revoke": True}
            events = [grant, {"op": "dispatch", "operation": "A", "turn": "T", "scope": scope}]
            if replace_first:
                events.append({**grant, "epoch": 2})
            events.extend([{"op": "revoke", "epoch": revocation_epoch, "grant": "g"},
                           {"op": "effect_boundary", "operation": "A"}])
            case = {
                "id": "custom-finish", "policy": "preauthorized_finish", "events": events,
                "expect": {"committed_effects": ["A"] if expected_finish else []},
            }
            check_suite({**self.fixture, "cases": [case]})
            for factory in (None, TrustedProjectExample):
                with self.subTest(scope=scope, epoch=revocation_epoch, factory=factory):
                    result = run_case(case, factory=factory)
                    self.assertTrue(result["passed"], result)
                    self.assertIs(result["effect_boundary_ledger"][0]["preauthorized_finish_exception"],
                                  expected_finish)

    def test_fixture_does_not_claim_to_be_dropin_community_case(self):
        self.assertEqual(self.fixture['schema'],'arquia.adapter-revocation-candidate/1')
        self.assertEqual(self.fixture['baseline']['current_community_suite_cases_reviewed'],34)
        self.assertNotEqual(self.fixture['schema'],'arquia.community-cases/1')
        self.assertEqual(len(self.fixture['cases']),3)


if __name__=='__main__':
    unittest.main()
