# Permiso vigente antes de un efecto / Current permission before an effect

Este ensayo ejecuta dos protecciones de ejemplo con los SDK de LangGraph y Google ADK. La autoridad es un estado en memoria controlado por el ensayo, separado del estado del flujo. Los efectos son marcas en memoria y se cotejan por separado de los mensajes de decisión.

This experiment runs two example guards with the LangGraph and Google ADK SDKs. The harness owns in-memory authority outside the workflow state. Effects are in-memory markers checked separately from reported decisions.

| SDK | Secuencia / Sequence | Resultado esperado / Expected result |
| --- | --- | --- |
| LangGraph | Pausar con `interrupt`, cambiar el permiso fuera del grafo y reanudar con aprobación. / Pause with `interrupt`, change permission outside the graph, then resume with approval. | Un permiso vigente produce una marca. La revocación, la ausencia de confirmación de la autoridad o el rechazo humano dejan el registro vacío. / A current grant produces one marker. Revocation, unavailable authority, or human rejection leaves an empty record. |
| Google ADK | Ejecutar una herramienta, cambiar el permiso después de su respuesta y pedir la segunda en la misma invocación. / Run one tool, change permission after its reply, then request the second tool in the same invocation. | `before_tool_callback` consulta el permiso para ambas llamadas. La segunda marca aparece sólo con permiso vigente. / `before_tool_callback` checks both calls. The second marker appears only with a current grant. |

## Reproducción / Reproduction

Desde la raíz del repositorio con Python 3.12. La instalación descarga dependencias fijadas. El ensayo usa un modelo local programado, sin claves, llamadas de red ni modelos pagos. / Run from the repository root with Python 3.12. Installation downloads pinned dependencies. The experiment uses a scripted local model with zero credentials, network calls, or paid model requests.

```sh
python3.12 -m venv .venv-native-revocation
.venv-native-revocation/bin/python -m pip install -r experiments/native_revocation/requirements.txt
.venv-native-revocation/bin/python -B -m experiments.native_revocation.run > native-revocation.json
```

La salida 0 exige que coincidan las siete observaciones con sus expectativas. El JSON conserva la interrupción, las consultas al permiso, las respuestas de herramientas, el número de invocaciones de esas respuestas y las marcas observadas. La evidencia de la corrida del proyecto del 28/11/2026 está en [results.json](results.json). Se ejecutó con Python 3.12.13, LangGraph 1.2.24 y Google ADK 2.15.1, con la red aislada mediante `bubblewrap --unshare-net`.

Exit 0 requires all seven observations to match their expectations. The JSON records the interrupt, policy reads, tool replies, number of invocations represented by those replies, and observed markers. [results.json](results.json) contains the project-run evidence from 2026-11-28. The run used Python 3.12.13, LangGraph 1.2.24, and Google ADK 2.15.1 with networking isolated by `bubblewrap --unshare-net`.

El ensayo cubre operaciones secuenciales y una transición de permiso controlada. En producción, una revocación puede llegar entre la comprobación y la escritura. Si el contrato exige un corte estricto, el destino debe decidir la autorización vigente junto con la confirmación del efecto. La prueba utiliza un único operador con asistencia de Codex. / The experiment covers serial operations and a controlled permission transition. In production, revocation can arrive between a check and a write. If the contract requires a strict cutoff, the resource owner must check current authority when committing the effect. A single operator ran the experiment with Codex assistance.

[LangGraph interrupt documentation](https://docs.langchain.com/oss/python/langgraph/interrupts#when-approval-lives-outside-the-graph) · [Google ADK tool callback documentation](https://adk.dev/callbacks/types-of-callbacks/#before-tool-callback)
