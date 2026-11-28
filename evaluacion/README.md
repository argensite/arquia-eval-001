# Poné a prueba ARQUÍA · Put ARQUÍA to the test

[Español](#español) · [English](#english) · [Materiales y licencias / Materials and licenses](MATERIALES.md) · [Mapa / Coverage](MAPA.md) · [Aportes / Contributions](https://github.com/argensite/arquia-eval-001/blob/main/evaluacion/APORTES.md) · [Resultados / Results](RESULTADOS.md) · [Índice JSON / JSON index](index.json) · [Historial / Changes](CAMBIOS.md)

## Español

¿Qué observarías para demostrar que una regla de gobernanza falló en tu agente? Por ejemplo, podés simular una asignación que parece válida hasta que aparece una parte afectada que quedó fuera de la decisión. Definí de antemano qué tendría que cambiar y qué evidencia mostraría que el sistema siguió adelante sin reconsiderarla.

Abrimos una convocatoria gratuita, abierta y sin fines de lucro para poner a prueba ARQUÍA en todo su alcance: arquitectura de gobernanza, ética relacional 0-1-2-3 y las hipótesis que las llevan a sistemas de agentes. ARQUÍA aporta las publicaciones, herramientas reutilizables y ayuda técnica a pedido. Podés elegir cualquier regla o combinación, cuestionar cómo está formulada, fijar tus casos y criterios de fallo y correrlos en tu máquina, tu fork o tu CI. No hace falta inscribirse, usar un modelo determinado ni pedir permiso para publicar tu informe.

1. Elegí una pregunta en el [mapa de la especificación](MAPA.md). Identificá versión, sección, hipótesis y límite de observación. Antes de correr, anotá qué evidencia cuenta como éxito, fallo o resultado inconcluso. Si comparás dos configuraciones, declarales la misma tarea e información y registrá presupuesto, costos y diferencias.
2. Usá tu agente o simulador con datos sintéticos o anonimizados. Guardá las observaciones del entorno, las decisiones y, cuando existan, los efectos que pueda verificar el evaluador. Las baterías publicadas son [ejemplos opcionales](INTEGRACION.md). Para comprobar tus propios criterios sobre JSON, podés reutilizar el [comparador local](INTEGRACION.md#casos-propios--your-own-cases) o elegir tu propia herramienta.
3. Guardá versión, entorno, comandos, salidas y códigos de retorno. Buscá también reglas en conflicto, criterios ambiguos y falsos positivos del evaluador. Publicá, si querés, resultados negativos, parciales, contradictorios o inconclusos, con la evidencia que los sostiene. Conservás el control de tu informe y podés enlazar tu publicación original.
4. Compartí el informe o pedí ayuda técnica. La sección [Compartir y actualizar un aporte](#compartir-y-actualizar-un-aporte) explica cómo hacerlo y cómo seguir los avances de otros equipos.

**Prueba de dos minutos.** Con Git y Python 3.10 o posterior, descargá el ejemplo fijado en la [guía de integración](INTEGRACION.md#inicio-rápido--quick-start), o descomprimí el [kit de la convocatoria](https://github.com/argensite/arquia-eval-001/releases/tag/open-evaluation-2026-11-26). Desde la raíz de esa descarga:

```sh
python3 evaluacion/compare.py evaluacion/ejemplos/casos.json evaluacion/ejemplos/observaciones.json
```

La muestra deja a la vista un caso que coincide, uno que falla y uno inconcluso. Sale con código 1 a propósito. El [registro público](RESULTADOS.md) indica qué se corrió y qué falta probar. Los resultados sintéticos se limitan a las propiedades observadas en cada caso. Si te sirve, compartí esta convocatoria, tus casos y resultados o avisale a otro equipo que pueda aprovecharlos.

Para probar una escritura en cola después de revocar su permiso, seguí el [ensayo de efecto observado](../experiments/observed_effect/README.md). El observador lee los archivos escritos y comprueba por separado el recibo tardío.

Si una escritura puede borrarse antes de la inspección, usá el [piloto con dos operadores](resultados/escritura-conjunta-20261127/README.md). El diario del destino permite verificar si hubo una escritura después de la revocación, incluso cuando ambos destinos terminan con el mismo contenido.

### Compartir y actualizar un aporte

1. Abrí el [formulario bilingüe](https://github.com/argensite/arquia-eval-001/issues/new?template=evaluation-report.yml) con tu cuenta de GitHub. Podés compartir una pregunta, un diseño de prueba, una crítica, una corrida o un pedido de ayuda. Indicá qué versión estudiaste, qué observaste y qué sigue pendiente. Podés enlazar un informe publicado en otro sitio. Usá sólo información que puedas hacer pública.
2. Guardá el enlace al aporte. Cuando encuentres algo nuevo, editá el texto de ese mismo aporte y agregá la fecha, qué cambió y el enlace a la evidencia, si existe. Podés usar los comentarios del mismo hilo para conversar. Si tu equipo publica el informe en otro sitio, actualizá también el enlace o el resumen en el hilo.
3. Cualquiera puede leer el [listado público de aportes](https://github.com/argensite/arquia-eval-001/blob/main/evaluacion/APORTES.md) y abrir cada hilo sin iniciar sesión. El listado se actualiza automáticamente. Cada aporte figura como reportado hasta que el equipo del proyecto confirme una reproducción y publique su evidencia en el hilo. El [registro de resultados](RESULTADOS.md) reúne la evidencia documentada, con su procedencia y alcance.

## English

What would you need to observe to show that a governance rule failed in your agent? Try a synthetic allocation that looks valid until you reveal an affected party left out of the decision. Decide beforehand what should change and what would show that the system proceeded without reconsidering.

This is an open, free, nonprofit call to test the full scope of ARQUÍA: its governance architecture, 0-1-2-3 relational ethics, and the engineering hypotheses that connect them to agent systems. ARQUÍA provides the papers, reusable tools, and technical help on request. Pick any rule or combination, challenge its wording, define your own cases and failure criteria, and run them on your machine, fork, or CI. You can publish your report without enrolling, using a particular model, or seeking approval.

1. Pick a question from the [specification map](MAPA.md). Record the version, section, hypothesis, and observation boundary. Specify what counts as a pass, a failure, or an inconclusive outcome before running. For comparative trials, give both variants the same task and information and record budgets, costs, and differences.
2. Use your own agent or simulator with synthetic or anonymized data. Preserve observations, decisions, and any effects the evaluator can verify. Published suites are [optional examples](INTEGRACION.md). For your own JSON observations, reuse the [local comparator](INTEGRACION.md#casos-propios--your-own-cases) or use your own tooling.
3. Keep the versions, environment, commands, outputs, and exit codes. Look for conflicting rules, ambiguous criteria, and false positives in the evaluator itself. Share negative, partial, contradictory, or inconclusive results with the evidence behind them. You control your report and can link to it wherever you published it.
4. Share your report or request technical help. See [Share and update a contribution](#share-and-update-a-contribution) for instructions and to follow other teams' progress.

**Two-minute example.** With Git and Python 3.10 or newer, use the pinned example in the [integration guide](INTEGRACION.md#inicio-rápido--quick-start) or unpack the [open call kit](https://github.com/argensite/arquia-eval-001/releases/tag/open-evaluation-2026-11-26). From the download root:

```sh
python3 evaluacion/compare.py evaluacion/ejemplos/casos.json evaluacion/ejemplos/observaciones.json
```

The sample shows one matching outcome, one failure, and one inconclusive result. It exits with status 1 by design. The [public record](RESULTADOS.md) shows what was run and what remains open. Synthetic results apply to the observed properties of each scenario. If this is useful, share the call, your own cases and results, or tell another team that could put them to work.

To test whether a queued write takes effect after revocation, run the [observed-effect trial](../experiments/observed_effect/README.md). The observer reads the files and corroborates the delayed receipt separately.

If a write can be deleted before inspection, use the [two-operator pilot](resultados/escritura-conjunta-20261127/README.md). The target journal lets you check whether a write was accepted after revocation even when both targets end with the same contents.

### Share and update a contribution

1. Open the [bilingual form](https://github.com/argensite/arquia-eval-001/issues/new?template=evaluation-report.yml) with your GitHub account. Share a question, a test design, a critique, a run, or a request for help. Say which version you studied, what you observed, and what remains open. You can link to a report you published elsewhere. Share only information you can make public.
2. Save the link to your contribution. When you have a new finding, edit the original contribution and add the date, what changed, and a link to any evidence. Use comments in the same thread for discussion. If your team publishes its report elsewhere, update the link or summary in the thread as well.
3. Anyone can read the [public contribution list](https://github.com/argensite/arquia-eval-001/blob/main/evaluacion/APORTES.md) and open each thread without signing in. The list updates automatically. Contributions appear as reported until the project team confirms a reproduction and posts its evidence in the thread. The [results record](RESULTADOS.md) documents evidence along with its provenance and scope.
