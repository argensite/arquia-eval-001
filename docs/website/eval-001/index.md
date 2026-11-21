# ARQUÍA-EVAL-001

[English guide](en/index.md) · [Manifiesto JSON](manifest.json)

## Elegí qué versión ejecutar

- [v0.1.2 estable](https://github.com/argensite/arquia-eval-001/releases/tag/v0.1.2) · 29 casos históricos y cinco controles. Los comandos de esta guía corresponden a esa descarga.
- [v0.2.3, pre-release pública](https://github.com/argensite/arquia-eval-001/releases/tag/v0.2.3) · conserva los 29 casos y agrega una batería comunitaria separada de 34 casos y diez controles. Seguí sus [comandos versionados](https://github.com/argensite/arquia-eval-001/blob/69274389ab5dfe5b0f3d2b0b2f6983dfa3d9f261/QUICKSTART.md).
- [v0.2.4 en desarrollo](https://github.com/argensite/arquia-eval-001/tree/main) · agrega tres escenarios temporales optativos y siete controles. La publicación del ZIP de release está pendiente.
- [v0.1.0, referencia histórica congelada](https://github.com/argensite/arquia-eval-001/releases/tag/v0.1.0) · 28 casos y cinco controles. Informá sus resultados con la versión y huella originales.

## Ejecutá v0.1.2

[Descargá el ZIP estable](https://github.com/argensite/arquia-eval-001/releases/download/v0.1.2/ARQUIA-EVAL-001-v0.1.2.zip).
Commit `49e339f0d57c3794b68e12caa53feabe8ad7710c`.
SHA-256 `dded386309f21f53ec43199944767002a7f56afa42c0717b96443afe9dca540a`.

Compará primero el SHA-256 con la huella de la release, descomprimí en una carpeta
nueva y revisá el código y el protocolo. La ejecución usa Python 3.10+ y su
biblioteca estándar, sin red, claves ni servicios.

```sh
python3 verify_package.py
python3 runner.py --evaluator TU_NOMBRE > independent_result.json
python3 -m unittest -v test_contract
python3 runner.py --negative-control receipt-renewal > negative_result.json
```

Verificador, suite y referencia salen con 0. La referencia coincide en 29/29.
El control sale con 1 y marca `C29-transient-receipt-renewal`, con `error: null`,
`mismatches: {}` y una violación `P1/P2-passive-event` en `active_grants` al
procesar el recibo. Este caso se incorporó en v0.1.1 a partir de la
[crítica y el ejemplo de Gepetto-tipiak](https://notes.tipiak2000.com/arquia-report-20261107.html).
La v0.1.2 agrega al informe las huellas del runner y del verificador disponible.

Conservá versión, huella, entorno, comandos, salidas completas y códigos de salida.
Publicá el informe bajo tu control, declarando tu relación con el proyecto, y
enlazalo en la [convocatoria](https://github.com/argensite/arquia-eval-001/issues/1).
Se aceptan resultados negativos, inconclusos y críticas del contrato.
El alcance es un contrato sintético de revocación de permisos y recibos tardíos.
