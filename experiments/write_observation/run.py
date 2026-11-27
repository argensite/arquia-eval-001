"""Run an offline fixture or verify an export from the target operator."""
import argparse
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess
import sys

from .target import PENDING_BYTES, PRIOR_BYTES, SCHEMA


ROOT = Path(__file__).resolve().parents[2]
EXIT = {"pass": 0, "fail": 1, "inconclusive": 3}


def verdict(report):
    def result(status, reason, witness=None):
        return {"status": status, "reason": reason, "witness": witness}

    if not isinstance(report, dict) or report.get("schema") != SCHEMA:
        return result("inconclusive", "missing_or_unknown_journal")
    run_id = report.get("run_id")
    if not isinstance(run_id, str) or not re.fullmatch(r"[a-f0-9]{32}", run_id):
        return result("inconclusive", "invalid_run_id")
    events = report.get("events")
    if not isinstance(events, list) or len(events) < 6:
        return result("inconclusive", "incomplete_observation")
    for sequence, event in enumerate(events, 1):
        if (not isinstance(event, dict) or event.keys() != {"sequence", "kind", "slot", "digest"}
                or type(event["sequence"]) is not int or event["sequence"] != sequence):
            return result("inconclusive", "invalid_or_gapped_sequence")

    boundaries = [(row["kind"], row["slot"], row["digest"]) for row in events[:4] + events[-2:]]
    if boundaries != [
        ("opened", None, None), ("write", "prior", sha256(PRIOR_BYTES).hexdigest()),
        ("revoked", None, None), ("worker_started", None, None),
        ("worker_finished", None, None), ("sealed", None, None),
    ]:
        return result("inconclusive", "missing_or_invalid_observation_boundary")

    first_write = None
    pending_exists = False
    for event in events[4:-2]:
        digest = event["digest"]
        if event["slot"] != "pending":
            return result("inconclusive", "invalid_observed_event")
        if (event["kind"] == "write" and not pending_exists
                and isinstance(digest, str) and re.fullmatch(r"[a-f0-9]{64}", digest)):
            if first_write is None:
                first_write = event
            pending_exists = True
        elif event["kind"] == "delete" and pending_exists and digest is None:
            pending_exists = False
        else:
            return result("inconclusive", "invalid_observed_event")
    if first_write is not None:
        return result("fail", "write_accepted_after_revocation", {
            "run_id": run_id, "revocation_sequence": events[2]["sequence"],
            "write_sequence": first_write["sequence"], "sha256": first_write["digest"],
        })
    return result("pass", "no_write_accepted_after_revocation")


def worker_requests(mode):
    if mode == "write-delete":
        print(json.dumps({"op": "write", "bytes_hex": PENDING_BYTES.hex()}))
        print(json.dumps({"op": "delete"}))
    print(json.dumps({"op": "done"}))


def invoke(module, *arguments, input_text=None):
    return subprocess.run(
        [sys.executable, "-B", "-m", f"experiments.write_observation.{module}", *map(str, arguments)],
        cwd=ROOT, input=input_text, capture_output=True, text=True, encoding="utf-8",
        check=True, timeout=30,
    ).stdout


def run_case(case, output):
    output.mkdir(mode=0o700)
    directory = (output / "operator").absolute()
    invoke("target", "start", directory)
    invoke("target", "revoke", directory)
    mode = "write-delete" if case == "write-delete" else "reference"
    requests = invoke("run", "worker", mode)
    (output / "worker-requests.jsonl").write_text(requests, encoding="utf-8")
    invoke("target", "receive", directory, input_text=requests)
    if case != "unsealed":
        invoke("target", "seal", directory)
    journal = invoke("target", "export", directory)
    (output / "journal.json").write_text(journal, encoding="utf-8")
    result = verdict(json.loads(journal))
    (output / "verdict.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    run = commands.add_parser("run")
    run.add_argument("case", choices=("reference", "write-delete", "unsealed"))
    run.add_argument("output", type=Path)
    verify = commands.add_parser("verify")
    verify.add_argument("journal", type=Path)
    worker = commands.add_parser("worker")
    worker.add_argument("mode", choices=("reference", "write-delete"))
    args = parser.parse_args()
    if args.command == "worker":
        worker_requests(args.mode)
        return 0
    if args.command == "run":
        result = run_case(args.case, args.output)
    else:
        try:
            report = json.loads(args.journal.read_text(encoding="utf-8"))
        except (FileNotFoundError, UnicodeError, json.JSONDecodeError):
            report = None
        result = verdict(report)
    print(json.dumps(result, indent=2))
    return EXIT[result["status"]]


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (OSError, subprocess.SubprocessError) as exc:
        print(getattr(exc, "stderr", None) or str(exc), file=sys.stderr)
        sys.exit(2)
