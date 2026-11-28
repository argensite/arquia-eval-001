"""Compare evaluator-defined expectations with local JSON observations."""

import argparse
from decimal import Decimal
from hashlib import sha256
import json
import math
from pathlib import Path
import sys


def reject_constant(value):
    raise ValueError(f"non-finite JSON number: {value}")


def finite_float(value):
    number = float(value)
    if not math.isfinite(number):
        reject_constant(value)
    return number


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key: {key}")
        result[key] = value
    return result


def read_rows(path, key):
    source = path.read_bytes()
    document = json.loads(source, parse_constant=reject_constant, parse_float=finite_float,
                          object_pairs_hook=unique_object)
    if not isinstance(document, dict) or not isinstance(document.get(key), list):
        raise ValueError(f"{key} must be an array")
    indexed = {}
    for row in document[key]:
        case_id = row.get("id") if isinstance(row, dict) else None
        if not isinstance(case_id, str) or not case_id.strip() or case_id in indexed:
            raise ValueError(f"invalid or duplicate id in {key}: {case_id!r}")
        indexed[case_id] = row
    return indexed, sha256(source).hexdigest()


def same_value(left, right):
    if isinstance(left, bool) or isinstance(right, bool):
        return left is right
    if isinstance(left, dict):
        return (isinstance(right, dict) and left.keys() == right.keys()
                and all(same_value(left[key], right[key]) for key in left))
    if isinstance(left, list):
        return (isinstance(right, list) and len(left) == len(right)
                and all(same_value(a, b) for a, b in zip(left, right)))
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        # Compare the decimal values that the report emits as JSON numbers.
        left_number = Decimal(str(left)) if isinstance(left, float) else Decimal(left)
        right_number = Decimal(str(right)) if isinstance(right, float) else Decimal(right)
        return left_number == right_number
    return left == right


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
            if not same_value(expected[field], observed[field]):
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
