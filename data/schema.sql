-- Extracto con forma OMOP CDM v5.4: SUBCONJUNTO de columnas para el prototipo. Solo datos sintéticos.
-- Columnas obligatorias (NOT NULL) comprobadas contra el DDL oficial de OHDSI:
--   OHDSI/CommonDataModel, inst/ddl/5.4/sqlite/OMOPCDM_sqlite_5.4_ddl.sql (14 nov 2026).
-- Se incluyen TODAS las columnas obligatorias de cada tabla; de las opcionales, solo las que usan las reglas.
-- Fechas como texto ISO 8601 (AAAA-MM-DD).

CREATE TABLE person (
  person_id             INTEGER PRIMARY KEY,
  gender_concept_id     INTEGER NOT NULL,
  year_of_birth         INTEGER NOT NULL,
  race_concept_id       INTEGER NOT NULL,  -- 0 = sin dato (no se registra en la historia española)
  ethnicity_concept_id  INTEGER NOT NULL,  -- 0 = sin dato
  person_source_value   TEXT,              -- seudónimo de la demo, p. ej. «Manuel»
  gender_source_value   TEXT
);

CREATE TABLE visit_occurrence (
  visit_occurrence_id    INTEGER PRIMARY KEY,
  person_id              INTEGER NOT NULL REFERENCES person(person_id),
  visit_concept_id       INTEGER NOT NULL,
  visit_start_date       TEXT NOT NULL,    -- una cita en fecha_referencia activa el aviso «hoy en consulta»
  visit_end_date         TEXT NOT NULL,
  visit_type_concept_id  INTEGER NOT NULL, -- procedencia del registro
  visit_start_datetime   TEXT              -- opcional en OMOP; la hora de la cita sale en el aviso
);

CREATE TABLE condition_occurrence (
  condition_occurrence_id    INTEGER PRIMARY KEY,
  person_id                  INTEGER NOT NULL REFERENCES person(person_id),
  condition_concept_id       INTEGER NOT NULL,
  condition_start_date       TEXT NOT NULL,
  condition_type_concept_id  INTEGER NOT NULL,
  condition_source_value     TEXT              -- CIE-10-ES, p. ej. E11, I10, N18.x
);

CREATE TABLE measurement (
  measurement_id               INTEGER PRIMARY KEY,
  person_id                    INTEGER NOT NULL REFERENCES person(person_id),
  measurement_concept_id       INTEGER NOT NULL,
  measurement_date             TEXT NOT NULL,
  measurement_type_concept_id  INTEGER NOT NULL,
  value_as_number              REAL,
  unit_concept_id              INTEGER,
  unit_source_value            TEXT,    -- mg/g o mg/mmol: ver «Decisiones pendientes» en docs/REGLAS.md
  measurement_source_value     TEXT,    -- código de origen (LOINC)
  visit_occurrence_id          INTEGER REFERENCES visit_occurrence(visit_occurrence_id)
);

CREATE TABLE drug_exposure (
  drug_exposure_id          INTEGER PRIMARY KEY,
  person_id                 INTEGER NOT NULL REFERENCES person(person_id),
  drug_concept_id           INTEGER NOT NULL,
  drug_exposure_start_date  TEXT NOT NULL,
  drug_exposure_end_date    TEXT NOT NULL,
  drug_type_concept_id      INTEGER NOT NULL,
  drug_source_value         TEXT      -- código ATC de origen
);

CREATE TABLE observation (
  observation_id               INTEGER PRIMARY KEY,
  person_id                    INTEGER NOT NULL REFERENCES person(person_id),
  observation_concept_id       INTEGER NOT NULL,
  observation_date             TEXT NOT NULL,
  observation_type_concept_id  INTEGER NOT NULL,
  value_as_string              TEXT,
  observation_source_value     TEXT
);

-- Notas clínicas en texto libre (OMOP CDM v5.4, tabla NOTE; todas sus columnas obligatorias). Solo sintéticas.
CREATE TABLE note (
  note_id                INTEGER PRIMARY KEY,
  person_id              INTEGER NOT NULL REFERENCES person(person_id),
  note_date              TEXT NOT NULL,
  note_type_concept_id   INTEGER NOT NULL,
  note_class_concept_id  INTEGER NOT NULL,
  note_title             TEXT,
  note_text              TEXT NOT NULL,
  encoding_concept_id    INTEGER NOT NULL,
  language_concept_id    INTEGER NOT NULL
);

-- ---------------------------------------------------------------------------------------------
-- Extensiones del prototipo (NO forman parte de OMOP CDM).
-- ---------------------------------------------------------------------------------------------

-- Pedidos de laboratorio ya solicitados y sin resultado: activan la supresión.
CREATE TABLE pedido_pendiente (
  pedido_id     INTEGER PRIMARY KEY,
  person_id     INTEGER NOT NULL REFERENCES person(person_id),
  prueba        TEXT NOT NULL CHECK (prueba IN ('CAC', 'FGe')),
  fecha_pedido  TEXT NOT NULL
);

-- Lo que el lector de notas encontró, después de las comprobaciones del código (regla N1, firmada 14 nov 2026).
-- La escribe notas/leer.py, nunca el extracto. Solo cuentan las filas con verificada = 1.
CREATE TABLE nota_hallazgo (
  note_id         INTEGER NOT NULL REFERENCES note(note_id),
  person_id       INTEGER NOT NULL REFERENCES person(person_id),
  note_date       TEXT NOT NULL,
  etiqueta        TEXT NOT NULL CHECK (etiqueta IN ('ya_realizada', 'rechazo', 'nefrologia', 'ninguna')),
  prueba          TEXT CHECK (prueba IN ('CAC', 'FGe')),
  fecha_cita      TEXT,                -- fecha leída por el código en la cita (no la del modelo)
  cita            TEXT,                -- frase copiada de la nota, comprobada contra el texto
  valor           REAL,                -- resultado leído por el código en la cita (p. ej. CAC 110)
  unidad          TEXT,                -- mg/g o mg/mmol (CAC)
  verificada      INTEGER NOT NULL CHECK (verificada IN (0, 1)),
  motivo_rechazo  TEXT,                -- verificada = 0: por qué no se aceptó · verificada = 1: observación (valor dudoso, causa transitoria)
  modelo          TEXT NOT NULL
);

-- Una sola fila por extracto. Todas las reglas usan fecha_referencia como «hoy», nunca date('now'):
-- así el mismo extracto da siempre la misma salida.
CREATE TABLE extract_meta (
  id                 INTEGER PRIMARY KEY CHECK (id = 1),
  fecha_referencia   TEXT NOT NULL,      -- fecha del extracto = «hoy» para todas las reglas
  extracto_completo  INTEGER NOT NULL CHECK (extracto_completo IN (0, 1)),
                                         -- 0 = faltan tablas o periodos: el que no se pueda decidir
                                         --     sale como «información insuficiente», nunca como aviso
  fuente             TEXT                -- p. ej. 'sintetico_demo', 'sintetico_ciego'
);
