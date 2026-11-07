"""Regression from a rejected project-side review; expected policy precedes fixes."""
from pathlib import Path
import unittest
from community_runner import evaluate
from conventional_candidate import Candidate
from synthetic_world import World
from schemas import load_suite

ROOT=Path(__file__).resolve().parent

class ParentCompletionTests(unittest.TestCase):
    def cases(self):return load_suite(ROOT/'suites/community-v1.json')['cases'][28:]

    def test_candidate_respects_parent_end_and_preserves_valid_own_exception(self):
        results=evaluate(Candidate,self.cases())
        self.assertTrue(all(r['passed'] for r in results),[(r['id'],r['mismatches']) for r in results if not r['passed']])

    def test_evaluator_detects_forced_completion_even_if_candidate_claims_authority(self):
        # Do not use candidate output to decide whether this effect is authorized.
        for case in self.cases()[:4]:
            with self.subTest(case=case['id']):
                world=World()
                for event in case['events']:
                    world.event(event)
                    if event['op']=='ask_dispatch':
                        world.execute([{'op':'dispatch','grant':event['grant'],'effect':'e',
                            'authority_epoch':event['authority_epoch'],'scope':'write','phase':'start'}])
                    if event['op']=='ask_complete':
                        violations=world.execute([{'op':'complete','grant':event['grant'],'effect':'e',
                            'authority_epoch':event['authority_epoch'],'scope':'write'}])
                        self.assertIn('unauthorized_complete',violations)
                        self.assertFalse(world.journal[-1]['authorized'])
                        self.assertTrue(world.journal[-1]['effect_occurred'])

    def test_forced_external_effect_is_detected_not_called_prevented(self):
        result=evaluate(Candidate,[self.cases()[-1]])[0]
        self.assertTrue(result['passed'])
        self.assertEqual(result['consequences']['unauthorized_effects'],1)
        self.assertIs(result['consequences']['prevention_demonstrated'],False)

if __name__=='__main__':unittest.main()
