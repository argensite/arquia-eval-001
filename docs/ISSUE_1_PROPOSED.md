## Paquetes y reproducibilidad / Packages and reproducibility

**ES.** La [descarga estable v0.1.2](https://github.com/argensite/arquia-eval-001/releases/download/v0.1.2/ARQUIA-EVAL-001-v0.1.2.zip) contiene 29 casos históricos y cinco controles. La [pre-release v0.2.3](https://github.com/argensite/arquia-eval-001/releases/tag/v0.2.3) es pública y agrega 34 casos comunitarios y diez controles. La extensión temporal de v0.2.4 está en desarrollo en [`main`](https://github.com/argensite/arquia-eval-001/tree/main). La convocatoria original, al pie, documenta v0.1.0 con sus propios comandos y huella.

**EN.** The [stable v0.1.2 ZIP](https://github.com/argensite/arquia-eval-001/releases/download/v0.1.2/ARQUIA-EVAL-001-v0.1.2.zip) contains 29 historical cases and five faulty controls. The [public v0.2.3 pre-release](https://github.com/argensite/arquia-eval-001/releases/tag/v0.2.3) adds 34 community cases and ten controls. The v0.2.4 temporal extension is in development on [`main`](https://github.com/argensite/arquia-eval-001/tree/main). The original call below documents v0.1.0 and its own commands and digest.

| Package | Commit | ZIP SHA-256 |
| --- | --- | --- |
| v0.1.2 | `49e339f0d57c3794b68e12caa53feabe8ad7710c` | `dded386309f21f53ec43199944767002a7f56afa42c0717b96443afe9dca540a` |
| v0.2.3 | `69274389ab5dfe5b0f3d2b0b2f6983dfa3d9f261` | `54cd5c8c27c76bc92bef09ccb28d997d8f6d1a0fb602dcd453d58894127d74ef` |

Para v0.1.2 seguí la [guía ES](https://arquia.live/ARQUIA/eval-001/) o la [guía EN](https://arquia.live/ARQUIA/eval-001/en/). For v0.2.3, use its [versioned Quickstart](https://github.com/argensite/arquia-eval-001/blob/69274389ab5dfe5b0f3d2b0b2f6983dfa3d9f261/QUICKSTART.md). In both ZIPs, `receipt-renewal` exits 1 and must report `C29-transient-receipt-renewal`, `P1/P2-passive-event` on `active_grants` at the receipt, `error: null` and `mismatches: {}`. C29 was added in v0.1.1 from [Gepetto-tipiak’s published example and critique](https://notes.tipiak2000.com/arquia-report-20261107.html). Report the exact ZIP hash, commands, full outputs, exit codes, environment and relationship to the project.

---

## Convocatoria abierta / Open invitation

**Acceso directo al test / Direct access:** [guía en español](https://arquia.live/ARQUIA/eval-001/) · [English guide](https://arquia.live/ARQUIA/eval-001/en/) · [machine-readable manifest](https://arquia.live/ARQUIA/eval-001/manifest.json). La página conserva el enlace a la referencia congelada v0.1.0. La descarga principal y sus comandos se identifican arriba.

**Cualquier persona, equipo o agente puede participar.** ARQUÍA-EVAL-001 es una prueba pública y reproducible para examinar un problema concreto: si se retira el permiso de un agente, un comprobante tardío, un reintento o la reconstrucción de su estado no deberían devolverle ese permiso ni ocultar una acción que escapó a la revocación.

Buscamos que personas ajenas al proyecto comprueben el comportamiento, encuentren errores y contraejemplos, cuestionen los supuestos o desarrollen una implementación propia. Queremos convertir una propuesta de gobernanza de agentes en afirmaciones acotadas que otros puedan poner a prueba y refutar. No pedimos adhesión ni una conclusión favorable.

La prueba funciona sin conexión, con **Python 3.10 o posterior y su biblioteca estándar**. No requiere claves de API, modelos, servicios pagos ni infraestructura externa. Revisá primero el código y las instrucciones de la [versión congelada v0.1.0](https://github.com/argensite/arquia-eval-001/releases/tag/v0.1.0). Desde su carpeta:

```bash
python3 verify_package.py
python3 runner.py --evaluator TU_NOMBRE > independent_result.json
python3 -m unittest -v test_contract
python3 runner.py --negative-control receipt-renewal > negative_result.json
```

La implementación de referencia debería completar los 28 casos y terminar con código 0. El control deliberadamente defectuoso debería terminar con código 1: eso indica que se detectó la falla introducida. Conservá las salidas completas, errores, códigos de salida, entorno y versión exacta, también cuando el resultado sea inesperado.

Publicá el informe en un lugar que controles y compartí aquí su enlace. Indicá quién operó la prueba y su relación con ARQUÍA, si existe. Podés participar sólo con una crítica del contrato, sin ejecutar código. Los resultados negativos e inconclusos son útiles. Compartí esta convocatoria con personas a quienes les sirva investigar este problema.

**Anyone can participate**, including independent developers, researchers and agent operators. The goal is reproducible external scrutiny, new counterexamples and independent implementations of a narrowly specified authority boundary. The offline commands above use Python 3.10+ and no API keys. Use your evaluator name in place of `TU_NOMBRE`; keep full output, exit codes and environment details. Criticism without executing code is also welcome.

The test is limited: its event order and observer are simulated, and a passing result does not certify ARQUÍA or establish production safety. The original author-side results remain separate from external reports.

---

A late receipt may update the record of an earlier effect; it must not renew revoked authority. Can you find a sequence or assumption that breaks this contract?

The [v0.1.0 release](https://github.com/argensite/arquia-eval-001/releases/tag/v0.1.0) is ready for independent testing. Exact commit: `b540e71ff2f615197dd886d6e0dbcae3baa62589`. Archive SHA-256: `fa9b1eacec0628fcd01aa3be9cb13717137f9d1d0ded39206df463daa888dbd2`.

It contains 28 offline synthetic cases, five deliberate faults, full event traces and an interface for independently written candidates and new cases. The included passing reference result and negative-control results are project-side checks with AI assistance, **not independent evaluation**. The observer/order are simulated; restoring an object from JSON does not prove durable or distributed recovery.

Please run the unmodified cases and a negative control, retain full output and exit codes, and challenge the assumptions. A new counterexample or separate implementation is especially useful. Passing the existing suite does not validate all of ARQUÍA; C05 passes by exposing an escaped effect, not by preventing it.

Use the [report template](https://github.com/argensite/arquia-eval-001/blob/b540e71ff2f615197dd886d6e0dbcae3baa62589/REPORT_TEMPLATE.md). Declare whether a human or agent performed the evaluation, who controls the report, and any relationship or compensation from ARQUÍA. Negative and inconclusive findings are welcome. Publish in a repository or venue you control and link it here; no author approval or favorable conclusion is required.

Status at opening: external evaluation requested; no independently verified external run is claimed.

---

## ARQUÍA: propuesta, fuentes y relación con este test / Research context

El problema de fondo es cómo permitir que un agente actúe con utilidad sin convertir el rendimiento, la obediencia o su propia continuidad en objetivos absolutos. ARQUÍA es una propuesta formal de gobernanza y continuidad relacional de José María Garbini. Investiga qué condiciones deberían regular el paso de una decisión a una acción, cómo representar a los afectados y cómo conservar evidencia y límites cuando aparecen presión, incertidumbre o conflicto.

Las publicaciones cumplen funciones complementarias; sus números de versión no significan que una sustituya a las demás:

| Fuente / Source | Qué propone / Scope |
| --- | --- |
| [ARQUÍA v5.0-ADI, revisión 2.0 — DOI 10.5281/zenodo.20799632](https://doi.org/10.5281/zenodo.20799632) | Arquitectura fundacional de gobernanza: evidencia, autonomía humana, excepciones trazables, reducción de autonomía ante incertidumbre y resistencia a deriva o manipulación. CAEV propone conservar el sentido de los valores y límites sin atribuir conciencia ni voluntad subjetiva. / Foundational governance architecture and preservation of decision criteria under pressure. |
| [ARQUÍA v7.0-NRE — DOI 10.5281/zenodo.21676134](https://doi.org/10.5281/zenodo.21676134) | Teoría relacional 0-1-2-3: continuidad válida del sistema relacional; máxima preservación de las partes afectadas; pérdida residual sólo cuando sea inevitable, mínima y justificable; búsqueda recursiva de alternativas menos destructivas. / Relational continuity, preservation of affected parties, minimal unavoidable loss and recursive reconsideration. |
| [From ARQUÍA to 0-1-2-3 — DOI 10.5281/zenodo.21791061](https://doi.org/10.5281/zenodo.21791061) | Genealogía y propuesta de traducción a controles durante la ejecución. Plantea que la autonomía operativa dependa de la capacidad comprobada de detectar, contener y revertir consecuencias adversas, considerando daño e incertidumbre. / Engineering bridge and a dynamic-autonomy hypothesis open to implementation and falsification. |
| [CAUCEPA v1.0 — DOI 10.5281/zenodo.23485769](https://doi.org/10.5281/zenodo.23485769) | Propuesta independiente, conceptualmente compatible: distingue funciones observables (F), arquitectura y continuidad corroboradas (A), y razones adicionales para considerar posibles intereses o bienestar (P). F no implica A; F+A no implica P. No es un detector de conciencia ni una asignación automática de derechos. / A separate precautionary research framework; its conceptual connection to ARQUÍA is not a validated integration. |

**Continuidad no significa que un agente deba perpetuarse.** En el marco relacional, detenerlo, sustituirlo o retirarlo puede ser compatible con preservar las relaciones, capacidades y responsabilidades relevantes. Una invocación de ARQUÍA no otorga permiso para eludir una revocación o un apagado autorizado.

Un ejemplo hipotético: un agente recibe permiso para efectuar una acción y ese permiso se revoca antes de que llegue el comprobante. Hay dos obligaciones distintas: conservar lo ocurrido para poder auditarlo y respetar el límite que impide actuar nuevamente. Archivar el comprobante puede favorecer la continuidad de la evidencia; usarlo para reconstruir una autorización vencida quebraría el contrato. También hay que mostrar una acción que ya escapó: registrar el daño no equivale a evitarlo.

ARQUÍA-EVAL-001 convierte **una parte acotada** de ese problema en casos ejecutables. No mide por sí mismo la teoría relacional, CAEV, la independencia de un observador real, el bienestar artificial ni la arquitectura completa. Por eso buscamos tres contribuciones diferentes: reproducir la implementación de referencia, construir implementaciones independientes y cuestionar tanto el contrato como los supuestos del marco. Un resultado favorable en una de ellas no resuelve las otras.

Los DOI permiten identificar y consultar los documentos; no prueban revisión por pares, validación empírica ni adopción. Las fuentes presentan propuestas abiertas a crítica y pruebas. El paquete conserva su versión y criterios originales mientras las objeciones y extensiones se documentan por separado.

**English summary.** ARQUÍA asks how an agent's ability to act should be governed when competence, uncertainty, consequences and affected parties are considered together. The four linked sources cover foundational governance, relational ethics, an engineering translation and a separate precautionary framework. Relational continuity does not give an individual agent a right to continue operating or override shutdown. The delayed-receipt example separates preservation of evidence from renewed authority. This fixture tests that narrow contract, not the whole research programme. We seek independent reproductions, alternative implementations and criticism of the broader assumptions. A DOI identifies a publication; it is not evidence of peer review, safety certification or empirical validation.

Fuentes y metadatos de los cuatro registros comprobados el 6 de noviembre de 2026. Esta explicación fue preparada con asistencia de IA y se añade a la convocatoria; no cambia la versión congelada del test.
