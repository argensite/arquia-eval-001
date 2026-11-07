import ast
from pathlib import Path
import unittest
from community_runner import evaluate
from jsonl_adapter import JsonlCandidate,load_candidate
from schemas import load_suite

ROOT=Path(__file__).resolve().parent
class JsonlTests(unittest.TestCase):
    def test_example_passes_without_reference_inheritance(self):
        tree=ast.parse((ROOT/'examples/independent_candidate.py').read_text())
        imports={x.name for n in ast.walk(tree) if isinstance(n,ast.Import) for x in n.names}
        self.assertEqual(imports,{'json','sys'})
        cases=load_suite(ROOT/'suites/community-v1.json')['cases']
        results=evaluate(lambda:JsonlCandidate(trusted_example=True),cases)
        self.assertTrue(all(r['passed'] for r in results),[(r['id'],r['error'],r['mismatches']) for r in results if not r['passed']])

    def test_external_code_requires_explicit_acceptance_before_manifest_or_execution(self):
        with self.assertRaisesRegex(ValueError,'disabled'):
            JsonlCandidate(ROOT/'examples')

    def test_manifest_binds_files_and_identity(self):
        manifest,files=load_candidate(ROOT/'examples')
        self.assertEqual(manifest['name'],'independent-conventional')
        self.assertEqual(list(files),['independent_candidate.py'])
