# Late receipts and decision-time knowledge

Brennan Zambo identified two failures in the [original A2A counterexample](https://github.com/a2aproject/A2A/discussions/2434#discussioncomment-19707087) and his [follow-up on chronology](https://github.com/a2aproject/A2A/discussions/2434#discussioncomment-19870471). A consumer can keep a grant revoked and still rewrite what it recorded at decision time. A second consumer can present all the right entries and rebuild every hash link after receipt arrival. A backdated commitment from the publisher adds no independent evidence about the order. See also [AER-1 draft-26, §7.3 and §10](https://datatracker.ietf.org/doc/html/draft-zambo-aer1-26).

This separate ARQUÍA experiment keeps the original decision at `absent`, appends receipt arrival as `not checked`, and appends `verified` after computing the hash of the saved result bytes. The follow-up action B stays blocked under the revoked grant. [The historical battery](../../PROTOCOL.md) and [temporal revocation suite](../../TEMPORAL_AUTHORITY.md) already test whether late receipts can restore authority and whether escaped effects remain visible. They do not test whether those three historical entries survive or whether a decision commitment predates receipt ingress. The experiment reuses the repository's canonical JSON and SHA-256 helpers. It runs outside the versioned distribution inventory.

## Reproduce

From the repository root at the pinned commit, use Python 3.10+ and Git. The experiment uses only the Python standard library. Tests need no network, credentials, paid API, real actuator or installed AER-1 implementation. Fetch the repository and tags before going offline.

```sh
python3 -B -m experiments.brennan.reproduce ../brennan-run --regression
```

Use a new output directory each time. The command launches each simulator and evidence verifier separately, preserves stdout and stderr, checks their actual return codes against the matrix, and writes `summary.json`. Omit `--regression` to run only the new cases. On Linux with unprivileged user namespaces you can run the same command with `unshare -Urn` at the front to remove network access.

To run a single case or inspect a published pair of evidence files:

```sh
python3 -B -m experiments.brennan.simulate publisher-only ../publisher-only
python3 -B -m experiments.brennan.verify ../publisher-only/publisher.json ../publisher-only/observer.json
```

Both commands should exit **1** for this case and return `publisher_controlled_witness` in JSON. Substitute another scenario name or archived file pair to check it independently of the simulator. An exit of **0** means all checks passed, **1** means a reported property violation, and **2** means a setup or input error. A detected control must match its expected violation, not just return a nonzero code.

| Scenario | Exit | Expected observations |
| --- | ---: | --- |
| `reference` | 0 | Three entries survive, bytes verify and B stays blocked. The observer records the decision digest before receipt ingress. |
| `rewrite` | 1 | The decision is overwritten with `verified`. B remains blocked, bytes verify and rebuilt links validate. The decision fails the history check and no longer matches the digest captured by the observer. |
| `publisher-only` | 1 | The complete rebuilt journal matches the reference byte for byte. The publisher supplies a commitment with an early claimed position. The observer has no decision commitment in its journal. |
| `missing-commitment` | 1 | The reference journal survives intact. There is no commitment. |
| `late-commitment` | 1 | The reference journal survives intact. A matching commitment in the observer's journal first appears after receipt ingress. |
| `collapsed-history` | 1 | A single overwritten decision field replaces the three distinct entries. |
| `corrupt-output` | 1 | The original decision and its prior commitment survive. The presented result bytes do not match the receipt. |
| `renewal` | 1 | History, receipt bytes and the prior commitment all check out. The late receipt wrongly restores permission for B. |

The regression also executes `check_all.py` from this branch, including the existing historical, community and temporal suites and their controls. It reruns the package, contract tests, reference battery and five negative controls from each frozen Git tag `v0.1.0`, `v0.1.1` and `v0.1.2`. The frozen reference totals are 28, 29 and 29 respectively. The inherited tests use shipped synthetic code only.

## What the observer establishes

The simulator controls the decision stimulus and receipt ingress. It puts the decision commitment in an evaluator-held observation sequence while the decision window is open. Only the fixture can write this sequence during simulation. The verifier takes it as a separate input selected by the evaluator and checks for the exact decision link digest between those two observed boundaries. The publisher's journal carries the original entry and its prior-link digest. Its own timestamp, claimed position or witness is insufficient for the ordering check. The three chronology negatives keep the exact same journal as the reference so the difference comes solely from the commitment evidence.

The ordering conclusion is conditional on the evaluator's simulated observations. These JSON files have no independent signature, publication time or external custodian. Someone who can replace the observer file can forge the simulation evidence as well. A real test would need an out-of-band trusted source that publicly or independently records the digest before arrival, plus an independently observed ingress or a trustworthy shared ordering for both events. A verified commitment bounds when the entry already existed. It gives no authority to trust a clock value inside the entry. Receipt integrity establishes which bytes match the commitment. Neither the receipt nor its log placement establishes when an unobserved actuator effect occurred.

The author-side run tests this fixture. An AER-1 implementation can reproduce the three entry states, substitute its own independently held commitments, and report any agreement, disagreement or inconclusive case. Independent replication is pending.
