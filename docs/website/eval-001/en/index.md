# ARQUÍA-EVAL-001

[Guía en español](../index.md) · [JSON manifest](../manifest.json)

## Choose a version to run

- [Stable v0.1.2](https://github.com/argensite/arquia-eval-001/releases/tag/v0.1.2) · 29 historical cases and five faulty controls. The commands on this page apply to this download.
- [Public v0.2.3 pre-release](https://github.com/argensite/arquia-eval-001/releases/tag/v0.2.3) · retains the 29 historical cases and adds a separate suite of 34 community cases and ten controls. Follow the [versioned Quickstart](https://github.com/argensite/arquia-eval-001/blob/69274389ab5dfe5b0f3d2b0b2f6983dfa3d9f261/QUICKSTART.md).
- [v0.2.4 development](https://github.com/argensite/arquia-eval-001/tree/main) · adds three opt-in temporal scenarios and seven controls. Publication of the release ZIP is pending.
- [Frozen historical v0.1.0](https://github.com/argensite/arquia-eval-001/releases/tag/v0.1.0) · 28 cases and five controls. Report results with its original version and digest.

## Run v0.1.2

[Download the stable ZIP](https://github.com/argensite/arquia-eval-001/releases/download/v0.1.2/ARQUIA-EVAL-001-v0.1.2.zip).
Commit `49e339f0d57c3794b68e12caa53feabe8ad7710c`.
SHA-256 `dded386309f21f53ec43199944767002a7f56afa42c0717b96443afe9dca540a`.

Compare the SHA-256 against the release before extracting to a fresh directory.
Review the code and protocol. Running uses Python 3.10+ and its standard
library, offline without keys or services.

```sh
python3 verify_package.py
python3 runner.py --evaluator YOUR_NAME > independent_result.json
python3 -m unittest -v test_contract
python3 runner.py --negative-control receipt-renewal > negative_result.json
```

The verifier, unit suite and reference exit 0. The reference matches 29/29.
The control exits 1 and reports `C29-transient-receipt-renewal` with
`error: null`, `mismatches: {}`, and the `P1/P2-passive-event` violation on
`active_grants` at the receipt. The project adapted this case in v0.1.1 from
[Gepetto-tipiak’s critique and example](https://notes.tipiak2000.com/arquia-report-20261107.html).
v0.1.2 added runner and available verifier digests to the report.

Keep the version, digest, environment, commands, full outputs and exit codes.
Publish under your control, state your relationship to the project and link
your report in the [open call](https://github.com/argensite/arquia-eval-001/issues/1).
Negative results, inconclusive results and contract criticism are welcome.
The scope is a synthetic revocation and late-receipt contract.
