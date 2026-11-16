# Reglas en SQL

Una consulta por regla, sobre `data/schema.sql`. Definición clínica exacta: [`../docs/REGLAS.md`](../docs/REGLAS.md).

Se ejecutan en este orden con `python ejecutar.py <extracto.sql>`; cada regla escribe filas en la tabla `candidato`.

| Archivo | Regla | Salida |
|---|---|---|
| `00_parametros.sql` | umbrales, códigos LOINC/CIE-10-ES/ATC y vistas de apoyo (`cac`, `fge`, `poblacion`…) | tablas `parametro`, `codigo_regla`, `candidato` |
| `s1a_cac_pendiente.sql` | S1a · sin CAC en >12 meses | filas en `candidato` |
| `s1b_albuminuria_sin_repetir.sql` | S1b · CAC ≥30 mg/g (≥3 mg/mmol) sin repetir >6 meses, sin N18 | igual; unidad desconocida → insuficiente |
| `s3_fge_en_descenso.sql` | S3 · pendiente < −5/año o caída de categoría ≥25 %; S3c · caída aislada >20 % | igual + pendiente calculada |
| `supresion.sql` | extracto incompleto, información insuficiente, pedido pendiente ≤3 meses | vistas `en_lista`, `fuera_de_la_lista` |
| `baseline_fge_menor_60.sql` | filtro básico de 1 variable para comparar | `person_id` |

Regla de oro: el mismo extracto da siempre la misma salida, y volver a ejecutar no duplica pedidos.
Por eso «hoy» es siempre `(SELECT fecha_referencia FROM extract_meta)`, nunca `date('now')`.

Decisiones D1–D5 y C2–C5: firmadas el 14 nov 2026, con su texto en [`../docs/REGLAS.md`](../docs/REGLAS.md).
