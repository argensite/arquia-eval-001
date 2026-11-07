# Community implementation review — 2026-11-07

The initial audit is in [AUDIT_COMMUNITY](AUDIT_COMMUNITY.md). Changes were prepared
in a separate branch, `community/evolution-20261107`, through separate audit,
measurement, case-suite, interoperability, documentation/quality and final-review
commits. The native v0.1.2 commit was merged without rewriting either lineage.
No source in the frozen historical engine, case set or original draft was changed.
The root legacy result files and RSI_RELEASE.json remain v0.1.2 records; earlier
sets are retained under history/ and at their tags.

## Implemented and executed locally

- 29/29 historical cases, with C29 still the sole temporal-only witness for the
  receipt-renewal mutant; disabling the temporal detector breaks its regression.
- 34/34 separate community cases and 32/32 generated cases with seed 42.
- All five historical controls return the required exit 1. Their passes/29 are
  14, 28, 28, 27 and 25 in the documented order.
- Ten additional controls each have a non-error witness. Deny-all also has two
  inconclusive scenarios; neither is counted as a successful fault detection.
- 31 root unit tests, 2 original tests and 7 Linux isolation/resource tests pass. The
  standalone JSONL example passes all 34 cases, including actual isolated launch.
- Source identity, measurement/result schemas, tamper detection, input copying,
  strict errors, readable reports and the eight interpretation questions work.
- Repeated semantic results match. Two source builds are byte-identical; rebuilding
  from the extracted archive reproduces those same bytes. The explicit inventory
  excludes unrelated user files. A new regression fails by AssertionError on
  v0.1.2 and passes on the candidate, using the same test bytes.

[Pre-publication receipts](evidence/community-review/summary.json) identify the
local commands and their real exits and output hashes. This is project-side
execution by Codex, not an independent evaluation. Native release assets, when
published, supply their own execution JSON and evidence archive bound to the final
commit/ZIP. Do not substitute this pre-publication snapshot for those receipts.

## Remaining questions and limits

Windows/macOS and additional Python versions have a read-only CI matrix; only
actual job receipts establish their execution. Linux namespace checks demonstrate
specific restrictions, not a universally secure sandbox. Level 3 real-system
experiments remain a contract/authorization guide, not an implemented production
connector. All effects here are synthetic and serial; distributed races, durable
storage failures, cryptographic identities and unmodeled adversaries are untested.

The ordinary capability/ACL comparator passes the same community rules. This
establishes no incremental advantage unique to ARQUÍA. The example's implementation
is separate from the engine but its author/evaluator is project-side. External
claims and critiques retain their original provenance and unverified status.
There is no global safety score, certification or validation of broader theory.

Next useful evidence includes independently controlled implementations and runs,
new counterexamples against the declared assumptions, cross-platform CI receipts
and a separately authorized real-effect experiment. Negative findings have the
same preservation and review requirements as favorable ones.

## Compatibility and publication

The new protocol and schemas are versioned separately. Historical CLI controls
and report fields remain; arbitrary Python adapter import is deliberately blocked
before execution. [MIGRATION](MIGRATION.md) explains JSONL integration and the
remaining trusted in-process API. No historical release is reinterpreted.

The owner authorized publication and hourly native ChatGPT/Qwen RSI. Reviewed
installation tooling preserves the original commits, obtains authentic closed
advice, requires real Qwen execution and reruns acceptance on the final archive
before publication. A prepared candidate may start once on the owner's order;
autonomous successor proposals become eligible hourly, subject to the existing
FIFO and controls. Rejection, incomplete evidence and uncertain remote writes are
retained. An hourly eligibility check is not a promise of an hourly release.
The community versions remain publication candidates, not safety certifications.

## Adverse review and correction before publication

The initial candidate `a72b0e7` passed its 28-case suite but was rejected by the native ChatGPT review for a shared omission in the candidate, example and evaluator: a delegated finish exception could outlive its parent. The same omission was reproduced in five of six newly declared scenarios (four invalid completions and an undetected forced external effect). Three tests produced six assertion failures before correction and pass after it. The first 28 case objects remain identical; COMM-029 through COMM-034 extend the unpublished community suite to 34. The historical C29 is unchanged.

The prior passing snapshot remains in evidence/community-review/. It was insufficient evidence for this property. The [rejection](evidence/adverse-review/native-review-rejection.json), [failing result](evidence/adverse-review/rejected-parent-authority.stdout) and [before-test failures](evidence/adverse-review/parent-tests-before.stderr) are retained. Delegation-correction acceptance is in evidence/adverse-review/acceptance.json; subsequent resource acceptance is in evidence/adverse-review/resource-acceptance.json. This is project-side criticism and reproduction; it is not an external independent review.

## Second adverse review: aggregate resource boundary

The native review of b118f02 rejected per-process-only quotas. The new boundary uses an existing systemd user manager and cgroup v2; it reads kernel quotas before releasing the candidate, then checks complete group cleanup. Bounded probes that created 24 children and requested 320 MiB in two children failed the intended limits before the change. Afterward, the measured task ceiling is 16, memory exhaustion produces a failed execution with kernel OOM counters, and detached descendants are removed. The second rejection and before/after outputs are retained in evidence/adverse-review/. A first test exposed a sampling race that lost terminal OOM counters; a short trusted stop phase preserves the final observation. That failed test is retained too. No daemon or host quota is changed by the launcher. Basic portable runs do not require these Linux facilities.
