-- Set adversarial de docs/SET_CIEGO.md: un paciente (o dos) por cada uno de los 20 casos difíciles, más 2 para
-- llegar al mínimo de 3 por regla. Maqueta · datos sintéticos: nombres y valores inventados, ningún dato real.
-- Diseñado internamente (14 nov 2026) desde la tabla de SET_CIEGO.md; NO es el set a ciegas de un autor independiente y Ahmed
-- (el autor conocía rules/). Las etiquetas (etiquetas.csv) se copiaron de la columna «Qué debería pasar».
-- «Hoy» = 2026-11-14. Códigos: CIE-10-ES, LOINC (CAC 9318-7 mg/g, 14958-3 mg/mmol; FGe 62238-1), ATC.

INSERT INTO extract_meta VALUES (1, '2026-11-14', 1, 'sintetico_ciego');

INSERT INTO person (person_id, gender_concept_id, year_of_birth, race_concept_id, ethnicity_concept_id, person_source_value, gender_source_value) VALUES
  (1,  8532, 1958, 0, 0, 'Encarna',   'M'),   -- caso 1
  (2,  8507, 1963, 0, 0, 'Vicente',   'H'),   -- caso 2
  (3,  8532, 1950, 0, 0, 'Amparo',    'M'),   -- caso 3
  (4,  8507, 1966, 0, 0, 'Salvador',  'H'),   -- caso 4
  (5,  8532, 1971, 0, 0, 'Remedios',  'M'),   -- caso 5
  (6,  8507, 1947, 0, 0, 'Joaquín',   'H'),   -- caso 6
  (7,  8532, 1960, 0, 0, 'Inmaculada','M'),   -- caso 7
  (8,  8507, 1955, 0, 0, 'Ramón',     'H'),   -- caso 8
  (9,  8532, 1952, 0, 0, 'Desamparados','M'), -- caso 9
  (10, 8507, 1969, 0, 0, 'Fermín',    'H'),   -- caso 10 (11 meses)
  (11, 8532, 1964, 0, 0, 'Consuelo',  'M'),   -- caso 10 (13 meses)
  (12, 8507, 1949, 0, 0, 'Teodoro',   'H'),   -- caso 11
  (13, 8532, 1957, 0, 0, 'Milagros',  'M'),   -- caso 12
  (14, 8507, 1961, 0, 0, 'Eusebio',   'H'),   -- caso 13
  (15, 8532, 1944, 0, 0, 'Purificación','M'), -- caso 14
  (16, 8507, 1968, 0, 0, 'Gaspar',    'H'),   -- caso 15
  (17, 8532, 1953, 0, 0, 'Visitación','M'),   -- caso 16
  (18, 8507, 1946, 0, 0, 'Leandro',   'H'),   -- caso 17
  (19, 8532, 1959, 0, 0, 'Asunción',  'M'),   -- caso 18
  (20, 8507, 1951, 0, 0, 'Baltasar',  'H'),   -- caso 19
  (21, 8532, 1956, 0, 0, 'Rosario',   'M'),   -- caso 20
  (22, 8507, 1975, 0, 0, 'Nicasio',   'H'),   -- extra S1a
  (23, 8532, 1948, 0, 0, 'Herminia',  'M');   -- extra S3c

INSERT INTO condition_occurrence (condition_occurrence_id, person_id, condition_concept_id, condition_start_date, condition_type_concept_id, condition_source_value) VALUES
  (1,  1,  0, '2016-02-01', 0, 'E11.9'),
  (2,  2,  0, '2015-05-12', 0, 'I10'),
  (3,  3,  0, '2012-09-30', 0, 'E11.9'),
  (4,  3,  0, '2014-01-20', 0, 'I10'),
  (5,  4,  0, '2018-03-03', 0, 'E11.9'),
  (6,  5,  0, '2017-07-07', 0, 'I10'),
  (7,  6,  0, '2010-11-11', 0, 'E11.9'),
  (8,  6,  0, '2023-06-15', 0, 'N18.3'),   -- ERC ya codificada
  (9,  7,  0, '2019-04-04', 0, 'E11.9'),
  (10, 8,  0, '2013-08-08', 0, 'I10'),
  (11, 9,  0, '2011-10-10', 0, 'E11.9'),
  (12, 10, 0, '2020-02-02', 0, 'I10'),
  (13, 11, 0, '2016-12-12', 0, 'E11.9'),
  -- 12: sin DM2 ni HTA (entra por FGe <60)
  (14, 13, 0, '2014-05-05', 0, 'E11.9'),
  (15, 14, 0, '2018-09-09', 0, 'I10'),
  (16, 15, 0, '2009-01-01', 0, 'E11.9'),
  (17, 15, 0, '2009-01-01', 0, 'I10'),
  (18, 16, 0, '2017-03-17', 0, 'E11.9'),
  (19, 17, 0, '2015-06-16', 0, 'I10'),
  (20, 18, 0, '2012-04-12', 0, 'E11.9'),
  (21, 18, 0, '2012-04-12', 0, 'I10'),
  (22, 19, 0, '2016-08-18', 0, 'E11.9'),
  (23, 20, 0, '2013-02-13', 0, 'I10'),
  (24, 21, 0, '2014-10-14', 0, 'E11.9'),
  (25, 22, 0, '2021-01-21', 0, 'E11.9'),
  (26, 22, 0, '2021-01-21', 0, 'I10'),
  (27, 23, 0, '2011-11-23', 0, 'E11.9');

INSERT INTO measurement (measurement_id, person_id, measurement_concept_id, measurement_date, measurement_type_concept_id, value_as_number, unit_source_value, measurement_source_value) VALUES
  -- 1 · CAC exactamente 30 mg/g hace 7 meses
  (1,  1,  0, '2026-04-10', 0, 30,   'mg/g',          '9318-7'),
  -- 2 · CAC 29 mg/g hace 7 meses
  (2,  2,  0, '2026-04-10', 0, 29,   'mg/g',          '9318-7'),
  -- 3 · CAC 4 mg/mmol hace 7 meses (laboratorio externo)
  (3,  3,  0, '2026-04-10', 0, 4,    'mg/mmol',       '14958-3'),
  -- 4 · CAC con unidad rara
  (4,  4,  0, '2026-09-01', 0, 40,   'mg/dL',         '9318-7'),
  -- 5 · CAC sin resultado numérico
  (5,  5,  0, '2026-09-01', 0, NULL, 'mg/g',          '9318-7'),
  -- 6 · CAC alterado con N18
  (6,  6,  0, '2026-04-10', 0, 85,   'mg/g',          '9318-7'),
  -- 7 · CAC alterado y otro normal después
  (7,  7,  0, '2026-01-10', 0, 120,  'mg/g',          '9318-7'),
  (8,  7,  0, '2026-07-10', 0, 15,   'mg/g',          '9318-7'),
  -- 8 · CAC alterado, repetición pedida hace 2 semanas
  (9,  8,  0, '2026-04-10', 0, 90,   'mg/g',          '9318-7'),
  -- 9 · CAC alterado, pedido de repetición de hace 5 meses
  (10, 9,  0, '2026-04-10', 0, 90,   'mg/g',          '9318-7'),
  -- 10 · último CAC hace 11 meses / hace 13 meses
  (11, 10, 0, '2025-12-14', 0, 12,   'mg/g',          '9318-7'),
  (12, 11, 0, '2025-10-14', 0, 12,   'mg/g',          '9318-7'),
  -- 11 · sin DM2 ni HTA, FGe 55
  (13, 12, 0, '2026-10-01', 0, 55,   'mL/min/1.73m2', '62238-1'),
  -- 12 · 3 FGe en exactamente 12 meses, pendiente < −5/año
  (14, 13, 0, '2025-11-01', 0, 80,   'mL/min/1.73m2', '62238-1'),
  (15, 13, 0, '2026-05-01', 0, 74,   'mL/min/1.73m2', '62238-1'),
  (16, 13, 0, '2026-11-01', 0, 68,   'mL/min/1.73m2', '62238-1'),
  (17, 13, 0, '2026-10-01', 0, 10,   'mg/g',          '9318-7'),
  -- 13 · 3 FGe en 11 meses
  (18, 14, 0, '2025-12-01', 0, 80,   'mL/min/1.73m2', '62238-1'),
  (19, 14, 0, '2026-05-01', 0, 74,   'mL/min/1.73m2', '62238-1'),
  (20, 14, 0, '2026-11-01', 0, 68,   'mL/min/1.73m2', '62238-1'),
  (21, 14, 0, '2026-10-01', 0, 10,   'mg/g',          '9318-7'),
  -- 14 · dos FGe el mismo día (76 y 80: media 78) dentro de una tendencia
  (22, 15, 0, '2024-11-05', 0, 76,   'mL/min/1.73m2', '62238-1'),
  (23, 15, 0, '2024-11-05', 0, 80,   'mL/min/1.73m2', '62238-1'),
  (24, 15, 0, '2025-11-10', 0, 69,   'mL/min/1.73m2', '62238-1'),
  (25, 15, 0, '2026-11-02', 0, 61,   'mL/min/1.73m2', '62238-1'),
  (26, 15, 0, '2026-11-02', 0, 14,   'mg/g',          '9318-7'),
  -- 15 · FGe en unidad rara
  (27, 16, 0, '2024-11-01', 0, 80,   'mL/min',        '62238-1'),
  (28, 16, 0, '2025-11-01', 0, 70,   'mL/min',        '62238-1'),
  (29, 16, 0, '2026-11-01', 0, 60,   'mL/min',        '62238-1'),
  (30, 16, 0, '2026-11-01', 0, 8,    'mg/g',          '9318-7'),
  -- 16 · caída aislada >20 % entre los dos últimos FGe (80 → 60: 25 %)
  (31, 17, 0, '2026-03-01', 0, 80,   'mL/min/1.73m2', '62238-1'),
  (32, 17, 0, '2026-10-01', 0, 60,   'mL/min/1.73m2', '62238-1'),
  (33, 17, 0, '2026-10-01', 0, 11,   'mg/g',          '9318-7'),
  -- 17 · S3 con inicio de iSGLT2 hace 2 meses
  (34, 18, 0, '2024-11-01', 0, 78,   'mL/min/1.73m2', '62238-1'),
  (35, 18, 0, '2025-11-01', 0, 69,   'mL/min/1.73m2', '62238-1'),
  (36, 18, 0, '2026-11-01', 0, 61,   'mL/min/1.73m2', '62238-1'),
  (37, 18, 0, '2026-10-01', 0, 9,    'mg/g',          '9318-7'),
  -- 18 · S3 con CAC ya pedido
  (38, 19, 0, '2024-11-01', 0, 78,   'mL/min/1.73m2', '62238-1'),
  (39, 19, 0, '2025-11-01', 0, 69,   'mL/min/1.73m2', '62238-1'),
  (40, 19, 0, '2026-11-01', 0, 61,   'mL/min/1.73m2', '62238-1'),
  (41, 19, 0, '2026-10-01', 0, 9,    'mg/g',          '9318-7'),
  -- 19 · S3 con FGe y CAC ya pedidos
  (42, 20, 0, '2024-11-01', 0, 78,   'mL/min/1.73m2', '62238-1'),
  (43, 20, 0, '2025-11-01', 0, 69,   'mL/min/1.73m2', '62238-1'),
  (44, 20, 0, '2026-11-01', 0, 61,   'mL/min/1.73m2', '62238-1'),
  (45, 20, 0, '2026-10-01', 0, 9,    'mg/g',          '9318-7'),
  -- 20 · dos hallazgos: caída aislada (S3c) y CAC alterado sin repetir (S1b)
  (46, 21, 0, '2026-02-01', 0, 85,   'mg/g',          '9318-7'),
  (47, 21, 0, '2026-03-01', 0, 80,   'mL/min/1.73m2', '62238-1'),
  (48, 21, 0, '2026-10-01', 0, 60,   'mL/min/1.73m2', '62238-1'),
  -- extra S1a · DM2 + HTA, nunca un CAC
  (49, 22, 0, '2026-06-01', 0, 85,   'mL/min/1.73m2', '62238-1'),
  -- extra S3c · caída del 21 % (80 → 63)
  (50, 23, 0, '2026-01-15', 0, 80,   'mL/min/1.73m2', '62238-1'),
  (51, 23, 0, '2026-09-15', 0, 63,   'mL/min/1.73m2', '62238-1'),
  (52, 23, 0, '2026-09-15', 0, 13,   'mg/g',          '9318-7');

INSERT INTO drug_exposure (drug_exposure_id, person_id, drug_concept_id, drug_exposure_start_date, drug_exposure_end_date, drug_type_concept_id, drug_source_value) VALUES
  (1, 18, 0, '2026-09-14', '2027-09-14', 0, 'A10BK01');   -- caso 17: empagliflozina, primera dispensación

INSERT INTO pedido_pendiente (pedido_id, person_id, prueba, fecha_pedido) VALUES
  (1, 8,  'CAC', '2026-10-31'),   -- caso 8: hace 2 semanas (vigente)
  (2, 9,  'CAC', '2026-06-14'),   -- caso 9: hace 5 meses (ya no vale)
  (3, 19, 'CAC', '2026-11-02'),   -- caso 18
  (4, 20, 'FGe', '2026-11-02'),   -- caso 19
  (5, 20, 'CAC', '2026-11-03');
