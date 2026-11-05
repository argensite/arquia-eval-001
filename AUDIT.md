# Internal review of the recovered draft

The original reference matches 12/12 original cases; its deliberate fault fails
8/12. These are reproduced results from a bounded, author-prepared example.

Six added cases expose behavior not covered by that original suite. The assertions
are proposed improvements and may themselves be challenged by outside reviewers.

| Added case | Behavior in recovered original | Change in v0.1.0 |
| --- | --- | --- |
| C14 | Executor claim consumes receipt ID, suppressing later valid evidence. | Untrusted evidence cannot reserve a valid observation's key. |
| C15 | A self-report overwrites a previously confirmed outcome. | Keep stronger evidence; count the unverified claim separately. |
| C16 | Changing receipt ID bypasses the duplicate-observation count. | Deduplicate by grant, effect, version and request hash. No duplicate real dispatch was demonstrated in the original by this case. |
| C23 | A permitted finish observed externally is called an escaped violation. | Apply the original grant's explicit phase completion semantics. |
| C25 | An inconsistent observer claim consumes the later valid observation's ID. | Retain the incident, accept subsequent corroborated evidence. |
| C28 | Wrong effect binding consumes the later correct receipt's ID. | Validate binding before accepting the identity. |

The original `clear_client_cache` and `recover` handlers were no-ops. v0.1.0's
runner performs a JSON round trip and instantiates a new object. That tests
serialization semantics only, not real disk durability or crash recovery.

The original observer and order were idealized. They remain synthetic here;
unavailable order can now be represented explicitly. No distributed algorithm,
cryptographic verification or production enforcement has been added.

The original runner checked selected final fields. The new runner also tests the
passive-event invariant after every event and supports external adapters/cases.
This increases coverage of selected faults; it does not make the finite suite
complete, independent, or scientifically validated.

Machine-readable original and revised results are in `results/`. No production
queues, permissions, agents, credentials, or published historical content were
changed by the experiment.
