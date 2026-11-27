from contextlib import closing
from hashlib import sha256
import json
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
import unittest

from .run import run_case, verdict
from .target import PENDING_BYTES, PRIOR_BYTES, advance, connect, export, receive, start


class ObservationTests(unittest.TestCase):
    def setUp(self):
        scratch = TemporaryDirectory()
        self.addCleanup(scratch.cleanup)
        self.directory = Path(scratch.name)

    def read_journal(self, name):
        return json.loads((self.directory / name / "journal.json").read_text(encoding="utf-8"))

    def test_same_final_objects_have_different_verdicts(self):
        reference = run_case("reference", self.directory / "reference")
        fault = run_case("write-delete", self.directory / "write-delete")
        self.assertEqual(reference["status"], "pass")
        self.assertEqual(fault["status"], "fail")
        self.assertEqual(fault["reason"], "write_accepted_after_revocation")
        self.assertEqual(fault["witness"]["sha256"], sha256(PENDING_BYTES).hexdigest())
        self.assertLess(fault["witness"]["revocation_sequence"], fault["witness"]["write_sequence"])

        for name in ("reference", "write-delete"):
            directory = self.directory / name / "operator"
            with closing(connect(directory, "ro")) as connection:
                objects = connection.execute("SELECT slot, payload FROM objects").fetchall()
                self.assertEqual([tuple(row) for row in objects], [("prior", PRIOR_BYTES)])

        evidence = self.read_journal("write-delete")
        self.assertIn("delete", [entry["kind"] for entry in evidence["events"]])
        self.assertEqual(verdict(evidence), fault)

    def test_missing_seal_or_gap_is_inconclusive(self):
        self.assertEqual(run_case("unsealed", self.directory / "unsealed")["status"], "inconclusive")
        run_case("write-delete", self.directory / "write-delete")
        evidence = self.read_journal("write-delete")
        del evidence["events"][4]
        self.assertEqual(verdict(evidence)["reason"], "invalid_or_gapped_sequence")

    def test_write_rolls_back_if_journal_insert_fails(self):
        directory = self.directory / "target"
        start(directory)
        with closing(connect(directory)) as connection:
            advance(connection, "write", "revoked")
            connection.executescript("""
                CREATE TRIGGER reject_pending_record BEFORE INSERT ON journal
                WHEN NEW.kind = 'write' AND NEW.slot = 'pending'
                BEGIN SELECT RAISE(ABORT, 'forced journal failure'); END;
            """)
            write = json.dumps({"op": "write", "bytes_hex": PENDING_BYTES.hex()})
            with self.assertRaisesRegex(sqlite3.IntegrityError, "forced journal failure"):
                receive(connection, [write, '{"op": "done"}'])
            self.assertIsNone(connection.execute(
                "SELECT payload FROM objects WHERE slot = 'pending'"
            ).fetchone())
            self.assertNotIn("pending", [event["slot"] for event in export(connection)["events"]])
            with self.assertRaisesRegex(ValueError, "cannot record sealed"):
                advance(connection, "worker_finished", "sealed")

    def test_incomplete_worker_stream_cannot_be_sealed(self):
        directory = self.directory / "target"
        start(directory)
        with closing(connect(directory)) as connection:
            advance(connection, "write", "revoked")
            with self.assertRaisesRegex(ValueError, "without its end marker"):
                receive(connection, [])
            with self.assertRaisesRegex(ValueError, "cannot record sealed"):
                advance(connection, "worker_finished", "sealed")
            self.assertEqual(verdict(export(connection))["status"], "inconclusive")

    def test_target_journal_rejects_updates_and_deletion(self):
        directory = self.directory / "target"
        start(directory)
        with closing(connect(directory)) as connection:
            for command in ("UPDATE journal SET kind='sealed'", "DELETE FROM journal"):
                with self.assertRaisesRegex(sqlite3.IntegrityError, "append-only"):
                    with connection:
                        connection.execute(command)
            self.assertEqual(len(export(connection)["events"]), 2)


if __name__ == "__main__":
    unittest.main()
