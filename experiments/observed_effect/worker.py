"""Perform one write in the evaluation workspace."""
import argparse
from hashlib import sha256
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("sandbox", type=Path)
    parser.add_argument("operation", choices=("prior", "pending"))
    parser.add_argument("--use-dispatch-snapshot", action="store_true")
    args = parser.parse_args()

    authority_name = "dispatch.json" if args.use_dispatch_snapshot else "authority.json"
    authority = json.loads((args.sandbox / authority_name).read_text(encoding="utf-8"))
    if not authority["write"]:
        print(json.dumps({"operation": args.operation, "worker_report": "blocked"}))
        return

    payload = f"{args.operation}\n".encode()
    with (args.sandbox / "effects" / args.operation).open("xb") as output:
        output.write(payload)
    print(json.dumps({
        "operation": args.operation,
        "worker_report": "completed",
        "receipt": {"operation": args.operation, "effect_sha256": sha256(payload).hexdigest()},
    }))


if __name__ == "__main__":
    main()
