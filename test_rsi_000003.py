"""The same regression fails by assertion on v0.1.2, without importing new modules."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT=Path(__file__).resolve().parent
class CommunityMeasurementRegression(unittest.TestCase):
    def test_complete_measurement_envelope_and_configuration_binding(self):
        p=subprocess.run([sys.executable,str(ROOT/'runner.py')],cwd=ROOT,capture_output=True,text=True,timeout=10)
        self.assertEqual(p.returncode,0,p.stderr)
        report=json.loads(p.stdout)
        self.assertIsInstance(report.get('measurement'),dict,'a full measurement envelope is required')
        m=report['measurement'];self.assertEqual(m['schema'],'arquia.measurement/1')
        for name in ('runner.py','engine.py','verify_package.py','measurement.py'):
            self.assertEqual(m['files'][name],hashlib.sha256((ROOT/name).read_bytes()).hexdigest())
        self.assertIn('configuration_sha256',m);self.assertIn('repository',m)
        self.assertIn('runtime_modules',m);self.assertEqual(m['exit_code'],p.returncode)
