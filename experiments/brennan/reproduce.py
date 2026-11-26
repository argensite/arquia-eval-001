"""Run each scenario in its own process and record actual exit codes and outputs."""

import argparse
from io import BytesIO
import json
from pathlib import Path
import platform
import subprocess
import sys
from zipfile import ZipFile

from measurement import file_hash
from schemas import read_json


ROOT = Path(__file__).resolve().parents[2]
PACKAGE = "experiments.brennan"
MATRIX = {
    "reference": ("committed_at_decision_before_receipt", []),
    "rewrite": ("decision_digest_mismatch", [
        "decision_history_preserved", "decision_committed_before_receipt",
    ]),
    "publisher-only": ("publisher_controlled_witness", ["decision_committed_before_receipt"]),
    "missing-commitment": ("missing_commitment", ["decision_committed_before_receipt"]),
    "late-commitment": ("commitment_after_receipt", ["decision_committed_before_receipt"]),
    "collapsed-history": ("decision_digest_mismatch", [
        "decision_history_preserved", "receipt_bytes_verified", "decision_committed_before_receipt",
    ]),
    "corrupt-output": ("committed_at_decision_before_receipt", ["receipt_bytes_verified"]),
    "renewal": ("committed_at_decision_before_receipt", ["authorization_remains_revoked"]),
}
FROZEN = {
    "v0.1.0": ("b540e71ff2f615197dd886d6e0dbcae3baa62589", 28),
    "v0.1.1": ("0ee97e2df0eeff03956782cbf2ce2ef8bc7a7af3", 29),
    "v0.1.2": ("49e339f0d57c3794b68e12caa53feabe8ad7710c", 29),
}
HISTORICAL_FAULTS = (
    "receipt-renewal", "blind-recovery", "completion-bypass", "hide-escape",
    "recovery-loses-revocation",
)


def git(*args):
    return subprocess.check_output(["git", "-C", str(ROOT), *args], timeout=30)


def record(command, directory, label, expected, cwd=ROOT):
    stdout = directory / f"{label}.stdout"
    stderr = directory / f"{label}.stderr"
    with stdout.open("wb") as out, stderr.open("wb") as err:
        try:
            result = subprocess.run(command, cwd=cwd, stdout=out, stderr=err, timeout=180)
            actual = result.returncode
        except (OSError, subprocess.TimeoutExpired) as exc:
            err.write(f"\n{exc}\n".encode())
            actual = None
    return {
        "command": command, "cwd": str(cwd),
        "expected_exit_code": expected, "actual_exit_code": actual,
        "stdout_sha256": file_hash(stdout), "stderr_sha256": file_hash(stderr),
    }


def run_cases(output):
    results = {}
    for name, (reason, violations) in MATRIX.items():
        expected = int(bool(violations))
        case = output / name
        data = case / "trace"
        case.mkdir()
        receipts = {
            "simulate": record(
                [sys.executable, "-m", PACKAGE + ".simulate", name, str(data)],
                case, "simulate", expected,
            ),
            "verify": record(
                [sys.executable, "-m", PACKAGE + ".verify",
                 str(data / "publisher.json"), str(data / "observer.json")],
                case, "verify", expected,
            ),
        }
        result = {
            "expected_violations": violations, "expected_ordering_reason": reason,
            "commands": receipts, "matches": False,
        }
        try:
            observed = read_json(case / "verify.stdout")
            result["observed"] = observed
            result["matches"] = (
                all(receipt["actual_exit_code"] == expected for receipt in receipts.values())
                and observed == read_json(case / "simulate.stdout")
                and observed["exit_code"] == expected
                and observed["violations"] == violations
                and observed["ordering_reason"] == reason
            )
        except (OSError, ValueError, KeyError) as exc:
            result["error"] = str(exc)
        results[name] = result
    return results


def same_chain_in_ordering_controls(output):
    reference = read_json(output / "reference/trace/publisher.json")["journal"]
    return all(
        read_json(output / name / "trace/publisher.json")["journal"] == reference
        for name in ("publisher-only", "missing-commitment", "late-commitment")
    )


def run_regressions(output):
    output.mkdir()
    current = record(
        [sys.executable, "check_all.py", "--output", str(output / "current"),
         "--evaluator", "ARQUIA project", "--relationship", "author-side"],
        output, "current", 0,
    )
    results = {"current": current, "frozen": {}}
    for tag, (commit, expected_count) in FROZEN.items():
        directory = output / tag
        directory.mkdir()
        source = directory / "source"
        observed_commit = git("rev-parse", tag + "^{commit}").decode().strip()
        if observed_commit != commit:
            raise ValueError(f"{tag} resolved to {observed_commit}, expected {commit}")
        with ZipFile(BytesIO(git("archive", "--format=zip", commit))) as archive:
            archive.extractall(source)
        commands = [
            ("package", ["verify_package.py"], 0),
            ("unit", ["-m", "unittest", "-v", "test_contract"], 0),
            ("reference", ["runner.py", "--evaluator", "ARQUIA project"], 0),
        ]
        commands.extend(
            (fault, ["runner.py", "--evaluator", "ARQUIA project", "--negative-control", fault], 1)
            for fault in HISTORICAL_FAULTS
        )
        runs = {}
        for name, args, expected in commands:
            receipt = record([sys.executable, *args], directory, name, expected, cwd=source)
            if name == "reference" or name in HISTORICAL_FAULTS:
                data = read_json(directory / f"{name}.stdout")
                receipt.update(passed=data["passed"], total=data["total"])
                receipt["matches"] = (
                    data["total"] == expected_count
                    and (data["passed"] == expected_count) == (expected == 0)
                    and all(not case["error"] for case in data["results"])
                )
            runs[name] = receipt
        if tag == "v0.1.0":
            original = source / "original"
            runs["original-unit"] = record(
                [sys.executable, "-m", "unittest", "-v", "test_runner"],
                directory, "original-unit", 0, cwd=original,
            )
            for name, flags, count in (
                ("original-reference", [], 12),
                ("original-negative", ["--negative-control"], 4),
            ):
                receipt = record(
                    [sys.executable, "runner.py", *flags],
                    directory, name, int(bool(flags)), cwd=original,
                )
                data = read_json(directory / f"{name}.stdout")
                receipt.update(passed=data["passed"], total=data["total"])
                receipt["matches"] = (data["passed"], data["total"]) == (count, 12)
                runs[name] = receipt
        results["frozen"][tag] = {"commit": commit, "commands": runs}
    receipts = [current] + [
        receipt for frozen in results["frozen"].values() for receipt in frozen["commands"].values()
    ]
    results["passed"] = all(
        item["actual_exit_code"] == item["expected_exit_code"] and item.get("matches", True)
        for item in receipts
    )
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path, help="Create a new output directory")
    parser.add_argument("--regression", action="store_true", help="Also run the historical suites")
    args = parser.parse_args()
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    cases = run_cases(output)
    result = {
        "source_commit": git("rev-parse", "HEAD").decode().strip(),
        "source_clean": not git("status", "--porcelain"),
        "environment": {
            "system": platform.system(), "release": platform.release(),
            "architecture": platform.machine(), "python": platform.python_version(),
            "implementation": platform.python_implementation(), "python_executable": sys.executable,
        },
        "cases": cases,
    }
    passed = all(case["matches"] for case in cases.values())
    result["ordering_controls_retain_reference_chain"] = passed and same_chain_in_ordering_controls(output)
    passed &= result["ordering_controls_retain_reference_chain"]
    if args.regression:
        try:
            result["regression"] = run_regressions(output / "regression")
        except (OSError, ValueError, KeyError, subprocess.SubprocessError) as exc:
            result["regression"] = {"passed": False, "error": str(exc)}
        passed &= result["regression"]["passed"]
    result["passed"] = passed
    (output / "summary.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(f"{sum(case['matches'] for case in cases.values())}/{len(cases)} scenario outcomes matched")
    if args.regression:
        print("Historical regressions:", "passed" if result["regression"]["passed"] else "failed")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
