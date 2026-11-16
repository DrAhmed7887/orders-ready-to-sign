# Arquitectura y por qué

El jurado valora sobre todo la **justificación de la arquitectura elegida**, y después el prototipo construido con ella. Cada decisión, con su alternativa descartada:

| Decisión | Por qué | Alternativa descartada |
|---|---|---|
| **Extracto con forma OMOP CDM v5.4** (person, visit_occurrence, measurement, condition_occurrence, drug_exposure, observation) | Responde a «¿dónde se conecta con mi historia?»: es el formato al que ya mapean redes españolas de investigación como SIDIAP. Una historia real llegaría por un mapeo OMOP o una lectura FHIR R4 (no se construye este fin de semana). Los códigos de origen (CIE-10-ES, LOINC) se guardan en las columnas `*_source_value` | Un esquema propio: obliga a cada centro a un mapeo a medida |
| **SQLite, un solo archivo** | Sin servidor, sin coste, corre en cualquier PC de la red del centro y en la CI | Un servidor de base de datos: la demo dependería de un servicio vivo |
| **Reglas SQL deterministas** | Cada aviso se puede auditar línea a línea frente a la guía; el mismo extracto da siempre el mismo resultado | Un modelo de aprendizaje automático o un LLM: no auditable frente a la guía, y los datos del paciente saldrían de la red |
| **Pedidos preparados para firmar**, no alertas | En dos ensayos aleatorizados por clústeres, una alerta interruptiva en la consulta no aumentó de forma significativa la prescripción de estatinas; un pedido ya preparado para firmar la aumentó 16,4 puntos (Fanaroff, JAMA Cardiol 2025, PMID 40136263) | Alertas emergentes en la consulta |
| **Revisión de todo el cupo crónico cada mañana** | Las herramientas de laboratorio (La Fe, San Juan de Alicante) actúan cuando llega una petición; nosotros cubrimos al paciente sin analítica reciente, el resultado alterado antiguo nunca repetido y la tendencia lenta. Complementario, no sustituto | Actuar solo cuando llega una analítica |
| **Página estática** (HTML + JS) que lee `pedidos.js` (la misma lista que `pedidos.json`, para abrirla con doble clic) | Se abre dentro de la historia como un panel, sin servidor; se puede alojar en la intranet | Una aplicación aparte con su propio inicio de sesión |
| **CI en cada push** (GitHub Actions + pytest + prueba de la pantalla) contra etiquetas escritas antes de las reglas (demo y set adversarial de `docs/SET_CIEGO.md`; set a ciegas pendiente) y un filtro básico de 1 variable al lado | Prueba, no promesas: el jurado ve en el historial que las reglas pasan | Probar a mano antes de la demo |

## Flujo real, paso a paso (lo que hace `ejecutar.py`)
1. **Carga** `data/schema.sql` en SQLite en memoria, con claves foráneas activas.
2. **Carga el extracto** con un autorizador de SQLite que solo permite `INSERT` en las tablas de datos: un extracto no puede crear, borrar, modificar ni adjuntar archivos.
3. **Valida** antes de decidir nada: una sola fila en `extract_meta`, todas las fechas reales en `AAAA-MM-DD`, resultados numéricos (SQLite guardaría «<3» como texto y lo trataría como mayor que cualquier número), ningún registro huérfano. Si algo falla, se para con un mensaje claro; nunca da avisos a medias.
4. **Ejecuta las reglas** en orden (`rules/00_parametros.sql` → S1a → S1b → S3/S3c): cada una escribe candidatos con la fecha y el valor que los disparan.
5. **Supresión** (`rules/supresion.sql`): extracto incompleto o dato no interpretable → «información insuficiente»; pedido ya pendiente de todas las pruebas → fuera de la lista; pendiente de una sola → se pide solo la otra.
6. **Agrupa** por paciente (un pedido principal + «También»), ordena por grupo y escribe `ui/pedidos.json` y `ui/pedidos.js`. El identificador de cada pedido depende de la regla, el paciente y la fecha del dato: volver a ejecutar da exactamente el mismo archivo.

## Cómo se comprueba (todo en la CI, en cada push)
| Qué | Dónde | Resultado actual |
|---|---|---|
| Reglas, supresión, validación del extracto, casos límite | `tests/` (pytest, Python 3.9 y 3.12) | en verde |
| Reglas y filtro básico frente a etiquetas escritas antes de las reglas | `eval/evaluar.py` → resumen de la CI y `eval/results/demo.md` | demo: 3/3 avisos correctos, 0 falsos; filtro básico: 0/3 |
| Los 20 casos difíciles de `docs/SET_CIEGO.md` (23 pacientes): unidades, límites, duplicados, pedidos, fármaco, dos hallazgos | `eval/evaluar.py --exigir` sobre `data/synthetic/ciego/` → `eval/results/ciego.md`; detalles en `tests/test_evaluar.py` | 23/23; 13/13 avisos correctos, 0 falsos; filtro básico: 1/13. Diseñado internamente conociendo las reglas: no es a ciegas |
| La pantalla con clics reales: firmar, aplazar, descartar con motivo, recargar, volver a ejecutar, exportar, enlace manipulado | `ui/tests/` (Chromium sin interfaz) | en verde |
| Revisión técnica del código | auditoría independiente + revisión de código; cada hallazgo corregido tiene su test de regresión | — |

Todo es verificación de software frente a las reglas firmadas, con datos sintéticos; no es validación clínica.

## Privacidad
- Las reglas no usan nube ni modelos: ningún dato del paciente sale de la red.
- Lector de notas (opcional): en el hackatón, el modelo corrió en Modal con GPU y tráfico en la UE (`region="eu"`, `routing_region="eu-west"`), en una ejecución efímera (`notas/modal_eu.py`), **solo sobre notas sintéticas**; la CI y la demo repiten sus salidas grabadas. En producción, un modelo abierto de 4B dentro de la red del departamento (diseño, no construido). Retención de Modal para este tipo de ejecución: entradas y salidas hasta 7 días, registros 1 día (plan Starter), imagen del contenedor hasta que se borre (modal.com/docs/guide/security, leído el 14 nov 2026): no es «retención cero», así que con datos reales no se haría así.
- Este repositorio solo contiene datos sintéticos.

## Cómo entra en el sistema del médico, sin una aplicación más
Pregunta del jurado en el checkpoint 1: «el médico de familia ya tiene su sistema; ¿cómo se supera esa resistencia? ¿qué proponéis?». Nuestra propuesta (diseño; la integración **no** está construida este fin de semana):

| Paso | Qué hace | Por qué no choca con el sistema actual |
|---|---|---|
| **1. Lee lo que ya existe** | Una exportación nocturna, **solo lectura**, del sistema de AP (SIA/Abucasis en la Comunitat Valenciana; ECAP, Diraya o AP-Madrid en otras comunidades), mapeada a la forma OMOP o leída por FHIR R4 | No pide al proveedor del sistema que cambie nada para empezar. OMOP es el formato al que ya mapean redes españolas de AP como SIDIAP |
| **2. Corre dentro de la red sanitaria** | Un archivo SQLite y unas reglas SQL en un ordenador del departamento de salud; sin servidor nuevo, sin nube | Ningún dato del paciente sale de la red: no hay tercero que reciba datos |
| **3. Devuelve peticiones, no alertas** | Cada mañana, la orden de laboratorio, la línea de nota y la fecha de revisión ya escritas, para firmar con un clic desde el propio puesto del médico (en la maqueta, un panel dentro de la estación clínica) | El médico no abre otra aplicación ni recibe más avisos: tiene **menos** trabajo, no más. En dos ensayos aleatorizados por clústeres, una alerta no cambió la prescripción de forma significativa y una orden preparada para firmar la subió 16,4 puntos (Fanaroff, JAMA Cardiol 2025; era una derivación a farmacia para estatinas, no una analítica: es una analogía) |
| **4. Se puede auditar** | Reglas SQL legibles, umbrales firmados por un clínico con su fuente, y cada pedido dice de qué tabla y de qué fecha sale cada dato | Sistemas de información y la dirección médica pueden revisar exactamente qué hace, línea a línea: no hay caja negra |
| **5. Empieza pequeño** | Piloto en un centro de salud en modo solo lectura: la lista se consulta aparte y no se escribe nada en la historia. Se mide lo que la maqueta ya registra: pedidos firmados, aplazados y descartados con su motivo | El riesgo del piloto es casi nulo; si funciona, el siguiente paso es que el proveedor lo integre como un módulo del puesto |

La Comunitat Valenciana es el ejemplo de trabajo; el enfoque vale para toda la atención primaria pública española.

## Trabajo futuro
Lo que dejamos fuera a propósito este fin de semana, en orden:

1. **Integración real:** el lector FHIR R4 ya existe (`fhir/leer_fhir.py`, probado solo con Bundles sintéticos: mismos pedidos que el extracto original en los seis conjuntos). Falta probarlo con una exportación real, validarlo con el validador de HL7, mapear los conceptos estándar de OMOP y escribir la petición firmada en el propio sistema (FHIR ServiceRequest).
2. **Set a ciegas de verdad:** pacientes escritos por una persona y etiquetados por el clínico sin ver la salida de las reglas (el set adversarial actual no lo es).
3. **Regla N1 más estricta:** que un resultado normal, un rechazo o una derivación leídos en una nota solo retiren un pedido si la frase dice expresamente que es del paciente (hoy depende de una lista de palabras; pendiente de firma clínica).
4. **S2 · «analítica aceptable», riesgo alto:** riesgo SCORE2 / SCORE2-Diabetes frente al objetivo de lípidos (`docs/REGLAS.md`).
5. **Lector de notas dentro de la red:** el modelo abierto de 4B en un servidor del departamento, con su tiempo medido en ese equipo.
6. **El lado del paciente:** que el paciente vea en su aplicación de salud qué prueba se le ha pedido y por qué, y que el resultado vuelva a su médico; hoy ese circuito se pierde entre consultas.
7. **Validación clínica:** con datos reales y aprobación ética, frente a la revisión manual de un médico. Lo de este repositorio es verificación de software con datos sintéticos.
