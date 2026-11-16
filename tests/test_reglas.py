"""Reglas S1a, S1b, S3 y supresión sobre los pacientes de la demo y casos límite sintéticos.

Verificación de software, no validación clínica.
"""
import sys
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(RAIZ))

from ejecutar import ExtractoInvalido, construir, generar  # noqa: E402

DEMO = (RAIZ / "data" / "synthetic" / "demo_seed.sql").read_text(encoding="utf-8")

META = "INSERT INTO extract_meta VALUES (1, '2026-11-14', {completo}, 'test');\n"


def persona(pid, nacimiento=1960, codigos=("E11.9",)):
    sql = (f"INSERT INTO person (person_id, gender_concept_id, year_of_birth, race_concept_id, "
           f"ethnicity_concept_id, person_source_value) VALUES ({pid}, 8532, {nacimiento}, 0, 0, 'P{pid}');\n")
    for i, cod in enumerate(codigos):
        sql += (f"INSERT INTO condition_occurrence (condition_occurrence_id, person_id, condition_concept_id, "
                f"condition_start_date, condition_type_concept_id, condition_source_value) "
                f"VALUES ({pid * 100 + i}, {pid}, 0, '2015-01-01', 0, '{cod}');\n")
    return sql


_mid = iter(range(1, 10_000))


def medida(pid, fecha, valor, unidad, loinc):
    return (f"INSERT INTO measurement (measurement_id, person_id, measurement_concept_id, measurement_date, "
            f"measurement_type_concept_id, value_as_number, unit_source_value, measurement_source_value) "
            f"VALUES ({next(_mid)}, {pid}, 0, '{fecha}', 0, {valor}, '{unidad}', '{loinc}');\n")


def cac(pid, fecha, valor, unidad="mg/g", loinc="9318-7"):
    return medida(pid, fecha, valor, unidad, loinc)


def fge(pid, fecha, valor):
    return medida(pid, fecha, valor, "mL/min/1.73m2", "62238-1")


def correr(sql, completo=1):
    return generar(construir(META.format(completo=completo) + sql))


def reglas(res, pid):
    return {p["regla"] for p in res["pedidos"] if p["person_id"] == pid} | {
        t["regla"] for p in res["pedidos"] if p["person_id"] == pid for t in p["tambien"]}


def fuera(res, pid):
    return [f["motivo_supresion"] for f in res["fuera_de_la_lista"] if f["person_id"] == pid]


# --- Demo ------------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def demo():
    return generar(construir(DEMO))


def test_demo_orden_y_grupos(demo):
    assert [(p["nombre"], p["regla"], p["grupo"]) for p in demo["pedidos"]] == [
        ("Manuel", "S3", 1), ("Pilar", "S1b", 2), ("Rosa", "S1a", 3)]


def test_demo_manuel_pendiente(demo):
    manuel = demo["pedidos"][0]
    assert "-8.5 ml/min" in manuel["motivo"]
    assert manuel["pedido"].startswith("Función renal en descenso")


def test_demo_pilar_hoy_en_consulta(demo):
    pilar = demo["pedidos"][1]
    assert pilar["hoy_en_consulta"] is True
    assert "85 mg/g" in pilar["motivo"]


def test_demo_antonio_fuera_por_pedido_pendiente(demo):
    assert demo["fuera_de_la_lista"][0]["nombre"] == "Antonio"
    assert demo["fuera_de_la_lista"][0]["motivo_supresion"].startswith("Pedido ya pendiente")


def test_demo_baseline_no_encuentra_a_nadie(demo):
    # Ningún paciente de la demo tiene FGe <60: el filtro básico no ve ninguno de los 3 hallazgos.
    assert demo["baseline_fge_menor_60"] == []


def test_demo_cuenta_los_pacientes_revisados(demo):
    # La pantalla enseña «N pacientes revisados»: es la población de las reglas (DM2, HTA o FGe <60).
    assert demo["pacientes_revisados"] == 4


def test_volver_a_ejecutar_no_duplica():
    a, b = generar(construir(DEMO)), generar(construir(DEMO))
    assert [p["id"] for p in a["pedidos"]] == [p["id"] for p in b["pedidos"]]
    assert len({p["id"] for p in a["pedidos"]}) == len(a["pedidos"])


# --- S1a ---------------------------------------------------------------------------------------

def test_s1a_sin_ningun_cac():
    res = correr(persona(1))
    assert reglas(res, 1) == {"S1a"}


def test_s1a_cac_hace_11_meses_no_avisa():
    res = correr(persona(1) + cac(1, "2025-12-20", 10))
    assert reglas(res, 1) == set()


def test_s1a_fuera_de_poblacion_no_avisa():
    res = correr(persona(1, codigos=("J45",)) + fge(1, "2026-10-01", 85))
    assert reglas(res, 1) == set()


def test_s1a_fge_menor_60_entra_en_poblacion():
    res = correr(persona(1, codigos=()) + fge(1, "2026-10-01", 55))
    assert reglas(res, 1) == {"S1a"}


# --- S1b ---------------------------------------------------------------------------------------

def test_s1b_limite_30_mg_g_avisa():
    res = correr(persona(1) + cac(1, "2026-04-01", 30))
    assert reglas(res, 1) == {"S1b"}


def test_s1b_29_mg_g_no_es_albuminuria():
    res = correr(persona(1) + cac(1, "2026-04-01", 29))
    assert reglas(res, 1) == set()


def test_s1b_mg_mmol_se_compara_con_su_propio_umbral():
    res = correr(persona(1) + cac(1, "2026-04-01", 4, "mg/mmol", "14958-3"))
    assert reglas(res, 1) == {"S1b"}


def test_s1b_unidad_desconocida_es_informacion_insuficiente():
    res = correr(persona(1) + cac(1, "2026-04-01", 40, "mg/dL"))
    assert reglas(res, 1) == set()
    assert fuera(res, 1)[0].startswith("Información insuficiente")


def test_s1b_con_codigo_n18_no_avisa():
    res = correr(persona(1, codigos=("E11.9", "N18.3")) + cac(1, "2026-04-01", 85))
    assert "S1b" not in reglas(res, 1)


def test_s1b_hace_5_meses_aun_no_avisa():
    res = correr(persona(1) + cac(1, "2026-07-01", 85))
    assert reglas(res, 1) == set()


def test_s1b_repetido_normal_no_avisa():
    res = correr(persona(1) + cac(1, "2026-02-01", 85) + cac(1, "2026-06-01", 12))
    assert reglas(res, 1) == set()


def test_s1b_a3_sale_antes_que_a2():
    res = correr(persona(1) + cac(1, "2026-04-01", 45) + persona(2) + cac(2, "2026-04-01", 350))
    assert [p["person_id"] for p in res["pedidos"]] == [2, 1]


# --- S3 ----------------------------------------------------------------------------------------

def test_s3_dos_valores_no_es_tendencia():
    res = correr(persona(1) + cac(1, "2026-10-01", 5) + fge(1, "2025-06-01", 80) + fge(1, "2026-10-01", 70))
    assert reglas(res, 1) == set()


def test_s3_menos_de_12_meses_no_es_tendencia():
    sql = persona(1) + cac(1, "2026-10-01", 5) + fge(1, "2026-01-01", 80) + fge(1, "2026-05-01", 74) + fge(1, "2026-10-01", 70)
    assert "S3" not in reglas(correr(sql), 1)


def test_s3_pendiente_lenta_no_avisa():
    sql = persona(1) + cac(1, "2026-10-01", 5) + fge(1, "2024-10-01", 80) + fge(1, "2025-10-01", 77) + fge(1, "2026-10-01", 74)
    assert reglas(correr(sql), 1) == set()


def test_s3_fechas_duplicadas_se_promedian():
    sql = (persona(1) + cac(1, "2026-10-01", 5) + fge(1, "2024-10-01", 80) + fge(1, "2024-10-01", 80)
           + fge(1, "2025-10-01", 70) + fge(1, "2026-10-01", 60))
    res = correr(sql)
    assert reglas(res, 1) == {"S3"}
    assert "3 valores" in res["pedidos"][0]["motivo"]


def test_s3_inicio_farmaco_reciente_no_suprime_y_avisa():
    sql = (persona(1) + cac(1, "2026-10-01", 5) + fge(1, "2024-11-01", 78) + fge(1, "2025-11-01", 69) + fge(1, "2026-11-01", 61)
           + "INSERT INTO drug_exposure VALUES (1, 1, 0, '2026-09-15', '2027-09-15', 0, 'A10BK01');\n")
    res = correr(sql)
    assert reglas(res, 1) == {"S3"}
    assert "iSRA/iSGLT2" in res["pedidos"][0]["aviso_farmaco"]


def test_s3c_caida_aislada_mayor_20():
    sql = persona(1) + cac(1, "2026-10-01", 5) + fge(1, "2026-03-01", 80) + fge(1, "2026-10-01", 60)
    assert reglas(correr(sql), 1) == {"S3c"}


# --- Supresión ---------------------------------------------------------------------------------

def test_pedido_pendiente_antiguo_ya_no_suprime():
    sql = (persona(1) + cac(1, "2026-02-01", 85)
           + "INSERT INTO pedido_pendiente VALUES (1, 1, 'CAC', '2026-06-01');\n")
    assert reglas(correr(sql), 1) == {"S1b"}


def test_pedido_pendiente_de_otra_prueba_no_suprime():
    sql = (persona(1) + cac(1, "2026-02-01", 85)
           + "INSERT INTO pedido_pendiente VALUES (1, 1, 'FGe', '2026-11-01');\n")
    assert reglas(correr(sql), 1) == {"S1b"}


def test_extracto_incompleto_todo_insuficiente():
    res = generar(construir(DEMO.replace("'2026-11-14', 1, 'sintetico_demo'", "'2026-11-14', 0, 'sintetico_demo'")))
    assert res["pedidos"] == []
    assert all(f["motivo_supresion"].startswith("Información insuficiente") for f in res["fuera_de_la_lista"])


def test_extracto_sin_fecha_de_referencia_falla_claro():
    with pytest.raises(ExtractoInvalido):
        construir(persona(1))


# --- Regresiones de la auditoría técnica (14 nov 2026) ------------------------------------------

def test_s3_exactamente_12_meses_es_tendencia():  # hallazgo 6
    sql = persona(1) + cac(1, "2026-10-01", 5) + fge(1, "2025-11-01", 80) + fge(1, "2026-05-01", 74) + fge(1, "2026-11-01", 68)
    assert reglas(correr(sql), 1) == {"S3"}


def test_s3_un_dia_antes_de_12_meses_no_es_tendencia():  # hallazgo 6
    sql = persona(1) + cac(1, "2026-10-01", 5) + fge(1, "2025-11-02", 80) + fge(1, "2026-05-01", 74) + fge(1, "2026-11-01", 68)
    assert "S3" not in reglas(correr(sql), 1)


def test_cac_sin_resultado_es_insuficiente_no_nunca_pedido():  # hallazgo 3
    res = correr(persona(1) + medida(1, "2026-11-01", "NULL", "mg/g", "9318-7"))
    assert reglas(res, 1) == set()
    assert fuera(res, 1) == ["Información insuficiente: el último CAC no tiene resultado numérico"]


def test_cac_vacio_tras_alterado_no_cuenta_como_sin_repetir():  # hallazgo 3
    res = correr(persona(1) + cac(1, "2026-02-01", 85) + medida(1, "2026-10-01", "NULL", "mg/g", "9318-7"))
    assert reglas(res, 1) == set()
    assert fuera(res, 1)[0].startswith("Información insuficiente")


def test_fge_unidad_desconocida_no_calcula_tendencia():  # hallazgo 4
    sql = (persona(1) + cac(1, "2026-10-01", 5) + medida(1, "2024-11-01", 80, "unknown", "62238-1")
           + medida(1, "2025-11-01", 70, "unknown", "62238-1") + medida(1, "2026-11-01", 60, "unknown", "62238-1"))
    res = correr(sql)
    assert reglas(res, 1) == set()
    assert fuera(res, 1)[0].startswith("Información insuficiente: unidad del FGe")


def test_fge_unidad_equivalente_se_acepta():  # hallazgo 4
    sql = (persona(1) + cac(1, "2026-10-01", 5) + medida(1, "2024-11-01", 78, "mL/min/{1.73_m2}", "62238-1")
           + fge(1, "2025-11-01", 69) + fge(1, "2026-11-01", 61))
    assert reglas(correr(sql), 1) == {"S3"}


TENDENCIA = persona(1) + cac(1, "2026-10-01", 5) + fge(1, "2024-11-01", 78) + fge(1, "2025-11-01", 69) + fge(1, "2026-11-01", 61)


def test_s3_con_cac_pendiente_pide_solo_fge():  # hallazgo 7
    res = correr(TENDENCIA + "INSERT INTO pedido_pendiente VALUES (1, 1, 'CAC', '2026-11-02');\n")
    assert res["pedidos"][0]["pedido"] == "Función renal en descenso: repetir FGe, valorar (CAC ya solicitado el 2026-11-02)"


def test_s3_con_fge_pendiente_pide_solo_cac():  # hallazgo 7
    res = correr(TENDENCIA + "INSERT INTO pedido_pendiente VALUES (1, 1, 'FGe', '2026-11-02');\n")
    assert res["pedidos"][0]["pedido"] == "Función renal en descenso: solicitar CAC, valorar (FGe ya solicitado el 2026-11-02)"


def test_s3_con_ambas_pendientes_queda_fuera():  # hallazgo 7
    res = correr(TENDENCIA + "INSERT INTO pedido_pendiente VALUES (1, 1, 'FGe', '2026-11-02');\n"
                 + "INSERT INTO pedido_pendiente VALUES (2, 1, 'CAC', '2026-11-03');\n")
    assert reglas(res, 1) == set()
    assert fuera(res, 1) == ["Pedido ya pendiente: FGe solicitado el 2026-11-02 y CAC el 2026-11-03"]


def test_tambien_lleva_su_propio_id_y_pedido():  # hallazgo 8
    sql = persona(1) + cac(1, "2026-02-01", 85) + fge(1, "2026-03-01", 80) + fge(1, "2026-10-01", 60)
    p = correr(sql)["pedidos"][0]
    assert p["regla"] == "S3c"
    assert [(t["regla"], t["pedido"]) for t in p["tambien"]] == [
        ("S1b", "Albuminuria sin confirmar: repetir CAC en primera orina de la mañana")]
    assert p["tambien"][0]["id"] != p["id"]


def test_registro_huerfano_falla_claro():  # hallazgo 13
    with pytest.raises(ExtractoInvalido):
        correr(cac(999, "2026-02-01", 85))


def test_fecha_referencia_imposible_falla_claro():  # hallazgo 14
    with pytest.raises(ExtractoInvalido, match="fecha no válida"):
        construir("INSERT INTO extract_meta VALUES (1, '2026-02-30', 1, 'x');")


def test_fecha_de_medida_no_iso_falla_claro():  # hallazgo 14 (y 2: una fecha con HTML no llega a la pantalla)
    with pytest.raises(ExtractoInvalido, match="measurement.measurement_date"):
        correr(persona(1) + cac(1, "2025<img src=x onerror=alert(1)>-01-01", 85))


def test_procedencia_incluye_toda_la_serie_de_s3():  # hallazgo 18
    sql = TENDENCIA + "".join(cac(1, f"2026-0{m}-01", 5) for m in range(3, 10))
    p = correr(sql)["pedidos"][0]
    assert [x["valor"] for x in p["procedencia"] if x["prueba"] == "FGe"] == [61, 69, 78]


def test_salida_completa_identica_al_volver_a_ejecutar():  # hallazgo 19
    import json
    assert json.dumps(generar(construir(DEMO)), sort_keys=True) == json.dumps(generar(construir(DEMO)), sort_keys=True)


# --- Regresiones de la revisión de código (code-reviewer, 14 nov 2026) ---------------------------

def test_resultado_de_texto_se_rechaza():  # HIGH 1: '<3' >= 300 es verdadero en SQLite
    with pytest.raises(ExtractoInvalido, match="no numérico"):
        correr(persona(1) + medida(1, "2026-04-01", "'<3'", "mg/g", "9318-7"))


@pytest.mark.parametrize("sentencia", [
    "ATTACH DATABASE ':memory:' AS otra;",
    "CREATE TABLE parametro (x);",
    "CREATE VIEW cac AS SELECT 1;",
    "DELETE FROM person;",
    "UPDATE extract_meta SET extracto_completo = 0;",
    "DROP TABLE measurement;",
])
def test_el_extracto_solo_puede_insertar(sentencia):  # HIGH 3
    with pytest.raises(ExtractoInvalido, match="más que insertar"):
        correr(persona(1) + sentencia)


def test_nota_coincide_con_pedido_parcial():  # MEDIUM 4
    p = correr(TENDENCIA + "INSERT INTO pedido_pendiente VALUES (1, 1, 'FGe', '2026-11-09');\n")["pedidos"][0]
    assert p["nota"] == "Descenso de FGe (KDIGO 2012, rec. 2.1.3): se solicita CAC (FGe ya solicitado el 2026-11-09)."


def test_fge_antiguo_con_unidad_rara_no_silencia_s3():  # MEDIUM 6
    sql = TENDENCIA + medida(1, "2019-05-01", 90, "mL/min", "62238-1")
    assert reglas(correr(sql), 1) == {"S3"}


def test_salida_js_se_rechaza(tmp_path):  # LOW 10
    from ejecutar import main
    assert main([str(RAIZ / "data" / "synthetic" / "demo_seed.sql"), "-o", str(tmp_path / "x.js")]) == 2


def test_salida_dice_si_el_extracto_esta_completo():  # T5: la pantalla avisa de extracto incompleto
    assert generar(construir(DEMO))["extracto_completo"] is True
    incompleto = DEMO.replace("'2026-11-14', 1, 'sintetico_demo'", "'2026-11-14', 0, 'sintetico_demo'")
    assert generar(construir(incompleto))["extracto_completo"] is False


# --- Decisiones clínicas firmadas por Ahmed (C2–C5, 14 nov 2026) ----------------------------------

def test_c2_mismo_dia_gana_a2_en_mg_mmol_frente_a_a1_en_mg_g():
    # 25 mg/g es A1 y 4 mg/mmol es A2: manda la categoría, no el número (25 > 4).
    res = correr(persona(1) + cac(1, "2026-04-01", 25) + cac(1, "2026-04-01", 4, "mg/mmol", "14958-3"))
    assert reglas(res, 1) == {"S1b"}
    assert "4 mg/mmol (A2)" in res["pedidos"][0]["motivo"]


def test_c2_mismo_dia_gana_a3_en_mg_mmol_frente_a_a2_en_mg_g():
    # 30 mg/g es A2 y 30 mg/mmol es A3: mismo número, gana el A3.
    res = correr(persona(1) + cac(1, "2026-04-01", 30) + cac(1, "2026-04-01", 30, "mg/mmol", "14958-3"))
    assert "30 mg/mmol (A3)" in res["pedidos"][0]["motivo"]
    assert res["pedidos"][0]["prioridad"] == 1


def test_c2_unidad_desconocida_no_esconde_un_alterado_del_mismo_dia():
    res = correr(persona(1) + cac(1, "2026-04-01", 900, "mg/dL") + cac(1, "2026-04-01", 85))
    assert reglas(res, 1) == {"S1b"}


def test_c2_un_normal_del_mismo_dia_no_tapa_una_unidad_desconocida():
    res = correr(persona(1) + cac(1, "2026-04-01", 900, "mg/dL") + cac(1, "2026-04-01", 12))
    assert reglas(res, 1) == set()
    assert fuera(res, 1)[0].startswith("Información insuficiente: unidad del CAC")


def test_c3_caida_aislada_solo_mira_la_ventana_de_36_meses():
    # Un FGe de hace 4 años no cuenta como «penúltimo valor» para S3c.
    sql = persona(1) + cac(1, "2026-10-01", 5) + fge(1, "2022-06-01", 90) + fge(1, "2026-10-01", 65)
    assert reglas(correr(sql), 1) == set()


def test_c4_dentro_de_s3_primero_la_caida_mas_rapida_y_despues_la_edad():
    rapida = persona(1, 1970) + cac(1, "2026-10-01", 5) + fge(1, "2024-11-01", 80) + fge(1, "2025-11-01", 65) + fge(1, "2026-11-01", 50)
    lenta_mayor = persona(2, 1940) + cac(2, "2026-10-01", 5) + fge(2, "2024-11-01", 78) + fge(2, "2025-11-01", 69) + fge(2, "2026-11-01", 61)
    lenta_joven = persona(3, 1975) + cac(3, "2026-10-01", 5) + fge(3, "2024-11-01", 78) + fge(3, "2025-11-01", 69) + fge(3, "2026-11-01", 61)
    res = correr(rapida + lenta_joven + lenta_mayor)
    assert [p["person_id"] for p in res["pedidos"]] == [1, 2, 3]


def _dispensacion(did, pid, fecha, atc):
    return f"INSERT INTO drug_exposure VALUES ({did}, {pid}, 0, '{fecha}', '2027-12-31', 0, '{atc}');\n"


def test_c5_renovacion_de_un_isra_cronico_no_es_inicio():
    sql = TENDENCIA + _dispensacion(1, 1, "2024-11-01", "C09AA05") + _dispensacion(2, 1, "2026-10-14", "C09AA05")
    p = correr(sql)["pedidos"][0]
    assert p["regla"] == "S3"
    assert p["aviso_farmaco"] is None


def test_c5_isra_cronico_no_tapa_el_inicio_de_un_isglt2():
    sql = TENDENCIA + _dispensacion(1, 1, "2024-11-01", "C09AA05") + _dispensacion(2, 1, "2026-10-14", "A10BK01")
    assert "iSRA/iSGLT2" in correr(sql)["pedidos"][0]["aviso_farmaco"]


# --- Auditoría técnica y casos límite, 14 nov -----------------------------------------------------

def test_s1b_y_s1a_no_piden_dos_cac_en_la_misma_ficha():
    # CAC alterado hace >12 meses: S1b («repetir CAC») ya cubre el cribado; S1a no añade otro CAC.
    res = correr(persona(1) + cac(1, "2025-06-01", 45))
    assert reglas(res, 1) == {"S1b"}


def test_s1a_sigue_avisando_si_el_ultimo_cac_no_tiene_resultado():
    res = correr(persona(1) + medida(1, "2025-06-01", "NULL", "mg/g", "9318-7"))
    assert "S1a" in reglas(res, 1)


def test_s3_caida_de_categoria_lo_dice_en_el_motivo():
    # Pendiente > −5/año, pero paso de G2 a G3a con caída ≥25 %: dispara por la rama de categoría.
    sql = (persona(1) + cac(1, "2026-10-01", 5) + fge(1, "2023-12-01", 60) + fge(1, "2024-11-01", 61)
           + fge(1, "2025-11-01", 62) + fge(1, "2026-11-01", 45))
    p = correr(sql)["pedidos"][0]
    assert p["regla"] == "S3"
    assert "G2 → G3a" in p["motivo"]


def test_hallazgo_fuera_avisa_si_el_paciente_sigue_en_la_lista():
    # Sin CAC (S1a) con CAC ya pedido → S1a fuera; la tendencia de FGe (S3) sigue en la lista.
    sql = (persona(1) + fge(1, "2024-11-01", 78) + fge(1, "2025-11-01", 69) + fge(1, "2026-11-01", 61)
           + "INSERT INTO pedido_pendiente VALUES (1, 1, 'CAC', '2026-11-02');\n")
    res = correr(sql)
    assert "S3" in reglas(res, 1)
    f = [f for f in res["fuera_de_la_lista"] if f["person_id"] == 1]
    assert f and all(x["sigue_en_lista"] for x in f)


def test_cac_unidad_en_mayusculas_se_reconoce():
    res = correr(persona(1) + cac(1, "2026-04-01", 45, unidad="MG/G "))
    assert reglas(res, 1) == {"S1b"}


def test_s3_con_s1b_no_pide_dos_cac_pero_conserva_el_motivo():  # Caso límite, 14 nov
    sql = persona(1) + cac(1, "2026-03-01", 85) + fge(1, "2024-11-01", 78) + fge(1, "2025-11-01", 69) + fge(1, "2026-11-01", 61)
    p = correr(sql)["pedidos"][0]
    assert p["regla"] == "S3" and p["pedido"] == "Función renal en descenso: repetir FGe + CAC, valorar"
    (t,) = p["tambien"]
    assert t["regla"] == "S1b" and "CAC 85 mg/g" in t["motivo"]
    assert t["pedido"] == "CAC ya incluido en el pedido principal"


def test_s3_con_s1a_no_pide_dos_cac():  # Caso límite, 14 nov
    sql = persona(1) + fge(1, "2024-11-01", 78) + fge(1, "2025-11-01", 69) + fge(1, "2026-11-01", 61)
    p = correr(sql)["pedidos"][0]
    assert [(t["regla"], t["pedido"]) for t in p["tambien"]] == [("S1a", "CAC ya incluido en el pedido principal")]


def test_s3_con_cac_pendiente_s1_queda_fuera_y_no_se_duplica():
    sql = (persona(1) + fge(1, "2024-11-01", 78) + fge(1, "2025-11-01", 69) + fge(1, "2026-11-01", 61)
           + "INSERT INTO pedido_pendiente VALUES (1, 1, 'CAC', '2026-11-02');\n")
    p = correr(sql)["pedidos"][0]
    assert p["tambien"] == []
