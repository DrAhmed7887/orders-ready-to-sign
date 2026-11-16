# Ficha de datos · Cupo AP español, 1.000 pacientes (100 % sintético)

> **Maqueta · datos sintéticos.** Ningún registro procede de una historia clínica. Nombres = combinaciones de nombres y apellidos frecuentes; «SIP-S…» = identificador inventado (tabla `observation`, `SIP_SINTETICO`).

- **Generador:** `scripts/generar_cupo_espanol.py`, semilla **2026**, fecha del extracto **2026-11-14**. Determinista: `python3 scripts/generar_cupo_espanol.py --comprobar` regenera en memoria y falla si algo difiere (lo comprueba la CI).
- **Tablas:** `person`, `observation` (SIP sintético), `condition_occurrence` (CIE-10-ES), `measurement` (FGe y CAC, LOINC), `drug_exposure` (ATC), `pedido_pendiente`, `visit_occurrence` (citas de hoy) y `note` (evolutivos en texto libre, con abreviaturas de AP).
- **Archivos:** `extracto.sql` · `etiquetas_cupo_1000.csv` (lista esperada con lector de notas) · `etiquetas_sin_notas.csv` · `etiquetas_notas.csv` (lo que debe quedar de cada nota tras las comprobaciones del código) · `salidas_oraculo.jsonl` (un lector perfecto: comprueba el código, no el modelo) · `estado_latente.csv` (el estado clínico de cada paciente y por qué tiene su etiqueta) · `RESUMEN.md` (cifras del cupo generado).

## Cómo se hacen las etiquetas (independientes del SQL)

1. Cada paciente tiene un **estado clínico latente** (DM2, HTA, ERC real, trayectoria del FGe, albuminuria, pedidos, notas).
2. El generador **escribe** ese estado como lo haría una historia real, con sus defectos.
3. Las etiquetas se calculan **en Python, desde el estado latente y los criterios firmados de `docs/REGLAS.md`**. El generador nunca ejecuta `rules/*.sql` ni lee su salida. Cuando el SQL y las etiquetas no coinciden, uno de los dos tiene un error: así aparecieron los fallos del bucle de estrés (`eval/stress_loop_report.json`).

**Límite:** las etiquetas las escribió el mismo asistente que conoce las reglas (no es un set a ciegas), y los criterios clínicos son los firmados, no un juicio clínico nuevo. Verificación de software, no validación clínica.

## Calibración (fuentes comprobadas el 14 nov 2026)

| Variable | Objetivo usado | Fuente | Cupo generado |
|---|---|---|---|
| Edad media · mujeres | 57,9 años · 54,5 % | IBERICAN, Llisterri et al., Med Clin 2020, PMID 32414634, doi:10.1016/j.medcli.2020.03.005 («mean age 57.9±14.8 years; 54.5% women»). Cohorte de riesgo CV reclutada en AP, no un cupo completo | 58,1 años · 56,5 % |
| HTA registrada | 19,4 % | Ministerio de Sanidad, BDCAP «Indicadores clínicos 2016», p. 16 («En mayores de 14 años la prevalencia registrada es del 19,4%») | 19,6 % |
| Dislipemia | 19,9 % | BDCAP 2016, p. 18 («trastorno del metabolismo lipídico al 19,9% de la población») | 19,3 % |
| DM2 registrada | 7,4 % | Ministerio de Sanidad, nota de prensa 9 mar 2016 (BDCAP 2012, >14 años); Girona Sud, BMC Prim Care 2025, PMID 41276836: DM2 7,1 % | 7,4 % |
| DM1 | 0,4 % | Girona Sud, tabla 1 («T1D 1,034 (0.4)») | 0,2 % |
| ERC de laboratorio (latente) | 14,4 % | IBERICAN («14.4% (95% CI: 13.6-15.1) had CKD»; FGe <60 y/o albuminuria ≥30 mg/g) | 14,3 % |
| ERC sin código N18 | 64–68 % de la ERC | BIG-PAC, Santamaría et al., Clin Kidney J 2026, PMID 42459742, doi:10.1093/ckj/sfag213 (67,77 % en 2018; 64,05 % en 2023; estudio financiado por AstraZeneca) | 71 % de la ERC real |
| DM2/HTA sin CAC en 12 meses | 24,5 % + 3,9–7,6 % nunca | Alicante, López-Garrigós et al., Diagnostics 2026, PMID 41515503 (24,5 %, otra población elegible); Girona Sud, tabla 2 (CAC alguna vez: DM2 96,09 %, HTA 92,36 %) | 35 % de 230 |
| Pendientes, caídas, pedidos, citas, notas | — | **supuesto** (declarado en `CALIBRACION` del generador) | — |

Cifras del cupo generado: `RESUMEN.md` (semilla 2026). «ERC real» es el estado latente del muestreo; los casos plantados con un laboratorio alterado (agujas, límites) no cambian esa marca, así que la ERC de laboratorio visible en el extracto puede ser algo mayor. Tres cifras quedan fuera del objetivo: DM1 0,2 % (n = 1.000 da muy pocos casos), ERC sin código 71 % y DM2/HTA sin CAC 35 % (los casos plantados añaden pacientes sin código y sin CAC reciente, a propósito).

### Cifras propuestas en el encargo que NO se usan (no se encontraron en la fuente)

| Propuesta | Qué dice la fuente |
|---|---|
| HTA 18,4 % · dislipemia 21,2 % (BDCAP) | BDCAP 2016: 19,4 % (>14 años) y 19,9 %; nota de prensa 2012: 18,3 % y 17,4 %. No se abrieron las tablas BDCAP 2017–2024 |
| DM2 ~11 % · DM1 ~0,8 % | Registrada 6,7–7,4 %; 13,8 % es la prevalencia medida con SOG en Di@bet.es (PMID 21987347), con 6,0 % no conocida. DM1 0,4 % (Girona) |
| ERC codificada 3–4 % · «82 % sin codificar» | 82,04 % en BIG-PAC 2018 es **sin código de etiología**, no sin código de ERC (Santamaría, Nefrologia 2025, PMID 40518657). Sin código de ERC: 64–68 % |
| 30–39 % sin CAC entre DM2/HTA | Girona Sud: 3,9 % (DM2) y 7,6 % (HTA) nunca medidos; el 30–39 % corresponde a dislipemia, ≥60 años u obesidad |

## Lo que se ha planteado a propósito (ver `estado_latente.csv`, columna `escenario`)

- **10 agujas tipo Amparo** (4 tablas + nota): DM2/HTA sin N18, CAC alterado de laboratorio hace 8–11 meses («analítica aceptable»), metformina, nada pedido, y una nota con un CAC alterado traído de fuera ≥3 meses después → S1c. Dos en mg/mmol; tres citadas hoy.
- **2 notas en conflicto:** una nota limpia (persistencia) y otra posterior con ITU o fiebre → sigue siendo S1c.
- **Señuelos:** causa transitoria (ITU, fiebre), nota <3 meses después, CAC normal posterior (retira), CAC sin unidad, negación, plan («se solicita»), otra persona (marido, hija), 3 inyecciones de órdenes al modelo, rechazo, Nefrología, fecha relativa («hace 2 años»), intervalo («entre julio y agosto»), fecha futura, nota de hace >12 meses (no se lee), FGe traído de fuera (retira una caída aislada; en un descenso, el FGe se da por hecho y se pide solo el CAC).
- **Límites:** CAC 29 / 30 / 300 mg/g y 2,9 / 3,0 mg/mmol; FGe 62 → 58 (con y sin DM2/HTA); pendiente −5,4 frente a −4,6; caída única >20 % frente a tendencia confirmada en >12 meses; pedido vigente, caducado y con fecha futura.
- **Defectos de registro:** unidades mg/g frente a mg/mmol, «MG/G», «mg/g␠», «mg/L» (desconocida), sin unidad, sin resultado; FGe con espacios en la unidad, sin unidad o «mL/min»; dos FGe y dos CAC el mismo día (C2); códigos «␠E11.9», «e11.9», «␠N18.3»; E11.22 sin N18; combinación A10BD; DM1 sin HTA (fuera de la población firmada de S1a).
