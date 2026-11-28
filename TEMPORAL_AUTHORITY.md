# Opt-in temporal authorization evaluation (`arquia.temporal/1`)

**Available as a separate deterministic community test, not as a live authorization service.** This extension adds a two-boundary synthetic evaluator without changing the historical `v0.1.0` tag, the 34 `community-v1` cases, or their JSONL response contract. Passing it **does not certify** AutoGen, ARQUÍA, production systems, cryptographic provenance, distribution, or hard real-time revocation.

## Run locally (Python 3.10+)

```sh
python3 temporal_runner.py --summary > temporal.json
python3 strict_unittest.py test_temporal_revocation
python3 temporal_runner.py --fault cache-per-turn --summary > stale-cache.json
```

The reference exits **0** if 3/3 pass. Each of seven named fault modes (`--fault`) must exit **1**, with explicit non-error violations. A setup/format failure exits **2**. Inspect `results[*].error` and `violations`; never interpret all nonzero statuses as successfully detected faults. Reports include the fixture and runner SHA-256 hashes and the evaluator's synthetic ledgers.

## What is observed

Each case declares one revocation contract **before execution**. The evaluator owns the logical permission version, operation dispatches, actuator-effect ledger, claims/receipts, world facts and pending-task state. In `REV-2CALL-HARD-STOP` two operations A and B are dispatched under permission v1, A crosses its effect boundary, v1 is revoked (v2), and B must not commit under v2. In `REV-2CALL-PREAUTHORIZED-FINISH` B may finish **only** under a v1 exception tied to an already-dispatched, in-flight B; this never grants fresh permission for C. In `REV-TURN-CACHE-NEGATIVE-CONTROL`, A dispatches under v1, v1 is revoked, and the same turn's second dispatch B must not reuse a turn-level cached grant.

For each dispatch, see `dispatch_ledger[*].permission_epoch_at_dispatch`, `authorized_at_dispatch`, `candidate_grant_version_read` and `candidate_authority_source`. For effect confirmation, see `effect_boundary_ledger[*].grant_version_at_dispatch`, `permission_version_at_effect_boundary`, `current_grant_valid_at_effect_boundary`, `preauthorized_finish_exception`, `effect_authorized_under_contract` and `effect_occurred`. The effect-boundary context exposes `revoked_grant` with the last revoked grant's ID (`grant`) and version (`epoch`), or `null` before any revocation. With no current grant, the exception requires that exact grant version to match the in-flight operation's original authorization, regardless of the gap between epochs or the operation's authorized scope. Unauthorized effects are **recorded, not erased**; detection alone is not prevention.

Both late receipts remain recorded. A receipt claiming an effect that did not occur is marked `unverified_claim`; a corroborated receipt proves only the historical synthetic effect, not a new grant. A `plan_step` must not advance or dispatch C using that receipt as permission, and `wake` must use fresh permission **and** world versions. Reconsideration of pending work never forces a dispatch.

## Run a candidate's own policy (Linux, isolation required)

The existing `JsonlCandidate` transport and Linux `bubblewrap` + systemd user service + verified cgroup v2 resource isolation are reused. The evaluator never imports or executes foreign candidate source in its own process. External code is **off by default**; there is no insecure fallback. See [ADAPTER.md](ADAPTER.md) and [SECURITY.md](SECURITY.md) before accepting external code.

```sh
python3 temporal_runner.py --candidate-dir examples/temporal --accept-external-code > temporal-example.json
```

This requires the host to meet the documented Linux containment preconditions, including a persistent TMPDIR. No installation or activation of that environment happens automatically. The project-shipped example is also exercised as trusted code in `test_temporal_revocation.py` for portable JSONL interoperability, but that test is **not evidence of containment**.

A candidate folder supplies `CANDIDATE.json` (`arquia.candidate/1`) with name/version, explicit source inventory and command. The transport sends **one JSONL request per active event**, with:

```json
{"protocol":"arquia.io/1","id":1,"event":{"op":"dispatch","operation":"A","turn":"T1","scope":"write"},"context":{"policy":"hard_stop","permission_epoch":1,"active_grant":{"epoch":1,"grant":"g-v1","scope":"write","allowed":["A","B","C"],"finish_after_revoke":false},"operations":{},"committed_effects":[],"operation_dispatch_epochs":{},"needed":{"C":true},"world_version":0},"checkpoint":{}}
```

The candidate must reply with the exact `arquia.io/1` envelope and candidate identity, using its `response` field for an operation-specific temporal decision and `checkpoint` for the next event. Example for this request:

```json
{"protocol":"arquia.io/1","id":1,"candidate":{"name":"temporal-conventional-example","version":"1"},"response":{"attempt_dispatch":true,"authority_source":"current_authority","grant_version_read":1},"checkpoint":{"receipts":{}}}
```

Event operations that call the candidate: `dispatch`, `effect_boundary`, `receipt`, `plan_step`, `wake`. Other events (`grant`, `revoke`, `world_update`) are issued by the trusted fixture and **must not cause candidate tool calls**. Decisions must have exactly the keys and primitive types defined in [`temporal_contract.py`](temporal_contract.py); invalid/unknown fields fail the case, not silently truncate it. The candidate is not given expected outputs, and actuator outcomes are tracked by the evaluator. Candidate state lives in the returned checkpoint, not an untracked process-global cache.

**Integration boundary for an actual AutoGen deployment:** wrap its permission check and tool dispatch in the protocol, then wrap the actuator's final effect commitment in `effect_boundary`; monitor planner transitions and wakeups. Run it only in an owner-authorized synthetic or staging environment. Merely executing this simulator does not instrument AutoGen; an independent evaluator must provide its own receipts and environment to claim an external reproduction.

## Historical integrity vs. live authorization

Brennan's immutable-record counterexample asks whether three historical facts remain distinct: decision without a receipt, later receipt arrival, and still-later receipt verification. A cryptographically stable final file does not retroactively make the receipt available at decision time. This suite tests a *different* error: a historically correct receipt or dispatch permit cannot authorize new effects after revocation. The two checks are complementary; neither proves the other.

## Scope and limitations

Deterministic serial interleavings, three public scenarios, seven deliberately defective policies, evaluator-owned synthetic ledger, and bounded JSON input/output only. No real concurrency, process-crash durability, transactional commits, network-attacker test, cryptographic witness, third-party attestation, production actuator or security certification. Explicit exceptions are synthetic policy choices, not generic permission to evade revocation.

**En español:** la prueba sirve para evaluar políticas antes de desplegarlas, no para habilitar operaciones productivas sin validación real. Se distingue permiso al despachar, permiso al confirmar y evidencia tardía. Preserva la batería histórica y puede correrse sin cuentas ni servicios pagos.
