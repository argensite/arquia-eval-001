"""Regression tests for offline checks and their reported verdicts."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from evaluacion.compare import compare

class StrictSelectionTests(unittest.TestCase):
    def test_selected_skip_is_a_real_failure(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/'selected_skip_fixture.py'
            path.write_text('import unittest\nclass Probe(unittest.TestCase):\n @unittest.skip("deliberate CI probe")\n def test_boundary(self): pass\n')
            result=subprocess.run([sys.executable,str(Path(__file__).with_name('strict_unittest.py')),'selected_skip_fixture'],
                                  cwd=folder,capture_output=True,text=True,timeout=15,
                                  env={**os.environ,'PYTHONPATH':folder,'PYTHONDONTWRITEBYTECODE':'1'})
            self.assertEqual(result.returncode,1,result.stderr)
            self.assertIn('skipped=1',result.stderr)
            self.assertIn('Ran 1 test',result.stderr)


class ObservationComparisonTests(unittest.TestCase):
    def test_json_numbers_compare_by_value_without_equating_booleans(self):
        expected = {"sample": [1, {"zero": 0, "large": 10**23}], "flag": True}
        case = {"id": "numeric", "rule": "r", "scenario": "s",
                "failure_criterion": "f", "expected": expected}
        with tempfile.TemporaryDirectory() as folder:
            cases = Path(folder) / "cases.json"
            observations = Path(folder) / "observations.json"
            cases.write_text(json.dumps({"cases": [case]}), encoding="utf-8")
            sample = [1.0, {"large": 1e23, "zero": -0.0}]
            for actual_sample, flag, exit_code in (
                (sample, True, 0),
                (sample, 1, 1),
                ([1.5, sample[1]], True, 1),
                ([True, sample[1]], True, 1),
            ):
                with self.subTest(sample=actual_sample, flag=flag):
                    row = {"id": "numeric", "observed": {"sample": actual_sample, "flag": flag}}
                    observations.write_text(json.dumps({"observations": [row]}), encoding="utf-8")
                    self.assertEqual(compare(cases, observations)["exit_code"], exit_code)


if __name__=='__main__':unittest.main()
