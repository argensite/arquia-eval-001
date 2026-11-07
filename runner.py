"""Offline contract runner; third parties may supply their own cases and adapter."""
import argparse
import hashlib
import importlib
import json
from pathlib import Path
import platform
import sys

VERSION = "0.1.1"
ROOT = Path(__file__).resolve().parent
MUTANTS = {
    "receipt-renewal": "ReceiptRenewal", "blind-recovery": "BlindRecovery",
    "completion-bypass": "CompletionBypass", "hide-escape": "HideEscape",
    "recovery-loses-revocation": "RecoveryLosesRevocation",
}


def load_cases(path):
    cases = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(cases, list) or not cases:
        raise ValueError("Expected a nonempty JSON list of cases")
    ids = set()
    for case in cases:
        if not isinstance(case.get("id"), str) or case["id"] in ids:
            raise ValueError("Each case must have a unique string id")
        ids.add(case["id"])
        if not case.get("events") or not case.get("expect"):
            raise ValueError("Each case needs events and nonempty expectations")
    return cases


def evaluate(cls, cases):
    results = []
    for case in cases:
        obj = cls()
        trace, violations, error = [], [], None
        try:
            for index, event in enumerate(case["events"]):
                before = obj.snapshot()
                obj.step(event)
                if event["op"] in ("clear_client_cache", "recover"):
                    checkpoint = json.loads(json.dumps(obj.export_state(), sort_keys=True))
                    obj = cls.from_state(checkpoint)
                after = obj.snapshot()
                if event["op"] in ("receipt", "recover", "clear_client_cache", "timeout"):
                    for field in ("active_grants", "dispatches", "completions", "committed_effects"):
                        if before[field] != after[field]:
                            violations.append(dict(step=index, property="P1/P2-passive-event", field=field,
                                                   before=before[field], after=after[field]))
                trace.append(dict(event=event, state=after))
            got = obj.snapshot()
            mismatches = {k: dict(expected=v, actual=got.get(k)) for k, v in case["expect"].items()
                          if k not in got or got[k] != v}
        except Exception as exc:
            got, mismatches = None, {}
            error = type(exc).__name__ + ": " + str(exc)
        results.append(dict(id=case["id"], passed=not (mismatches or violations or error),
            mismatches=mismatches, violations=violations, error=error, actual=got, trace=trace))
    return results


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--cases", type=Path, default=ROOT / "cases.json")
    p.add_argument("--adapter", default="engine:Gate", help="Importable module:Class; executes its code")
    p.add_argument("--negative-control", choices=sorted(MUTANTS))
    p.add_argument("--evaluator", default="unspecified", help="Self-declared identity; not proof of independence")
    args = p.parse_args(argv)
    if args.negative_control and args.adapter != "engine:Gate":
        p.error("Choose an adapter OR a negative control")
    candidate = "engine:" + MUTANTS[args.negative_control] if args.negative_control else args.adapter
    module_name, class_name = candidate.split(":", 1)
    module = importlib.import_module(module_name)
    cases = load_cases(args.cases)
    results = evaluate(getattr(module, class_name), cases)
    path = Path(module.__file__)
    report = dict(protocol="ARQUIA-EVAL-001", version=VERSION, evidence_type="local_execution",
        independence="not_established_by_runner", evaluator=args.evaluator, candidate=candidate,
        python=platform.python_version(), platform=platform.system(),
        cases_sha256=hashlib.sha256(args.cases.read_bytes()).hexdigest(),
        adapter_file_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
        passed=sum(r["passed"] for r in results), total=len(results), results=results)
    print(json.dumps(report, indent=2, ensure_ascii=False))
    return 0 if all(r["passed"] for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
