# Datos sintéticos: qué es cada archivo

> **Maqueta · datos sintéticos.** Ningún paciente es real. Detalle de fuentes y supuestos: [`DATA_CARD.md`](DATA_CARD.md) y [`cupo_espanol_1000/DATA_CARD.md`](cupo_espanol_1000/DATA_CARD.md).

Cada conjunto tiene un **extracto** (lo que leen las reglas) y unas **etiquetas** (la respuesta esperada, escrita aparte de las reglas). La CI y `eval/bucle_estres.py` comparan una con otra: de ahí salen cifras como «1000/1000».

## Los conjuntos

| Carpeta o archivo | Pacientes | Para qué |
|---|---|---|
| `demo_seed.sql` + `demo_etiquetas.csv` | 4 | El caso de Carmen que se ve en la pantalla (Rosa, Manuel, Antonio, Pilar) |
| `ciego/` | 23 | Los 20 casos difíciles de [`docs/SET_CIEGO.md`](../../docs/SET_CIEGO.md): unidades, límites, duplicados, pedidos. Adversarial, **no** a ciegas |
| `notas_dev/` | 12 | Notas clínicas trampa para el lector de notas (negaciones, otra persona, fechas dudosas, un modelo hostil) |
| `aguja/` | 251 | La aguja en el pajar: Amparo, cuyo segundo CAC solo está en una nota |
| `cupo_250.sql` | 250 | Cupo pequeño para contar ruido y tiempo (lo genera `generar_cupo.py`) |
| `cupo_espanol_1000/` | 1.000 | Cupo de AP español calibrado con fuentes publicadas (lo genera `scripts/generar_cupo_espanol.py`) |

## Los archivos de cada carpeta

| Archivo | Qué es |
|---|---|
| `extracto.sql` | El extracto de la historia clínica (subconjunto OMOP: personas, diagnósticos, resultados, fármacos, pedidos, notas) |
| `etiquetas.csv` · `etiquetas_cupo_1000.csv` | Resultado esperado por paciente **con** el lector de notas (S1a, S1b, S1c, S3, S3c, «fuera» o «ninguno») |
| `etiquetas_sin_notas.csv` | Resultado esperado con las notas apagadas: solo las reglas sobre tablas |
| `etiquetas_notas.csv` | Lo que debería decir cada nota (ya realizada, rechazo, Nefrología, nada) |
| `estado_latente.csv` | La «verdad oculta» del generador para cada paciente del cupo de 1.000, para que cualquiera pueda auditar las etiquetas |
| `salidas_oraculo.jsonl` | Salidas perfectas del lector (la etiqueta correcta de cada nota): prueban las reglas sin depender del modelo |
| `salidas_qwen3-4b-instruct-2507.jsonl` | Salidas grabadas del modelo local real (Qwen3-4B); se reproducen sin GPU |
| `salidas_qwen3.8-27b.jsonl` | Salidas grabadas de un modelo mayor, solo como comparación informativa |
| `salidas_hostil.jsonl` | (`notas_dev/`) Un «modelo» que miente a propósito: el código debe impedir que saque a nadie de la lista |
| `generar_*.py` | El generador con semilla: vuelve a crear el conjunto idéntico (para el cupo de 1.000, `python3 scripts/generar_cupo_espanol.py --comprobar` lo verifica) |

El esquema común está en [`../schema.sql`](../schema.sql).
