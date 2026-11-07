import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import verify_package
import verify_report

ROOT = Path(__file__).resolve().parent


class MeasurementTests(unittest.TestCase):
    def test_producer_and_dependency_identity_and_tampering(self):
        p = subprocess.run([sys.executable, 'runner.py'], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stderr)
        r = json.loads(p.stdout)
        self.assertIn('runner.py', r['measurement']['files'])
        self.assertIn('engine.py', r['measurement']['files'])
        self.assertIn('verify_package.py', r['measurement']['files'])
        verify_report.verify(r, ROOT, ROOT/'cases.json')
        tampered = copy.deepcopy(r); tampered['passed'] = 0
        with self.assertRaisesRegex(ValueError, 'payload digest'):
            verify_report.verify(tampered, ROOT)

    def test_empty_duplicate_traversal_and_symlink_manifests_fail(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); manifest=root/'CHECKSUMS.sha256'
            for text in ('', '0'*64+'  ../runner.py\n', 'malformed\n'):
                manifest.write_text(text)
                with self.assertRaises(ValueError): verify_package.verify(root)

    def test_constructor_failure_is_a_case_failure(self):
        from runner import evaluate
        class Broken:
            def __init__(self): raise RuntimeError('constructor')
        result=evaluate(Broken,[{'id':'constructor','events':[],'expect':{'dispatches':0}}])[0]
        self.assertFalse(result['passed']);self.assertIn('constructor',result['error'])
