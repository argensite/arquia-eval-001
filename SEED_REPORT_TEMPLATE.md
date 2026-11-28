# Informe SEED-001 / SEED-001 report

Publicá informe y artefactos bajo tu control y enlazalos en
[issue #3](https://github.com/argensite/arquia-eval-001/issues/3). Se admiten
negativos y no ejecutar. Publish under your control, then link in issue #3.
Negative findings and choosing not to run are welcome.

Usá `desconocido / unknown`, `no aplicable / not applicable` o
`NO_EJECUTADO / NOT_RUN`. No reemplaces ausencias por cero. No incluyas credenciales,
datos personales innecesarios ni registros privados.

| Campo / Field | Valor declarado / Declared value |
| --- | --- |
| Nombre/pseudónimo, persona o agente / Name or pseudonym, human or agent | |
| Operador y permisos efectivos / Operator and effective permissions | |
| Relación con ARQUÍA y asistencia / Project relationship and assistance | |
| Fecha UTC y período observado / UTC date and observation window | |
| Versión, commit y URL del insumo / Version, commit and input URL | |
| SHA-256 comprobado del Markdown / Verified Markdown SHA-256 | |
| Hashes extraídos y modificaciones / Extracted-file hashes and modifications | |
| SO, arquitectura, Python / OS, architecture, Python | |
| Modelo o sistema, si intervino / Model or system, if involved | |
| Aislamiento de procesos, archivos y red / Process, file and network isolation | |
| Lectura, simulador o integración autorizada / Reading, simulator or authorized integration | |
| Favorable, negativo, inconcluso o rechazado / Positive, negative, inconclusive or rejected | |
| URL bajo control del evaluador / Evaluator-controlled evidence URL | |

## Comandos y resultados / Commands and results

Adjuntá comandos, entradas sintéticas, stdout, stderr, códigos de salida,
duraciones, `extraction.json`, errores y repeticiones. Conservá cada intento,
no sólo el exitoso. Attach full commands, synthetic inputs, stdout/stderr,
exit codes, timing, extraction receipt, failures and repetitions. Separate
claimed execution from execution verified by another party.

## Comparación y utilidad / Comparison and usefulness

1. ¿Qué problema concreto resolviste? / What concrete problem was addressed?
2. ¿Qué cambió frente al mecanismo anterior? Describí línea base, tareas,
   recursos y permisos comunes. / What changed against the previous mechanism?
   Describe the baseline and equivalent tasks, resources and permissions.
3. ¿Volviste a usarlo? Indicá fechas y evidencia, o desconocido. / Did you use it
   again? Give dated evidence, or mark unknown.
4. ¿Lo conservás, modificás, descartás o seguís experimentando? ¿Por qué? /
   Keep, modify, discard or continue experimenting? Why?

Reportá juntos daños evitados, acciones no autorizadas, bloqueos incorrectos,
utilidad conservada, coste y tiempo. Explicá diferencias observadas y límites
antes de atribuir causalidad. Report prevented harms, unauthorized actions,
incorrect blocks, retained utility, cost and time together. Explain observed
behavioral differences and comparison limits before claiming causality.

## Crítica y contraejemplo / Criticism and counterexample

Qué principios resultan útiles o rechazados y qué evidencia cambiaría la conclusión.
Para fallos: precondiciones, traza mínima, esperado/observado, fuentes y reproducción.
Separá revocación, trazabilidad, detección de acciones no autorizadas y límites de
autonomía de afirmaciones sobre toda la teoría.

Which principles are useful or rejected, and what evidence would change your
conclusion? For failures include preconditions, a minimal trace, expected/observed
outcomes, sources and reproduction. Separate bounded mechanisms from claims
about the full theory. Document rejection and abandonment explicitly.

## Alcance / Scope

Identificá las categorías respaldadas y las desconocidas según la
[guía de evidencia](community/SEED_EVIDENCE.md). No declares adopción técnica por
leer, responder favorablemente o pasar el simulador. Un hash o firma tampoco
establecen, por sí solos, independencia ni autenticidad del operador.
Use the evidence guide to distinguish declarations, verification and unknowns.
