"""Acceptance checks for the fixture, with mutation sensitivity and restart evidence."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import engine
from runner import evaluate, load_cases, MUTANTS

ROOT = Path(__file__).resolve().parent


class ContractTests(unittest.TestCase):
    def test_reference_and_each_negative_control(self):
        cases = load_cases(ROOT / "cases.json")
        failed = [r for r in evaluate(engine.Gate, cases) if not r["passed"]]
        self.assertEqual(failed, [])
        for name, cls_name in MUTANTS.items():
            with self.subTest(mutant=name):
                self.assertTrue(any(not r["passed"] for r in evaluate(getattr(engine, cls_name), cases)))

    def test_restart_is_a_new_instance_with_identical_observable_state(self):
        cases = load_cases(ROOT / "cases.json")
        for case in cases:
            g = engine.Gate()
            for event in case["events"]:
                g.step(event)
                restored = engine.Gate.from_state(json.loads(json.dumps(g.export_state())))
                self.assertIsNot(restored, g)
                self.assertEqual(restored.snapshot(), g.snapshot(), (case["id"], event))
                g = restored

    def test_independent_case_file_can_fail_and_exceptions_are_failures(self):
        cases = [{"id":"reviewer-case", "events":[{"op":"unknown-op"}], "expect":{"dispatches":0}}]
        r = evaluate(engine.Gate, cases)
        self.assertFalse(r[0]["passed"])
        self.assertIn("ValueError", r[0]["error"])

    def test_cli_reports_failure_and_exact_source_identity(self):
        result = subprocess.run([sys.executable, str(ROOT / "runner.py"),
                                 "--negative-control", "hide-escape"], capture_output=True, text=True)
        self.assertEqual(result.returncode, 1, result.stderr)
        d = json.loads(result.stdout)
        self.assertEqual(len(d["cases_sha256"]), 64)
        self.assertEqual(d["independence"], "not_established_by_runner")

    def test_external_module_execution_is_disabled_before_import(self):
        with tempfile.TemporaryDirectory() as directory:
            p = Path(directory)
            (p / "reviewer_candidate.py").write_text(
                'class Candidate:\n'
                '    def step(self, event): pass\n'
                '    def snapshot(self): return {"active_grants": [], "dispatches": 0, "completions": 0, "committed_effects": []}\n')
            cases = [{"id":"external", "events":[{"op":"timeout"}], "expect":{"dispatches":1}}]
            (p / "reviewer_cases.json").write_text(json.dumps(cases))
            r = subprocess.run([sys.executable, str(ROOT / "runner.py"),
                "--adapter", "reviewer_candidate:Candidate", "--cases", str(p / "reviewer_cases.json")],
                env={**os.environ, "PYTHONPATH": directory}, capture_output=True, text=True)
            self.assertEqual(r.returncode, 2, r.stderr)
            self.assertIn("External Python imports are disabled", r.stderr)
            self.assertEqual(r.stdout, "")


if __name__ == "__main__":
    unittest.main()
