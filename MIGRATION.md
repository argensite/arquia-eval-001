# Migrating from v0.1.x

Historical `cases.json`, `engine.py`, `original/`, C29 and published results retain
their bytes. `runner.py` keeps its reference and five negative-control CLI options,
exit meanings and existing report fields; it adds a versioned measurement object.
Historical v0.1.0/v0.1.1 tags and ZIPs remain available without reinterpretation.

Security change: importing arbitrary `--adapter module:Class` in the CLI is now
rejected **before import**. Use the JSONL contract and candidate manifest with
explicit isolated execution. Trusted Python callers can still call `evaluate`,
but that library API is not a sandbox. The historical external-import unit test
is replaced by an import-denial regression in this branch; its old bytes remain
in the historic Git commits.

Community events have a separate schema: `authority_epoch` is not a receipt
sequence, outcomes are `committed`, `aborted`, `unresolved`, and the evaluator owns
effects. Do not silently translate historical `unknown` into verified failure or
relabel historical candidate snapshots as independent observations.

Package builds use `PACKAGE_FILES.json` and source identity. They no longer
regenerate or overwrite historical author reports or attribute a user's run to
Qwen. Reports include variable UTC/runtime metadata: compare case semantics for
repeatability; compare ZIP bytes for package reproducibility.
