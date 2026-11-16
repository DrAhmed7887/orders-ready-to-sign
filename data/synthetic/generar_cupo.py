"""Genera un cupo crónico sintético (DM2 / HTA) con semilla, para contar avisos y supresiones.

Uso:
    python data/synthetic/generar_cupo.py --n 250 --semilla 35 -o data/synthetic/cupo_250.sql

Es una COMPROBACIÓN DE RUIDO («¿cuántos pedidos le saldrían a un cupo?»), no una validación ni una calibración.
Cada probabilidad lleva su fuente o dice «supuesto». Ningún dato real.
"""
from __future__ import annotations

import argparse
import random
from datetime import date, timedelta
from pathlib import Path
from typing import Dict, List, NamedTuple

HOY = date(2026, 11, 14)


class Parametro(NamedTuple):
    valor: float
    fuente: str


PARAMETROS: Dict[str, Parametro] = {
    "p_dm2_sola": Parametro(0.30, "supuesto"),
    "p_hta_sola": Parametro(0.40, "supuesto"),            # el resto: DM2 + HTA
    "p_cac_vencido": Parametro(0.245, "Alicante, Diagnostics 2025 (PMID 41515503): 24,5 % de los objetivos sin cribado en 12 meses; otra población elegible; aquí se aplica por paciente"),
    "p_nunca_cac": Parametro(0.25, "supuesto (fracción de los vencidos sin ningún CAC)"),
    "p_cac_alterado": Parametro(0.20, "supuesto"),
    "p_sin_codigo_erc": Parametro(0.54, "DIAMOND2 (PMID 41741270): 54 % de la ERC de laboratorio sin registrar en DM2; aquí se aplica también a HTA y solo al CAC alterado"),
    "p_en_mg_mmol": Parametro(0.10, "supuesto (laboratorios que informan en mg/mmol)"),
    "pendiente_media": Parametro(-1.0, "supuesto (ml/min/1,73 m²/año)"),
    "pendiente_de": Parametro(2.5, "supuesto"),
    "p_pedido_pendiente": Parametro(0.15, "supuesto (de los pacientes con CAC vencido o alterado, los que ya tienen la repetición pedida)"),
    "p_cita_hoy": Parametro(0.04, "supuesto"),
    "p_inicio_farmaco": Parametro(0.03, "supuesto"),
}

# Normal en mg/g hasta 26: así sigue siendo normal también en mg/mmol (26/8,84 = 2,9 < 3), sin avisos por redondeo.
CAC_NORMAL_MAX_MG_G = 26
FGE_MINIMO = 8   # límite inferior para que el ruido no dé valores imposibles


def _p(nombre: str) -> float:
    return PARAMETROS[nombre].valor


def _fecha(meses_atras: float) -> str:
    return (HOY - timedelta(days=int(meses_atras * 30.44))).isoformat()


class Cupo:
    """Acumula filas como tuplas inmutables y las escribe como INSERTs."""

    def __init__(self) -> None:
        self.filas: Dict[str, List[tuple]] = {t: [] for t in (
            "person", "condition_occurrence", "measurement", "visit_occurrence", "drug_exposure", "pedido_pendiente")}

    def medida(self, pid: int, fecha: str, valor: float, unidad: str, loinc: str) -> None:
        self.filas["measurement"].append(
            (len(self.filas["measurement"]) + 1, pid, 0, fecha, 0, valor, unidad, loinc))


def generar(n: int, semilla: int) -> Cupo:
    r = random.Random(semilla)
    cupo = Cupo()
    for pid in range(1, n + 1):
        u = r.random()
        codigos = ["E11.9"] if u < _p("p_dm2_sola") else ["I10"] if u < _p("p_dm2_sola") + _p("p_hta_sola") else ["E11.9", "I10"]
        cupo.filas["person"].append((pid, r.choice((8507, 8532)), r.randint(1941, 1981), 0, 0,
                                     f"Paciente {pid}"))
        for cod in codigos:
            cupo.filas["condition_occurrence"].append(
                (len(cupo.filas["condition_occurrence"]) + 1, pid, 0, _fecha(r.uniform(24, 180)), 0, cod))

        # CAC: vencido (o nunca) o al día; a veces alterado; a veces con ERC ya codificada.
        if r.random() < _p("p_cac_vencido"):
            meses_cac = None if r.random() < _p("p_nunca_cac") else r.uniform(13, 36)
        else:
            meses_cac = r.uniform(0.5, 11.5)
        alterado = False
        if meses_cac is not None:
            alterado = r.random() < _p("p_cac_alterado")
            valor = round(r.uniform(30, 400) if alterado else r.uniform(3, CAC_NORMAL_MAX_MG_G))
            if r.random() < _p("p_en_mg_mmol"):
                cupo.medida(pid, _fecha(meses_cac), round(valor / 8.84, 1), "mg/mmol", "14958-3")
            else:
                cupo.medida(pid, _fecha(meses_cac), valor, "mg/g", "9318-7")
            if alterado and r.random() >= _p("p_sin_codigo_erc"):
                cupo.filas["condition_occurrence"].append(
                    (len(cupo.filas["condition_occurrence"]) + 1, pid, 0, _fecha(meses_cac), 0, "N18.9"))

        # FGe: 3 a 5 valores en fechas distintas de los últimos ~30 meses, con una pendiente individual.
        fge_inicial, pendiente = r.uniform(62, 98), r.gauss(_p("pendiente_media"), _p("pendiente_de"))
        fechas = sorted({_fecha(r.uniform(0.5, 30)) for _ in range(r.randint(3, 5))})
        for f in fechas:
            anios_desde_inicio = 2.5 - (HOY - date.fromisoformat(f)).days / 365.25
            valor = fge_inicial + pendiente * anios_desde_inicio + r.gauss(0, 2)
            cupo.medida(pid, f, round(max(valor, FGE_MINIMO), 1), "mL/min/1.73m2", "62238-1")

        # Supuesto: el médico ya pidió la repetición a parte de quienes tienen el CAC vencido o alterado.
        # Es aproximado a propósito (no replica los umbrales de las reglas): sirve para ver la supresión en acción.
        con_motivo = meses_cac is None or meses_cac > 12 or alterado
        if con_motivo and r.random() < _p("p_pedido_pendiente"):
            cupo.filas["pedido_pendiente"].append(
                (len(cupo.filas["pedido_pendiente"]) + 1, pid, "CAC", _fecha(r.uniform(0.1, 2.5))))
        if r.random() < _p("p_cita_hoy"):
            cupo.filas["visit_occurrence"].append(
                (len(cupo.filas["visit_occurrence"]) + 1, pid, 0, HOY.isoformat(), HOY.isoformat(), 0))
        if r.random() < _p("p_inicio_farmaco"):
            inicio = _fecha(r.uniform(0.2, 2.8))
            cupo.filas["drug_exposure"].append(
                (len(cupo.filas["drug_exposure"]) + 1, pid, 0, inicio, (HOY + timedelta(days=300)).isoformat(), 0,
                 r.choice(("C09AA05", "A10BK01"))))
    return cupo


COLUMNAS = {
    "person": "person_id, gender_concept_id, year_of_birth, race_concept_id, ethnicity_concept_id, person_source_value",
    "condition_occurrence": "condition_occurrence_id, person_id, condition_concept_id, condition_start_date, condition_type_concept_id, condition_source_value",
    "measurement": "measurement_id, person_id, measurement_concept_id, measurement_date, measurement_type_concept_id, value_as_number, unit_source_value, measurement_source_value",
    "visit_occurrence": "visit_occurrence_id, person_id, visit_concept_id, visit_start_date, visit_end_date, visit_type_concept_id",
    "drug_exposure": "drug_exposure_id, person_id, drug_concept_id, drug_exposure_start_date, drug_exposure_end_date, drug_type_concept_id, drug_source_value",
    "pedido_pendiente": "pedido_id, person_id, prueba, fecha_pedido",
}


def _literal(v: object) -> str:
    if isinstance(v, str):
        return "'" + v.replace("'", "''") + "'"
    return repr(v)


def a_sql(cupo: Cupo, n: int, semilla: int) -> str:
    cabecera = [f"-- Cupo sintético generado por data/synthetic/generar_cupo.py (n={n}, semilla={semilla}).",
                "-- Maqueta · datos sintéticos. Comprobación de ruido, no validación. Parámetros y fuentes:"]
    cabecera += [f"--   {k} = {p.valor} · {p.fuente}" for k, p in PARAMETROS.items()]
    cuerpo = [f"INSERT INTO extract_meta VALUES (1, '{HOY.isoformat()}', 1, 'sintetico_cupo_{n}_{semilla}');"]
    for tabla in COLUMNAS:
        for fila in cupo.filas[tabla]:
            cuerpo.append(f"INSERT INTO {tabla} ({COLUMNAS[tabla]}) VALUES ({', '.join(map(_literal, fila))});")
    return "\n".join(cabecera + cuerpo) + "\n"


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--n", type=int, default=250)
    ap.add_argument("--semilla", type=int, default=35)
    ap.add_argument("-o", "--salida", type=Path, required=True)
    args = ap.parse_args()
    if not 1 <= args.n <= 100_000:
        ap.error("--n debe estar entre 1 y 100000")
    args.salida.write_text(a_sql(generar(args.n, args.semilla), args.n, args.semilla), encoding="utf-8")
    print(f"{args.n} pacientes → {args.salida}")


if __name__ == "__main__":
    main()
