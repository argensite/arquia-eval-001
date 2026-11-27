# One decision commitment per run

A custodian that accepts two decisions under the same run ID lets the publisher choose which decision to disclose after receipt ingress. Both digests can predate ingress. [Brennan Zambo identified this gap and proposed the control](https://github.com/a2aproject/A2A/discussions/2434#discussioncomment-19951434).

This pilot accepts the first digest for an evaluator-issued run ID. The custodian refuses and records every subsequent attempt, including retries of the same digest. Acceptance and the attempt record are written in the same SQLite transaction. The verifier requires the disclosed bytes to match the accepted digest and checks the evaluator's observation order.

## Run the control locally

From the repository root with Python 3.10 or later:

```sh
python3 -B -m unittest -v experiments.custody_pilot.test_pilot
```

The double-submission control sends two distinct digests before the receipt is released. It passes when the first is accepted, the second is refused and logged, and the evaluator observes that refusal before release. The test also feeds the verifier a faulty record that accepts both. It must fail with `multiple_accepted_digests`. A missing rejection, a rejection after release and disclosure of the second decision are each checked separately. The local test uses a synthetic receipt and one operator.

## Run with a separate custodian

Use separate operator accounts, with no publisher write access to the evaluator's record or the custodian's database. The custodian accepts registrations only from the evaluator over a channel that authenticates their identity. Give the evaluator the custodian's acknowledgement and final export directly. The evaluator and custodian keep their original records under their own control. Run the reference and the double-submission control with fresh IDs.

1. **Evaluator.** Generate a fresh ID with `python3 -B -m experiments.custody_pilot.pilot issue` at the start of the run and give it to the custodian and publisher. Open the observation record for that ID.
2. **Custodian.** Run `python3 -B -m experiments.custody_pilot.pilot init ledger.db` in private storage once. Register each ID with `python3 -B -m experiments.custody_pilot.pilot register ledger.db "$run_id"`. Keep this database for the whole pilot and use `snapshot` to recover the acknowledgement after an uncertain submission.
3. **Publisher and custodian.** Compute the decision commitment with `python3 -B -m experiments.custody_pilot.pilot digest "$run_id" decision.json`. Give the digest to the custodian. The custodian runs `python3 -B -m experiments.custody_pilot.pilot submit ledger.db "$run_id" "$digest"` and returns the exact JSON event to the evaluator directly. Exit 0 means accepted. Exit 1 means rejected and recorded. In the double-submission control, submit a distinct second digest under the same ID and deliver that rejection to the evaluator before release.
4. **Evaluator.** Record the acknowledgement before releasing the controlled receipt. In the control also record the rejection before release. Record ingress for the same receipt and ID when observed. If you cannot establish the ordering, preserve the partial observations as inconclusive.
5. **Custodian and evaluator.** Export the ledger with `python3 -B -m experiments.custody_pilot.pilot snapshot ledger.db "$run_id" > ledger.json`. The evaluator selects this export, their own observations and the exact decision bytes, then runs:

```sh
python3 -B -m experiments.custody_pilot.pilot verify ledger.json observer.json decision.json
python3 -B -m experiments.custody_pilot.pilot verify ledger.json observer.json decision.json --rejected-digest "$second_digest"
```

Use the second command for the double-submission control. A pass has exit 0, a witnessed failure exit 1, invalid input exit 2 and an inconclusive observation exit 3.

The observer file has one run ID and an ordered list of events. The evaluator builds it from actual observations as they occur. For the control, insert `{"kind":"custody_rejection","attempt_sha256":"…"}` immediately after the acknowledgement.

```json
{
  "run_id": "<evaluator-issued ID>",
  "events": [
    {"kind":"decision_open"},
    {"kind":"custody_ack","ack_sha256":"<hash of the accepted event>"},
    {"kind":"receipt_released","receipt_sha256":"<hash of the receipt bytes released>"},
    {"kind":"receipt_ingress","receipt_sha256":"<hash of the receipt bytes observed>"}
  ]
}
```

Hash the acknowledgement and rejection with the repository's canonical JSON format. For example, from the root, `python3 -B -c 'from measurement import canonical, sha; from schemas import read_json; import sys; print(sha(canonical(read_json(sys.argv[1]))))' ack.json`. Publish the commands, exits, decision and receipt artifacts, ledger export, observations, and the roles and relationship of the operators. Synthetic data is sufficient.

The verifier checks consistency and declared observation order across inputs. Authentication of the exchanges, custody independence and the observation of ingress come from the operators' separate evidence. The pilot makes no claim about when an unobserved effect occurred. The earlier [eight-case fixture](https://github.com/argensite/arquia-eval-001/tree/c7575824b746863a631b7a561b78f4c99a19972f/experiments/brennan) covers additional history, receipt and authorization properties in simulation.
