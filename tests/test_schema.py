"""El esquema del extracto se carga en SQLite y cumple las columnas obligatorias de OMOP CDM v5.4."""
import sqlite3
from pathlib import Path

import pytest

SCHEMA = Path(__file__).resolve().parent.parent / "data" / "schema.sql"

# Columnas NOT NULL del DDL oficial: OHDSI/CommonDataModel inst/ddl/5.4/sqlite (comprobado 14 nov 2026).
OMOP_REQUIRED = {
    "person": {"person_id", "gender_concept_id", "year_of_birth",
               "race_concept_id", "ethnicity_concept_id"},
    "visit_occurrence": {"visit_occurrence_id", "person_id", "visit_concept_id",
                         "visit_start_date", "visit_end_date", "visit_type_concept_id"},
    "condition_occurrence": {"condition_occurrence_id", "person_id", "condition_concept_id",
                             "condition_start_date", "condition_type_concept_id"},
    "measurement": {"measurement_id", "person_id", "measurement_concept_id",
                    "measurement_date", "measurement_type_concept_id"},
    "drug_exposure": {"drug_exposure_id", "person_id", "drug_concept_id",
                      "drug_exposure_start_date", "drug_exposure_end_date",
                      "drug_type_concept_id"},
    "observation": {"observation_id", "person_id", "observation_concept_id",
                    "observation_date", "observation_type_concept_id"},
    "note": {"note_id", "person_id", "note_date", "note_type_concept_id", "note_class_concept_id",
             "note_text", "encoding_concept_id", "language_concept_id"},
}
EXTENSIONS = {"pedido_pendiente", "extract_meta", "nota_hallazgo"}


@pytest.fixture()
def con():
    c = sqlite3.connect(":memory:")
    c.executescript(SCHEMA.read_text(encoding="utf-8"))
    yield c
    c.close()


def _columns(con: sqlite3.Connection, table: str) -> dict[str, tuple]:
    return {row[1]: row for row in con.execute(f"PRAGMA table_info({table})")}


def test_all_tables_exist(con):
    tables = {r[0] for r in con.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert set(OMOP_REQUIRED) | EXTENSIONS <= tables


@pytest.mark.parametrize("table", sorted(OMOP_REQUIRED))
def test_omop_required_columns_present_and_not_null(con, table):
    cols = _columns(con, table)
    missing = OMOP_REQUIRED[table] - set(cols)
    assert not missing, f"{table}: faltan columnas obligatorias {missing}"
    nullable = {c for c in OMOP_REQUIRED[table] if not cols[c][3] and not cols[c][5]}
    assert not nullable, f"{table}: deberían ser NOT NULL {nullable}"


def test_extract_meta_holds_one_row_with_reference_date(con):
    con.execute("INSERT INTO extract_meta VALUES (1, '2026-11-14', 1, 'sintetico_demo')")
    with pytest.raises(sqlite3.IntegrityError):
        con.execute("INSERT INTO extract_meta VALUES (2, '2026-11-15', 1, 'otro')")
    with pytest.raises(sqlite3.IntegrityError):
        con.execute("UPDATE extract_meta SET fecha_referencia = NULL")
