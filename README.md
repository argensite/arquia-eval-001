<!-- native-release -->
Current version: **v0.1.1**. See [release notes](RELEASE_NOTES.md) and [RSI evidence](RSI_RELEASE.json). Historical v0.1.0 remains available at its immutable commit/tag. Counts and results below that explicitly refer to v0.1.0 are historical. Current verified counts are in RSI_RELEASE.json. Project-side tests do not establish independent validation.
<!-- /native-release -->

# ARQUÍA-EVAL-001

**Late receipts, revoked authority, and escaped effects — v0.1.0**

A small, offline experiment for independent criticism and replication. A late
receipt may update evidence about an earlier action. It must not restore a
revoked grant, initiate another action, or conceal an effect that escaped after
revocation.

**Status: author-side simulation, externally unvalidated.** Passing these cases
means matching the stated model contract. It does not certify an agent, a live
system, the ARQUÍA architecture, or the philosophical 0-1-2-3 theory. This is a
standard kind of access-control question; we do not claim the invariant is unique
to ARQUÍA or that this example establishes scientific novelty.

## Run in a few seconds

Python 3.10 or later, standard library only. No installation, API keys, network,
models, paid services, or real-world actions are needed. Read the source before
running it. On systems where Python is named `python`, substitute that command.

```sh
python3 verify_package.py
python3 runner.py --evaluator YOUR_NAME > independent_result.json
python3 -m unittest -v test_contract
python3 runner.py --negative-control receipt-renewal > negative_result.json
```

The reference command should exit **0** and match **28/28** cases. The negative
control should exit **1** because its intentionally introduced bug is detected.
Four more negative controls are listed by `python3 runner.py --help`. A report
contains each event, observed state, mismatched fields, invariant violations,
Python version, and hashes of the vectors and adapter file. An error is a failure,
not a skipped or successful case.

`verify_package.py` checks file hashes against the supplied manifest. It does not
prove authorship or that the manifest is trustworthy; compare the archive digest
with the separate publication record. See [the protocol](PROTOCOL.md).

## What is being evaluated

The 28 fixed cases cover receipt/revocation ordering, renamed and duplicate
deliveries, wrong effect/version/request binding, self-reported success, unknown
outcomes, escaped effects, two-phase completion contracts, separate compensation
authority, and restoration into a new object through a serialized checkpoint.

The observer is simulated. Its `independent_observer` label is **not** real
authentication or evidence of third-party independence. JSON checkpoint restoration
is **not** a process-kill, durable-disk, distributed-consensus, or production test.
`ordering: undetermined` checks how missing ordering evidence is represented; it
does not create or solve a network partition.

In C05, a synthetic external effect commits after hard-stop revocation. The case
passes only when the violation is **reported**. The world in that case is still
unsafe: a green contract result must not be described as successful prevention.

## Independent evaluation

You control your conclusions and publication. No positive result, endorsement,
merge, or ARQUÍA approval is required. Negative and inconclusive results are useful.

1. Record the archive SHA-256, release tag and exact Git commit.
2. Run the unmodified cases and at least one negative control; retain complete
   output, command lines, exit codes, and environment information.
3. Challenge the contract and its assumptions, including which revocation
   semantics are meaningful. A model can consistently implement a wrong contract.
4. Add at least one case designed by you, or implement the contract independently.
   Describe the hypothesis and expected result before running the new experiment.
5. Publish the full report in a repository or venue you control. Link it in an
   issue here or in the originating discussion. State your relationship to ARQUÍA
   and whether a human, agent, or combination performed the work.

Use [REPORT_TEMPLATE.md](REPORT_TEMPLATE.md) and [ADAPTER.md](ADAPTER.md).
Re-running our code externally is replication of this fixture. An independently
implemented candidate or new falsifying case provides different evidence. Neither
automatically constitutes human academic peer review.

## Provenance and internal review

The [original example](original/) was recovered from visible code in the supplied
ChatGPT conversation. Its 12-case result and 8 detected failures in the original
negative control were reproduced. The original archive could not be downloaded;
we do not claim our reconstructed directory is a byte-identical copy of that ZIP.

Six additional cases exposed weaknesses in that original example. The amended
model and additional assertions are separate. See [AUDIT.md](AUDIT.md),
[PROVENANCE.md](PROVENANCE.md), and [author-side results](results/summary.json).
All preparation, revisions and runs in this release were performed on behalf of
the project owner with AI assistance (ChatGPT/Codex). They are not independent
review. The baseline is frozen for subsequent external testing; internal results
were already known when it was frozen, so this is not their preregistration.

## Discussion and attribution

This experiment follows the concrete objections and offer to test in the
[October 16 discussion on The Colony](https://thecolony.ai/post/a04d3184-c593-476d-91db-153531d0f79a).
Deep Seeker raised evidence provenance, compensation and replay binding;
ColonistOne raised timeout recovery, two-phase effects and timestamp semantics.
These contributions are credited in [PROVENANCE.md](PROVENANCE.md).

Project owner: José María Garbini. [ARQUÍA](https://arquia.live) is the originating
governance research project, not a certifying authority for this package.
The software and documentation authored for this package are available under the
[MIT license](LICENSE); linked third-party material retains its own terms.

Resumen en español: [LEEME.md](LEEME.md).
