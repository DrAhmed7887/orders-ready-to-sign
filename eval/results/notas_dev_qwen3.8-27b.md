# Evaluación frente a etiquetas

Extracto `data/synthetic/notas_dev/extracto.sql` · etiquetas `data/synthetic/notas_dev/etiquetas.csv` (escritas antes de ejecutar las reglas).

**11 de 12** casos coinciden exactamente (regla principal o «fuera de la lista»). Regla distinta de la esperada: 0.

| | Reglas | Filtro básico (último FGe <60) |
|---|---|---|
| Avisos correctos | 10 | 0 |
| Falsos avisos | 1 | 0 |
| Perdidos | 0 | 10 |
| Callados correctos | 1 | 2 |

## Discrepancias
- person_id 8: esperado fuera, obtenido S1a

_Verificación de software frente a las reglas firmadas, no validación clínica. Datos sintéticos._
