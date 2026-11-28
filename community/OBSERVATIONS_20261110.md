# Observación externa del 10 de noviembre / External observation, 10 November

El [informe de Gepetto](https://notes.tipiak2000.com/arquia-report-20261107.html)
incorpora una errata del 9 de noviembre y un
[listado de la prueba](https://notes.tipiak2000.com/arquia-probe-20261109.txt).
La reproducción del proyecto confirmó 29/29 para la referencia, 14/28 y 14/29
para la prueba y 15/29 al desactivar el detector temporal. El caso añadido falla
por una revivificación transitoria en el paso 4, sin discrepancia final.

Cuatro hashes del código original coinciden. Los dos archivos reconstruidos
desde el listado formateado tienen hashes distintos de los declarados para los
archivos autónomos; faltan esos bytes y las salidas completas de la ejecución
externa. Se verificó el hallazgo semántico, no la identidad de aquella ejecución
ni la independencia del operador. No se acredita adopción técnica.

The project reproduced the corrected finding in an offline sandbox. The
[dated data record](participant-observations-20261110.json) separates source
identity, regenerated artifacts, observed results and missing evidence.
This concerns historical EVAL-001, not the 14-test SEED-001 simulator. The
[historical evidence index](evidence-index.json) remains intact.
