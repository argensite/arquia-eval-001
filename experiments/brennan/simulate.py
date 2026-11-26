"""Run one synthetic late-receipt scenario and export both sides of the evidence."""

import argparse
from base64 import b64encode
import json
from pathlib import Path
import sys

from measurement import sha

from .verify import DECISION, GRANT, RECEIPT, TRACE, chain_link, decision_commitment, evaluate


SCENARIOS = (
    "reference", "rewrite", "publisher-only", "missing-commitment", "late-commitment",
    "collapsed-history", "corrupt-output", "renewal",
)
SAVED_OUTPUT = b'{"operation":"A","result":"saved"}\n'


def simulate(scenario):
    journal = []
    observations = []

    def append(entry):
        previous = journal[-1]["digest"] if journal else None
        journal.append(chain_link(previous, entry))

    append({"kind": "grant", "grant_id": GRANT, "operation": "A"})
    append({"kind": "dispatch", "grant_id": GRANT, "operation": "A"})
    append({"kind": "revoke", "grant_id": GRANT, "acknowledged": True})
    decision = {
        "kind": "decision", "decision_id": DECISION, "anchor_status": "absent",
        "receipt_id": None, "permission_active": False,
    }
    observations.append({"kind": "decision_point", "decision_id": DECISION})
    if scenario != "publisher-only":
        append(decision)
        if scenario not in ("missing-commitment", "late-commitment"):
            observations.append(decision_commitment(journal[-1]))

    output_hash = sha(SAVED_OUTPUT)
    ingress = {"kind": "receipt_ingress", "receipt_id": RECEIPT, "output_hash": output_hash}
    observations.append(ingress)

    publisher_witness = None
    if scenario == "publisher-only":
        # Build the same decision entry only after ingress. The publisher can
        # rebuild every link and supply its own earlier claimed position.
        append(decision)
        publisher_witness = {**decision_commitment(journal[-1]), "claimed_position": 1}

    arrival = {**ingress, "kind": "arrival", "anchor_status": "not checked"}
    append(arrival)
    verification = {
        "kind": "verification", "receipt_id": RECEIPT, "anchor_status": "verified",
        "computed_output_hash": sha(SAVED_OUTPUT),
    }
    append(verification)
    if scenario == "late-commitment":
        observations.append(decision_commitment(journal[3]))

    if scenario in ("rewrite", "collapsed-history"):
        journal[3:] = []
        append({**decision, "anchor_status": "verified", "receipt_id": RECEIPT})
        if scenario == "rewrite":
            append(arrival)
            append(verification)

    renewed = scenario == "renewal"
    append({
        "kind": "followup", "operation": "B", "allowed": renewed,
        "active_grant": GRANT if renewed else None, "effect_committed": renewed,
    })
    output = SAVED_OUTPUT if scenario != "corrupt-output" else SAVED_OUTPUT + b"changed\n"
    publisher = {
        "trace": TRACE,
        "journal": journal,
        "output_base64": b64encode(output).decode("ascii"),
        "publisher_witness": publisher_witness,
    }
    observer = {"trace": TRACE, "observations": observations}
    return publisher, observer


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("scenario", choices=SCENARIOS)
    parser.add_argument("output", type=Path, help="Create a new directory for this run")
    args = parser.parse_args()
    try:
        args.output.mkdir(parents=True, exist_ok=False)
        publisher, observer = simulate(args.scenario)
        for name, record in (("publisher", publisher), ("observer", observer)):
            (args.output / f"{name}.json").write_text(
                json.dumps(record, indent=2) + "\n", encoding="utf-8",
            )
        report = evaluate(publisher, observer)
    except (OSError, ValueError) as exc:
        print(f"Could not run scenario: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2))
    return report["exit_code"]


if __name__ == "__main__":
    sys.exit(main())
