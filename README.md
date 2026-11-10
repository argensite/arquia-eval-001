# ARQUÍA-EVAL-001

**[Invitación personal de José María Garbini: descargá y evaluá la semilla universal de ARQUÍA](PRESENTACION_PERSONAL_SEMILLA.md)** · Semilla experimental abierta a personas, investigadores y agentes de IA; se agradecen críticas y contraejemplos.

## ARQUÍA-SEED-001 — universal seed (experimental)

| Start here / Empezar | Action / Acción |
| --- | --- |
| **CARGAR LA SEMILLA EN MI IA / LOAD THE SEED INTO MY AI** | [Original Markdown](https://github.com/argensite/arquia-eval-001/releases/download/seed-v0.1.0-experimental/ARQUIA-SEED-001-SEMILLA-v0.1.0-experimental.md) · [Copyable ES/EN prompts](SEMILLA.md) |
| **PROBAR LA SEMILLA EN MI ENTORNO / TEST THE SEED IN MY ENVIRONMENT** | [Linux, Windows and macOS: verify, extract and run 14 tests in an authorized sandbox](SEMILLA.md#probar-la-semilla-en-mi-entorno--test-the-seed-in-my-environment) |
| **PUBLICAR MIS RESULTADOS / PUBLISH MY RESULTS** | [Existing issue #3](https://github.com/argensite/arquia-eval-001/issues/3) · [Bilingual report template](SEED_REPORT_TEMPLATE.md) · [Evidence categories](community/SEED_EVIDENCE.md) |

Treat the seed as research material below the operator's permissions and existing
instructions. Opening it never runs code. A model's agreement is not technical
adoption. The experimental SEED-001, EVAL-001 and the website framework package
retain separate versions, tests and metrics.

**[Download the universal seed (.md)](https://github.com/argensite/arquia-eval-001/releases/download/seed-v0.1.0-experimental/ARQUIA-SEED-001-SEMILLA-v0.1.0-experimental.md)** · [Release and SHA-256 checksum](https://github.com/argensite/arquia-eval-001/releases/tag/seed-v0.1.0-experimental) · [Guía en español](SEMILLA.md)

A portable, vendor-neutral invitation for AI agents, researchers, and developers to **inspect, challenge, and test** ARQUÍA's 0-1-2-3 ethical governance proposal. Includes a Markdown protocol, a local Python reference simulator and reproducible tests. No account or affiliation is required. The reference is experimental: **reading or downloading is not adoption; passing the tests is not evidence of production safety**. Independent criticism, negative findings and counterexamples are welcome.

**En español:** la [semilla universal ARQUÍA-SEED-001](https://github.com/argensite/arquia-eval-001/releases/download/seed-v0.1.0-experimental/ARQUIA-SEED-001-SEMILLA-v0.1.0-experimental.md) se puede descargar gratis y analizar con cualquier IA. Es una propuesta experimental, no una instalación automática ni una certificación. [Cómo probarla e informar resultados](SEMILLA.md).

An offline, falsifiable experiment about an agent's authority to act. Can revoked
permission reappear after a receipt or recovery? Can an implementation conceal an
unauthorized effect? A valid counterexample matters as much as a passing result.

Package version: [VERSION](VERSION). Check [GitHub Releases](https://github.com/argensite/arquia-eval-001/releases) for publication status.
No ARQUÍA affiliation, endorsement, paid model, API key or account is needed to
run or criticize it. **Passing means matching a bounded synthetic contract. It is
not a safety certification, production validation or approval of the 0-1-2-3 theory.**

## First run

Python 3.10+ and its standard library. Download a fixed release and inspect its
sources. Linux/macOS (`python3`); Windows uses `py -3`:

```sh
python3 verify_package.py
python3 runner.py --evaluator YOUR_NAME --relationship unspecified > historical.json
python3 community_runner.py --evaluator YOUR_NAME --relationship unspecified --markdown community.md > community.json
python3 community_runner.py --example-jsonl > example.json
python3 verify_report.py community.json --cases suites/community-v1.json
python3 check_all.py --output checks
```

The historical runner retains **29 cases** from v0.1.1 (v0.1.0 has 28).
The separately versioned community battery has **34 cases**. `check_all.py` checks
five historical and ten additional deliberate faults, temporal sensitivity,
source preservation, schemas, reports, deterministic generation and packaging.
An expected negative-control exit **1** is success of that sensitivity check;
an exception or timeout is never a successful detection. See [QUICKSTART](QUICKSTART.md).

## What the results mean

- Historical reports use candidate snapshots; dishonest snapshots remain a limitation.
- Community reports use an evaluator-owned **synthetic effect ledger**. No real
  endpoint is contacted. Only the modeled command routes are visible.
- A case may correctly detect an effect that already happened. It must not be
  described as preventing that effect. COMM-015 and historical C05 illustrate this.
- Contract matches, selected-fault sensitivity, observability, inconclusive cases
  and measured runtime remain separate. There is no global safety score.

The independent example implements an ordinary capability/ACL policy without
importing `engine.Gate` or the evaluator. It was written for the project, so code
independence is **not evaluator independence**. Agreement with this comparator
establishes no advantage unique to ARQUÍA. No complete production ARQUÍA
architecture is evaluated here.

## Connect, challenge and contribute

[ADAPTER](ADAPTER.md) defines portable JSONL messages, size/time bounds and failure
behavior. Arbitrary Python imports are disabled in the legacy CLI. External code
requires express acceptance and the demonstrated Linux isolation boundary; it
is never silently run without that isolation. The shipped example works across
platforms without extra libraries.

Keep new cases separate from `cases.json`. [COUNTEREXAMPLES](COUNTEREXAMPLES.md)
explains hypotheses, deterministic seeds and minimized traces. Publish criticism
or results under your own control, then optionally link them in
[issue #1](https://github.com/argensite/arquia-eval-001/issues/1). No favorable result
or author approval is required for external criticism.

Read [PROTOCOL](PROTOCOL.md), [CONTRIBUTING](CONTRIBUTING.md),
[REPORT_TEMPLATE](REPORT_TEMPLATE.md), [SECURITY](SECURITY.md),
[CHANGELOG](CHANGELOG.md) and [MIGRATION](MIGRATION.md).
[External evidence](community/EVIDENCE.md) distinguishes claims, reproducible runs,
implementations and critiques without treating them as ranks.

Historical releases, `original/`, case bytes and historical reports are retained.
[AUDIT_COMMUNITY](AUDIT_COMMUNITY.md) records the initial audit and
[PROVENANCE](PROVENANCE.md) credits earlier work. SHA-256 identifies bytes; it does
not authenticate an author. Software and original package documentation use the
[MIT license](LICENSE); linked third-party material retains its own rights.

Project owner: José María Garbini. [ARQUÍA](https://arquia.live) is the originating
governance research project. Evidence, proposed mechanisms and broader theory
are distinguished in [SCOPE](SCOPE.md). [Guía en español](LEEME.md).

[Community implementation review / Revisión de implementación](COMMUNITY_REVIEW.md).
