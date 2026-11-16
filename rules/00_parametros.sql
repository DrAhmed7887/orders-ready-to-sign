-- Parámetros y códigos de las reglas. Un único sitio para cada umbral: si cambia, cambia aquí y en docs/REGLAS.md.
-- estado = 'firmado' (Ahmed: S1a/S1b/S3 el 13 nov 2026; D1–D5 y C2–C5 el 14 nov 2026) o 'propuesta Dn' (pendiente de firma).
-- Se carga DESPUÉS de data/schema.sql y del extracto.

CREATE TABLE parametro (
  clave   TEXT PRIMARY KEY,
  valor   REAL NOT NULL,
  estado  TEXT NOT NULL,
  fuente  TEXT
);

INSERT INTO parametro VALUES
  ('meses_sin_cac',          12, 'firmado',     'PROT-AP ERC 2025: cribado anual con FGe y CAC'),
  ('cac_umbral_mg_g',        30, 'firmado',     'KDIGO 2024, tabla 1: A2 30–299 mg/g'),
  ('cac_umbral_mg_mmol',      3, 'firmado',     'KDIGO 2024, tabla 1: «ACR ≥30 mg/g [≥3 mg/mmol]»'),
  ('cac_a3_mg_g',           300, 'firmado',     'KDIGO 2024, tabla 1: A3 ≥300 mg/g'),
  ('cac_a3_mg_mmol',         30, 'firmado',     'KDIGO 2024, tabla 1: A3 ≥30 mg/mmol'),
  ('meses_sin_repetir_cac',   6, 'firmado',     'Decisión de diseño (la guía no da cifra)'),
  ('pendiente_fge',          -5, 'firmado',     'KDIGO 2012, rec. 2.1.3'),
  ('meses_min_tendencia',    12, 'firmado',     'Decisión de diseño'),
  ('caida_categoria_pct',    25, 'firmado',     'KDIGO 2012, rec. 2.1.3'),
  ('caida_aislada_pct',      20, 'firmado',     'KDIGO 2024, PP 2.1.3'),
  ('meses_inicio_farmaco',    3, 'firmado',     'KDIGO 2024, PP 2.1.4'),
  ('meses_ventana_fge',      36, 'firmado',     'Decisión de diseño: solo FGe de los últimos 36 meses entran en la tendencia'),
  ('meses_pedido_vigente',    3, 'firmado',     'Decisión de diseño: un pedido de más de 3 meses sin resultado ya no suprime'),
  ('dias_revision',          30, 'firmado',     'Decisión de diseño: fecha de revisión del resultado'),
  ('meses_persistencia_cac',  3, 'firmado',     'N1a enmendada (Ahmed, 14 nov 2026): dos CAC alterados separados ≥3 meses = persistente (KDIGO 2024, cronicidad de al menos 3 meses)'),
  ('fge_max_plausible',     200, 'firmado',     'Vuelta 13 (Ahmed, 16 nov 2026), R6: un FGe ≤0 o >200 es imposible → información insuficiente. Comprobación de datos'),
  ('meses_dm1_cribado',      60, 'firmado',     'Vuelta 13 (Ahmed, 16 nov 2026), D: DM1 entra en el cribado 5 años después del primer código E10. Consenso ADA–KDIGO 2022 (Diabetes Care, doi:10.2337/dci22-0027): «For T1D, screening is recommended commencing 5 years after diagnosis»'),
  ('meses_embarazo',         10, 'firmado',     'Vuelta 13 (16 nov 2026), R2: un código O (embarazo) excluye si empezó en los últimos 10 meses. Decisión de diseño (la firma dice «embarazo», no da ventana)'),
  ('meses_nota_realizada',   12, 'firmado',     'N1f (Ahmed, 14 nov 2026): una prueba hecha según una nota cuenta 12 meses, como el cribado anual de S1a. Decisión de diseño');

-- Códigos de origen. Coincidencia por prefijo (E11 cubre E11.9; C09 cubre C09AA05).
CREATE TABLE codigo_regla (
  grupo        TEXT NOT NULL,   -- DM2, HTA, ERC, CAC, FGE, ISRA, ISGLT2
  sistema      TEXT NOT NULL,   -- CIE-10-ES, LOINC, ATC
  codigo       TEXT NOT NULL,
  descripcion  TEXT,
  estado       TEXT NOT NULL,
  PRIMARY KEY (grupo, codigo)
);

INSERT INTO codigo_regla VALUES
  ('DM2',    'CIE-10-ES', 'E11',     'Diabetes mellitus tipo 2',                       'firmado'),
  ('DM1',    'CIE-10-ES', 'E10',     'Diabetes mellitus tipo 1 (vuelta 13, D)',        'firmado'),
  ('HTA',    'CIE-10-ES', 'I10',     'Hipertensión esencial',                          'firmado'),
  ('HTA',    'CIE-10-ES', 'I11',     'Cardiopatía hipertensiva',                       'firmado'),
  ('HTA',    'CIE-10-ES', 'I12',     'Enfermedad renal hipertensiva',                  'firmado'),
  ('HTA',    'CIE-10-ES', 'I13',     'Enfermedad cardiorrenal hipertensiva',           'firmado'),
  ('HTA',    'CIE-10-ES', 'I15',     'Hipertensión secundaria',                        'firmado'),
  ('ERC',    'CIE-10-ES', 'N18',     'Enfermedad renal crónica',                       'firmado'),
  ('ERC',    'CIE-10-ES', 'I12',     'Enfermedad renal hipertensiva (vuelta 13, R4)',  'firmado'),
  ('ERC',    'CIE-10-ES', 'I13',     'Enfermedad cardiorrenal hipertensiva (vuelta 13, R4)', 'firmado'),
  ('ERC',    'CIE-10-ES', 'E11.21',  'DM2 con nefropatía diabética (vuelta 13, R4)',   'firmado'),
  ('ERC',    'CIE-10-ES', 'E11.22',  'DM2 con enfermedad renal crónica (vuelta 13, R4)', 'firmado'),
  ('EXCL_DIALISIS',  'CIE-10-ES', 'Z99.2', 'Dependencia de diálisis renal (vuelta 13, R2)', 'firmado'),
  ('EXCL_DIALISIS',  'CIE-10-ES', 'Z49',   'Contacto para diálisis (vuelta 13, R2)',        'firmado'),
  ('EXCL_DIALISIS',  'CIE-10-ES', 'N18.6', 'ERC terminal (vuelta 13, R2)',                  'firmado'),
  ('EXCL_TRASPLANTE','CIE-10-ES', 'Z94.0', 'Trasplante de riñón (vuelta 13, R2)',           'firmado'),
  ('EXCL_PALIATIVO', 'CIE-10-ES', 'Z51.5', 'Cuidados paliativos (vuelta 13, R2)',           'firmado'),
  ('EXCL_EMBARAZO',  'CIE-10-ES', 'O',     'Embarazo, parto y puerperio O00–O9A (vuelta 13, R2; últimos meses_embarazo)', 'firmado'),
  ('CAC',    'LOINC',     '9318-7',  'Albumin/Creatinine [Mass Ratio] in Urine',       'firmado'),
  ('CAC',    'LOINC',     '14959-1', 'Microalbumin/Creatinine [Mass Ratio] in Urine',  'firmado'),
  ('CAC',    'LOINC',     '14958-3', 'Microalbumin/Creatinine [Molar Ratio] in Urine', 'firmado'),
  ('FGE',    'LOINC',     '62238-1', 'eGFR CKD-EPI (creatinina)',                      'firmado'),
  ('FGE',    'LOINC',     '98979-8', 'eGFR CKD-EPI 2021 (creatinina)',                 'firmado'),
  ('FGE',    'LOINC',     '33914-3', 'eGFR MDRD',                                      'firmado'),
  ('ISRA',   'ATC',       'C09',     'Agentes que actúan sobre el sistema renina-angiotensina', 'firmado'),
  ('ISGLT2', 'ATC',       'A10BK',   'Inhibidores de SGLT2',                           'firmado');

-- Unidades de FGe que se aceptan (todas equivalentes). Otra unidad → «información insuficiente».
CREATE TABLE unidad_regla (
  grupo   TEXT NOT NULL,
  unidad  TEXT NOT NULL,   -- se compara en minúsculas
  PRIMARY KEY (grupo, unidad)
);

INSERT INTO unidad_regla VALUES
  ('FGE', 'ml/min/1.73m2'), ('FGE', 'ml/min/1.73 m2'), ('FGE', 'ml/min/{1.73_m2}'),
  ('FGE', 'ml/min/1,73m2'), ('FGE', 'ml/min/1,73 m2'), ('FGE', 'ml/min/1,73 m²'), ('FGE', 'ml/min/1.73 m²'),
  ('FGE', 'ml/min/1.73m²'), ('FGE', 'ml/min/1,73m²');

-- Vistas de apoyo -----------------------------------------------------------------------------

CREATE VIEW ref AS
SELECT fecha_referencia AS hoy, extracto_completo FROM extract_meta;

-- CAC con su categoría según la unidad. Unidad desconocida o resultado vacío → alterado NULL → «información insuficiente».
-- Un CAC sin resultado se conserva: cuenta como prueba hecha, no como «nunca pedido».
CREATE VIEW cac AS
SELECT m.measurement_id, m.person_id, m.measurement_date AS fecha, m.value_as_number AS valor,
       m.unit_source_value AS unidad, m.measurement_source_value AS codigo,
       CASE WHEN m.value_as_number < 0 THEN NULL   -- vuelta 13, R6: un CAC negativo es imposible → información insuficiente
            ELSE CASE lower(trim(m.unit_source_value))
         WHEN 'mg/g'    THEN m.value_as_number >= (SELECT valor FROM parametro WHERE clave = 'cac_umbral_mg_g')
         WHEN 'mg/mmol' THEN m.value_as_number >= (SELECT valor FROM parametro WHERE clave = 'cac_umbral_mg_mmol')
       END END AS alterado,
       CASE WHEN m.value_as_number < 0 THEN NULL ELSE CASE lower(trim(m.unit_source_value))
         WHEN 'mg/g'    THEN m.value_as_number >= (SELECT valor FROM parametro WHERE clave = 'cac_a3_mg_g')
         WHEN 'mg/mmol' THEN m.value_as_number >= (SELECT valor FROM parametro WHERE clave = 'cac_a3_mg_mmol')
       END END AS a3
FROM measurement m
JOIN codigo_regla c ON c.grupo = 'CAC' AND m.measurement_source_value = c.codigo
JOIN ref ON m.measurement_date <= ref.hoy;

-- Último CAC por persona. Si hay dos el mismo día (C2, firmado 14 nov 2026): manda la mayor categoría KDIGO,
-- A3 > A2 > A1, comparando cada valor con el umbral de SU unidad (25 mg/g es A1 y 4 mg/mmol es A2: gana el A2,
-- aunque 25 > 4). Un resultado vacío va primero para que salga como «información insuficiente».
-- Una unidad desconocida queda entre A2 y A1: no esconde un alterado conocido, pero tampoco la tapa un normal.
-- Dentro de la misma categoría, el mayor valor; desempate final estable: measurement_id.
CREATE VIEW cac_ultimo AS
SELECT * FROM (
  SELECT cac.*, ROW_NUMBER() OVER (PARTITION BY person_id
                                   ORDER BY fecha DESC, valor IS NULL DESC,
                                            CASE WHEN a3 = 1 THEN 3 WHEN alterado = 1 THEN 2
                                                 WHEN alterado IS NULL THEN 1 ELSE 0 END DESC,
                                            valor DESC, measurement_id) AS rn
  FROM cac
) WHERE rn = 1;

-- FGe con unidad aceptada y valor posible: un valor por persona, día y ECUACIÓN (media si hay duplicados de la misma).
-- Vuelta 13 (Ahmed, 16 nov 2026), R3: valores de ecuaciones distintas (MDRD, CKD-EPI 2009, CKD-EPI 2021) ya no se
-- promedian ni se mezclan en una tendencia (KDIGO 2024, PP 1.2.4.1: «Use the same equation within geographical regions»).
-- R6: un FGe ≤0 o > fge_max_plausible no entra (va a fge_invalido → información insuficiente).
CREATE VIEW fge AS
SELECT m.person_id, m.measurement_date AS fecha, m.measurement_source_value AS codigo,
       AVG(m.value_as_number) AS valor, MIN(m.unit_source_value) AS unidad,
       CASE m.measurement_source_value WHEN '98979-8' THEN 1 WHEN '62238-1' THEN 2 ELSE 3 END AS preferencia
FROM measurement m
JOIN codigo_regla c ON c.grupo = 'FGE' AND m.measurement_source_value = c.codigo
JOIN ref ON m.measurement_date <= ref.hoy
WHERE m.value_as_number IS NOT NULL
  AND m.value_as_number > 0 AND m.value_as_number <= (SELECT valor FROM parametro WHERE clave = 'fge_max_plausible')
  AND lower(trim(m.unit_source_value)) IN (SELECT unidad FROM unidad_regla WHERE grupo = 'FGE')   -- bucle 1: sin espacios
GROUP BY m.person_id, m.measurement_date, m.measurement_source_value;

-- FGe con unidad no aceptada o valor imposible dentro de la ventana de la tendencia: la persona no se evalúa en S3
-- y sale como «información insuficiente». Un valor antiguo fuera de la ventana no la silencia.
CREATE VIEW fge_invalido AS
SELECT m.person_id, MAX(m.measurement_date) AS fecha,
       CASE WHEN SUM(lower(trim(COALESCE(m.unit_source_value, ''))) NOT IN (SELECT unidad FROM unidad_regla WHERE grupo = 'FGE')) > 0
            THEN 'unidad del FGe no reconocida («' || MIN(CASE WHEN lower(trim(COALESCE(m.unit_source_value, ''))) NOT IN
                   (SELECT unidad FROM unidad_regla WHERE grupo = 'FGE') THEN COALESCE(m.unit_source_value, 'vacía') END) || '»)'
            ELSE 'FGe con valor imposible (' || printf('%g', MIN(m.value_as_number)) || ')' END AS problema
FROM measurement m
JOIN codigo_regla c ON c.grupo = 'FGE' AND m.measurement_source_value = c.codigo
JOIN ref ON m.measurement_date <= ref.hoy
        AND m.measurement_date >= date(ref.hoy, '-' || (SELECT CAST(valor AS INTEGER) FROM parametro WHERE clave = 'meses_ventana_fge') || ' months')
WHERE m.value_as_number IS NOT NULL
  AND (lower(trim(COALESCE(m.unit_source_value, ''))) NOT IN (SELECT unidad FROM unidad_regla WHERE grupo = 'FGE')
       OR m.value_as_number <= 0 OR m.value_as_number > (SELECT valor FROM parametro WHERE clave = 'fge_max_plausible'))
GROUP BY m.person_id;

-- Último FGe: la fecha más reciente; el mismo día, la ecuación preferida (CKD-EPI 2021 > 2009 > MDRD).
CREATE VIEW fge_ultimo AS
SELECT person_id, fecha, valor, codigo FROM (
  SELECT fge.*, ROW_NUMBER() OVER (PARTITION BY person_id ORDER BY fecha DESC, preferencia) AS rn FROM fge
) WHERE rn = 1;

CREATE VIEW tiene_codigo AS
SELECT DISTINCT co.person_id, c.grupo
FROM condition_occurrence co
JOIN codigo_regla c ON c.sistema = 'CIE-10-ES' AND trim(co.condition_source_value) LIKE c.codigo || '%'   -- bucle 1: « N18.3»
JOIN ref ON co.condition_start_date <= ref.hoy;

-- Vuelta 13 (Ahmed, 16 nov 2026), R2: personas que no van a la lista (diálisis, trasplante renal, paliativos, embarazo
-- reciente). Sus filas salen en «Fuera de la lista · Excluido» con el motivo. KDIGO 2024 §1.1.1: la detección
-- «should be individualized based on the person's goals of care»; p. S250: «Creatinine decreases physiologically
-- during pregnancy».
CREATE VIEW excluido AS
SELECT co.person_id,
       MIN(CASE c.grupo WHEN 'EXCL_DIALISIS' THEN 1 WHEN 'EXCL_TRASPLANTE' THEN 2 WHEN 'EXCL_PALIATIVO' THEN 3 ELSE 4 END) AS orden
FROM condition_occurrence co
JOIN codigo_regla c ON c.grupo LIKE 'EXCL_%' AND c.sistema = 'CIE-10-ES' AND trim(co.condition_source_value) LIKE c.codigo || '%'
JOIN ref ON co.condition_start_date <= ref.hoy
WHERE c.grupo <> 'EXCL_EMBARAZO'
   OR co.condition_start_date >= date(ref.hoy, '-' || (SELECT CAST(valor AS INTEGER) FROM parametro WHERE clave = 'meses_embarazo') || ' months')
GROUP BY co.person_id;

CREATE VIEW excluido_motivo AS
SELECT person_id, CASE orden WHEN 1 THEN 'diálisis' WHEN 2 THEN 'trasplante renal' WHEN 3 THEN 'cuidados paliativos'
                             ELSE 'embarazo o puerperio reciente' END AS motivo
FROM excluido;

-- Población del cupo crónico: DM2, HTA, DM1 con ≥5 años desde el primer código E10 (vuelta 13, D) o último FGe <60.
CREATE VIEW poblacion AS
SELECT person_id FROM tiene_codigo WHERE grupo IN ('DM2', 'HTA')
UNION
SELECT co.person_id FROM condition_occurrence co CROSS JOIN ref
WHERE upper(trim(co.condition_source_value)) LIKE 'E10%' AND co.condition_start_date <= ref.hoy
GROUP BY co.person_id
HAVING MIN(co.condition_start_date) <= date((SELECT hoy FROM ref), '-' || (SELECT CAST(valor AS INTEGER) FROM parametro WHERE clave = 'meses_dm1_cribado') || ' months')
UNION
SELECT person_id FROM fge_ultimo WHERE valor < 60;

-- Inicio de iSRA / iSGLT2 en los últimos 3 meses: la fila lo muestra, no se suprime.
-- C5 (firmado 14 nov 2026): es un INICIO solo si no hay ninguna dispensación previa del mismo grupo
-- antes de esos 3 meses; una renovación de un tratamiento crónico no cuenta.
CREATE VIEW inicio_farmaco_reciente AS
SELECT DISTINCT d.person_id
FROM drug_exposure d
JOIN codigo_regla c ON c.grupo IN ('ISRA', 'ISGLT2') AND d.drug_source_value LIKE c.codigo || '%'
JOIN ref ON d.drug_exposure_start_date <= ref.hoy
        AND d.drug_exposure_start_date >  date(ref.hoy, '-' || (SELECT CAST(valor AS INTEGER) FROM parametro WHERE clave = 'meses_inicio_farmaco') || ' months')
WHERE NOT EXISTS (
  SELECT 1 FROM drug_exposure d0
  JOIN codigo_regla c0 ON c0.grupo = c.grupo AND d0.drug_source_value LIKE c0.codigo || '%'
  WHERE d0.person_id = d.person_id
    AND d0.drug_exposure_start_date <= date(ref.hoy, '-' || (SELECT CAST(valor AS INTEGER) FROM parametro WHERE clave = 'meses_inicio_farmaco') || ' months')
);

-- Cita hoy → aviso «hoy en consulta».
CREATE VIEW cita_hoy AS
SELECT v.person_id, MIN(substr(v.visit_start_datetime, 12, 5)) AS hora
FROM visit_occurrence v JOIN ref ON v.visit_start_date = ref.hoy
GROUP BY v.person_id;

-- Candidatos que escriben las reglas; la supresión decide quién sale en la lista.
CREATE TABLE candidato (
  person_id      INTEGER NOT NULL,
  regla          TEXT NOT NULL,       -- S1a, S1b, S3, S3c
  grupo          INTEGER NOT NULL,    -- 1 Empeorando · 2 Sin seguimiento · 3 Prueba pendiente
  prioridad      REAL,                -- orden dentro del grupo (mayor primero)
  prueba         TEXT NOT NULL,       -- prueba que se pide: CAC o FGe
  prueba_extra   TEXT,                -- segunda prueba del mismo pedido (S3 pide FGe + CAC); la supresión mira las dos
  motivo         TEXT NOT NULL,
  pedido         TEXT NOT NULL,
  nota           TEXT NOT NULL,
  fecha_origen   TEXT,                -- fecha del dato que dispara el aviso (procedencia)
  insuficiente   TEXT                 -- no NULL = no se puede decidir: va al registro, nunca a la lista
);
