# Piloto conjunto ARQUÍA y AER-1 · Joint ARQUÍA and AER-1 pilot

## Resultado / Result

El 27 de noviembre de 2026, Brennan Zambo presentó tres huellas de decisión desde AER-1. ARQUÍA emitió los identificadores y mantuvo el registro de custodia bajo su control. Publicó dos aceptaciones y un rechazo registrado antes de liberar los dos recibos de prueba. El verificador devolvió código 0 en la referencia y en el control de doble compromiso. Al sustituir la huella de ingreso por la del otro recibo, devolvió `receipt_mismatch`. [Envío de Brennan](https://github.com/a2aproject/A2A/discussions/2434#discussioncomment-19953726) · [Acuses de custodia](https://github.com/a2aproject/A2A/discussions/2434#discussioncomment-19955053)

Brennan Zambo submitted three decision digests from AER-1. ARQUÍA issued the IDs, held the custody ledger, and published two acceptances and one recorded rejection before releasing the two test receipts. Both the reference and the double-submission control returned exit 0. Substituting the other receipt's ingress hash was detected as `receipt_mismatch`.

| Caso / Case | Custodia / Custody | Verificación / Verification |
| --- | --- | --- |
| Referencia / Reference | Primera huella aceptada / First digest accepted | Exit 0 |
| Doble compromiso / Double submission | Primera aceptada, segunda rechazada y registrada / First accepted, second refused and logged | Exit 0 |
| Sustitución de recibo / Receipt substitution | Huella del otro recibo en la observación de ingreso / Other receipt hash in ingress observation | `receipt_mismatch` |

## Evidencia y reproducción / Evidence and reproduction

1. El registro del publicador contiene los bytes exactos de las decisiones y los recibos preparados. / The publisher archive contains the exact decision and fixture receipt bytes. [Archivo de Brennan fijado por revisión](https://gist.github.com/zambodotdev/fa87ff686619835994223a6c52318bfc/b4ea74bdbae2da4b8f8197ed5418b17dd486d18d)
2. ARQUÍA liberó los mismos bytes desde su cuenta después de cotejar el acuse público. Se observó el ingreso mediante una descarga HTTPS anónima de cada archivo fijado. / ARQUÍA released the same bytes from its account after reading back the public acknowledgment. The evaluator observed ingress via an anonymous HTTPS retrieval of each released file. [Recibos liberados](https://gist.github.com/argensite/cf0b77edd924ef4168917c5438873bfb/a86e0a9ce8e08b83a597f7c4faafda7492601226)
3. Las huellas, las horas de los eventos, los resultados y la evidencia por caso se conservan aquí. / This directory preserves hashes, event times, results and the case files. [Resultados JSON](validation.json) · [Custodia de referencia](ledger-reference.json) · [Observación de referencia](observer-reference.json) · [Custodia del control](ledger-double-submission.json) · [Observación del control](observer-double-submission.json)

Desde la raíz de una copia del [piloto fijado en `22477d6`](https://github.com/argensite/arquia-eval-001/tree/22477d6887303d29758586c3e6017c76817ca307/experiments/custody_pilot), colocá los archivos de custodia, observación y decisión de cada caso en un directorio `evidence/`. / From the root of that checkout, place the ledger, observer and original decision files in `evidence/`.

```sh
python3 -B -m experiments.custody_pilot.pilot verify evidence/ledger-reference.json evidence/observer-reference.json evidence/decision-reference.json
python3 -B -m experiments.custody_pilot.pilot verify evidence/ledger-double-submission.json evidence/observer-double-submission.json evidence/decision-double-submission.json --rejected-digest e51c98a259fdc0c3d319fc01c1d86a63c8e29fc5ab13fd822b232c3b7c643c55
```

## Alcance / Scope

AER-1 operó como publicador. ARQUÍA ejerció ambos roles de su lado, evaluador y custodio, con el registro bajo control separado del publicador. La prueba comprueba el orden respecto a la liberación controlada y la llegada observada, con datos sintéticos. Los bytes que Brennan preparó estaban disponibles antes de ese acto de liberación.

AER-1 operated as publisher. ARQUÍA acted as evaluator and custodian, with the ledger under control separate from the publisher. The test covers ordering relative to the controlled release and observed ingress of synthetic receipts. The publisher fixture bytes were available before that release.
