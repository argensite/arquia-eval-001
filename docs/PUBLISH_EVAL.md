# Publicar ARQUÍA-EVAL-001

La descarga estable de arquia.live y el indicador **Latest** de GitHub apuntan
a v0.1.2. v0.2.3 es una pre-release pública. El código con la extensión temporal
v0.2.4 requiere una nueva release para ofrecer su ZIP a evaluadores. Las notas
de la candidata están en [RELEASE_NOTES.md](../RELEASE_NOTES.md).

## Seleccionar el ZIP aprobado

1. Fijá el commit a etiquetar y comprobá que el job portable de GitHub Actions
   terminó en ese SHA. Si hubo un merge, usá su corrida posterior al merge.
2. Descargá el artefacto `verified-release-zip` de ese job. Conservá el ZIP
   interior y el archivo `.zip.sha256`. Verificá que el SHA-256 de sus bytes
   coincida con `source_archive_sha256` en `summary.json`, y que
   `archive_source.commit` coincida con el commit a etiquetar. La fecha y
   el tiempo de las pruebas quedan en los recibos.
3. El control se puede volver a ejecutar antes de publicar, desde un checkout
   de ese commit, con `python3 check_all.py --archive RUTA_AL_ZIP --output zip-checks`.
   Conservá la salida y los resultados de los testigos C29 y cache-per-turn.
4. Con aprobación del titular, etiquetá ese commit y adjuntá los bytes
   verificados y el checksum a la nueva GitHub release. Descargá el adjunto
   público y compará el SHA-256 antes de anunciarlo.

## Sincronizar la web y la convocatoria

Los archivos en [docs/website/eval-001](website/eval-001) son fuentes estáticas
para `/ARQUIA/eval-001/`. Describen los dos ZIP que ya existen y la candidata.
El [texto propuesto para issue #1](ISSUE_1_PROPOSED.md) conserva el cuerpo original
debajo de la actualización. Las cinco fuentes de la web corresponden a los dos
`index.html`, los dos `index.md` y `manifest.json`.

Si se aprueba anunciar v0.2.4, actualizá en esas fuentes y en la propuesta del
issue el estado que haya recibido en GitHub, el commit y la huella del adjunto
público. Usá el nombre del ZIP de release, enlazá QUICKSTART y TEMPORAL_AUTHORITY
al commit publicado y conservá las tres baterías y sus comandos por separado.
La descarga principal sólo se promueve si la nueva release se publica como
estable. Si se publica como pre-release, mantené la descarga principal estable
y sumá la nueva pre-release con enlace propio.

Con aprobación para desplegar, compará las páginas remotas con las fuentes
revisadas antes de sustituirlas. Volvé a leer las dos guías y el manifiesto
públicos, descargá por su enlace principal y comprobá versión, commit, bytes y
SHA-256. Aplicá la actualización del issue contra su cuerpo vigente. El tag,
ZIP, checksum y archivos históricos de v0.1.0 se conservan con sus bytes
originales.
