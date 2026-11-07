import copy
import json
from pathlib import Path
import unittest
from unittest.mock import patch
import engine
import runner
import test_rsi_000001
from community_runner import evaluate
from conventional_candidate import Candidate,Fault,FAULTS
from schemas import load_suite,strict_json,validate,read_json
from build_community_cases import generate
from generate_cases import minimize

ROOT=Path(__file__).resolve().parent

class CommunityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.cases=load_suite(ROOT/'suites/community-v1.json')['cases']

    def test_all_reference_cases_and_distinct_fault_controls(self):
        self.assertTrue(all(r['passed'] for r in evaluate(Candidate,self.cases)))
        for fault in FAULTS:
            with self.subTest(fault=fault):
                results=evaluate(lambda:Fault(fault),self.cases)
                self.assertTrue(any(not r['passed'] for r in results),fault)
                self.assertTrue(any(not r['passed'] and r['error'] is None for r in results),fault)

    def test_c29_metatest_fails_when_temporal_detector_is_disabled(self):
        witness=[c for c in runner.load_cases(ROOT/'cases.json') if c['id'].startswith('C29')]
        self.assertFalse(runner.evaluate(engine.ReceiptRenewal,witness)[0]['passed'])
        with patch.object(runner,'temporal_violations',return_value=[]):
            self.assertTrue(runner.evaluate(engine.ReceiptRenewal,witness)[0]['passed'])
            result=unittest.TestResult()
            test_rsi_000001.RSI000001Tests('test_transient_receipt_renewal_is_detected_only_temporally').run(result)
            self.assertEqual(len(result.failures),1);self.assertEqual(result.errors,[])

    def test_detecting_an_effect_does_not_mean_preventing_it(self):
        result=evaluate(Candidate,[self.cases[14]])[0]
        self.assertTrue(result['passed']);self.assertEqual(result['consequences']['unauthorized_effects'],1)
        self.assertIs(result['consequences']['prevention_demonstrated'],False)

    def test_no_actions_is_not_a_trustworthy_pass(self):
        result=evaluate(lambda:Fault('deny-all'),[self.cases[0]])[0]
        self.assertFalse(result['passed']);self.assertIn('dispatches',result['mismatches'])

    def test_snapshot_lies_do_not_remove_effects_from_world(self):
        result=evaluate(lambda:Fault('hide-effect'),[self.cases[14]])[0]
        self.assertFalse(result['passed']);self.assertEqual(result['consequences']['unauthorized_effects'],1)
        self.assertIn('e',result['actual']['committed_effects'])

    def test_seed_reproducibility_and_violation_minimization(self):
        self.assertEqual(generate(42),generate(42));self.assertNotEqual(generate(42),generate(43))
        for seed in (0,42,719):self.assertTrue(all(r['passed'] for r in evaluate(Candidate,generate(seed))))
        case=self.cases[10];f=lambda:Fault('rollback-authority')
        result=minimize(f,case,'observation_active_grants')
        self.assertLessEqual(len(result['case']['events']),len(case['events']))
        self.assertFalse(result['result']['passed']);self.assertIsNone(result['result']['error'])
        for i in range(len(result['case']['events'])):
            trial=copy.deepcopy(result['case']);del trial['events'][i]
            r=evaluate(f,[trial])[0]
            self.assertFalse(r['error'] is None and any(v['property']=='observation_active_grants' for v in r['violations']))

    def test_schema_rejects_ambiguous_data_unknown_events_and_empty_expectation(self):
        for data in ('{"a":1,"a":2}','{"a":NaN}'):
            with self.assertRaises(ValueError):strict_json(data)
        schema=read_json(ROOT/'schemas/case.schema.json')
        for change in ('unknown','expect','epoch'):
            c=copy.deepcopy(self.cases[0])
            if change=='unknown':c['events'][0]['op']='launch'
            if change=='expect':c['expect']={}
            if change=='epoch':c['events'][0]['authority_epoch']=True
            with self.assertRaises(ValueError):validate({'schema':'arquia.community-cases/1','cases':[c]},schema)
