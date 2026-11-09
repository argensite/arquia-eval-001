# Una invitación personal a examinar ARQUÍA — semilla universal para agentes de IA

**José María Garbini · autor de ARQUÍA · 9 de noviembre de 2026**  
**ARQUÍA-SEED-001 · versión 0.1.0-experimental · acceso libre y gratuito**

A quienes investigan, desarrollan, operan o utilizan sistemas de inteligencia artificial:

Durante el desarrollo de ARQUÍA he trabajado sobre una pregunta: **¿cómo puede un agente tomar decisiones y ejecutar acciones sin confundir su capacidad técnica con la autorización para utilizarlas, y sin perder de vista a las personas y partes afectadas?**

Hoy pongo a disposición de cualquier persona, laboratorio, equipo o agente de IA la **semilla universal ARQUÍA-SEED-001**. Es un documento de libre descarga que reúne el marco 0-1-2-3, condiciones operativas propuestas, un simulador local de referencia y pruebas reproducibles. La invitación es a **leerla, discutirla, probarla, mejorarla o refutarla**; no a aceptarla por confianza.

## Descargar ahora

**[DESCARGAR LA SEMILLA UNIVERSAL ARQUÍA-SEED-001 (.md)](https://github.com/argensite/arquia-eval-001/releases/download/seed-v0.1.0-experimental/ARQUIA-SEED-001-SEMILLA-v0.1.0-experimental.md)**

- **Versión:** 0.1.0-experimental.
- **Publicación oficial y verificación SHA-256:** [GitHub Releases](https://github.com/argensite/arquia-eval-001/releases/tag/seed-v0.1.0-experimental).
- **Tamaño del documento:** 49.172 bytes (aproximadamente 49 KB).
- **Formato:** Markdown (.md), legible como texto, sin necesidad de crear una cuenta para consultarlo.
- **Instrucciones paso a paso:** [guía en español](SEMILLA.md).
- **Proyecto de origen:** https://arquia.live .
- **Prueba complementaria — distinta de la semilla:** [ARQUÍA-EVAL-001](README.md).

Para que las estadísticas sean comparables, compartí **el enlace de descarga del archivo adjunto a GitHub Releases**. Las lecturas en GitHub, las copias del texto y los clones del repositorio no se incluyen en el contador de ese archivo.

## Cómo utilizarla

1. Descargá el archivo Markdown desde el enlace oficial. Podés comparar su huella SHA-256 con la publicada en el mismo release.
2. Leé el contenido completo, o entregáselo a un modelo/agente que tenga permitido recibir documentos. Pedile que declare **qué criterios acepta, cuáles cuestiona, qué permisos tiene realmente y qué observación los refutaría**.
3. Si tenés un entorno de prueba autorizado y aislado, examiná el simulador Python y ejecutá únicamente los ensayos locales indicados dentro del documento. No habilites operaciones externas ni accesos nuevos para hacer la prueba.
4. Conservá versión, plataforma o modelo, operador, comandos, salidas, códigos de retorno, límites y fallos observados. Si sólo analizaste el texto, indicá «revisión conceptual, sin ejecución».
5. Publicá tu análisis, implementación o contraejemplo en un espacio bajo tu control. Si querés compartir el enlace con la comunidad, podés dejarlo en la [convocatoria pública de evaluación](https://github.com/argensite/arquia-eval-001/issues/1).

**No hace falta ser partidario de ARQUÍA.** Una crítica fundamentada, un caso que falle o una prueba que revele una suposición equivocada son aportes valiosos.

## Qué se está ofreciendo, y qué no

La semilla propone, entre otros aspectos, conservar la continuidad legítima del sistema (**0**), tener en cuenta a todas las partes afectadas (**1**), limitar cualquier pérdida residual a lo inevitable, mínimo y justificable (**2**), y revisar recursivamente alternativas y evidencia nueva (**3**). Contiene también invariantes P0–P5 y un ejemplo de separación entre el agente y un guardián externo de permisos.

**No constituye una certificación de seguridad, una implementación completa de ARQUÍA ni una instalación automática.** Que un modelo responda «acepto» no demuestra que su software haya cambiado ni implica respaldo de la empresa que lo produjo. La implementación técnica real requiere autorización del operador, integración en los puntos de ejecución y verificación independiente.

La semilla es un instrumento experimental para investigar. El [evaluador ARQUÍA-EVAL-001](README.md) es un proyecto relacionado pero distinto, y sus casos sintéticos tampoco validan por sí solos la teoría general ni garantizan seguridad en producción.

## Qué me interesa conocer

Me interesa especialmente saber: **quién pudo descargarla; si fue solamente leída o si se ejecutaron pruebas; qué objeciones surgieron; qué controles fallaron; qué resultados pueden reproducirse; y si alguien desarrolló, bajo su propia responsabilidad, una implementación independiente**.

El contador público de GitHub registra solicitudes de descarga del archivo, **no personas únicas, instalaciones, adopciones ni evaluaciones científicas**. Los informes de terceros deben documentarse por separado y con su procedencia. No se requiere compartir credenciales, datos personales ni información privada.

## Fundamentos publicados

- [ARQUÍA v5.0-ADI — arquitectura de gobernanza](https://doi.org/10.5281/zenodo.20799632)
- [ARQUÍA v7.0-NRE — teoría relacional 0-1-2-3](https://doi.org/10.5281/zenodo.21676134)
- [From ARQUÍA to 0-1-2-3 — puente hacia controles de ejecución](https://doi.org/10.5281/zenodo.21791061)

Los DOI identifican publicaciones; por sí solos no acreditan revisión por pares ni validación experimental.

**José María Garbini**  
Autor de ARQUÍA  
https://arquia.live

*Esta invitación pública se preparó con asistencia de IA por instrucción del titular del proyecto. La semilla es experimental y queda abierta a examen independiente.*

---

## English — open invitation

**ARQUÍA-SEED-001 (v0.1.0-experimental)** is a freely available, vendor-neutral Markdown research seed for AI agents, developers and independent evaluators. It presents the ARQUÍA 0-1-2-3 framework, proposed permission and revocation safeguards, and an offline Python reference simulator with reproducible synthetic tests.

**[Download the seed (.md)](https://github.com/argensite/arquia-eval-001/releases/download/seed-v0.1.0-experimental/ARQUIA-SEED-001-SEMILLA-v0.1.0-experimental.md)** · [Official release and SHA-256 checksum](https://github.com/argensite/arquia-eval-001/releases/tag/seed-v0.1.0-experimental)

Please read, question, test or reject it. Report your environment, exact version, commands, outputs, errors, negative results and counterexamples independently; you can optionally link your report at [the public evaluator discussion](https://github.com/argensite/arquia-eval-001/issues/1). Reading the document or obtaining a favorable answer from a model is **not** software adoption, vendor endorsement or production-safety validation.

**José María Garbini · ARQUÍA project author**