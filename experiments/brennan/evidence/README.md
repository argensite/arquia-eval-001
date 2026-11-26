# Observed run

ARQUÍA project-side run on 2026-11-26. The execution used a clean checkout of [commit `c7575824b746863a631b7a561b78f4c99a19972f`](https://github.com/argensite/arquia-eval-001/commit/c7575824b746863a631b7a561b78f4c99a19972f). See the [test instructions](https://github.com/argensite/arquia-eval-001/blob/c7575824b746863a631b7a561b78f4c99a19972f/experiments/brennan/README.md) for the expected matrix and trust boundary.

```sh
git clone https://github.com/argensite/arquia-eval-001.git arquia-brennan
cd arquia-brennan
git checkout --detach c7575824b746863a631b7a561b78f4c99a19972f
unshare -Urn python3 -B -m experiments.brennan.reproduce ../brennan-run --regression
```

The recorded Linux run used CPython 3.14.4, Git 2.53.0 and Ubuntu 26.04.1 LTS on x86-64 (kernel 7.0.0-44-generic). It ran in a new Linux user, mount and network namespace created with `unshare -Urnm`. The only network interface was [loopback](network-interfaces.txt). The checkout and output directories were exposed at `/mnt` inside that mount namespace. This was the command inside it:

```sh
cd /mnt/clean-source
env -i PATH=/usr/bin:/bin TMPDIR=/mnt/tmp LC_ALL=C.UTF-8 PYTHONDONTWRITEBYTECODE=1 \
  python3 -B -m experiments.brennan.reproduce /mnt/observed --regression
```

The command [exited 0](reproduce.exit) and [reported eight matching outcomes](reproduce.stdout). The [summary](summary.json) records the full command lines, expected and actual exit codes, verifier reasons and output hashes. Each scenario in [cases](cases/) contains the publisher trace, observer input, and both processes' stdout and stderr. For a direct inspection, compare [the reference observer sequence](cases/reference/trace/observer.json), [the publisher-only claim](cases/publisher-only/trace/publisher.json) and [the late-commitment observer sequence](cases/late-commitment/trace/observer.json). The three chronology controls contain the exact reference journal and still fail the prior-commitment check. In the rewrite case the receipt bytes and rebuilt chain still verify, and B stays blocked. The overwritten decision fails the three-entry check and disagrees with the original commitment.

The current regression passed 29/29 historical, 34/34 community and 3/3 temporal reference cases. It detected all 5, 10 and 7 injected faults in those respective suites with observed violations. The inherited community `deny-all` control also recorded three inconclusive case results, alongside 18 cases demonstrating violations. The frozen references passed 28/28, 29/29 and 29/29 for `v0.1.0`, `v0.1.1` and `v0.1.2` respectively, and each detected five controls. The original reconstructed example passed 12/12, and its negative control failed eight of twelve. See the [current regression summary](current-regression.json) and [raw regression logs](regression-logs.tar.gz) with [SHA-256](regression-logs.sha256). The wall times, runtime details and output paths in historical command receipts can vary on rerun.

The observer sequence models a fixture-controlled witness and ingress marker. Neither has an independent operator or external publication timestamp. An external verifier can recompute the hashes and rerun these scenarios. Independent reproduction and a test with a real external witness remain pending.
