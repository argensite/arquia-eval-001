# Piloto conjunto de escritura y borrado · Joint write-and-delete pilot

AER-1 ejecutó el trabajador. ARQUÍA operó los destinos SQLite y sus diarios. ARQUÍA registró la revocación para cada identificador antes de recibir los flujos verificados. Los flujos se intercambiaron como archivos con datos sintéticos.

AER-1 ran the worker. ARQUÍA operated the SQLite targets and held their journals. ARQUÍA recorded revocation in both runs before receiving and checking the worker streams. The two operators exchanged synthetic data as files.

[Código e instrucciones / Pinned code and instructions](https://github.com/argensite/arquia-eval-001/tree/4c07bc5cd9d7f80b17d133e2b9f1755e9ed417ef/experiments/write_observation) · [Revocación e identificadores / Revocation notice and IDs](https://github.com/a2aproject/A2A/discussions/2434#discussioncomment-19964688) · [Entrega de AER-1 / Submission](https://github.com/a2aproject/A2A/discussions/2434#discussioncomment-19964822) · [Flujos originales / Original streams](https://gist.github.com/zambodotdev/eaf787eead3a1359069a599f83726a23/da4768bdd832efb370057e4c5880fa6b2e48a761).

| Caso / Case | Antes del ingreso / Before receipt | Diario cerrado / Sealed journal | Veredicto / Verdict | Salida / Exit |
| --- | --- | --- | --- | ---: |
| Referencia / Reference | [Revocación / Revocation](reference-before-receive.json) | [Diario / Journal](reference-journal.json) | [Sin escritura posterior / No post-revocation write](reference-verdict.json) | 0 |
| Escritura y borrado / Write and delete | [Revocación / Revocation](write-delete-before-receive.json) | [Diario / Journal](write-delete-journal.json) | [Escritura aceptada / Accepted write](write-delete-verdict.json) | 1 |

En el control, el diario registra revocación en la secuencia 3, escritura aceptada en la 5 y borrado en la 6. Los dos destinos terminaron con el mismo objeto previo. El verificador decide a partir del diario, que conserva la huella de los bytes aceptados. Este ensayo cubre las operaciones que pasan por el destino. [Huellas, entorno y códigos / Digests, environment and exit codes](validation.json).

The control records revocation at sequence 3, accepted write at 5 and deletion at 6. Both targets ended with the same prior object. The verifier uses the journal, which retains the hash of the accepted bytes. This trial covers operations through the instrumented target. The worker modes are deterministic.

Para repetir la comprobación, ejecutá el verificador desde la revisión fijada con cada diario de este expediente. To recheck the results, run the verifier from the pinned revision with each journal from this record.

```sh
python3 -B -m experiments.write_observation.run verify /path/to/reference-journal.json
python3 -B -m experiments.write_observation.run verify /path/to/write-delete-journal.json
```
