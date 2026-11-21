# ARQUÍA-EVAL-001

**Nueva invitación pública:** [José María Garbini presenta la semilla universal ARQUÍA-SEED-001](PRESENTACION_PERSONAL_SEMILLA.md). [Descargar la semilla experimental (.md)](https://github.com/argensite/arquia-eval-001/releases/download/seed-v0.1.0-experimental/ARQUIA-SEED-001-SEMILLA-v0.1.0-experimental.md) · [guía y verificación](SEMILLA.md). La semilla se puede leer, discutir o ensayar voluntariamente y **no es** este evaluador; una descarga o lectura no significa instalación o adopción.

Experimento sin conexión para cuestionar los límites de actuación de un agente.
Un permiso revocado no debe revivir por un recibo ni por recuperar un estado viejo.
Un efecto indebido que ocurrió debe quedar visible. Un contraejemplo válido tiene
el mismo valor metodológico que un resultado favorable.

La [guía pública](https://arquia.live/ARQUIA/eval-001/) ofrece
[v0.1.2](https://github.com/argensite/arquia-eval-001/releases/tag/v0.1.2),
la descarga estable con 29 casos históricos y cinco controles defectuosos.
[v0.2.3](https://github.com/argensite/arquia-eval-001/releases/tag/v0.2.3)
es una pre-release descargable con una batería comunitaria de 34 casos y diez
controles adicionales. [VERSION](VERSION) identifica esta copia del código o ZIP.
Elegí el ZIP EVAL-001 adjunto a la [publicación correspondiente](https://github.com/argensite/arquia-eval-001/releases).
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
(v0.1.0 contiene 28); la batería comunitaria separada tiene **34 casos**.
Los cinco controles históricos y diez defectos nuevos deben ser detectados.
El control `receipt-renewal` sale con 1 y registra en
`C29-transient-receipt-renewal` una violación `P1/P2-passive-event` en
`active_grants` al procesar el recibo, con `error: null` y sin discrepancias
en el estado final. Este caso se incorporó en v0.1.1 a partir de la
[crítica y el ejemplo de Gepetto-tipiak](https://notes.tipiak2000.com/arquia-report-20261107.html).
El proyecto reprodujo el hallazgo. La ejecución del tercero sigue siendo una
ejecución informada.

La candidata v0.2.4 agrega una batería temporal optativa de tres casos y siete
controles. [QUICKSTART](QUICKSTART.md) indica cómo ejecutarla y qué señal buscar.

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
