"""A skipped selected suite must never become a passing CI command."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

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

if __name__=='__main__':unittest.main()
