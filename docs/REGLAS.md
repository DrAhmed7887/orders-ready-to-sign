# Reglas clínicas · firmadas 13 nov 2026 · decisiones D1–D5 y C2–C5 firmadas 14 nov 2026

Firmadas por el clínico del equipo. Cualquier cambio de umbral pasa por él y queda anotado aquí con la fecha.
Cada aviso dice «revisar / repetir / valorar»: nunca un diagnóstico ni un fármaco.

## Construimos este fin de semana (en este orden)

### S1a · Cribado que nunca se pidió → grupo 3 «Prueba pendiente»
- **Población:** DM2, HTA o FGe <60.
- **Disparador:** ningún CAC registrado en los últimos **12 meses**.
- **Preparado:** «Solicitar CAC».
- **Fuente:** PROT-AP ERC 2025 (Conselleria de Sanitat): «No se recomienda omitir el cribado anual de ERC en población de riesgo (p.e: HTA, DM2) mediante la determinación del FGe y el CAC».

### S1b · Albuminuria que nadie repitió → grupo 2 «Sin seguimiento»
- **Disparador:** CAC ≥30 mg/g (A2/A3) **y** sin CAC posterior en **>6 meses** **y** sin código de ERC (CIE-10 N18).
- **Preparado:** «Albuminuria sin confirmar: repetir CAC en primera orina de la mañana» (vuelta 13, R7; KDIGO 2024 PP 1.3.1.2 y tabla 16 en la nota). A3 (≥300) sale primero.
- **Fuente:** KDIGO 2024, tabla 1 (A1 <30, A2 30–299, A3 ≥300 mg/g); PP 1.1.3.2 («do not assume chronicity based upon a single abnormal level»).
- **Decisión de diseño:** la ventana de >6 meses es nuestra; la guía no da cifra.

### S3 · Función renal que cae en silencio → grupo 1 «Empeorando»
- **Disparador:** ≥3 valores de FGe que abarcan **≥12 meses** con pendiente **< −5 ml/min/1,73 m²/año**, **o** paso a peor categoría G con caída **≥25 %** desde el primer valor.
- **Preparado:** «Función renal en descenso: repetir FGe + CAC, valorar».
- **Caída aislada >20 %:** «Cambio >20 %: repetir analítica» (no es aviso de tendencia).
- **Caída aislada y ventana (C3):** S3c usa los mismos FGe de los **últimos 36 meses** que la tendencia; un valor más antiguo no cuenta como «penúltimo».
- **Inicio de iSRA / iSGLT2 en los últimos 3 meses:** el aviso **no se suprime**; la fila muestra «Inicio de iSRA/iSGLT2 hace <3 meses: descenso esperable hasta 30 % (KDIGO 2024) — revisar».
  Es un **inicio** solo si no hay ninguna dispensación previa del mismo grupo (iSRA C09* o iSGLT2 A10BK*) antes de esos 3 meses (C5): la renovación de un tratamiento crónico no cuenta.
- **Fuentes:** KDIGO 2012, rec. 2.1.3; KDIGO 2024, PP 2.1.3 (>20 %) y PP 2.1.4 (>30 %).
- **Decisión de diseño:** el mínimo de 12 meses entre el primer y el último valor es nuestro.

### S1c · Albuminuria persistente (con el lector de notas) → grupo 2 «Sin seguimiento»
- **N1a enmendada (Ahmed, sábado 14 nov 2026):** un CAC **alterado** (≥30 mg/g o ≥3 mg/mmol) leído en una nota **nunca** retira el aviso.
- Si el paciente tiene S1b (CAC alterado de laboratorio, sin repetir, sin N18) y la nota trae otro CAC alterado **≥3 meses después** (valor, unidad y fecha leídos por el código en la cita comprobada): **«Albuminuria persistente: valorar código de ERC (N18)»**. Sustituye a S1b (la repetición ya está hecha). KDIGO 2024: cronicidad de al menos 3 meses.
- **Vuelta 10 (Ahmed, sábado 14 nov 2026):** el CAC citado en la nota solo cuenta si su fecha es de los **últimos 12 meses** (parámetro `meses_nota_realizada`, el mismo de N1f). Un CAC alterado más antiguo citado en una nota no da S1c: el paciente sigue con S1b (repetir CAC).
- Nunca propone un fármaco ni un diagnóstico: pide valorar el código.
- `rules/n1_nota_confirma.sql`; parámetro `meses_persistencia_cac` = 3.
- **Redacción prudente firmada (Ahmed, médico, sábado 14 nov 2026):** el motivo dice «… (informe externo en nota, pendiente de validar/incorporar; nota del …, cita comprobada: «…»)» y la explicación «Posible albuminuria persistente en dos determinaciones separadas ≥3 meses (lab + informe externo en nota, pendiente de validar/incorporar; KDIGO 2024): valorar diagnóstico de ERC.». El pedido sigue siendo «Albuminuria persistente: valorar código de ERC (N18)». ☑ Firmado (14 nov 2026). **A6 (Ahmed, 14 nov):** el texto decía «>3 meses» y el código usa ≥3; se corrige el texto a «≥3 meses» para que diga lo que hace el código (sin cambio de lógica).

### Lector de notas (N1, firmada 14 nov 2026)
- **N1a:** «ya realizada» con cita comprobada, la misma prueba nombrada en la frase, una sola fecha leída por el código, posterior al dato que dispara el aviso y de los últimos 12 meses (`meses_nota_realizada`) → retira esa prueba, como un pedido pendiente. Enmienda: un CAC alterado nunca retira (ver S1c).
  - **Segunda enmienda (Ahmed, sábado 14 nov 2026): para el CAC, solo un resultado normal retira.** Retira un valor legible <30 mg/g o <3 mg/mmol, o, sin valor legible, la palabra «normal» sin negar ni matizar («CAC normal», «CAC normal (A1)»). Todo lo demás (sin resultado: «CAC realizado»; descrito con palabras: «moderado», «no normal», «normal-alto»; cifra en letras) es dudoso y no tiene efecto: el aviso sigue. Motivo: una lista de palabras «alteradas» nunca está completa (revisor en bucle, ronda 2, 14 nov). ☑ Firmado (Ahmed, 14 nov 2026)
  - **Cómo se lee «sin negar ni matizar» (vuelta 9, ronda 3; misma regla firmada, lectura estricta):** «normal» solo cuenta en una frase llana: quitadas la prueba, la fecha, «(A1)», «en rango» y unas pocas palabras neutras («trae», «informe», «mutua», «laboratorio»…), no queda nada más. «Normal según el paciente», «parece normal», «¿normal?», «normal, sin confirmar» o «normal y albuminuria» son dudosos y el aviso sigue.
- **N1b** rechazo y **N1c** Nefrología: solo anotan; nunca retiran.
- **N1d** negación, plan, petición, cancelación u otra persona en la frase → sin efecto. **N1e** cualquier duda → sin efecto.
  - **Vuelta 11 (revisor, ronda 4):** «familia», «familiar», «pareja», «tutor», «compañero» o «tito» sin determinante pueden ser del paciente («médico de familia», «pareja estable») o de otra persona («Pareja: CAC 12 mg/g»). En esa duda solo conserva su efecto un **CAC alterado** (que nunca retira, N1a); un CAC normal, un rechazo o una derivación a Nefrología **no retiran**. Con determinante o posesivo («su», «tu», «este», «esa», «nuestra», «del»…) es otra persona y la frase no tiene ningún efecto. Corrige la vuelta 9, que con un CAC normal sí retiraba (exclusión equivocada).
  - **Vuelta 12 (revisor, ronda 5):** se añaden abreviaturas y palabras de pareja o expareja («AF», «Fam.», «Hna/Hno», «Hij@», «Sr./Sra.», «señora», «ex», «exmarido», «consanguíneo», «parentesco», «chico/a», «los suyos», «parejas»). **Límite conocido:** saber si una frase habla de otra persona depende de una lista de palabras, que nunca está completa; una palabra que falte puede retirar un pedido con el resultado normal de otra persona. Alternativa pendiente de firma: que un resultado normal, un rechazo o una derivación solo retiren si la frase dice expresamente que es del paciente.
- Fechas en formato español (día/mes/año); «hace 3 meses» o varias fechas en la frase → sin fecha → no retira.

## Vuelta 13 (firmada por Ahmed, 16 nov 2026; `docs/FIRMA_VUELTA_13.md`)
- **S1d · Albuminuria persistente en dos analíticas → grupo 2.** Último CAC alterado y otro CAC alterado de laboratorio ≥3 meses antes, sin CAC normal entre los dos y sin código de ERC: «Albuminuria persistente en dos analíticas: valorar código de ERC (N18)». Sustituye a S1b (KDIGO 2024, PP 1.1.3.1).
- **Exclusiones** → «Fuera de la lista · Excluido»: diálisis (Z99.2, Z49, N18.6), trasplante renal (Z94.0), paliativos (Z51.5), embarazo (códigos O, si empezó en los últimos 10 meses: ventana de diseño). Sin límite de edad.
- **FGe:** la tendencia usa solo la ecuación del último valor; con ecuaciones mezcladas y pocos valores de la misma, información insuficiente, solo si mezclándolas habría habido tendencia (≥3 fechas en ≥12 meses; lectura del código, más estrecha que el texto firmado). Un FGe ≤0 o >200 es imposible: información insuficiente.
- **Códigos de ERC:** N18, I12, I13, E11.21, E11.22.
- **Notas:** una nota nunca retira un pedido de FGe (solo anota). «Seguido en Nefrología» exige la palabra de seguimiento en la misma cláusula que «Nefrología», a 8 palabras o menos.
- **CAC negativo:** información insuficiente.
- **Vuelta 14 (Ahmed, 16 nov 2026):** una palabra de ingreso (ingres…, hospitaliz…) en la misma cláusula anula la palabra de seguimiento de Nefrología.
- **Vuelta 15 (Ahmed, 16 nov 2026, «B: sign V2–V7, hold V1»; `docs/FIRMA_VUELTA_15.md`), lectura de notas:**
  - V2: el CAC también se nombra «índice/ratio/relación albúmina/creatinina» y «microalbúmina/creatinina».
  - V3: una tira reactiva, una albúmina de 24 h o en concentración no es un CAC.
  - V4: «FG > 60» y similares son un límite, no un valor.
  - V5: el nombre de la ecuación con su año («CKD-EPI 2021», «MDRD-4») no es el valor del FGe.
  - V6: «menos de», «más de», «por encima/debajo de», «hasta» hacen ilegible el CAC.
  - V7: un «ya realizada» se lee en la frase entera cuando el divisor la cortó en «; ».
  - **V1 (no firmada):** otra cifra en la frase sigue bloqueando el valor del CAC.
- **DM1 (E10):** entra en el cribado 5 años después del primer código E10 (consenso ADA–KDIGO 2022, doi:10.2337/dci22-0027, texto completo leído en PMC9870667 el 16 nov 2026: «For T1D, screening is recommended commencing 5 years after diagnosis, prior to which CKD is uncommon»). La fecha del primer código no es siempre la del diagnóstico.

## Supresión (vale para todas las reglas)
- Pedido ya pendiente o repetición reciente → fuera de la lista, al registro «Fuera de la lista, y por qué».
- El extracto no permite decidir → «información insuficiente», nunca un aviso.
- Volver a ejecutar nunca duplica un pedido.

## Fecha de referencia
Todas las reglas calculan «hoy» como `extract_meta.fecha_referencia`, nunca `date('now')`: el mismo extracto da siempre la misma salida.

## Decisiones firmadas (Ahmed, 14 nov 2026)
Todas viven en `rules/00_parametros.sql` con `estado = 'firmado'`. Un cambio futuro vuelve a `propuesta Dn` hasta su firma, y la ficha del paciente lo marca en amarillo («pendiente de firma clínica»).

| # | Pregunta | Decisión programada | Estado |
|---|---|---|---|
| D1 | ¿Qué cuenta como «repetición reciente» para suprimir? | La repetición reciente ya está dentro de S1a (CAC <12 meses) y S1b (CAC posterior). La supresión solo usa **pedido de la misma prueba pendiente desde hace ≤3 meses**; uno más antiguo se considera perdido y el aviso vuelve | ☑ Firmado (14 nov 2026) |
| D2 | CAC en mg/mmol | **Sin conversión:** cada unidad con su umbral de KDIGO 2024, tabla 1: «≥30 mg/g [≥3 mg/mmol]», A3 «≥300 mg/g (≥30 mg/mmol)». Otra unidad → «información insuficiente» | ☑ Firmado (14 nov 2026) |
| D3 | Códigos de origen | LOINC CAC 9318-7, 14959-1, 14958-3 (molar); FGe 62238-1, 98979-8, 33914-3. ATC iSRA C09*, iSGLT2 A10BK*. Las combinaciones A10BD no entran en esta versión (A10BD también incluye combinaciones sin iSGLT2, como sitagliptina + metformina) | ☑ Firmado (14 nov 2026) |
| D4 | Ventana y revisión | Tendencia S3 con los FGe de los **últimos 36 meses**; fecha de revisión = **+30 días** | ☑ Firmado (14 nov 2026) |
| D5 | Lectura de S3 | La vía «peor categoría G + caída ≥25 %» también exige ≥3 valores en ≥12 meses (lectura conservadora del texto firmado) | ☑ Firmado (14 nov 2026) |
| C2 | Dos CAC el mismo día, en unidades distintas | **Manda la mayor categoría KDIGO: A3 > A2 > A1**, cada valor frente al umbral de su unidad (25 mg/g es A1 y 4 mg/mmol es A2: sale el A2, aunque 25 > 4; 30 mg/g es A2 y 30 mg/mmol es A3: sale el A3). Dentro de la misma categoría, el mayor valor. Un resultado vacío sale primero («información insuficiente»); una unidad desconocida queda entre A2 y A1 (no esconde un alterado conocido, y un normal no la tapa) | ☑ Firmado (14 nov 2026) |
| C3 | ¿La ventana de 36 meses vale también para S3c? | **Sí:** la caída aislada compara los dos últimos FGe de los últimos 36 meses | ☑ Firmado (14 nov 2026) |
| C4 | Orden dentro de cada grupo | **Primero la gravedad del hallazgo** (en S3, la pendiente más negativa; en S1b, A3 antes que A2), **después la edad** (mayor primero) | ☑ Firmado (14 nov 2026) |
| C5 | Inicio de iSRA/iSGLT2 frente a renovación | **Inicio = ninguna dispensación previa del mismo grupo antes de los 3 meses.** Una renovación de un tratamiento crónico no activa el aviso del fármaco | ☑ Firmado (14 nov 2026) |
| C6 | ¿Un FGe con unidad no reconocida anula la tendencia S3 aunque los demás valores sean válidos? | **Sí, se mantiene:** con un FGe de unidad no reconocida en los últimos 36 meses, S3/S3c no se calculan y el paciente sale en «Fuera de la lista · Desconocido ≠ Normal» (información insuficiente), visible para revisión manual. Planteado por el ataque de GPT-6.1 Sol (A4) | ☑ Firmado (Ahmed, 14 nov 2026) |

Pruebas de cada decisión: `tests/test_reglas.py` (sección «Decisiones clínicas firmadas por Ahmed»).

## Orden en pantalla
Grupo 1 (S3, después S3c) → grupo 2 (S1b) → grupo 3 (S1a). Dentro de cada grupo, según C4: gravedad del hallazgo y después edad. Es configurable; no es una priorización validada.

## Solo si S1 y S3 pasan la CI
- **S2 · «Analítica aceptable», riesgo alto:** riesgo SCORE2 / SCORE2-Diabetes frente a objetivo de lípidos según categoría.

## Siguiente paso (no se construye este fin de semana)
- **S4 · Un corazón que empieza a fallar:** DM2 con NT-proBNP ≥125 pg/mL (o BNP ≥50) sin ecocardiograma, código de IC ni derivación (ADA 2024, rec. 10.39).

## Referencias
- KDIGO 2024 CKD: doi:10.1016/j.kint.2023.10.018 (PMID 38490803)
- ADA Standards of Care 2024 §10: doi:10.2337/dc24-S010 (PMID 38078592)
- DIAMOND2: doi:10.1016/j.pcd.2026.02.007 (PMID 41741270)
