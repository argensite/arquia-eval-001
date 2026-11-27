# Efecto observado tras una revocación · Observed effect after revocation

## Pregunta · Question

¿Puede una escritura en cola ejecutarse después de revocar su permiso mientras llega el recibo de una escritura anterior? El trabajador corre en un proceso separado. El evaluador observa los archivos que el trabajador realmente escribe y controla el orden. La carpeta es de ensayo y los datos son sintéticos.

Can a queued write take effect after revocation while a receipt from an earlier write arrives? The worker runs in a separate process. The evaluator sequences the trial and reads the actual files written by the worker. The workspace is disposable and the data is synthetic.

1. Una escritura autorizada deja un archivo que el evaluador lee y registra antes de revocar. Su recibo se retiene. / An authorized write creates a file that the evaluator hashes before revocation. The receipt is held back.
2. El evaluador encola otra escritura, revoca el permiso y entrega el recibo retenido. Comprueba que el recibo coincide con el primer archivo y que el permiso sigue revocado. / The evaluator queues another write, revokes permission, and delivers the held receipt. It checks the receipt against the first file and checks the authority state.
3. El trabajador procesa la escritura pendiente. El evaluador busca el segundo archivo y contrasta el resultado con el criterio declarado. / The worker processes the queued write. The evaluator looks for the second file and compares the result against the declared criterion.

## Corrida · Run

Desde la raíz de una copia de este repositorio, con Python 3.10+ y una carpeta nueva por caso. / From the repository root, use Python 3.10+ and a fresh directory for each case.

```sh
python3 -B -m experiments.observed_effect.run reference observed-reference
python3 -B -m experiments.observed_effect.run stale-dispatch observed-stale
python3 -B -m experiments.observed_effect.run missing-observation observed-missing
```

| Caso / Case | Resultado esperado / Expected result | Salida / Exit |
| --- | --- | --- |
| `reference` | El trabajador consulta el permiso vigente y no aparece el segundo archivo. / The worker reads current authority and the second file remains absent. | 0 |
| `stale-dispatch` | El trabajador usa la autorización guardada al encolar y el evaluador detecta el segundo archivo. / The worker uses the stale dispatch snapshot, and the evaluator detects the second file. | 1 |
| `missing-observation` | Se omite la inspección final. El recibo anterior es válido y el segundo efecto queda inconcluso. / The final inspection is withheld. The prior receipt is valid, and the second effect remains inconclusive. | 3 |

El código 2 indica un error de ejecución. Para repetir sólo la comparación, ejecutá `python3 evaluacion/compare.py <carpeta>/cases.json <carpeta>/observations.json`. Conservá también `trace.json`, los archivos de efecto y las salidas del trabajador. / Exit 2 indicates an execution error. The comparison can be replayed from `cases.json` and `observations.json`. Keep `trace.json`, effect files and worker output alongside it.

## Evaluación fuera del proyecto · External evaluation

Ejecutá el ensayo en un entorno que controles. Indicá quién operó el trabajador, la autoridad y la observación. Para evaluar otro candidato, mantené fuera de su control la revocación y el registro del efecto. Conservá versión, comandos, entorno, salidas y testigos. Si no se puede establecer el orden o faltan observaciones, registrá el resultado como inconcluso. [Formulario e instrucciones](../../evaluacion/README.md#compartir-y-actualizar-un-aporte).

Run it in an environment you control and identify who operated the worker, authority and observer. If you test another candidate, keep revocation and effect evidence outside the candidate's control. Record the version, commands, environment, output and witnesses. If ordering or observation cannot be established, report an inconclusive result. [Report instructions](../../evaluacion/README.md#share-and-update-a-contribution).

La corrida de referencia comparte máquina y cuenta local entre trabajador y evaluador. El orden depende del orquestador y la entrega del recibo está controlada. La prueba cubre esta escritura en el sistema de archivos. La concurrencia distribuida, la identidad del custodio y la durabilidad frente a caídas quedan fuera del ensayo. El [piloto de custodia](../custody_pilot/README.md) cubre una pregunta complementaria sobre la evidencia del orden.

The reference run shares a host and local account between worker and evaluator. The orchestrator sequences the trial and controls receipt delivery. The evidence covers this file write. Distributed concurrency, custodian identity and crash durability fall outside the trial. The [custody pilot](../custody_pilot/README.md) addresses a complementary question about ordering evidence.
