"""Compare evaluator-defined expectations with local JSON observations."""

import argparse
from hashlib import sha256
import json
from pathlib import Path
import sys


def reject_constant(value):
    raise ValueError(f"non-finite JSON number: {value}")


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def read_rows(path, key):
    source = path.read_bytes()
    document = json.loads(source, parse_constant=reject_constant, object_pairs_hook=unique_object)
    if not isinstance(document, dict) or not isinstance(document.get(key), list):
        raise ValueError(f"{key} must be an array")
    indexed = {}
    for row in document[key]:
        case_id = row.get("id") if isinstance(row, dict) else None
        if not isinstance(case_id, str) or not case_id.strip() or case_id in indexed:
            raise ValueError(f"invalid or duplicate id in {key}: {case_id!r}")
        indexed[case_id] = row
    return indexed, sha256(source).hexdigest()


def compare(cases_path, observations_path):
    cases, cases_sha = read_rows(cases_path, "cases")
    observations, observations_sha = read_rows(observations_path, "observations")
    if not cases or observations.keys() - cases.keys():
        raise ValueError("provide at least one case and use only known case IDs in observations")

    counts = {"pass": 0, "fail": 0, "inconclusive": 0}
    results = []
    for case_id, case in cases.items():
        for field in ("rule", "scenario", "failure_criterion"):
            if not isinstance(case.get(field), str) or not case[field].strip():
                raise ValueError(f"{case_id}: {field} must be a nonempty string")
        expected = case.get("expected")
        observed = observations.get(case_id, {}).get("observed", {})
        if not isinstance(expected, dict) or not expected or not isinstance(observed, dict):
            raise ValueError(f"{case_id}: expected needs fields and observed must be an object")
        if case_id in observations and "observed" not in observations[case_id]:
            raise ValueError(f"{case_id}: observation row needs an observed object")

        missing = sorted(expected.keys() - observed.keys())
        mismatches = {}
        for field in sorted(expected.keys() & observed.keys()):
            # JSON comparison preserves the distinction between a boolean and a number.
            left = json.dumps(expected[field], sort_keys=True, allow_nan=False)
            right = json.dumps(observed[field], sort_keys=True, allow_nan=False)
            if left != right:
                mismatches[field] = {"expected": expected[field], "observed": observed[field]}
        status = "pass"
        if mismatches:
            status = "fail"
        elif missing:
            status = "inconclusive"
        counts[status] += 1
        results.append({
            "id": case_id, "rule": case["rule"], "scenario": case["scenario"],
            "failure_criterion": case["failure_criterion"], "status": status,
            "observed": {key: observed[key] for key in sorted(expected.keys() & observed.keys())},
            "missing": missing, "mismatches": mismatches,
        })

    exit_code = 1 if counts["fail"] else 3 if counts["inconclusive"] else 0
    return {
        "schema": "arquia.observation-comparison/1",
        "cases_sha256": cases_sha, "observations_sha256": observations_sha,
        "counts": counts, "results": results, "exit_code": exit_code,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("cases", type=Path)
    parser.add_argument("observations", type=Path)
    arguments = parser.parse_args()
    try:
        report = compare(arguments.cases, arguments.observations)
    except (OSError, ValueError, RecursionError) as error:
        print(str(error), file=sys.stderr)
        return 2
    print(json.dumps(report, ensure_ascii=True, indent=2))
    return report["exit_code"]


if __name__ == "__main__":
    sys.exit(main())
