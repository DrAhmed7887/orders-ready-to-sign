# Ficha de datos · pacientes sintéticos

- **Origen:** la organización no entregó dataset; el reto incluye un documento con el caso de Carmen (médica de familia) y sus señales ocultas. Todos los pacientes de este repositorio son **inventados** a partir de ese caso y de las reglas de `docs/REGLAS.md`.
- **Datos reales:** ninguno. Ningún registro procede de una historia clínica.
- **Etiqueta obligatoria en pantalla y vídeo:** «Maqueta · datos sintéticos».

## Pacientes de la demo (fijos)
| Paciente | Historia | Regla | Esperado |
|---|---|---|---|
| Manuel, 72, HTA | FGe 78 → 69 → 61 en 2 años | S3 | Grupo 1 · «Función renal en descenso: repetir FGe + CAC» |
| Pilar, 67, DM2 | CAC 85 mg/g hace 9 meses, sin repetir, sin N18; cita hoy | S1b | Grupo 2 · «Repetir CAC» + aviso «hoy en consulta» |
| Rosa, 59, DM2 + HTA | Sin CAC desde hace 18 meses | S1a | Grupo 3 · «Solicitar CAC» |
| Antonio, 64, DM2 | CAC 120 mg/g, repetición ya pedida | suprimido | «Fuera de la lista: pedido ya pendiente» |

## Set adversarial (`ciego/`, 14 nov 2026)
- 23 pacientes inventados que cubren los 20 casos difíciles de `docs/SET_CIEGO.md` (el caso 10 son dos pacientes) y 2 más para llegar a ≥3 por regla. Etiquetas copiadas de la columna «Qué debería pasar» y en `main` antes de ejecutar las reglas (commit `test: set adversarial…`).
- **No es a ciegas:** diseñado internamente conociendo `rules/`. Resultado: 23/23 (`eval/results/ciego.md`).

## Notas en texto libre (lector de notas, 14 nov 2026)
- `notas_dev/`: 12 pacientes, 11 notas (cada una prueba un caso de N1, con trampas: negación, otra persona, inyección, fecha anterior, >12 meses). **Borrador interno** para ajustar el código; nunca se presenta como resultado. Salidas `salidas_oraculo.jsonl` (modelo perfecto, a mano) y `salidas_hostil.jsonl` (un «modelo» que dice «ya realizada» en todo: 0 exclusiones equivocadas).
- `aguja/`: `cupo_250.sql` sin cambios + Amparo (251) + 6 notas (1 aguja, 5 señuelos). Generado por `aguja/generar_aguja.py`. Borrador para la demo; Ahmed lo revisa.
- Todo sintético; ningún paciente real. Las notas ciegas las escribe un autor independiente y las etiqueta Ahmed antes de ejecutar.

## Cupo AP español de 1.000 (`cupo_espanol_1000/`, 14 nov 2026)
- 1.000 adultos sintéticos con estado clínico latente, notas y etiquetas calculadas desde ese estado (nunca desde el SQL). Calibración, fuentes y casos plantados: [`cupo_espanol_1000/DATA_CARD.md`](cupo_espanol_1000/DATA_CARD.md).

## Set de prueba a ciegas (pendiente)
- Lo escribe un autor independiente a partir de una especificación de una página; Ahmed etiqueta cada caso **antes** de ejecutar las reglas.
- Incluye casos difíciles: laboratorio externo, mg/g frente a mg/mmol, fechas duplicadas, pedido ya pendiente, valores límite, inicio reciente de iSRA/iSGLT2, «información insuficiente».
- Resultado = verificación de software, no validación clínica.

## Vuelta 13 (16 nov 2026)
- Las etiquetas del cupo de 1.000 se recalcularon con el oráculo actualizado a la vuelta 13 (independiente del SQL). Cambiaron 8 pacientes; cada cambio sale de una regla firmada.
- El generador daba una ecuación de FGe distinta a cada valor; ahora todos los FGe de un paciente llevan la del primero (mismos sorteos, mismas notas).
- El generador asigna «I12.9» a algunos hipertensos sin ERC; desde la vuelta 13 cuenta como código de ERC. Se mantiene para no mover la semilla.
- `notas_dev`: la etiqueta del paciente 10 pasó de «fuera» a «S3» porque una nota ya no retira un FGe (R5). **Esta etiqueta se cambió después de cambiar la regla**, no antes.
