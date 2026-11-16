# Rendimiento sobre un cupo sintético

Extracto `data/synthetic/cupo_250.sql` · **250 pacientes** con DM2 y/o HTA.

- **85 pacientes con un pedido preparado (34 %)**, 8 de ellos con más de un hallazgo agrupado; 3 citados hoy.
- Filtro básico (último FGe <60): 9 pacientes, 6 de ellos también en la lista.

| Regla principal | Pacientes |
|---|---|
| S1a | 50 |
| S1b | 13 |
| S3 | 22 |

| Fuera de la lista | Pacientes |
|---|---|
| Pedido ya pendiente | 16 |

**Estos recuentos reflejan los parámetros de entrada del generador, no un hallazgo:** no son la carga de trabajo esperada de un cupo real.

_Comprobación de ruido con parámetros declarados en la cabecera del extracto (fuente o «supuesto»). No es validación ni calibración. Datos sintéticos._
