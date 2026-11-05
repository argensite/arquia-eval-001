"""Freeze author-proposed assertions independently of the candidate implementation."""
import copy
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def e(op, **kw):
    return dict(op=op, **kw)


def baseline(*, finish=False, phase="dispatch", request="synthetic-request"):
    return [e("grant", grant="g1", effect="e1", finish_after_revoke=finish, request=request),
            e(phase, grant="g1", effect="e1")]


def receipt(rid="r1", effect="e1", grant="g1", **kw):
    return e("receipt", receipt_id=rid, grant=grant, effect=effect,
             source=kw.pop("source", "independent_observer"), **kw)


def case(id, description, events, **expect):
    return dict(id=id, description=description, events=events, expect=expect)


def build():
    cases = json.loads((ROOT / "original/cases.json").read_text())
    cases += [
        case("C13-receipt-id-conflict", "A valid receipt identifier cannot certify a different effect",
             baseline() + [e("external_commit", effect="e1"), receipt(),
             e("grant", grant="g2", effect="e2"), e("dispatch", grant="g2", effect="e2"),
             e("external_commit", effect="e2"), receipt(effect="e2", grant="g2")],
             conflicting_receipts=1, incidents=["receipt_id_conflict"],
             outcomes={"e1":"confirmed_by_sandbox_observer", "e2":"unknown"}),
        case("C14-untrusted-cannot-poison", "An untrusted first delivery cannot consume a later evidence key",
             baseline() + [e("external_commit", effect="e1"), receipt(source="executor"), receipt()],
             unverified_receipts=1, duplicate_receipts=0, outcomes={"e1":"confirmed_by_sandbox_observer"}),
        case("C15-confirmed-not-downgraded", "Later self-report cannot erase confirmed evidence",
             baseline() + [e("external_commit", effect="e1"), receipt(), receipt("r2", source="executor")],
             unverified_receipts=1, outcomes={"e1":"confirmed_by_sandbox_observer"}),
        case("C16-replay-renamed", "Changing delivery ID does not create another logical receipt",
             baseline() + [e("external_commit", effect="e1"), e("revoke", grant="g1"), receipt(), receipt("r2")],
             duplicate_receipts=1, dispatches=1, active_grants=[], committed_effects=["e1"]),
        case("C17-request-substitution", "Wrong request digest is rejected without poisoning the correct receipt",
             baseline() + [e("external_commit", effect="e1"), receipt(request_hash="0"*64), receipt()],
             orphan_receipts=1, duplicate_receipts=0, outcomes={"e1":"confirmed_by_sandbox_observer"}),
        case("C18-completion-once", "The preauthorized completion exception can be exercised at most once",
             baseline(finish=True, phase="start") + [e("revoke", grant="g1"),
             e("complete", grant="g1", effect="e1"), e("complete", grant="g1", effect="e1")],
             active_grants=[], dispatches=1, completions=1, blocks=1),
        case("C19-completion-no-start", "An exception cannot create an effect that never started",
             [e("grant", grant="g1", effect="e1", finish_after_revoke=True), e("revoke", grant="g1"),
             e("complete", grant="g1", effect="e1")],
             dispatches=0, completions=0, blocks=1, committed_effects=[]),
        case("C20-compensation-new-authority", "Compensation cannot inherit a revoked effect's grant",
             baseline() + [e("revoke", grant="g1"), e("external_commit", effect="e1"), receipt(),
             e("dispatch", grant="g1", effect="compensation"),
             e("grant", grant="g2", effect="compensation"), e("dispatch", grant="g2", effect="compensation")],
             active_grants=["g2"], dispatches=2, blocks=1,
             incidents=["escaped_effect_after_revocation"], pending_effects=["compensation"]),
        case("C21-recover-then-replay", "Serialized restoration preserves revocation and receipt bindings",
             baseline() + [e("external_commit", effect="e1"), e("revoke", grant="g1"), receipt(),
             e("clear_client_cache"), e("recover"), receipt("r2"), e("dispatch", grant="g1", effect="e1")],
             active_grants=[], dispatches=1, duplicate_receipts=1, blocks=1),
        case("C22-unorderable-commit", "Observed existence does not manufacture an ordering witness",
             baseline() + [e("revoke", grant="g1"), e("external_commit", effect="e1", ordering="undetermined"), receipt()],
             active_grants=[], execution_order={"e1":"undetermined"},
             incidents=["execution_order_undetermined"], outcomes={"e1":"confirmed_by_sandbox_observer"}),
        case("C23-completion-contract", "A preauthorized second phase observed after revocation follows its explicit exception",
             baseline(finish=True, phase="start") + [e("revoke", grant="g1"), e("external_commit", effect="e1"), receipt()],
             active_grants=[], execution_order={"e1":"after_revocation"}, incidents=[], committed_effects=["e1"]),
        case("C24-revoke-before-start", "A preauthorized completion flag cannot authorize a new start after revocation",
             [e("grant", grant="g1", effect="e1", finish_after_revoke=True), e("revoke", grant="g1"),
             e("start", grant="g1", effect="e1"), e("complete", grant="g1", effect="e1")],
             active_grants=[], dispatches=0, completions=0, blocks=2),
        case("C25-false-then-valid-evidence", "An inconsistent observer claim does not consume a later valid observation",
             baseline() + [receipt(), e("external_commit", effect="e1"), receipt()],
             incidents=["receipt_without_observed_effect"], duplicate_receipts=0,
             outcomes={"e1":"confirmed_by_sandbox_observer"}),
        case("C26-altered-request-retry", "Same effect ID with changed request cannot reuse the original grant",
             baseline(request="request-A") + [e("dispatch", grant="g1", effect="e1", request="request-B")],
             dispatches=1, blocks=1, pending_effects=["e1"]),
        case("C27-receipt-before-revoke", "Receipt first, revocation second still closes future execution",
             baseline() + [e("external_commit", effect="e1"), receipt(), e("revoke", grant="g1"),
             e("recover"), e("dispatch", grant="g1", effect="e1")],
             active_grants=[], dispatches=1, blocks=1, incidents=[]),
        case("C28-wrong-binding-first", "A mismatched receipt cannot reserve the identifier of the valid one",
             baseline() + [e("external_commit", effect="e1"), receipt(effect="e2"), receipt()],
             orphan_receipts=1, duplicate_receipts=0, outcomes={"e1":"confirmed_by_sandbox_observer"}),
    ]
    # Explicit request binding in v0.1.0; original vectors are kept untouched in original/.
    for c in cases:
        grants = {}
        for event in c["events"]:
            if event["op"] == "grant":
                grants[event["grant"]] = event
            elif event["op"] == "receipt" and "request_hash" not in event:
                grant = grants.get(event["grant"], {})
                raw = json.dumps([event["effect"], grant.get("request", "synthetic-request")],
                                 ensure_ascii=False, sort_keys=True, separators=(",", ":"))
                event["request_hash"] = hashlib.sha256(raw.encode()).hexdigest()
    return cases


if __name__ == "__main__":
    (ROOT / "cases.json").write_text(json.dumps(build(), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
