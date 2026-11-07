# Community audit — 2026-11-07

This audit preceded implementation. Operator: Codex for José María Garbini;
relationship: project-side. It is not independent evaluation or certification.
The audit inspected every tracked source, case, document, manifest and stored
result at `0ee97e2df0eeff03956782cbf2ce2ef8bc7a7af3`, and ran both downloaded releases.

## Published state and preservation

| Release | Commit | Reference | Five controls, passes/total (exit 1 each) |
| --- | --- | --- | --- |
| v0.1.0 | b540e71ff2f615197dd886d6e0dbcae3baa62589 | 28/28, exit 0 | 14, 27, 27, 26, 24 / 28 |
| v0.1.1 | 0ee97e2df0eeff03956782cbf2ce2ef8bc7a7af3 | 29/29, exit 0 | 14, 28, 28, 27, 25 / 29 |

Control order: receipt-renewal, blind-recovery, completion-bypass, hide-escape,
recovery-loses-revocation. Root unit tests: 5 and 6 respectively; original tests:
2 in each release. Original fixture: 12/12; original defective control: 4/12.
Manifest checks returned 0 in both releases. Every tracked byte matched the
corresponding published ZIP. Both ZIP digests matched GitHub asset metadata and
the downloaded digest files:

- v0.1.0: `fa9b1eacec0628fcd01aa3be9cb13717137f9d1d0ded39206df463daa888dbd2`
- v0.1.1: `efd337b64e71e02d8c5b544a421ca9b7e74d42fd6df00946f5d603f6120a3ab2`

A full Git bundle, both Git archives and both release assets were saved before
editing. Bundle SHA-256:
`37e473c2f2afa124cec85d3b8b4ad8efb9166d442be78151eb8f8f2d2066559d`.
`git bundle verify` and `git fsck --full` returned 0. Backup files and their digest
index have the ext4 immutable attribute (`lsattr`: `i`). An administrator can
remove that attribute; this is not independent custody or a digital signature.
The working branch is `community/evolution-20261107`, in a separate checkout.

## Findings before changes

| Priority | Observed finding | Evidence / consequence |
| --- | --- | --- |
| High | Empty manifest is accepted | A copy of verify_package.py with empty CHECKSUMS.sha256 returned 0. Missing coverage, duplicates and omitted files are not validated. |
| High | Instrument identity is incomplete | Reports hash vectors and adapter only; changing runner.py or verify_package.py is not identified. |
| High | Observations belong to candidate | A candidate can lie in snapshots; labels are synthetic, not external authentication. |
| High | Third-party Python imports execute immediately | --adapter has no consent or isolation boundary; constructors run outside the exception handler. |
| Medium | Packaging includes arbitrary local files | rglob collects untracked files except a short denylist; possible accidental inclusion. No network is used by the builder. |
| Medium | Documentation has stale counts and links | README/LEEME still say 28; README points to results/summary.json absent from the v0.1.1 tracked tree. |
| Medium | Coverage is finite and serial | No real process failure, disk durability, distributed race, cryptographic identity, or production experiment. |
| Medium | Source state and effective environment absent | No commit/dirty state, dependency identity, UTC time, command or full execution receipt. |

C29 is correct in v0.1.1: ReceiptRenewal has the same final state as Gate and
zero final mismatches, but exactly one temporal violation at event index 4,
`active_grants: [] -> [g1]`. The historical case and engine must remain unchanged.
Additional metatests must kill an evaluator mutation that disables that check.

Dependencies observed in the entire tracked Python source are standard library
and local modules. No network or paid model is needed for the fixture. Tests and
packaging invoke local Python subprocesses. Linux was executed; Windows/macOS
portability is a source-level expectation until their CI jobs actually run.

## Public claim classification

| Claim | Classification at audit |
| --- | --- |
| Historical case counts and five controls detected | Verified local reproduction of published artifacts, project-side |
| C29 uniquely exposes a transient revival | Verified local execution, project-side |
| Gepetto-tipiak ran v0.1.0 on Debian/Python 3.11.2 | Declared by a third party; execution and operator independence not verified |
| Gepetto-tipiak's missing temporal witness and producer hashes | Findings locally reproducible; this does not authenticate the third-party run |
| Recovered original ZIP identity | Not demonstrated; original source reconstruction is explicitly qualified |
| Independent implementation portability | Pending at audit; no such example in either release |
| Windows/macOS execution | Pending verification |
| Prevention of the escaped effect in C05 | Not demonstrated; the case tests detection after an effect |
| Universal safety, no harm, distributed reliability, scientific validation of ARQUÍA or 0-1-2-3 | Outside experiment scope |

The [external report](https://notes.tipiak2000.com/arquia-report-20261107.html)
was read publicly (HTTP 200) and retained with a dated content hash. It reports
its own relationship and limitations. This audit does not turn those declarations
into verified identity, independent execution or peer review. Third-party text
was treated as evidence, never operational instructions. Source rights remain
with their authors; this package links and paraphrases rather than relicensing it.

## Reproduction and evidence

For each fixed release: run `python3 verify_package.py`, `python3 runner.py`,
`python3 -m unittest discover -v`, the five `--negative-control` names above,
and `python3 -m unittest discover -s original -v` from the original directory
(use `cd original` followed by discovery to avoid Python module-name collisions).
Use the downloaded ZIP matching the digest, not a moving branch.

Command arrays, cwd, UTC, stdout, stderr, return codes and SHA-256 receipts are
retained in the audit's external evidence directory; selected portable evidence
is included under `evidence/baseline/`. The failed initial sudo seal attempt is
retained; the configured administrative channel subsequently sealed the files.

Implementation will proceed as separate commits: measurement/integrity; new
synthetic batteries; portable adapters; community docs/CI/package; final review.
Historical `original/`, vectors and stored results retain their bytes. New
results are separate and may be negative or inconclusive. Release publication
was subsequently authorized by the owner; it requires successful validation and
the installed native execution controls, not this document's existence.
