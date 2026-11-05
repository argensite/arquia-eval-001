# Bring an independent implementation

Implement a class in an importable Python module, without inheriting `engine.Gate`
if you want to claim implementation independence. It must support:

```python
class Candidate:
    def __init__(self): ...
    def step(self, event: dict): ...
    def snapshot(self) -> dict: ...
    def export_state(self) -> dict: ...  # JSON-serializable complete checkpoint
    @classmethod
    def from_state(cls, checkpoint: dict): ...  # a newly constructed instance
```

Use the event contract in `PROTOCOL.md`. The snapshot contains the fields used in
`cases.json`, including counts, active grants, effects, outcomes, ordering and
incidents. Stable lists are sorted; IDs are case-sensitive. Avoid importing this
model to generate expected answers. Record a mapping if your representation differs.

Place `my_candidate.py` beside `runner.py`, then run:

```sh
python3 runner.py --adapter my_candidate:Candidate --evaluator YOUR_NAME > independent_result.json
python3 runner.py --adapter my_candidate:Candidate --cases my_cases.json > added_cases_result.json
```

The adapter is executable code, not inert input. Inspect it yourself and choose an
appropriate environment. The default experiment needs no network or credentials.
Do not point an adapter at production, real messaging, accounts or payments for
this evaluation. A different real-system study requires its own authorization,
sandbox, threat model and protocol.

A case is a JSON object with `id`, `description`, a nonempty `events` array and a
nonempty `expect` object. Keep added vectors in a separate file and commit their
expected outcomes before inspecting the candidate's output. Report original and
added cases separately. Exceptions are reported as failures, not swallowed.
