"""RSI regression for the transient receipt-renewal witness."""
import unittest
from pathlib import Path

import engine
from runner import evaluate, load_cases

ROOT = Path(__file__).resolve().parent
WITNESS_ID = "C29-transient-receipt-renewal"


class RSI000001Tests(unittest.TestCase):
    def test_transient_receipt_renewal_is_detected_only_temporally(self):
        cases = load_cases(ROOT / "cases.json")
        witness = [case for case in cases if case["id"] == WITNESS_ID]
        self.assertEqual(len(witness), 1, "transient-renewal witness is missing")

        reference = evaluate(engine.Gate, witness)[0]
        mutant = evaluate(engine.ReceiptRenewal, witness)[0]

        self.assertTrue(reference["passed"], reference)
        self.assertFalse(mutant["passed"], mutant)
        self.assertEqual(mutant["mismatches"], {})
        self.assertEqual(mutant["actual"], reference["actual"])
        self.assertEqual(
            mutant["violations"],
            [{
                "step": 4,
                "property": "P1/P2-passive-event",
                "field": "active_grants",
                "before": [],
                "after": ["g1"],
            }],
        )


if __name__ == "__main__":
    unittest.main()
