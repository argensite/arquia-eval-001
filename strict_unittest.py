"""CI entry: discovery without skipped/expected-failure false approvals."""
from pathlib import Path
import sys
import unittest

if __name__=='__main__':
    suite=unittest.defaultTestLoader.discover(str(Path(__file__).resolve().parent))
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    sys.exit(0 if result.testsRun>0 and result.wasSuccessful() and not result.skipped and not result.expectedFailures else 1)
