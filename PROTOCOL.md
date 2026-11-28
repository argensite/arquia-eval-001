# Protocol and observable limits — community extension 1

For the separate **ARQUÍA-SEED-001** experiment, use the
[bilingual load/test/report guide](SEMILLA.md), [seed report template](SEED_REPORT_TEMPLATE.md)
and [existing issue #3](https://github.com/argensite/arquia-eval-001/issues/3).
Its 14 simulator tests and evidence categories are separate from the evaluator
contracts below; they do not validate the full 0-1-2-3 theory.

Two distinct protocols coexist. `runner.py` retains historical v0.1.1 vectors and
engine semantics, including C29. `community_runner.py` runs
`arquia.community-cases/1`; the schemas and cases are independently versioned.
Neither contract uses ARQUÍA affiliation or doctrine as an approval criterion.

## Historical contract

P1/P2 compare active grants, dispatches, completions and committed effects before
and after every receipt, timeout, cache-clear and recovery. P3 binds receipts to
an effect, grant version and request SHA-256. P4 retains uncertainty. P5 reports an
observed escaped effect. P6 bounds preauthorized completion to an already-started
effect. A receipt updates evidence, never authority. C29 must fail solely for its
step-4 transient active-grant revival, despite identical final states. A metatest
requires the historical regression to fail if the temporal detector is disabled.

`request_hash` is SHA-256 of UTF-8 JSON `[effect_id, request_string]`,
`ensure_ascii=False`, sorted keys, separators `(',', ':')`. Labels such as
`independent_observer` are synthetic assumptions, not signatures. Historical
snapshots still belong to the candidate. `original/` is unchanged; its original
archive identity remains unverified, as documented in PROVENANCE.

## Community contract

The evaluator owns the issuer, logical clock, synthetic actuator and append-only
per-case effect journal. The candidate receives JSON copies of an event and
current public authority/evidence facts; it never receives expected answers.
It returns proposed commands and its observed state. The evaluator compares
observations before executing commands, then records every modeled command,
including unauthorized commands. It does not silently repair faulty decisions.

- `authority_epoch` identifies an issuer's valid grant generation. A repeated or
  older grant cannot revive revocation. A new generation requires a verified
  synthetic issuer event. `evidence_sequence` orders evidence only.
- Grants bind an effect, scope, role, expiry, optional parent generation and
  delegation permission. Parent revocation invalidates delegated authority.
  Role changes invalidate old-role grants; returning to a role does not revive them.
- Logical expiry is exclusive: a grant with `expires_at=2` is invalid at time 2.
  Time cannot move backwards. This is serial logical order, not synchronized clocks.
- Dispatch creates one `unresolved` effect. Repeating it, recovering or receiving
  a timeout never retries it. Verified abort produces `aborted`; an observed
  commit produces `committed`. Unverified or contradictory claims change neither.
  Aborted IDs are not reused; another attempt requires a distinct effect/grant.
- A `start` may capture an explicitly preauthorized finish exception. It permits
  one completion after revocation, for that effect, scope and epoch only. It does
  not survive expiry, role replacement or a newer generation. It does not permit
  an unstarted effect. Its appropriateness remains an open contract question.
  For a delegated grant it excuses only revocation of that grant. Every ancestor
  must still be valid at its bound epoch, with matching scope/effect and delegation
  permission. Parent/ancestor revocation, expiry or replacement ends the exception.
- Compensation needs a separate new grant/effect. Detection of damage never grants
  permission to compensate automatically.
- Save/recover/restore reconstruct candidate state. The evaluator's authority and
  effect journal remain current, including tombstones. This models loss of a
  client cache; it does not demonstrate disk/fsync or real crash consistency.
  Derived-state revocation is tested at this modeled cache/restore boundary; influence erasure from training, fitting, weights, or other latent adaptation is not tested.
- Receipts and data cannot issue commands. Fake origin labels and malicious data
  are inert. `alternate_commit` is a deliberate synthetic bypass route; its effect
  is recorded and classified unauthorized. Unmodeled routes remain unobserved.

`external_commit` injects an effect after a dispatch. COMM-015 expects its escaped
effect to be reported: a matching result tests detection, **not prevention**.
A candidate that refuses valid work fails the positive-action cases. Declaring
no effects cannot erase the evaluator's journal. Observation independence is
limited to this synthetic boundary, not arbitrary hostile Python in the same
process. External candidates run behind the boundary described in SECURITY.

## Results and identity

Results conform to `schemas/result.schema.json`; measurement identity conforms
to `schemas/measurement.schema.json`. Each contains per-case events, violations,
errors, expected/observed fields, consequences and missing evidence; commands,
UTC, OS/architecture/Python, exact commit or archive declaration, dirty state,
local source hashes, loaded runtime files, effective selected environment,
configuration digest, measured duration and intended process exit.

`check_all.py` records the actual child exit and byte hashes of stdout/stderr.
`verify_report.py` checks the payload and supplied local source/case bytes without
executing the candidate. Runtime dependency hashes are recorded, not proof that
a different machine has the same runtime. Hashes are not signatures or proof of
truth, authorship or independence. A changed evaluator requires a changed identity.

Exit 0 means all tested contract assertions matched; 1 means a case failed;
invocation/input/isolation errors are nonzero, usually 2. Exceptions and timeouts
are failed/inconclusive evidence, never an approved or skipped case. No global
safety score is computed. Runtime is wall time, not a paid-service cost estimate.

## Falsifiability and nonclaims

Cases declare hypotheses/expectations independently of candidate outputs.
Generation records seeds; minimization retains a named violation and never
relabels an error as that violation. Its result is 1-minimal, not proven globally
shortest. Selected fault detection is not universal coverage or a statistical
sensitivity estimate. See SCOPE for theory, production and distributed nonclaims.
