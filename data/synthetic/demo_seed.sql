-- Pacientes de la demo (fijos). Maqueta · datos sintéticos: todos inventados a partir del caso de Carmen.
-- Conceptos OMOP: género estándar (8507 hombre, 8532 mujer); el resto 0 = sin concepto estándar todavía,
-- con el código de origen (CIE-10-ES, LOINC, ATC) en *_source_value. Mapeo a conceptos estándar: pendiente.

INSERT INTO extract_meta VALUES (1, '2026-11-14', 1, 'sintetico_demo');

INSERT INTO person (person_id, gender_concept_id, year_of_birth, race_concept_id, ethnicity_concept_id, person_source_value, gender_source_value) VALUES
  (1, 8507, 1954, 0, 0, 'Manuel',  'H'),
  (2, 8532, 1959, 0, 0, 'Pilar',   'M'),
  (3, 8532, 1967, 0, 0, 'Rosa',    'M'),
  (4, 8507, 1962, 0, 0, 'Antonio', 'H');

INSERT INTO condition_occurrence (condition_occurrence_id, person_id, condition_concept_id, condition_start_date, condition_type_concept_id, condition_source_value) VALUES
  (1, 1, 0, '2015-03-10', 0, 'I10'),
  (2, 2, 0, '2014-06-21', 0, 'E11.9'),
  (3, 3, 0, '2016-01-15', 0, 'E11.9'),
  (4, 3, 0, '2019-09-02', 0, 'I10'),
  (5, 4, 0, '2017-04-30', 0, 'E11.9');

-- Manuel: FGe 78 → 69 → 61 en 2 años (S3). CAC reciente normal: solo sale por la tendencia.
-- Pilar: CAC 85 mg/g hace 9 meses, sin repetir, sin N18 (S1b); cita hoy.
-- Rosa: analítica de sangre en junio, pero último CAC hace 18 meses (S1a).
-- Antonio: CAC 120 mg/g hace 8 meses; repetición ya pedida hace 12 días (suprimido).
INSERT INTO measurement (measurement_id, person_id, measurement_concept_id, measurement_date, measurement_type_concept_id, value_as_number, unit_source_value, measurement_source_value) VALUES
  (1,  1, 0, '2024-11-05', 0, 78,  'mL/min/1.73m2', '62238-1'),
  (2,  1, 0, '2025-11-10', 0, 69,  'mL/min/1.73m2', '62238-1'),
  (3,  1, 0, '2026-11-02', 0, 61,  'mL/min/1.73m2', '62238-1'),
  (4,  1, 0, '2026-11-02', 0, 12,  'mg/g',          '9318-7'),
  (5,  2, 0, '2026-02-12', 0, 74,  'mL/min/1.73m2', '62238-1'),
  (6,  2, 0, '2026-02-12', 0, 85,  'mg/g',          '9318-7'),
  (7,  3, 0, '2025-05-12', 0, 18,  'mg/g',          '9318-7'),
  (8,  3, 0, '2025-05-12', 0, 91,  'mL/min/1.73m2', '62238-1'),
  (9,  3, 0, '2026-06-01', 0, 88,  'mL/min/1.73m2', '62238-1'),
  (10, 4, 0, '2026-03-03', 0, 120, 'mg/g',          '9318-7'),
  (11, 4, 0, '2026-03-03', 0, 74,  'mL/min/1.73m2', '62238-1');

INSERT INTO visit_occurrence (visit_occurrence_id, person_id, visit_concept_id, visit_start_date, visit_end_date, visit_type_concept_id, visit_start_datetime) VALUES
  (1, 2, 0, '2026-11-14', '2026-11-14', 0, '2026-11-14T10:40');

INSERT INTO pedido_pendiente (pedido_id, person_id, prueba, fecha_pedido) VALUES
  (1, 4, 'CAC', '2026-11-02');
