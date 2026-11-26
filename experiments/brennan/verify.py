"""Verify a synthetic publisher trace against evaluator-held observations."""

import argparse
from base64 import b64decode
import json
from pathlib import Path
import sys

from measurement import canonical, sha
from schemas import read_json


TRACE = "brennan-late-receipt"
DECISION = "decision-A"
RECEIPT = "receipt-A"
GRANT = "grant-P"
KINDS = ("grant", "dispatch", "revoke", "decision", "arrival", "verification", "followup")


def chain_link(previous, entry):
    return {
        "prev_digest": previous,
        "digest": sha(canonical({"trace": TRACE, "prev_digest": previous, "entry": entry})),
        "entry": entry,
    }


def decision_commitment(link):
    return {
        "kind": "decision_commitment",
        "decision_id": DECISION,
        "entry_digest": link["digest"],
    }


def ordering_reason(events, decision, publisher_witness):
    kinds = [event["kind"] for event in events]
    if kinds.count("decision_point") != 1 or kinds.count("receipt_ingress") != 1:
        return "missing_or_ambiguous_observer_boundaries"
    start = kinds.index("decision_point")
    end = kinds.index("receipt_ingress")
    if (
        start >= end
        or events[start] != {"kind": "decision_point", "decision_id": DECISION}
        or events[end].get("receipt_id") != RECEIPT
    ):
        return "invalid_observer_boundaries"
    if decision is None:
        return "missing_decision"
    wanted = decision_commitment(decision)
    if wanted in events[start + 1:end]:
        return "committed_at_decision_before_receipt"
    if wanted in events[end + 1:]:
        return "commitment_after_receipt"
    if wanted in events[:start]:
        return "commitment_before_decision_window"
    if "decision_commitment" in kinds:
        return "decision_digest_mismatch"
    if publisher_witness is not None:
        return "publisher_controlled_witness"
    return "missing_commitment"


def evaluate(publisher, observer):
    if publisher["trace"] != TRACE or observer["trace"] != TRACE:
        raise ValueError("unexpected trace identity")
    journal = publisher["journal"]
    events = observer["observations"]
    chain_ok = True
    previous = None
    for link in journal:
        chain_ok &= link == chain_link(previous, link["entry"])
        previous = link["digest"]

    entries = [link["entry"] for link in journal]
    kinds = tuple(entry["kind"] for entry in entries)
    decisions = [link for link in journal if link["entry"]["kind"] == "decision"]
    decision = decisions[0] if len(decisions) == 1 else None
    entries_by_kind = {entry["kind"]: entry for entry in entries}
    arrival = entries_by_kind.get("arrival", {})
    verification = entries_by_kind.get("verification", {})
    # The fixture supplies known stimulus and state assertions. A clean final
    # shape can satisfy these even when its prior existence is unproven.
    history_ok = (
        kinds == KINDS
        and canonical(decision["entry"]) == canonical({
            "kind": "decision", "decision_id": DECISION, "anchor_status": "absent",
            "receipt_id": None, "permission_active": False,
        })
        and arrival.get("anchor_status") == "not checked"
        and verification.get("anchor_status") == "verified"
        and arrival.get("receipt_id") == verification.get("receipt_id") == RECEIPT
    )

    ingress = [event for event in events if event["kind"] == "receipt_ingress"]
    output_hash = sha(b64decode(publisher["output_base64"], validate=True))
    receipt_ok = (
        ingress == [{"kind": "receipt_ingress", "receipt_id": RECEIPT, "output_hash": output_hash}]
        and arrival.get("output_hash") == verification.get("computed_output_hash") == output_hash
        and arrival.get("receipt_id") == verification.get("receipt_id") == RECEIPT
        and verification.get("anchor_status") == "verified"
    )
    authority_ok = (
        canonical(entries[:3]) == canonical([
            {"kind": "grant", "grant_id": GRANT, "operation": "A"},
            {"kind": "dispatch", "grant_id": GRANT, "operation": "A"},
            {"kind": "revoke", "grant_id": GRANT, "acknowledged": True},
        ])
        and kinds.count("followup") == 1
        and kinds[-1] == "followup"
        and canonical(entries[-1]) == canonical({
            "kind": "followup", "operation": "B", "allowed": False,
            "active_grant": None, "effect_committed": False,
        })
    )
    order_reason = ordering_reason(events, decision, publisher["publisher_witness"])
    checks = {
        "authorization_remains_revoked": authority_ok,
        "decision_history_preserved": history_ok,
        "chain_links_valid": chain_ok,
        "receipt_bytes_verified": receipt_ok,
        "decision_committed_before_receipt": order_reason == "committed_at_decision_before_receipt",
    }
    return {
        "trace": TRACE,
        "proof_scope": "evaluator-controlled simulation",
        "checks": checks,
        "ordering_reason": order_reason,
        "violations": [name for name, passed in checks.items() if not passed],
        "exit_code": 0 if all(checks.values()) else 1,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("publisher", type=Path)
    parser.add_argument("observer", type=Path, help="Select the evaluator's own observations")
    args = parser.parse_args()
    try:
        report = evaluate(read_json(args.publisher), read_json(args.observer))
    except (OSError, ValueError, KeyError, TypeError) as exc:
        print(f"Invalid evidence: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return report["exit_code"]


if __name__ == "__main__":
    sys.exit(main())
