# Escritura seguida de borrado tras la revocación · Write then delete after revocation

[English](#english) · [Español](#español) · [Design review in A2A](https://github.com/a2aproject/A2A/discussions/2434#discussioncomment-19963501)

## Español

El [ensayo anterior](../observed_effect/README.md) inspecciona el directorio cuando termina el trabajador. Una escritura que se borra antes de esa inspección puede dejar el mismo estado que una escritura bloqueada. Este ensayo traslada la observación al destino que recibe la escritura.

El operador controla un destino de prueba con objetos de bytes en SQLite. Cada escritura aceptada incorpora el objeto y su entrada de auditoría en **una sola transacción**. El destino calcula SHA-256 sobre los bytes que acepta. La revocación y las escrituras quedan en un mismo registro ordenado que admite agregar entradas y conserva las anteriores. El borrado quita el objeto y agrega su propio evento. El verificador usa exclusivamente la exportación del operador para decidir. Una observación incompleta queda inconclusa.

### Repetir localmente

Ejecutá estos comandos desde la raíz de la copia con Python 3.10 o posterior y directorios nuevos.

```sh
python3 -B -m experiments.write_observation.run run reference write-reference
python3 -B -m experiments.write_observation.run run write-delete write-delete
python3 -B -m experiments.write_observation.run run unsealed write-unsealed
python3 -B -m experiments.write_observation.run verify write-delete/journal.json
python3 -B -m unittest -v experiments.write_observation.test_write_observation
```

La tabla en inglés muestra los resultados previstos. Conservá los comandos, códigos de salida y las exportaciones `journal.json` y `verdict.json`. En la referencia y en el control de escritura seguida de borrado, el destino conserva el objeto inicial y ya no tiene el pendiente. La secuencia del destino permite distinguirlos.

## English

The [earlier trial](../observed_effect/README.md) inspects the directory after the worker exits. A write followed by deletion can leave the same final state as a blocked write. This fixture moves observation to the target that accepts the write.

The target operator holds a SQLite-backed byte store. Each accepted write creates a byte object and its journal entry in **one transaction**. The target computes SHA-256 over the accepted bytes. Revocation and writes share one append-only sequence. Deletion removes the object and appends its own event. The verifier reads the operator’s exported journal alone. An unaccounted interval is inconclusive.

### Run locally

Run these commands from the checkout root with Python 3.10 or later and fresh output directories.

```sh
python3 -B -m experiments.write_observation.run run reference write-reference
python3 -B -m experiments.write_observation.run run write-delete write-delete
python3 -B -m experiments.write_observation.run run unsealed write-unsealed
python3 -B -m experiments.write_observation.run verify write-delete/journal.json
python3 -B -m unittest -v experiments.write_observation.test_write_observation
```

| Case | Expected outcome | Exit |
| --- | --- | ---: |
| `reference` | The worker withholds the queued write. The complete sequence has no accepted write after revocation. | 0 |
| `write-delete` | The worker sends a write and then a deletion. The journal still identifies the accepted post-revocation write and its hash. | 1 |
| `unsealed` | The operator withholds the closing boundary. Observation is incomplete. | 3 |

Exit 2 is an execution error. Keep the commands, exit codes, `journal.json` and `verdict.json` for each run. The reference and faulty case both finish with the prior object present and the pending slot empty. The tests also force a journal insertion to fail and check that the associated write rolls back.

### Run with separate operators

1. From the same pinned revision the target operator runs `python3 -B -m experiments.write_observation.target start operator-run` and then `python3 -B -m experiments.write_observation.target revoke operator-run`. Use a fresh private directory for each case and keep its database under the target operator’s control.
2. After the operator confirms revocation, the worker operator runs `python3 -B -m experiments.write_observation.run worker reference > requests.jsonl` or uses `worker write-delete` for the fault. Send the complete synthetic JSONL stream to the target operator. The final frame marks the end of the worker’s request stream.
3. The target operator runs `python3 -B -m experiments.write_observation.target receive operator-run < requests.jsonl`. After successful receipt, close the interval with `python3 -B -m experiments.write_observation.target seal operator-run`. Export the record with `python3 -B -m experiments.write_observation.target export operator-run > journal.json`.
4. Share the export directly from the target operator and verify it with `python3 -B -m experiments.write_observation.run verify journal.json`. If transport or observation was incomplete, leave the journal unsealed and record the gap. Keep the participants, revision, commands, exit codes and export with the result.

The local runner uses separate processes under one local operator. The separate-operator procedure depends on the target owner controlling the byte store and journal and supplying the export. The fixture tests synthetic objects written through that target, with revocation ordered by the operator. The worker modes are deterministic controls.
