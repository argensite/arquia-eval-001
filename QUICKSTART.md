# Quickstart / Primera ejecución

Download and extract a fixed release. Compare its ZIP SHA-256 with the publication
record. Python 3.10+ is the only requirement for reference, examples and checks.
All commands below run offline. Execute from the extracted package directory.

## Linux and macOS

```sh
python3 verify_package.py
python3 runner.py --evaluator YOUR_NAME --relationship unspecified > historical.json
python3 community_runner.py --markdown community.md > community.json
python3 community_runner.py --example-jsonl > example.json
python3 verify_report.py historical.json --cases cases.json
python3 verify_report.py community.json --cases suites/community-v1.json
python3 render_report.py historical.json --output historical.md
python3 check_all.py --output checks
```

## Windows PowerShell

```powershell
py -3 verify_package.py
py -3 runner.py --evaluator YOUR_NAME --relationship unspecified | Out-File -Encoding utf8 historical.json
py -3 community_runner.py --markdown community.md | Out-File -Encoding utf8 community.json
py -3 community_runner.py --example-jsonl | Out-File -Encoding utf8 example.json
py -3 verify_report.py historical.json --cases cases.json
py -3 verify_report.py community.json --cases suites/community-v1.json
py -3 render_report.py historical.json --output historical.md
py -3 check_all.py --output checks
```

Report readers accept UTF-8 with or without BOM. Avoid UTF-16 redirection in older
PowerShell. `check_all.py` captures child bytes directly and creates complete
stdout/stderr/exit receipts, independent of shell redirection.

Reference commands return 0. Historical reference: 29/29; community: 28/28.
A failing candidate returns 1. Invalid invocation/isolation unavailable returns
nonzero; no run is inferred. To see a deliberate fault:

```sh
python3 runner.py --negative-control receipt-renewal > negative.json
```

Expected exit is **1**, 14/29 historical cases match. All five controls are checked
by `check_all.py`; do not invert every nonzero exit into a successful detection.

## Own cases and package

```sh
python3 generate_cases.py --seed 42 --count 32 --output generated.json
python3 community_runner.py --cases generated.json > generated-result.json
python3 build_release.py --output dist
```

Use a fresh output filename for generated cases. The builder uses an explicit
inventory and never sweeps untracked files or regenerates historical reports.
Two builds from the same source identity must have identical ZIP bytes. Runtime
measurements contain timestamps and duration and are compared semantically.

Optional external execution on Linux needs existing `bwrap`, `findmnt`, a systemd user manager and delegated cgroup v2:

```sh
python3 community_runner.py --candidate-dir examples --accept-external-code > isolated.json
python3 -m unittest -v isolation_checks resource_checks
```

For this host's isolation checks, TMPDIR must point to persistent disk, not tmpfs.
No dependencies are installed automatically. See ADAPTER and SECURITY for the
boundary actually enforced and the limits. Windows/macOS can run the reference
and shipped example; arbitrary external code is refused there by this launcher.
