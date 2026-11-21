# ARQUÍA-EVAL-001 v0.2.4

La candidata agrega una extensión temporal optativa de tres escenarios
sintéticos y siete controles deliberadamente defectuosos. Distingue el permiso
al despachar del permiso cuando se confirma el efecto y prueba comprobantes
tardíos y permisos almacenados durante el mismo turno.

Conserva 29 casos históricos con cinco controles y 34 casos comunitarios
con diez controles. El caso `C29-transient-receipt-renewal` está incluido
desde v0.1.1, a partir del [aporte de Gepetto-tipiak](https://notes.tipiak2000.com/arquia-report-20261107.html).

[Primera ejecución](QUICKSTART.md) · [Batería temporal](TEMPORAL_AUTHORITY.md)

The v0.2.4 candidate adds a separate opt-in temporal suite with three synthetic
scenarios and seven faulty controls. The offline checks use Python 3.10+ and
its standard library. See [Quickstart](QUICKSTART.md) for commands and expected
failure witnesses. Project-side results measure the synthetic contract.
