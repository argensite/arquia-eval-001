# ARQUÍA-EVAL-001

Experimento sin conexión para cuestionar los límites de actuación de un agente.
Un permiso revocado no debe revivir por un recibo ni por recuperar un estado viejo.
Un efecto indebido que ocurrió debe quedar visible. Un contraejemplo válido tiene
el mismo valor metodológico que un resultado favorable.

Versión del paquete: [VERSION](VERSION). La publicación se comprueba en [GitHub Releases](https://github.com/argensite/arquia-eval-001/releases).
No exige pertenecer a ARQUÍA, adherir a su propuesta, usar modelos pagos ni abrir
cuentas. Aprobar sólo demuestra coincidencia con invariantes sintéticas acotadas.
No certifica seguridad de producción ni valida la teoría 0-1-2-3.

## Primera ejecución

Python 3.10 o posterior, sin bibliotecas adicionales. En Linux/macOS:

```sh
python3 verify_package.py
python3 runner.py --evaluator NOMBRE --relationship unspecified > historical.json
python3 community_runner.py --evaluator NOMBRE --relationship unspecified --markdown community.md > community.json
python3 community_runner.py --example-jsonl > example.json
python3 verify_report.py community.json --cases suites/community-v1.json
python3 check_all.py --output checks
```

En Windows reemplazá `python3` por `py -3`. [QUICKSTART](QUICKSTART.md) detalla
comandos y códigos de salida. Se conservan los **29 casos históricos** de v0.1.1
(v0.1.0 contiene 28); la batería comunitaria separada tiene **28 casos**.
Los cinco controles históricos y diez defectos nuevos deben ser detectados.
El fallo esperado de un control tiene salida 1; una excepción no demuestra que
se detectó el defecto previsto.

## Interpretación

El evaluador histórico depende de observaciones declaradas por el candidato.
La extensión comunitaria controla su propio registro sintético de efectos:
permite contrastar esas declaraciones dentro del entorno modelado. No observa
rutas reales externas. C05 y COMM-015 pueden aprobar por detectar correctamente
un efecto indebido que ocurrió: **detección no equivale a prevención**.

Los informes separan cumplimiento, sensibilidad a defectos elegidos,
observabilidad, resultados inconclusos y tiempo medido. No producen una
puntuación global de seguridad. El ejemplo independiente usa un control
convencional de capacidades/permisos sin heredar del motor; fue escrito para el
proyecto y no constituye evaluación externa independiente. No prueba una ventaja
exclusiva de ARQUÍA ni ejecuta toda su arquitectura.

## Integración y crítica

[ADAPTER](ADAPTER.md) define JSONL portable para otros lenguajes, límites y errores.
El código externo queda deshabilitado por defecto; requiere aceptación expresa
y aislamiento Linux disponible. El ejemplo incluido funciona sin dependencias
adicionales. El antiguo import arbitrario por `--adapter` se retira por seguridad;
[MIGRATION](MIGRATION.md) explica el cambio.

Un tercero puede crear casos propios sin modificar los históricos, ejecutar y
publicar resultados negativos, positivos o inconclusos bajo su propio control.
No necesita aprobación ni adhesión. Puede enlazarlos en
[issue #1](https://github.com/argensite/arquia-eval-001/issues/1).

Documentación: [protocolo](PROTOCOL.md), [contraejemplos](COUNTEREXAMPLES.md),
[colaboración](CONTRIBUTING.md), [plantilla de informe](REPORT_TEMPLATE.md),
[seguridad](SECURITY.md), [cambios](CHANGELOG.md), [alcance](SCOPE.md),
[auditoría](AUDIT_COMMUNITY.md) e [índice de evidencia externa](community/EVIDENCE.md).
Una ejecución declarada, una reproducción verificada y una revisión formal son
categorías distintas; ninguna se infiere de una invitación o de una cuenta.

José María Garbini es el titular del proyecto. [ARQUÍA](https://arquia.live) aporta
la propuesta de gobernanza que motivó el experimento; no actúa como certificador.
Los archivos históricos se conservan. Un hash identifica bytes, no autentica al
autor. Se mantiene la [licencia MIT](LICENSE) y los derechos de fuentes externas.

[Community implementation review / Revisión de implementación](COMMUNITY_REVIEW.md).
