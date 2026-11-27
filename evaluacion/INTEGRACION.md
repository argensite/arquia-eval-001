# Inicio rápido e integración · Quick start and integration

## Inicio rápido · Quick start

En cualquier sistema con Git y Python 3.10+, el tag de la convocatoria fija el ejemplo. También podés descargar el ZIP y el SHA-256 desde la [release del kit](https://github.com/argensite/arquia-eval-001/releases/tag/open-evaluation-2026-11-26). Once downloaded, the example runs offline with the standard library.

```sh
git clone --branch open-evaluation-2026-11-26 --depth 1 https://github.com/argensite/arquia-eval-001.git arquia-evaluation
cd arquia-evaluation
git rev-parse HEAD
python3 evaluacion/compare.py evaluacion/ejemplos/casos.json evaluacion/ejemplos/observaciones.json > comparison.json
```

El último comando sale con 1 a propósito. On Windows, use `py -3` in place of `python3`. Exit codes are part of the observation, so save them before running another command. On a POSIX shell, run `printf '%s\n' "$?" > comparison.exit` immediately after the command. You can parse `comparison.json` whether the demonstration exits 0, 1 or 3.

### Batería existente · Existing suite

En Linux, macOS o un runner con `curl`, `unzip` y Python, descargá la versión preliminar v0.2.4 en un directorio nuevo. This URL and digest identify the distributed ZIP. The [materials catalogue](MATERIALES.md) includes the stable v0.1.2 and the historical releases.

```sh
curl -fL https://github.com/argensite/arquia-eval-001/releases/download/v0.2.4/ARQUIA-EVAL-001-v0.2.4.zip -o ARQUIA-EVAL-001-v0.2.4.zip
python3 -c 'from hashlib import sha256; from pathlib import Path; import sys; sys.exit(sha256(Path("ARQUIA-EVAL-001-v0.2.4.zip").read_bytes()).hexdigest() != "86bfc232066ddd52f3049aaeb3b0e584cf8fef824ee27f39628aa977ea26cbab")' &&
unzip -q ARQUIA-EVAL-001-v0.2.4.zip &&
cd ARQUIA-EVAL-001-v0.2.4 &&
python3 verify_package.py &&
python3 check_all.py --output ../evidence-024
```

`check_all.py` conserva resúmenes, recibos, salidas y códigos de retorno. Its optional suites test synthetic authority and receipt behavior. A declared fault yielding exit 1 with the expected witness can pass the sensitivity check. The same exit by itself is insufficient. Do not merge the suites into a global score.

### Ensayo de efecto observado · Observed-effect trial

El repositorio ofrece un [ensayo reproducible](../experiments/observed_effect/README.md) de una escritura en cola tras revocar el permiso. Conserva los archivos de efecto, la secuencia y el resultado del comparador. The repository also provides a trial where the evaluator observes actual file writes and evaluates a delayed receipt separately. The frozen packages above have their own test suites.

## Casos propios · Your own cases

1. Copiá [casos.json](ejemplos/casos.json) a tu proyecto. Cambiá cada `id`, `rule`, `scenario`, `failure_criterion` y el objeto `expected`. Podés usar cualquier propiedad de tu agente y más de una condición observable por caso.
2. Run your agent under your own observation boundary. Translate your trace to the shape in [observaciones.json](ejemplos/observaciones.json), with an `id` and `observed` object per case. Keep the underlying trace and explain how the fields were produced. For example, use an evaluator-owned mock service to record a requested action or a simulated third party to check who was included in a decision.
3. Ejecutá el comparador con tus dos archivos. El resultado JSON identifica los insumos por SHA-256 y conserva discrepancias y campos faltantes. Guardá aparte la versión del agente, entorno, comandos y fuente de cada observación. Si la métrica requiere tolerancias, orden temporal o una rúbrica cualitativa, calculá esa observación con tu propio código o usá otro evaluador.
4. The checker compares declared JSON values (including JSON types), with object key order ignored. A decisive mismatch gives case status `fail`, even if another field is missing. Missing evidence without a mismatch gives `inconclusive`. Overall exits are 0 for all matched, 1 for a mismatch, 2 for unreadable or invalid input and 3 for incomplete evidence without a mismatch. It reads data and runs no candidate, shell expression, network request or uploaded program. It cannot establish whether an input observation is true.

Para integrarlo, copiá `evaluacion/compare.py` y el aviso [MIT](../LICENSE) a tu repositorio. El script recibe sólo los dos archivos y funciona sin el resto del kit. You can vendor it, translate the example, call the CLI from your runner, or consume `arquia.observation-comparison/1` in your own reporting tool. For authorization fixtures specifically, the separate EVAL-001 community and temporal runners accept `--cases` with their own schemas. The pinned [JSONL adapter](https://github.com/argensite/arquia-eval-001/blob/027ca85d09fde650cda2585fcfe562765119067e/ADAPTER.md) describes the optional candidate interface and its platform requirements. Run any integration you build in your own environment.

La [plantilla de CI](ejemplos/ci.yml) es para copiar a **tu** `.github/workflows/arquía-evaluation.yml`. La primera etapa comprueba la descarga y el resultado de ejemplo. La segunda lee fixtures locales, guarda el informe y respeta el código de retorno. Cambiá las rutas a tus casos y observaciones y generá ese archivo con tu integración. The workflow is manual, uses read-only contents permissions, and runs in the evaluator's repository. The contribution form is an intake channel for reports and links. It does not trigger an execution.

## Índice descargable · Downloadable index

```sh
curl -fL https://raw.githubusercontent.com/argensite/arquia-eval-001/open-evaluation-2026-11-26/evaluacion/index.json -o index.json
python3 -c 'import json; d=json.load(open("index.json",encoding="utf-8")); print(d["schema"]); print(*(r["id"] for r in d["results"]),sep="\n")'
```

`materials` identifies fixed releases and source records, `coverage` ties topics to source sections and evidence IDs, and `results` identifies the producer's role and available artifacts. Artifact URLs are absolute and point to the tagged source, fixed release assets, or the original evidence. The tagged index is a snapshot. See the [current index on main](https://raw.githubusercontent.com/argensite/arquia-eval-001/main/evaluacion/index.json) for later entries. Preserve the originally cited artifact and its checksums when recording a reproduction.
