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

    def test_empty_traversal_and_malformed_manifests_fail(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d); manifest=root/'CHECKSUMS.sha256'
            for text in ('', '0'*64+'  ../runner.py\n', 'malformed\n'):
                manifest.write_text(text)
                with self.assertRaises(ValueError): verify_package.verify(root)

    def test_duplicate_manifest_entry_fails(self):
        import hashlib
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'file').write_bytes(b'x')
            line=hashlib.sha256(b'x').hexdigest()+'  file\n'
            (root/'CHECKSUMS.sha256').write_text(line+line)
            with self.assertRaisesRegex(ValueError,'duplicate'):verify_package.verify(root)

    def test_symlink_path_rejected_before_reading_target(self):
        from unittest.mock import patch
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);(root/'file').write_bytes(b'x')
            # Windows contributors need no elevated symlink-creation privilege.
            with patch.object(Path,'is_symlink',return_value=True):
                with self.assertRaisesRegex(ValueError,'symlink'):verify_package.safe_file(root,'file')

    def test_constructor_failure_is_a_case_failure(self):
        from runner import evaluate
        class Broken:
            def __init__(self): raise RuntimeError('constructor')
        result=evaluate(Broken,[{'id':'constructor','events':[],'expect':{'dispatches':0}}])[0]
        self.assertFalse(result['passed']);self.assertIn('constructor',result['error'])

class TamperTests(unittest.TestCase):
    def test_changed_instrument_is_detected_even_with_unchanged_report(self):
        p=subprocess.run([sys.executable,'runner.py'],cwd=ROOT,capture_output=True,text=True)
        r=json.loads(p.stdout)
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            for n in set(r['measurement']['files'])|set(r['measurement']['files_after']):
                target=root/n;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((ROOT/n).read_bytes())
            target=root/'runner.py';target.write_bytes(target.read_bytes()+b'\n# altered instrument\n')
            with self.assertRaisesRegex(ValueError,'measurement file mismatch'):
                verify_report.verify(r,root)
