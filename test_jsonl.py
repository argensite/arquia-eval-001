import ast
import os
from pathlib import Path
import unittest
from unittest.mock import patch
from community_runner import evaluate
from jsonl_adapter import JsonlCandidate,load_candidate,trusted_environment
from schemas import load_suite

ROOT=Path(__file__).resolve().parent
class JsonlTests(unittest.TestCase):
    def test_wire_schema_and_runtime_reject_unknown_command_phase(self):
        from community_runner import validate_response
        from schemas import validate,read_json
        response={'commands':[{'op':'dispatch','authority_epoch':1,'grant':'g','effect':'e','scope':'write','phase':'unknown'}],
                  'observed':{'active_grants':[],'outcomes':{},'incidents':[]}}
        with self.assertRaisesRegex(ValueError,'command phase'):validate_response(response)
        schema=read_json(ROOT/'schemas/response.schema.json')
        with self.assertRaises(ValueError):validate({'protocol':'arquia.io/1','id':1,'candidate':{'name':'x','version':'1'},'response':response,'checkpoint':{}},schema)

    def test_example_passes_without_reference_inheritance(self):
        tree=ast.parse((ROOT/'examples/independent_candidate.py').read_text())
        imports={x.name for n in ast.walk(tree) if isinstance(n,ast.Import) for x in n.names}
        self.assertEqual(imports,{'json','sys'})
        cases=load_suite(ROOT/'suites/community-v1.json')['cases']
        results=evaluate(lambda:JsonlCandidate(trusted_example=True),cases)
        self.assertTrue(all(r['passed'] for r in results),[(r['id'],r['error'],r['mismatches'],r.get('last_transport')) for r in results if not r['passed']])

    def test_windows_runtime_root_is_preserved_without_private_environment(self):
        with patch('jsonl_adapter.os.name','nt'),patch.dict(os.environ,{'SystemRoot':r'C:\Windows','ARQUIA_TEST_PRIVATE':'private marker'},clear=True):
            self.assertEqual(trusted_environment(),{'PATH':os.defpath,'SystemRoot':r'C:\Windows'})
        with patch('jsonl_adapter.os.name','nt'),patch.dict(os.environ,{},clear=True):
            with self.assertRaisesRegex(ValueError,'SystemRoot'):trusted_environment()

    def test_external_code_requires_explicit_acceptance_before_manifest_or_execution(self):
        with self.assertRaisesRegex(ValueError,'disabled'):
            JsonlCandidate(ROOT/'examples')

    def test_manifest_binds_files_and_identity(self):
        manifest,files=load_candidate(ROOT/'examples')
        self.assertEqual(manifest['name'],'independent-conventional')
        self.assertEqual(list(files),['independent_candidate.py'])
