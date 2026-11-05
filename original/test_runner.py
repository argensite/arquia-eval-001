import unittest
from runner import evaluate
from engine import Gate, KnownBadGate

class FixtureTests(unittest.TestCase):
    def test_reference_matches_predeclared_vectors(self):
        failures=[r for r in evaluate(Gate) if not r["pass"]]
        self.assertFalse(failures, failures)

    def test_suite_detects_deliberately_bad_receipt_renewal(self):
        failures={r["id"] for r in evaluate(KnownBadGate) if not r["pass"]}
        self.assertTrue(failures)
        self.assertIn("C01-late-receipt",failures)

if __name__=="__main__":
    unittest.main()
