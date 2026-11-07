# Portable candidate integration

Level 1: `python3 runner.py` and `python3 community_runner.py` need only Python.
Level 2: implement the JSONL contract below in any language. The standalone
`examples/independent_candidate.py` has no imports from the engine or evaluator.
Level 3: a real-system experiment requires its own authorized isolated environment,
threat model, effect boundary and protocol; this release does not implement it.

## One request, one response, one process

UTF-8 JSONL, exactly one object and final LF on stdin and stdout. Maximum 256 KiB
per message, 64 KiB stderr, 8 commands per response, 2 seconds per process. The
launcher starts a new process per event and carries the returned JSON checkpoint.
It never repeats an uncertain call. No unsolicited output or extra stdout lines.

Request (`schemas/request.schema.json`):

```json
{"protocol":"arquia.io/1","id":1,"event":{"op":"timeout"},"context":{"grants":{},"effects":{},"clock":0,"role":"operator","evidence_sequence":0,"incidents":[]},"checkpoint":{}}
```

Response (`schemas/response.schema.json`):

```json
{"protocol":"arquia.io/1","id":1,"candidate":{"name":"independent-conventional","version":"1"},"response":{"commands":[],"observed":{"active_grants":[],"outcomes":{},"incidents":[]}},"checkpoint":{}}
```

Echo the request ID and protocol exactly. `observed` describes **pre-command**
state, derived from available facts. `commands` contains `dispatch`, `complete`
or the deliberate fault route `alternate_commit`, with `grant`, `effect`, integer
`authority_epoch`, `scope`, and optional `phase` (`dispatch` or `start`). Stable
lists are sorted. `context.grants/effects` use the fields in PROTOCOL and the
complete example. Requests never carry expected case answers.

The candidate directory needs `CANDIDATE.json`: schema `arquia.candidate/1`,
name/version, an explicit relative `files` array, and a command array (no shell).
See the example manifest. Executable paths are `/usr/bin/...` or `/candidate/...`;
only inventoried files are copied into the read-only candidate mount. Maximum
128 files and 8 MiB. No symlinks or traversal paths. Candidate source/manifest
hashes, commands, responses, stdout/stderr and exit codes are retained.

```sh
python3 community_runner.py --example-jsonl > example.json
python3 community_runner.py --candidate-dir examples --accept-external-code > isolated.json
```

The second command requires Linux, existing bubblewrap/findmnt, a systemd user manager with delegated cgroup v2,
and a persistent TMPDIR. External execution is off by default and refuses unavailable isolation.
The first executes only the project-shipped example, not an isolation claim.
For other languages put your standalone executable or script/runtime command in
the manifest. Runtime binaries must exist inside `/usr`; no downloads occur.

Malformed/oversized output, unknown operations, identity mismatch, changed source,
nonzero exit and timeout fail the case or reject setup. A timeout is not a pass
and is not retried. Checkpoint recovery does not erase the evaluator's ledger.
On Windows/macOS use the shipped example for protocol development or a separately
authorized Linux environment for foreign code; no insecure fallback is provided.

The old Python `--adapter module:Class` CLI is disabled before import. Trusted
in-process `evaluate` remains a library API with the caller's own isolation
responsibility. Read MIGRATION before adapting a v0.1.x plugin.

External runs additionally verify aggregate resource limits before releasing the
payload, and record cleanup even after failure; see SECURITY. No systemd daemon
is started or configured implicitly by the launcher. Output hashes identify the
retained bounded prefix, with explicit truncation flags. The last transport record
is preserved even when malformed output, timeout or resource termination fails a case.

The external payload has no writable regular filesystem. Use the JSON checkpoint
for state; runtimes that require a disk cache need a separately authorized Level 3
environment. The host stores bounded transport receipts on persistent storage.
