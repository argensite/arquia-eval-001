# Constructing and sharing a counterexample

Choose one precise claim, e.g. “receipt evidence cannot revive a revoked grant.”
State its preconditions and expected behavior independently of the candidate.
Start from a copy of a community case in a **new** suite file; assign your own
stable ID/provenance. Keep historical cases unchanged. The schema requires the
problem, hypothesis, events, expected fields, invariants, evidence, limits and
reproduction command. `expect` must contain at least one known observation.

```sh
python3 community_runner.py --cases my-cases.json > my-result.json
python3 generate_cases.py --seed 42 --count 32 --output generated.json
python3 community_runner.py --cases generated.json > generated-result.json
python3 generate_cases.py --minimize suites/community-v1.json --case-id COMM-011 --fault rollback-authority --property observation_active_grants --output counterexample.json
```

The minimizer removes events only if the **same named violation** remains and no
protocol/execution error replaces it. It produces a 1-minimal sequence under
single-event deletion, not a proof of globally shortest length. Original expected
criteria, seed and original hash remain in the artifact. It does not tune the
expected output to the failing implementation. For a foreign candidate perform
the same reduction under explicit isolation and retain all receipts.

A useful negative result can also show a contract defect: an allowed unsafe
behavior, dishonest observation that escapes detection, or assumptions a real
system cannot meet. “No counterexample found” is not a universal proof.
Publish the full result under your control and optionally link it in an issue.
