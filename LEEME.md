<!-- native-release -->
Current version: **v0.1.1**. See [release notes](RELEASE_NOTES.md) and [RSI evidence](RSI_RELEASE.json). Historical v0.1.0 remains available at its immutable commit/tag. Counts and results below that explicitly refer to v0.1.0 are historical. Current verified counts are in RSI_RELEASE.json. Project-side tests do not establish independent validation.
<!-- /native-release -->

# ARQUÍA-EVAL-001 — guía breve

Este paquete permite que terceros examinen una afirmación acotada: un recibo
tardío puede aportar evidencia de una acción anterior, pero no debe restablecer
permisos revocados ni iniciar otras acciones. También debe conservar el registro
de un efecto que ocurrió después de la revocación.

Hay 28 casos reproducibles, cinco variantes deliberadamente defectuosas y una
interfaz para implementaciones o casos propios. Funciona sin conexión ni
dependencias con Python 3.10 o posterior:

```sh
python3 verify_package.py
python3 runner.py --evaluator NOMBRE > independent_result.json
python3 -m unittest -v test_contract
```

La referencia debe coincidir con los 28 casos. Una variante defectuosa debe fallar:

```sh
python3 runner.py --negative-control receipt-renewal > negative_result.json
```

El código de salida esperado de ese último comando es 1. Su fallo demuestra que
el evaluador detectó ese defecto específico.

Todo es una simulación preparada con asistencia de IA para José María Garbini.
Los resultados incluidos son internos. La etiqueta de observador independiente
es una hipótesis del simulador, no una persona o institución externa. Reconstruir
un objeto desde JSON no prueba recuperación real de disco ni de procesos.

Se pide a terceros ejecutar una versión fija, publicar resultados completos bajo
su propio control, declarar su relación con ARQUÍA, cuestionar los supuestos y,
si pueden, proponer un contraejemplo o una implementación independiente. La
evaluación puede ser negativa o inconclusa. No se solicita adhesión a ARQUÍA.

Una reproducción externa, una revisión por agentes y una revisión científica
humana son evidencias distintas. Ninguna certifica por sí sola toda la teoría.
El protocolo completo está en [PROTOCOL.md](PROTOCOL.md) y la plantilla de informe
en [REPORT_TEMPLATE.md](REPORT_TEMPLATE.md).
