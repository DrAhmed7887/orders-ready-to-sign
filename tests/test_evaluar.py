"""Evaluación frente a etiquetas: la demo coincide y las etiquetas mal formadas fallan claro."""
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ / "eval"))
sys.path.insert(0, str(RAIZ))

from evaluar import comparar, leer_etiquetas, main, resumen  # noqa: E402
from ejecutar import construir, generar  # noqa: E402

DEMO = RAIZ / "data" / "synthetic" / "demo_seed.sql"
ETIQUETAS = RAIZ / "data" / "synthetic" / "demo_etiquetas.csv"


def test_demo_coincide_con_etiquetas_y_supera_al_filtro_basico():
    r = resumen(comparar(generar(construir(DEMO.read_text(encoding="utf-8"))), leer_etiquetas(ETIQUETAS)))
    assert r["coinciden_exactamente"] == r["casos"] == 4
    assert r["reglas"]["avisos_correctos"] == 3 and r["reglas"]["falsos_avisos"] == 0
    assert r["filtro_basico_fge_menor_60"]["perdidos"] == 3


def test_exigir_falla_si_una_etiqueta_no_coincide(tmp_path):
    mal = tmp_path / "e.csv"
    mal.write_text("person_id,esperado\n1,S1a\n", encoding="utf-8")
    assert main([str(DEMO), str(mal), "--exigir"]) == 1


@pytest.mark.parametrize("contenido", ["person_id,esperado\n1,quizas\n", "person_id,esperado\nx,S1a\n",
                                       "person_id,esperado\n1,S1a\n1,S3\n", "person_id,esperado\n"])
def test_etiquetas_mal_formadas(tmp_path, contenido):
    f = tmp_path / "e.csv"
    f.write_text(contenido, encoding="utf-8")
    with pytest.raises(ValueError):
        leer_etiquetas(f)


CIEGO = RAIZ / "data" / "synthetic" / "ciego" / "extracto.sql"
CIEGO_ETIQUETAS = RAIZ / "data" / "synthetic" / "ciego" / "etiquetas.csv"


@pytest.fixture(scope="module")
def ciego():
    return generar(construir(CIEGO.read_text(encoding="utf-8")))


def test_set_adversarial_coincide_con_sus_etiquetas(ciego):
    # Los 20 casos difíciles de docs/SET_CIEGO.md (23 pacientes: el caso 10 son dos y 2 extra para ≥3 por regla).
    etiquetas = leer_etiquetas(CIEGO_ETIQUETAS)
    r = resumen(comparar(ciego, etiquetas))
    assert r["casos"] == 23 and r["discrepancias"] == []
    reparto = {e: list(etiquetas.values()).count(e) for e in ("S1a", "S1b", "S3", "S3c", "fuera", "ninguno")}
    assert min(reparto[e] for e in ("S1a", "S1b", "S3", "S3c")) >= 3
    assert reparto["fuera"] >= 3 and reparto["ninguno"] >= 5
    assert ciego["fuente"] == "sintetico_ciego"


def test_set_adversarial_detalles_que_la_etiqueta_no_mide(ciego):
    p = {x["person_id"]: x for x in ciego["pedidos"]}
    f = {x["person_id"]: x["motivo_supresion"] for x in ciego["fuera_de_la_lista"]}
    assert "iSRA/iSGLT2" in p[18]["aviso_farmaco"]                                   # caso 17
    assert p[19]["pedido"].startswith("Función renal en descenso: repetir FGe, valorar (CAC ya solicitado")  # caso 18
    assert [t["regla"] for t in p[21]["tambien"]] == ["S1b"]                        # caso 20
    assert "3 valores" in p[15]["motivo"]                                           # caso 14: duplicado promediado
    assert f[4].startswith("Información insuficiente: unidad del CAC")              # caso 4
    assert f[5].startswith("Información insuficiente: el último CAC")               # caso 5
    assert f[8].startswith("Pedido ya pendiente")                                   # caso 8
    assert f[16].startswith("Información insuficiente: unidad del FGe")             # caso 15
    assert f[20].startswith("Pedido ya pendiente: FGe")                             # caso 19
