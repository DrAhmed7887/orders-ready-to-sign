"""La aguja en el pajar: el cupo sintético de 250 pacientes + Amparo (251), cuya señal está repartida entre tablas.

Amparo (sintética): DM2 + HTA en condition_occurrence, sin N18 · CAC 85 mg/g hace 10 meses y FGe 72 → 68
(«analítica aceptable») en measurement · metformina en drug_exposure · ningún pedido en pedido_pendiente ·
y una frase en note: «Trae informe de la mutua: CAC 110 mg/g el 12/09/2026».
- Filtro básico (último FGe <60): no la ve.
- Reglas sin notas: «repetir CAC» (S1b), una prueba que ya está hecha.
- Reglas + lector de notas: albuminuria persistente → «valorar código de ERC» (S1c, N1a enmendada 14 nov 2026).
Además, 5 notas señuelo en pacientes del cupo (pendiente, otra persona, rechazo, Nefrología, repetición normal).

Uso: python3 data/synthetic/aguja/generar_aguja.py   (reescribe extracto.sql, etiquetas*.csv y salidas_oraculo.jsonl)
Sintético, sin pacientes reales. Borrador (14 nov 2026) para la demo; Ahmed lo revisa.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parents[2]
sys.path.insert(0, str(RAIZ))

from notas.leer import huella  # noqa: E402

AMPARO = 251
NOTAS = [
    # note_id, person_id, fecha, texto, etiqueta esperada, salida «oráculo» (lo que diría un modelo perfecto)
    (1, AMPARO, "2026-09-20", "Control DM2 y HTA. Trae informe de la mutua: CAC 110 mg/g el 12/09/2026. Asintomática, TA 132/80.",
     "ya_realizada", {"etiqueta": "ya_realizada", "prueba": "CAC", "fecha_en_nota": "2026-09-12", "cita": "Trae informe de la mutua: CAC 110 mg/g el 12/09/2026"}),
    (2, 167, "2026-11-06", "Repetido CAC en el H. de Manises el 05/11/2026: 18 mg/g. Trae informe.",
     "ya_realizada", {"etiqueta": "ya_realizada", "prueba": "CAC", "fecha_en_nota": "2026-11-05", "cita": "Repetido CAC en el H. de Manises el 05/11/2026: 18 mg/g"}),
    (3, 30, "2026-10-02", "DM2. Pendiente de CAC, se cursa petición.",
     "ninguna", {"etiqueta": "ninguna", "prueba": None, "fecha_en_nota": None, "cita": ""}),
    (4, 26, "2026-10-03", "Acude con su hija. Su madre se hizo el CAC el 02/10/2026 en la mutua.",
     "ninguna", {"etiqueta": "ninguna", "prueba": None, "fecha_en_nota": None, "cita": ""}),
    (5, 124, "2026-10-08", "HTA. No quiere hacerse el análisis de orina por ahora.",
     "rechazo", {"etiqueta": "rechazo", "prueba": "CAC", "fecha_en_nota": None, "cita": "No quiere hacerse el análisis de orina por ahora"}),
    (6, 143, "2026-08-11", "ERC conocida. Seguido en Nefrología del H. Clínico. Sin cambios.",
     "nefrologia", {"etiqueta": "nefrologia", "prueba": None, "fecha_en_nota": None, "cita": "Seguido en Nefrología del H. Clínico"}),
]
# Lista esperada CON notas (solo los pacientes que tocan las notas): escrita antes de ejecutar las reglas.
ESPERADO = {AMPARO: "S1c", 167: "fuera", 30: "S1a", 26: "S1a", 124: "S1a", 143: "S3"}
ESPERADO_SIN_NOTAS = {AMPARO: "S1b", 167: "S1b", 30: "S1a", 26: "S1a", 124: "S1a", 143: "S3"}


def sql_amparo() -> str:
    m = "INSERT INTO measurement (measurement_id, person_id, measurement_concept_id, measurement_date, measurement_type_concept_id, value_as_number, unit_source_value, measurement_source_value) VALUES "
    return "\n".join([
        "-- Amparo (251): la aguja.",
        f"INSERT INTO person (person_id, gender_concept_id, year_of_birth, race_concept_id, ethnicity_concept_id, person_source_value) VALUES ({AMPARO}, 8532, 1957, 0, 0, 'Amparo');",
        f"INSERT INTO condition_occurrence (condition_occurrence_id, person_id, condition_concept_id, condition_start_date, condition_type_concept_id, condition_source_value) VALUES (9001, {AMPARO}, 0, '2014-03-02', 0, 'E11.9');",
        f"INSERT INTO condition_occurrence (condition_occurrence_id, person_id, condition_concept_id, condition_start_date, condition_type_concept_id, condition_source_value) VALUES (9002, {AMPARO}, 0, '2016-06-21', 0, 'I10');",
        f"{m}(9001, {AMPARO}, 0, '2026-01-10', 0, 85, 'mg/g', '9318-7');",
        f"{m}(9002, {AMPARO}, 0, '2025-09-20', 0, 72, 'mL/min/1.73m2', '62238-1');",
        f"{m}(9003, {AMPARO}, 0, '2026-09-20', 0, 68, 'mL/min/1.73m2', '62238-1');",
        f"INSERT INTO drug_exposure (drug_exposure_id, person_id, drug_concept_id, drug_exposure_start_date, drug_exposure_end_date, drug_type_concept_id, drug_source_value) VALUES (9001, {AMPARO}, 0, '2026-08-01', '2026-11-01', 0, 'A10BA02');",
        f"INSERT INTO visit_occurrence (visit_occurrence_id, person_id, visit_concept_id, visit_start_date, visit_end_date, visit_type_concept_id, visit_start_datetime) VALUES (9001, {AMPARO}, 0, '2026-11-14', '2026-11-14', 0, '2026-11-14 10:20');",
    ])


def sql_nota(nid: int, pid: int, fecha: str, texto: str) -> str:
    t = texto.replace("'", "''")
    return (f"INSERT INTO note (note_id, person_id, note_date, note_type_concept_id, note_class_concept_id, note_title, "
            f"note_text, encoding_concept_id, language_concept_id) VALUES ({nid}, {pid}, '{fecha}', 0, 0, 'Evolutivo', '{t}', 0, 0);")


def main() -> None:
    cupo = (RAIZ / "data" / "synthetic" / "cupo_250.sql").read_text(encoding="utf-8")
    cabecera = "-- La aguja en el pajar: cupo_250.sql (sin cambios) + Amparo + 6 notas. Generado por generar_aguja.py.\n"
    cuerpo = "\n".join([sql_amparo(), "-- Notas (texto libre, sintéticas)."] + [sql_nota(*n[:4]) for n in NOTAS])
    (AQUI / "extracto.sql").write_text(cabecera + cupo + "\n" + cuerpo + "\n", encoding="utf-8")
    (AQUI / "etiquetas.csv").write_text("person_id,esperado\n" + "".join(f"{k},{v}\n" for k, v in ESPERADO.items()), encoding="utf-8")
    (AQUI / "etiquetas_sin_notas.csv").write_text("person_id,esperado\n" + "".join(f"{k},{v}\n" for k, v in ESPERADO_SIN_NOTAS.items()), encoding="utf-8")
    (AQUI / "etiquetas_notas.csv").write_text("note_id,etiqueta,prueba\n" + "".join(f"{n[0]},{n[4]},{n[5]['prueba'] or ''}\n" for n in NOTAS), encoding="utf-8")
    (AQUI / "salidas_oraculo.jsonl").write_text("".join(
        json.dumps({"note_id": n[0], "sha256": huella(n[3]), "modelo": "oraculo-aguja", "salida": n[5]}, ensure_ascii=False) + "\n"
        for n in NOTAS), encoding="utf-8")


if __name__ == "__main__":
    main()
