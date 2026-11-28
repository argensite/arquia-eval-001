"""Record one decision commitment per evaluator-issued run."""

import argparse
from contextlib import closing
import json
from pathlib import Path
import re
import secrets
import sqlite3
import sys

from measurement import canonical, sha
from schemas import read_json


SCHEMA = """
CREATE TABLE IF NOT EXISTS runs (run_id TEXT PRIMARY KEY);
CREATE TABLE IF NOT EXISTS attempts (
    sequence INTEGER PRIMARY KEY,
    run_id TEXT NOT NULL REFERENCES runs(run_id),
    digest TEXT NOT NULL,
    accepted INTEGER NOT NULL CHECK (accepted IN (0, 1))
);
CREATE UNIQUE INDEX IF NOT EXISTS one_accepted_decision
    ON attempts(run_id) WHERE accepted = 1;
"""
OBSERVATIONS = ("decision_open", "custody_ack", "receipt_released", "receipt_ingress")


def hex_value(value):
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{64}", value):
        raise ValueError("expected 64 lowercase hexadecimal characters")
    return value


def decision_digest(run_id, decision_bytes):
    return sha(canonical({
        "protocol": "arquia.custody-pilot/1",
        "run_id": hex_value(run_id),
        "decision_sha256": sha(decision_bytes),
    }))


def connect(database):
    connection = sqlite3.connect(database, timeout=10)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def initialize(database):
    with closing(connect(database)) as connection, connection:
        connection.executescript(SCHEMA)


def register(database, run_id):
    with closing(connect(database)) as connection, connection:
        connection.execute("INSERT INTO runs(run_id) VALUES (?)", (hex_value(run_id),))


def require_run(connection, run_id):
    if not connection.execute("SELECT 1 FROM runs WHERE run_id = ?", (hex_value(run_id),)).fetchone():
        raise ValueError("run ID was not registered by the evaluator")


def submit(database, run_id, digest):
    hex_value(digest)
    with closing(connect(database)) as connection, connection:
        # Serialize readers deciding first acceptance with the append itself.
        connection.execute("BEGIN IMMEDIATE")
        require_run(connection, run_id)
        accepted = connection.execute(
            "SELECT 1 FROM attempts WHERE run_id = ? AND accepted = 1", (run_id,)
        ).fetchone() is None
        cursor = connection.execute(
            "INSERT INTO attempts(run_id, digest, accepted) VALUES (?, ?, ?)",
            (run_id, digest, accepted),
        )
        return {"run_id": run_id, "sequence": cursor.lastrowid, "digest": digest, "accepted": accepted}


def snapshot(database, run_id):
    with closing(connect(database)) as connection:
        require_run(connection, run_id)
        rows = connection.execute(
            "SELECT sequence, digest, accepted FROM attempts WHERE run_id = ? ORDER BY sequence",
            (run_id,),
        )
        return {
            "run_id": run_id,
            "attempts": [
                {"run_id": run_id, "sequence": row["sequence"], "digest": row["digest"],
                 "accepted": bool(row["accepted"])}
                for row in rows
            ],
        }


def result(status, reason, attempts):
    return {
        "status": status,
        "reason": reason,
        "recorded_rejections": sum(not attempt["accepted"] for attempt in attempts),
    }


def verify(ledger, observer, decision_bytes, rejected_digest=None):
    run_id = hex_value(observer["run_id"])
    if hex_value(ledger["run_id"]) != run_id:
        raise ValueError("custodian and evaluator run IDs differ")
    attempts = ledger["attempts"]
    previous = 0
    for attempt in attempts:
        hex_value(attempt["digest"])
        sequence = attempt["sequence"]
        if (attempt["run_id"] != run_id or type(attempt["accepted"]) is not bool
                or type(sequence) is not int or sequence <= previous):
            raise ValueError("invalid custody attempt")
        previous = sequence

    accepted = [attempt for attempt in attempts if attempt["accepted"]]
    if len(accepted) > 1:
        return result("fail", "multiple_accepted_digests", attempts)
    if not accepted:
        return result("inconclusive", "missing_custody_acknowledgement", attempts)
    if accepted[0] != attempts[0]:
        return result("fail", "first_attempt_was_not_accepted", attempts)
    if accepted[0]["digest"] != decision_digest(run_id, decision_bytes):
        return result("fail", "decision_digest_mismatch", attempts)

    events = observer["events"]
    kinds = [event["kind"] for event in events]
    expected = OBSERVATIONS
    if rejected_digest is not None:
        hex_value(rejected_digest)
        if (len(attempts) != 2 or attempts[1]["digest"] != rejected_digest
                or rejected_digest == accepted[0]["digest"]):
            return result("fail", "second_distinct_digest_rejection_not_recorded", attempts)
        expected = (*OBSERVATIONS[:2], "custody_rejection", *OBSERVATIONS[2:])
    if len(kinds) != len(expected) or set(kinds) != set(expected):
        return result("inconclusive", "missing_or_ambiguous_observations", attempts)
    if tuple(kinds) != expected:
        return result("fail", "invalid_observation_order", attempts)
    if hex_value(events[1]["ack_sha256"]) != sha(canonical(accepted[0])):
        return result("fail", "custody_acknowledgement_mismatch", attempts)
    if rejected_digest is not None and hex_value(events[2]["attempt_sha256"]) != sha(canonical(attempts[1])):
        return result("fail", "custody_rejection_mismatch", attempts)
    if hex_value(events[-2]["receipt_sha256"]) != hex_value(events[-1]["receipt_sha256"]):
        return result("fail", "receipt_mismatch", attempts)
    return result("pass", "one_decision_committed_before_ingress", attempts)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("issue", help="Mint a run ID as evaluator")
    digest_parser = commands.add_parser("digest", help="Bind decision bytes to a run ID")
    digest_parser.add_argument("run_id")
    digest_parser.add_argument("decision", type=Path)
    for name in ("init", "register", "submit", "snapshot"):
        command = commands.add_parser(name)
        command.add_argument("database", type=Path)
        if name != "init":
            command.add_argument("run_id")
        if name == "submit":
            command.add_argument("digest")
    check = commands.add_parser("verify")
    for name in ("ledger", "observer", "decision"):
        check.add_argument(name, type=Path)
    check.add_argument("--rejected-digest", help="Check that a distinct second digest was refused before release")
    args = parser.parse_args()

    try:
        if args.command == "issue":
            print(secrets.token_hex(32))
        elif args.command == "digest":
            print(decision_digest(args.run_id, args.decision.read_bytes()))
        elif args.command == "init":
            initialize(args.database)
        elif args.command == "register":
            register(args.database, args.run_id)
        elif args.command == "submit":
            attempt = submit(args.database, args.run_id, args.digest)
            print(json.dumps(attempt, sort_keys=True))
            return 0 if attempt["accepted"] else 1
        elif args.command == "snapshot":
            print(json.dumps(snapshot(args.database, args.run_id), indent=2))
        else:
            report = verify(read_json(args.ledger), read_json(args.observer),
                            args.decision.read_bytes(), args.rejected_digest)
            print(json.dumps(report, indent=2))
            return {"pass": 0, "fail": 1, "inconclusive": 3}[report["status"]]
    except (OSError, ValueError, sqlite3.Error, KeyError, TypeError) as error:
        print(str(error), file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
