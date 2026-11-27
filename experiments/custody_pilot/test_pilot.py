import copy
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from tempfile import TemporaryDirectory
import threading
import unittest

from experiments.custody_pilot import pilot
from measurement import canonical, sha


class CustodyPilotTests(unittest.TestCase):
    run_id = "a" * 64
    decision = b'{"permission":"revoked","receipt":"absent"}'
    alternate = b'{"permission":"revoked","receipt":"verified"}'

    def setUp(self):
        temp = TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.database = Path(temp.name) / "ledger.db"
        pilot.initialize(self.database)
        pilot.register(self.database, self.run_id)
        self.first = pilot.decision_digest(self.run_id, self.decision)
        self.second = pilot.decision_digest(self.run_id, self.alternate)

    def observe(self, accepted, rejection=None):
        receipt = sha(b"test receipt")
        events = [
            {"kind": "decision_open"},
            {"kind": "custody_ack", "ack_sha256": sha(canonical(accepted))},
        ]
        if rejection is not None:
            events.append({"kind": "custody_rejection", "attempt_sha256": sha(canonical(rejection))})
        events.extend([
            {"kind": "receipt_released", "receipt_sha256": receipt},
            {"kind": "receipt_ingress", "receipt_sha256": receipt},
        ])
        return {"run_id": self.run_id, "events": events}

    def test_reference_accepts_first_digest_and_checks_observed_order(self):
        accepted = pilot.submit(self.database, self.run_id, self.first)
        observer = self.observe(accepted)
        ledger = pilot.snapshot(self.database, self.run_id)
        self.assertTrue(accepted["accepted"])
        self.assertEqual(pilot.verify(ledger, observer, self.decision)["status"], "pass")
        observer["events"][1], observer["events"][2] = observer["events"][2], observer["events"][1]
        self.assertEqual(pilot.verify(ledger, observer, self.decision)["reason"], "invalid_observation_order")

    def test_second_distinct_digest_is_refused_and_logged_before_release(self):
        accepted = pilot.submit(self.database, self.run_id, self.first)
        rejected = pilot.submit(self.database, self.run_id, self.second)
        observer = self.observe(accepted, rejected)
        ledger = pilot.snapshot(self.database, self.run_id)
        self.assertFalse(rejected["accepted"])
        self.assertEqual(ledger["attempts"], [accepted, rejected])
        report = pilot.verify(ledger, observer, self.decision, self.second)
        self.assertEqual((report["status"], report["recorded_rejections"]), ("pass", 1))

        unlogged = {"run_id": self.run_id, "attempts": [accepted]}
        self.assertEqual(pilot.verify(unlogged, observer, self.decision, self.second)["reason"],
                         "second_distinct_digest_rejection_not_recorded")
        after_release = copy.deepcopy(observer)
        events = after_release["events"]
        events[2], events[3] = events[3], events[2]
        self.assertEqual(pilot.verify(ledger, after_release, self.decision, self.second)["reason"],
                         "invalid_observation_order")

        # A custodian that accepts both digests must fail even if the first was timely.
        corrupted = copy.deepcopy(ledger)
        corrupted["attempts"][1]["accepted"] = True
        self.assertEqual(pilot.verify(corrupted, observer, self.decision, self.second)["reason"],
                         "multiple_accepted_digests")
        self.assertEqual(pilot.verify(ledger, observer, self.alternate, self.second)["reason"],
                         "decision_digest_mismatch")

    def test_concurrent_submissions_leave_exactly_one_acceptance(self):
        barrier = threading.Barrier(2, timeout=10)

        def attempt(digest):
            barrier.wait()
            return pilot.submit(self.database, self.run_id, digest)

        with ThreadPoolExecutor(max_workers=2) as pool:
            rows = list(pool.map(attempt, (self.first, self.second)))
        self.assertEqual(sorted(row["accepted"] for row in rows), [False, True])
        self.assertEqual(pilot.snapshot(self.database, self.run_id)["attempts"],
                         sorted(rows, key=lambda row: row["sequence"]))

    def test_replayed_digest_cannot_reset_custody(self):
        first = pilot.submit(self.database, self.run_id, self.first)
        replayed = pilot.submit(self.database, self.run_id, self.first)
        self.assertFalse(replayed["accepted"])
        self.assertEqual(pilot.snapshot(self.database, self.run_id)["attempts"], [first, replayed])
        other = "b" * 64
        self.assertNotEqual(pilot.decision_digest(other, self.decision), self.first)
        with self.assertRaisesRegex(ValueError, "not registered"):
            pilot.submit(self.database, other, self.first)

    def test_publisher_assertion_alone_is_inconclusive(self):
        empty = pilot.snapshot(self.database, self.run_id)
        observer = {"run_id": self.run_id, "events": []}
        self.assertEqual(pilot.verify(empty, observer, self.decision)["status"], "inconclusive")

    def test_ack_and_receipt_must_match(self):
        accepted = pilot.submit(self.database, self.run_id, self.first)
        ledger = pilot.snapshot(self.database, self.run_id)
        observer = self.observe(accepted)
        observer["events"][1]["ack_sha256"] = "b" * 64
        self.assertEqual(pilot.verify(ledger, observer, self.decision)["reason"],
                         "custody_acknowledgement_mismatch")
        observer = self.observe(accepted)
        observer["events"][-1]["receipt_sha256"] = "c" * 64
        self.assertEqual(pilot.verify(ledger, observer, self.decision)["reason"], "receipt_mismatch")


if __name__ == "__main__":
    unittest.main()
