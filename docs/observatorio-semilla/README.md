# ARQUÍA — Observatorio móvil de la semilla

Panel web estático e instalable como acceso a pantalla de inicio en Android. No modifica el evaluador ni la semilla y no recolecta datos personales.


## Acceso público a la semilla

- [Descarga directa de ARQUÍA-SEED-001](https://github.com/argensite/arquia-eval-001/releases/download/seed-v0.1.0-experimental/ARQUIA-SEED-001-SEMILLA-v0.1.0-experimental.md)
- [Presentación personal de José María Garbini](../../PRESENTACION_PERSONAL_SEMILLA.md)
- [Versión oficial y SHA-256](https://github.com/argensite/arquia-eval-001/releases/tag/seed-v0.1.0-experimental)

## Estado del producto

- **Listo para probar como HTML**: abrir `index.html` desde un servidor web.
- **No instalado en un teléfono ni desplegado automáticamente**: para usarlo como acceso desde Android hay que publicarlo bajo HTTPS y, desde Chrome, elegir «Agregar a pantalla principal» o «Instalar aplicación».
- Repositorio inicial configurado: `argensite/arquia-eval-001`. Se pueden agregar otras fuentes GitHub Releases en el propio panel. No hay datos de descarga de la semilla hasta que exista un archivo identificado por la API.

## Datos incluidos

- Descargas acumuladas de archivos de semilla cuyo nombre incluya `ARQUIA` y `SEMILLA` o `SEED` en las versiones de GitHub Releases supervisadas.
- Descargas de los ZIP principales de **ARQUÍA-EVAL-001** por separado, sin sumar evidencias, hashes, JSON, código fuente automático o repositorios clonados.
- Archivo, release, versión, fecha, enlace, cambios observados, última consulta, fallos, limitaciones y exportación JSON.
- Historial privado por dispositivo (localStorage). Los registros comienzan al abrir el panel y no reconstruyen el pasado; cambios observados no implican descargas únicas ni causalidad.

## Limitaciones y control

La API de GitHub devuelve `download_count` de cada *release asset*. No es el número de personas, instalaciones, lecturas, ejecuciones, adopciones ni descargas de la página web del proyecto. Si la semilla se publica en `arquia.live` u otro servicio, hay que conectar una fuente medible real (p. ej. logs de entrega en el servidor) antes de atribuirle un contador. Tampoco se monitorean de manera fiable descargas de código fuente (GitHub autogenerado) o clones.

El navegador solicita `GET /repos/{owner}/{repo}/releases?per_page=100` sin credenciales; hay un límite anónimo de GitHub por IP. Cobertura de 100 releases o fuentes con fallas se señala como parcial. Para un historial compartido entre dispositivos, el despliegue posterior debe incorporar almacenamiento en servidor y control de integridad.

La información de adopción o pruebas independientes necesita recibos de terceros. **Nunca inferir una adopción a partir de una descarga.**

## Publicación

Subir estos archivos juntos bajo una ruta HTTPS, por ejemplo un directorio de una web o GitHub Pages, y abrir `index.html`. Ningún token, clave ni base de datos es necesario para consultas públicas. Este paquete no incorpora un backend para el servidor que distribuye la semilla ni activa estadísticas de ese servidor.