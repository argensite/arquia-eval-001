"""Regression for explicit revocation-scope reporting."""
from pathlib import Path
import unittest

import render_report

ROOT = Path(__file__).resolve().parent


class RevocationScopeTests(unittest.TestCase):
    def test_protocol_distinguishes_derived_state_from_influence_erasure(self):
        text = (ROOT / "PROTOCOL.md").read_text(encoding="utf-8")
        self.assertIn(
            "Derived-state revocation is tested at this modeled cache/restore boundary; "
            "influence erasure from training, fitting, weights, or other latent adaptation is not tested.",
            text,
        )

    def test_readable_report_surfaces_influence_erasure_nonclaim(self):
        report = {
            "candidate": "synthetic",
            "passed": 1,
            "total": 1,
            "exit_code": 0,
            "report_sha256": "0" * 64,
            "measurement": {
                "evaluator": {
                    "declared_identity": "test",
                    "declared_relationship": "test",
                },
                "duration_seconds": 0.0,
                "command": [],
                "repository": {},
            },
            "results": [
                {
                    "id": "scope-witness",
                    "passed": True,
                    "violations": [],
                    "mismatches": {},
                    "actual": {},
                    "error": None,
                }
            ],
        }
        rendered = render_report.render(report)
        self.assertIn("influence erasure after revocation", rendered)


if __name__ == "__main__":
    unittest.main()
