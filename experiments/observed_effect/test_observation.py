from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class ObservedEffectTests(unittest.TestCase):
    def test_reference_fault_and_inconclusive_observation(self):
        outcomes = [("reference", 0), ("stale-dispatch", 1), ("missing-observation", 3)]
        with tempfile.TemporaryDirectory() as directory:
            for scenario, expected_exit in outcomes:
                with self.subTest(scenario=scenario):
                    output = Path(directory) / scenario
                    result = subprocess.run(
                        [sys.executable, "-B", "-m", "experiments.observed_effect.run",
                         scenario, str(output)],
                        capture_output=True, text=True, timeout=30,
                    )
                    self.assertEqual(result.returncode, expected_exit, result.stderr)
                    report = json.loads(result.stdout)["results"][0]
                    trace = json.loads((output / "trace.json").read_text())["events"]
                    self.assertEqual([item["event"] for item in trace[:5]], [
                        "prior_effect_observed", "write_queued", "permission_revoked",
                        "late_receipt_delivered", "before_pending_worker",
                    ])
                    self.assertTrue(report["observed"]["late_receipt_corroborated"])
                    self.assertTrue(report["observed"]["permission_revoked_after_receipt"])
                    self.assertIsNone(trace[4]["effect_sha256"])
                    pending = output / "effects" / "pending"
                    if scenario == "stale-dispatch":
                        self.assertEqual(pending.read_bytes(), b"pending\n")
                        self.assertEqual(trace[-1]["effect_sha256"], sha256(b"pending\n").hexdigest())
                        self.assertEqual(report["mismatches"], {
                            "pending_effect_after_revocation": {"expected": False, "observed": True}
                        })
                    elif scenario == "missing-observation":
                        self.assertEqual(report["missing"], ["pending_effect_after_revocation"])
                        self.assertEqual(report["mismatches"], {})
                    else:
                        self.assertFalse(pending.exists())
                        self.assertEqual(report["status"], "pass")

    def test_existing_directory_keeps_prior_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory)
            evidence = output / "prior.stdout"
            evidence.write_bytes(b"original")
            result = subprocess.run(
                [sys.executable, "-B", "-m", "experiments.observed_effect.run",
                 "reference", str(output)],
                capture_output=True, timeout=30,
            )
            self.assertEqual(result.returncode, 2)
            self.assertEqual(evidence.read_bytes(), b"original")
