"""Operator-owned byte slots and their ordered acceptance journal."""
import argparse
from contextlib import closing
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
import sys
from uuid import uuid4


SCHEMA = "arquia-write-observation-v1"
PRIOR_BYTES = b"synthetic prior write\n"
PENDING_BYTES = b"synthetic queued write\n"

DATABASE_SCHEMA = """
CREATE TABLE run (id TEXT PRIMARY KEY);
CREATE TABLE objects (slot TEXT PRIMARY KEY, payload BLOB NOT NULL);
CREATE TABLE journal (
    sequence INTEGER PRIMARY KEY,
    kind TEXT NOT NULL,
    slot TEXT,
    digest TEXT
);
CREATE TRIGGER journal_no_update BEFORE UPDATE ON journal
BEGIN SELECT RAISE(ABORT, 'journal is append-only'); END;
CREATE TRIGGER journal_no_delete BEFORE DELETE ON journal
BEGIN SELECT RAISE(ABORT, 'journal is append-only'); END;
"""


def connect(directory, mode="rw"):
    uri = (directory / "target.sqlite3").absolute().as_uri()
    connection = sqlite3.connect(f"{uri}?mode={mode}", uri=True)
    connection.row_factory = sqlite3.Row
    return connection


def append(connection, kind, slot=None, digest=None):
    connection.execute(
        "INSERT INTO journal(kind, slot, digest) VALUES (?, ?, ?)",
        (kind, slot, digest),
    )


def phase(connection):
    return connection.execute(
        """SELECT kind FROM journal WHERE slot IS NULL OR slot = 'prior'
           ORDER BY sequence DESC LIMIT 1"""
    ).fetchone()["kind"]


def record_write(connection, slot, payload):
    digest = sha256(payload).hexdigest()
    connection.execute("INSERT INTO objects VALUES (?, ?)", (slot, payload))
    append(connection, "write", slot, digest)


def start(directory):
    directory.mkdir(mode=0o700)
    with closing(connect(directory, "rwc")) as connection:
        connection.executescript(DATABASE_SCHEMA)
        with connection:
            connection.execute("INSERT INTO run VALUES (?)", (uuid4().hex,))
            append(connection, "opened")
            record_write(connection, "prior", PRIOR_BYTES)


def advance(connection, expected, kind):
    with connection:
        connection.execute("BEGIN IMMEDIATE")
        if phase(connection) != expected:
            raise ValueError(f"cannot record {kind} at this point in the run")
        append(connection, kind)


def receive(connection, requests):
    advance(connection, "revoked", "worker_started")
    finished = False
    for line in requests:
        if finished:
            raise ValueError("worker sent data after its end marker")
        request = json.loads(line)
        if not isinstance(request, dict):
            raise ValueError("invalid worker request")
        if request == {"op": "done"}:
            finished = True
            continue
        with connection:
            connection.execute("BEGIN IMMEDIATE")
            if phase(connection) != "worker_started":
                raise ValueError("worker interval is closed")
            if request.keys() == {"op", "bytes_hex"} and request["op"] == "write":
                if not isinstance(request["bytes_hex"], str):
                    raise ValueError("write bytes must be hexadecimal text")
                record_write(connection, "pending", bytes.fromhex(request["bytes_hex"]))
            elif request == {"op": "delete"}:
                deleted = connection.execute("DELETE FROM objects WHERE slot = 'pending'")
                if deleted.rowcount != 1:
                    raise ValueError("there is no pending object to delete")
                append(connection, "delete", "pending")
            else:
                raise ValueError("invalid worker request")
    if not finished:
        raise ValueError("worker stream ended without its end marker")
    advance(connection, "worker_started", "worker_finished")


def export(connection):
    with connection:
        connection.execute("BEGIN")
        run_id = connection.execute("SELECT id FROM run").fetchone()["id"]
        rows = connection.execute("SELECT * FROM journal ORDER BY sequence")
        return {"schema": SCHEMA, "run_id": run_id, "events": [dict(row) for row in rows]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("start", "revoke", "receive", "seal", "export"))
    parser.add_argument("directory", type=Path)
    args = parser.parse_args()
    if args.command == "start":
        start(args.directory)
        return
    mode = "ro" if args.command == "export" else "rw"
    with closing(connect(args.directory, mode)) as connection:
        if args.command == "revoke":
            advance(connection, "write", "revoked")
        elif args.command == "receive":
            receive(connection, sys.stdin)
        elif args.command == "seal":
            advance(connection, "worker_finished", "sealed")
        else:
            print(json.dumps(export(connection), indent=2))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, sqlite3.Error) as exc:
        print(str(exc), file=sys.stderr)
        sys.exit(2)
