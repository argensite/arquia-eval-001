# Evidencia SEED-001 / SEED-001 evidence

El [registro de datos](seed-evidence.json) comienza sin informes de participantes:
es ausencia de informes registrados, no prueba de que nadie haya usado la semilla.
Los informes históricos de **EVAL-001** permanecen en su [índice original](evidence-index.json);
no se convierten en pruebas de SEED-001.

| Nivel / Level | Evidencia / Evidence represented |
| --- | --- |
| 0 | Acceso o descarga observada / Observed access or download |
| 1 | Lectura y análisis conceptual documentado / Documented conceptual analysis |
| 2 | Ejecución declarada / Declared test execution |
| 3 | Ejecución reproducible con artefactos verificables / Reproducible execution with verifiable artifacts |
| 4 | Implementación independiente documentada / Documented independent implementation |
| 5 | Uso reiterado o integración operativa demostrada / Demonstrated repeat use or operational integration |

Son categorías de seguimiento, **no puntajes, certificaciones de seguridad ni una
escalera automática**. Registrar cada afirmación por separado. Una implementación
puede estar documentada sin ejecución reproducida; la reproducción del autor no
verifica la independencia del tercero. These are tracking categories, not scores,
safety certifications or automatic promotion rules. Separately written code does
not by itself establish evaluator independence or operating authority.

Cada entrada conserva, cuando existan: identidad/relación declaradas, fecha,
versión/hash, plataforma/modelo, operador/permisos, comandos/salidas/códigos,
fallos, comparación, motivos de aceptación/rechazo/abandono y URL controlada por
el evaluador. Ausencias: `null` (desconocido). Conservar fuente y fecha de cada
comprobación. No investigar identidades privadas ni recopilar credenciales.
Usar la [plantilla bilingüe](../SEED_REPORT_TEMPLATE.md).

Keep identity/affiliation declarations, date, version/hash, platform/model,
operator/permissions, commands/outputs/exits, failures, comparison, rationale
and evaluator-controlled evidence URL when available. Missing facts are `null`,
not zero. Preserve provenance and distinguish a declaration from verification.
A signature or checksum alone does not authenticate the operator or independence.

## Contadores y cobertura / Counters and coverage

[GitHub Releases](https://api.github.com/repos/argensite/arquia-eval-001/releases)
expone `assets[].download_count`. Para SEED-001 contar sólo el Markdown oficial;
no sumar su checksum, ZIP de EVAL, adjuntos de evidencia ni contadores web.
Registrar fecha, activo, valor y descargas propias conocidas. Consultar la API no
descarga el activo; verificarlo descargándolo puede aumentar el contador y se
declara como actividad del proyecto. No deducir usuarios únicos o instalaciones.

GitHub asset download counts are requests, not unique people or adoption. Raw
reads, repository clones and website downloads have separate coverage. Do not
subtract guessed self-traffic or infer participants from a difference. Unavailable
metrics are unknown. Independent technical adoption remains unknown until an
adequate report is available.

## Resultados y utilidad / Outcomes and usefulness

Conservar positivos, negativos e inconclusos separados. Investigar problema
resuelto, diferencia frente al mecanismo anterior, uso posterior y decisión de
conservar/modificar/abandonar. Comparar tareas, permisos y recursos equivalentes;
medir daños evitados, bloqueos incorrectos y utilidad conservada juntos.
Actividad o coincidencia temporal no prueban causalidad ni toda la teoría 0-1-2-3.

Keep positive, negative and inconclusive results distinct. Ask what problem was
solved, what changed against the baseline, whether use recurred, and why the
participant kept, modified or discarded it. Report harm, incorrect blocks and
retained utility together; do not infer causal benefit from activity alone.
