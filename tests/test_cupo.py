"""Cupo sintético: mismo resultado con la misma semilla, extracto válido y recuentos coherentes."""
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "data" / "synthetic"))
sys.path.insert(0, str(RAIZ / "eval"))
sys.path.insert(0, str(RAIZ))

from generar_cupo import a_sql, generar as generar_cupo  # noqa: E402
from rendimiento import contar  # noqa: E402
from ejecutar import construir, generar  # noqa: E402


def test_misma_semilla_mismo_cupo_y_otra_semilla_otro():
    assert a_sql(generar_cupo(60, 7), 60, 7) == a_sql(generar_cupo(60, 7), 60, 7)
    assert a_sql(generar_cupo(60, 7), 60, 7) != a_sql(generar_cupo(60, 8), 60, 8)


def test_el_cupo_pasa_la_validacion_y_los_recuentos_cuadran():
    con = construir(a_sql(generar_cupo(120, 35), 120, 35))
    c = contar(generar(con), 120)
    assert c["con_pedido"] == sum(c["por_regla"].values())
    assert 0 < c["con_pedido"] < 120
    assert c["filtro_basico_y_reglas"] <= c["filtro_basico"]


def test_el_archivo_del_repo_es_el_que_genera_la_semilla():
    guardado = (RAIZ / "data" / "synthetic" / "cupo_250.sql").read_text(encoding="utf-8")
    assert guardado == a_sql(generar_cupo(250, 35), 250, 35), (
        "cupo_250.sql no coincide: regenera con python data/synthetic/generar_cupo.py --n 250 --semilla 35 "
        "-o data/synthetic/cupo_250.sql")


def test_ningun_cac_normal_cruza_el_umbral_al_pasar_a_mg_mmol():
    from generar_cupo import CAC_NORMAL_MAX_MG_G
    assert round(CAC_NORMAL_MAX_MG_G / 8.84, 1) < 3
