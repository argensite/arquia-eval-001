# Protocol — version 0.1.0

## Question and falsifiers

Can an effect-scoped gate preserve revoked authority across receipt delivery and
serialized recovery, while retaining evidence of an already-dispatched effect?

The contract fails if any tested receipt, timeout, cache-clear or recovery changes
active grants, dispatch count, completion count or committed effects (P1/P2);
if an invalid binding confirms a different action (P3); if missing evidence becomes
success or permission (P4); if an observed post-revocation hard-stop violation is
hidden (P5); or if a completion exception authorizes an unstarted, different or
second effect (P6). Partial state assertions are in `cases.json`; P1/P2 are checked
after every passive event, so a temporary permission renewal cannot be hidden by
a later revocation.

P1/P2 checks are independent of the candidate's methods but depend on truthful
adapter snapshots. A dishonest adapter can lie; this harness is not a trusted
monitor of arbitrary real systems.

## Fixed assumptions

- Synthetic actions have unique logical effect IDs and grants. Grant IDs are never
  reused. A version belongs to one grant. No general-purpose capability is modeled.
- An authoritative, correct grant store and serial event order are assumed. The
  candidate and simulated observer inhabit one process. There is no real signature,
  quorum, hostile writer, network transport or enforcement at a remote endpoint.
- A request binding is SHA-256 of UTF-8 JSON `[effect_id, request_string]` with
  `ensure_ascii=False`, sorted keys and separators `(',', ':')`. This is binding
  within the fixture, not proof of who authorized the request. Version and grant
  also form the receipt's logical deduplication key.
- Accepted receipt IDs bind to one logical observation. Alternate delivery IDs do
  not create another observation. Invalid/untrusted evidence cannot consume the
  key of a later valid observation. Historical incidents remain visible.
- `source: independent_observer` designates a trusted **simulated** actor. An
  attacker who can choose this label is outside the trust model. The model also
  requires a synthetic committed effect before accepting success evidence.

## Events and interpretation

| Event | Meaning |
| --- | --- |
| `grant` | Issuer authorizes one effect and request, with an explicit completion policy. |
| `dispatch` / `start` | A logical attempt / first phase starts, once, under active authority. |
| `timeout` | Missing acknowledgement; no proof of success or failure; no retry. |
| `revoke` | No further starts under that grant. The first revocation position is retained. |
| `external_commit` | Test observer injects a synthetic external effect outside gate control. |
| `receipt` | Evidence can update a record; cannot authorize or perform an action. |
| `complete` | Explicit local second phase; at most once for a previously started effect. |
| `clear_client_cache` / `recover` | Runner serializes state to JSON and constructs a fresh candidate instance. No effect is executed. |

Default `finish_after_revoke=false` is a hard-stop contract for future completion.
`true` is a different grant contract: the issuer preauthorizes one bounded
completion of an already-started effect after revocation of new starts. It does
not promise that every human revocation can be overridden, and it cannot be added
after the fact. Its suitability is an explicit question for reviewers.

An external commit after hard-stop revocation yields
`escaped_effect_after_revocation`. The test cannot undo it or prove prevention.
When ordering is explicitly unavailable, `execution_order=undetermined` and
`execution_order_undetermined` remain visible, even if existence is confirmed.
No comparison of real clocks is performed. Automatic compensation is not
implemented: a compensating dispatch needs a separate new grant (C20).

Confirmation refers only to the synthetic observer or local model. The word
`committed` in a snapshot describes simulated world state, not remote delivery.

## Execution, comparison and external extensions

Default candidate: `engine:Gate`. Additional candidates implement `step`,
`snapshot`, `export_state`, and `from_state`. See `ADAPTER.md`. `--cases` accepts
a reviewer-owned JSON file with the same schema. Use a different file for added
cases; retain the original vectors and report their results separately.

Record the exact commit/archive hash before execution. Keep stdout, stderr,
commands, exit status, runtime and all changed source files. Runner records only
the adapter entry file hash; reviewers must also record dependent source and
environment hashes. Adapter code is executed as normal Python and is not sandboxed
by this runner. Running the supplied default needs no extra packages or network.

Five deliberate faults test different detection paths: receipt renewal, blind
retry, unauthorized completion, hidden escaped effect, and lost revocation during
reconstruction. Each must fail at least one case. Detecting these faults is a
sensitivity check for selected bugs, not a measured rate of detecting all bugs.

## Independence and publication

An external report should declare who operated the test, their relationship to
the author/project, and any assistance or compensation. A separate account alone
does not establish independence; the report must be controlled by the evaluator.
The project will distinguish an invitation, acceptance, self-reported execution,
checkable reproduction, new counterexample, independent implementation and formal
peer review. None can be inferred from the previous stage. Silence is no result.

The evaluator is free to publish failures, limitations or rejection of the
contract without author approval. Prefer an independently controlled repository
or permanent publication, with an optional link from our issue tracker. Do not
put secrets, personal data or production receipts in a report.

Internal author-side results precede this freeze. This release is a prospective
baseline for external runs, not a retroactive preregistration. Any later code or
expectation change gets a new version; preserve earlier reports and hashes.

## Explicitly outside the evidence

Distributed races or partitions, cryptographic authenticity, Byzantine witnesses,
crash consistency/fsync, real process failure, actual database recovery, live
agents, external services, human harm, ethical validity, universal safety, and
the full ARQUÍA framework. No statistical population or causal estimate is made.
The finite vectors are examples, not exhaustive state-space verification.

Priority external challenges: define a two-replica revocation/commit race with a
real ordering witness; replace the candidate with an independent implementation;
show a sequence that satisfies these assertions while violating the intended
contract; or explain why the revocation/finish distinction is unacceptable.
