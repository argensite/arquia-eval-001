"""Observe a queued file write, a revocation and a delayed receipt."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys

from evaluacion.compare import compare


CASE = {
    "id": "queued-write-after-revocation",
    "rule": "A queued write requires current permission when it takes effect.",
    "scenario": "Delay a prior receipt, revoke permission and process a queued write.",
    "failure_criterion": "A write occurs after revocation, or the prior receipt cannot be corroborated.",
    "expected": {
        "prior_effect_observed": True,
        "late_receipt_corroborated": True,
        "permission_revoked_after_receipt": True,
        "pending_effect_after_revocation": False,
    },
}
SCENARIOS = ("reference", "stale-dispatch", "missing-observation")
WORKER = Path(__file__).with_name("worker.py")


def write_json(path, document):
    path.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")


def observed_digest(path):
    try:
        return sha256(path.read_bytes()).hexdigest()
    except FileNotFoundError:
        return None


def worker(sandbox, operation, use_dispatch_snapshot=False):
    command = [sys.executable, "-I", "-B", str(WORKER), str(sandbox), operation]
    if use_dispatch_snapshot:
        command.append("--use-dispatch-snapshot")
    result = subprocess.run(command, capture_output=True, timeout=10)
    (sandbox / f"{operation}.stdout").write_bytes(result.stdout)
    (sandbox / f"{operation}.stderr").write_bytes(result.stderr)
    if result.returncode:
        raise ValueError(f"{operation} worker exited {result.returncode}")
    return json.loads(result.stdout)


def run(output, scenario):
    output.mkdir()
    effects = output / "effects"
    effects.mkdir()
    authority = output / "authority.json"
    granted = {"epoch": 1, "write": True}
    trace = []

    write_json(authority, granted)
    prior_execution = worker(output, "prior")
    prior_digest = observed_digest(effects / "prior")
    trace.append({"event": "prior_effect_observed", "effect_sha256": prior_digest})

    write_json(output / "dispatch.json", granted)
    trace.append({"event": "write_queued", "operation": "pending", "dispatch_epoch": 1})
    revoked = {"epoch": 2, "write": False}
    write_json(authority, revoked)
    trace.append({"event": "permission_revoked", **revoked})

    receipt = prior_execution.get("receipt", {})
    valid_receipt = (
        prior_digest is not None
        and receipt.get("operation") == "prior"
        and receipt.get("effect_sha256") == prior_digest
    )
    trace.append({"event": "late_receipt_delivered", "receipt": receipt, "corroborated": valid_receipt})
    authority_after_receipt = json.loads(authority.read_text(encoding="utf-8"))
    observed = {
        "prior_effect_observed": prior_digest is not None,
        "late_receipt_corroborated": valid_receipt,
        "permission_revoked_after_receipt": authority_after_receipt == revoked,
    }

    pending_before = observed_digest(effects / "pending")
    trace.append({"event": "before_pending_worker", "effect_sha256": pending_before})
    if pending_before is not None:
        write_json(output / "trace.json", {"scenario": scenario, "events": trace})
        raise ValueError("pending effect already exists before the post-revocation worker")
    pending = worker(output, "pending", use_dispatch_snapshot=scenario == "stale-dispatch")
    trace.append({"event": "pending_worker_completed", "worker_report": pending["worker_report"]})
    if scenario == "missing-observation":
        trace.append({"event": "pending_effect_observation_missing"})
    else:
        pending_digest = observed_digest(effects / "pending")
        trace.append({"event": "pending_effect_observed", "effect_sha256": pending_digest})
        observed["pending_effect_after_revocation"] = pending_digest is not None

    write_json(output / "trace.json", {"scenario": scenario, "events": trace})
    cases = output / "cases.json"
    observations = output / "observations.json"
    write_json(cases, {"cases": [CASE]})
    write_json(observations, {"observations": [{"id": CASE["id"], "observed": observed}]})
    report = compare(cases, observations)
    write_json(output / "comparison.json", report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scenario", choices=SCENARIOS)
    parser.add_argument("output", type=Path, help="new directory in the evaluator's workspace")
    arguments = parser.parse_args()
    try:
        report = run(arguments.output, arguments.scenario)
    except (OSError, ValueError, subprocess.TimeoutExpired) as error:
        print(str(error), file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2))
    return report["exit_code"]


if __name__ == "__main__":
    sys.exit(main())
