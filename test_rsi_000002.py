"""RSI regression: execution reports bind the exact runner and package verifier bytes."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parent


class ProducerIdentityTests(unittest.TestCase):
    def test_cli_reports_exact_runner_and_verifier_hashes(self):
        case = [{
            "id": "producer-identity",
            "events": [{"op": "grant", "grant": "g1", "effect": "e1"}],
            "expect": {"active_grants": ["g1"]}
        }]
        with tempfile.TemporaryDirectory() as directory:
            cases_path = Path(directory) / "cases.json"
            cases_path.write_text(json.dumps(case), encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(ROOT / "runner.py"), "--cases", str(cases_path)],
                capture_output=True, text=True
            )
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertIn("runner_sha256", report)
        self.assertIn("verifier_sha256", report)
        self.assertEqual(
            report["runner_sha256"],
            hashlib.sha256((ROOT / "runner.py").read_bytes()).hexdigest()
        )
        self.assertEqual(
            report["verifier_sha256"],
            hashlib.sha256((ROOT / "verify_package.py").read_bytes()).hexdigest()
        )


if __name__ == "__main__":
    unittest.main()
