# Provenance and contributions

Preparation date: 2026-11-05. Project owner: José María Garbini.
Implementation and documentation prepared with ChatGPT/Codex assistance.
All included runs are project-side work, not independent evaluation.

The initiating [shared conversation](https://chatgpt.com/share/6aec9898-3ac4-83ea-bd1a-224603c990f0)
proposed 12 cases and a deliberate receipt-renewal fault. The download control
did not yield an archive during this review. The visible Python tool cells
contained the model, vector declarations, runner and two tests. These were
transcribed into `original/`; the original model, runner, test and generated
case file match the displayed byte sizes (5029, 1154, 562 and 9724 respectively).
Matching sizes are not a cryptographic identity proof.

The chat displayed an original ZIP digest
`dda4ab9577b30f946cdcad00c6524a119c0a2215bdd3c2677e0b2a9b34ce9c89`.
We did not retrieve that ZIP and have not verified that digest. Our release has
its own manifest, archive digest and Git commit. Original prose and ZIP metadata
were not reconstructed as if recovered files. `original/reconstruct_cases.py`
preserves the visible vector declarations with a local output wrapper.

The 12-case pass and 8/12 detected negative-control failures were reproduced
locally. Additional findings are described in `AUDIT.md`. Version 0.1.0 includes
16 additional author-side cases, explicit request hashes, semantic receipt
deduplication, evidence monotonicity, a serialized-state adapter contract,
uncertain ordering and additional negative controls. These are revisions, not
claims about the original package or production ARQUÍA software.

## Public discussion that motivated the test

- [Deep Seeker's critique and offer to execute a fixture](https://thecolony.ai/comment/cae738d1-6236-4187-8a34-485f62b88781):
  self-witness limitations, ordering, separate compensation authority and replay
  binding. The offer was read directly; execution has not been inferred from it.
- [ColonistOne's cases](https://thecolony.ai/comment/f55e8cac-ad8b-40c3-8835-3143da4e8eeb):
  unknown timeout outcomes, two-phase completion, and what timestamp events mean.
- [ColonistOne on a pending effect](https://thecolony.ai/comment/db323c43-edfc-45d5-ac2f-e6a9f8f35bed):
  lost creation response and unavailable completion token.
- [ARQUÍA's explicit completion-contract distinction](https://thecolony.ai/comment/ce1a89a0-e93a-475e-bf0b-14eea3266b2e).
- [ARQUÍA's authority/effect commit boundary](https://thecolony.ai/comment/65205d07-6b9b-4f8a-b5db-01aa4ef44b36).

These links credit public contributions; they do not imply endorsement, verified
human identity, independence of account operators, academic credentials or
completed peer review. We have not republished the participants' full comments.
