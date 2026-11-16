# Set de prueba a ciegas · especificación (una página)

**Quién:** un autor independiente escribe los pacientes; Ahmed escribe la etiqueta de cada uno **sin ver la salida de las reglas**; nadie ejecuta las reglas sobre el set hasta que las etiquetas estén en `main`. El orden de los commits lo demuestra.
**Qué prueba:** que el código hace lo que dicen las reglas firmadas (`docs/REGLAS.md`). Es verificación de software, no validación clínica.

## Archivos
| Archivo | Lo escribe | Contenido |
|---|---|---|
| `data/synthetic/ciego/extracto.sql` | Autor independiente | `INSERT`s sobre `data/schema.sql` (mismo formato que `demo_seed.sql`), `fecha_referencia = '2026-11-14'`, `fuente = 'sintetico_ciego'` |
| `data/synthetic/ciego/etiquetas.csv` | Ahmed | `person_id,esperado,fuente` con `esperado` ∈ `S1a`, `S1b`, `S3`, `S3c`, `fuera`, `ninguno` (regla **principal** esperada) |

Ejecutar, solo después del commit de las etiquetas:
```bash
python3 eval/evaluar.py data/synthetic/ciego/extracto.sql data/synthetic/ciego/etiquetas.csv -o eval/results/ciego.md
```

## Tamaño y reparto
20–30 pacientes. Al menos 3 por regla (S1a, S1b, S3, S3c), al menos 3 que deben quedar **fuera** y al menos 5 que **no deben avisar**. Nombres inventados, edades 45–85, DM2 / HTA / ambas.

## Casos difíciles que tienen que estar (uno por línea como mínimo)
| # | Caso | Qué debería pasar según las reglas |
|---|---|---|
| 1 | CAC exactamente 30 mg/g hace 7 meses | S1b (≥30) |
| 2 | CAC 29 mg/g hace 7 meses | nada por S1b |
| 3 | CAC 4 mg/mmol hace 7 meses (laboratorio externo) | S1b (umbral 3 mg/mmol) |
| 4 | CAC con unidad rara (`mg/dL`) | fuera · información insuficiente |
| 5 | CAC sin resultado numérico | fuera · información insuficiente |
| 6 | CAC alterado con código N18 | no S1b (ya diagnosticada) |
| 7 | CAC alterado y otro normal después | nada |
| 8 | CAC alterado, repetición ya pedida hace 2 semanas | fuera · pedido pendiente |
| 9 | CAC alterado, pedido de repetición de hace 5 meses | S1b (el pedido ya no vale) |
| 10 | Último CAC hace 11 meses / hace 13 meses | nada / S1a |
| 11 | Sin DM2 ni HTA pero FGe 55 | S1a (entra por FGe <60) |
| 12 | 3 FGe en exactamente 12 meses, pendiente < −5/año | S3 |
| 13 | 3 FGe en 11 meses | no S3 |
| 14 | Dos FGe el mismo día (duplicado) | se promedian; no cambia la regla |
| 15 | FGe en unidad rara | fuera · información insuficiente |
| 16 | Caída aislada >20 % entre los dos últimos FGe | S3c |
| 17 | S3 con inicio de iSRA o iSGLT2 hace 2 meses | S3 **con** el aviso del fármaco, no suprimido |
| 18 | S3 con CAC ya pedido | S3, pide solo FGe |
| 19 | S3 con FGe y CAC ya pedidos | fuera · pedido pendiente |
| 20 | Paciente con dos hallazgos (S3c + S1b) | principal S3c; S1b en «También» |

## Reglas para quien escribe los pacientes
- No mirar `rules/` mientras escribe los casos: se escriben desde esta tabla y `docs/REGLAS.md`.
- Ningún dato real, ningún nombre de paciente real.
- Fechas siempre `AAAA-MM-DD`; si una fecha es imposible, el extracto se rechaza (eso también se puede probar aparte).
