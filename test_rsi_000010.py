"""RSI regression: receipt claims cannot advance evaluator-owned evidence sequence."""
import unittest

from synthetic_world import World


class ReceiptEvidenceSequenceTests(unittest.TestCase):
    def test_receipt_cannot_forge_evaluator_sequence(self):
        world = World()
        world.event({"op": "grant", "grant": "g1", "effect": "e1", "authority_epoch": 1})
        world.execute([{"op": "dispatch", "grant": "g1", "effect": "e1",
                        "authority_epoch": 1, "scope": "write"}])
        world.event({"op": "external_commit", "effect": "e1"})
        self.assertEqual(world.evidence_sequence, 1)

        world.event({"op": "receipt", "receipt_id": "r1", "grant": "g1", "effect": "e1",
                     "source": "executor", "evidence_sequence": 999999})

        self.assertEqual(
            world.evidence_sequence, 1,
            "receipt payload must not advance evaluator-owned evidence sequencing",
        )


if __name__ == "__main__":
    unittest.main()
